import pytest
import numpy as np
import os
import sys
from unittest.mock import MagicMock, patch

# Adiciona a raiz do projeto ao PYTHONPATH para permitir a importação de 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.audio_process import AudioProcessor

@pytest.fixture
def audio_processor():
    return AudioProcessor(sample_rate=22050)

def test_init(audio_processor):
    assert audio_processor.sample_rate == 22050
    assert audio_processor.audio_database_path == "linguagens"

@patch('sounddevice.rec')
@patch('sounddevice.wait')
def test_record_audio(mock_wait, mock_rec, audio_processor):
    duration = 1.0
    expected_shape = (int(duration * audio_processor.sample_rate), 1)
    mock_rec.return_value = np.zeros(expected_shape, dtype='float32')
    
    audio = audio_processor.record_audio(duration=duration)
    
    mock_rec.assert_called_once()
    mock_wait.assert_called_once()
    assert isinstance(audio, np.ndarray)
    assert audio.ndim == 1

@patch('librosa.feature.mfcc')
def test_extract_features(mock_mfcc, audio_processor):
    # Mock MFCC output: 13 rows (n_mfcc), 10 columns (time steps)
    mock_mfcc.return_value = np.random.rand(13, 10)
    dummy_audio = np.random.rand(22050)
    
    features = audio_processor.extract_features(dummy_audio)
    
    assert features.shape == (13,)
    assert isinstance(features, np.ndarray)

@patch('os.makedirs')
@patch('scipy.io.wavfile.write')
def test_save_audio(mock_wav_write, mock_makedirs, audio_processor):
    dummy_audio = np.random.rand(22050)
    filename = "test_word"
    language = "rock"
    
    filepath = audio_processor.save_audio(dummy_audio, filename, language)
    
    expected_path = os.path.join("linguagens", language, f"{filename}.wav")
    assert filepath == expected_path
    mock_makedirs.assert_called_with(os.path.join("linguagens", language), exist_ok=True)
    mock_wav_write.assert_called_once()

@patch('librosa.load')
def test_load_audio(mock_load, audio_processor):
    mock_load.return_value = (np.random.rand(22050), 22050)
    path = "dummy/path.wav"
    
    audio, sr = audio_processor.load_audio(path)
    
    mock_load.assert_called_with(path, sr=audio_processor.sample_rate)
    assert sr == 22050
    assert len(audio) == 22050

def test_compare_audio(audio_processor):
    # Mocking extract_features within the class
    with patch.object(AudioProcessor, 'extract_features') as mock_extract:
        # Return same features for both
        feat = np.array([1.0, 0.0, 0.0])
        mock_extract.return_value = feat
        
        sim = audio_processor.compare_audio(np.zeros(10), np.zeros(10))
        
        assert sim == pytest.approx(1.0)
        assert mock_extract.call_count == 2

@patch('os.path.exists')
@patch('os.listdir')
def test_find_best_match(mock_listdir, mock_exists, audio_processor):
    mock_exists.return_value = True
    mock_listdir.return_value = ["word1.wav", "word2.wav"]
    
    query_audio = np.zeros(10)
    
    with patch.object(AudioProcessor, 'load_audio') as mock_load:
        with patch.object(AudioProcessor, 'extract_features') as mock_extract:
            # Word1 has high similarity, Word2 has low
            # query_features will be returned first call to extract_features in find_best_match
            # db_features for word1 and word2 will follow
            mock_extract.side_effect = [
                np.array([1, 0]), # query
                np.array([1, 0]), # word1 (exact match)
                np.array([0, 1])  # word2 (orthogonal)
            ]
            mock_load.return_value = (np.zeros(10), 22050)
            
            result = audio_processor.find_best_match(query_audio, "rock", threshold=0.5)
            
            assert result is not None
            assert result[0] == "word1"
            assert result[1] == pytest.approx(1.0)

def test_real_file_interaction(tmp_path, audio_processor):
    """Teste de integração: salva e carrega arquivos reais"""
    # Configura um diretório temporário para o banco de dados
    db_path = tmp_path / "linguagens"
    db_path.mkdir()
    audio_processor.audio_database_path = str(db_path)
    
    # Cria dois sons diferentes (frequências diferentes)
    t = np.linspace(0, 1.0, audio_processor.sample_rate)
    audio_word1 = np.sin(2 * np.pi * 440 * t).astype(np.float32) # Tom de 440Hz
    audio_word2 = np.sin(2 * np.pi * 880 * t).astype(np.float32) # Tom de 880Hz
    
    # Salva no "banco de dados" temporário
    audio_processor.save_audio(audio_word1, "la", "rock")
    audio_processor.save_audio(audio_word2, "la_agudo", "rock")
    
    # Tenta encontrar o "la" passando o áudio original
    match = audio_processor.find_best_match(audio_word1, "rock", threshold=0.8)
    
    assert match is not None
    assert match[0] == "la"
    assert match[1] > 0.9 # Deve ser quase 1.0

if __name__ == "__main__":
    pytest.main([__file__])
