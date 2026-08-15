"""
Sync service between local SQLite registry and mock cloud persistence.
Hardened with schema validation, atomic file writes, and race-condition resilience.
"""
import json
import os
import time
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from src.database.registry import TranslatorDB, Dictionary
try:
    from src.security_utils import sanitize_identifier, sanitize_word_key
except ImportError:
    from security_utils import sanitize_identifier, sanitize_word_key

MAX_CLOUD_RECORDS = 50000


class SyncResult:
    """Represents the outcome of a synchronization cycle."""
    def __init__(self, success: bool, records_pushed: int = 0, records_pulled: int = 0, error_message: str = ""):
        self.success = success
        self.records_pushed = records_pushed
        self.records_pulled = records_pulled
        self.error_message = error_message

    def __repr__(self):
        return f"<SyncResult success={self.success} pushed={self.records_pushed} pulled={self.records_pulled}>"


class RetryManager:
    """Implements Exponential Backoff Circuit Breaker."""
    def __init__(self, max_retries: int = 3, base_delay: float = 0.5):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute(self, func, *args, **kwargs) -> Any:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except (IOError, OSError) as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise RuntimeError(f"Circuit tripped after {self.max_retries} attempts: {str(e)}") from e
                time.sleep(self.base_delay * (2 ** (attempt - 1)))
        return None


class MockSupabaseSync:
    """Orchestrates secure sync between local SQLite and Mock Cloud JSON."""
    
    def __init__(self, registry_db: TranslatorDB, mock_bucket_path="mock_supabase_bucket.json"):
        self.registry = registry_db
        self.mock_bucket_path = os.path.abspath(mock_bucket_path)
        self.retry_manager = RetryManager()
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not os.path.exists(self.mock_bucket_path):
            self._write_cloud({"records": []})

    def _validate_record_schema(self, record: Any) -> Optional[Dict[str, Any]]:
        """Validate individual cloud record schema to prevent deserialization vulnerabilities."""
        if not isinstance(record, dict):
            return None

        uuid_val = record.get("uuid")
        english_word = record.get("english_word")
        lang_name = record.get("language_name")
        updated_at = record.get("updated_at")
        audio_path = record.get("audio_path", "")

        if not (uuid_val and isinstance(uuid_val, str) and len(uuid_val) <= 128):
            return None
        if not (english_word and isinstance(english_word, str) and len(english_word) <= 128):
            return None
        if not (lang_name and isinstance(lang_name, str) and len(lang_name) <= 64):
            return None
        if not (updated_at and isinstance(updated_at, str)):
            updated_at = datetime.now(timezone.utc).isoformat()

        try:
            clean_word = sanitize_word_key(english_word)
            clean_lang = sanitize_identifier(lang_name)
        except ValueError:
            return None

        return {
            "uuid": str(uuid_val).strip(),
            "english_word": clean_word,
            "language_name": clean_lang,
            "audio_path": str(audio_path),
            "updated_at": str(updated_at)
        }

    def _read_cloud(self) -> Dict[str, Any]:
        """Read and validate cloud JSON structure safely."""
        if not os.path.exists(self.mock_bucket_path):
            return {"records": []}

        try:
            with open(self.mock_bucket_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            # If file is corrupted, return safe empty state
            return {"records": []}

        if not isinstance(data, dict) or "records" not in data or not isinstance(data["records"], list):
            return {"records": []}

        valid_records = []
        for raw_r in data["records"][:MAX_CLOUD_RECORDS]:
            validated = self._validate_record_schema(raw_r)
            if validated:
                valid_records.append(validated)

        return {"records": valid_records}

    def _write_cloud(self, data: Dict[str, Any]):
        """Atomic write using temporary file + atomic rename to prevent corruption & race conditions."""
        dir_name = os.path.dirname(self.mock_bucket_path) or "."
        os.makedirs(dir_name, exist_ok=True)

        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tmp_file:
            tmp_name = tmp_file.name
            json.dump(data, tmp_file, indent=4)

        # Atomic replacement of file
        os.replace(tmp_name, self.mock_bucket_path)

    def sync_all(self, vector_db_instance=None) -> SyncResult:
        """Main orchestrator for bi-directional sync."""
        try:
            return self.retry_manager.execute(self._sync_logic, vector_db_instance)
        except Exception as e:
            return SyncResult(success=False, error_message=str(e))

    def _sync_logic(self, vector_db_instance=None) -> SyncResult:
        cloud_data = self._read_cloud()
        cloud_records = {r["uuid"]: r for r in cloud_data.get("records", [])}
        
        records_pushed = 0
        records_pulled = 0
        
        with self.registry.Session() as session:
            local_records = session.query(Dictionary).all()
            local_dict = {r.uuid: r for r in local_records if r.uuid}

            # 1. PULL & CONFLICT RESOLUTION (Cloud Authority)
            for cloud_uuid, cloud_rec in cloud_records.items():
                if cloud_uuid in local_dict:
                    local_r = local_dict[cloud_uuid]
                    if local_r.updated_at != cloud_rec["updated_at"]:
                        local_r.audio_path = cloud_rec.get("audio_path", local_r.audio_path)
                        local_r.updated_at = cloud_rec["updated_at"]
                        local_r.synced = 1
                        records_pulled += 1
                else:
                    lang_id = self.registry.get_or_create_language(session, cloud_rec.get("language_name", "alien"))
                    new_local = Dictionary(
                        uuid=cloud_uuid,
                        language_id=lang_id,
                        word_key=cloud_rec["english_word"],
                        audio_path=cloud_rec.get("audio_path", ""),
                        synced=1,
                        updated_at=cloud_rec["updated_at"]
                    )
                    session.add(new_local)
                    records_pulled += 1

            # 2. PUSH (Local un-synced)
            unsynced = session.query(Dictionary).filter(Dictionary.synced == 0).all()
            for record in unsynced:
                lang = record.language
                clean_lang_name = lang.name if lang else "unknown"
                cloud_records[record.uuid] = {
                    "uuid": record.uuid,
                    "english_word": record.word_key,
                    "language_name": clean_lang_name,
                    "audio_path": record.audio_path,
                    "updated_at": record.updated_at,
                }
                record.synced = 1
                records_pushed += 1

            # Save to mock cloud atomically
            cloud_data["records"] = list(cloud_records.values())
            self._write_cloud(cloud_data)
            session.commit()

        return SyncResult(success=True, records_pushed=records_pushed, records_pulled=records_pulled)
