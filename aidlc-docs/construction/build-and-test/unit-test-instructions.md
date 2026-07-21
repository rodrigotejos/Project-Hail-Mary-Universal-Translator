# Unit Test Execution - Unit 2

## Run Unit Tests

### 1. Execute All Unit Tests
```bash
python -m pytest tests/test_sync_service.py
```

### 2. Test Coverage & Strategy
- **Framework**: `pytest` + `hypothesis` (Property-Based Testing)
- **Target Coverage**:
  - Deterministic SHA-256 UUID hashing on string boundary extremes.
  - Resilience Circuit Breaker and Exponential Backoff under simulated IOError failures.
- **Expected Outcome**: All property-based fuzz tests pass across 50+ random inputs per test suite.
