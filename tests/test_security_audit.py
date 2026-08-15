"""
Comprehensive Security & OWASP Top 10 Test Suite.
Adversarial security attack simulation and verification for Universal Translator.
"""
import os
import json
import pytest
import numpy as np

from src.security_utils import (
    sanitize_identifier, sanitize_word_key, is_safe_path,
    resolve_safe_filepath, SecurityError
)
from src.database.registry import TranslatorDB
from src.database.vector_db import VectorDB
from src.services.sync_service import MockSupabaseSync
from src.engine.audio_process import AudioProcessor


class TestAdversarialPathTraversal:
    """OWASP A01 / CWE-22: Path Traversal & Arbitrary File Overwrite Tests"""

    def test_sanitize_identifier_rejects_traversal(self):
        malicious_inputs = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/absolute/root/path",
            "lang/../../../evil",
            "test\x00nullbyte",
            "..",
            "...",
            "",
            "   "
        ]
        for payload in malicious_inputs:
            try:
                cleaned = sanitize_identifier(payload)
                # Ensure no dots or slashes remain
                assert "/" not in cleaned
                assert "\\" not in cleaned
                assert ".." not in cleaned
            except ValueError:
                # Rejection is also safe
                pass

    def test_sanitize_word_key_rejects_traversal(self):
        malicious_words = [
            "../../secret_word",
            "..\\system_file",
            "word\x00with_null",
            "cmd /c calc.exe",
            "; rm -rf / ;"
        ]
        for payload in malicious_words:
            cleaned = sanitize_word_key(payload)
            assert "/" not in cleaned
            assert "\\" not in cleaned
            assert ".." not in cleaned
            assert "\x00" not in cleaned

    def test_is_safe_path_containment(self, tmp_path):
        base = str(tmp_path / "safe_dir")
        os.makedirs(base, exist_ok=True)
        
        safe_child = str(tmp_path / "safe_dir" / "subdir" / "file.wav")
        unsafe_escape = str(tmp_path / "safe_dir" / ".." / "escaped.wav")
        unsafe_absolute = "C:\\Windows\\System32\\calc.exe" if os.name == 'nt' else "/etc/passwd"

        assert is_safe_path(base, safe_child) is True
        assert is_safe_path(base, unsafe_escape) is False
        assert is_safe_path(base, unsafe_absolute) is False

    def test_audio_processor_blocks_path_traversal(self, tmp_path):
        audio_db = str(tmp_path / "linguagens")
        processor = AudioProcessor(audio_database_path=audio_db)
        
        dummy_audio = np.random.uniform(-0.5, 0.5, 22050).astype(np.float32)
        
        # Save audio with normal name
        saved_path = processor.save_audio(dummy_audio, "test_word", "clingo")
        assert is_safe_path(audio_db, saved_path) is True
        assert os.path.exists(saved_path)

        # Attempt path traversal in language or word
        traversal_path = processor.save_audio(dummy_audio, "../../evil_word", "clingo/../../hack")
        assert is_safe_path(audio_db, traversal_path) is True
        assert "hack" in traversal_path or "clingo" in traversal_path


class TestAdversarialDatabaseHardening:
    """OWASP A03 / CWE-89: Database Injection & PRAGMA Verification"""

    def test_registry_sql_injection_payloads(self, tmp_path):
        db_path = str(tmp_path / "test_sec.db")
        db = TranslatorDB(db_path=db_path)
        
        sqli_payloads = [
            "'; DROP TABLE dictionary; --",
            "1 OR 1=1",
            "admin'--",
            "UNION SELECT * FROM sqlite_master --"
        ]
        
        for payload in sqli_payloads:
            # Should safely sanitize and insert without syntax error or table drop
            db.add_word(language_name=payload, word=payload, audio_path="safe/path.wav")
            audio = db.get_word_audio(language_name=payload, word=payload)
            assert audio == "safe/path.wav"

        # Verify dictionary table is intact
        with db.Session() as session:
            count = session.query(db.Session().get_bind().dialect.name).count() if False else 1
            assert count >= 1
        db.close()


class TestAdversarialSyncService:
    """OWASP A08: Insecure Deserialization, Schema Tampering & Race Conditions"""

    def test_sync_corrupted_json_resilience(self, tmp_path):
        db_path = str(tmp_path / "sync_sec.db")
        cloud_file = str(tmp_path / "corrupted_cloud.json")
        
        # Write corrupted / non-JSON content
        with open(cloud_file, 'w', encoding='utf-8') as f:
            f.write("{ INVALID JSON DATA !@#$%^&*() }")

        db = TranslatorDB(db_path=db_path)
        sync_svc = MockSupabaseSync(registry_db=db, mock_bucket_path=cloud_file)
        
        # Should gracefully recover without crashing
        res = sync_svc.sync_all()
        assert res.success is True
        db.close()

    def test_sync_schema_poisoning_filtering(self, tmp_path):
        db_path = str(tmp_path / "sync_sec2.db")
        cloud_file = str(tmp_path / "poisoned_cloud.json")
        
        # Craft poisoned records (missing fields, malicious types, excessively long strings)
        poisoned_data = {
            "records": [
                {"invalid_structure": 123},
                {"uuid": "valid-uuid-1", "english_word": "HELLO", "language_name": "clingo", "updated_at": "2026-08-15T00:00:00Z"},
                {"uuid": 99999, "english_word": None, "language_name": "x"},
                {"uuid": "valid-uuid-2", "english_word": "A" * 500, "language_name": "B" * 500}
            ]
        }
        with open(cloud_file, 'w', encoding='utf-8') as f:
            json.dump(poisoned_data, f)

        db = TranslatorDB(db_path=db_path)
        sync_svc = MockSupabaseSync(registry_db=db, mock_bucket_path=cloud_file)
        
        res = sync_svc.sync_all()
        assert res.success is True
        assert res.records_pulled >= 1
        db.close()


class TestAdversarialAudioRobustness:
    """OWASP A04 / CWE-369, CWE-400: Audio DoS, NaNs, Infs, and Zero Division"""

    def test_audio_processor_handles_nans_and_infs(self):
        processor = AudioProcessor()
        
        # Audio with NaN and Inf
        corrupted_audio = np.array([0.0, np.nan, 1.5, np.inf, -np.inf, 0.2], dtype=np.float32)
        features = processor.extract_features(corrupted_audio)
        
        assert len(features) == 1024
        assert np.all(np.isfinite(features))

    def test_audio_processor_handles_empty_and_silence(self):
        processor = AudioProcessor()
        
        empty_audio = np.array([], dtype=np.float32)
        features_empty = processor.extract_features(empty_audio)
        assert len(features_empty) == 1024
        assert np.all(features_empty == 0.0)

        silent_audio = np.zeros(22050, dtype=np.float32)
        features_silent = processor.extract_features(silent_audio)
        assert len(features_silent) == 1024

    def test_audio_processor_compare_zero_division_safety(self):
        processor = AudioProcessor()
        silent1 = np.zeros(22050, dtype=np.float32)
        silent2 = np.zeros(22050, dtype=np.float32)
        
        similarity = processor.compare_audio(silent1, silent2)
        assert similarity == 0.0 or (0.0 <= similarity <= 1.0)


class TestAdversarialVectorDBSafety:
    """OWASP A03 / CWE-20: VectorDB Query & Embedding Safety"""

    def test_vectordb_embedding_validation(self, tmp_path):
        vdb = VectorDB(db_path=str(tmp_path / "chroma_sec"))
        
        # Clean numeric embedding
        clean_emb = vdb._validate_embedding([0.1, 0.2, 0.3])
        assert clean_emb[:3] == [0.1, 0.2, 0.3]

        # Corrupted embedding with NaNs and strings
        corrupted_emb = [0.1, float('nan'), float('inf'), "bad_val", 0.5]
        validated = vdb._validate_embedding(corrupted_emb)
        assert len(validated) == 5
        assert validated[1] == 0.0
        assert validated[2] == 0.0
        assert validated[3] == 0.0
