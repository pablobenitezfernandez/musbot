from random import Random

from musbot.core.baraja import Baraja


def test_baraja_espanola_base_tiene_40_cartas() -> None:
    baraja = Baraja.espanola_40()

    assert len(baraja) == 40
    assert len({carta.codigo for carta in baraja.cartas}) == 40


def test_barajar_preserva_las_cartas() -> None:
    baraja = Baraja.espanola_40()
    originales = [carta.codigo for carta in baraja.cartas]

    baraja.barajar(Random(7))

    barajadas = [carta.codigo for carta in baraja.cartas]
    assert sorted(barajadas) == sorted(originales)


def test_robar_reduce_el_tamano_de_la_baraja() -> None:
    baraja = Baraja.espanola_40()

    robadas = baraja.robar(4)

    assert len(robadas) == 4
    assert len(baraja) == 36
