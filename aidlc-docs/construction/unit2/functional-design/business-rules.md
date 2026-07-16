# Business Rules - Unit 2

## Rule 1: Deterministic UUIDs
- Legacy integer IDs must be maintained for backwards compatibility in SQLite, but all synchronization logic must strictly use the UUID string.
- UUID generation for existing data must be deterministic (hash of english and alien text) to prevent duplication if two local clients migrate the same foundational dataset independently.

## Rule 2: Cloud Authority over Local Data
- The mock cloud is considered the ultimate source of truth.
- In the event of a conflict (same UUID, different data), the local database is forcefully updated to match the cloud state. `updated_at` timestamps are ignored for conflict resolution purposes.

## Rule 3: Resiliency and User Notification
- Sync failures must not crash the application.
- The `SyncService` must catch any `IOError` or simulated network timeouts, preserve the `synced = 0` state, and return a `SyncResult(success=False, error_msg="...")` object.
- The UI layer (which calls the service) is responsible for interpreting this object and displaying a SnackBar to the user.

## Rule 4: Data Atomicity
- A sync operation for a single vocabulary word is only considered successful if *both* the `RegistryDB` (metadata) and `VectorDB` (ChromaDB embeddings) are successfully pushed to the cloud JSON structure.
- If one fails, the entire transaction for that word must be rolled back to `synced = 0`.
