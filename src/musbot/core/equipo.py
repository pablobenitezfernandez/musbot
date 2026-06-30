"""Representaciones simples para equipos."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Equipo:
    """Equipo basico de mus."""

    equipo_id: str
    nombre: str
    jugadores: list[str] = field(default_factory=list)
    puntos: int = 0
