"""
Script to list contents of the vector database.
"""
import os
import sys

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from database.vector_db import VectorDB  # pylint: disable=wrong-import-position

def main():
    """Main execution function to explore the vector database."""
    print("=== EXPLORADOR DE BANCO VETORIAL (CHROMADB) ===")

    vdb = VectorDB()

    # Busca todos os itens da coleção
    results = vdb.collection.get(
        include=["metadatas", "embeddings"]
    )

    ids = results['ids']
    metadatas = results['metadatas']
    embeddings = results['embeddings']

    if not ids:
        print("O banco vetorial está vazio.")
        return

    print(f"\nTotal de registros: {len(ids)}")
    print(f"{'ID (Chroma)':<25} | {'PALAVRA':<15} | {'IDIOMA':<10} | {'VETOR (Início)'}")
    print("-" * 100)

    for i, _id in enumerate(ids):
        meta = metadatas[i]
        # Mostra apenas os 3 primeiros números do vetor para não encher a tela
        vector_snippet = str([round(x, 4) for x in embeddings[i][:3]]) + "..."

        print(f"{_id:<25} | {meta['word']:<15} | {meta['language']:<10} | {vector_snippet}")

    print("-" * 100)
    print("Busca vetorial pronta para uso!")

if __name__ == "__main__":
    main()
