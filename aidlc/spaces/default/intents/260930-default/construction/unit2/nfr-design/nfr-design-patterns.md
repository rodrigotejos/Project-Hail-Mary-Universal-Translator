# NFR Design Patterns - Unit 2

## 1. Resilience Patterns
- **Exponential Backoff Strategy**: 
  - The `SyncService` will implement a retry loop for network-related failures (IOError simulating the mock JSON write failure).
  - **Pattern**: Wait `2^c * base_delay` seconds between attempts (e.g., 2s, 4s, 8s).
  - **Circuit Breaker**: If max retries (e.g., 3) are exhausted, the circuit trips, the background task stops retrying, and an alert is definitively pushed to the UI to notify the user. The records remain `synced=0`.

## 2. Security Patterns
- **ORM Adoption (SQLAlchemy)**: 
  - Instead of raw SQLite queries (`cursor.execute("SELECT * FROM ...")`), the database access will be fully migrated to SQLAlchemy ORM models.
  - **Threat Mitigated**: Eliminates SQL Injection risks dynamically. Provides native, secure handling of the new UUID strings and handles type safety inherently.
  - **Migration Pattern**: The existing `RegistryDB` logic will be wrapped or completely replaced by SQLAlchemy session objects during the Code Generation phase.

## 3. Property-Based Testing Patterns
- **Hybrid Fuzzing Strategy (Hypothesis Library)**:
  - **Data Fuzzing**: Test the deterministic UUID hashing function by generating extreme text bounds (length up to 100,000 chars, complex Unicode, emojis) for the English and Alien words to ensure hash consistency and prevent crashes.
  - **State/Network Fuzzing**: Mock the `open()` call to the Supabase JSON bucket to randomly throw IOExceptions during the sync loop, proving that the Exponential Backoff gracefully recovers or trips the circuit without breaking the app state.
