# Consolidated Application Design

This document consolidates the Application Design phase for the Universal Translator UI and Cloud Sync features.

## 1. Components
- **`LearningPanel` (UI)**: Flet component for recording new alien vocabulary.
- **`ConversationPanel` (UI)**: Flet component displaying real-time STT translations with missing words highlighted.
- **`SyncButton` (UI)**: Flet button triggering the cloud sync.
- **`TranslatorEngine` (Engine)**: Backend STT pipeline modified to push to async queues.
- **`RegistryDB` & `VectorDB` (Database)**: Enhanced with `UUID`, `synced`, and `updated_at`.

## 2. Component Methods
- `LearningPanel.update_waveform(data)`: Dynamically redraws the audio waveform based on mic levels.
- `ConversationPanel.append_transcription(text_chunk, missing_words)`: Appends text dynamically without refreshing the whole page.
- `SyncService.sync_all()`: Pushes unsynced local SQLite entries to mock cloud and pulls new ones.
- `TranslatorEngine.start_async_loop(queue)`: Bridges the blocking Whisper STT loop to Flet's async event loop.

## 3. Services
- **`SyncService` (`src/services/sync_service.py`)**: A standalone orchestrator managing the conflict resolution and bi-directional push/pull of vocabulary between local SQLite and the simulated cloud environment.

## 4. Dependencies
- The UI layer (`app.py`) depends on `TranslatorEngine` (via `asyncio.Queue`) and `SyncService` (via direct invocation).
- `SyncService` depends on `RegistryDB` (SQLite metadata) and `VectorDB` (ChromaDB vectors).
- The `TranslatorEngine` is decoupled from the UI, operating strictly via Pub/Sub queue pushing, ensuring thread safety and preventing UI freezing.
