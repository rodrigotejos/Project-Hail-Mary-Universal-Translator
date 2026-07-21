# Business Rules - Unit 1 (UI & Flet Integration)

## Rule 1: Non-Blocking User Interaction
- Triggering a sync operation must not lock or freeze the Flet UI loop.
- Long-running or retried sync requests must execute in a background thread or async handler, maintaining UI responsiveness.

## Rule 2: Explicit Visual Feedback
- Sync status must always be prominently displayed in the top header (`[Cloud] STATUS: ...`).
- Color coding:
  - Green / Cyan: `ONLINE` / `SINCRONIZADO`
  - Yellow: `SINCRONIZANDO...`
  - Red / Orange: `FALHA DE CONEXÃO` / `OFFLINE`

## Rule 3: SnackBar Notification Contract
- Success messages must display pushed and pulled counts.
- Error messages must cleanly explain the issue without dumping unhandled Python stack traces to the end user.

## Rule 4: Automation-Friendly Identifiers
- Every interactive element (buttons, text fields, icons) must define explicit `key` or `data_id` properties (e.g., `btn-sync-cloud`, `status-cloud-text`, `input-word-key`).
