"""Infraestructura de runs, checkpoints y metricas de entrenamiento."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """Devuelve una marca temporal UTC estable para archivos."""

    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class TrainingConfig:
    """Configuracion serializable de un run de entrenamiento."""

    episodes_to_run: int
    checkpoint_interval: int = 10
    evaluation_interval: int = 10
    evaluation_hands: int = 20
    seed: int = 0
    epsilon: float = 0.1
    learning_rate: float = 0.1
    notes: str = ""
    trainer_version: str = "tabular_v1"
    opponent: str = "mixed"


@dataclass(slots=True)
class RunState:
    """Estado mutable y persistente de un run."""

    run_id: str
    status: str
    created_at: str
    updated_at: str
    total_episodes: int = 0
    total_updates: int = 0
    best_metric: float | None = None
    best_checkpoint: str | None = None
    latest_checkpoint: str | None = None
    parent_run_id: str | None = None
    parent_checkpoint: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class RunPaths:
    """Rutas relevantes de un run concreto."""

    root: Path
    run_dir: Path
    checkpoints_dir: Path
    config_path: Path
    state_path: Path
    metrics_path: Path
    summary_path: Path
    latest_checkpoint_path: Path
    best_checkpoint_path: Path


class TrainingRunManager:
    """Gestiona runs, checkpoints, metricas y resumentes por modelo."""

    def __init__(self, root_dir: str | Path = "data/modelos") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def create_run(
        self,
        config: TrainingConfig,
        *,
        parent_run_id: str | None = None,
        parent_checkpoint: str | None = None,
    ) -> tuple[RunPaths, RunState]:
        """Crea un run nuevo con estructura completa."""

        run_id = self._next_run_id()
        paths = self._paths(run_id)
        paths.run_dir.mkdir(parents=True, exist_ok=False)
        paths.checkpoints_dir.mkdir(parents=True, exist_ok=False)

        self._write_json(paths.config_path, asdict(config))

        state = RunState(
            run_id=run_id,
            status="running",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
            parent_run_id=parent_run_id,
            parent_checkpoint=parent_checkpoint,
            notes=config.notes,
        )
        self.save_state(paths, state)
        self.update_summary(paths, config, state)
        return paths, state

    def load_run(self, run_id: str) -> tuple[RunPaths, TrainingConfig, RunState]:
        """Carga configuracion y estado de un run existente."""

        paths = self._paths(run_id)
        config = TrainingConfig(**self._read_json(paths.config_path))
        state = RunState(**self._read_json(paths.state_path))
        return paths, config, state

    def save_state(self, paths: RunPaths, state: RunState) -> None:
        """Persiste el estado mutable del run."""

        state.updated_at = utc_now_iso()
        self._write_json(paths.state_path, asdict(state))

    def save_config(self, paths: RunPaths, config: TrainingConfig) -> None:
        """Persiste la configuracion del run."""

        self._write_json(paths.config_path, asdict(config))

    def save_checkpoint(
        self,
        paths: RunPaths,
        state: RunState,
        *,
        episode: int,
        agent_state: dict[str, Any],
        metric_value: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Guarda un checkpoint y actualiza `latest` y opcionalmente `best`."""

        checkpoint_name = f"episode_{episode:06d}.json"
        checkpoint_path = paths.checkpoints_dir / checkpoint_name
        payload = {
            "run_id": state.run_id,
            "episode": episode,
            "saved_at": utc_now_iso(),
            "metric_value": metric_value,
            "metadata": metadata or {},
            "agent_state": agent_state,
        }
        self._write_json(checkpoint_path, payload)
        shutil.copyfile(checkpoint_path, paths.latest_checkpoint_path)
        state.latest_checkpoint = checkpoint_name

        if metric_value is not None and (
            state.best_metric is None or metric_value >= state.best_metric
        ):
            shutil.copyfile(checkpoint_path, paths.best_checkpoint_path)
            state.best_metric = metric_value
            state.best_checkpoint = checkpoint_name

        self.save_state(paths, state)
        return checkpoint_path

    def load_checkpoint(self, path: str | Path) -> dict[str, Any]:
        """Carga un checkpoint desde ruta absoluta o relativa."""

        checkpoint_path = Path(path)
        return self._read_json(checkpoint_path)

    def append_metric(self, paths: RunPaths, record: dict[str, Any]) -> None:
        """Anade una metrica en JSONL."""

        paths.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with paths.metrics_path.open("a", encoding="utf-8") as output_file:
            json.dump(record, output_file, ensure_ascii=False, sort_keys=True)
            output_file.write("\n")

    def read_metrics(self, paths: RunPaths) -> list[dict[str, Any]]:
        """Lee el historico de metricas del run."""

        if not paths.metrics_path.exists():
            return []

        with paths.metrics_path.open("r", encoding="utf-8") as input_file:
            return [json.loads(line) for line in input_file if line.strip()]

    def update_summary(
        self,
        paths: RunPaths,
        config: TrainingConfig,
        state: RunState,
        last_metric: dict[str, Any] | None = None,
    ) -> None:
        """Regenera el resumen humano del run."""

        metrics = self.read_metrics(paths)
        recientes = metrics[-5:]

        lineas = [
            f"# {state.run_id}",
            "",
            "## Estado",
            "",
            f"- status: {state.status}",
            f"- creado: {state.created_at}",
            f"- actualizado: {state.updated_at}",
            f"- episodios totales: {state.total_episodes}",
            f"- updates totales: {state.total_updates}",
            f"- ultimo checkpoint: {state.latest_checkpoint or 'ninguno'}",
            f"- mejor checkpoint: {state.best_checkpoint or 'ninguno'}",
            f"- mejor metrica: {state.best_metric if state.best_metric is not None else 'n/d'}",
        ]

        if state.parent_run_id is not None:
            lineas.extend(
                [
                    f"- derivado de: {state.parent_run_id}",
                    f"- checkpoint origen: {state.parent_checkpoint or 'desconocido'}",
                ]
            )

        lineas.extend(
            [
                "",
                "## Configuracion",
                "",
                f"- trainer: {config.trainer_version}",
                f"- opponent: {config.opponent}",
                f"- episodes_to_run: {config.episodes_to_run}",
                f"- checkpoint_interval: {config.checkpoint_interval}",
                f"- evaluation_interval: {config.evaluation_interval}",
                f"- evaluation_hands: {config.evaluation_hands}",
                f"- epsilon: {config.epsilon}",
                f"- learning_rate: {config.learning_rate}",
                f"- seed: {config.seed}",
                f"- notes: {config.notes or 'sin notas'}",
                "",
                "## Ultima evaluacion",
                "",
            ]
        )

        if last_metric is None and recientes:
            last_metric = recientes[-1]

        if last_metric is None:
            lineas.append("- aun no hay metricas registradas")
        else:
            lineas.extend(
                [
                    f"- episodio: {last_metric.get('episode')}",
                    f"- win_rate: {last_metric.get('win_rate')}",
                    f"- avg_reward: {last_metric.get('avg_reward')}",
                    f"- avg_score_diff: {last_metric.get('avg_score_diff')}",
                ]
            )

        lineas.extend(["", "## Evolucion reciente", ""])
        if not recientes:
            lineas.append("- sin metricas todavia")
        else:
            for record in recientes:
                lineas.append(
                    "- episodio {episode}: win_rate={win_rate}, avg_reward={avg_reward}, "
                    "avg_score_diff={avg_score_diff}".format(**record)
                )

        paths.summary_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    def checkpoint_path(self, paths: RunPaths, checkpoint_name: str) -> Path:
        """Devuelve la ruta a un checkpoint nominal."""

        if checkpoint_name == "latest":
            return paths.latest_checkpoint_path
        if checkpoint_name == "best":
            return paths.best_checkpoint_path
        return paths.checkpoints_dir / checkpoint_name

    def _next_run_id(self) -> str:
        existentes = sorted(
            path.name
            for path in self.root_dir.iterdir()
            if path.is_dir() and path.name.startswith("run_")
        )
        if not existentes:
            return "run_0001"

        ultimo = max(int(nombre.split("_", maxsplit=1)[1]) for nombre in existentes)
        return f"run_{ultimo + 1:04d}"

    def _paths(self, run_id: str) -> RunPaths:
        run_dir = self.root_dir / run_id
        return RunPaths(
            root=self.root_dir,
            run_dir=run_dir,
            checkpoints_dir=run_dir / "checkpoints",
            config_path=run_dir / "config.json",
            state_path=run_dir / "state.json",
            metrics_path=run_dir / "metrics.jsonl",
            summary_path=run_dir / "resumen.md",
            latest_checkpoint_path=run_dir / "latest_checkpoint.json",
            best_checkpoint_path=run_dir / "best_checkpoint.json",
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as input_file:
            return json.load(input_file)

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as output_file:
            json.dump(payload, output_file, ensure_ascii=False, indent=2, sort_keys=True)
