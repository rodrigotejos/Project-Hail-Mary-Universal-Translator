# Business Rules: Google Colab Cloud Training & Progressive Benchmarking

## Business Rules Specification

```yaml
rules:
  - id: BR1.1
    statement: CLI Parameter & Configuration Validation
    category: validation
    applies_to: ColabJobConfig
    trigger: Invocation of colab_train.py CLI or program initialization
    logic: >
      IF accelerator_type NOT IN ['none', 't4', 'v100', 'a100', 'tpu']
      OR epochs <= 0 OR batch_size <= 0 OR learning_rate <= 0
      THEN raise a ValidationError with actionable error message and exit code 1.
    violation_behavior: Reject execution immediately before any bundle preparation.
    source: FR1.1, FR1.2

  - id: BR1.2
    statement: Dry-Run Local Isolation Policy
    category: policy
    applies_to: ColabJobConfig
    trigger: When dry_run is set to true
    logic: >
      IF dry_run is true
      THEN generate mock training bundle, validate file structure and verify dependencies locally;
      DO NOT invoke the external 'colab' executable and DO NOT issue remote network requests.
    violation_behavior: Enforce local simulation with exit code 0 on successful validation.
    source: FR1.3

  - id: BR1.3
    statement: Colab CLI Process Execution & Return Code Verification
    category: policy
    applies_to: ColabJobConfig
    trigger: Dispatch of colab training process
    logic: >
      IF dry_run is false
      THEN verify 'colab' CLI binary is in PATH;
      invoke 'colab exec' with the structured notebook path;
      stream stdout/stderr in real-time;
      IF returncode != 0
      THEN emit diagnostic error instructions and indicate fallback manual web URL.
    violation_behavior: Log critical error and suggest manual browser execution.
    source: FR1.4, NFR3

  - id: BR2.1
    statement: Autonomous Notebook Environment & Data Extraction
    category: constraint
    applies_to: colab_train_siamese.ipynb
    trigger: Execution of notebook setup cells
    logic: >
      IF running in Google Colab environment (detected via google.colab module)
      THEN auto-install missing packages non-interactively;
      unpack compressed acoustic dataset archive into Colab local runtime (/content/linguagens/);
      verify dataset audio file counts are non-zero.
    violation_behavior: Fail cell with explanatory assertion message.
    source: FR2.1, FR2.2, FR2.5

  - id: BR2.2
    statement: Triplet Loss Optimization & Checkpoint Serialization
    category: calculation
    applies_to: UniversalTranslatorSiameseNet, TrainingMetrics
    trigger: Completion of training epochs loop
    logic: >
      IF training epochs complete
      THEN save model weights state_dict to 'models/siamese_colab.pth';
      compute total duration and seconds_per_epoch;
      write metrics summary to 'training_metrics.json';
      ensure files are downloadable or synced.
    violation_behavior: If save fails, retain metrics in notebook memory and print error.
    source: FR2.3, FR2.4

  - id: BR3.1
    statement: Progressive Hardware Baseline Preference
    category: policy
    applies_to: HardwareProfile
    trigger: Hardware selection when no accelerator is explicitly requested
    logic: >
      IF no explicit accelerator argument is passed
      THEN default to 't4' (standard balanced GPU tier);
      discourage default usage of expensive tiers (v100/a100).
    violation_behavior: Apply T4 profile automatically.
    source: FR3.1, NFR1

  - id: BR3.2
    statement: Cost-Benefit Escalation Threshold
    category: calculation
    applies_to: HardwareProfile, TrainingMetrics
    trigger: Post-training benchmark analysis across multiple hardware runs
    logic: >
      LET speedup = (t4_seconds_per_epoch / target_seconds_per_epoch);
      LET cost_ratio = target_relative_cost_factor / 1.0;
      LET efficiency = speedup / cost_ratio;
      IF target_tier IN ['v100', 'a100', 'tpu'] AND efficiency < 1.25
      THEN emit benchmark warning: 'Hardware tier does not deliver sufficient speedup to justify cost premium; recommend T4'.
    violation_behavior: Log cost-benefit recommendation in summary report.
    source: FR3.2, FR3.3, NFR1

  - id: BR3.3
    statement: Hardware Fallback and Resource Contention Policy
    category: policy
    applies_to: HardwareProfile
    trigger: Colab runtime failure due to quota exhaustion or unavailable GPU
    logic: >
      IF Colab reports 'Cannot connect to GPU backend' or quota exhaustion
      THEN log explanatory notice to user and provide command flag to retry with 'none' (CPU) or wait for quota reset.
    violation_behavior: Provide clear user mitigation steps.
    source: FR3.1, NFR3

  - id: BR4.1
    statement: Checkpoint Structure & State Dict Integrity Check
    category: validation
    applies_to: AcousticEvaluationResult
    trigger: Local retrieval of trained checkpoint
    logic: >
      IF checkpoint file is missing OR size < 1KB
      OR torch.load fails to deserialize state_dict keys matching UniversalTranslatorSiameseNet
      THEN flag checkpoint as INVALID and abort deployment.
    violation_behavior: Reject checkpoint and report corruption error.
    source: FR4.1

  - id: BR4.2
    statement: Acoustic Triplet Separation Validation
    category: calculation
    applies_to: AcousticEvaluationResult
    trigger: Post-training inference validation routine
    logic: >
      Compute mean positive cosine distance (D_pos) and mean negative cosine distance (D_neg);
      LET delta = D_neg - D_pos;
      IF delta < 0.15
      THEN mark AcousticEvaluationResult.passed = false and warn that embedding separation is insufficient;
      ELSE mark AcousticEvaluationResult.passed = true.
    violation_behavior: Flag model as unverified for production use.
    source: FR4.2, FR4.3

  - id: BR4.3
    statement: Secure Credential & Token Handling Policy
    category: policy
    applies_to: colab_train.py
    trigger: Storage or transmission of access tokens
    logic: >
      NEVER hardcode API keys, passwords, or authentication cookies in source files or notebook cells;
      rely strictly on Google Colab CLI native authentication (colab login) or external environment variables.
    violation_behavior: Prevent check-in and sanitize logs.
    source: NFR4
```

## Business Rules Summary Table

| Rule ID | Rule Statement | Category | Target Component / Entity | Source FR / NFR |
| :--- | :--- | :--- | :--- | :--- |
| **BR1.1** | CLI Parameter & Config Validation | Validation | `ColabJobConfig` | FR1.1, FR1.2 |
| **BR1.2** | Dry-Run Local Isolation Policy | Policy | `ColabJobConfig` | FR1.3 |
| **BR1.3** | Colab CLI Process Execution & Return Code | Policy | `colab_train.py` | FR1.4, NFR3 |
| **BR2.1** | Autonomous Notebook Setup & Data Extraction | Constraint | `colab_train_siamese.ipynb` | FR2.1, FR2.2, FR2.5 |
| **BR2.2** | Triplet Optimization & Checkpoint Saving | Calculation | `UniversalTranslatorSiameseNet` | FR2.3, FR2.4 |
| **BR3.1** | Progressive Hardware Baseline Preference | Policy | `HardwareProfile` | FR3.1, NFR1 |
| **BR3.2** | Cost-Benefit Escalation Threshold | Calculation | `HardwareProfile` / Metrics | FR3.2, FR3.3, NFR1 |
| **BR3.3** | Hardware Fallback on Quota Exhaustion | Policy | `HardwareProfile` | FR3.1, NFR3 |
| **BR4.1** | Checkpoint Structure & State Dict Integrity | Validation | `AcousticEvaluationResult` | FR4.1 |
| **BR4.2** | Acoustic Triplet Separation Validation | Calculation | `AcousticEvaluationResult` | FR4.2, FR4.3 |
| **BR4.3** | Secure Credential & Token Handling | Policy | `colab_train.py` | NFR4 |
