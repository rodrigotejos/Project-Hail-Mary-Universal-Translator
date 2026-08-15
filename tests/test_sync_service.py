import os
import json
import pytest
from hypothesis import given, settings, HealthCheck, strategies as st
from unittest.mock import patch

from src.database.registry import TranslatorDB, Dictionary, Language
from src.services.sync_service import MockSupabaseSync, RetryManager, SyncResult

# --- Step 3.1: Fuzz text boundaries for the UUID generator ---
@given(
    english=st.text(min_size=1, max_size=500),
    alien_lang=st.from_regex(r'^[a-zA-Z0-9_]{1,50}$', fullmatch=True)
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
def test_uuid_deterministic_generation(english, alien_lang):
    """
    Test that the UUID generation does not crash on extreme text input
    and remains deterministic.
    """
    test_db = TranslatorDB(db_path=":memory:")
    try:
        test_db.add_word(language_name=alien_lang, word=english, audio_path="/dummy/path")
        
        with test_db.Session() as session:
            lang = session.query(Language).filter_by(name=alien_lang.lower()).first()
            assert lang is not None
            
            record = session.query(Dictionary).filter_by(language_id=lang.id, word_key=english.upper()).first()
            assert record is not None
            assert record.uuid is not None
            assert len(record.uuid) == 64  # SHA-256 hash length
            
            # Re-adding the same word shouldn't crash, should just update
            test_db.add_word(language_name=alien_lang, word=english, audio_path="/dummy/path2")
            
            # Expire session cache to read updated state from DB
            session.expire_all()
            
            # Ensure UUID remained the same (deterministic)
            record2 = session.query(Dictionary).filter_by(language_id=lang.id, word_key=english.upper()).first()
            assert record.uuid == record2.uuid
            assert record2.audio_path == "/dummy/path2"
            
    finally:
        test_db.close()

# --- Step 3.2: Fuzz network exceptions on the Mock JSON file to test the RetryManager ---
@given(
    fail_attempts=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=10)
def test_retry_manager_resiliency(fail_attempts):
    """
    Test that the RetryManager correctly trips the circuit or recovers 
    based on the number of mock network failures.
    """
    manager = RetryManager(max_retries=3, base_delay=0.01) # fast delay for tests
    
    attempts = {"count": 0}
    
    def mock_network_call():
        attempts["count"] += 1
        if attempts["count"] <= fail_attempts:
            raise IOError("Simulated network timeout")
        return "Success"
        
    if fail_attempts > 3:
        # Should trip circuit
        with pytest.raises(Exception) as excinfo:
            manager.execute(mock_network_call)
        assert "Circuit tripped" in str(excinfo.value)
    else:
        # Should recover
        result = manager.execute(mock_network_call)
        assert result == "Success"
        assert attempts["count"] == fail_attempts + 1
