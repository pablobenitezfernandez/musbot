from musbot.training.self_play import (
    DecisionTrace,
    _aggressive_envite_in_bad_context,
    _ordago_in_bad_context,
    _reward_by_team,
    resumir_decisiones,
)


def test_ordago_bad_context_depende_de_marcador_y_fuerza() -> None:
    debil = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="grande",
        lance_actual="grande",
        action_label="ordago",
        action_type="ordago",
        quantity=None,
        score_own=20,
        score_rival=20,
        lance_strength=0.62,
    )
    fuerte = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="juego",
        lance_actual="juego",
        action_label="ordago",
        action_type="ordago",
        quantity=None,
        score_own=20,
        score_rival=20,
        lance_strength=1.0,
    )
    cierre = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="grande",
        lance_actual="grande",
        action_label="ordago",
        action_type="ordago",
        quantity=None,
        score_own=38,
        score_rival=25,
        lance_strength=0.45,
    )

    assert _ordago_in_bad_context(debil) is True
    assert _ordago_in_bad_context(fuerte) is False
    assert _ordago_in_bad_context(cierre) is False


def test_reward_by_team_penaliza_mas_el_ordago_debil() -> None:
    base = _reward_by_team(
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
        decision_traces=[
            DecisionTrace(
                player_id="j1",
                team_id="equipo_1",
                phase="grande",
                lance_actual="grande",
                action_label="ordago",
                action_type="ordago",
                quantity=None,
                score_own=10,
                score_rival=10,
                lance_strength=0.60,
            )
        ],
    )
    con_ordago_fuerte = _reward_by_team(
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
        marcador_final={"equipo_1": 10, "equipo_2": 0},
        juegos_iniciales={"equipo_1": 0, "equipo_2": 0},
        juegos_finales={"equipo_1": 0, "equipo_2": 0},
        decision_traces=[
            DecisionTrace(
                player_id="j1",
                team_id="equipo_1",
                phase="juego",
                lance_actual="juego",
                action_label="ordago",
                action_type="ordago",
                quantity=None,
                score_own=10,
                score_rival=10,
                lance_strength=1.0,
            )
        ],
    )

    assert base["equipo_1"] > con_ordago_fuerte["equipo_1"] > con_ordago_debil["equipo_1"]


def test_envite_agresivo_bad_context_depende_de_marcador_fuerza_y_cantidad() -> None:
    agresivo_debil = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="grande",
        lance_actual="grande",
        action_label="envidar:20",
        action_type="envidar",
        quantity=20,
        score_own=18,
        score_rival=15,
        lance_strength=0.55,
    )
    agresivo_fuerte = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="juego",
        lance_actual="juego",
        action_label="envidar:20",
        action_type="envidar",
        quantity=20,
        score_own=18,
        score_rival=15,
        lance_strength=1.0,
    )
    pequeno_debil = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="pares",
        lance_actual="pares",
        action_label="envidar:3",
        action_type="envidar",
        quantity=3,
        score_own=18,
        score_rival=15,
        lance_strength=0.40,
    )
    cierre = DecisionTrace(
        player_id="j1",
        team_id="equipo_1",
        phase="grande",
        lance_actual="grande",
        action_label="envidar:20",
        action_type="envidar",
        quantity=20,
        score_own=36,
        score_rival=20,
        lance_strength=0.40,
    )

    assert _aggressive_envite_in_bad_context(agresivo_debil) is True
    assert _aggressive_envite_in_bad_context(agresivo_fuerte) is False
    assert _aggressive_envite_in_bad_context(pequeno_debil) is False
    assert _aggressive_envite_in_bad_context(cierre) is False


def test_reward_by_team_penaliza_envite_agresivo_debil() -> None:
    base = _reward_by_team(
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
        marcador_final={"equipo_1": 10, "equipo_2": 0},
        juegos_iniciales={"equipo_1": 0, "equipo_2": 0},
        juegos_finales={"equipo_1": 0, "equipo_2": 0},
        decision_traces=[],
    )
    con_envite_agresivo_debil = _reward_by_team(
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
        marcador_final={"equipo_1": 10, "equipo_2": 0},
        juegos_iniciales={"equipo_1": 0, "equipo_2": 0},
        juegos_finales={"equipo_1": 0, "equipo_2": 0},
        decision_traces=[
            DecisionTrace(
                player_id="j1",
                team_id="equipo_1",
                phase="grande",
                lance_actual="grande",
                action_label="envidar:20",
                action_type="envidar",
                quantity=20,
                score_own=10,
                score_rival=10,
                lance_strength=0.55,
            )
        ],
    )
    con_envite_agresivo_fuerte = _reward_by_team(
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
        marcador_final={"equipo_1": 10, "equipo_2": 0},
        juegos_iniciales={"equipo_1": 0, "equipo_2": 0},
        juegos_finales={"equipo_1": 0, "equipo_2": 0},
        decision_traces=[
            DecisionTrace(
                player_id="j1",
                team_id="equipo_1",
                phase="juego",
                lance_actual="juego",
                action_label="envidar:20",
                action_type="envidar",
                quantity=20,
                score_own=10,
                score_rival=10,
                lance_strength=1.0,
            )
        ],
    )

    assert base["equipo_1"] == con_envite_agresivo_fuerte["equipo_1"]
    assert base["equipo_1"] > con_envite_agresivo_debil["equipo_1"]


def test_resumir_decisiones_expone_ordago_en_mal_contexto() -> None:
    resumen = resumir_decisiones(
        [
            DecisionTrace(
                player_id="j1",
                team_id="equipo_1",
                phase="grande",
                lance_actual="grande",
                action_label="ordago",
                action_type="ordago",
                quantity=None,
                score_own=15,
                score_rival=14,
                lance_strength=0.50,
            ),
            DecisionTrace(
                player_id="j3",
                team_id="equipo_1",
                phase="juego",
                lance_actual="juego",
                action_label="ordago",
                action_type="ordago",
                quantity=None,
                score_own=39,
                score_rival=30,
                lance_strength=0.40,
            ),
        ],
        team_id="equipo_1",
        episodes=2,
    )

    assert resumen["ordago_bad_context_count"] == 1
    assert resumen["ordago_bad_context_rate"] == 0.5


def test_resumir_decisiones_expone_envites_agresivos_en_mal_contexto() -> None:
    resumen = resumir_decisiones(
        [
            DecisionTrace(
                player_id="j1",
                team_id="equipo_1",
                phase="grande",
                lance_actual="grande",
                action_label="envidar:20",
                action_type="envidar",
                quantity=20,
                score_own=15,
                score_rival=14,
                lance_strength=0.50,
            ),
            DecisionTrace(
                player_id="j3",
                team_id="equipo_1",
                phase="juego",
                lance_actual="juego",
                action_label="envidar:10",
                action_type="envidar",
                quantity=10,
                score_own=38,
                score_rival=30,
                lance_strength=0.40,
            ),
        ],
        team_id="equipo_1",
        episodes=2,
    )

    assert resumen["aggressive_envite_count"] == 2
    assert resumen["aggressive_envite_bad_context_count"] == 1
    assert resumen["aggressive_envite_bad_context_rate"] == 0.5
