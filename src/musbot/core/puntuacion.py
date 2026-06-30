"""Utilidades de marcador y tanteo del mus."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from musbot.core.estado_partida import LanceMus, ResultadoLance

ORDEN_TANTEO: tuple[LanceMus, ...] = (
    LanceMus.GRANDE,
    LanceMus.CHICA,
    LanceMus.PARES,
    LanceMus.JUEGO,
    LanceMus.PUNTO,
)


@dataclass(slots=True)
class Marcador:
    """Marcador generico por equipo."""

    puntos_por_equipo: dict[str, int] = field(default_factory=dict)

    def sumar(self, equipo_id: str, puntos: int) -> None:
        """Suma puntos a un equipo."""

        if puntos < 0:
            raise ValueError("Los puntos a sumar no pueden ser negativos.")

        self.puntos_por_equipo[equipo_id] = self.puntos_por_equipo.get(equipo_id, 0) + puntos

    def puntos(self, equipo_id: str) -> int:
        """Consulta los puntos acumulados de un equipo."""

        return self.puntos_por_equipo.get(equipo_id, 0)


@dataclass(frozen=True, slots=True)
class AnotacionTanteo:
    """Apunte individual de tanteo por lance."""

    lance: LanceMus
    equipo_id: str
    puntos: int
    descripcion: str
    cierra_juego: bool = False
    ordago_resuelto: bool = False


def resolver_puntuacion_mano(
    resultados_lances: Mapping[LanceMus, ResultadoLance],
    marcador_actual: Mapping[str, int],
    piedras_objetivo: int = 40,
) -> list[AnotacionTanteo]:
    """Resuelve el tanteo reglamentario de una mano.

    Se cuentan los lances en orden. Si un equipo llega a `piedras_objetivo`
    antes de alcanzar un ordago aceptado en un lance posterior, el juego se
    cierra y ese ordago deja de importar.
    """

    tanteo = dict(marcador_actual)
    anotaciones: list[AnotacionTanteo] = []

    for lance in ORDEN_TANTEO:
        resultado = resultados_lances.get(lance)
        if resultado is None:
            continue

        if resultado.ordago_aceptado:
            if any(puntos >= piedras_objetivo for puntos in tanteo.values()):
                anotaciones.append(
                    AnotacionTanteo(
                        lance=lance,
                        equipo_id=resultado.ganador_equipo,
                        puntos=0,
                        descripcion="ordago ignorado porque un lance anterior ya cerro el juego",
                        ordago_resuelto=False,
                    )
                )
                break

            if resultado.puntos_apuesta and resultado.equipo_apuesta is not None:
                tanteo[resultado.equipo_apuesta] = (
                    tanteo.get(resultado.equipo_apuesta, 0) + resultado.puntos_apuesta
                )
                cierra_apuesta = tanteo[resultado.equipo_apuesta] >= piedras_objetivo
                anotaciones.append(
                    AnotacionTanteo(
                        lance=lance,
                        equipo_id=resultado.equipo_apuesta,
                        puntos=resultado.puntos_apuesta,
                        descripcion=f"apuesta previa en {lance.value}",
                        cierra_juego=cierra_apuesta,
                    )
                )
                if cierra_apuesta:
                    break

            puntos_para_cerrar = max(0, piedras_objetivo - tanteo.get(resultado.ganador_equipo, 0))
            tanteo[resultado.ganador_equipo] = (
                tanteo.get(resultado.ganador_equipo, 0) + puntos_para_cerrar
            )
            anotaciones.append(
                AnotacionTanteo(
                    lance=lance,
                    equipo_id=resultado.ganador_equipo,
                    puntos=puntos_para_cerrar,
                    descripcion=resultado.descripcion,
                    cierra_juego=True,
                    ordago_resuelto=True,
                )
            )
            break

        if resultado.puntos_apuesta and resultado.equipo_apuesta is not None:
            tanteo[resultado.equipo_apuesta] = (
                tanteo.get(resultado.equipo_apuesta, 0) + resultado.puntos_apuesta
            )
            cierra_apuesta = tanteo[resultado.equipo_apuesta] >= piedras_objetivo
            anotaciones.append(
                AnotacionTanteo(
                    lance=lance,
                    equipo_id=resultado.equipo_apuesta,
                    puntos=resultado.puntos_apuesta,
                    descripcion=resultado.descripcion,
                    cierra_juego=cierra_apuesta,
                )
            )
            if cierra_apuesta:
                break

        if resultado.puntos_base_ganador:
            tanteo[resultado.ganador_equipo] = (
                tanteo.get(resultado.ganador_equipo, 0) + resultado.puntos_base_ganador
            )
            cierra = tanteo[resultado.ganador_equipo] >= piedras_objetivo
            anotaciones.append(
                AnotacionTanteo(
                    lance=lance,
                    equipo_id=resultado.ganador_equipo,
                    puntos=resultado.puntos_base_ganador,
                    descripcion=resultado.descripcion,
                    cierra_juego=cierra,
                )
            )
            if cierra:
                break

    return anotaciones


def aplicar_anotaciones(
    marcador: dict[str, int],
    anotaciones: Sequence[AnotacionTanteo],
) -> dict[str, int]:
    """Devuelve un nuevo marcador tras aplicar un tanteo."""

    nuevo_marcador = dict(marcador)
    for anotacion in anotaciones:
        nuevo_marcador[anotacion.equipo_id] = (
            nuevo_marcador.get(anotacion.equipo_id, 0) + anotacion.puntos
        )
    return nuevo_marcador
