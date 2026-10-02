# Functional Design Plan - Unit 2 (Mock Sync Service & DB Modifications)

## Functional Design Artifacts
- [x] Generate `aidlc-docs/construction/unit2/functional-design/business-logic-model.md`
- [x] Generate `aidlc-docs/construction/unit2/functional-design/business-rules.md`
- [x] Generate `aidlc-docs/construction/unit2/functional-design/domain-entities.md`

## Clarification Questions

To accurately design the business logic for Unit 2, please answer the following questions. Provide your answers directly after each `[Answer]:` tag.

### 1. Conflict Resolution (Last Write Wins)
If the local SQLite DB and the Mock Cloud JSON both have modifications for the same `UUID`, how should the `SyncService` resolve the conflict?
A) **Last Write Wins (LWW)**: Compare the `updated_at` timestamps. The most recent timestamp overwrites the older one.
B) **Cloud Authority**: The cloud version always overrides the local version to maintain a central source of truth.
X) Other (please describe after [Answer]: tag below)

[Answer]: b

### 2. UUID Generation for Existing Records (Migration)
When running the migration on the existing `registry.db`, how should we generate UUIDs for old records that only have integer IDs?
A) **Random UUID4**: Generate a random standard `uuid.uuid4()` for every existing record.
B) **Deterministic Hash**: Generate a UUID based on a hash of the english word + alien word. This prevents duplicates if two devices migrate the same initial dataset independently.
X) Other (please describe after [Answer]: tag below)

[Answer]: b

### 3. Sync Failure Handling (Resiliency)
Since we have the Resiliency Extension enabled, how should the UI react if the Mock Cloud (JSON file simulation) is "unreachable" (e.g. simulated network timeout)?
A) **Silent Retry**: Log the error, keep the records marked as `synced=0`, and silently try again next time without bothering the user.
B) **Alert User**: Throw a Flet SnackBar error immediately to inform the user that the sync failed.
X) Other (please describe after [Answer]: tag below)

[Answer]: both they try again but notfy the user.
