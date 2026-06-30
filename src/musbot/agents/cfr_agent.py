"""Agente CFR (Counterfactual Regret Minimization) y helpers compartidos.

Este modulo contiene las funciones puras que definen la *abstraccion* del juego
para CFR — la clave de information set y la abstraccion de acciones — usadas tanto
por el entrenador (`musbot.training.cfr`) como por el agente que juega la
estrategia media. Mantener una sola fuente de verdad evita que la politica
entrenada y la jugada en vivo usen claves o acciones distintas.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Any

from musbot.agents.base_agent import BaseAgent, LegalAction, Observacion
from musbot.env.acciones import AccionLegal, AccionMus

ENVIDAR_CHICO = "envidar_chico"
ENVIDAR_GRANDE = "envidar_grande"
# Niveles ABSOLUTOS de apuesta de la abstraccion. Solo se permite subir a un
# nivel estrictamente superior al pendiente, lo que acota el numero de subidas
# por lance (a lo sumo len(_NIVELES_ENVITE)) y mantiene finito el arbol de CFR.
# Sin esto, el motor admite subir de 1 en 1 hasta 40 y el arbol explota.
_NIVELES_ENVITE: tuple[int, ...] = (2, 6, 14)

_FASE_BUCKETS: dict[str, int] = {
    "decision_mus": 0,
    "grande": 1,
    "chica": 2,
    "pares": 3,
    "juego": 4,
    "punto": 5,
}
_FUERZA_FIELDS: dict[str, str] = {
    "grande": "fuerza_grande",
    "chica": "fuerza_chica",
    "pares": "fuerza_pares",
    "juego": "fuerza_juego",
    "punto": "fuerza_punto",
}
_PARES_BUCKETS: dict[object, int] = {None: 0, "pares": 1, "medias": 2, "duples": 3}


def _materializar(accion: LegalAction) -> AccionLegal:
    return accion if isinstance(accion, AccionLegal) else AccionLegal.simple(accion)


def _pendiente_actual(obs: Observacion) -> int:
    detalle = obs.get("detalle_envite_pendiente") if obs else None
    if isinstance(detalle, Mapping):
        cantidad = detalle.get("cantidad_actual")
        if cantidad is not None:
            return int(cantidad)
    return 0


def acciones_abstractas(
    acciones_legales: Sequence[LegalAction],
    obs: Observacion = None,
) -> list[tuple[str, AccionLegal]]:
    """Reduce las acciones legales concretas al conjunto abstracto de CFR.

    Las acciones no-apuesta se mantienen por tipo. Las apuestas se colapsan en a
    lo sumo dos: *chico* (subir al siguiente nivel absoluto) y *grande* (subir al
    nivel más alto disponible). Como `envidar:N` es un *incremento* sobre la
    apuesta pendiente, se traduce el nivel objetivo a su incremento. La misma
    reducción se aplica en entrenamiento y en juego para que las claves coincidan.
    """

    materializadas = [_materializar(accion) for accion in acciones_legales]
    abstractas: list[tuple[str, AccionLegal]] = []
    hay_envidar = False

    for accion in materializadas:
        if accion.tipo is AccionMus.ENVIDAR:
            hay_envidar = True
        else:
            abstractas.append((accion.tipo.value, accion))

    if hay_envidar:
        pendiente = _pendiente_actual(obs)
        objetivos = [nivel for nivel in _NIVELES_ENVITE if nivel > pendiente]
        if objetivos:
            chico = objetivos[0]
            abstractas.append((ENVIDAR_CHICO, AccionLegal.envidar(chico - pendiente)))
            if len(objetivos) >= 2:
                grande = objetivos[-1]
                abstractas.append((ENVIDAR_GRANDE, AccionLegal.envidar(grande - pendiente)))

    return abstractas


def _fuerza_lance(obs: Mapping[str, object]) -> float:
    fase = str(obs.get("fase", "decision_mus"))
    lance = str(obs.get("lance_actual") or fase)
    campo = _FUERZA_FIELDS.get(lance)
    if campo is not None:
        return float(obs.get(campo) or 0.0)
    g = float(obs.get("fuerza_grande") or 0.0)
    c = float(obs.get("fuerza_chica") or 0.0)
    return (g + c) / 2


def _bucket_fuerza(fuerza: float) -> int:
    if fuerza < 0.30:
        return 0
    if fuerza < 0.55:
        return 1
    if fuerza < 0.80:
        return 2
    return 3


def _bucket_cantidad(cantidad: object) -> str:
    if cantidad is None:
        return "x"
    valor = int(cantidad)
    if valor <= 3:
        return "b"
    if valor <= 10:
        return "m"
    return "a"


def _contexto_envite(obs: Mapping[str, object]) -> str:
    detalle = obs.get("detalle_envite_pendiente")
    if not isinstance(detalle, Mapping):
        return "abre"
    tipo = str(detalle.get("tipo_apuesta", "envite"))
    if tipo == "ordago":
        cant = "o"
    else:
        cant = _bucket_cantidad(detalle.get("cantidad_actual"))
    rol = "resp" if detalle.get("me_toca_responder") else "wait"
    return f"{tipo}:{cant}:{rol}"


def infoset_key(obs: Observacion) -> str:
    """Clave de information set para CFR a partir de la observación pública+propia.

    Incluye solo lo que el jugador conoce (su mano resumida + estado público); las
    cartas rivales nunca entran. Debe ser estable entre entrenamiento y juego.
    """

    if not obs:
        return "sin_observacion"

    fase = str(obs.get("fase", "decision_mus"))
    fase_bucket = _FASE_BUCKETS.get(fase, 0)
    posicion = int(obs.get("indice_turno") or 0)
    fuerza_bucket = _bucket_fuerza(_fuerza_lance(obs))
    pares_bucket = _PARES_BUCKETS.get(obs.get("categoria_pares"), 0)

    if not obs.get("tiene_juego"):
        juego_bucket = 0
    elif int(obs.get("valor_juego") or 0) == 31:
        juego_bucket = 2
    else:
        juego_bucket = 1

    diferencial = int(obs.get("diferencial_marcador") or 0)
    marcador_bucket = 0 if diferencial <= -5 else (2 if diferencial >= 5 else 1)

    contexto = _contexto_envite(obs)

    return (
        f"{fase_bucket}|{posicion}|{fuerza_bucket}|{pares_bucket}"
        f"|{juego_bucket}|{marcador_bucket}|{contexto}"
    )


def probabilidades_desde_politica(
    distribucion: Mapping[str, float] | None,
    labels: Sequence[str],
) -> dict[str, float]:
    """Distribucion de juego sobre `labels`, con respaldo prudente si falta info.

    Si el infoset no fue visto durante el entrenamiento, se reparte de forma
    uniforme entre las acciones no agresivas (se evita lanzar órdagos al azar);
    si solo queda el órdago, se juega.
    """

    if distribucion:
        filtrada = {label: max(distribucion.get(label, 0.0), 0.0) for label in labels}
        total = sum(filtrada.values())
        if total > 0:
            return {label: valor / total for label, valor in filtrada.items()}

    no_agresivas = [label for label in labels if label != AccionMus.ORDAGO.value]
    objetivo = no_agresivas or list(labels)
    peso = 1.0 / len(objetivo)
    return {label: (peso if label in objetivo else 0.0) for label in labels}


def muestrear_label(probabilidades: Mapping[str, float], rng: Random) -> str:
    """Muestrea una etiqueta segun su probabilidad."""

    umbral = rng.random()
    acumulado = 0.0
    etiqueta = ""
    for etiqueta, probabilidad in probabilidades.items():
        acumulado += probabilidad
        if umbral < acumulado:
            return etiqueta
    return etiqueta  # respaldo por errores de redondeo


@dataclass(slots=True)
class CFRAgent(BaseAgent):
    """Juega la estrategia media de un entrenamiento CFR.

    Mantiene la coherencia con el entrenamiento: corta el mus siempre (la fase de
    mus se excluye de la abstracción CFR) y juega las apuestas muestreando la
    estrategia media del information set correspondiente.
    """

    policy: dict[str, dict[str, float]] = field(default_factory=dict)
    seed: int | None = None
    model_version: str = "cfr_v1"
    _rng: Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = Random(self.seed)

    def elegir_accion(
        self,
        acciones_legales: Sequence[LegalAction],
        observacion: Observacion = None,
    ) -> LegalAction:
        opciones = [_materializar(accion) for accion in acciones_legales]
        if not opciones:
            raise ValueError("El agente CFR necesita al menos una accion legal.")

        # Fase de mus: el CFR no la modela; corta siempre (auto-consistente).
        cortar = next((a for a in opciones if a.tipo is AccionMus.CORTAR_MUS), None)
        if cortar is not None and any(a.tipo is AccionMus.PEDIR_MUS for a in opciones):
            return cortar

        abstractas = acciones_abstractas(opciones, observacion)
        if not abstractas:
            return opciones[0]
        if len(abstractas) == 1:
            return abstractas[0][1]

        labels = [label for label, _ in abstractas]
        clave = infoset_key(observacion)
        probabilidades = probabilidades_desde_politica(self.policy.get(clave), labels)
        elegido = muestrear_label(probabilidades, self._rng)
        return dict(abstractas)[elegido]

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "seed": self.seed,
            "version": self.model_version,
            "policy": self.policy,
        }

    @classmethod
    def from_state_dict(cls, payload: Mapping[str, Any]) -> CFRAgent:
        return cls(
            agent_id=str(payload.get("agent_id", "cfr_main")),
            seed=payload.get("seed"),
            model_version=str(payload.get("version", "cfr_v1")),
            policy=_normalizar_politica(payload.get("policy", {})),
        )


def _normalizar_politica(politica: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    return {
        str(infoset): {str(label): float(prob) for label, prob in dict(dist).items()}
        for infoset, dist in dict(politica).items()
    }


def cargar_politica_cfr(path: str | Path) -> dict[str, dict[str, float]]:
    """Lee la estrategia media CFR guardada en JSON y devuelve su política."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return _normalizar_politica(payload.get("policy", {}))
