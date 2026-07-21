# Business Logic Model - Unit 1 (UI & Flet Integration)

## UI & Sync Service Integration Flow

```
+------------------+         Sync Button Click         +-------------------+
|  Flet Main Page  |  ------------------------------>  |    UI Handler     |
|   (src/main.py)  |                                   |  (on_sync_click)  |
+------------------+                                   +-------------------+
        ^                                                        |
        |                                                        v
        | Show SnackBar                                +-------------------+
        +--------------------------------------------  |    SyncService    |
        |                                              |  (sync_all)       |
        | Updates Status Indicator                     +-------------------+
        | ("ONLINE" / "ERRO DE CONEXAO")                         |
        +--------------------------------------------------------+
```

## Workflows

### 1. Manual Cloud Sync Workflow
1. User clicks the `Sincronizar Nuvem` button in the header bar.
2. UI updates status text to `[Cloud] STATUS: SINCRONIZANDO...` and disables the sync button.
3. UI calls `SyncService.sync_all()`.
4. If `SyncResult.success` is `True`:
   - UI updates status text to `[Cloud] STATUS: ONLINE (Empurrados: X | Puxados: Y)`.
   - UI opens a green SnackBar: `"Sincronização concluída com sucesso!"`.
5. If `SyncResult.success` is `False`:
   - UI updates status text to `[Cloud] STATUS: FALHA NA SINCRONIZAÇÃO`.
   - UI opens a red SnackBar: `"Erro ao sincronizar com a nuvem: {error_message}"`.
6. UI re-enables the sync button.

### 2. Auto-Sync on Vocabulary Save Workflow
1. When a new word is saved via the Learning Module (`add_word`), the UI automatically invokes background sync.
2. Feedback is displayed via SnackBar without blocking the user input loop.
