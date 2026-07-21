# Integration Test Instructions - Unit 2

## Purpose
Validate the interaction between `TranslatorDB` (SQLAlchemy SQLite) and `MockSupabaseSync` (Local JSON Mock Bucket).

## Test Scenarios

### Scenario 1: Local to Cloud Sync
- **Description**: Add new vocabulary word locally and trigger `sync_all()`.
- **Expected Result**: Record is pushed to `mock_supabase_bucket.json` and local `synced` flag is updated to `1`.

### Scenario 2: Cloud Authority Conflict Resolution
- **Description**: Modify a record in `mock_supabase_bucket.json` and trigger `sync_all()`.
- **Expected Result**: Local database record is overwritten with cloud values to enforce Cloud Authority.

## Execution Command
```bash
python -m pytest tests/test_sync_service.py -k test_retry_manager_resiliency
```
