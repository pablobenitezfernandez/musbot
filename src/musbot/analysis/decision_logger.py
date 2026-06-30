"""Registro de decisiones del bot en formato JSONL."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """Registro estructurado de una decision del bot."""

    partida_id: str
    mano_id: str | int
    jugador_id: str
    fase: str
    cartas_propias: list[str]
    marcador: dict[str, int]
    historial_publico: list[str]
    acciones_legales: list[str]
    accion_elegida: str
    probabilidades_accion: dict[str, float] | None = None
    valor_estimado: float | None = None
    recompensa_posterior: float | None = None
    comentario: str = ""


class DecisionLogger:
    """Persistencia simple de decisiones para auditoria posterior."""

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)

    def registrar(self, decision: DecisionRecord | Mapping[str, Any]) -> Path:
        """Anade un registro al archivo JSONL."""

        payload = self._serializar(decision)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with self.output_path.open("a", encoding="utf-8") as output_file:
            json.dump(payload, output_file, ensure_ascii=False, default=str)
            output_file.write("\n")

        return self.output_path

    def leer_todas(self) -> list[dict[str, Any]]:
        """Lee todos los registros existentes."""

        if not self.output_path.exists():
            return []

        with self.output_path.open("r", encoding="utf-8") as input_file:
            return [json.loads(line) for line in input_file if line.strip()]

    @staticmethod
    def _serializar(decision: DecisionRecord | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(decision, DecisionRecord):
            return asdict(decision)
        if isinstance(decision, Mapping):
            return dict(decision)

        raise TypeError("La decision debe ser un DecisionRecord o un mapping compatible.")
