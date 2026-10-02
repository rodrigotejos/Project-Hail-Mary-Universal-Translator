# Logical Components - Unit 1 (UI & Flet Integration)

## 1. `SyncButtonHandler`
- **Role**: Event handler bound to `btn-sync-cloud`.
- **Responsibility**: Spawns a `threading.Thread`, updates `txt-cloud-status` to `[Cloud] STATUS: SINCRONIZANDO...`, disables button, executes `SyncService.sync_all()`, and triggers SnackBar feedback upon thread termination.

## 2. `InputSanitizer`
- **Role**: Text validation helper.
- **Responsibility**: Strips whitespace and strips unprintable characters before passing text to `TranslatorDB.add_word()`.

## 3. `UIAutomationKeys`
- **Role**: Automation contract dictionary.
- **Responsibility**: Provides fixed, stable `key` attributes to all Flet elements (`btn-sync-cloud`, `txt-cloud-status`, `input-word-key`, `input-conversation-msg`).
