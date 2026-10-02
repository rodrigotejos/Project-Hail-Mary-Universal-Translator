# System Architecture

## System Overview
The Universal Translator is a hybrid Local-First system. It orchestrates real-time audio capture, CPU-based speech transcription, vector storage, and an advanced acoustic Siamese Neural Network capable of computing similarities between completely different sound profiles. Training can be offloaded to serverless cloud GPUs.

## Architecture Diagram
```mermaid
graph TD
    subgraph Frontend
        FletUI[Flet UI Module - In Progress]
    end
    subgraph CLI Scripts
        Translate[translate_audio.py]
        Learn[learn_vocabulary.py]
        Train[train_siamese.py]
        Migrate[migrate_to_vector_db.py]
    end
    subgraph Core Engine
        Audio[audio_process.py\nRMS Trimming & Mel Pipeline]
        Model[siamese_net.py\nMobileNet/AST Triplet Loss]
        Cloud[cloud_train.py\nModal.com API]
        STT[stt_manager.py\nFaster-Whisper CPU]
        TransLogic[translator.py\nCore Logic]
    end
    subgraph Storage
        SQLite[(SQLite\nregistry.db)]
        Chroma[(ChromaDB\nVector Index)]
    end
    
    FletUI -.-> TransLogic
    Translate --> TransLogic
    Learn --> SQLite
    Learn --> Audio
    Train --> Model
    Train --> Cloud
    Migrate --> Model
    Migrate --> Chroma
    TransLogic --> STT
    TransLogic --> Audio
    TransLogic --> Chroma
```

## Component Descriptions
### `src/engine` (Core Engine)
- **Purpose**: Holds the entire deep learning and signal processing logic.
- **Responsibilities**: Audio processing (RMS trimming, spectrograms), training the Siamese model, communicating with the Modal cloud, running Faster-Whisper, and orchestrating the translation query.
- **Dependencies**: Librosa, PyTorch, Faster-Whisper, Modal.
- **Type**: Application/Model

### `src/database` (Storage)
- **Purpose**: Data layer for vector and relational indexing.
- **Responsibilities**: Storing audio mappings and performing high-speed cosine similarity searches.
- **Dependencies**: SQLite3, ChromaDB.
- **Type**: Application/Database

### `scripts` (CLI Executors)
- **Purpose**: Provides the executable points of entry.
- **Responsibilities**: Binding user actions to engine logic.
- **Dependencies**: `src` modules.
- **Type**: Application

## Data Flow
```mermaid
sequenceDiagram
    participant Mic as Microphone
    participant STT as Faster-Whisper
    participant Audio as RMS Trimmer
    participant DB as ChromaDB
    participant Screen as Interface
    Mic->>STT: Speak stream
    STT->>Audio: Text / Timestamp
    Audio->>Audio: Trim isolated audio
    Audio->>DB: Extract Vector & Cosine Search
    DB-->>Screen: Return closest match (Translation)
```

## Integration Points
- **External APIs**: Modal.com (for cloud GPU serverless training).
- **Databases**: Local SQLite, Local ChromaDB (future plan for Supabase sync).
- **Third-party Services**: AudioSet pre-trained weights (HuggingFace) for the AST backbone.

## Infrastructure Components
- **Deployment Model**: Local Python environment with optional serverless cloud bursting via Modal.
- **Networking**: Cloud training communicates via gRPC/HTTPS to Modal instances.
