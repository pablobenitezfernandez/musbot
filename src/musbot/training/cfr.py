"""Entrenamiento de mus por External-Sampling Monte Carlo CFR.

CFR (Counterfactual Regret Minimization) es el estándar para juegos de
información imperfecta: aprende una estrategia *aleatorizada* cercana al
equilibrio, capaz de farolear y mezclar manos fuertes y débiles — algo que un
Q-learning greedy no puede expresar.

Abstracción (MVP):
- *Chance*: el reparto, muestreado por iteración (external sampling de chance).
- *Mus*: se fuerza `cortar_mus` siempre, eliminando descartes y re-reparto. Es
  auto-consistente con `CFRAgent`, que también corta siempre.
- *Apuestas*: CFR decide en grande/chica/pares/juego/punto sobre el conjunto
  abstracto de acciones de `acciones_abstractas`.
- *Pago*: diferencial de piedras al final de la mano (juego de suma cero).

El juego es de parejas (j1+j3 vs j2+j4). Se entrenan los cuatro asientos con
tablas de regret compartidas por information set; cada asiento optimiza el
diferencial de su equipo. No hay garantía teórica de equilibrio en juegos de
parejas, pero el self-play external-sampling produce estrategias fuertes en la
práctica; su calidad se valida empíricamente contra los baselines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random

from musbot.agents.cfr_agent import (
    CFRAgent,
    acciones_abstractas,
    infoset_key,
    muestrear_label,
)
from musbot.core.estado_partida import EstadoPartida, FaseMano
from musbot.core.motor import MotorMus
from musbot.env.acciones import AccionLegal, AccionMus
from musbot.env.observaciones import construir_observacion_agente

_ASIENTOS: tuple[str, ...] = ("j1", "j2", "j3", "j4")
_CORTAR_MUS = AccionLegal.simple(AccionMus.CORTAR_MUS)


@dataclass(slots=True)
class CFRTrainer:
    """Acumula regrets y estrategia media por external-sampling MCCFR."""

    motor: MotorMus = field(default_factory=MotorMus)
    regret_sum: dict[str, dict[str, float]] = field(default_factory=dict)
    strategy_sum: dict[str, dict[str, float]] = field(default_factory=dict)
    iterations: int = 0
    sampling_seed: int = 0xC4F
    _sampling_rng: Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._sampling_rng = Random(self.sampling_seed)

    def entrenar(self, iteraciones: int, *, seed: int = 0) -> None:
        """Ejecuta `iteraciones` de MCCFR sobre repartos muestreados."""

        rng = Random(seed)
        for _ in range(iteraciones):
            raiz = self.motor.iniciar_partida(seed=rng.randint(0, 10_000_000))
            for traverser in _ASIENTOS:
                self._walk(raiz, traverser)
            self.iterations += 1

    def average_strategy(self) -> dict[str, dict[str, float]]:
        """Estrategia media normalizada (la que converge al equilibrio en CFR)."""

        politica: dict[str, dict[str, float]] = {}
        for infoset, strat in self.strategy_sum.items():
            total = sum(strat.values())
            if total > 0:
                politica[infoset] = {label: valor / total for label, valor in strat.items()}
        return politica

    def build_agent(self, *, agent_id: str = "cfr_main", seed: int | None = None) -> CFRAgent:
        return CFRAgent(agent_id=agent_id, seed=seed, policy=self.average_strategy())

    # -- internals -----------------------------------------------------------

    def _walk(self, estado: EstadoPartida, traverser: str) -> float:
        if estado.fase is FaseMano.FINALIZADA:
            return self._payoff(estado, traverser)

        if estado.fase is FaseMano.DECISION_MUS:
            estado = self._forzar_cortar_mus(estado)
            if estado.fase is FaseMano.FINALIZADA:
                return self._payoff(estado, traverser)

        jugador = estado.jugador_activo
        if jugador is None:
            raise ValueError("Se esperaba un jugador activo en una fase jugable.")

        legales = self.motor.acciones_legales(estado)
        obs = construir_observacion_agente(estado, jugador).to_agent_dict()
        abstractas = acciones_abstractas(legales, obs)

        if len(abstractas) <= 1:
            _, accion = abstractas[0]
            return self._walk(self.motor.aplicar_accion(estado, accion, jugador), traverser)

        labels = [label for label, _ in abstractas]
        infoset = infoset_key(obs)
        sigma = self._regret_matching(infoset, labels)

        if jugador == traverser:
            utilidades: dict[str, float] = {}
            util_nodo = 0.0
            for label, accion in abstractas:
                siguiente = self.motor.aplicar_accion(estado, accion, jugador)
                utilidades[label] = self._walk(siguiente, traverser)
                util_nodo += sigma[label] * utilidades[label]
            regrets = self.regret_sum.setdefault(infoset, {})
            for label in labels:
                regrets[label] = regrets.get(label, 0.0) + (utilidades[label] - util_nodo)
            return util_nodo

        estrategia = self.strategy_sum.setdefault(infoset, {})
        for label in labels:
            estrategia[label] = estrategia.get(label, 0.0) + sigma[label]
        elegido = muestrear_label(sigma, self._sampling_rng)
        accion = dict(abstractas)[elegido]
        return self._walk(self.motor.aplicar_accion(estado, accion, jugador), traverser)

    def _forzar_cortar_mus(self, estado: EstadoPartida) -> EstadoPartida:
        while estado.fase is FaseMano.DECISION_MUS:
            jugador = estado.jugador_activo
            if jugador is None:
                break
            estado = self.motor.aplicar_accion(estado, _CORTAR_MUS, jugador)
        return estado

    def _regret_matching(self, infoset: str, labels: list[str]) -> dict[str, float]:
        regrets = self.regret_sum.get(infoset, {})
        positivos = {label: max(regrets.get(label, 0.0), 0.0) for label in labels}
        total = sum(positivos.values())
        if total > 0:
            return {label: valor / total for label, valor in positivos.items()}
        peso = 1.0 / len(labels)
        return {label: peso for label in labels}

    def _payoff(self, estado: EstadoPartida, traverser: str) -> float:
        equipo = estado.equipos_por_jugador[traverser]
        rival = "equipo_2" if equipo == "equipo_1" else "equipo_1"
        return float(estado.marcador.get(equipo, 0) - estado.marcador.get(rival, 0))


def entrenar_cfr(
    motor: MotorMus,
    *,
    iteraciones: int,
    seed: int = 0,
) -> CFRTrainer:
    """Atajo: crea un `CFRTrainer`, entrena y lo devuelve."""

    trainer = CFRTrainer(motor=motor)
    trainer.entrenar(iteraciones, seed=seed)
    return trainer
