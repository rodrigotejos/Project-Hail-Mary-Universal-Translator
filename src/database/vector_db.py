"""
Vector database for audio embeddings using ChromaDB.
"""
import os
from typing import Optional, List, Dict, Any

import chromadb


class VectorDB:
    """Class for interacting with the ChromaDB vector database."""
    def __init__(self, db_path="src/database/chroma_db"):
        # Garante que o diretório existe
        os.makedirs(db_path, exist_ok=True)

        # Inicializa o cliente ChromaDB (Local Persistente)
        self.client = chromadb.PersistentClient(path=db_path)

        # Cria ou obtém a coleção de áudios
        # Usamos L2 (Euclidean distance) ou Cosine para comparar vetores de áudio
        self.collection = self.client.get_or_create_collection(
            name="alien_vocabulary",
            metadata={"hnsw:space": "cosine"}
        )

    def add_audio_signature(
        self, word: str, language: str, embedding: List[float], audio_path: str
    ):
        """
        Adiciona a assinatura de áudio ao banco vetorial.
        """
        # O ID deve ser único, então usamos idioma + palavra
        id_key = f"{language}_{word.upper()}"

        self.collection.upsert(
            ids=[id_key],
            embeddings=[embedding],
            metadatas=[{
                "word": word.upper(),
                "language": language,
                "audio_path": audio_path
            }]
        )
        print(f"[VectorDB] Assinatura de '{word}' salva no ChromaDB.")

    def search_similar_audio(
        self, query_embedding: List[float], language: str, threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Busca o áudio mais parecido no banco vetorial.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            where={"language": language}
        )

        if not results['ids'] or not results['ids'][0]:
            return None

        # O ChromaDB retorna distâncias. No modo 'cosine',
        # a distância 0 é identidade e 2 é oposto.
        # Similaridade = 1 - (distância / 2) ou similar dependendo da config.
        # Vamos usar a distância direta para o threshold.
        distance = results['distances'][0][0]
        similarity = 1 - distance # Simplificação para cosine no Chroma

        if similarity >= threshold:
            return {
                "word": results['metadatas'][0][0]['word'],
                "similarity": similarity,
                "audio_path": results['metadatas'][0][0]['audio_path']
            }

        return None
