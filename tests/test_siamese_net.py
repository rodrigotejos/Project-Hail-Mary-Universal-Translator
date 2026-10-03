"""
Unit tests for Siamese Network (InterspeciesTripletDataset and UniversalTranslatorSiameseNet).
"""
import unittest
from unittest.mock import MagicMock, patch
import pytest

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for SiameseNet tests")
class TestSiameseNet(unittest.TestCase):
    """Tests for Siamese Network components."""

    def test_triplet_dataset_insufficient_classes_raises(self):
        from src.engine.siamese_net import InterspeciesTripletDataset
        # Only 1 class -> should raise ValueError
        data_dict = {
            "OLA": {"ingles": ["mock1.wav"], "clingo": ["mock2.wav"]}
        }
        with self.assertRaises(ValueError) as ctx:
            InterspeciesTripletDataset(data_dict, anchor_lang="ingles")
        self.assertIn("pelo menos 2 palavras", str(ctx.exception))

    def test_triplet_dataset_sampling(self):
        from src.engine.siamese_net import InterspeciesTripletDataset
        t1 = torch.zeros(1, 16000)
        t2 = torch.ones(1, 16000)
        data_dict = {
            "OLA": {"ingles": [t1], "clingo": [t1]},
            "TCHAU": {"ingles": [t2], "clingo": [t2]}
        }
        ds = InterspeciesTripletDataset(data_dict, anchor_lang="ingles", virtual_size=5)
        self.assertEqual(len(ds), 5)

        anc, pos, neg = ds[0]
        self.assertEqual(anc.shape, (1, 16000))
        self.assertEqual(pos.shape, (1, 16000))
        self.assertEqual(neg.shape, (1, 16000))

    def test_acoustic_transform_pipeline_mobilenet(self):
        from src.engine.siamese_net import AcousticTransformPipeline
        pipeline = AcousticTransformPipeline(model_backbone="mobilenet", sample_rate=16000)
        waveform = torch.randn(2, 1, 16000)
        features = pipeline(waveform)
        self.assertIsNotNone(features)
        self.assertEqual(features.shape[0], 2)

    def test_siamese_net_forward_mobilenet(self):
        from src.engine.siamese_net import UniversalTranslatorSiameseNet
        model = UniversalTranslatorSiameseNet(embedding_dim=128, model_backbone="mobilenet")
        waveform = torch.randn(2, 1, 16000)
        embeddings = model(waveform)
        self.assertEqual(embeddings.shape, (2, 128))

        # Check L2 normalization
        norms = torch.norm(embeddings, p=2, dim=-1)
        for n in norms:
            self.assertAlmostEqual(n.item(), 1.0, places=4)
