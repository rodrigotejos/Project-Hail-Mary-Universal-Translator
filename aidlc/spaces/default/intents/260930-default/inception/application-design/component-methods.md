# Component Methods Design

## `LearningPanel` (Flet Component)
- `build()`: Returns the Flet UI tree.
- `on_record_click(e)`: Handles the microphone toggle.
- `update_waveform(data)`: Updates the UI canvas with new audio frame data.

## `ConversationPanel` (Flet Component)
- `build()`: Returns the Flet UI tree.
- `append_transcription(text_chunk, missing_words)`: Adds a new text row, formatting missing words in red.

## `SyncService` (`src/services/sync_service.py`)
- `push_local_changes()`: Fetches records where `synced=0` and pushes to mock cloud.
- `pull_cloud_changes()`: Fetches mock cloud updates and updates local DBs.
- `sync_all()`: Orchestrates the full push/pull loop.

## `TranslatorEngine` (`src/engine/translator.py`)
- `start_async_loop(queue)`: Initiates the STT loop, pushing results into the provided `asyncio.Queue`.
