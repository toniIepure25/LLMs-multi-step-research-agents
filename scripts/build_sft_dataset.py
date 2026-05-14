"""Thin shim that delegates to :mod:`asar.finetune.cli_build_dataset`."""

from __future__ import annotations

import sys

from asar.finetune.cli_build_dataset import main


if __name__ == "__main__":
    sys.exit(main())
