"""
Siamese Network definitions for Universal Translator.
"""
import os
import random

import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.data import Dataset

import torchaudio.transforms as T
from torchvision.models import mobilenet_v2

# ==============================================================================
# 1. Conjunto de Dados Dinâmico para Aprendizado Few-Shot Interespécies
# ==============================================================================
class InterspeciesTripletDataset(Dataset):
    """
    Construtor dinâmico para amostragem no contexto Few-Shot Learning.
    Produz tripletos (Anchor, Positive, Negative) suportando múltiplos idiomas alvo.
    """
    def __init__(self, data_dict, anchor_lang='ingles', virtual_size=500):
        """
        data_dict format:
        {
            'CACHORRO': { 'ingles': ['path1'], 'elvish': ['path2'] }
        }
        """
        self.data_dict = data_dict
        self.anchor_lang = anchor_lang
        self.virtual_dataset_size = virtual_size

        # Detecta todos os idiomas disponíveis na pasta
        all_langs = set()
        for _, langs in data_dict.items():
            for lang in langs.keys():
                all_langs.add(lang)

        # Define idiomas alvos (qualquer pasta que não seja a âncora)
        self.target_langs = [l for l in all_langs if l != anchor_lang]
        if not self.target_langs:
            self.target_langs = [anchor_lang]

        # Filtra classes que possuem pelo menos um áudio na âncora
        self.classes = [
            c for c in data_dict.keys()
            if anchor_lang in data_dict[c] and len(data_dict[c][anchor_lang]) > 0
        ]

        if len(self.classes) < 2:
            raise ValueError(f"É necessário pelo menos 2 palavras cadastradas "
                             f"em '{anchor_lang}' para treinar a rede siamesa.")

    def __len__(self):
        return self.virtual_dataset_size

    def _load_and_resample(self, path_or_tensor):
        if isinstance(path_or_tensor, torch.Tensor):
            return path_or_tensor

        import librosa # pylint: disable=import-outside-toplevel
        # librosa já faz o resample e carrega como numpy array
        waveform_np, _ = librosa.load(path_or_tensor, sr=16000, mono=True)
        waveform = torch.tensor(waveform_np, dtype=torch.float32).unsqueeze(0)

        return waveform

    def __getitem__(self, idx):
        # pylint: disable=too-many-locals
        anchor_class = random.choice(self.classes)
        negative_class = random.choice(self.classes)
        while negative_class == anchor_class:
            negative_class = random.choice(self.classes)

        anchor_path = random.choice(self.data_dict[anchor_class][self.anchor_lang])

        # Escolhe dinamicamente um dos idiomas alvo disponíveis para a palavra âncora
        pos_langs = [l for l in self.target_langs if l in self.data_dict[anchor_class]
                     and len(self.data_dict[anchor_class][l]) > 0]
        if not pos_langs:
            positive_lang = self.anchor_lang
        else:
            positive_lang = random.choice(pos_langs)
        positive_path = random.choice(self.data_dict[anchor_class][positive_lang])

        # Escolhe dinamicamente um dos idiomas alvo disponíveis para a palavra negativa
        neg_langs = [l for l in self.target_langs if l in self.data_dict[negative_class]
                     and len(self.data_dict[negative_class][l]) > 0]
        if not neg_langs:
            negative_lang = self.anchor_lang
        else:
            negative_lang = random.choice(neg_langs)
        negative_path = random.choice(self.data_dict[negative_class][negative_lang])

        anchor_audio = self._load_and_resample(anchor_path)
        positive_audio = self._load_and_resample(positive_path)
        negative_audio = self._load_and_resample(negative_path)

        # Se não há gravações diferentes (só tem 1 arquivo para a palavra),
        # aplicamos Data Augmentation (Ruído/Volume) no Positivo
        is_same = False
        if isinstance(anchor_path, str) and isinstance(positive_path, str):
            is_same = anchor_path == positive_path
        elif isinstance(anchor_path, torch.Tensor) and isinstance(positive_path, torch.Tensor):
            is_same = anchor_path is positive_path

        if is_same:
            noise = torch.randn_like(positive_audio) * 0.05 * torch.max(torch.abs(positive_audio))
            volume_scale = random.uniform(0.5, 1.5)
            positive_audio = (positive_audio * volume_scale) + noise

        return anchor_audio, positive_audio, negative_audio


# ==============================================================================
# 2. Pipeline de Compressão Espectro-Temporal Transponível
# ==============================================================================
class MelSpectrogramPipeline(nn.Module):
    """Pipeline that transforms audio into Mel Spectrograms."""
    def __init__(self, sample_rate=16000, n_mels=128, n_fft=1024, hop_length=256):
        super().__init__()
        self.mel_extractor = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            power=2.0
        )
        self.amplitude_to_db = T.AmplitudeToDB(stype='power', top_db=80)

    def forward(self, waveform):
        """Converts waveform to Mel Spectrogram."""
        # Ajeita dimensões para a convolução (adicionando Batch ou Channel)
        mel_power = self.mel_extractor(waveform)
        mel_db = self.amplitude_to_db(mel_power)
        return mel_db


# ==============================================================================
# 3. Backbone Acústico-Topológico e Projection Head L2-Normalizada
# ==============================================================================
class UniversalTranslatorSiameseNet(nn.Module):
    """
    MobileNetV2 adaptada para tradução semântica de áudios brutos.
    """
    def __init__(self, embedding_dim=1024):
        super().__init__()

        # Backbone ignorando pesos pré-treinados para focar nas assinaturas alienígenas
        self.backbone = mobilenet_v2(weights=None)

        # Modificação A: 1 Canal de entrada (Espectrograma monocromático)
        original_initial_conv = self.backbone.features[0][0]
        self.backbone.features[0][0] = nn.Conv2d(
            in_channels=1,
            out_channels=original_initial_conv.out_channels,
            kernel_size=original_initial_conv.kernel_size,
            stride=original_initial_conv.stride,
            padding=original_initial_conv.padding,
            bias=False
        )

        # Remove classificador final das 1000 classes de imagem
        self.backbone.classifier = nn.Identity()

        backbone_latent_channels = 1280

        # Modificação B: Projection Head para 1024D (ChromaDB)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.projection_bottleneck = nn.Sequential(
            nn.Linear(backbone_latent_channels, 1024),
            nn.BatchNorm1d(1024),
            nn.GELU(),
            nn.Linear(1024, embedding_dim)
        )

    def forward_single_branch(self, audio_tensor):
        """ Executa uma vertente da rede Siamesa """
        features_2d = self.backbone.features(audio_tensor)
        pooled_tensor = self.adaptive_pool(features_2d)
        flattened_vector = torch.flatten(pooled_tensor, 1)
        projection_vector = self.projection_bottleneck(flattened_vector)

        # Modificação C: L2-Norm Obrigatória para adequação matemática da similaridade Cosseno
        normalized_vector = F.normalize(projection_vector, p=2, dim=1)
        return normalized_vector

    def forward(self, anchor, positive, negative=None):
        """ Passagem Dupla ou Tripla """
        output_anchor = self.forward_single_branch(anchor)
        output_positive = self.forward_single_branch(positive)

        if negative is not None:
            output_negative = self.forward_single_branch(negative)
            return output_anchor, output_positive, output_negative

        return output_anchor, output_positive


# ==============================================================================
# 4. Orquestrador Computacional: Funções Auxiliares
# ==============================================================================
def build_dataset_dictionary(base_path="linguagens"):
    """
    Lê a pasta de linguagens e monta o dicionário de treino.
    Exemplo: {'CACHORRO': {'ingles': ['path'], 'clingo': ['path']}}
    """
    data_dict = {}
    if not os.path.exists(base_path):
        return data_dict

    for lang in os.listdir(base_path):
        lang_path = os.path.join(base_path, lang)
        if os.path.isdir(lang_path):
            for filename in os.listdir(lang_path):
                if filename.endswith(".wav"):
                    word = os.path.splitext(filename)[0].upper()
                    filepath = os.path.join(lang_path, filename)

                    if word not in data_dict:
                        data_dict[word] = {}
                    if lang not in data_dict[word]:
                        data_dict[word][lang] = []

                    data_dict[word][lang].append(filepath)
    return data_dict
