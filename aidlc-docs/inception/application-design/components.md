# Components Design

## Flet UI Components (`src/ui/components/`)
1. **`LearningPanel`**:
   - **Purpose**: Allows users to record human anchor words and hear alien sounds to register new vocabulary using few-shot learning.
   - **Responsibilities**: Displays an animated waveform, handles microphone recording start/stop events, captures text input for meanings.
   - **Interface**: Exposes Flet `Container` or `Column` object. Emits events for "Save Recording".

2. **`ConversationPanel`**:
   - **Purpose**: Real-time STT visualization with highlighted unknown words.
   - **Responsibilities**: Renders transcribed chunks. Parses missing words to highlight them in red.
   - **Interface**: Exposes Flet `Container`. Receives updates via async queues.

3. **`SyncButton`**:
   - **Purpose**: Cloud synchronization trigger.
   - **Responsibilities**: Triggers the sync service and displays sync status (success/failure/syncing).
   - **Interface**: Exposes a Flet `ElevatedButton`.

## Backend Components
1. **`TranslatorEngine` (`src/engine/translator.py`)**:
   - **Purpose**: Orchestrates STT, vector lookup, and audio translation.
   - **Responsibilities**: (Updated) Pushes translation chunks to an `asyncio.Queue` instead of blocking/printing to CLI.

2. **`RegistryDB` & `VectorDB` (`src/database/`)**:
   - **Purpose**: Data storage.
   - **Responsibilities**: (Updated) Manage `UUID`, `synced`, and `updated_at` properties.
