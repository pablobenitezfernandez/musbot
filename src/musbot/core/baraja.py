"""Estructuras para crear y manejar una baraja."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random

from musbot.core.cartas import Carta, Figura, Palo

FIGURAS_BARAJA_ESPANOLA_40: tuple[Figura, ...] = (
    Figura.AS,
    Figura.DOS,
    Figura.TRES,
    Figura.CUATRO,
    Figura.CINCO,
    Figura.SEIS,
    Figura.SIETE,
    Figura.SOTA,
    Figura.CABALLO,
    Figura.REY,
)


@dataclass(slots=True)
class Baraja:
    """Coleccion mutable de cartas."""

    cartas: list[Carta] = field(default_factory=list)

    @classmethod
    def espanola_40(cls) -> Baraja:
        """Crea una baraja espanola base de 40 cartas.

        TODO: confirmar con el reglamento oficial que esta composicion es la usada
        exactamente por la variante de mus objetivo.
        """

        cartas = [
            Carta(figura=figura, palo=palo)
            for palo in Palo
            for figura in FIGURAS_BARAJA_ESPANOLA_40
        ]
        return cls(cartas=cartas)

    def barajar(self, rng: Random | None = None) -> None:
        """Baraja las cartas in place."""

        generador = rng if rng is not None else Random()
        generador.shuffle(self.cartas)

    def robar(self, cantidad: int = 1) -> list[Carta]:
        """Extrae cartas de la parte superior de la baraja."""

        if cantidad < 0:
            raise ValueError("La cantidad a robar no puede ser negativa.")
        if cantidad > len(self.cartas):
            raise ValueError("No hay suficientes cartas en la baraja.")

        cartas_robadas = self.cartas[:cantidad]
        del self.cartas[:cantidad]
        return cartas_robadas

    def __len__(self) -> int:
        return len(self.cartas)
