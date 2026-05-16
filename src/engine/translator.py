"""
Universal Translator engine tying together audio processing, STT, and vector database.
"""
from typing import Optional, Tuple

import numpy as np

from database.registry import TranslatorDB
from database.vector_db import VectorDB

from .audio_process import AudioProcessor
from .stt_manager import STTManager

class UniversalTranslator:
    """Core translator class connecting all components."""
    def __init__(self, model_size: str = "small", device: str = "cpu", load_stt: bool = True):
        self.audio_processor = AudioProcessor()
        self.stt_manager = STTManager(model_size=model_size, device=device) if load_stt else None
        self.db = TranslatorDB()
        self.vdb = VectorDB()
        self.target_language = "clingo" # Idioma alienígena padrão

    def listen_and_transcribe(self, duration: float = 3.0) -> str:
        """Grava áudio e transcreve para texto usando Whisper"""
        if not self.stt_manager:
            raise RuntimeError("Módulo Whisper (STT) não foi carregado nesta instância.")
        print("Aguardando fala...")
        audio = self.audio_processor.record_audio(duration=duration)
        text = self.stt_manager.transcribe(audio)
        return text

    def process_speech_to_alien(self, audio: np.ndarray) -> Tuple[str, Optional[str]]:
        """
        Recebe áudio humano, transcreve e tenta encontrar a 'tradução'
        no banco de dados de sons alienígenas.
        """
        # 1. Transcrever fala humana
        human_text = self.stt_manager.transcribe(audio)
        human_text = human_text.strip().upper()

        if not human_text:
            return "", None

        # 2. Tenta encontrar o som alienígena correspondente no banco
        # (Nesta fase, a tradução é baseada no nome do arquivo salvo)
        match = self.audio_processor.find_best_match(audio, self.target_language)

        alien_word = match[0] if match else None
        return human_text, alien_word

    def learn_word(self, human_word: str, duration: float = 3.0, language: str = None) -> str:
        """
        Grava um áudio para uma palavra humana e salva no banco de dados.
        """
        target_lang = language or self.target_language

        # 1. Grava o áudio do "alienígena" ou do novo idioma
        print(f"Gravando som para '{human_word}' em '{target_lang}'...")
        audio = self.audio_processor.record_audio(duration=duration)

        # 2. Salva o arquivo físico (.wav)
        filepath = self.audio_processor.save_audio(audio, human_word, target_lang)

        # 3. Registra no banco de dados SQLite (Metadados)
        self.db.add_word(target_lang, human_word, filepath)

        # 4. Registra no banco VETORIAL (ChromaDB) para buscas rápidas
        signature = self.audio_processor.extract_features(audio)
        self.vdb.add_audio_signature(
            word=human_word,
            language=target_lang,
            embedding=signature.tolist(),
            audio_path=filepath
        )

        return filepath

    def translate_alien_audio(self, audio: np.ndarray) -> Optional[str]:
        """
        Recebe um som alienígena e tenta identificar qual palavra humana ele representa
        usando a busca vetorial do ChromaDB.
        """
        # Extrai a assinatura do áudio atual
        signature = self.audio_processor.extract_features(audio)

        # Busca no banco vetorial (com threshold 0.0 para ver o melhor resultado)
        match = self.vdb.search_similar_audio(
            query_embedding=signature.tolist(),
            language=self.target_language,
            threshold=0.0 # Pegamos o melhor, independente da pontuação
        )

        if match:
            word = match['word']
            confidence = match['similarity']

            if confidence >= 0.68: # Limiar restaurado para Espectrograma de 1024D
                print(f"[VectorDB] Match encontrado: {word} (Similaridade: {confidence:.2f})")
                return word

            print(
                f"[VectorDB] Candidato mais próximo: {word} "
                f"(Similaridade: {confidence:.2f} - ABAIXO DO LIMIAR)"
            )

        print("[VectorDB] Nenhuma palavra com similaridade mínima encontrada.")
        return None
