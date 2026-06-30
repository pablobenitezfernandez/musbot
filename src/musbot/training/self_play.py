"""Rutinas base de self-play y evaluacion de agentes."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from random import Random

from musbot.agents.base_agent import BaseAgent
from musbot.agents.heuristic_agent import HeuristicAgent
from musbot.agents.random_agent import RandomAgent
from musbot.agents.rl_agent import ExperienceStep, RLAgent, action_key
from musbot.core.cartas import Carta
from musbot.core.estado_partida import EstadoPartida, FaseMano
from musbot.core.motor import MotorMus
from musbot.env.acciones import AccionLegal, AccionMus
from musbot.env.observaciones import construir_observacion_agente
from musbot.env.recompensas import EsquemaRecompensas, calcular_recompensa_terminal

ENVITES_CANDIDATOS: tuple[int, ...] = (1, 2, 3, 5, 7, 10, 15, 20, 30, 40)
TRAINING_REWARD_SCHEME = EsquemaRecompensas(
    victoria_mano=1.0,
    derrota_mano=-1.0,
    empate_mano=0.0,
    factor_diferencial_piedras=0.05,
    bonus_ganar_juego=0.25,
    penalizacion_perder_juego=-0.25,
)
ORDAGO_BASE_PENALTY = 0.02
ORDAGO_SAFE_STRENGTH = 0.95
ORDAGO_NEAR_CLOSE_SCORE = 36
ORDAGO_BAD_CONTEXT_BASE = 0.35
ORDAGO_BAD_CONTEXT_DISTANCE_FACTOR = 0.01
ORDAGO_BAD_CONTEXT_STRENGTH_FACTOR = 0.40
AGGRESSIVE_ENVITE_MIN_AMOUNT = 7
ENVITE_SAFE_STRENGTH = 0.85
ENVITE_NEAR_CLOSE_SCORE = 34
ENVITE_BAD_CONTEXT_BASE = 0.05
ENVITE_BAD_CONTEXT_AMOUNT_FACTOR = 0.02
ENVITE_BAD_CONTEXT_DISTANCE_FACTOR = 0.005
ENVITE_BAD_CONTEXT_STRENGTH_FACTOR = 0.25


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    """Resultado de una mano jugada entre agentes."""

    final_state: EstadoPartida
    score_delta: dict[str, int]
    reward_by_team: dict[str, float]
    trajectories_by_player: dict[str, list[ExperienceStep]]
    decision_traces: tuple[DecisionTrace, ...]


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Trazas ligeras de decisiones para analisis agregado."""

    player_id: str
    team_id: str
    phase: str
    lance_actual: str | None
    action_label: str
    action_type: str
    quantity: int | None
    score_own: int
    score_rival: int
    lance_strength: float | None


def construir_observacion(estado: EstadoPartida, jugador_id: str) -> dict[str, object]:
    """Construye una observacion minima y estable para un agente."""

    return construir_observacion_agente(estado, jugador_id).to_agent_dict()


def jugar_mano(
    motor: MotorMus,
    agentes: Mapping[str, BaseAgent],
    *,
    seed: int | None = None,
    partida_id: str | None = None,
    marcador_inicial: Mapping[str, int] | None = None,
    manos_iniciales: Mapping[str, list[Carta]] | None = None,
) -> EpisodeResult:
    """Juega una mano completa usando el motor y los agentes dados."""

    estado = motor.iniciar_partida(
        partida_id=partida_id,
        marcador_inicial=marcador_inicial,
        manos_iniciales=manos_iniciales,
        seed=seed,
    )
    marcador_inicial_efectivo = dict(estado.marcador)
    juegos_iniciales_efectivos = dict(estado.juegos_ganados)
    trayectorias: dict[str, list[ExperienceStep]] = defaultdict(list)
    decision_traces: list[DecisionTrace] = []

    while estado.fase is not FaseMano.FINALIZADA:
        jugador_id = estado.jugador_activo
        if jugador_id is None:
            raise ValueError("El motor deberia exponer un jugador activo en fases jugables.")

        acciones_legales = expandir_acciones_para_agente(motor.acciones_legales(estado))
        observacion = construir_observacion(estado, jugador_id)
        agente = agentes[jugador_id]
        accion = agente.elegir_accion(acciones_legales, observacion)
        accion_materializada = (
            accion if isinstance(accion, AccionLegal) else AccionLegal.simple(accion)
        )
        decision_traces.append(
            DecisionTrace(
                player_id=jugador_id,
                team_id=estado.equipos_por_jugador[jugador_id],
                phase=estado.fase.value,
                lance_actual=(
                    None if estado.lance_en_curso is None else estado.lance_en_curso.lance.value
                ),
                action_label=str(accion_materializada),
                action_type=accion_materializada.tipo.value,
                quantity=accion_materializada.cantidad,
                score_own=int(observacion.get("marcador_propio") or 0),
                score_rival=int(observacion.get("marcador_rival") or 0),
                lance_strength=_lance_strength_from_observation(observacion),
            )
        )

        if isinstance(agente, RLAgent):
            trayectorias[jugador_id].append(
                ExperienceStep(
                    state_key=agente.state_key(observacion),
                    action_key=action_key(accion),
                )
            )

        estado = motor.aplicar_accion(estado, accion, jugador_id)

    score_delta = {
        equipo_id: estado.marcador.get(equipo_id, 0) - marcador_inicial_efectivo.get(equipo_id, 0)
        for equipo_id in marcador_inicial_efectivo
    }
    reward_by_team = _reward_by_team(
        marcador_inicial=marcador_inicial_efectivo,
        marcador_final=estado.marcador,
        juegos_iniciales=juegos_iniciales_efectivos,
        juegos_finales=estado.juegos_ganados,
        decision_traces=decision_traces,
    )
    return EpisodeResult(
        final_state=estado,
        score_delta=score_delta,
        reward_by_team=reward_by_team,
        trajectories_by_player=dict(trayectorias),
        decision_traces=tuple(decision_traces),
    )


def expandir_acciones_para_agente(
    acciones_legales: Sequence[AccionLegal | AccionMus],
) -> list[AccionLegal]:
    """Expande plantillas del motor a acciones concretas para agentes.

    Esto permite que `self_play` use cantidades reales de envite y no solo la
    materializacion minima implícita del motor.
    """

    expandidas: list[AccionLegal] = []
    for accion in acciones_legales:
        materializada = accion if isinstance(accion, AccionLegal) else AccionLegal.simple(accion)
        if materializada.tipo is not AccionMus.ENVIDAR or not materializada.requiere_cantidad:
            expandidas.append(materializada)
            continue

        candidatas = [
            cantidad
            for cantidad in ENVITES_CANDIDATOS
            if cantidad >= materializada.cantidad_minima
            and (materializada.cantidad_maxima is None or cantidad <= materializada.cantidad_maxima)
        ]
        if materializada.cantidad_minima not in candidatas:
            candidatas.insert(0, materializada.cantidad_minima)
        for cantidad in sorted(set(candidatas)):
            expandidas.append(AccionLegal.envidar(cantidad))
    return expandidas


def construir_pareja_oponente(
    opponent: str,
    *,
    rng: Random,
    seat_ids: tuple[str, str] = ("j2", "j4"),
) -> dict[str, BaseAgent]:
    """Construye la pareja rival segun el baseline indicado."""

    if opponent == "random":
        return {
            jugador_id: RandomAgent(
                agent_id=f"random_{jugador_id}",
                seed=rng.randint(0, 10_000_000),
            )
            for jugador_id in seat_ids
        }
    if opponent == "heuristic":
        return {
            jugador_id: HeuristicAgent(agent_id=f"heuristic_{jugador_id}")
            for jugador_id in seat_ids
        }
    if opponent == "mixed":
        rivales: dict[str, BaseAgent] = {}
        for jugador_id in seat_ids:
            kind = rng.choice(("random", "heuristic"))
            rivales[jugador_id] = _crear_oponente_individual(kind, jugador_id, rng)
        return rivales
    raise ValueError(f"Baseline rival desconocido: {opponent}")


def _crear_oponente_individual(kind: str, jugador_id: str, rng: Random) -> BaseAgent:
    if kind == "random":
        return RandomAgent(
            agent_id=f"random_{jugador_id}",
            seed=rng.randint(0, 10_000_000),
        )
    if kind == "heuristic":
        return HeuristicAgent(agent_id=f"heuristic_{jugador_id}")
    raise ValueError(f"Tipo de oponente individual desconocido: {kind}")


def entrenar_vs_opponent(
    motor: MotorMus,
    agente: RLAgent,
    *,
    episodes: int,
    seed: int,
    opponent: str,
) -> list[EpisodeResult]:
    """Entrena un agente RL contra un baseline configurable."""

    resultados: list[EpisodeResult] = []
    rng = Random(seed)

    for episode in range(episodes):
        agentes = {
            "j1": agente,
            "j3": agente,
            **construir_pareja_oponente(opponent, rng=rng),
        }
        resultado = jugar_mano(
            motor,
            agentes,
            seed=rng.randint(0, 10_000_000),
            partida_id=f"train-episode-{episode + 1}",
        )
        reward = resultado.reward_by_team["equipo_1"]
        agente.actualizar_desde_experiencias(resultado.trajectories_by_player.get("j1", []), reward)
        agente.actualizar_desde_experiencias(resultado.trajectories_by_player.get("j3", []), reward)
        resultados.append(resultado)

    return resultados


def entrenar_vs_random(
    motor: MotorMus,
    agente: RLAgent,
    *,
    episodes: int,
    seed: int,
) -> list[EpisodeResult]:
    """Ejecuta entrenamiento simple del agente contra oponentes aleatorios."""

    return entrenar_vs_opponent(
        motor,
        agente,
        episodes=episodes,
        seed=seed,
        opponent="random",
    )


def evaluar_vs_opponent(
    motor: MotorMus,
    agente: RLAgent,
    *,
    episodes: int,
    seed: int,
    opponent: str,
) -> dict[str, float]:
    """Evalua el agente contra un baseline configurable."""

    rng = Random(seed)
    victorias = 0
    recompensas: list[float] = []
    diferenciales: list[int] = []
    decision_traces: list[DecisionTrace] = []

    for episode in range(episodes):
        agentes = {
            "j1": agente,
            "j3": agente,
            **construir_pareja_oponente(opponent, rng=rng),
        }
        resultado = jugar_mano(
            motor,
            agentes,
            seed=rng.randint(0, 10_000_000),
            partida_id=f"eval-episode-{episode + 1}",
        )
        recompensa = resultado.reward_by_team["equipo_1"]
        recompensas.append(recompensa)
        diferencial = resultado.score_delta["equipo_1"] - resultado.score_delta["equipo_2"]
        diferenciales.append(diferencial)
        decision_traces.extend(resultado.decision_traces)
        if recompensa > 0:
            victorias += 1

    total = max(episodes, 1)
    comportamiento = resumir_decisiones(
        decision_traces,
        team_id="equipo_1",
        episodes=episodes,
    )
    return {
        "win_rate": victorias / total,
        "avg_reward": sum(recompensas) / total,
        "avg_score_diff": sum(diferenciales) / total,
        "behavior_summary": comportamiento,
    }


def evaluar_vs_random(
    motor: MotorMus,
    agente: RLAgent,
    *,
    episodes: int,
    seed: int,
) -> dict[str, float]:
    """Evalua el agente contra una pareja aleatoria."""

    return evaluar_vs_opponent(
        motor,
        agente,
        episodes=episodes,
        seed=seed,
        opponent="random",
    )


def _reward_by_team(
    *,
    marcador_inicial: Mapping[str, int],
    marcador_final: Mapping[str, int],
    juegos_iniciales: Mapping[str, int],
    juegos_finales: Mapping[str, int],
    decision_traces: Sequence[DecisionTrace],
) -> dict[str, float]:
    reward_equipo_1 = calcular_recompensa_terminal(
        equipo_controlado="equipo_1",
        equipo_rival="equipo_2",
        marcador_inicial=marcador_inicial,
        marcador_final=marcador_final,
        juegos_iniciales=juegos_iniciales,
        juegos_finales=juegos_finales,
        esquema=TRAINING_REWARD_SCHEME,
    ).total
    reward_equipo_2 = calcular_recompensa_terminal(
        equipo_controlado="equipo_2",
        equipo_rival="equipo_1",
        marcador_inicial=marcador_inicial,
        marcador_final=marcador_final,
        juegos_iniciales=juegos_iniciales,
        juegos_finales=juegos_finales,
        esquema=TRAINING_REWARD_SCHEME,
    ).total
    ordago_penalties = _ordago_penalties_by_team(decision_traces)
    envite_penalties = _aggressive_envite_penalties_by_team(decision_traces)
    return {
        "equipo_1": reward_equipo_1 + ordago_penalties["equipo_1"] + envite_penalties["equipo_1"],
        "equipo_2": reward_equipo_2 + ordago_penalties["equipo_2"] + envite_penalties["equipo_2"],
    }


def _ordago_penalties_by_team(
    decision_traces: Sequence[DecisionTrace],
) -> dict[str, float]:
    penalties = {"equipo_1": 0.0, "equipo_2": 0.0}
    for trace in decision_traces:
        if trace.action_type != AccionMus.ORDAGO.value:
            continue
        penalties[trace.team_id] -= _ordago_penalty(trace)
    return penalties


def _aggressive_envite_penalties_by_team(
    decision_traces: Sequence[DecisionTrace],
) -> dict[str, float]:
    penalties = {"equipo_1": 0.0, "equipo_2": 0.0}
    for trace in decision_traces:
        penalty = _aggressive_envite_penalty(trace)
        if penalty <= 0.0:
            continue
        penalties[trace.team_id] -= penalty
    return penalties


def _ordago_penalty(trace: DecisionTrace) -> float:
    if trace.action_type != AccionMus.ORDAGO.value:
        return 0.0
    if not _ordago_in_bad_context(trace):
        return ORDAGO_BASE_PENALTY

    fuerza = 0.0 if trace.lance_strength is None else trace.lance_strength
    margen = max(trace.score_own, trace.score_rival)
    distancia_cierre = max(0, ORDAGO_NEAR_CLOSE_SCORE - margen)
    brecha_fuerza = max(0.0, ORDAGO_SAFE_STRENGTH - fuerza)
    return (
        ORDAGO_BASE_PENALTY
        + ORDAGO_BAD_CONTEXT_BASE
        + ORDAGO_BAD_CONTEXT_DISTANCE_FACTOR * distancia_cierre
        + ORDAGO_BAD_CONTEXT_STRENGTH_FACTOR * brecha_fuerza
    )


def _ordago_in_bad_context(trace: DecisionTrace) -> bool:
    if trace.score_own >= ORDAGO_NEAR_CLOSE_SCORE:
        return False
    if trace.score_rival >= ORDAGO_NEAR_CLOSE_SCORE:
        return False
    if trace.lance_strength is not None and trace.lance_strength >= ORDAGO_SAFE_STRENGTH:
        return False
    return True


def _aggressive_envite_penalty(trace: DecisionTrace) -> float:
    if not _aggressive_envite_in_bad_context(trace):
        return 0.0

    if trace.quantity is None:
        return 0.0
    fuerza = 0.0 if trace.lance_strength is None else trace.lance_strength
    margen = max(trace.score_own, trace.score_rival)
    distancia_cierre = max(0, ENVITE_NEAR_CLOSE_SCORE - margen)
    brecha_fuerza = max(0.0, ENVITE_SAFE_STRENGTH - fuerza)
    exceso_envite = max(0, trace.quantity - 5)
    return (
        ENVITE_BAD_CONTEXT_BASE
        + ENVITE_BAD_CONTEXT_AMOUNT_FACTOR * exceso_envite
        + ENVITE_BAD_CONTEXT_DISTANCE_FACTOR * distancia_cierre
        + ENVITE_BAD_CONTEXT_STRENGTH_FACTOR * brecha_fuerza
    )


def _aggressive_envite_in_bad_context(trace: DecisionTrace) -> bool:
    if trace.action_type != AccionMus.ENVIDAR.value:
        return False
    if trace.quantity is None or trace.quantity < AGGRESSIVE_ENVITE_MIN_AMOUNT:
        return False
    if trace.score_own >= ENVITE_NEAR_CLOSE_SCORE:
        return False
    if trace.score_rival >= ENVITE_NEAR_CLOSE_SCORE:
        return False
    if trace.lance_strength is not None and trace.lance_strength >= ENVITE_SAFE_STRENGTH:
        return False
    return True


def _lance_strength_from_observation(observacion: Mapping[str, object]) -> float | None:
    lance = str(observacion.get("lance_actual") or observacion.get("fase") or "")
    if lance == "grande":
        valor = observacion.get("fuerza_grande")
    elif lance == "chica":
        valor = observacion.get("fuerza_chica")
    elif lance == "pares":
        valor = observacion.get("fuerza_pares")
    elif lance == "juego":
        valor = observacion.get("fuerza_juego")
    elif lance == "punto":
        valor = observacion.get("fuerza_punto")
    else:
        valor = None

    if isinstance(valor, (float, int)):
        return float(valor)
    return None


def resumir_decisiones(
    decision_traces: Sequence[DecisionTrace],
    *,
    team_id: str,
    episodes: int,
) -> dict[str, object]:
    """Resume tendencias de accion del equipo controlado."""

    filtradas = [trace for trace in decision_traces if trace.team_id == team_id]
    action_counts = Counter(trace.action_type for trace in filtradas)
    phase_action_counts: dict[str, Counter[str]] = defaultdict(Counter)
    envite_amounts: Counter[int] = Counter()
    for trace in filtradas:
        phase_action_counts[trace.phase][trace.action_label] += 1
        if trace.action_type == AccionMus.ENVIDAR.value and trace.quantity is not None:
            envite_amounts[trace.quantity] += 1

    total_decisiones = len(filtradas)
    mus_decisiones = action_counts.get(AccionMus.PEDIR_MUS.value, 0) + action_counts.get(
        AccionMus.CORTAR_MUS.value, 0
    )
    respuestas_envite = action_counts.get(AccionMus.QUIERO.value, 0) + action_counts.get(
        AccionMus.NO_QUIERO.value,
        0,
    )
    envites_totales = sum(envite_amounts.values())
    ordago_traces = [trace for trace in filtradas if trace.action_type == AccionMus.ORDAGO.value]
    ordagos_en_mal_contexto = sum(1 for trace in ordago_traces if _ordago_in_bad_context(trace))
    envites_agresivos = [
        trace
        for trace in filtradas
        if trace.action_type == AccionMus.ENVIDAR.value
        and trace.quantity is not None
        and trace.quantity >= AGGRESSIVE_ENVITE_MIN_AMOUNT
    ]
    envites_agresivos_en_mal_contexto = sum(
        1 for trace in envites_agresivos if _aggressive_envite_in_bad_context(trace)
    )
    avg_envite = (
        sum(cantidad * conteo for cantidad, conteo in envite_amounts.items()) / envites_totales
        if envites_totales
        else 0.0
    )
    avg_envite_agresivo = (
        sum((trace.quantity or 0) for trace in envites_agresivos) / len(envites_agresivos)
        if envites_agresivos
        else 0.0
    )

    return {
        "episodes": episodes,
        "total_decisions": total_decisiones,
        "action_counts": dict(action_counts),
        "phase_top_actions": {
            phase: [{"action": action, "count": count} for action, count in counter.most_common(3)]
            for phase, counter in phase_action_counts.items()
        },
        "mus_cut_rate": (
            action_counts.get(AccionMus.CORTAR_MUS.value, 0) / mus_decisiones
            if mus_decisiones
            else 0.0
        ),
        "quiero_rate": (
            action_counts.get(AccionMus.QUIERO.value, 0) / respuestas_envite
            if respuestas_envite
            else 0.0
        ),
        "no_quiero_rate": (
            action_counts.get(AccionMus.NO_QUIERO.value, 0) / respuestas_envite
            if respuestas_envite
            else 0.0
        ),
        "ordago_rate": (
            action_counts.get(AccionMus.ORDAGO.value, 0) / total_decisiones
            if total_decisiones
            else 0.0
        ),
        "ordago_bad_context_count": ordagos_en_mal_contexto,
        "ordago_bad_context_rate": (
            ordagos_en_mal_contexto / len(ordago_traces) if ordago_traces else 0.0
        ),
        "aggressive_envite_count": len(envites_agresivos),
        "aggressive_envite_bad_context_count": envites_agresivos_en_mal_contexto,
        "aggressive_envite_bad_context_rate": (
            envites_agresivos_en_mal_contexto / len(envites_agresivos) if envites_agresivos else 0.0
        ),
        "envite_rate": (envites_totales / total_decisiones if total_decisiones else 0.0),
        "avg_envite_amount": avg_envite,
        "avg_aggressive_envite_amount": avg_envite_agresivo,
        "envite_amounts": dict(sorted(envite_amounts.items())),
    }
