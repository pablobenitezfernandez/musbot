from dataclasses import FrozenInstanceError

import pytest

from musbot.core.cartas import Carta, Figura, Palo


def test_carta_codigo_formato_legible() -> None:
    carta = Carta(figura=Figura.REY, palo=Palo.OROS)

    assert carta.codigo == "rey_de_oros"
    assert str(carta) == "rey_de_oros"


def test_carta_es_inmutable() -> None:
    carta = Carta(figura=Figura.AS, palo=Palo.COPAS)

    with pytest.raises(FrozenInstanceError):
        carta.figura = Figura.REY  # type: ignore[misc]


def test_carta_expone_valores_normalizados_de_mus_y_juego() -> None:
    dos = Carta(figura=Figura.DOS, palo=Palo.BASTOS)
    tres = Carta(figura=Figura.TRES, palo=Palo.ESPADAS)

    assert dos.valor_normalizado_mus == 0
    assert dos.valor_juego_punto == 1
    assert dos.nombre_normalizado_mus == "as"
    assert tres.valor_normalizado_mus == 7
    assert tres.valor_juego_punto == 10
    assert tres.nombre_normalizado_mus == "rey"
