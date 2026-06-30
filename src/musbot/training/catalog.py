"""Catalogo de runs y modelos entrenados."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from musbot.training.experiment_manager import TrainingRunManager


@dataclass(frozen=True, slots=True)
class ModelRunSummary:
    """Resumen de un run entrenado o en entrenamiento."""

    run_id: str
    trainer_version: str
    status: str
    total_episodes: int
    total_updates: int
    best_metric: float | None
    latest_checkpoint: str | None
    best_checkpoint: str | None
    created_at: str
    updated_at: str
    notes: str
    parent_run_id: str | None
    parent_checkpoint: str | None
    run_dir: Path


def list_model_runs(root_dir: str | Path = "data/modelos") -> list[ModelRunSummary]:
    """Lista todos los runs disponibles en disco."""

    manager = TrainingRunManager(root_dir=root_dir)
    summaries: list[ModelRunSummary] = []

    for run_dir in sorted(manager.root_dir.glob("run_*")):
        if not run_dir.is_dir():
            continue
        try:
            paths, config, state = manager.load_run(run_dir.name)
        except FileNotFoundError:
            continue

        summaries.append(
            ModelRunSummary(
                run_id=state.run_id,
                trainer_version=config.trainer_version,
                status=state.status,
                total_episodes=state.total_episodes,
                total_updates=state.total_updates,
                best_metric=state.best_metric,
                latest_checkpoint=state.latest_checkpoint,
                best_checkpoint=state.best_checkpoint,
                created_at=state.created_at,
                updated_at=state.updated_at,
                notes=state.notes,
                parent_run_id=state.parent_run_id,
                parent_checkpoint=state.parent_checkpoint,
                run_dir=paths.run_dir,
            )
        )

    return summaries


def best_model_run(
    root_dir: str | Path = "data/modelos",
    *,
    trainer_version: str | None = None,
) -> ModelRunSummary | None:
    """Devuelve el mejor run segun la mejor metrica registrada."""

    candidates = [
        run
        for run in list_model_runs(root_dir=root_dir)
        if run.best_metric is not None
        and (trainer_version is None or run.trainer_version == trainer_version)
    ]
    if not candidates:
        return None

    return max(
        candidates,
        key=lambda run: (
            float(run.best_metric or float("-inf")),
            run.total_episodes,
            run.run_id,
        ),
    )
