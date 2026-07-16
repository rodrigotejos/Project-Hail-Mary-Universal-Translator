"""
SQLAlchemy database registry for Universal Translator.
"""
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import create_engine, inspect, Column, Integer, String, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class Language(Base):
    __tablename__ = 'languages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    
    words = relationship("Dictionary", back_populates="language")

class Dictionary(Base):
    __tablename__ = 'dictionary'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, unique=True, nullable=True) # Will be backfilled
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    word_key = Column(String, nullable=False)
    audio_path = Column(String, nullable=False)
    synced = Column(Integer, default=0)
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

    __table_args__ = (
        UniqueConstraint('language_id', 'word_key', name='uq_language_word'),
    )
    
    language = relationship("Language", back_populates="words")

class TranslatorDB:
    """Class to manage SQLAlchemy database operations for the translator."""
    
    def __init__(self, db_path="src/database/registry.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        # sqlite:/// requires absolute path or relative, 
        # but relative to the current working directory, it's sqlite:///src/database/registry.db
        # Let's ensure it's absolute
        abs_path = os.path.abspath(db_path)
        db_url = f"sqlite:///{abs_path}"
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        self._ensure_schema_and_migrate()

    def _ensure_schema_and_migrate(self):
        """Creates tables and runs the deterministic UUID migration for legacy data."""
        inspector = inspect(self.engine)
        if not inspector.has_table('dictionary'):
            Base.metadata.create_all(self.engine)
            return

        # If table exists, check for new columns (uuid, synced, updated_at)
        columns = [col['name'] for col in inspector.get_columns('dictionary')]
        with self.engine.connect() as conn:
            if 'uuid' not in columns:
                conn.execute(text("ALTER TABLE dictionary ADD COLUMN uuid VARCHAR UNIQUE"))
            if 'synced' not in columns:
                conn.execute(text("ALTER TABLE dictionary ADD COLUMN synced INTEGER DEFAULT 0"))
            if 'updated_at' not in columns:
                conn.execute(text("ALTER TABLE dictionary ADD COLUMN updated_at VARCHAR"))
            conn.commit()

        # Run migration logic
        with self.Session() as session:
            # Find records without UUID
            legacy_records = session.query(Dictionary).filter(Dictionary.uuid.is_(None)).all()
            for record in legacy_records:
                lang = session.query(Language).filter(Language.id == record.language_id).first()
                lang_name = lang.name if lang else "unknown"
                
                # Deterministic hash: SHA256 of english_word:alien_word
                # In this app, word_key is the human text. We don't store the exact "alien text" structurally here,
                # we just map it to the audio_path. So we hash word_key + lang_name
                raw_str = f"{record.word_key}:{lang_name}".encode('utf-8')
                new_uuid = hashlib.sha256(raw_str).hexdigest()
                
                record.uuid = new_uuid
                record.synced = 0
                record.updated_at = datetime.now(timezone.utc).isoformat()
            
            if legacy_records:
                session.commit()
                print(f"[DB] Migrated {len(legacy_records)} legacy records to UUIDs.")

    def get_or_create_language(self, session, name: str) -> int:
        """Get or create a language ID by name."""
        name = name.lower()
        lang = session.query(Language).filter(Language.name == name).first()
        if not lang:
            lang = Language(name=name)
            session.add(lang)
            session.commit()
        return lang.id

    def add_word(self, language_name: str, word: str, audio_path: str):
        """Adiciona ou atualiza uma palavra no dicionário"""
        with self.Session() as session:
            lang_id = self.get_or_create_language(session, language_name)
            word = word.upper()
            
            record = session.query(Dictionary).filter(
                Dictionary.language_id == lang_id,
                Dictionary.word_key == word
            ).first()
            
            raw_str = f"{word}:{language_name.lower()}".encode('utf-8')
            new_uuid = hashlib.sha256(raw_str).hexdigest()
            now_iso = datetime.now(timezone.utc).isoformat()

            if record:
                record.audio_path = audio_path
                record.synced = 0
                record.updated_at = now_iso
            else:
                record = Dictionary(
                    uuid=new_uuid,
                    language_id=lang_id,
                    word_key=word,
                    audio_path=audio_path,
                    synced=0,
                    updated_at=now_iso,
                    created_at=now_iso
                )
                session.add(record)
            
            session.commit()
            print(f"[DB] Palavra '{word}' salva para o idioma '{language_name}'")

    def get_word_audio(self, language_name: str, word: str) -> Optional[str]:
        """Busca o caminho do áudio de uma palavra"""
        with self.Session() as session:
            name = language_name.lower()
            lang = session.query(Language).filter(Language.name == name).first()
            if not lang:
                return None
            
            record = session.query(Dictionary).filter(
                Dictionary.language_id == lang.id,
                Dictionary.word_key == word.upper()
            ).first()
            
            return record.audio_path if record else None

    def get_all_vocabulary(self, language_name: str) -> List[Tuple[str, str]]:
        """Retorna todas as palavras aprendidas de um idioma"""
        with self.Session() as session:
            name = language_name.lower()
            lang = session.query(Language).filter(Language.name == name).first()
            if not lang:
                return []
            
            records = session.query(Dictionary).filter(Dictionary.language_id == lang.id).all()
            return [(r.word_key, r.audio_path) for r in records]

    def close(self):
        """Close the database connection (dispose engine)."""
        self.engine.dispose()
