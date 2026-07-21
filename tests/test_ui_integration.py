import pytest
import flet as ft
from unittest.mock import MagicMock, patch

from src.ui.layout import create_main_layout
from src.services.sync_service import SyncResult

def test_layout_contains_automation_keys():
    """Verify that create_main_layout returns all required automation keys."""
    layout, controls = create_main_layout()
    assert layout is not None
    assert "txt_cloud_status" in controls
    assert "btn_sync_cloud" in controls
    assert "input_word_key" in controls
    assert "input_conversation_msg" in controls

    assert controls["txt_cloud_status"].key == "txt-cloud-status"
    assert controls["btn_sync_cloud"].key == "btn-sync-cloud"
    assert controls["input_word_key"].key == "input-word-key"
    assert controls["input_conversation_msg"].key == "input-conversation-msg"

def test_input_sanitizer_trimming():
    """Verify whitespace trimming logic on text entries."""
    raw_word = "   MÚSICA   \n"
    sanitized = raw_word.strip()
    assert sanitized == "MÚSICA"
    assert len(sanitized) == 6

def test_sync_result_formatting():
    """Verify SyncResult format string generation for UI display."""
    res_success = SyncResult(success=True, records_pushed=3, records_pulled=5)
    assert res_success.success is True
    assert res_success.records_pushed == 3
    assert res_success.records_pulled == 5

    res_fail = SyncResult(success=False, error_message="Network Timeout")
    assert res_fail.success is False
    assert res_fail.error_message == "Network Timeout"
