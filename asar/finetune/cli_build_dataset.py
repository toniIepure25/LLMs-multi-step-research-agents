"""
CLI: build the SciFact-derived SFT dataset.

Usage:
    uv run python -m asar.finetune.cli_build_dataset \\
        --prepare \\
        --output data/sft/scifact_qa.jsonl \\
        --limit 1500

The actual logic lives in :mod:`asar.finetune.dataset`. This module is just a
thin argparse front end so the script-based and module-based entry points
share the same code path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from asar.execution.rag.scifact_loader import SciFactDatasetAdapter, default_root
from asar.finetune.dataset import build_examples, write_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a SciFact-derived SFT dataset for ASAR.")
    parser.add_argument("--root", default=None, help="SciFact storage root.")
    parser.add_argument(
        "--output",
        default="data/sft/scifact_qa.jsonl",
        help="Output JSONL path.",
    )
    parser.add_argument("--limit", type=int, default=1500, help="Cap on number of examples.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--prepare", action="store_true", help="Run dataset download/normalize first."
    )
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else default_root()
    if args.prepare:
        SciFactDatasetAdapter(root=root).prepare()

    out_path = Path(args.output)
    count = write_dataset(build_examples(root=root, limit=args.limit, seed=args.seed), out_path)
    print(f"Wrote {count} SFT examples -> {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
