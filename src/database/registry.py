"""
SQLite database registry for Universal Translator.
"""
import sqlite3
import os
from typing import List, Optional, Tuple

class TranslatorDB:
    """Class to manage SQLite database operations for the translator."""
    def __init__(self, db_path="src/database/registry.db"):
        # Garante que o diretório do banco existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Create necessary tables if they do not exist."""
        cursor = self.conn.cursor()
        # Tabela de Idiomas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        # Tabela de Dicionário (Mapeia palavra humana -> áudio alienígena)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dictionary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_id INTEGER,
                word_key TEXT NOT NULL,
                audio_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(language_id) REFERENCES languages(id),
                UNIQUE(language_id, word_key)
            )
        """)
        self.conn.commit()

    def get_or_create_language(self, name: str) -> int:
        """Get or create a language ID by name."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO languages (name) VALUES (?)", (name.lower(),))
        self.conn.commit()
        cursor.execute("SELECT id FROM languages WHERE name = ?", (name.lower(),))
        return cursor.fetchone()[0]

    def add_word(self, language_name: str, word: str, audio_path: str):
        """Adiciona ou atualiza uma palavra no dicionário"""
        lang_id = self.get_or_create_language(language_name)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO dictionary (language_id, word_key, audio_path)
            VALUES (?, ?, ?)
        """, (lang_id, word.upper(), audio_path))
        self.conn.commit()
        print(f"[DB] Palavra '{word}' salva para o idioma '{language_name}'")

    def get_word_audio(self, language_name: str, word: str) -> Optional[str]:
        """Busca o caminho do áudio de uma palavra"""
        lang_id = self.get_or_create_language(language_name)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT audio_path FROM dictionary 
            WHERE language_id = ? AND word_key = ?
        """, (lang_id, word.upper()))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_all_vocabulary(self, language_name: str) -> List[Tuple[str, str]]:
        """Retorna todas as palavras aprendidas de um idioma"""
        lang_id = self.get_or_create_language(language_name)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT word_key, audio_path FROM dictionary 
            WHERE language_id = ?
        """, (lang_id,))
        return cursor.fetchall()

    def close(self):
        """Close the database connection."""
        self.conn.close()
