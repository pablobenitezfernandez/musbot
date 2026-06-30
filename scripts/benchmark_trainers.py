"""Script para comparar familias RL con entrenamiento y evaluacion reproducibles."""

from __future__ import annotations

import argparse

from musbot.training.benchmark import benchmark_trainers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trainer-versions",
        nargs="+",
        default=["tabular_v1", "tabular_v4"],
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--root-dir", default="data/modelos")
    parser.add_argument(
        "--training-opponent",
        default="mixed",
        choices=("random", "heuristic", "mixed"),
    )
    parser.add_argument(
        "--evaluation-opponents",
        nargs="+",
        default=["random", "heuristic", "mixed"],
    )
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--checkpoint-interval", type=int, default=10)
    parser.add_argument("--evaluation-interval", type=int, default=10)
    parser.add_argument("--evaluation-hands", type=int, default=20)
    args = parser.parse_args()

    resumen = benchmark_trainers(
        trainer_versions=args.trainer_versions,
        seeds=args.seeds,
        root_dir=args.root_dir,
        training_opponent=args.training_opponent,
        evaluation_opponents=args.evaluation_opponents,
        episodes_to_run=args.episodes,
        checkpoint_interval=args.checkpoint_interval,
        evaluation_interval=args.evaluation_interval,
        evaluation_hands=args.evaluation_hands,
    )

    print("Resultados individuales:")
    for record in resumen.records:
        print(
            f"- {record.trainer_version} | seed={record.seed} | "
            f"eval_vs={record.evaluation_opponent} | run_id={record.run_id} | "
            f"win_rate={record.win_rate:.3f} | avg_reward={record.avg_reward:.3f} | "
            f"avg_score_diff={record.avg_score_diff:.3f}"
        )

    print("")
    print("Agregado:")
    for (trainer_version, evaluation_opponent), metricas in sorted(resumen.aggregate().items()):
        print(
            f"- {trainer_version} vs {evaluation_opponent}: "
            f"runs={metricas['runs']:.0f}, "
            f"avg_win_rate={metricas['avg_win_rate']:.3f}, "
            f"avg_reward={metricas['avg_reward']:.3f}, "
            f"avg_score_diff={metricas['avg_score_diff']:.3f}"
        )


if __name__ == "__main__":
    main()
