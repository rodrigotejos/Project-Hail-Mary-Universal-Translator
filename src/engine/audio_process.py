import numpy as np
import librosa
import sounddevice as sd
import os
from typing import Optional, Tuple

class AudioProcessor:
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.audio_database_path = "linguagens"
    
    def record_audio(self, duration: float = 3.0) -> np.ndarray:
        """Record audio from microphone"""
        print("Gravando áudio...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()  # Wait until recording is finished
        print("Gravação concluída.")
        return audio.flatten()
    
    def extract_features(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCC features from audio"""
        # Compute MFCCs
        mfccs = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=13
        )
        # Return mean of MFCCs across time
        return np.mean(mfccs.T, axis=0)
    
    def save_audio(self, audio: np.ndarray, filename: str, language: str) -> str:
        """Save audio file to language directory"""
        # Create language directory if it doesn't exist
        lang_path = os.path.join(self.audio_database_path, language)
        os.makedirs(lang_path, exist_ok=True)
        
        # Save as WAV file
        filepath = os.path.join(lang_path, f"{filename}.wav")
        # Convert float32 to int16 for WAV file
        audio_int16 = (audio * 32767).astype(np.int16)
        from scipy.io import wavfile
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
    
    def find_best_match(self, query_audio: np.ndarray, language: str, threshold: float = 0.7) -> Optional[Tuple[str, float]]:
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
                        best_match = (word, similarity)
                except Exception as e:
                    print(f"Erro ao processar {filename}: {e}")
                    continue
        
        return best_match
