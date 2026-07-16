# Domain Entities - Unit 2

## Entity: `VocabularyRecord` (Local SQLite)
- `id`: Integer (Primary Key, Auto-increment - Legacy)
- `uuid`: String (Primary Key for Sync - Unique constraint)
- `english_word`: String
- `alien_word`: String
- `audio_path`: String
- `synced`: Integer (Boolean: 0 = False, 1 = True)
- `updated_at`: String (ISO 8601 Timestamp)

## Entity: `CloudVocabulary` (Mock Supabase JSON)
- `uuid`: String
- `english_word`: String
- `alien_word`: String
- `vector_embedding`: List[Float] (The actual float array from ChromaDB)
- `updated_at`: String (ISO 8601 Timestamp)

## Value Object: `SyncResult`
- `success`: Boolean (True if sync finished without critical errors)
- `records_pushed`: Integer
- `records_pulled`: Integer
- `error_message`: String (Optional, contains error details if `success` is False)
