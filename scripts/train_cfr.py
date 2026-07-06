"""Entrena una estrategia de mus por MCCFR y la evalua contra los baselines."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from musbot.core.motor import MotorMus
from musbot.training.cfr import CFRTrainer
from musbot.training.self_play import evaluar_vs_opponent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--eval-interval", type=int, default=1000)
    parser.add_argument("--eval-hands", type=int, default=500)
    parser.add_argument("--eval-seed", type=int, default=777)
    parser.add_argument("--output", default="data/cfr/strategy.json")
    parser.add_argument("--modelar-mus", action="store_true")
    args = parser.parse_args()

    motor = MotorMus()
    trainer = CFRTrainer(motor=motor, modelar_mus=args.modelar_mus)
    salida = Path(args.output)
    salida.parent.mkdir(parents=True, exist_ok=True)

    def guardar() -> int:
        payload = trainer.build_agent(seed=args.eval_seed).to_state_dict()
        payload["iterations"] = trainer.iterations
        salida.write_text(json.dumps(payload), encoding="utf-8")
        return len(payload["policy"])

    hechas = 0
    t0 = time.time()
    while hechas < args.iterations:
        tramo = min(args.eval_interval, args.iterations - hechas)
        trainer.entrenar(tramo, seed=args.seed + hechas)
        hechas += tramo
        agente = trainer.build_agent(seed=args.eval_seed)
        marcas = {
            opp: evaluar_vs_opponent(
                motor, agente, episodes=args.eval_hands, seed=args.eval_seed, opponent=opp
            )["win_rate"]
            for opp in ("random", "heuristic", "mixed")
        }
        n_infosets = guardar()  # guardado periódico: una corrida larga es segura
        elapsed = time.time() - t0
        print(
            f"iter={hechas} | infosets={n_infosets} | "
            f"random={marcas['random']:.3f} heuristic={marcas['heuristic']:.3f} "
            f"mixed={marcas['mixed']:.3f} | {elapsed:.0f}s",
            flush=True,
        )

    print(f"Estrategia guardada en {salida} ({guardar()} information sets).")


if __name__ == "__main__":
    main()
