# NFR Design Plan - Unit 2 (Mock Sync Service & DB Modifications)

## NFR Design Artifacts
- [x] Generate `aidlc-docs/construction/unit2/nfr-design/nfr-design-patterns.md`
- [x] Generate `aidlc-docs/construction/unit2/nfr-design/logical-components.md`

## Clarification Questions

To accurately design the non-functional components (Security, Resiliency, Property-Based Testing) for Unit 2, please answer the following questions. Provide your answers directly after each `[Answer]:` tag.

### 1. Resilience Patterns (Retry Policy)
We defined that on a sync failure, we notify the user and keep `synced=0`. Should the system automatically retry in the background using an Exponential Backoff algorithm, or strictly wait for the user to manually click the "Sync" button again?
A) **Exponential Backoff**: Implement a background retry loop (e.g., 2s, 4s, 8s) for a set number of attempts.
B) **Manual Only**: Fail fast and only retry when the user manually triggers the sync again.
X) Other (please describe after [Answer]: tag below)

[Answer]: a

### 2. Security Patterns (Local Database)
To enforce the Security Baseline during the UUID migration and Sync, how should we construct the local SQLite queries?
A) **Strict Parameterization**: Continue using raw SQL but enforce strict `?` parameterization for all inputs (fastest for this brownfield project).
B) **ORM Adoption**: Migrate the database interaction to an ORM (like SQLAlchemy) for maximum safety, even if it adds overhead.
X) Other (please describe after [Answer]: tag below)

[Answer]: b

### 3. Property-Based Testing Strategy
To satisfy the Property-Based Testing requirement for the `SyncService`, what boundaries should we fuzz?
A) **Data Structure Fuzzing**: Focus on fuzzing the text fields (`english_word`, `alien_word`) with extreme edge cases (e.g., max length, emojis, malformed characters) to ensure the UUID hash and JSON sync don't break.
B) **Network State Fuzzing**: Focus on fuzzing the "mock network" state (randomly alternating between success, timeout, and IOErrors) to test the resiliency logic.
C) **Both A and B**.
X) Other (please describe after [Answer]: tag below)

[Answer]: c
