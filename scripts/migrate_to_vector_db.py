"""
Script to migrate existing audio files to ChromaDB vector database.
"""
import os
import sys

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine.translator import UniversalTranslator  # pylint: disable=wrong-import-position

def main():
    """Main execution function for the migration process."""
    print("=== MIGRANDO BANCO DE DADOS PARA CHROMADB (BUSCA VETORIAL) ===")

    # Inicializa o tradutor
    translator = UniversalTranslator()

    base_path = "linguagens"
    if not os.path.exists(base_path):
        print("Pasta 'linguagens' não encontrada. Nada para migrar.")
        return

    count = 0
    # Percorre as pastas de idiomas
    for lang_name in os.listdir(base_path):
        lang_path = os.path.join(base_path, lang_name)

        if os.path.isdir(lang_path):
            print(f"\nProcessando idioma: {lang_name.upper()}")

            # Percorre os arquivos .wav
            for filename in os.listdir(lang_path):
                if filename.endswith(".wav"):
                    word = os.path.splitext(filename)[0]
                    filepath = os.path.join(lang_path, filename)

                    try:
                        # 1. Carrega o áudio
                        audio, _sr = translator.audio_processor.load_audio(filepath)

                        # 2. Extrai a assinatura (embedding)
                        signature = translator.audio_processor.extract_features(audio)

                        # 3. Adiciona ao ChromaDB
                        translator.vdb.add_audio_signature(
                            word=word,
                            language=lang_name,
                            embedding=signature.tolist(),
                            audio_path=filepath
                        )

                        # 4. Garante que também esteja no SQLite
                        translator.db.add_word(lang_name, word, filepath)

                        print(f"  [OK] {word} migrado.")
                        count += 1

                    except Exception as e:  # pylint: disable=broad-exception-caught
                        print(f"  [ERRO] Falha ao migrar {filename}: {e}")

    print("\n" + "="*50)
    print(f"MIGRAÇÃO CONCLUÍDA! {count} palavras cadastradas no ChromaDB.")
    print("="*50)

if __name__ == "__main__":
    main()
