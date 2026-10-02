# API Documentation

## REST APIs
*No external REST APIs exposed by this application. It relies entirely on internal APIs and gRPC out to Modal.*

## Internal APIs
### `AudioProcess` (in `audio_process.py`)
- **Methods**: `trim_audio_rms(audio, threshold)`, `extract_mel_spectrogram(audio_path)`
- **Parameters**: `audio` (numpy array), `audio_path` (string)
- **Return Types**: Processed numpy arrays or tensors representing the audio waveform/spectrogram.

### `SiameseNet` (in `siamese_net.py`)
- **Methods**: `forward(x)`, `get_embedding(audio_tensor)`
- **Parameters**: `x` (PyTorch tensor)
- **Return Types**: 1024-dimensional normalized vector (PyTorch tensor).

### `VectorDB` (in `vector_db.py`)
- **Methods**: `add_embedding(id, vector, metadata)`, `query_similar(vector, k)`
- **Parameters**: `vector` (1024D list/array), `k` (int)
- **Return Types**: Dictionary of closest matches based on Cosine Distance.

## Data Models
### `AudioRegistry` (SQLite)
- **Fields**: `id` (PK), `word` (String), `language` (String), `file_path` (String)
- **Relationships**: N/A
- **Validation**: Enforces unique audio file paths.
