"""Estado de partida y subestados del motor del mus."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from random import Random

from musbot.core.cartas import Carta
from musbot.core.jugador import Jugador


class FaseMano(StrEnum):
    """Fases jugables de una mano normal."""

    PREPARACION = "preparacion"
    DECISION_MUS = "decision_mus"
    DESCARTE = "descarte"
    GRANDE = "grande"
    CHICA = "chica"
    PARES = "pares"
    JUEGO = "juego"
    PUNTO = "punto"
    TANTEO = "tanteo"
    FINALIZADA = "finalizada"


class LanceMus(StrEnum):
    """Lances reglados del mus."""

    GRANDE = "grande"
    CHICA = "chica"
    PARES = "pares"
    JUEGO = "juego"
    PUNTO = "punto"


@dataclass(frozen=True, slots=True)
class EnvitePendiente:
    """Envite u ordago pendiente de respuesta."""

    lance: LanceMus
    jugador_apostador: str
    equipo_apostador: str
    cantidad: int | None = None
    cantidad_previa: int = 0
    es_ordago: bool = False


@dataclass(slots=True)
class EstadoLance:
    """Subestado del lance actualmente en disputa."""

    lance: LanceMus
    participantes: tuple[str, ...]
    indice_turno: int = 0
    jugadores_que_pasaron: list[str] = field(default_factory=list)
    envite_pendiente: EnvitePendiente | None = None
    puntos_envite_aceptado: int = 0


@dataclass(frozen=True, slots=True)
class ResultadoLance:
    """Resultado ya cerrado de un lance."""

    lance: LanceMus
    ganador_jugador: str
    ganador_equipo: str
    participantes: tuple[str, ...]
    puntos_base_ganador: int
    descripcion: str
    puntos_apuesta: int = 0
    equipo_apuesta: str | None = None
    ordago_aceptado: bool = False
    apuesta_rechazada: bool = False


@dataclass(slots=True)
class EstadoPartida:
    """Estado principal del motor de mus.

    Este modelo representa una mano normal sin capa de arbitraje ni errores
    humanos. El motor se encarga de calcular automaticamente informacion
    objetiva, como pares, juego y ganadores de lances.
    """

    partida_id: str
    mano_id: int = 1
    fase: FaseMano = FaseMano.PREPARACION
    jugador_activo: str | None = None
    historial_publico: list[str] = field(default_factory=list)
    marcador: dict[str, int] = field(default_factory=dict)
    juegos_ganados: dict[str, int] = field(default_factory=dict)
    jugadores: dict[str, Jugador] = field(default_factory=dict)
    equipos_por_jugador: dict[str, str] = field(default_factory=dict)
    orden_turnos: tuple[str, ...] = ()
    indice_mano: int = 0
    orden_descarte: tuple[str, ...] = ()
    mazo_restante: list[Carta] = field(default_factory=list)
    descarte: list[Carta] = field(default_factory=list)
    decisiones_mus: list[str] = field(default_factory=list)
    lance_en_curso: EstadoLance | None = None
    resultados_lances: dict[LanceMus, ResultadoLance] = field(default_factory=dict)
    jugadores_con_pares: tuple[str, ...] = ()
    jugadores_con_juego: tuple[str, ...] = ()
    ganador_juego_actual: str | None = None
    ganador_partida: str | None = None
    rng: Random = field(default_factory=Random)

    def mano(self, jugador_id: str) -> list[Carta]:
        return self.jugadores[jugador_id].mano
