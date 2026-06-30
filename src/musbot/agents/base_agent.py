"""Interfaz base para agentes del proyecto."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from musbot.env.acciones import AccionLegal, AccionMus

LegalAction = AccionLegal | AccionMus
Observacion = Mapping[str, object] | None


@dataclass(slots=True)
class BaseAgent(ABC):
    """Interfaz comun para agentes."""

    agent_id: str

    @abstractmethod
    def elegir_accion(
        self,
        acciones_legales: Sequence[LegalAction],
        observacion: Observacion = None,
    ) -> LegalAction:
        """Selecciona una accion legal sin modificar directamente el estado."""
