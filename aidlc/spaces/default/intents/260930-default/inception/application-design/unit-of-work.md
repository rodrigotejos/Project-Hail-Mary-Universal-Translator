# Units of Work Definitions

## Overview
Based on the application design, the project has been decomposed into two distinct, manageable units of work to ensure separation of concerns and allow for incremental delivery and testing.

## Unit 1: Flet UI & Engine Async Binding
- **Definition**: The presentation layer and the event loop orchestration required to connect the Flet frontend to the existing STT and Vector AI backends without blocking the UI thread.
- **Components Included**:
  - `src.ui.app`
  - `src.ui.components.learning_panel`
  - `src.ui.components.conversation_panel`
  - `src.ui.components.sync_button`
  - `src.engine.translator` (async `asyncio.Queue` modifications)
- **Responsibilities**:
  - Render the responsive Sci-Fi interface.
  - Animate audio waveforms.
  - Parse and display live transcription strings and highlight missing words.
  - Bridge the heavy AI processes to the reactive UI event loop.

## Unit 2: Mock Sync Service & DB Modifications
- **Definition**: The data layer expansion and local-first simulation for cloud synchronization.
- **Components Included**:
  - `src.database.registry` (Schema updates for UUID, synced, updated_at)
  - `src.services.sync_service` (New `MockSupabaseSync` service)
- **Responsibilities**:
  - Run the SQLite migration to assign UUIDs to existing int-based PKs.
  - Manage the push/pull logic of the `synced` flag.
  - Resolve sync conflicts based on timestamp.
  - Mock the external network call to a local JSON file.
