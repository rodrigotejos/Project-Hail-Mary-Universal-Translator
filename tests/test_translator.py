"""
Tests for the Universal Translator engine.
"""
# pylint: disable=redefined-outer-name, missing-function-docstring
import os
import sys

import numpy as np
import pytest

# Adiciona a raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.translator import UniversalTranslator  # pylint: disable=wrong-import-position

@pytest.fixture
def translator(tmp_path):
    """Fixture providing an isolated instance of UniversalTranslator."""
    db_file = tmp_path / "registry.db"
    vdb_dir = tmp_path / "chroma_db"
    t = UniversalTranslator(
        model_size="tiny",
        device="cpu",
        db_path=str(db_file),
        vector_db_path=str(vdb_dir)
    )
    t.audio_processor.audio_database_path = str(tmp_path / "linguagens")
    return t

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
    filepath = translator.audio_processor.save_audio(audio_data, "FOME", "clingo")

    # 3. Adiciona a assinatura ao VectorDB
    signature = translator.audio_processor.extract_features(audio_data)
    translator.vdb.add_audio_signature(
        word="FOME",
        language="clingo",
        embedding=signature.tolist(),
        audio_path=filepath
    )

    # 4. O tradutor ouve o mesmo som e deve reconhecer a palavra
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


def test_listen_and_transcribe_flows(translator):
    """Test listen_and_transcribe with and without STT manager."""
    from unittest.mock import patch
    dummy_audio = np.zeros(16000, dtype=np.float32)

    with patch.object(translator.audio_processor, "record_audio", return_value=dummy_audio):
        with patch.object(translator.stt_manager, "transcribe", return_value="HELLO"):
            res = translator.listen_and_transcribe(duration=1.0)
            assert res == "HELLO"

    translator.stt_manager = None
    with pytest.raises(RuntimeError):
        translator.listen_and_transcribe()


def test_process_speech_to_alien_flows(translator):
    """Test process_speech_to_alien with valid and empty transcriptions."""
    from unittest.mock import patch
    dummy_audio = np.zeros(16000, dtype=np.float32)

    translator.stt_manager = None
    text, match = translator.process_speech_to_alien(dummy_audio)
    assert text == ""
    assert match is None

    from unittest.mock import MagicMock
    mock_stt = MagicMock()
    mock_stt.transcribe.return_value = "OLA"
    translator.stt_manager = mock_stt

    with patch.object(translator.audio_processor, "find_best_match", return_value=("CLINGO_OLA", 0.95)):
        human_text, alien_word = translator.process_speech_to_alien(dummy_audio)
        assert human_text == "OLA"
        assert alien_word == "CLINGO_OLA"


def test_learn_word_execution(tmp_path, translator):
    """Test learn_word method creates records in DB, VectorDB, and files."""
    from unittest.mock import patch
    dummy_audio = np.zeros(16000, dtype=np.float32)
    db_path = tmp_path / "linguagens"
    db_path.mkdir(exist_ok=True)
    translator.audio_processor.audio_database_path = str(db_path)

    with patch.object(translator.audio_processor, "record_audio", return_value=dummy_audio):
        with patch("subprocess.run") as mock_run:
            saved_path = translator.learn_word("AGUA", duration=1.0, language="clingo")
            assert os.path.exists(saved_path)
            # Verify registered in SQLite
            saved_audio = translator.db.get_word_audio("clingo", "AGUA")
            assert saved_audio == saved_path
            vocab = translator.db.get_all_vocabulary("clingo")
            assert any(word == "AGUA" for word, _ in vocab)


def test_translate_alien_audio_low_confidence(translator):
    """Verify that search matches below 0.68 similarity return None."""
    from unittest.mock import patch
    dummy_audio = np.zeros(16000, dtype=np.float32)

    with patch.object(translator.vdb, "search_similar_audio", return_value={"word": "FRIO", "similarity": 0.50}):
        res = translator.translate_alien_audio(dummy_audio)
        assert res is None

    with patch.object(translator.vdb, "search_similar_audio", return_value=None):
        res = translator.translate_alien_audio(dummy_audio)
        assert res is None


def test_vector_db_in_memory_fallback(tmp_path):
    """Verify VectorDB in-memory fallback search logic."""
    from src.database.vector_db import VectorDB
    vdb = VectorDB(str(tmp_path / "test_vdb"))
    vdb.collection = None  # Force in-memory fallback

    emb1 = [1.0] * 128
    vdb.add_audio_signature("LUZ", "clingo", emb1, "mock_path_1.wav")

    # Exact match query
    match = vdb.search_similar_audio(emb1, "clingo", threshold=0.9)
    assert match is not None
    assert match["word"] == "LUZ"

    # Orthogonal / different language query
    diff_match = vdb.search_similar_audio(emb1, "ingles", threshold=0.9)
    assert diff_match is None

    # Zero vector returns None
    zero_match = vdb.search_similar_audio([0.0] * 128, "clingo", threshold=0.1)
    assert zero_match is None


if __name__ == "__main__":
    pytest.main([__file__])
