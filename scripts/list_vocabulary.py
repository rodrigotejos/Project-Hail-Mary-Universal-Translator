import os
import sys

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from database.registry import TranslatorDB

def main():
    db = TranslatorDB()
    
    # Busca todos os idiomas cadastrados
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM languages")
    languages = [row[0] for row in cursor.fetchall()]
    
    if not languages:
        print("Nenhum idioma ou palavra cadastrada ainda.")
        return

    print("=== DICIONÁRIO DO TRADUTOR UNIVERSAL ===")
    print(f"{'IDIOMA':<15} | {'PALAVRA':<20} | {'CAMINHO DO ÁUDIO'}")
    print("-" * 70)
    
    for lang in languages:
        vocab = db.get_all_vocabulary(lang)
        for word, path in vocab:
            print(f"{lang.upper():<15} | {word:<20} | {path}")
    
    print("-" * 70)
    db.close()

if __name__ == "__main__":
    main()
