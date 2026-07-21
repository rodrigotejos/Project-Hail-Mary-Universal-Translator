# Domain Entities - Unit 1 (UI & Flet Integration)

## 1. `UIState`
Represents the runtime UI state bound to Flet controls.

```python
class UIState:
    is_syncing: bool = False
    cloud_status_text: str = "[Cloud] STATUS: OFFLINE"
    cloud_status_color: str = "orange"
```

## 2. `ControlIdentifiers`
Standardized element keys for UI automation and testing.

- `SYNC_BUTTON_KEY`: `"btn-sync-cloud"`
- `CLOUD_STATUS_TEXT_KEY`: `"txt-cloud-status"`
- `LEARNING_WORD_INPUT_KEY`: `"input-word-key"`
- `CONVERSATION_MSG_INPUT_KEY`: `"input-conversation-msg"`
