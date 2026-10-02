# Performance Test Instructions: Accelerator Benchmarking & Cost-Efficiency

## Benchmark Objectives & Profiling

Performance testing validates that:
1. The hardware accelerator catalog accurately projects relative throughput across CPU, T4, V100, A100, and TPU.
2. The cost-efficiency metric formula correctly identifies diminishing returns when escalating beyond the baseline T4 tier.

## Accelerator Matrix Performance Profiling

To execute the hardware catalog and efficiency calculation tests:

```bash
python -m pytest tests/test_colab_train.py -k "TestHardwareProfilesAndEfficiency" -v
```

Profiles evaluated:
- **`none` (CPU)**: 0.15x relative speedup, 0.2x relative cost factor.
- **`t4` (GPU)**: 1.0x baseline speedup, 1.0x cost factor (Efficiency = 1.0).
- **`v100` (GPU)**: 1.8x projected speedup, 2.5x cost factor.
- **`a100` (GPU)**: 3.2x projected speedup, 4.0x cost factor.
- **`tpu` (TPU)**: 2.4x projected speedup, 3.0x cost factor.

## Cost-Efficiency Threshold Assertions

- Under Rule **BR3.2**, an accelerator escalation must yield an efficiency ratio $\ge 1.25$.
- If an A100 delivers only 1.5x speedup for a 4.0x cost multiplier (efficiency = 0.38), the system MUST emit a recommendation warning to downgrade to T4.
- If high batch sizes enable a 9.0x speedup (efficiency = 2.25), the system MUST confirm that the high-tier instance is cost-justified.
