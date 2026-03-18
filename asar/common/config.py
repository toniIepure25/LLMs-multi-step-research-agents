"""
Typed configuration loading for ASAR foundation modules.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from asar.core.errors import ConfigurationError

try:  # pragma: no cover - import path depends on runtime Python
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


class ProjectSettings(BaseModel):
    """Metadata from `config/project.toml`."""

    name: str
    version: str
    description: str
    phase: str
    authors: dict[str, str] = Field(default_factory=dict)


class ProjectConfig(BaseModel):
    """Project config file wrapper."""

    model_config = ConfigDict(extra="ignore")

    project: ProjectSettings


class ModelRouteSettings(BaseModel):
    """Provider routing for one model consumer."""

    provider: str
    model: str
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(ge=1)


class ModelsSettings(BaseModel):
    """Model routing configuration across v0 components."""

    model_config = ConfigDict(extra="ignore")

    default: ModelRouteSettings
    planning: ModelRouteSettings | None = None
    execution: ModelRouteSettings | None = None
    deliberation: ModelRouteSettings | None = None
    verification: ModelRouteSettings | None = None

    def route_for(self, layer: str) -> ModelRouteSettings:
        route = getattr(self, layer, None)
        if isinstance(route, ModelRouteSettings):
            return route
        return self.default


class PipelineLayerSettings(BaseModel):
    """Per-layer feature toggles."""

    planning: bool
    execution: bool
    memory: bool
    grounding: bool
    deliberation: bool
    verification: bool
    evaluation: bool


class ExecutionSettings(BaseModel):
    """Execution-related pipeline settings."""

    parallel: bool
    max_parallel_tasks: int = Field(ge=1)
    timeout_seconds: int = Field(ge=1)


class MemorySettings(BaseModel):
    """Memory-related pipeline settings."""

    working_memory_max_items: int = Field(ge=1)
    compression_enabled: bool
    long_term_storage: bool


class LoggingSettings(BaseModel):
    """Logging configuration used by foundation utilities."""

    level: Literal["debug", "info", "warning", "error", "critical"]
    log_all_llm_calls: bool
    log_schemas: bool


class PipelineSettings(BaseModel):
    """Pipeline config file wrapper."""

    model_config = ConfigDict(extra="ignore")

    layers: PipelineLayerSettings
    execution: ExecutionSettings
    memory: MemorySettings
    logging: LoggingSettings


class ExperimentDefaults(BaseModel):
    """Default settings for experiments."""

    seed: int
    output_dir: str
    log_level: str
    cache_llm_responses: bool


class BenchmarkSettings(BaseModel):
    """Benchmark configuration."""

    data_dir: str
    default_tier: int


class ExperimentEvaluationSettings(BaseModel):
    """Evaluation defaults for experiments."""

    human_eval_enabled: bool
    automated_metrics: list[str] = Field(default_factory=list)


class ExperimentSettings(BaseModel):
    """Experiment config file wrapper."""

    model_config = ConfigDict(extra="ignore")

    defaults: ExperimentDefaults
    benchmarks: BenchmarkSettings
    evaluation: ExperimentEvaluationSettings


class ASARSettings(BaseModel):
    """Merged typed settings across all config files."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config_dir: Path
    project: ProjectSettings
    models: ModelsSettings
    pipeline: PipelineSettings
    experiments: ExperimentSettings


def load_settings(config_dir: str | Path = "config") -> ASARSettings:
    """Load and validate all ASAR config files from a directory."""

    resolved_dir = Path(config_dir).expanduser().resolve()
    try:
        project_raw = _read_toml(resolved_dir / "project.toml")
        models_raw = _read_toml(resolved_dir / "models.toml")
        pipeline_raw = _read_toml(resolved_dir / "pipeline.toml")
        experiments_raw = _read_toml(resolved_dir / "experiments.toml")
    except OSError as exc:
        raise ConfigurationError(
            "Unable to read configuration files",
            details={"config_dir": str(resolved_dir), "error": str(exc)},
        ) from exc

    project = _validate(ProjectConfig, project_raw, "project.toml").project
    models = _validate(
        ModelsSettings,
        _apply_model_env_overrides(models_raw),
        "models.toml",
    )
    pipeline = _validate(
        PipelineSettings,
        _apply_pipeline_env_overrides(pipeline_raw),
        "pipeline.toml",
    )
    experiments = _validate(ExperimentSettings, experiments_raw, "experiments.toml")

    return ASARSettings(
        config_dir=resolved_dir,
        project=project,
        models=models,
        pipeline=pipeline,
        experiments=experiments,
    )


def _validate(model_cls: type[BaseModel], data: dict[str, Any], filename: str) -> BaseModel:
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(
            f"Invalid configuration in {filename}",
            details={"file": filename, "errors": exc.errors()},
        ) from exc


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(
            "Missing configuration file",
            details={"path": str(path)},
        )
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _apply_model_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    overridden = _deep_copy(data)
    fields = ("provider", "model", "temperature", "max_tokens")
    sections = ("default", "planning", "execution", "deliberation", "verification")

    for field in fields:
        alias_name = f"ASAR_MODEL_{field.upper()}"
        if alias_name in os.environ:
            alias_value = _coerce_env_value(os.environ[alias_name], overridden.get("default", {}).get(field))
            _set_nested_value(
                overridden,
                ("default", field),
                alias_value,
            )
            for section in sections:
                if section == "default":
                    continue
                section_env_name = f"ASAR_{section.upper()}_{field.upper()}"
                if section_env_name in os.environ:
                    continue
                if section in overridden:
                    _set_nested_value(overridden, (section, field), alias_value)

    for section in sections:
        for field in fields:
            env_name = f"ASAR_{section.upper()}_{field.upper()}"
            if env_name not in os.environ:
                continue
            current = overridden.get(section, {}).get(field)
            _set_nested_value(
                overridden,
                (section, field),
                _coerce_env_value(os.environ[env_name], current),
            )

    return overridden


def _apply_pipeline_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    overridden = _deep_copy(data)
    if "ASAR_LOG_LEVEL" in os.environ:
        current = overridden.get("logging", {}).get("level")
        _set_nested_value(
            overridden,
            ("logging", "level"),
            _coerce_env_value(os.environ["ASAR_LOG_LEVEL"], current),
        )
    return overridden


def _deep_copy(data: dict[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            copied[key] = _deep_copy(value)
        else:
            copied[key] = value
    return copied


def _set_nested_value(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current: dict[str, Any] = data
    for key in path[:-1]:
        next_value = current.get(key)
        if not isinstance(next_value, dict):
            next_value = {}
            current[key] = next_value
        current = next_value
    current[path[-1]] = value


def _coerce_env_value(raw: str, current: Any) -> Any:
    if isinstance(current, bool):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(current, int) and not isinstance(current, bool):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    return raw
