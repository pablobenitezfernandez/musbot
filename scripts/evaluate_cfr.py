"""Evalua una estrategia CFR guardada contra los baselines."""

from __future__ import annotations

import argparse

from musbot.agents.cfr_agent import CFRAgent, cargar_politica_cfr
from musbot.core.motor import MotorMus
from musbot.training.self_play import evaluar_vs_opponent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", default="data/cfr/strategy.json")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument(
        "--opponents",
        nargs="+",
        default=["random", "heuristic", "mixed"],
    )
    args = parser.parse_args()

    motor = MotorMus()
    politica = cargar_politica_cfr(args.strategy)
    agente = CFRAgent(agent_id="cfr_eval", policy=politica, seed=args.seed)

    print(f"Estrategia: {args.strategy} ({len(politica)} information sets)")
    for opponent in args.opponents:
        resultado = evaluar_vs_opponent(
            motor, agente, episodes=args.episodes, seed=args.seed, opponent=opponent
        )
        print(
            f"- vs {opponent}: win_rate={resultado['win_rate']:.3f} "
            f"avg_reward={resultado['avg_reward']:.3f} "
            f"avg_score_diff={resultado['avg_score_diff']:.3f}"
        )


if __name__ == "__main__":
    main()
