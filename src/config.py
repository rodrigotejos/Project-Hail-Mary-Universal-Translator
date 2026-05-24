"""
Global Configuration for Project Hail Mary Universal Translator.
"""

# TRAINING_MODE can be:
# - "local": Runs the Siamese Network training locally (uses GPU RTX if available, else CPU).
# - "cloud": Runs the Siamese Network training on Modal.com using a remote T4 GPU.
TRAINING_MODE = "cloud"

# Space setup for vector database (ChromaDB)
VDB_SPACE = "cosine"
EMBEDDING_DIM = 1024
