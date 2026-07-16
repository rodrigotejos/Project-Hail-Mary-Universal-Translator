import json
import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from src.database.registry import TranslatorDB, Dictionary

class SyncResult:
    def __init__(self, success: bool, records_pushed: int = 0, records_pulled: int = 0, error_message: str = ""):
        self.success = success
        self.records_pushed = records_pushed
        self.records_pulled = records_pulled
        self.error_message = error_message

    def __repr__(self):
        return f"<SyncResult success={self.success} pushed={self.records_pushed} pulled={self.records_pulled}>"

class RetryManager:
    """Implements Exponential Backoff Circuit Breaker"""
    def __init__(self, max_retries: int = 3, base_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute(self, func, *args, **kwargs) -> Any:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except IOError as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise Exception(f"Circuit tripped after {self.max_retries} attempts: {str(e)}")
                # Exponential backoff
                time.sleep(self.base_delay * (2 ** (attempt - 1)))
        return None

class MockSupabaseSync:
    """Orchestrates sync between local SQLite and Mock Cloud JSON"""
    
    def __init__(self, registry_db: TranslatorDB, mock_bucket_path="mock_supabase_bucket.json"):
        self.registry = registry_db
        self.mock_bucket_path = mock_bucket_path
        self.retry_manager = RetryManager()
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not os.path.exists(self.mock_bucket_path):
            with open(self.mock_bucket_path, 'w', encoding='utf-8') as f:
                json.dump({"records": []}, f)

    def _read_cloud(self) -> Dict[str, Any]:
        with open(self.mock_bucket_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_cloud(self, data: Dict[str, Any]):
        with open(self.mock_bucket_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

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
                    # Conflict: Cloud Authority dictates we overwrite local if they differ
                    # For simplicity, we can just check if updated_at differs or force overwrite
                    local_r = local_dict[cloud_uuid]
                    if local_r.updated_at != cloud_rec["updated_at"]:
                        local_r.audio_path = cloud_rec.get("audio_path", local_r.audio_path)
                        local_r.updated_at = cloud_rec["updated_at"]
                        local_r.synced = 1
                        # Wait, we should also pull vector data if vector_db_instance is provided!
                        # Not fully implementing vector sync here for simplicity of unit 2 mock, 
                        # but in reality we would add it to ChromaDB.
                        records_pulled += 1
                else:
                    # New from cloud
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
                cloud_records[record.uuid] = {
                    "uuid": record.uuid,
                    "english_word": record.word_key,
                    "language_name": lang.name if lang else "unknown",
                    "audio_path": record.audio_path,
                    "updated_at": record.updated_at,
                    # "vector_embedding": [] # Here we would read from ChromaDB
                }
                record.synced = 1
                records_pushed += 1

            # Save to mock cloud
            cloud_data["records"] = list(cloud_records.values())
            self._write_cloud(cloud_data)
            
            session.commit()

        return SyncResult(success=True, records_pushed=records_pushed, records_pulled=records_pulled)
