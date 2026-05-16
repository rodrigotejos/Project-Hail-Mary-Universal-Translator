"""
Audio processing module for recording, manipulating and feature extraction.
"""
import os
from typing import Optional, Tuple

import numpy as np
import librosa
import sounddevice as sd
import scipy.ndimage
from scipy.io import wavfile

class AudioProcessor:
    """Processor for audio signals."""
    def __init__(self):
        # O Spectrograma 1024D trabalha bem com 22050Hz
        self.sample_rate = 22050
        self.channels = 1
        self.audio_database_path = "linguagens"

    def record_audio(self, duration: float = 3.0) -> np.ndarray:
        """Record audio from microphone"""
        print("Gravando áudio...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )
        sd.wait()  # Wait until recording is finished
        print("Gravação concluída.")
        return audio.flatten()

    def extract_features(self, audio: np.ndarray) -> np.ndarray: # pylint: disable=too-many-locals
        """Extract temporally-aware audio signature (Fixed-Size Mel-Spectrogram) with RMS Trim"""
        target_shape = (32, 32)
        vector_size = target_shape[0] * target_shape[1] # 1024

        if len(audio) == 0:
            return np.zeros(vector_size)

        # 1. Normalizar o volume para o máximo (ignora se você falou perto ou longe do mic)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val

        # 2. Corte Inteligente (RMS) para isolar EXATAMENTE a palavra e ignorar ruído de fundo
        rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
        threshold = np.max(rms) * 0.10 # O som deve ter pelo menos 10% do volume máximo
        active_frames = np.where(rms > threshold)[0]

        if len(active_frames) == 0:
            return np.zeros(vector_size) # Retorna zero se for só silêncio

        # Pega a palavra e adiciona uma gordurinha de 0.1s de cada lado para não cortar seco
        padding = int(0.1 * self.sample_rate)
        start_sample = max(0, active_frames[0] * 512 - padding)
        end_sample = min(len(audio), (active_frames[-1] + 1) * 512 + padding)

        audio = audio[start_sample:end_sample]

        # 3. Pré-ênfase
        audio = librosa.effects.preemphasis(audio)

        # 4. Gerar Espectrograma Mel
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=self.sample_rate,
            n_mels=target_shape[0]
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # --- FILTRO DE RUÍDO (NOISE GATE) ---
        noise_threshold = -35
        mel_spec_db[mel_spec_db < noise_threshold] = -80

        # 5. Redimensionar matematicamente o eixo do tempo para caber em 32 fatias
        time_bins = mel_spec_db.shape[1]

        if time_bins == 0:
            return np.zeros(vector_size)

        zoom_factor = target_shape[1] / time_bins
        resized_spec = scipy.ndimage.zoom(mel_spec_db, (1.0, zoom_factor))

        # 6. Transformar em vetor 1D e Padronizar
        vector_1d = resized_spec.flatten()
        vector_1d = (vector_1d - np.mean(vector_1d)) / (np.std(vector_1d) + 1e-8)

        # Normalização padrão para busca vetorial (Cosine Similarity)
        vector_1d = vector_1d / (np.linalg.norm(vector_1d) + 1e-8)

        return vector_1d

    def save_audio(self, audio: np.ndarray, filename: str, language: str) -> str:
        """Save audio file to language directory"""
        # Create language directory if it doesn't exist
        lang_path = os.path.join(self.audio_database_path, language)
        os.makedirs(lang_path, exist_ok=True)

        # Save as WAV file
        filepath = os.path.join(lang_path, f"{filename}.wav")
        # Convert float32 to int16 for WAV file
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(filepath, self.sample_rate, audio_int16)

        return filepath

    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load audio file"""
        return librosa.load(filepath, sr=self.sample_rate)

    def compare_audio(self, audio1: np.ndarray, audio2: np.ndarray) -> float:
        """Compare two audio signals using cosine similarity of MFCC features"""
        features1 = self.extract_features(audio1)
        features2 = self.extract_features(audio2)

        # Cosine similarity
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_best_match(
        self, query_audio: np.ndarray, language: str, threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
        """Find best matching word in language database"""
        lang_path = os.path.join(self.audio_database_path, language)
        if not os.path.exists(lang_path):
            return None

        best_match = None
        best_score = 0.0

        # Extract features from query audio
        query_features = self.extract_features(query_audio)

        # Check all audio files in language directory
        for filename in os.listdir(lang_path):
            if filename.endswith(".wav"):
                filepath = os.path.join(lang_path, filename)
                try:
                    audio, _ = self.load_audio(filepath)
                    # Extract features from database audio
                    db_features = self.extract_features(audio)

                    # Calculate similarity
                    similarity = np.dot(query_features, db_features) / (
                        np.linalg.norm(query_features) * np.linalg.norm(db_features)
                    )

                    if similarity > best_score and similarity > threshold:
                        best_score = similarity
                        # Remove .wav extension to get the word
                        word = os.path.splitext(filename)[0]
                        best_match = (word, float(similarity))
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Erro ao processar {filename}: {e}")
                    continue

        return best_match
