# Unit Test Instructions: Google Colab Cloud Training Integration

## Test Framework & Prerequisites

- **Test Framework**: `pytest` (Python 3.10+)
- **Test File Path**: `tests/test_colab_train.py`
- **Dependencies**: `pytest`, `torch`, `torchaudio`

## Scoped Execution Command

To execute tests strictly scoped to this unit:

```bash
python -m pytest tests/test_colab_train.py -v
```

> **Requirement**: Scoped command must target `tests/test_colab_train.py` directly without executing the broader suite.

## Expected Test Coverage

Under the **Minimal Test Strategy**, the suite validates each primary requirement with focused, deterministic tests:

1. **Configuration & Validation (FR1.1, FR1.2, BR1.1)**:
   - Valid configuration instantiates `ColabJobConfig` cleanly.
   - Invalid accelerator (e.g. `invalid_gpu`) raises `ValueError`.
   - Non-positive epochs/batch-size raises `ValueError`.

2. **Dry-Run & Bundling (FR1.3, BR1.2, FR2.2)**:
   - Running in `--dry-run` prepares the mock archive and verifies contents without calling external subprocesses.

3. **Hardware Catalog & Cost-Efficiency (FR3.1, FR3.2, FR3.3, BR3.1, BR3.2)**:
   - Hardware profile catalog resolves `none`, `t4`, `v100`, `a100`, `tpu`.
   - Efficiency formula computes speedup-to-cost ratio correctly.
   - Recommendation flags when expensive tiers fail to meet the 1.25x efficiency threshold.

4. **Acoustic Separation & Checkpoint Validation (FR4.1, FR4.2, FR4.3, BR4.1, BR4.2)**:
   - Checkpoint integrity check detects corrupted or missing files.
   - Separation evaluation passes when $\Delta \ge 0.15$ and fails when separation is insufficient.

## Mocking & Isolation Guidance

- Mock `subprocess.Popen` or `subprocess.run` to simulate `colab exec` output and return codes without requiring a live Google Colab account or CLI during unit test execution.
- Mock torch model loading when testing corrupt vs valid state dictionaries.
- Use temporary directories (`tmp_path` pytest fixture) for all file creation and bundle extraction tests to ensure complete test isolation.
