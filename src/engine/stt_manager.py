from faster_whisper import WhisperModel
import os
import numpy as np

class STTManager:
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Initialize the Whisper model for speech-to-text
        
        Args:
            model_size: Size of the model ("tiny", "base", "small", "medium", "large")
            device: Device to run on ("cpu" or "cuda")
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16"
            )
            print(f"Whisper model '{self.model_size}' loaded on {self.device}")
        except Exception as e:
            print(f"Erro ao carregar modelo Whisper: {e}")
            self.model = None
    
    def transcribe(self, audio: np.ndarray, language: str = "pt", input_sr: int = 22050) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio: Audio signal as numpy array
            language: Language code for transcription (default: "pt" for Portuguese)
            input_sr: The sample rate of the input audio (default: 22050 from AudioProcessor)
            
        Returns:
            Transcribed text
        """
        if self.model is None:
            print("Modelo Whisper não carregado")
            return ""
        
        try:
            # Whisper expects float32 audio
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # NORMALIZATION: Scale audio to [-1, 1] range
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val
            
            # RESAMPLING: Whisper MUST have 16000Hz
            if input_sr != 16000:
                import librosa
                audio = librosa.resample(audio, orig_sr=input_sr, target_sr=16000)
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio,
                language=language,
                beam_size=10,
                vad_filter=True
            )
            
            # Collect all segments
            transcription = " ".join([segment.text for segment in segments])
            return transcription.strip()
            
        except Exception as e:
            print(f"Erro durante transcrição: {e}")
            return ""
    
    def transcribe_file(self, filepath: str, language: str = "pt") -> str:
        """
        Transcribe audio file to text
        
        Args:
            filepath: Path to audio file
            language: Language code for transcription
            
        Returns:
            Transcribed text
        """
        if not os.path.exists(filepath):
            print(f"Arquivo não encontrado: {filepath}")
            return ""
        
        try:
            # Load audio file
            import librosa
            audio, sr = librosa.load(filepath, sr=16000)  # Whisper expects 16kHz
            return self.transcribe(audio, language)
        except Exception as e:
            print(f"Erro ao transcrever arquivo: {e}")
            return ""
