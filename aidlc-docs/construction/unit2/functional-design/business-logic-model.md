# Business Logic Model - Unit 2 (Mock Sync Service & DB Modifications)

## 1. UUID Migration Workflow
- **Trigger**: Application initialization (`RegistryDB` instantiation).
- **Process**:
  1. Query all existing records in `registry` table.
  2. For any record missing a `UUID`, generate one deterministically using a SHA-256 hash of `f"{english_word}:{alien_word}"`.
  3. Update the record with the generated UUID, set `synced = 0`, and set `updated_at` to the current UTC timestamp.
  4. Ensure schema is updated to support these new columns.

## 2. Mock Cloud Sync Loop
- **Trigger**: Manual trigger via UI (`SyncButton`) or automatic retry on failure.
- **Process (Push)**:
  1. `SyncService` queries `RegistryDB` for all records where `synced = 0`.
  2. For each record, read the corresponding embeddings from `VectorDB`.
  3. Attempt to write to the mock cloud storage (local JSON file `mock_supabase_bucket.json`).
  4. **Resiliency Policy**: If the mock cloud write fails (simulated network error), catch the exception, leave `synced = 0`, and return an error state so the UI can notify the user. The system will retry the next time the sync loop is triggered.
  5. On success, update the local SQLite record to `synced = 1`.
- **Process (Pull & Conflict Resolution)**:
  1. `SyncService` reads the mock cloud JSON.
  2. Compare cloud UUIDs with local UUIDs.
  3. **Cloud Authority Policy**: If a UUID exists in the cloud but differs from the local DB, the cloud version *always* overwrites the local DB and ChromaDB embeddings.
