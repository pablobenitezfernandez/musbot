"""Script para evaluar un modelo RL guardado."""

from __future__ import annotations

import argparse

from musbot.training.evaluate import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root-dir", default="data/modelos")
    parser.add_argument("--checkpoint", default="best")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument(
        "--opponent",
        choices=("random", "heuristic", "mixed"),
    )
    args = parser.parse_args()

    resultado = evaluate(
        run_id=args.run_id,
        root_dir=args.root_dir,
        checkpoint=args.checkpoint,
        episodes=args.episodes,
        seed=args.seed,
        opponent=args.opponent,
    )
    print(f"run_id: {resultado.run_id}")
    print(f"checkpoint: {resultado.checkpoint_used}")
    print(f"win_rate: {resultado.win_rate:.3f}")
    print(f"avg_reward: {resultado.avg_reward:.3f}")
    print(f"avg_score_diff: {resultado.avg_score_diff:.3f}")
    for report_path in resultado.behavior_report_paths:
        print(f"behavior_report: {report_path}")


if __name__ == "__main__":
    main()
