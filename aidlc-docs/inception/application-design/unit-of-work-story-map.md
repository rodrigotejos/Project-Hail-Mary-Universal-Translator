# Unit of Work Requirements Map

*Note: Since the User Stories stage was skipped based on project simplicity, this document maps the core functional and non-functional requirements to the respective Units of Work.*

## Unit 1: Flet UI & Engine Async Binding
- **REQ-01**: Fully Responsive Flet UI (Desktop, Web, Mobile) -> `src.ui.app`
- **REQ-02**: Dynamic Animated Waveform -> `src.ui.components.learning_panel`
- **REQ-04**: Offline First Architecture Real-time Translation -> `src.engine.translator` and `src.ui.components.conversation_panel`
- **REQ-05**: Missing Words Visual Alerts -> `src.ui.components.conversation_panel`
- **NFR-04**: Non-blocking Performance (Async Queues) -> `src.engine.translator`

## Unit 2: Mock Sync Service & DB Modifications
- **REQ-03**: Mocked Supabase Sync Logic -> `src.services.sync_service`
- **NFR-01**: Security Baseline (Input validation, Secure queries) -> `src.database.registry`
- **NFR-02**: Resiliency Baseline (Mock failure handling) -> `src.services.sync_service`
- **NFR-03**: Property-Based Testing (Data struct fuzzing) -> Applied to `src.database` schemas and `sync_service` logic.
