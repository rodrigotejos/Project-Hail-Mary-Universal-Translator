# Domain Entities: Google Colab Cloud Training & Progressive Benchmarking

## Entity Model Specification

```yaml
entities:
  - name: ColabJobConfig
    description: Encapsulates all execution and environment parameters required to prepare, run, or simulate a Colab training job.
    attributes:
      - name: job_id
        type: string
        required: true
        unique: true
        constraints: Non-empty alphanumeric string or ISO timestamp identifier.
      - name: accelerator_type
        type: string
        required: true
        allowed_values: [none, t4, v100, a100, tpu]
        default: t4
        constraints: Must match an active HardwareProfile identifier.
      - name: epochs
        type: integer
        required: true
        default: 30
        min: 1
        max: 1000
        constraints: Strictly positive integer.
      - name: batch_size
        type: integer
        required: true
        default: 32
        min: 1
        max: 512
        constraints: Batch size for triplet pairs.
      - name: learning_rate
        type: float
        required: true
        default: 0.0005
        min: 0.000001
        max: 0.1
        constraints: Initial optimizer learning rate.
      - name: backbone
        type: string
        required: true
        allowed_values: [mobilenet, ast]
        default: mobilenet
        constraints: Siamese acoustic feature extractor backbone.
      - name: dry_run
        type: boolean
        required: true
        default: false
        constraints: If true, verifies local environment and bundle packaging without launching external Colab CLI process.
      - name: notebook_path
        type: string
        required: true
        default: notebooks/colab_train_siamese.ipynb
        constraints: Relative path to version-controlled Jupyter notebook.
      - name: output_dir
        type: string
        required: true
        default: models/colab_runs
        constraints: Local target directory to collect downloaded checkpoints and metrics.
    constraints:
      - When dry_run is true, network calls and external processes are completely omitted.
      - When accelerator_type is tpu, PyTorch XLA setup must be initialized in the notebook runtime.
    relationships:
      - target: HardwareProfile
        cardinality: N:1
        direction: references
      - target: TrainingMetrics
        cardinality: 1:1
        direction: produces

  - name: HardwareProfile
    description: Defines computational specifications, relative cost weight, and performance expectation for each supported Google Colab accelerator.
    attributes:
      - name: profile_id
        type: string
        required: true
        unique: true
        allowed_values: [none, t4, v100, a100, tpu]
      - name: accelerator_class
        type: string
        required: true
        allowed_values: [cpu, gpu, tpu]
      - name: vram_gb
        type: float
        required: true
        min: 0.0
        constraints: Dedicated memory size in Gigabytes (0 for CPU).
      - name: relative_cost_factor
        type: float
        required: true
        min: 0.0
        constraints: Relative cost per compute unit normalized to T4 (e.g., none=0.0, t4=1.0, v100=2.5, a100=4.0, tpu=3.0).
      - name: expected_speedup_vs_t4
        type: float
        required: true
        min: 0.1
        constraints: Projected throughput ratio compared to T4 baseline (e.g., none=0.15, t4=1.0, v100=1.8, a100=3.2, tpu=2.4).
      - name: cost_benefit_threshold
        type: float
        required: true
        default: 1.25
        constraints: Minimum speedup-to-cost ratio required to recommend this hardware profile over the lower tier.
    constraints:
      - Baseline tier t4 is defined as cost reference with relative_cost_factor equal to 1.0.
    relationships:
      - target: ColabJobConfig
        cardinality: 1:N
        direction: referenced_by

  - name: TrainingMetrics
    description: Quantitative measurements recorded during or after execution of a training job.
    attributes:
      - name: job_id
        type: string
        required: true
        unique: true
        references: ColabJobConfig.job_id
      - name: accelerator_used
        type: string
        required: true
      - name: total_epochs_completed
        type: integer
        required: true
        min: 0
      - name: total_duration_seconds
        type: float
        required: true
        min: 0.0
      - name: seconds_per_epoch
        type: float
        required: true
        min: 0.0
      - name: final_train_loss
        type: float
        required: true
      - name: final_val_loss
        type: float
        required: true
      - name: peak_vram_mb
        type: float
        required: false
        min: 0.0
      - name: relative_efficiency_score
        type: float
        required: true
        constraints: Calculated as (t4_seconds_per_epoch / seconds_per_epoch) / relative_cost_factor.
      - name: recorded_at
        type: string
        required: true
        constraints: ISO 8601 UTC timestamp.
    constraints:
      - seconds_per_epoch must equal total_duration_seconds divided by total_epochs_completed when total_epochs_completed > 0.
    relationships:
      - target: ColabJobConfig
        cardinality: 1:1
        direction: belongs_to
      - target: AcousticEvaluationResult
        cardinality: 1:1
        direction: correlates_with

  - name: AcousticEvaluationResult
    description: Validation metrics computed on the trained checkpoint evaluating triplet separation and embedding discriminability.
    attributes:
      - name: evaluation_id
        type: string
        required: true
        unique: true
      - name: job_id
        type: string
        required: true
        references: ColabJobConfig.job_id
      - name: checkpoint_path
        type: string
        required: true
        constraints: Valid local filesystem path to the downloaded .pth state dict.
      - name: mean_positive_distance
        type: float
        required: true
        min: 0.0
        max: 2.0
        constraints: Average cosine distance between same-language audio embeddings.
      - name: mean_negative_distance
        type: float
        required: true
        min: 0.0
        max: 2.0
        constraints: Average cosine distance between different-language audio embeddings.
      - name: separation_delta
        type: float
        required: true
        constraints: Computed as (mean_negative_distance - mean_positive_distance).
      - name: min_required_margin
        type: float
        required: true
        default: 0.15
        constraints: Minimum positive difference required for acceptance.
      - name: passed
        type: boolean
        required: true
        constraints: True if separation_delta >= min_required_margin.
    constraints:
      - If passed is false, the checkpoint is flagged as substandard and not promoted to production inference.
    relationships:
      - target: ColabJobConfig
        cardinality: 1:1
        direction: validates
```

## Entity Model Summary

The domain model structures the lifecycle of Colab-based cloud acoustic training into four cohesive entities:

1. **`ColabJobConfig`**: Represents the job intent and operational parameters, decoupling runtime arguments (`accelerator_type`, `epochs`, `backbone`, `dry_run`) from low-level execution logic.
2. **`HardwareProfile`**: Defines the hardware tier catalog (CPU, T4, V100, A100, TPU) with relative cost factors and baseline benchmarks, enabling objective cost-benefit evaluation.
3. **`TrainingMetrics`**: Collects runtime profiling (seconds/epoch, memory footprint, loss curves) and computes the relative cost-efficiency index.
4. **`AcousticEvaluationResult`**: Measures the statistical quality of the produced Siamese embeddings, ensuring that acoustic triplets achieve the required separation margin before deployment.
