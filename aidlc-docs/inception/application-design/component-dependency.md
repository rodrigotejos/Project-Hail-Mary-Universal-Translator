# Component Dependencies

## Dependency Matrix

```mermaid
graph TD
    subgraph UI ["Flet UI Layer (src/ui/)"]
        App[app.py]
        LP[LearningPanel]
        CP[ConversationPanel]
        SB[SyncButton]
        App --> LP
        App --> CP
        App --> SB
    end

    subgraph Service ["Service Layer (src/services/)"]
        SS[SyncService]
    end

    subgraph Engine ["Engine Layer (src/engine/)"]
        TE[TranslatorEngine]
        AM[AudioManager]
    end

    subgraph Database ["Database Layer (src/database/)"]
        RD[(RegistryDB)]
        VD[(VectorDB)]
    end

    SB --> SS
    SS --> RD
    SS --> VD
    
    LP --> AM
    LP --> RD
    LP --> VD
    
    App --> TE
    TE -- "Asyncio.Queue" --> CP
    TE --> RD
    TE --> VD
```

## Communication Patterns
1. **User Input -> Sync**: Synchronous call from UI to `SyncService`. The UI will display a loading spinner while awaiting the service return.
2. **Microphone -> Engine -> UI**: The `TranslatorEngine` runs continuously in a background thread. It pushes `(text, missing_words)` tuples into an `asyncio.Queue`. The `app.py` runs an async loop checking this queue, triggering UI state updates on `ConversationPanel` when new data arrives. This prevents the STT processing from blocking the UI rendering thread.
