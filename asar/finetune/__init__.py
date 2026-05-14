"""
Fine-tuning subsystem — dataset preparation + LoRA training entry point.

This package lives outside the v0 layer architecture intentionally: it
produces the **adapter artifact** that the ``LocalSLMClient`` provider
consumes at inference time. From the rest of the pipeline's point of view,
fine-tuning is a one-time offline step.
"""

from asar.finetune.dataset import build_examples, write_dataset
from asar.finetune.preference_dataset import build_preference_pairs, write_preference_dataset

__all__ = [
    "build_examples",
    "write_dataset",
    "build_preference_pairs",
    "write_preference_dataset",
]
