"""
Audio processing module for recording, manipulating, and feature extraction.
Hardened with input validation, path traversal prevention, and resilience.
"""
import os
import sys
from typing import Optional, Tuple

import numpy as np
import librosa
import sounddevice as sd
from scipy.io import wavfile

# Safely import security utils
try:
    from src.security_utils import sanitize_identifier, sanitize_filename, is_safe_path, SecurityError
except ImportError:
    from security_utils import sanitize_identifier, sanitize_filename, is_safe_path, SecurityError


class AudioProcessor:
    """Processor for audio signals with security constraints and safe feature extraction."""
    def __init__(self, audio_database_path: str = "linguagens"):
        self.sample_rate = 22050
        self.channels = 1
        self.audio_database_path = audio_database_path
        self._model = None
        self._model_backbone = None

    def _validate_audio_input(self, audio: np.ndarray, max_duration_sec: float = 60.0) -> np.ndarray:
        """Validates, sanitizes, and bounds audio input to prevent DoS, NaNs, and memory exhaustion."""
        if not isinstance(audio, np.ndarray):
            try:
                audio = np.asarray(audio, dtype=np.float32)
            except Exception as ex:
                raise ValueError(f"Audio input cannot be converted to numpy array: {ex}") from ex

        if audio.ndim > 1:
            audio = audio.flatten()

        # Handle NaNs and Infs (CWE-369 / CWE-391)
        if not np.all(np.isfinite(audio)):
            audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)

        # Enforce maximum duration bounds to prevent DoS via unbounded memory (CWE-400)
        max_samples = int(max_duration_sec * self.sample_rate)
        if len(audio) > max_samples:
            audio = audio[:max_samples]

        return audio.astype(np.float32)

    def record_audio(self, duration: float = 3.0) -> np.ndarray:
        """Record audio from microphone with bounded duration."""
        bounded_duration = max(0.1, min(duration, 30.0))
        print(f"Gravando áudio ({bounded_duration}s)...")
        audio = sd.rec(
            int(bounded_duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32'
        )
        sd.wait()
        print("Gravação concluída.")
        return self._validate_audio_input(audio.flatten())

    def _fallback_mfcc_features(self, audio: np.ndarray, dim: int = 1024) -> np.ndarray:
        """
        Deterministic 1024D fallback feature extraction using MFCCs and spectral statistics
        when PyTorch / GPU is unavailable.
        """
        try:
            mfcc = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=32)
            spec_cent = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)
            spec_bw = librosa.feature.spectral_bandwidth(y=audio, sr=self.sample_rate)
            spec_roll = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)
            zcr = librosa.feature.zero_crossing_rate(audio)

            combined = np.concatenate([
                mfcc.flatten(),
                spec_cent.flatten(),
                spec_bw.flatten(),
                spec_roll.flatten(),
                zcr.flatten()
            ])

            if len(combined) >= dim:
                vec = combined[:dim]
            else:
                vec = np.pad(combined, (0, dim - len(combined)), mode='constant')

            norm = np.linalg.norm(vec)
            return (vec / norm).astype(np.float32) if norm > 0 else np.zeros(dim, dtype=np.float32)
        except Exception:
            return np.zeros(dim, dtype=np.float32)

    def extract_features(self, audio: np.ndarray) -> np.ndarray:
        """Extract temporally-aware audio signature (Siamese Network 1024D or robust fallback)."""
        # pylint: disable=import-outside-toplevel, too-many-locals
        audio = self._validate_audio_input(audio)

        if len(audio) == 0:
            return np.zeros(1024, dtype=np.float32)

        # 1. Normalizar o volume para o máximo de forma segura contra divisão por zero
        max_val = float(np.max(np.abs(audio)))
        if max_val > 1e-6:
            audio = audio / max_val

        # 2. Corte Inteligente (RMS) para isolar a palavra
        try:
            rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
            max_rms = float(np.max(rms)) if len(rms) > 0 else 0.0
            if max_rms > 1e-6:
                threshold = max_rms * 0.10
                active_frames = np.nonzero(rms > threshold)[0]
                if len(active_frames) > 0:
                    padding = int(0.1 * self.sample_rate)
                    start_sample = max(0, active_frames[0] * 512 - padding)
                    end_sample = min(len(audio), (active_frames[-1] + 1) * 512 + padding)
                    audio = audio[start_sample:end_sample]
                else:
                    return np.zeros(1024, dtype=np.float32)
            else:
                return np.zeros(1024, dtype=np.float32)
        except Exception:
            pass

        # 3. Tenta extração via PyTorch / Rede Siamesa
        try:
            import torch
            import torchaudio.transforms as T
            try:
                from src.config import ACOUSTIC_MODEL_BACKBONE
                from src.engine.siamese_net import UniversalTranslatorSiameseNet, AcousticTransformPipeline
            except ImportError:
                from config import ACOUSTIC_MODEL_BACKBONE
                from engine.siamese_net import UniversalTranslatorSiameseNet, AcousticTransformPipeline

            device = torch.device("cpu")
            waveform = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
            if self.sample_rate != 16000:
                resampler = T.Resample(orig_freq=self.sample_rate, new_freq=16000)
                waveform = resampler(waveform).to(device)
            else:
                waveform = waveform.to(device)

            transform_pipeline = AcousticTransformPipeline(
                model_backbone=ACOUSTIC_MODEL_BACKBONE,
                sample_rate=16000
            ).to(device)

            features_input = transform_pipeline(waveform)
            if ACOUSTIC_MODEL_BACKBONE == "mobilenet":
                features_input = features_input.unsqueeze(0)

            if self._model is None or self._model_backbone != ACOUSTIC_MODEL_BACKBONE:
                model_filename = f'siamese_universal_translator_1024d_{ACOUSTIC_MODEL_BACKBONE}.pth'
                model_path = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), '..', '..', 'models', model_filename
                ))

                self._model = UniversalTranslatorSiameseNet(
                    embedding_dim=1024,
                    model_backbone=ACOUSTIC_MODEL_BACKBONE
                ).to(device)

                if os.path.exists(model_path):
                    self._model.load_state_dict(
                        torch.load(model_path, map_location=device, weights_only=True)
                    )
                self._model_backbone = ACOUSTIC_MODEL_BACKBONE
                self._model.eval()

            with torch.no_grad():
                normalized_vector = self._model.forward_single_branch(features_input)

            vector_1d = normalized_vector.cpu().numpy().flatten().astype(np.float32)
            return vector_1d
        except (ImportError, Exception):
            # Fallback seguro quando torch não estiver presente ou erro de inferência
            return self._fallback_mfcc_features(audio, dim=1024)

    def save_audio(self, audio: np.ndarray, filename: str, language: str) -> str:
        """Save audio file to language directory with path containment and validation."""
        audio = self._validate_audio_input(audio)
        clean_lang = sanitize_identifier(language)
        clean_name = sanitize_filename(filename)

        lang_path = os.path.join(self.audio_database_path, clean_lang)
        os.makedirs(lang_path, exist_ok=True)

        filepath = os.path.join(lang_path, f"{clean_name}.wav")
        if not is_safe_path(self.audio_database_path, filepath):
            raise SecurityError(f"Path traversal detected: {filepath} escapes {self.audio_database_path}")

        # Normaliza volume e salva como int16
        max_val = np.max(np.abs(audio)) if len(audio) > 0 else 0.0
        if max_val > 0:
            audio_normalized = audio / max_val
        else:
            audio_normalized = audio
        audio_int16 = (audio_normalized * 32767).astype(np.int16)
        wavfile.write(filepath, self.sample_rate, audio_int16)

        return filepath

    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load audio file."""
        return librosa.load(filepath, sr=self.sample_rate)

    def compare_audio(self, audio1: np.ndarray, audio2: np.ndarray) -> float:
        """Compare two audio signals using cosine similarity with zero division protection."""
        features1 = self.extract_features(audio1)
        features2 = self.extract_features(audio2)

        norm1 = float(np.linalg.norm(features1))
        norm2 = float(np.linalg.norm(features2))

        if norm1 <= 1e-8 or norm2 <= 1e-8:
            return 0.0

        dot_product = float(np.dot(features1, features2))
        return float(np.clip(dot_product / (norm1 * norm2), -1.0, 1.0))

    def find_best_match(
        self, query_audio: np.ndarray, language: str, threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
        """Find best matching word in language database safely."""
        clean_lang = sanitize_identifier(language)
        lang_path = os.path.join(self.audio_database_path, clean_lang)
        if not is_safe_path(self.audio_database_path, lang_path) or not os.path.exists(lang_path):
            return None

        best_match = None
        best_score = 0.0

        query_features = self.extract_features(query_audio)
        q_norm = float(np.linalg.norm(query_features))
        if q_norm <= 1e-8:
            return None

        for filename in os.listdir(lang_path):
            if filename.endswith(".wav") and not filename.startswith("."):
                filepath = os.path.join(lang_path, filename)
                if not is_safe_path(lang_path, filepath):
                    continue
                try:
                    audio, _ = self.load_audio(filepath)
                    db_features = self.extract_features(audio)
                    db_norm = float(np.linalg.norm(db_features))
                    if db_norm <= 1e-8:
                        continue

                    similarity = float(np.dot(query_features, db_features) / (q_norm * db_norm))
                    if similarity > best_score and similarity >= threshold:
                        best_score = similarity
                        word = os.path.splitext(filename)[0]
                        best_match = (word, float(similarity))
                except Exception as e:
                    print(f"Erro ao processar {filename}: {e}")
                    continue

        return best_match
