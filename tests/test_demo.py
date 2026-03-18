"""
Tests for the local mocked v0 demo entrypoint.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from asar.demo import DEFAULT_DEMO_GOAL, main, run_demo_pipeline


@pytest.mark.asyncio
async def test_run_demo_pipeline_returns_output_and_writes_artifacts(tmp_path: Path) -> None:
    output = await run_demo_pipeline(output_dir=tmp_path)

    assert output.goal == DEFAULT_DEMO_GOAL
    assert output.experiment is not None
    assert len(output.experiment.artifacts) == 2
    assert all(Path(path).exists() for path in output.experiment.artifacts)


def test_demo_main_prints_artifact_paths(tmp_path: Path, capsys) -> None:
    exit_code = main(["--output-dir", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ResearchOutput artifact:" in captured.out
    assert "ExperimentRecord artifact:" in captured.out
