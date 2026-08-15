"""
Universal Translator engine tying together audio processing, STT, and vector database.
Hardened with input validation, path resolution, and error resilience.
"""
import os
import sys
from typing import Optional, Tuple

import numpy as np

try:
    from src.database.registry import TranslatorDB
    from src.database.vector_db import VectorDB
    from src.security_utils import sanitize_identifier, sanitize_word_key, is_safe_path
except ImportError:
    from database.registry import TranslatorDB
    from database.vector_db import VectorDB
    from security_utils import sanitize_identifier, sanitize_word_key, is_safe_path

from .audio_process import AudioProcessor
from .stt_manager import STTManager


class UniversalTranslator:
    """Core translator class connecting all components with security checks."""
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        load_stt: bool = True,
        db_path: Optional[str] = None,
        vector_db_path: Optional[str] = None
    ):
        self.audio_processor = AudioProcessor()
        self.stt_manager = STTManager(model_size=model_size, device=device) if load_stt else None
        self.db = TranslatorDB(db_path) if db_path else TranslatorDB()
        self.vdb = VectorDB(vector_db_path) if vector_db_path else VectorDB()
        self.target_language = "clingo"

    def listen_and_transcribe(self, duration: float = 3.0) -> str:
        """Grava áudio e transcreve para texto usando Whisper"""
        if not self.stt_manager:
            raise RuntimeError("Módulo Whisper (STT) não foi carregado nesta instância.")
        bounded_duration = max(0.5, min(duration, 30.0))
        print("Aguardando fala...")
        audio = self.audio_processor.record_audio(duration=bounded_duration)
        text = self.stt_manager.transcribe(audio)
        return text

    def process_speech_to_alien(self, audio: np.ndarray) -> Tuple[str, Optional[str]]:
        """
        Recebe áudio humano, transcreve e tenta encontrar a tradução.
        """
        if self.stt_manager:
            human_text = self.stt_manager.transcribe(audio)
            try:
                human_text = sanitize_word_key(human_text)
            except ValueError:
                human_text = ""
        else:
            human_text = ""

        if not human_text:
            return "", None

        match = self.audio_processor.find_best_match(audio, self.target_language)
        alien_word = match[0] if match else None
        return human_text, alien_word

    def learn_word(self, human_word: str, duration: float = 3.0, language: str = None) -> str:
        """
        Grava um áudio para uma palavra humana e salva no banco de dados com segurança.
        """
        target_lang = sanitize_identifier(language or self.target_language)
        clean_word = sanitize_word_key(human_word)

        # 1. Grava áudio
        bounded_duration = max(0.5, min(duration, 30.0))
        print(f"Gravando som para '{clean_word}' em '{target_lang}'...")
        audio = self.audio_processor.record_audio(duration=bounded_duration)

        # 2. Salva arquivo WAV seguro
        filepath = self.audio_processor.save_audio(audio, clean_word, target_lang)

        # 3. Registra no SQLite
        self.db.add_word(target_lang, clean_word, filepath)

        # 4. Registra no ChromaDB
        signature = self.audio_processor.extract_features(audio)
        self.vdb.add_audio_signature(
            word=clean_word,
            language=target_lang,
            embedding=signature.tolist(),
            audio_path=filepath
        )

        # 5. Aciona o Treinamento Siames com caminho absoluto validado
        print("\n[SISTEMA] Verificando necessidade de alinhamento Siames interespécies...")
        import subprocess
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            script_path = os.path.join(project_root, "scripts", "train_siamese.py")
            if is_safe_path(project_root, script_path) and os.path.exists(script_path):
                subprocess.run([sys.executable, script_path], check=True, timeout=60)
        except Exception as e:
            print(f"[AVISO] Treinamento Siamês postergado: {e}")

        return filepath

    def translate_alien_audio(self, audio: np.ndarray) -> Optional[str]:
        """
        Recebe som alienígena e identifica a palavra usando busca vetorial.
        """
        signature = self.audio_processor.extract_features(audio)
        match = self.vdb.search_similar_audio(
            query_embedding=signature.tolist(),
            language=self.target_language,
            threshold=0.0
        )

        if match:
            word = match['word']
            confidence = match['similarity']
            if confidence >= 0.68:
                print(f"[VectorDB] Match encontrado: {word} (Similaridade: {confidence:.2f})")
                return word
            print(f"[VectorDB] Candidato mais próximo: {word} (Similaridade: {confidence:.2f} - ABAIXO DO LIMIAR)")

        print("[VectorDB] Nenhuma palavra com similaridade mínima encontrada.")
        return None
