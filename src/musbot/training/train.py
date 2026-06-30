"""Punto de entrada para entrenamiento."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from musbot.analysis.model_behavior import write_behavior_report
from musbot.core.motor import MotorMus
from musbot.training.experiment_manager import (
    TrainingConfig,
    TrainingRunManager,
)
from musbot.training.registry import get_trainer_definition


@dataclass(frozen=True, slots=True)
class TrainingResult:
    """Resultado de una sesion de entrenamiento."""

    run_id: str
    run_dir: Path
    total_episodes: int
    latest_checkpoint: str | None
    best_checkpoint: str | None
    best_metric: float | None


def train(
    *,
    root_dir: str | Path = "data/modelos",
    episodes_to_run: int = 50,
    checkpoint_interval: int = 10,
    evaluation_interval: int = 10,
    evaluation_hands: int = 20,
    seed: int = 0,
    epsilon: float = 0.1,
    learning_rate: float = 0.1,
    opponent: str = "mixed",
    notes: str = "",
    trainer_version: str | None = None,
    resume_run_id: str | None = None,
    fork_from_run_id: str | None = None,
    fork_checkpoint: str = "latest",
) -> TrainingResult:
    """Entrena o reanuda un agente RL tabular."""

    manager = TrainingRunManager(root_dir=root_dir)
    motor = MotorMus()

    if resume_run_id is not None and fork_from_run_id is not None:
        raise ValueError("No se puede hacer resume y fork a la vez.")

    if resume_run_id is not None:
        paths, config, state = manager.load_run(resume_run_id)
        if trainer_version is not None and trainer_version != config.trainer_version:
            raise ValueError(
                "No se puede reanudar un run con una familia RL distinta a la original."
            )
        trainer = get_trainer_definition(config.trainer_version)
        checkpoint_payload = manager.load_checkpoint(paths.latest_checkpoint_path)
        agent = trainer.load_agent(checkpoint_payload["agent_state"])
        state.status = "running"
        config = TrainingConfig(
            episodes_to_run=episodes_to_run,
            checkpoint_interval=checkpoint_interval,
            evaluation_interval=evaluation_interval,
            evaluation_hands=evaluation_hands,
            seed=seed,
            epsilon=agent.epsilon,
            learning_rate=agent.learning_rate,
            notes=notes or config.notes,
            trainer_version=config.trainer_version,
            opponent=config.opponent,
        )
        manager.save_config(paths, config)
    elif fork_from_run_id is not None:
        parent_paths, parent_config, _ = manager.load_run(fork_from_run_id)
        if trainer_version is not None and trainer_version != parent_config.trainer_version:
            raise ValueError(
                "No se puede bifurcar cambiando de familia RL en esta primera version."
            )
        trainer = get_trainer_definition(parent_config.trainer_version)
        checkpoint_path = manager.checkpoint_path(parent_paths, fork_checkpoint)
        checkpoint_payload = manager.load_checkpoint(checkpoint_path)
        agent = trainer.load_agent(checkpoint_payload["agent_state"])
        paths, state = manager.create_run(
            TrainingConfig(
                episodes_to_run=episodes_to_run,
                checkpoint_interval=checkpoint_interval,
                evaluation_interval=evaluation_interval,
                evaluation_hands=evaluation_hands,
                seed=seed,
                epsilon=getattr(agent, "epsilon", epsilon),
                learning_rate=getattr(agent, "learning_rate", learning_rate),
                notes=notes,
                trainer_version=parent_config.trainer_version,
                opponent=parent_config.opponent,
            ),
            parent_run_id=fork_from_run_id,
            parent_checkpoint=checkpoint_path.name,
        )
        config = TrainingConfig(**manager._read_json(paths.config_path))
    else:
        resolved_trainer_version = trainer_version or "tabular_v1"
        trainer = get_trainer_definition(resolved_trainer_version)
        config = TrainingConfig(
            episodes_to_run=episodes_to_run,
            checkpoint_interval=checkpoint_interval,
            evaluation_interval=evaluation_interval,
            evaluation_hands=evaluation_hands,
            seed=seed,
            epsilon=epsilon,
            learning_rate=learning_rate,
            notes=notes,
            trainer_version=resolved_trainer_version,
            opponent=opponent,
        )
        paths, state = manager.create_run(config)
        agent = trainer.create_agent(config)
        manager.save_checkpoint(
            paths,
            state,
            episode=0,
            agent_state=trainer.snapshot_agent(agent),
            metadata={"kind": "initial"},
        )

    episodios_iniciales = state.total_episodes
    resultados = trainer.train_fn(
        motor,
        agent,
        config.episodes_to_run,
        config.seed + episodios_iniciales,
        config.opponent,
    )

    acumuladas: list[float] = []
    acumulados_diff: list[int] = []
    for indice, resultado in enumerate(resultados, start=1):
        episodio_global = episodios_iniciales + indice
        reward = resultado.reward_by_team["equipo_1"]
        diferencial = resultado.score_delta["equipo_1"] - resultado.score_delta["equipo_2"]
        acumuladas.append(reward)
        acumulados_diff.append(diferencial)
        state.total_episodes = episodio_global
        state.total_updates = trainer.update_count(agent)

        metric_record: dict[str, float | int | str] | None = None
        if episodio_global % config.evaluation_interval == 0:
            evaluacion = trainer.eval_fn(
                motor,
                agent,
                config.evaluation_hands,
                config.seed + 100_000 + episodio_global,
                config.opponent,
            )
            metric_record = {
                "episode": episodio_global,
                "win_rate": evaluacion["win_rate"],
                "avg_reward": sum(acumuladas) / len(acumuladas),
                "avg_score_diff": sum(acumulados_diff) / len(acumulados_diff),
            }
            manager.append_metric(paths, metric_record)
            manager.update_summary(paths, config, state, metric_record)
            behavior_summary = evaluacion.get("behavior_summary")
            if isinstance(behavior_summary, dict):
                write_behavior_report(
                    run_dir=paths.run_dir,
                    run_id=state.run_id,
                    trainer_version=config.trainer_version,
                    checkpoint_used=state.latest_checkpoint or "latest",
                    opponent=config.opponent,
                    metrics=metric_record,
                    behavior_summary=behavior_summary,
                    agent=agent,
                )
            acumuladas.clear()
            acumulados_diff.clear()

        if episodio_global % config.checkpoint_interval == 0:
            metric_value = None if metric_record is None else float(metric_record["win_rate"])
            manager.save_checkpoint(
                paths,
                state,
                episode=episodio_global,
                agent_state=trainer.snapshot_agent(agent),
                metric_value=metric_value,
                metadata={"trainer_version": config.trainer_version},
            )

    if state.total_episodes and state.total_episodes % config.checkpoint_interval != 0:
        ultima_metrica = manager.read_metrics(paths)
        metric_value = None if not ultima_metrica else float(ultima_metrica[-1]["win_rate"])
        manager.save_checkpoint(
            paths,
            state,
            episode=state.total_episodes,
            agent_state=trainer.snapshot_agent(agent),
            metric_value=metric_value,
            metadata={"trainer_version": config.trainer_version, "kind": "final"},
        )

    state.status = "completed"
    manager.save_state(paths, state)
    manager.update_summary(paths, config, state)
    return TrainingResult(
        run_id=state.run_id,
        run_dir=paths.run_dir,
        total_episodes=state.total_episodes,
        latest_checkpoint=state.latest_checkpoint,
        best_checkpoint=state.best_checkpoint,
        best_metric=state.best_metric,
    )
