"""Agente heuristico baseline sobre reglas ya verificadas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from musbot.agents.base_agent import BaseAgent, LegalAction, Observacion
from musbot.core.evaluacion import (
    fuerza_relativa_chica_desde_valores,
    fuerza_relativa_grande_desde_valores,
    fuerza_relativa_juego_desde_total,
    fuerza_relativa_pares_desde_valores,
    fuerza_relativa_punto_desde_total,
)
from musbot.env.acciones import AccionLegal, AccionMus

ORDEN_JUEGO = (31, 32, 40, 37, 36, 35, 34, 33)


@dataclass(slots=True)
class HeuristicAgent(BaseAgent):
    """Agente baseline con reglas simples y deterministas.

    No pretende jugar "bien" en sentido experto, pero si:

    - superar claramente a un agente aleatorio
    - generar un rival mas informativo para entrenamiento
    - usar cantidades de envite coherentes con la fuerza estimada de la mano
    """

    def elegir_accion(
        self,
        acciones_legales: Sequence[LegalAction],
        observacion: Observacion = None,
    ) -> LegalAction:
        opciones = [self._materializar(accion) for accion in acciones_legales]
        if not opciones:
            raise ValueError("El agente heuristico necesita al menos una accion legal.")
        if observacion is None:
            return opciones[0]

        fase = str(observacion.get("fase", ""))
        if any(accion.tipo is AccionMus.DESCARTAR for accion in opciones):
            return self._elegir_descarte(opciones, observacion)
        if {accion.tipo for accion in opciones} >= {
            AccionMus.PEDIR_MUS,
            AccionMus.CORTAR_MUS,
        }:
            return self._elegir_mus(opciones, observacion)
        if any(accion.tipo in {AccionMus.QUIERO, AccionMus.NO_QUIERO} for accion in opciones):
            return self._responder_envite(opciones, observacion)
        if fase in {"grande", "chica", "pares", "juego", "punto"}:
            return self._abrir_lance(opciones, observacion)
        return opciones[0]

    @staticmethod
    def _materializar(accion: LegalAction) -> AccionLegal:
        if isinstance(accion, AccionLegal):
            return accion
        return AccionLegal.simple(accion)

    def _elegir_mus(
        self,
        opciones: Sequence[AccionLegal],
        observacion: Mapping[str, object],
    ) -> AccionLegal:
        cortar = self._buscar(opciones, AccionMus.CORTAR_MUS)
        pedir = self._buscar(opciones, AccionMus.PEDIR_MUS)
        if cortar is None:
            return pedir or opciones[0]
        if pedir is None:
            return cortar

        tiene_pares = bool(observacion.get("tiene_pares"))
        tiene_juego = bool(observacion.get("tiene_juego"))
        valor_juego = int(observacion.get("valor_juego") or 0)
        fuerza_grande = self._resolver_fuerza(observacion, "grande")
        fuerza_pares = self._resolver_fuerza(observacion, "pares")
        fuerza_chica = self._resolver_fuerza(observacion, "chica")

        if valor_juego == 31:
            return cortar
        if fuerza_pares is not None and fuerza_pares >= 0.55:
            return cortar
        if tiene_pares:
            return cortar
        if tiene_juego and valor_juego >= 32:
            return cortar
        if fuerza_grande >= 0.88 or fuerza_chica >= 0.88:
            return cortar
        return pedir

    def _elegir_descarte(
        self,
        opciones: Sequence[AccionLegal],
        observacion: Mapping[str, object],
    ) -> AccionLegal:
        valores = self._valores_mus(observacion)
        suma_cartas = int(observacion.get("suma_cartas") or 0)
        tiene_juego = bool(observacion.get("tiene_juego"))
        categoria = str(observacion.get("categoria_pares") or "")

        indices_a_conservar: set[int] = set()
        if categoria in {"duples", "medias", "pares"}:
            frecuencias: dict[int, list[int]] = {}
            for indice, valor in enumerate(valores):
                frecuencias.setdefault(valor, []).append(indice)
            for indices in frecuencias.values():
                if len(indices) >= 2:
                    indices_a_conservar.update(indices)

        if tiene_juego and suma_cartas >= 31:
            return self._descartar_indices(opciones, ())

        if not indices_a_conservar:
            indices_a_conservar = {
                indice for indice, valor in enumerate(valores) if valor in {0, 7}
            }
            if len(indices_a_conservar) < 2:
                mejores = sorted(
                    range(len(valores)),
                    key=lambda idx: self._valor_descarte(valores[idx]),
                )
                indices_a_conservar.update(mejores[:2])

        indices_descartar = tuple(
            indice for indice in range(len(valores)) if indice not in indices_a_conservar
        )
        return self._descartar_indices(opciones, indices_descartar)

    def _abrir_lance(
        self,
        opciones: Sequence[AccionLegal],
        observacion: Mapping[str, object],
    ) -> AccionLegal:
        fuerza = self._fuerza_lance(observacion)
        lance = str(observacion.get("lance_actual") or observacion.get("fase") or "")
        piedras_restantes = max(0, 40 - int(observacion.get("marcador_propio") or 0))
        ordago = self._buscar(opciones, AccionMus.ORDAGO)
        pasar = self._buscar(opciones, AccionMus.PASAR)

        if ordago is not None and piedras_restantes <= 4 and fuerza >= 0.82:
            return ordago

        if self._tiene_envite(opciones):
            cantidad_objetivo = self._cantidad_objetivo_apertura(lance, fuerza, observacion)
            if cantidad_objetivo is not None:
                return self._accion_envite(opciones, cantidad_objetivo)

        return pasar or opciones[0]

    def _responder_envite(
        self,
        opciones: Sequence[AccionLegal],
        observacion: Mapping[str, object],
    ) -> AccionLegal:
        detalle = observacion.get("detalle_envite_pendiente")
        if not isinstance(detalle, Mapping):
            return self._buscar(opciones, AccionMus.QUIERO) or opciones[0]

        fuerza = self._fuerza_lance(observacion)
        quiero = self._buscar(opciones, AccionMus.QUIERO)
        no_quiero = self._buscar(opciones, AccionMus.NO_QUIERO)
        ordago = self._buscar(opciones, AccionMus.ORDAGO)
        cantidad_actual = int(detalle.get("cantidad_actual") or 0)
        valor_no_quiero = int(detalle.get("valor_no_quiero") or 1)
        piedras_restantes = max(0, 40 - int(observacion.get("marcador_propio") or 0))
        lance = str(observacion.get("lance_actual") or observacion.get("fase") or "")

        if str(detalle.get("tipo_apuesta")) == "ordago":
            if quiero is not None and (
                fuerza >= 0.95 or (piedras_restantes <= 4 and fuerza >= 0.82)
            ):
                return quiero
            return no_quiero or opciones[0]

        cantidad_subida = self._cantidad_objetivo_respuesta(
            lance,
            fuerza,
            cantidad_actual,
            observacion,
        )
        if self._tiene_envite(opciones) and cantidad_subida is not None:
            return self._accion_envite(opciones, cantidad_subida)
        if ordago is not None and fuerza >= 0.99:
            return ordago
        if quiero is not None and (
            fuerza >= 0.72
            or (fuerza >= 0.60 and cantidad_actual <= 2)
            or (fuerza >= 0.58 and valor_no_quiero >= 3)
        ):
            return quiero
        return no_quiero or opciones[0]

    def _fuerza_lance(self, observacion: Mapping[str, object]) -> float:
        lance = str(observacion.get("lance_actual") or observacion.get("fase") or "")
        fuerza = self._resolver_fuerza(observacion, lance)
        if fuerza is not None:
            return fuerza
        return 0.5

    def _resolver_fuerza(
        self,
        observacion: Mapping[str, object],
        lance: str,
    ) -> float | None:
        if lance == "grande":
            valor = observacion.get("fuerza_grande")
            if isinstance(valor, (float, int)):
                return float(valor)
            valores = self._valores_mus(observacion)
            return fuerza_relativa_grande_desde_valores(valores) if valores else None
        if lance == "chica":
            valor = observacion.get("fuerza_chica")
            if isinstance(valor, (float, int)):
                return float(valor)
            valores = self._valores_mus(observacion)
            return fuerza_relativa_chica_desde_valores(valores) if valores else None
        if lance == "pares":
            valor = observacion.get("fuerza_pares")
            if isinstance(valor, (float, int)):
                return float(valor)
            valores = self._valores_mus(observacion)
            return fuerza_relativa_pares_desde_valores(valores) if valores else None
        if lance == "juego":
            valor = observacion.get("fuerza_juego")
            if isinstance(valor, (float, int)):
                return float(valor)
            total = int(observacion.get("suma_cartas") or 0)
            return fuerza_relativa_juego_desde_total(total)
        if lance == "punto":
            valor = observacion.get("fuerza_punto")
            if isinstance(valor, (float, int)):
                return float(valor)
            total = int(observacion.get("valor_punto") or 0)
            return fuerza_relativa_punto_desde_total(total) if total else None
        return None

    @staticmethod
    def _valores_mus(observacion: Mapping[str, object]) -> list[int]:
        valores = observacion.get("valores_mus")
        if not isinstance(valores, Sequence):
            return []
        return [int(valor) for valor in valores]

    def _cantidad_objetivo_apertura(
        self,
        lance: str,
        fuerza: float,
        observacion: Mapping[str, object],
    ) -> int | None:
        if lance == "grande":
            if fuerza >= 0.90:
                return 3
            if fuerza >= 0.82:
                return 2
            return None
        if lance == "chica":
            if fuerza >= 0.88:
                return 2
            return None
        if lance == "pares":
            if fuerza >= 0.85:
                return 5
            if fuerza >= 0.68:
                return 2
            return None
        if lance == "juego":
            valor_juego = int(observacion.get("valor_juego") or 0)
            if valor_juego == 31:
                return 3
            if fuerza >= 0.85:
                return 2
            return None
        if lance == "punto":
            if fuerza >= 0.82:
                return 2
            return None
        return None

    def _cantidad_objetivo_respuesta(
        self,
        lance: str,
        fuerza: float,
        cantidad_actual: int,
        observacion: Mapping[str, object],
    ) -> int | None:
        if cantidad_actual > 10:
            return None
        if lance == "juego" and int(observacion.get("valor_juego") or 0) == 31 and fuerza >= 0.96:
            return 2
        if lance == "pares" and fuerza >= 0.94:
            return 2
        if lance == "grande" and fuerza >= 0.95:
            return 2
        if lance == "punto" and fuerza >= 0.92:
            return 2
        return None

    @staticmethod
    def _valor_descarte(valor: int) -> tuple[int, int]:
        if valor in {0, 7}:
            return (1, valor)
        return (0, valor)

    def _descartar_indices(
        self,
        opciones: Sequence[AccionLegal],
        indices_descartar: tuple[int, ...],
    ) -> AccionLegal:
        ordenados = tuple(sorted(indices_descartar))
        for accion in opciones:
            if accion.tipo is AccionMus.DESCARTAR and accion.cartas_descartadas == ordenados:
                return accion
        return self._buscar(opciones, AccionMus.DESCARTAR) or opciones[0]

    @staticmethod
    def _buscar(opciones: Sequence[AccionLegal], tipo: AccionMus) -> AccionLegal | None:
        for accion in opciones:
            if accion.tipo is tipo:
                return accion
        return None

    @staticmethod
    def _tiene_envite(opciones: Sequence[AccionLegal]) -> bool:
        return any(accion.tipo is AccionMus.ENVIDAR for accion in opciones)

    def _accion_envite(
        self,
        opciones: Sequence[AccionLegal],
        cantidad_deseada: int,
    ) -> AccionLegal:
        candidatas: list[AccionLegal] = [
            accion for accion in opciones if accion.tipo is AccionMus.ENVIDAR
        ]
        if not candidatas:
            quiero = self._buscar(opciones, AccionMus.QUIERO)
            return quiero or opciones[0]

        cantidades_concretas = sorted(
            {
                accion.cantidad
                for accion in candidatas
                if accion.cantidad is not None and accion.cantidad > 0
            }
        )
        if cantidades_concretas:
            elegible = [
                cantidad for cantidad in cantidades_concretas if cantidad <= cantidad_deseada
            ]
            cantidad = elegible[-1] if elegible else cantidades_concretas[0]
            return AccionLegal.envidar(cantidad)

        plantilla = candidatas[0]
        minimo = plantilla.cantidad_minima
        maximo = plantilla.cantidad_maxima
        cantidad = max(minimo, cantidad_deseada)
        if maximo is not None:
            cantidad = min(cantidad, maximo)
        return AccionLegal.envidar(cantidad)
