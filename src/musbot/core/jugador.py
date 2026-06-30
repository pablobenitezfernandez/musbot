"""Representaciones simples para jugadores."""

from __future__ import annotations

from dataclasses import dataclass, field

from musbot.core.cartas import Carta


@dataclass(slots=True)
class Jugador:
    """Estado basico de un jugador.

    TODO: ampliar cuando el reglamento verificado obligue a modelar mano, turno
    y relacion exacta con el equipo.
    """

    jugador_id: str
    nombre: str
    equipo_id: str | None = None
    mano: list[Carta] = field(default_factory=list)
