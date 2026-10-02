# Integration Test Instructions: Google Colab Cloud Training Integration

## Integration Scope & Objectives

Integration tests verify the end-to-end interactions between the local orchestrator (`src/engine/colab_train.py`), file bundling routines, subprocess invocation, and checkpoint evaluation pipelines.

Key integration boundaries:
- Orchestrator CLI to filesystem packaging (`create_training_bundle`).
- Dry-run pipeline producing valid JSON metric contracts.
- Checkpoint validation routine consuming serializable weights files.

## Execution Commands & Test Scenarios

To execute the integration scenarios:

```bash
python -m pytest tests/test_colab_train.py -k "TestTrainingBundleAndDryRun or TestColabCliExecutionFallback" -v
```

Scenarios covered:
1. **Packaging Integration**:
   - Creates a temporary directory structure mimicking `linguagens/` and `src/`.
   - Packs into `tar.gz` and verifies archive readability.
2. **Subprocess Boundary Integration**:
   - Intercepts `shutil.which` to assert graceful fallback behavior when the Colab CLI is not authenticated or not installed.

## Mocking & Cloud Boundaries

- **Google Colab Cloud API**: Never invoke actual remote cloud instances or spend cloud credits during automated integration tests.
- **Subprocess Mocking**: Use `unittest.mock.patch` over `subprocess.Popen` to test return code handling, real-time stdout streaming, and process failure exits.
