# Services Design

## Service Layer

### 1. `SyncService` (`src/services/sync_service.py`)
- **Definition**: A standalone orchestrator service responsible for bridging the gap between local data storage and the mock Supabase cloud environment.
- **Responsibilities**:
  - Abstracting the cloud implementation details from the rest of the app.
  - Reading from `RegistryDB` (SQLite).
  - Writing to a mock JSON file simulating the cloud bucket.
  - Ensuring conflict resolution (author IDs, UUIDs) during sync.
- **Interactions**:
  - Called by `SyncButton` (UI).
  - Instantiates and queries `RegistryDB` and `VectorDB`.

### 2. `TranslationService` (Wrapped in `src/engine/translator.py`)
- **Definition**: Manages the continuous listening pipeline.
- **Responsibilities**:
  - Initializes Faster-Whisper and ChromaDB.
  - Pipes audio from microphone to STT.
  - Pushes parsed strings to an `asyncio.Queue` (Pub/Sub pattern).
- **Interactions**:
  - Called by `app.py` as a background task.
  - UI `ConversationPanel` consumes from its queue.
