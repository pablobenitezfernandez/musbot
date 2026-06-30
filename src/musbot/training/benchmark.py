"""Benchmark reproducible de familias RL entrenables."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from musbot.training.evaluate import evaluate
from musbot.training.train import train


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    """Resultado individual de un trainer con una seed y un baseline de evaluacion."""

    trainer_version: str
    run_id: str
    seed: int
    training_opponent: str
    evaluation_opponent: str
    episodes_trained: int
    checkpoint_used: str
    win_rate: float
    avg_reward: float
    avg_score_diff: float


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    """Resumen agregado del benchmark."""

    records: tuple[BenchmarkRecord, ...]

    def aggregate(self) -> dict[tuple[str, str], dict[str, float]]:
        agrupados: dict[tuple[str, str], list[BenchmarkRecord]] = defaultdict(list)
        for record in self.records:
            agrupados[(record.trainer_version, record.evaluation_opponent)].append(record)

        return {
            clave: {
                "runs": float(len(records)),
                "avg_win_rate": sum(record.win_rate for record in records) / len(records),
                "avg_reward": sum(record.avg_reward for record in records) / len(records),
                "avg_score_diff": (sum(record.avg_score_diff for record in records) / len(records)),
            }
            for clave, records in agrupados.items()
        }


def benchmark_trainers(
    *,
    trainer_versions: Sequence[str] = ("tabular_v1", "tabular_v4"),
    seeds: Sequence[int] = (0, 1, 2),
    root_dir: str | Path = "data/modelos",
    training_opponent: str = "mixed",
    evaluation_opponents: Sequence[str] = ("random", "heuristic", "mixed"),
    episodes_to_run: int = 50,
    checkpoint_interval: int = 10,
    evaluation_interval: int = 10,
    evaluation_hands: int = 20,
    patience: int = 0,
) -> BenchmarkSummary:
    """Entrena y evalua varias familias bajo una configuracion comparable."""

    records: list[BenchmarkRecord] = []
    root_path = Path(root_dir)

    for trainer_version in trainer_versions:
        for seed in seeds:
            train_result = train(
                root_dir=root_path,
                episodes_to_run=episodes_to_run,
                checkpoint_interval=checkpoint_interval,
                evaluation_interval=evaluation_interval,
                evaluation_hands=evaluation_hands,
                seed=seed,
                trainer_version=trainer_version,
                opponent=training_opponent,
                patience=patience,
                notes=(
                    "benchmark:"
                    f" trainer={trainer_version},"
                    f" training_opponent={training_opponent},"
                    f" seed={seed}"
                ),
            )
            for evaluation_opponent in evaluation_opponents:
                eval_result = evaluate(
                    run_id=train_result.run_id,
                    root_dir=root_path,
                    checkpoint="best",
                    episodes=evaluation_hands,
                    seed=seed + 200_000,
                    opponent=evaluation_opponent,
                )
                records.append(
                    BenchmarkRecord(
                        trainer_version=trainer_version,
                        run_id=train_result.run_id,
                        seed=seed,
                        training_opponent=training_opponent,
                        evaluation_opponent=evaluation_opponent,
                        episodes_trained=train_result.total_episodes,
                        checkpoint_used=eval_result.checkpoint_used,
                        win_rate=eval_result.win_rate,
                        avg_reward=eval_result.avg_reward,
                        avg_score_diff=eval_result.avg_score_diff,
                    )
                )

    return BenchmarkSummary(records=tuple(records))
