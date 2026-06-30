"""Script para entrenar, reanudar o bifurcar modelos RL."""

from __future__ import annotations

import argparse

from musbot.training.catalog import best_model_run
from musbot.training.registry import list_trainer_definitions
from musbot.training.train import train


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-trainers", action="store_true")
    parser.add_argument("--root-dir", default="data/modelos")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--checkpoint-interval", type=int, default=10)
    parser.add_argument("--evaluation-interval", type=int, default=10)
    parser.add_argument("--evaluation-hands", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument(
        "--opponent",
        default="mixed",
        choices=("random", "heuristic", "mixed"),
    )
    parser.add_argument("--notes", default="")
    parser.add_argument("--trainer-version")
    parser.add_argument("--resume-run-id")
    parser.add_argument("--resume-best", action="store_true")
    parser.add_argument("--fork-from-run-id")
    parser.add_argument("--fork-checkpoint", default="latest")
    args = parser.parse_args()

    if args.list_trainers:
        for definition in list_trainer_definitions():
            print(f"{definition.trainer_version}: {definition.label}")
            print(f"  {definition.description}")
        return

    resume_run_id = args.resume_run_id
    if args.resume_best:
        mejor = best_model_run(
            root_dir=args.root_dir,
            trainer_version=args.trainer_version,
        )
        if mejor is None:
            raise SystemExit("No hay ningun run con metricas para reanudar.")
        resume_run_id = mejor.run_id

    resultado = train(
        root_dir=args.root_dir,
        episodes_to_run=args.episodes,
        checkpoint_interval=args.checkpoint_interval,
        evaluation_interval=args.evaluation_interval,
        evaluation_hands=args.evaluation_hands,
        seed=args.seed,
        epsilon=args.epsilon,
        learning_rate=args.learning_rate,
        opponent=args.opponent,
        notes=args.notes,
        trainer_version=args.trainer_version,
        resume_run_id=resume_run_id,
        fork_from_run_id=args.fork_from_run_id,
        fork_checkpoint=args.fork_checkpoint,
    )
    print(f"run_id: {resultado.run_id}")
    print(f"run_dir: {resultado.run_dir}")
    print(f"episodes: {resultado.total_episodes}")
    print(f"latest_checkpoint: {resultado.latest_checkpoint}")
    print(f"best_checkpoint: {resultado.best_checkpoint}")
    print(f"best_metric: {resultado.best_metric}")


if __name__ == "__main__":
    main()
