"""
Helpers and CLI wiring for the local mocked v0 demo path.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path

from asar.common import load_settings
from asar.core.errors import ASARError, ConfigurationError
from asar.deliberation import SimpleSynthesizer
from asar.demo.mock_clients import DEFAULT_DEMO_GOAL, DeterministicDemoLLMClient, DeterministicDemoSearchClient
from asar.evaluation import ExperimentLogger
from asar.execution import WebSearchExecutor
from asar.memory import WorkingMemory
from asar.orchestration import SequentialOrchestrator
from asar.planning import SimplePlanner
from asar.providers import build_live_llm_client, build_live_search_client
from asar.verification import EvidenceChecker
from schemas.research_output import ResearchOutput


def build_demo_orchestrator(
    *,
    config_dir: str | Path = "config",
    output_dir: str | Path | None = None,
    mode: str = "mock",
) -> SequentialOrchestrator:
    """Build the real v0 pipeline wired to mock or live providers."""

    settings = load_settings(config_dir)
    if mode == "mock":
        llm_client = DeterministicDemoLLMClient()
        search_client = DeterministicDemoSearchClient()
    elif mode == "live":
        llm_client = build_live_llm_client(settings)
        search_client = build_live_search_client()
    else:
        raise ConfigurationError(
            "Unsupported demo mode",
            details={"mode": mode, "supported_modes": ["mock", "live"]},
        )

    return SequentialOrchestrator(
        planner=SimplePlanner(llm_client, settings),
        executor=WebSearchExecutor(search_client, settings),
        memory=WorkingMemory(max_items=settings.pipeline.memory.working_memory_max_items),
        synthesizer=SimpleSynthesizer(llm_client, settings),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=output_dir),
        settings=settings,
    )


async def run_demo_pipeline(
    goal: str = DEFAULT_DEMO_GOAL,
    *,
    config_dir: str | Path = "config",
    output_dir: str | Path | None = None,
    mode: str = "mock",
) -> ResearchOutput:
    """Run the real v0 pipeline with mock or live provider clients."""

    orchestrator = build_demo_orchestrator(
        config_dir=config_dir,
        output_dir=output_dir,
        mode=mode,
    )
    return await orchestrator.run(goal)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local v0 demo and print the artifact location for manual inspection."""

    parser = argparse.ArgumentParser(description="Run the local ASAR v0 demo pipeline.")
    parser.add_argument(
        "goal",
        nargs="?",
        default=DEFAULT_DEMO_GOAL,
        help="Research goal to run through the v0 pipeline.",
    )
    parser.add_argument("--config-dir", default="config", help="Path to the ASAR config directory.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional override for the experiment output directory.",
    )
    parser.add_argument(
        "--mode",
        choices=("mock", "live"),
        default="mock",
        help="Run with deterministic mocks or live provider adapters.",
    )
    args = parser.parse_args(argv)

    try:
        output = asyncio.run(
            run_demo_pipeline(
                args.goal,
                config_dir=args.config_dir,
                output_dir=args.output_dir,
                mode=args.mode,
            )
        )
    except ASARError as exc:
        print(f"ASAR demo failed: {exc.message}", file=sys.stderr)
        if exc.details:
            print(f"Details: {exc.details}", file=sys.stderr)
        return 2

    print(f"Demo goal: {output.goal}")
    print(f"Mode: {args.mode}")
    print(f"Plan steps: {len(output.plan.steps)}")
    print(f"Evidence items: {len(output.evidence)}")
    if output.experiment is not None and output.experiment.artifacts:
        print(f"ResearchOutput artifact: {output.experiment.artifacts[0]}")
        print(f"ExperimentRecord artifact: {output.experiment.artifacts[1]}")
    else:
        print("No experiment artifacts were written.")
    return 0
