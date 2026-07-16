# Logical Components - Unit 2

## Infrastructure Elements

### 1. `SQLAlchemy Session Manager`
- **Role**: Replaces the raw SQLite connection.
- **Responsibility**: Manages transactions, rollback on failure, and ORM entity mapping for `VocabularyRecord`.
- **Integration**: Injected into the `SyncService` and anywhere `RegistryDB` is currently used.

### 2. `RetryManager` (Circuit Breaker)
- **Role**: Encapsulates the Exponential Backoff logic.
- **Responsibility**: Takes any network-bound lambda function (like `write_to_mock_cloud`) and executes it. Keeps state of retry attempts. Returns a structured `SyncResult`.
- **Integration**: Wraps the push/pull methods inside `SyncService`.

### 3. `Hypothesis Test Suite` (PBT)
- **Role**: Independent test orchestrator.
- **Responsibility**: Runs the fuzzing strategies against the SQLAlchemy models and the `RetryManager`.
- **Integration**: Placed in `tests/test_sync_service.py` to be run during the Build and Test phase.
