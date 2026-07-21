# Build Instructions - Unit 2

## Prerequisites
- **Build Tool**: Python 3.12+ / pip
- **Dependencies**: `sqlalchemy`, `hypothesis`, `pytest`
- **Environment Variables**: None required (uses local SQLite and local mock JSON)
- **System Requirements**: Windows/Linux/macOS

## Build Steps

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Verify Schema Migration
```bash
python -c "from src.database.registry import TranslatorDB; db = TranslatorDB(); db.close()"
```

### 3. Build Status
- **Expected Output**: Clean instantiation of SQLAlchemy models and automatic schema migration of legacy tables.
- **Build Artifacts**: `src/database/registry.db`
