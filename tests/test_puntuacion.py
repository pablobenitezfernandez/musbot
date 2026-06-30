import pytest

from musbot.core.cartas import Carta, Figura, Palo
from musbot.core.estado_partida import LanceMus, ResultadoLance
from musbot.core.evaluacion import (
    comparacion_pares,
    evaluar_grande,
    evaluar_pares,
    mejor_jugador,
)
from musbot.core.puntuacion import Marcador, resolver_puntuacion_mano


def test_marcador_suma_puntos_por_equipo() -> None:
    marcador = Marcador()

    marcador.sumar("equipo_a", 2)
    marcador.sumar("equipo_a", 3)

    assert marcador.puntos("equipo_a") == 5


def test_marcador_rechaza_puntos_negativos() -> None:
    marcador = Marcador()

    with pytest.raises(ValueError):
        marcador.sumar("equipo_a", -1)


def test_duples_altos_ganan_a_cuatro_sietes() -> None:
    duples_altos = [
        Carta(Figura.REY, Palo.OROS),
        Carta(Figura.TRES, Palo.COPAS),
        Carta(Figura.AS, Palo.ESPADAS),
        Carta(Figura.DOS, Palo.BASTOS),
    ]
    cuatro_sietes = [
        Carta(Figura.SIETE, Palo.OROS),
        Carta(Figura.SIETE, Palo.COPAS),
        Carta(Figura.SIETE, Palo.ESPADAS),
        Carta(Figura.SIETE, Palo.BASTOS),
    ]

    pares_altos = evaluar_pares(duples_altos)
    pares_sietes = evaluar_pares(cuatro_sietes)

    assert pares_altos is not None
    assert pares_sietes is not None
    assert comparacion_pares(pares_altos) > comparacion_pares(pares_sietes)


def test_mejor_jugador_desempata_por_orden_de_turno() -> None:
    mano_a = [
        Carta(Figura.REY, Palo.OROS),
        Carta(Figura.CABALLO, Palo.COPAS),
        Carta(Figura.SIETE, Palo.ESPADAS),
        Carta(Figura.CUATRO, Palo.BASTOS),
    ]
    mano_b = [
        Carta(Figura.REY, Palo.COPAS),
        Carta(Figura.CABALLO, Palo.ESPADAS),
        Carta(Figura.SIETE, Palo.BASTOS),
        Carta(Figura.CUATRO, Palo.OROS),
    ]

    ganador = mejor_jugador(
        ("j1", "j2", "j3", "j4"),
        {"j1": evaluar_grande(mano_a), "j2": evaluar_grande(mano_b)},
        lambda clave: clave,
    )

    assert ganador == "j1"


def test_resolver_puntuacion_cierra_antes_del_ordago_si_llega_a_40() -> None:
    anotaciones = resolver_puntuacion_mano(
        resultados_lances={
            LanceMus.GRANDE: ResultadoLance(
                lance=LanceMus.GRANDE,
                ganador_jugador="j1",
                ganador_equipo="equipo_1",
                participantes=("j1", "j2", "j3", "j4"),
                puntos_base_ganador=2,
                descripcion="grande por 2 puntos",
            ),
            LanceMus.CHICA: ResultadoLance(
                lance=LanceMus.CHICA,
                ganador_jugador="j2",
                ganador_equipo="equipo_2",
                participantes=("j1", "j2", "j3", "j4"),
                puntos_base_ganador=0,
                descripcion="ordago aceptado en chica",
                ordago_aceptado=True,
            ),
        },
        marcador_actual={"equipo_1": 39, "equipo_2": 25},
    )

    assert len(anotaciones) == 1
    assert anotaciones[0].equipo_id == "equipo_1"
    assert anotaciones[0].puntos == 2
    assert anotaciones[0].cierra_juego is True
