"""
Vector database for audio embeddings using ChromaDB with built-in resilient fallback.
Hardened with embedding dimension validation, metadata sanitization, and graceful fallback.
"""
import os
import math
from typing import Optional, List, Dict, Any
import numpy as np

try:
    from src.security_utils import sanitize_identifier, sanitize_word_key
except ImportError:
    from security_utils import sanitize_identifier, sanitize_word_key

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorDB:
    """Class for interacting with vector embeddings using ChromaDB or resilient in-memory fallback."""
    def __init__(self, db_path: str = "src/database/chroma_db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(self.db_path, exist_ok=True)
        self.client = None
        self.collection = None
        self._in_memory_records: Dict[str, Dict[str, Any]] = {}

        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=self.db_path)
                self.collection = self.client.get_or_create_collection(
                    name="alien_vocabulary",
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"[VectorDB] Warning: ChromaDB initialization error: {e}")

    def _validate_embedding(self, embedding: List[float], expected_dim: int = 1024) -> List[float]:
        """Validates and cleans embedding vector against NaNs, Infs, and invalid dimensions."""
        if not isinstance(embedding, (list, tuple, np.ndarray)):
            raise ValueError("Embedding must be a list, tuple, or numpy array of numeric values.")

        clean_vector = []
        for val in embedding:
            if not isinstance(val, (int, float, np.floating, np.integer)) or math.isnan(val) or math.isinf(val):
                clean_vector.append(0.0)
            else:
                clean_vector.append(float(val))

        if len(clean_vector) == 0:
            clean_vector = [0.0] * expected_dim

        return clean_vector

    def add_audio_signature(
        self, word: str, language: str, embedding: List[float], audio_path: str
    ):
        """
        Adiciona a assinatura de áudio ao banco vetorial de forma sanitizada.
        """
        clean_lang = sanitize_identifier(language)
        clean_word = sanitize_word_key(word)
        clean_emb = self._validate_embedding(embedding)

        id_key = f"{clean_lang}_{clean_word}"

        # Store in fallback dictionary
        self._in_memory_records[id_key] = {
            "word": clean_word,
            "language": clean_lang,
            "embedding": clean_emb,
            "audio_path": str(audio_path)
        }

        if self.collection:
            self.collection.upsert(
                ids=[id_key],
                embeddings=[clean_emb],
                metadatas=[{
                    "word": clean_word,
                    "language": clean_lang,
                    "audio_path": str(audio_path)
                }]
            )
        print(f"[VectorDB] Assinatura de '{clean_word}' salva.")

    def search_similar_audio(
        self, query_embedding: List[float], language: str, threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Busca o áudio mais parecido no banco vetorial de forma segura.
        """
        clean_lang = sanitize_identifier(language)
        clean_emb = self._validate_embedding(query_embedding)

        if self.collection:
            try:
                results = self.collection.query(
                    query_embeddings=[clean_emb],
                    n_results=1,
                    where={"language": clean_lang}
                )

                if results.get('ids') and results['ids'][0]:
                    distance = results['distances'][0][0]
                    similarity = 1.0 - distance

                    if similarity >= threshold:
                        return {
                            "word": results['metadatas'][0][0]['word'],
                            "similarity": similarity,
                            "audio_path": results['metadatas'][0][0]['audio_path']
                        }
                    return None
            except Exception as e:
                print(f"[VectorDB] Chroma query error, falling back to memory: {e}")

        # In-memory cosine calculation fallback
        q_vec = np.array(clean_emb, dtype=np.float32)
        q_norm = float(np.linalg.norm(q_vec))
        if q_norm <= 1e-8:
            return None

        best_match = None
        best_sim = -1.0

        for record in self._in_memory_records.values():
            if record["language"] == clean_lang:
                rec_vec = np.array(record["embedding"], dtype=np.float32)
                rec_norm = float(np.linalg.norm(rec_vec))
                if rec_norm <= 1e-8:
                    continue

                sim = float(np.dot(q_vec, rec_vec) / (q_norm * rec_norm))
                if sim > best_sim and sim >= threshold:
                    best_sim = sim
                    best_match = {
                        "word": record["word"],
                        "similarity": sim,
                        "audio_path": record["audio_path"]
                    }

        return best_match
