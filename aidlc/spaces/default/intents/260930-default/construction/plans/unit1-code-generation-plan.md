# Code Generation Plan - Unit 1 (UI & Flet Integration)

## Context
- **Stories**: Flet UI Layout enhancement, Cloud Sync Button & Status Integration, Input Sanitization, Automation Keys.
- **Dependencies**: Unit 2 (`SyncService`, `TranslatorDB`).
- **Target Files**:
  - `src/ui/layout.py`: Update header layout to include "Sincronizar Nuvem" button, status text, and assign keys.
  - `src/main.py`: Instantiate `SyncService` & `TranslatorDB`, wire `btn-sync-cloud` click handler to `threading.Thread`, handle SnackBar alerts, and sanitize inputs.
  - `tests/test_ui_integration.py`: Headless Flet UI component and `UIState` handler tests.

## Execution Steps

### 1. UI Layout & Controls Update
- **Target**: `src/ui/layout.py`
- **Action**: Add `Sincronizar Nuvem` button, update status indicator layout, and set `key` properties on all controls.
- [ ] Step 1.1: Add `btn-sync-cloud` and `txt-cloud-status` to header container in `create_main_layout()`.
- [ ] Step 1.2: Assign automation `key` properties to inputs and buttons.

### 2. UI Wiring & Event Handlers (Flet Main)
- **Target**: `src/main.py`
- **Action**: Connect Flet app lifecycle to `SyncService` and `TranslatorDB`.
- [ ] Step 2.1: Wire `on_sync_click` with `threading.Thread` to execute `SyncService.sync_all()` without blocking UI.
- [ ] Step 2.2: Add SnackBar notification handlers for sync success (`green`) and failure (`red`).
- [ ] Step 2.3: Add `InputSanitizer` logic on word entry (`add_word`).

### 3. Unit & Component Integration Testing
- **Target**: `tests/test_ui_integration.py` (New File)
- **Action**: Create pytest tests for `UIState` and Flet control property updates.
- [ ] Step 3.1: Test `on_sync_click` state transitions.
- [ ] Step 3.2: Test `InputSanitizer` whitespace trimming and control char stripping.

### 4. Summary & Documentation
- [ ] Step 4.1: Update documentation in `aidlc-docs/construction/unit1/code/summary.md`.
