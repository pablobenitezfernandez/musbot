from musbot.training.self_play import (
    DecisionTrace,
    _aggressive_envite_in_bad_context,
    _ordago_in_bad_context,
    _reward_by_team,
    resumir_decisiones,
)


def _trace(
    action_type: str,
    quantity: int | None = None,
    score_own: int = 20,
    score_rival: int = 20,
    lance_strength: float | None = 0.5,
    lance_actual: str = "grande",
) -> DecisionTrace:
    return DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase=lance_actual,
        lance_actual=lance_actual,
        action_label=action_type,
        action_type=action_type,
        quantity=quantity,
        score_own=score_own,
        score_rival=score_rival,
        lance_strength=lance_strength,
    )


def test_ordago_bad_context_depende_de_marcador_y_fuerza() -> None:
    assert _ordago_in_bad_context(_trace("ordago", lance_strength=0.62)) is True
    assert _ordago_in_bad_context(_trace("ordago", lance_strength=1.0)) is False
    assert _ordago_in_bad_context(_trace("ordago", score_own=38, lance_strength=0.45)) is False


def test_envite_agresivo_bad_context_depende_de_marcador_fuerza_y_cantidad() -> None:
    malo = _aggressive_envite_in_bad_context
    assert malo(_trace("envidar", quantity=20, lance_strength=0.55)) is True
    assert malo(_trace("envidar", quantity=20, lance_strength=1.0)) is False
    assert malo(_trace("envidar", quantity=3, lance_strength=0.40)) is False
    assert malo(_trace("envidar", quantity=20, score_own=36, lance_strength=0.40)) is False


def test_reward_by_team_no_aplica_penalizaciones() -> None:
    """El reward solo depende del resultado de la mano, no de penalizaciones."""
    sin_traces = _reward_by_team(
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
        marcador_final={"equipo_1": 10, "equipo_2": 0},
        juegos_iniciales={"equipo_1": 0, "equipo_2": 0},
        juegos_finales={"equipo_1": 0, "equipo_2": 0},
        decision_traces=[],
    )
    con_ordago_debil = _reward_by_team(
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
        marcador_final={"equipo_1": 10, "equipo_2": 0},
        juegos_iniciales={"equipo_1": 0, "equipo_2": 0},
        juegos_finales={"equipo_1": 0, "equipo_2": 0},
        decision_traces=[_trace("ordago", lance_strength=0.10)],
    )
    assert sin_traces["equipo_1"] == con_ordago_debil["equipo_1"]


def test_resumir_decisiones_expone_ordago_en_mal_contexto() -> None:
    resumen = resumir_decisiones(
        [
            _trace("ordago", score_own=15, score_rival=14, lance_strength=0.50),
            _trace("ordago", score_own=39, score_rival=30, lance_strength=0.40),
        ],
        team_id="equipo_1",
        episodes=2,
    )

    assert resumen["ordago_bad_context_count"] == 1
    assert resumen["ordago_bad_context_rate"] == 0.5


def test_resumir_decisiones_expone_envites_agresivos_en_mal_contexto() -> None:
    resumen = resumir_decisiones(
        [
            _trace("envidar", quantity=20, score_own=15, score_rival=14, lance_strength=0.50),
            _trace("envidar", quantity=10, score_own=38, score_rival=30, lance_strength=0.40),
        ],
        team_id="equipo_1",
        episodes=2,
    )

    assert resumen["aggressive_envite_count"] == 2
    assert resumen["aggressive_envite_bad_context_count"] == 1
    assert resumen["aggressive_envite_bad_context_rate"] == 0.5
