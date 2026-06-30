"""Punto de entrada para evaluacion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from musbot.analysis.model_behavior import write_behavior_report
from musbot.core.motor import MotorMus
from musbot.training.experiment_manager import TrainingRunManager
from musbot.training.registry import get_trainer_definition


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Resultado agregado de una evaluacion."""

    run_id: str
    checkpoint_used: str
    win_rate: float
    avg_reward: float
    avg_score_diff: float
    behavior_report_paths: tuple[str, ...] = ()


def evaluate(
    *,
    run_id: str,
    root_dir: str | Path = "data/modelos",
    checkpoint: str = "best",
    episodes: int = 50,
    seed: int = 12345,
    opponent: str | None = None,
) -> EvaluationResult:
    """Evalua un run o checkpoint frente a oponentes aleatorios."""

    manager = TrainingRunManager(root_dir=root_dir)
    paths, config, state = manager.load_run(run_id)
    trainer = get_trainer_definition(config.trainer_version)
    checkpoint_path = manager.checkpoint_path(paths, checkpoint)
    if not checkpoint_path.exists():
        checkpoint_path = paths.checkpoints_dir / (state.latest_checkpoint or "")
    payload = manager.load_checkpoint(checkpoint_path)
    agent = trainer.load_agent(payload["agent_state"])
    metrics = trainer.eval_fn(
        MotorMus(),
        agent,
        episodes,
        seed,
        opponent or config.opponent,
    )
    report_paths: tuple[str, ...] = ()
    behavior_summary = metrics.get("behavior_summary")
    if isinstance(behavior_summary, dict):
        report_paths = tuple(
            str(path)
            for path in write_behavior_report(
                run_dir=paths.run_dir,
                run_id=run_id,
                trainer_version=config.trainer_version,
                checkpoint_used=checkpoint_path.name,
                opponent=opponent or config.opponent,
                metrics=metrics,
                behavior_summary=behavior_summary,
                agent=agent,
            )
        )
    return EvaluationResult(
        run_id=run_id,
        checkpoint_used=checkpoint_path.name,
        win_rate=metrics["win_rate"],
        avg_reward=metrics["avg_reward"],
        avg_score_diff=metrics["avg_score_diff"],
        behavior_report_paths=report_paths,
    )
