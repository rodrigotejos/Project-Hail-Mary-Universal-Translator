# Code Generation Plan - Unit 2 (Mock Sync Service & DB Modifications)

## Context
- **Stories**: Migrating SQLite data to support Sync, Mocking Cloud Sync logic.
- **Dependencies**: None (This is the foundational data layer. UI will depend on this).
- **Entities**: `VocabularyRecord` (SQLite), `CloudVocabulary` (JSON).

## Execution Steps

### 1. Repository Layer Generation (SQLAlchemy)
- **Target**: `src/database/registry.py`
- **Action**: Replace `sqlite3` raw queries with SQLAlchemy. Define `VocabularyRecord` with `uuid`, `synced`, `updated_at`.
- [ ] Step 1.1: Install/Add `SQLAlchemy` to requirements.
- [ ] Step 1.2: Rewrite `TranslatorDB` into an SQLAlchemy Session Manager.
- [ ] Step 1.3: Implement the Deterministic UUID Migration algorithm (hash of english + alien words) on initialization.

### 2. Business Logic Generation (Sync Service)
- **Target**: `src/services/sync_service.py` (New File)
- **Action**: Implement the `MockSupabaseSync` service.
- [ ] Step 2.1: Implement the `RetryManager` for Exponential Backoff (Resiliency NFR).
- [ ] Step 2.2: Implement `push_to_cloud` and `pull_from_cloud` using the Mock JSON file.
- [ ] Step 2.3: Implement Conflict Resolution (Cloud Authority).

### 3. Business Logic Unit Testing (PBT)
- **Target**: `tests/test_sync_service.py` (New File)
- **Action**: Implement Hypothesis-based fuzzing.
- [ ] Step 3.1: Fuzz text boundaries for the UUID generator.
- [ ] Step 3.2: Fuzz network exceptions on the Mock JSON file to test the `RetryManager`.

### 4. Summary & Documentation
- [ ] Step 4.1: Update documentation in `aidlc-docs/construction/unit2/code/`.
