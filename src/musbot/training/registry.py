"""Registro de familias de entrenamiento RL disponibles."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from musbot.agents.rl_agent import RLAgent
from musbot.core.motor import MotorMus
from musbot.training.experiment_manager import TrainingConfig
from musbot.training.self_play import (
    EpisodeResult,
    entrenar_vs_opponent,
    evaluar_vs_opponent,
)

TrainFn = Callable[[MotorMus, Any, int, int, str], list[EpisodeResult]]
EvalFn = Callable[[MotorMus, Any, int, int, str], dict[str, float]]
CreateAgentFn = Callable[[TrainingConfig], Any]
LoadAgentFn = Callable[[dict[str, Any]], Any]
SnapshotFn = Callable[[Any], dict[str, Any]]
UpdateCountFn = Callable[[Any], int]


@dataclass(frozen=True, slots=True)
class TrainerDefinition:
    """Describe una familia concreta de entrenamiento."""

    trainer_version: str
    label: str
    description: str
    create_agent: CreateAgentFn
    load_agent: LoadAgentFn
    snapshot_agent: SnapshotFn
    update_count: UpdateCountFn
    train_fn: TrainFn
    eval_fn: EvalFn


def _create_tabular_agent(
    config: TrainingConfig,
    *,
    trainer_version: str,
    state_encoder_version: str,
) -> RLAgent:
    return RLAgent(
        agent_id="rl_main",
        epsilon=config.epsilon,
        learning_rate=config.learning_rate,
        seed=config.seed,
        model_version=trainer_version,
        state_encoder_version=state_encoder_version,
    )


def _load_tabular_agent(payload: dict[str, Any]) -> RLAgent:
    return RLAgent.from_state_dict(payload)


def _snapshot_tabular_agent(agent: Any) -> dict[str, Any]:
    if not isinstance(agent, RLAgent):
        raise TypeError("El trainer tabular esperaba un RLAgent.")
    return agent.snapshot()


def _tabular_update_count(agent: Any) -> int:
    if not isinstance(agent, RLAgent):
        raise TypeError("El trainer tabular esperaba un RLAgent.")
    return agent.update_count


def _tabular_train(
    motor: MotorMus,
    agent: Any,
    episodes: int,
    seed: int,
    opponent: str,
) -> list[EpisodeResult]:
    if not isinstance(agent, RLAgent):
        raise TypeError("El trainer tabular esperaba un RLAgent.")
    return entrenar_vs_opponent(
        motor,
        agent,
        episodes=episodes,
        seed=seed,
        opponent=opponent,
    )


def _tabular_eval(
    motor: MotorMus,
    agent: Any,
    episodes: int,
    seed: int,
    opponent: str,
) -> dict[str, float]:
    if not isinstance(agent, RLAgent):
        raise TypeError("El trainer tabular esperaba un RLAgent.")
    return evaluar_vs_opponent(
        motor,
        agent,
        episodes=episodes,
        seed=seed,
        opponent=opponent,
    )


_TRAINERS: dict[str, TrainerDefinition] = {
    "tabular_v1": TrainerDefinition(
        trainer_version="tabular_v1",
        label="Tabular v1",
        description=(
            "Agente tabular legacy con estado resumido muy simple, "
            "exploracion epsilon-greedy y checkpoints JSON."
        ),
        create_agent=lambda config: _create_tabular_agent(
            config,
            trainer_version="tabular_v1",
            state_encoder_version="v1",
        ),
        load_agent=_load_tabular_agent,
        snapshot_agent=_snapshot_tabular_agent,
        update_count=_tabular_update_count,
        train_fn=_tabular_train,
        eval_fn=_tabular_eval,
    ),
    "tabular_v2": TrainerDefinition(
        trainer_version="tabular_v2",
        label="Tabular v2",
        description=(
            "Agente tabular mejorado con observacion mas rica de envites, "
            "contexto de acciones y actualizacion estable acotada."
        ),
        create_agent=lambda config: _create_tabular_agent(
            config,
            trainer_version="tabular_v2",
            state_encoder_version="v2",
        ),
        load_agent=_load_tabular_agent,
        snapshot_agent=_snapshot_tabular_agent,
        update_count=_tabular_update_count,
        train_fn=_tabular_train,
        eval_fn=_tabular_eval,
    ),
    "tabular_v3": TrainerDefinition(
        trainer_version="tabular_v3",
        label="Tabular v3",
        description=(
            "Agente tabular con foco en informacion publica util de pareja/rivales, "
            "historial resumido y detalles comprimidos de pares y envites."
        ),
        create_agent=lambda config: _create_tabular_agent(
            config,
            trainer_version="tabular_v3",
            state_encoder_version="v3",
        ),
        load_agent=_load_tabular_agent,
        snapshot_agent=_snapshot_tabular_agent,
        update_count=_tabular_update_count,
        train_fn=_tabular_train,
        eval_fn=_tabular_eval,
    ),
    "tabular_v4": TrainerDefinition(
        trainer_version="tabular_v4",
        label="Tabular v4",
        description=(
            "Agente tabular compacto con fuerza exacta por lance, perfil de mano "
            "mas util para mus y contexto publico resumido."
        ),
        create_agent=lambda config: _create_tabular_agent(
            config,
            trainer_version="tabular_v4",
            state_encoder_version="v4",
        ),
        load_agent=_load_tabular_agent,
        snapshot_agent=_snapshot_tabular_agent,
        update_count=_tabular_update_count,
        train_fn=_tabular_train,
        eval_fn=_tabular_eval,
    ),
    "tabular_v5": TrainerDefinition(
        trainer_version="tabular_v5",
        label="Tabular v5 (recomendado)",
        description=(
            "Encoder compacto con ~864 estados teoricos: fase, fuerza del lance, "
            "pares/juego, marcador relativo y contexto de envite. "
            "Learning rate adaptativo 1/(1+n), epsilon decay 0.995/episodio."
        ),
        create_agent=lambda config: _create_tabular_agent(
            config,
            trainer_version="tabular_v5",
            state_encoder_version="v5",
        ),
        load_agent=_load_tabular_agent,
        snapshot_agent=_snapshot_tabular_agent,
        update_count=_tabular_update_count,
        train_fn=_tabular_train,
        eval_fn=_tabular_eval,
    ),
}


def get_trainer_definition(trainer_version: str) -> TrainerDefinition:
    """Recupera una familia registrada por nombre."""

    try:
        return _TRAINERS[trainer_version]
    except KeyError as exc:
        disponibles = ", ".join(sorted(_TRAINERS))
        raise ValueError(
            f"Trainer desconocido: {trainer_version}. Disponibles: {disponibles}"
        ) from exc


def list_trainer_definitions() -> list[TrainerDefinition]:
    """Lista las familias de entrenamiento registradas."""

    return [definition for _, definition in sorted(_TRAINERS.items())]
