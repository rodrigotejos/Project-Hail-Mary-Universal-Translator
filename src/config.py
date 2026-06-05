"""
Global Configuration for Project Hail Mary Universal Translator.
"""

# TRAINING_MODE can be:
# - "local": Runs the Siamese Network training locally (uses GPU RTX if available, else CPU).
# - "cloud": Runs the Siamese Network training on Modal.com using a remote T4 GPU.
TRAINING_MODE = "cloud"

# ACOUSTIC_MODEL_BACKBONE can be:
# - "mobilenet": Lightweight CNN model (trained from scratch/fine-tuned locally).
# - "ast": Google's Audio Spectrogram Transformer (pre-trained on AudioSet, high accuracy).
ACOUSTIC_MODEL_BACKBONE = "ast"

# Space setup for vector database (ChromaDB)
VDB_SPACE = "cosine"
EMBEDDING_DIM = 1024

# Cloud training configurations (Modal.com)
# GPU options: "T4", "L4", "A10G", "A100", "H100" (or None/empty string for CPU)
CLOUD_GPU_MOBILENET = "T4"
CLOUD_GPU_AST = "L4"
CLOUD_TIMEOUT = 1200  # Execution timeout in seconds (20 minutes)

