"""Representaciones simples para jugadores."""

from __future__ import annotations

from dataclasses import dataclass, field

from musbot.core.cartas import Carta


@dataclass(slots=True)
class Jugador:
    """Estado basico de un jugador."""

    jugador_id: str
    nombre: str
    equipo_id: str | None = None
    mano: list[Carta] = field(default_factory=list)
