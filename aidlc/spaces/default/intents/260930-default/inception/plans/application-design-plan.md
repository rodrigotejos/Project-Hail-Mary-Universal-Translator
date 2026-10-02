# Application Design Plan

## Mandatory Design Artifacts
- [ ] Generate `components.md` with component definitions and high-level responsibilities
- [ ] Generate `component-methods.md` with method signatures (business rules detailed later in Functional Design)
- [ ] Generate `services.md` with service definitions and orchestration patterns
- [ ] Generate `component-dependency.md` with dependency relationships and communication patterns
- [ ] Validate design completeness and consistency
- [ ] Consolidate into `application-design.md`

## Application Design Clarification Questions

To ensure our high-level component boundaries and service layers are designed correctly, please answer the following questions. Provide your answers directly after each `[Answer]:` tag.

### 1. Component Grouping (Flet UI)
Since Flet applications can grow quickly, how should we organize the UI components?
A) Keep them consolidated in a single `components.py` file to maintain a flat structure alongside `app.py`.
B) Create a `src/ui/components/` directory to modularize each panel (e.g., `learning_panel.py`, `conversation_panel.py`) separately.
X) Other (please describe after [Answer]: tag below)

[Answer]: b

### 2. Service Layer Boundary (Cloud Sync)
How should the `MockSupabaseSync` class interact with the existing local databases (`registry.db` and ChromaDB)?
A) **Standalone Service**: A completely independent orchestrator service (`src/services/sync_service.py`) that acts as a middleman, reading from local DBs and pushing to the mock cloud.
B) **Integrated Database Method**: Built directly into the existing `RegistryDB` class as a new `.sync_to_cloud()` method.
X) Other (please describe after [Answer]: tag below)

[Answer]: a

### 3. Communication Pattern (Engine -> UI)
The AI STT engine (Faster-Whisper) is a heavy, blocking process. How should the Flet UI receive transcription updates from the engine without freezing?
A) **Callback Injection**: The UI passes a callback function (`on_text_received`) down into the Engine, which the Engine calls whenever a new chunk is transcribed.
B) **Async Queue/PubSub**: The Engine pushes transcribed text into an `asyncio.Queue`, and the UI runs a background Flet task that constantly reads from this queue.
X) Other (please describe after [Answer]: tag below)

[Answer]: b
