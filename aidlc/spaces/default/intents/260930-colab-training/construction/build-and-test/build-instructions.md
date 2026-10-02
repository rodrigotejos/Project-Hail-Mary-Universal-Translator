# Build Instructions: Google Colab Cloud Training Integration

## Environment Prerequisites & Installation

The Google Colab cloud training integration requires Python 3.10+ and standard build dependencies:

- **Python Version**: Python >= 3.10 (tested on Python 3.12.10)
- **Local Requirements**:
  ```bash
  pip install -r requirements.txt
  ```
  Core libraries required for local orchestration and dry-run execution:
  - `numpy >= 1.24`
  - `scipy >= 1.10`
  - `pytest >= 8.0`

- **Remote Colab Environment**:
  The Colab runtime autonomously installs deep learning packages on notebook launch:
  ```bash
  pip install torchaudio transformers==4.41.2 librosa scipy
  ```

## Packaging & Dry-Run Build Verification

To verify that the code packages cleanly and local build artifacts assemble without error:

1. **Syntax & Compilation Check**:
   ```bash
   python -m py_compile src/engine/colab_train.py
   ```
2. **Orchestrator Dry-Run Packaging**:
   ```bash
   python src/engine/colab_train.py --dry-run
   ```
   Verifies that:
   - `src/` modules and `linguagens/` assets are bundled into `models/colab_runs/bundle_*.tar.gz`.
   - Simulated execution metrics are successfully recorded to `models/colab_runs/metrics_*.json`.

3. **Notebook JSON Integrity**:
   ```bash
   python -c "import json; json.load(open('notebooks/colab_train_siamese.ipynb', 'r', encoding='utf-8'))"
   ```

## Troubleshooting Common Build Issues

- **Missing CLI Binary**: If `colab` is not found, verify Google Colab CLI installation (`pip install google-colab-cli` or follow Google Developer guidelines) and run `colab login`. Alternatively, use the browser fallback by uploading `notebooks/colab_train_siamese.ipynb`.
- **Missing Audio Dataset**: If `linguagens/` has no audio files, `--dry-run` and synthetic fallback within the notebook will supply mock embeddings to ensure continuous pipeline verification.
- **PyTorch Absence on Local Machine**: Local orchestration uses lazy imports and numpy fallbacks; local PyTorch installation is not required for dry-run bundling or metric evaluation.
