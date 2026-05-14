"""CLI: build a SciFact-derived DPO preference dataset.

Example:

    uv run python -m asar.finetune.cli_build_preference \\
        --prepare --output data/dpo/scifact_pref.jsonl --limit 1000
"""

from __future__ import annotations

import argparse
from pathlib import Path

from asar.execution.rag.scifact_loader import SciFactDatasetAdapter, default_root
from asar.finetune.preference_dataset import (
    build_preference_pairs,
    write_preference_dataset,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a SciFact-derived DPO preference dataset.",
    )
    parser.add_argument(
        "--scifact-root",
        default=str(default_root()),
        help="Root directory of the normalized SciFact corpus.",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Download + normalize SciFact if it is not already prepared.",
    )
    parser.add_argument(
        "--output",
        default="data/dpo/scifact_pref.jsonl",
        help="Where to write the preference JSONL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of source documents to use.",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    root = Path(args.scifact_root)
    if args.prepare:
        adapter = SciFactDatasetAdapter(root=root)
        adapter.prepare(download=True)

    out_path = Path(args.output)
    pairs = build_preference_pairs(root=root, limit=args.limit, seed=args.seed)
    count = write_preference_dataset(pairs, out_path)
    print(f"Wrote {count} preference pairs to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
