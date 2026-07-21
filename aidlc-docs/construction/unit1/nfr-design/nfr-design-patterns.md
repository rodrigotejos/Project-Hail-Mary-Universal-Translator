# NFR Design Patterns - Unit 1 (UI & Flet Integration)

## 1. Resilience Patterns
- **Background Worker Threading (`threading.Thread`)**:
  - UI event handlers (e.g., `on_sync_click`) dispatch cloud sync calls via daemon worker threads.
  - Keeps Flet UI responsive and interactive while `SyncService.sync_all()` retries across exponential backoff periods.
  - Safe UI updating via Flet's `page.update()` callbacks after thread completion.

## 2. Security Patterns
- **Input Sanitization & Whitespace Trimming**:
  - Text fields for `word_key` and conversation messages strip leading/trailing whitespace (`.strip()`) and sanitize unprintable ASCII control characters prior to database or sync calls.
  - Mitigates UI layout overflow bugs and dirty key indexing.

## 3. Property-Based Testing & Component Validation
- **State & Component Integration Strategy**:
  - Unit tests inspect `UIState` transitions when `SyncResult` events are emitted.
  - Headless Flet layout verification ensures control keys (`btn-sync-cloud`, `txt-cloud-status`, `input-word-key`) exist and update properties cleanly.
