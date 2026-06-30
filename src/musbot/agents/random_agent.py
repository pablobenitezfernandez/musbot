"""Agente base que elige una accion legal al azar."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from random import Random

from musbot.agents.base_agent import BaseAgent, LegalAction, Observacion


@dataclass(slots=True)
class RandomAgent(BaseAgent):
    """Agente baseline que elige uniformemente entre acciones legales."""

    seed: int | None = None
    _rng: Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = Random(self.seed)

    def elegir_accion(
        self,
        acciones_legales: Sequence[LegalAction],
        observacion: Observacion = None,
    ) -> LegalAction:
        del observacion

        opciones = list(acciones_legales)
        if not opciones:
            raise ValueError("El agente necesita al menos una accion legal.")

        return self._rng.choice(opciones)
