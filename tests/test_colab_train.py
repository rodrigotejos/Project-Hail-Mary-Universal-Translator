"""
Unit tests for Google Colab Cloud Training and Progressive Benchmarking Module.
Scoped to: tests/test_colab_train.py
"""

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.engine.colab_train import (
    AcousticEvaluationResult,
    ColabJobConfig,
    ColabTrainOrchestrator,
    HardwareProfile,
    TrainingMetrics,
    create_training_bundle,
    evaluate_hardware_efficiency,
    get_hardware_catalog,
    validate_checkpoint,
)


class TestColabJobConfig(unittest.TestCase):
    """Tests for job configuration and parameter validation (FR1.1, FR1.2, BR1.1)."""

    def test_valid_configuration(self):
        config = ColabJobConfig(
            job_id="test_job_001",
            accelerator_type="t4",
            epochs=20,
            batch_size=16,
            backbone="mobilenet",
            dry_run=True,
        )
        # Should not raise
        config.validate()
        self.assertEqual(config.accelerator_type, "t4")
        self.assertEqual(config.epochs, 20)

    def test_invalid_accelerator_raises_value_error(self):
        config = ColabJobConfig(
            job_id="test_job_invalid_gpu",
            accelerator_type="rtx4090",  # Not in catalog
        )
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("Invalid accelerator_type", str(ctx.exception))

    def test_invalid_epochs_raises_value_error(self):
        config = ColabJobConfig(job_id="test_job_zero_epochs", epochs=0)
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("epochs must be strictly positive", str(ctx.exception))

    def test_invalid_batch_size_raises_value_error(self):
        config = ColabJobConfig(job_id="test_job_neg_batch", batch_size=-8)
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("batch_size must be strictly positive", str(ctx.exception))

    def test_invalid_backbone_raises_value_error(self):
        config = ColabJobConfig(job_id="test_job_bad_bb", backbone="resnet50")
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("backbone must be 'mobilenet' or 'ast'", str(ctx.exception))

    def test_invalid_learning_rate_raises_value_error(self):
        config = ColabJobConfig(job_id="test_job_bad_lr", learning_rate=-0.001)
        with self.assertRaises(ValueError) as ctx:
            config.validate()
        self.assertIn("learning_rate must be strictly positive", str(ctx.exception))


class TestHardwareProfilesAndEfficiency(unittest.TestCase):
    """Tests for progressive accelerator matrix and cost-efficiency scoring (FR3.1, FR3.2, FR3.3, BR3.1, BR3.2)."""

    def test_catalog_contains_expected_accelerators(self):
        catalog = get_hardware_catalog()
        expected = ["none", "t4", "v100", "a100", "tpu"]
        for key in expected:
            self.assertIn(key, catalog)
            self.assertIsInstance(catalog[key], HardwareProfile)

    def test_t4_baseline_efficiency(self):
        efficiency, rec = evaluate_hardware_efficiency(
            profile_id="t4",
            seconds_per_epoch=45.0,
            t4_seconds_per_epoch=45.0
        )
        self.assertAlmostEqual(efficiency, 1.0, places=2)
        self.assertIn("T4 tier active", rec)

    def test_expensive_tier_unjustified_speedup(self):
        # A100 costs 4.0x T4. If it runs at 30s vs 45s (speedup = 1.5x),
        # efficiency = 1.5 / 4.0 = 0.375 (< 1.25 threshold) -> Should warn to downgrade
        efficiency, rec = evaluate_hardware_efficiency(
            profile_id="a100",
            seconds_per_epoch=30.0,
            t4_seconds_per_epoch=45.0
        )
        self.assertLess(efficiency, 1.25)
        self.assertIn("Downgrade to standard T4", rec)

    def test_expensive_tier_justified_speedup(self):
        # A100 running at 5s vs 45s (speedup = 9.0x),
        # efficiency = 9.0 / 4.0 = 2.25 (>= 1.25 threshold) -> High performance justified
        efficiency, rec = evaluate_hardware_efficiency(
            profile_id="a100",
            seconds_per_epoch=5.0,
            t4_seconds_per_epoch=45.0
        )
        self.assertGreaterEqual(efficiency, 1.25)
        self.assertIn("High performance justified", rec)

    def test_zero_or_negative_duration_efficiency(self):
        eff, rec = evaluate_hardware_efficiency(profile_id="t4", seconds_per_epoch=0.0)
        self.assertEqual(eff, 0.0)
        self.assertIn("Invalid execution duration", rec)

    def test_cpu_tier_efficiency(self):
        eff, rec = evaluate_hardware_efficiency(profile_id="none", seconds_per_epoch=100.0)
        self.assertIn("CPU tier active", rec)


class TestTrainingBundleAndDryRun(unittest.TestCase):
    """Tests for bundle packaging and dry-run execution (FR1.3, FR2.2, BR1.2)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root_path = Path(self.temp_dir)
        (self.root_path / "src").mkdir()
        (self.root_path / "src" / "test.py").write_text("print('test')")
        (self.root_path / "linguagens").mkdir()
        (self.root_path / "linguagens" / "audio.wav").write_bytes(b"RIFFmockwavdata")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_training_bundle(self):
        bundle_out = self.root_path / "bundle.tar.gz"
        created_path = create_training_bundle(self.root_path, bundle_out)
        self.assertTrue(created_path.exists())
        self.assertGreater(created_path.stat().st_size, 0)

    def test_orchestrator_dry_run_simulation(self):
        config = ColabJobConfig(
            job_id="dryrun_test_01",
            accelerator_type="t4",
            epochs=5,
            dry_run=True,
            output_dir="output_runs",
        )
        orchestrator = ColabTrainOrchestrator(config, project_root=self.root_path)
        result = orchestrator.run()

        self.assertEqual(result["status"], "dry_run_completed")
        self.assertTrue(Path(result["bundle_path"]).exists())
        self.assertTrue(Path(result["metrics_path"]).exists())

        with open(result["metrics_path"], "r", encoding="utf-8") as f:
            metrics = json.load(f)
        self.assertEqual(metrics["job_id"], "dryrun_test_01")
        self.assertEqual(metrics["total_epochs_completed"], 5)

    def test_create_training_bundle_with_config(self):
        (self.root_path / "config.py").write_text("# mock config")
        bundle_out = self.root_path / "bundle_with_cfg.tar.gz"
        created_path = create_training_bundle(self.root_path, bundle_out)
        self.assertTrue(created_path.exists())

    def test_orchestrator_dry_run_payload_failure(self):
        config = ColabJobConfig(
            job_id="dryrun_fail",
            accelerator_type="t4",
            dry_run=True,
            output_dir="output_runs",
        )
        orchestrator = ColabTrainOrchestrator(config, project_root=self.root_path)
        with patch.object(orchestrator, "prepare_bundle", return_value=Path(self.temp_dir) / "empty.tar.gz"):
            with self.assertRaises(RuntimeError) as ctx:
                orchestrator.run()
            self.assertIn("Failed to create bundle payload", str(ctx.exception))


class TestAcousticCheckpointValidation(unittest.TestCase):
    """Tests for model checkpoint integrity and embedding separation (FR4.1, FR4.2, FR4.3, BR4.1, BR4.2)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.chk_path = Path(self.temp_dir) / "test_model.pth"
        try:
            import torch
            torch.save({"linear.weight": torch.randn(64, 64)}, self.chk_path)
        except ImportError:
            # Write dummy binary file > 1024 bytes
            self.chk_path.write_bytes(b"P" * 2048)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_checkpoint_raises_error(self):
        missing = Path(self.temp_dir) / "non_existent.pth"
        with self.assertRaises(ValueError):
            validate_checkpoint(missing)

    def test_checkpoint_separation_evaluation(self):
        # Uses numpy synthetic projection fallback if torch is absent
        res = validate_checkpoint(self.chk_path, min_margin=0.15)
        self.assertIsInstance(res, AcousticEvaluationResult)
        self.assertGreater(res.mean_negative_distance, res.mean_positive_distance)
        self.assertGreaterEqual(res.separation_delta, 0.15)
        self.assertTrue(res.passed)

    def test_insufficient_margin_flags_failed(self):
        # Demanding unrealistically high margin (e.g. 1.8) triggers passed=False
        res = validate_checkpoint(self.chk_path, min_margin=1.80)
        self.assertFalse(res.passed)

    def test_corrupted_checkpoint_raises_error(self):
        corrupt_path = Path(self.temp_dir) / "corrupt.pth"
        corrupt_path.write_bytes(b"CORRUPTED_NOT_A_VALID_PICKLE" * 100)
        try:
            import torch
            with self.assertRaises(ValueError):
                validate_checkpoint(corrupt_path)
        except ImportError:
            pass

    def test_checkpoint_too_small_raises_error(self):
        small_path = Path(self.temp_dir) / "small.pth"
        small_path.write_bytes(b"too_small")
        with self.assertRaises(ValueError) as ctx:
            validate_checkpoint(small_path)
        self.assertIn("missing or invalid", str(ctx.exception))

    def test_mock_torch_empty_state_dict(self):
        mock_torch = MagicMock()
        mock_torch.load.return_value = {}
        with patch.dict("sys.modules", {"torch": mock_torch, "torch.nn.functional": MagicMock()}):
            with self.assertRaises(ValueError) as ctx:
                validate_checkpoint(self.chk_path)
            self.assertIn("empty", str(ctx.exception))


class TestColabCliExecutionFallback(unittest.TestCase):
    """Tests for subprocess invocation and missing CLI fallback (FR1.4, BR1.3, BR3.3)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root_path = Path(self.temp_dir)
        (self.root_path / "notebooks").mkdir(parents=True, exist_ok=True)
        (self.root_path / "notebooks" / "colab_train_siamese.ipynb").write_text("{}")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_colab_cli_raises_informative_error(self):
        config = ColabJobConfig(
            job_id="cli_test_01",
            accelerator_type="t4",
            dry_run=False,
        )
        orchestrator = ColabTrainOrchestrator(config, project_root=self.root_path)
        with patch("shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError) as ctx:
                orchestrator._execute_colab_cli()
            self.assertIn("not found", str(ctx.exception))

    def test_missing_notebook_raises_file_not_found(self):
        config = ColabJobConfig(
            job_id="cli_test_02",
            notebook_path="nonexistent.ipynb",
            dry_run=False,
        )
        orchestrator = ColabTrainOrchestrator(config, project_root=self.root_path)
        with patch("shutil.which", return_value="/bin/colab"):
            with self.assertRaises(FileNotFoundError) as ctx:
                orchestrator._execute_colab_cli()
            self.assertIn("Notebook template not found", str(ctx.exception))

    def test_successful_colab_cli_invocation(self):
        config = ColabJobConfig(
            job_id="cli_test_03",
            accelerator_type="t4",
            dry_run=False,
        )
        orchestrator = ColabTrainOrchestrator(config, project_root=self.root_path)
        mock_proc = MagicMock()
        mock_proc.stdout = ["[COLAB] Epoch 1/30 - Loss: 0.05", "[COLAB] Finished"]
        mock_proc.wait.return_value = 0
        mock_proc.returncode = 0
        mock_proc.__enter__.return_value = mock_proc

        with patch("shutil.which", return_value="/bin/colab"):
            with patch("src.engine.colab_train.subprocess.Popen", return_value=mock_proc):
                res = orchestrator.run()
                self.assertEqual(res["status"], "completed")
                self.assertEqual(res["job_id"], "cli_test_03")

    def test_colab_cli_failure_raises_called_process_error(self):
        config = ColabJobConfig(
            job_id="cli_test_04",
            accelerator_type="t4",
            dry_run=False,
        )
        orchestrator = ColabTrainOrchestrator(config, project_root=self.root_path)
        mock_proc = MagicMock()
        mock_proc.stdout = ["[COLAB] Out of Memory error"]
        mock_proc.wait.return_value = 1
        mock_proc.returncode = 1
        mock_proc.__enter__.return_value = mock_proc

        import subprocess
        with patch("shutil.which", return_value="/bin/colab"):
            with patch("src.engine.colab_train.subprocess.Popen", return_value=mock_proc):
                with self.assertRaises(subprocess.CalledProcessError):
                    orchestrator.run()


class TestColabTrainMainCli(unittest.TestCase):
    """Tests for main() CLI entrypoint execution paths."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.chk_path = Path(self.temp_dir) / "test_chk.pth"
        self.chk_path.write_bytes(b"P" * 2048)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_main_cli_dry_run(self):
        from src.engine.colab_train import main
        with patch("sys.argv", ["colab_train.py", "--dry-run", "--gpu", "t4", "--epochs", "5"]):
            with patch.object(ColabTrainOrchestrator, "run") as mock_run:
                main()
                mock_run.assert_called_once()

    def test_main_cli_validate_checkpoint_pass(self):
        from src.engine.colab_train import main
        mock_eval = AcousticEvaluationResult(
            evaluation_id="eval_01",
            job_id="job_01",
            checkpoint_path=str(self.chk_path),
            mean_positive_distance=0.1,
            mean_negative_distance=0.9,
            separation_delta=0.8,
            min_required_margin=0.15,
            passed=True,
        )
        with patch("sys.argv", ["colab_train.py", "--validate-checkpoint", str(self.chk_path)]):
            with patch("src.engine.colab_train.validate_checkpoint", return_value=mock_eval):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)

    def test_main_cli_validate_checkpoint_fail(self):
        from src.engine.colab_train import main
        mock_eval = AcousticEvaluationResult(
            evaluation_id="eval_02",
            job_id="job_02",
            checkpoint_path=str(self.chk_path),
            mean_positive_distance=0.5,
            mean_negative_distance=0.5,
            separation_delta=0.0,
            min_required_margin=0.15,
            passed=False,
        )
        with patch("sys.argv", ["colab_train.py", "--validate-checkpoint", str(self.chk_path)]):
            with patch("src.engine.colab_train.validate_checkpoint", return_value=mock_eval):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)
