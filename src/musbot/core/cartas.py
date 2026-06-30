"""Tipos basicos para representar cartas de la baraja espanola."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Palo(StrEnum):
    """Palos base de la baraja espanola."""

    OROS = "oros"
    COPAS = "copas"
    ESPADAS = "espadas"
    BASTOS = "bastos"


class Figura(StrEnum):
    """Figuras base de la baraja espanola de 40 cartas."""

    AS = "as"
    DOS = "dos"
    TRES = "tres"
    CUATRO = "cuatro"
    CINCO = "cinco"
    SEIS = "seis"
    SIETE = "siete"
    SOTA = "sota"
    CABALLO = "caballo"
    REY = "rey"


VALOR_NORMALIZADO_MUS = {
    Figura.AS: 0,
    Figura.DOS: 0,
    Figura.CUATRO: 1,
    Figura.CINCO: 2,
    Figura.SEIS: 3,
    Figura.SIETE: 4,
    Figura.SOTA: 5,
    Figura.CABALLO: 6,
    Figura.TRES: 7,
    Figura.REY: 7,
}

VALOR_JUEGO_PUNTO = {
    Figura.AS: 1,
    Figura.DOS: 1,
    Figura.CUATRO: 4,
    Figura.CINCO: 5,
    Figura.SEIS: 6,
    Figura.SIETE: 7,
    Figura.SOTA: 10,
    Figura.CABALLO: 10,
    Figura.TRES: 10,
    Figura.REY: 10,
}

NOMBRE_NORMALIZADO_MUS = {
    Figura.AS: "as",
    Figura.DOS: "as",
    Figura.CUATRO: "cuatro",
    Figura.CINCO: "cinco",
    Figura.SEIS: "seis",
    Figura.SIETE: "siete",
    Figura.SOTA: "sota",
    Figura.CABALLO: "caballo",
    Figura.TRES: "rey",
    Figura.REY: "rey",
}


@dataclass(frozen=True, slots=True)
class Carta:
    """Representa una carta simple.

    Variante fijada para el proyecto:

    - `2` vale como `as`
    - `3` vale como `rey`
    """

    figura: Figura
    palo: Palo

    @property
    def codigo(self) -> str:
        """Devuelve un identificador legible y estable para logs y tests."""

        return f"{self.figura.value}_de_{self.palo.value}"

    @property
    def valor_normalizado_mus(self) -> int:
        """Rango normalizado para grande, chica y pares."""

        return VALOR_NORMALIZADO_MUS[self.figura]

    @property
    def nombre_normalizado_mus(self) -> str:
        """Nombre normalizado para trazas y depuracion."""

        return NOMBRE_NORMALIZADO_MUS[self.figura]

    @property
    def valor_juego_punto(self) -> int:
        """Valor de la carta para sumar juego o punto."""

        return VALOR_JUEGO_PUNTO[self.figura]

    def __str__(self) -> str:
        return self.codigo
