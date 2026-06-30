"""Evaluadores puros de jugadas del mus."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations_with_replacement
from typing import Any

from musbot.core.cartas import Carta

ORDEN_JUEGO: tuple[int, ...] = (31, 32, 40, 37, 36, 35, 34, 33)
ORDEN_PUNTO: tuple[int, ...] = tuple(range(30, 3, -1))
RANK_JUEGO: dict[int, int] = {
    total: len(ORDEN_JUEGO) - indice for indice, total in enumerate(ORDEN_JUEGO)
}
RANGO_PUNTO: dict[int, int] = {
    total: len(ORDEN_PUNTO) - indice for indice, total in enumerate(ORDEN_PUNTO)
}


class CategoriaPares(StrEnum):
    """Categorias de pares admitidas por la variante objetivo."""

    PARES = "pares"
    MEDIAS = "medias"
    DUPLES = "duples"


@dataclass(frozen=True, slots=True)
class ResultadoPares:
    """Resultado de evaluar pares para una mano."""

    categoria: CategoriaPares
    clave_desempate: tuple[int, ...]
    puntos: int

    @property
    def comparacion(self) -> tuple[int, ...]:
        categoria_rank = {
            CategoriaPares.PARES: 1,
            CategoriaPares.MEDIAS: 2,
            CategoriaPares.DUPLES: 3,
        }[self.categoria]
        return (categoria_rank, *self.clave_desempate)


@dataclass(frozen=True, slots=True)
class ResultadoJuego:
    """Resultado de evaluar juego para una mano."""

    total: int
    puntos: int

    @property
    def comparacion(self) -> tuple[int]:
        return (RANK_JUEGO[self.total],)


def evaluar_grande(cartas: Sequence[Carta]) -> tuple[int, ...]:
    """Devuelve una clave comparable para el lance de grande."""

    return tuple(sorted((carta.valor_normalizado_mus for carta in cartas), reverse=True))


def evaluar_chica(cartas: Sequence[Carta]) -> tuple[int, ...]:
    """Devuelve una clave comparable para el lance de chica."""

    return tuple(-valor for valor in sorted(carta.valor_normalizado_mus for carta in cartas))


def evaluar_pares(cartas: Sequence[Carta]) -> ResultadoPares | None:
    """Detecta y clasifica los pares de una mano."""

    return evaluar_pares_desde_valores([carta.valor_normalizado_mus for carta in cartas])


def evaluar_pares_desde_valores(valores: Sequence[int]) -> ResultadoPares | None:
    """Detecta y clasifica pares a partir de valores normalizados de mus."""

    contador = Counter(valores)
    por_tamano = sorted(contador.items(), key=lambda item: (item[1], item[0]), reverse=True)
    tamanos = sorted(contador.values(), reverse=True)

    if tamanos == [4]:
        valor = por_tamano[0][0]
        return ResultadoPares(
            categoria=CategoriaPares.DUPLES,
            clave_desempate=(valor, valor),
            puntos=3,
        )

    if tamanos == [2, 2]:
        valores = tuple(
            sorted(
                (valor for valor, cantidad in contador.items() if cantidad == 2),
                reverse=True,
            )
        )
        return ResultadoPares(
            categoria=CategoriaPares.DUPLES,
            clave_desempate=valores,
            puntos=3,
        )

    if tamanos == [3, 1]:
        valor = por_tamano[0][0]
        return ResultadoPares(
            categoria=CategoriaPares.MEDIAS,
            clave_desempate=(valor,),
            puntos=2,
        )

    if tamanos == [2, 1, 1]:
        valor = por_tamano[0][0]
        return ResultadoPares(
            categoria=CategoriaPares.PARES,
            clave_desempate=(valor,),
            puntos=1,
        )

    return None


def suma_juego_punto(cartas: Sequence[Carta]) -> int:
    """Suma el valor de una mano para juego o punto."""

    return sum(carta.valor_juego_punto for carta in cartas)


def evaluar_juego(cartas: Sequence[Carta]) -> ResultadoJuego | None:
    """Evalua la mano si tiene juego."""

    return evaluar_juego_desde_total(suma_juego_punto(cartas))


def evaluar_juego_desde_total(total: int) -> ResultadoJuego | None:
    """Evalua juego a partir del total ya sumado."""

    if total not in RANK_JUEGO:
        return None
    return ResultadoJuego(total=total, puntos=3 if total == 31 else 2)


def evaluar_punto(cartas: Sequence[Carta]) -> int:
    """Evalua el punto de una mano cuando nadie tiene juego."""

    return evaluar_punto_desde_total(suma_juego_punto(cartas))


def evaluar_punto_desde_total(total: int) -> int:
    """Valida un total de punto ya sumado."""

    if total not in RANGO_PUNTO:
        raise ValueError(f"El total {total} no es valido para punto.")
    return total


def mejor_jugador(
    orden_turnos: Sequence[str],
    evaluaciones: Mapping[str, Any],
    comparador: Callable[[Any], tuple[int, ...] | tuple[int]],
) -> str:
    """Devuelve el mejor jugador, desempantando por orden de turno."""

    ganador: str | None = None
    mejor_clave: tuple[int, ...] | None = None

    for jugador_id in orden_turnos:
        if jugador_id not in evaluaciones:
            continue

        clave = comparador(evaluaciones[jugador_id])
        if ganador is None or mejor_clave is None or clave > mejor_clave:
            ganador = jugador_id
            mejor_clave = clave

    if ganador is None:
        raise ValueError("No hay jugadores evaluables para determinar ganador.")

    return ganador


def comparacion_grande(clave: tuple[int, ...]) -> tuple[int, ...]:
    return clave


def comparacion_chica(clave: tuple[int, ...]) -> tuple[int, ...]:
    return clave


def comparacion_pares(resultado: ResultadoPares) -> tuple[int, ...]:
    return resultado.comparacion


def comparacion_juego(resultado: ResultadoJuego) -> tuple[int]:
    return resultado.comparacion


def comparacion_punto(total: int) -> tuple[int]:
    return (RANGO_PUNTO[total],)


def fuerza_relativa_grande_desde_valores(valores: Sequence[int]) -> float:
    """Fuerza relativa de grande entre 0 y 1."""

    clave = tuple(sorted((int(valor) for valor in valores), reverse=True))
    return _GRANDE_SCORES[clave]


def fuerza_relativa_chica_desde_valores(valores: Sequence[int]) -> float:
    """Fuerza relativa de chica entre 0 y 1."""

    clave = tuple(-valor for valor in sorted(int(valor) for valor in valores))
    return _CHICA_SCORES[clave]


def fuerza_relativa_pares_desde_valores(valores: Sequence[int]) -> float | None:
    """Fuerza relativa de pares entre 0 y 1, o `None` si no hay pares."""

    resultado = evaluar_pares_desde_valores(valores)
    if resultado is None:
        return None
    return _PARES_SCORES[resultado.comparacion]


def fuerza_relativa_juego_desde_total(total: int) -> float | None:
    """Fuerza relativa de juego entre 0 y 1, o `None` si no hay juego."""

    if total not in RANK_JUEGO:
        return None
    if len(ORDEN_JUEGO) == 1:
        return 1.0
    return (RANK_JUEGO[total] - 1) / (len(ORDEN_JUEGO) - 1)


def fuerza_relativa_punto_desde_total(total: int) -> float:
    """Fuerza relativa de punto entre 0 y 1."""

    evaluar_punto_desde_total(total)
    if len(ORDEN_PUNTO) == 1:
        return 1.0
    return (RANGO_PUNTO[total] - 1) / (len(ORDEN_PUNTO) - 1)


def _build_relative_scores(keys: Sequence[tuple[int, ...]]) -> dict[tuple[int, ...], float]:
    if not keys:
        return {}
    if len(keys) == 1:
        return {keys[0]: 1.0}
    return {key: indice / (len(keys) - 1) for indice, key in enumerate(sorted(keys))}


def _build_grande_scores() -> dict[tuple[int, ...], float]:
    keys = {
        tuple(sorted(valores, reverse=True))
        for valores in combinations_with_replacement(range(8), 4)
    }
    return _build_relative_scores(tuple(keys))


def _build_chica_scores() -> dict[tuple[int, ...], float]:
    keys = {
        tuple(-valor for valor in sorted(valores))
        for valores in combinations_with_replacement(range(8), 4)
    }
    return _build_relative_scores(tuple(keys))


def _build_pares_scores() -> dict[tuple[int, ...], float]:
    keys = {
        resultado.comparacion
        for valores in combinations_with_replacement(range(8), 4)
        for resultado in [evaluar_pares_desde_valores(valores)]
        if resultado is not None
    }
    return _build_relative_scores(tuple(keys))


_GRANDE_SCORES = _build_grande_scores()
_CHICA_SCORES = _build_chica_scores()
_PARES_SCORES = _build_pares_scores()
