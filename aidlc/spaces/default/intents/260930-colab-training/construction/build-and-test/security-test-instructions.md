# Security Test Instructions: Credential Safety & Input Sanitization

## Security Guidelines & Token Safety

In compliance with Rule **BR4.3** and Requirement **NFR4**:
- No Google Cloud credentials, Colab access tokens, or account passwords may be hardcoded or written into Jupyter notebook cells or source code.
- Authentication relies exclusively on Google's native CLI (`colab login`) or environment variables managed by the user.

## Local Bundle Containment & Validation

- The archive creation utility (`create_training_bundle`) must strictly constrain packaging to approved workspace directories (`src/`, `linguagens/`, and `config.py`).
- Symlinks pointing outside the workspace boundary are ignored to prevent path traversal vulnerabilities.

## Subprocess Command Sanitization

- Subprocess arguments in `ColabTrainOrchestrator` are passed as a structured list to `subprocess.Popen`, never through `shell=True`, preventing shell injection vulnerabilities.
- User-provided parameters (`--gpu`, `--epochs`, `--batch-size`, `--backbone`) are validated strictly against allowlists and numeric boundaries before execution.
