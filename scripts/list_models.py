"""Lista los modelos entrenados disponibles y destaca el mejor segun metrica."""

from __future__ import annotations

import argparse

from musbot.training.catalog import best_model_run, list_model_runs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", default="data/modelos")
    parser.add_argument("--trainer-version")
    parser.add_argument("--best-only", action="store_true")
    args = parser.parse_args()

    if args.best_only:
        mejor = best_model_run(
            root_dir=args.root_dir,
            trainer_version=args.trainer_version,
        )
        if mejor is None:
            print("No hay modelos con metricas registradas.")
            return
        _print_run(mejor, destacado=True)
        return

    runs = list_model_runs(root_dir=args.root_dir)
    if args.trainer_version is not None:
        runs = [run for run in runs if run.trainer_version == args.trainer_version]

    if not runs:
        print("No hay modelos registrados.")
        return

    mejor_run = best_model_run(
        root_dir=args.root_dir,
        trainer_version=args.trainer_version,
    )
    for run in runs:
        _print_run(run, destacado=mejor_run is not None and run.run_id == mejor_run.run_id)


def _print_run(run: object, *, destacado: bool) -> None:
    prefijo = "*" if destacado else "-"
    print(
        f"{prefijo} {run.run_id} | trainer={run.trainer_version} | status={run.status} | "
        f"episodes={run.total_episodes} | best_metric={run.best_metric} | "
        f"best_checkpoint={run.best_checkpoint} | latest_checkpoint={run.latest_checkpoint}"
    )
    if run.parent_run_id is not None:
        print(
            f"  parent={run.parent_run_id} checkpoint={run.parent_checkpoint} | "
            f"notes={run.notes or 'sin notas'}"
        )
    else:
        print(f"  notes={run.notes or 'sin notas'}")


if __name__ == "__main__":
    main()
