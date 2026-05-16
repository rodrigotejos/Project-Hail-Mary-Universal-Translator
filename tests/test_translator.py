import pytest
import numpy as np
import os
import sys

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.translator import UniversalTranslator

@pytest.fixture
def translator():
    # Usando modelo 'tiny' para o teste ser mais rápido
    return UniversalTranslator(model_size="tiny", device="cpu")

def test_translator_initialization(translator):
    assert translator.stt_manager is not None
    assert translator.audio_processor is not None

def test_alien_audio_recognition_real_flow(tmp_path, translator):
    """Teste de fluxo real: salva um áudio e tenta reconhecê-lo como tradutor"""
    db_path = tmp_path / "linguagens"
    db_path.mkdir()
    translator.audio_processor.audio_database_path = str(db_path)
    translator.target_language = "clingo"
    
    # 1. Cria um som 'alienígena' (onda senoidal)
    t = np.linspace(0, 0.5, 16000)
    audio_data = np.sin(2 * np.pi * 500 * t).astype(np.float32)
    
    # 2. Salva como se fosse a palavra "FOME" em clingo
    translator.audio_processor.save_audio(audio_data, "FOME", "clingo")
    
    # 3. O tradutor ouve o mesmo som e deve reconhecer a palavra
    result = translator.translate_alien_audio(audio_data)
    
    assert result == "FOME"

def test_whisper_integration_simple(translator):
    """Verifica se o Whisper consegue processar um array numpy sem erro"""
    # Áudio de 1 segundo de silêncio (com um pouco de ruído branco)
    audio = np.random.uniform(-0.01, 0.01, 16000).astype(np.float32)
    
    # Não esperamos uma transcrição específica de um ruído, 
    # apenas que o método não lance exceção e retorne uma string.
    text = translator.stt_manager.transcribe(audio)
    assert isinstance(text, str)

if __name__ == "__main__":
    pytest.main([__file__])
