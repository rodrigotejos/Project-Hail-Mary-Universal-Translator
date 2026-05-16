import numpy as np
import os
from typing import Optional, Tuple, List
from .audio_process import AudioProcessor
from .stt_manager import STTManager
from database.registry import TranslatorDB

class UniversalTranslator:
    def __init__(self, model_size: str = "small", device: str = "cpu"):
        self.audio_processor = AudioProcessor()
        self.stt_manager = STTManager(model_size=model_size, device=device)
        self.db = TranslatorDB()
        self.target_language = "clingo" # Idioma alienígena padrão
        
    def listen_and_transcribe(self, duration: float = 3.0) -> str:
        """Grava áudio e transcreve para texto usando Whisper"""
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
        
        # 3. Registra no banco de dados SQLite
        self.db.add_word(target_lang, human_word, filepath)
        
        return filepath

    def translate_alien_audio(self, audio: np.ndarray) -> Optional[str]:
        """
        Recebe um som alienígena e tenta identificar qual palavra humana ele representa
        comparando com o banco de dados de áudios conhecidos.
        """
        match = self.audio_processor.find_best_match(audio, self.target_language)
        if match:
            word, confidence = match
            print(f"Match encontrado: {word} (Confiança: {confidence:.2f})")
            return word
        return None
