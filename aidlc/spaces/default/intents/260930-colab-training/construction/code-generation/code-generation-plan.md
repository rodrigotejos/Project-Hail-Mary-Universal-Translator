# Code Generation Plan: Google Colab Cloud Training Integration

## Testing Contract

```json
{
  "version": 1,
  "methodology": "test-after",
  "source": "org",
  "ordering": "implement each applicable testable layer, then write and run that layer's tests.",
  "scope": "colab-cloud-training",
  "test_strategy": "minimal",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    }
  ],
  "obligations": {
    "strategy": "minimal",
    "strategy_volume": [
      "One verifiable test per requirement at the narrowest effective level.",
      "At least one happy-path unit test per component.",
      "Unit tests are the default; a bugfix/security scope floor may require an integration or E2E regression when that is the narrowest level that reproduces the defect."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "test-after",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Data model / database behavior - implement.",
      "Data model / database behavior - write and run its tests after implementation.",
      "Repository / data access - implement.",
      "Repository / data access - write and run its tests after implementation.",
      "Business logic - implement.",
      "Business logic - write and run its tests after implementation.",
      "API / endpoint - implement.",
      "API / endpoint - write and run its tests after implementation.",
      "Frontend behavior - implement.",
      "Frontend behavior - write and run its tests after implementation.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:10a8245a7c77d34ed252d8ae2c168caa80c34a71609483357c7d0bd1df15217a",
  "contract_sha256": "sha256:a9cf36d6613627de11d9125946efb85469c043ec59d1d04912f1fc066a194627"
}
```

## Implementation Steps & Plan Breakdown

- [x] **Step 1: Project structure and module skeleton**
  - Create `src/engine/colab_train.py` structure matching `src/engine/cloud_train.py` conventions.
  - Implements: FR1.1, BR1.1

- [x] **Step 2: Test runner readiness verification**
  - Verify `pytest` environment and ensure unit test runner is available.
  - Command: `python -m pytest tests/test_colab_train.py -v`
  - Implements: Testing Contract runner_ready obligation

- [x] **Step 3: Data models and hardware profiles implementation**
  - Implement dataclasses: `ColabJobConfig`, `HardwareProfile`, `TrainingMetrics`, `AcousticEvaluationResult`.
  - Register hardware catalog (`cpu`/`none`, `t4`, `v100`, `a100`, `tpu`) with cost factors and speedup thresholds.
  - Implements: FR1.2, FR3.1, BR1.1, BR3.1, BR3.2

- [x] **Step 4: Training bundle packaging & asset preparation**
  - Implement bundle creation to package `linguagens/` audio assets and core engine code into staging zip/tar.
  - Implements: FR2.2, BR2.1

- [x] **Step 5: Subprocess execution & real-time streaming with dry-run support**
  - Implement `colab exec` command dispatcher and log streamer.
  - Implement isolated dry-run mode without external process invocation.
  - Implement error handling for missing CLI or quota failures with manual browser fallback guidance.
  - Implements: FR1.3, FR1.4, BR1.2, BR1.3, BR3.3, NFR3, NFR4

- [x] **Step 6: Version-controlled training notebook**
  - Author `notebooks/colab_train_siamese.ipynb` containing 6 autonomous cells:
    1. Environment detection & dependencies installation (`torchaudio`, `transformers`, `scipy`).
    2. Data unpack & audio verification.
    3. Siamese model & transforms initialization.
    4. Triplet training loop with epoch benchmarking.
    5. Weights and `training_metrics.json` export.
    6. Standalone verification inference.
  - Implements: FR2.1, FR2.2, FR2.3, FR2.4, FR2.5, BR2.1, BR2.2

- [x] **Step 7: Post-training validation & acoustic separation evaluation**
  - Implement `validate_checkpoint()` verifying `.pth` integrity and computing cosine distance separation margin ($\Delta \ge 0.15$).
  - Implements: FR4.1, FR4.2, FR4.3, BR4.1, BR4.2

- [x] **Step 8: Unit test implementation and execution**
  - Author `tests/test_colab_train.py` covering:
    - CLI argument parsing and validation errors (BR1.1).
    - Dry-run execution path and artifact bundle generation (BR1.2).
    - Hardware profile catalog and cost-efficiency calculation (BR3.1, BR3.2).
    - Checkpoint validation logic and separation margin thresholds (BR4.1, BR4.2).
  - Execute test suite and confirm 100% pass rate.
  - Implements: Minimal test strategy floor

- [x] **Step 9: Documentation, source manifest & traceability**
  - Generate `source-manifest.json` listing created files.
  - Create `code-summary.md` and `traceability.json`.
  - Implements: Stage completion deliverables
