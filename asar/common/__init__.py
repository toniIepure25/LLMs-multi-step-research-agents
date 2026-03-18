"""
Common — Shared utilities, logging, and configuration loading.

Responsibilities:
- Structured logging setup
- Configuration loading from TOML files
- ID generation utilities
- Shared helper functions

This module must NOT import from any layer module.
It provides utilities that any module can use.

TODO: Implement config loader (read config/*.toml, merge with env vars)
TODO: Implement structured logger with trace ID support
TODO: Implement ID generator (for plan_id, task_id, evidence_id, etc.)
"""

from asar.common.config import (
    ASARSettings,
    ExecutionSettings,
    ExperimentDefaults,
    ExperimentEvaluationSettings,
    ExperimentSettings,
    LoggingSettings,
    MemorySettings,
    ModelRouteSettings,
    ModelsSettings,
    PipelineLayerSettings,
    PipelineSettings,
    ProjectSettings,
    load_settings,
)
from asar.common.ids import IDPrefix, generate_id, generate_trace_id
from asar.common.logging import TraceLoggerAdapter, get_logger, setup_logging

__all__ = [
    "ASARSettings",
    "ProjectSettings",
    "ModelRouteSettings",
    "ModelsSettings",
    "PipelineLayerSettings",
    "ExecutionSettings",
    "MemorySettings",
    "LoggingSettings",
    "PipelineSettings",
    "ExperimentDefaults",
    "ExperimentEvaluationSettings",
    "ExperimentSettings",
    "load_settings",
    "IDPrefix",
    "generate_id",
    "generate_trace_id",
    "TraceLoggerAdapter",
    "setup_logging",
    "get_logger",
]
