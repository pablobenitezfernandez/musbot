from __future__ import annotations

import pytest

from musbot.agents.rl_agent import ExperienceStep, RLAgent


def test_rl_agent_v2_distingue_apertura_de_reenvite() -> None:
    agente = RLAgent(agent_id="rl_v2", state_encoder_version="v2", model_version="tabular_v2")
    base = {
        "fase": "grande",
        "lance_actual": "grande",
        "es_mano": True,
        "indice_turno": 0,
        "tiene_pares": False,
        "categoria_pares": None,
        "tiene_juego": False,
        "valor_punto": 30,
        "suma_cartas": 30,
        "valores_mus": [7, 4, 3, 1],
        "diferencial_marcador": 0,
        "marcador_propio": 20,
        "marcador_rival": 20,
        "legal_action_labels": ["quiero", "no_quiero", "envidar:1", "ordago"],
    }

    apertura = {
        **base,
        "detalle_envite_pendiente": {
            "tipo_apuesta": "envite",
            "lance": "grande",
            "cantidad_actual": 2,
            "cantidad_previa": 0,
            "es_reenvite": False,
            "valor_no_quiero": 1,
            "jugador_apostador": "j1",
            "equipo_apostador": "equipo_1",
            "soy_equipo_apostador": False,
            "me_toca_responder": True,
        },
    }
    reenvite = {
        **base,
        "detalle_envite_pendiente": {
            "tipo_apuesta": "envite",
            "lance": "grande",
            "cantidad_actual": 12,
            "cantidad_previa": 5,
            "es_reenvite": True,
            "valor_no_quiero": 5,
            "jugador_apostador": "j2",
            "equipo_apostador": "equipo_2",
            "soy_equipo_apostador": False,
            "me_toca_responder": True,
        },
    }

    assert agente.state_key(apertura) != agente.state_key(reenvite)


def test_rl_agent_actualiza_hacia_recompensa_y_acumula_visitas() -> None:
    # Learning rate adaptativo: alpha = 1 / (1 + visitas).
    agente = RLAgent(agent_id="rl_v5")
    experiencias = [ExperienceStep(state_key="estado", action_key="pasar")]

    agente.actualizar_desde_experiencias(experiencias, recompensa_final=1.0)
    assert agente.policy["estado"]["pasar"] == 0.5  # alpha=1/2
    assert agente.visit_counts["estado"]["pasar"] == 1

    agente.actualizar_desde_experiencias(experiencias, recompensa_final=1.0)
    assert agente.policy["estado"]["pasar"] == pytest.approx(2 / 3)  # 0.5 + (1/3)(0.5)
    assert agente.visit_counts["estado"]["pasar"] == 2

    agente.actualizar_desde_experiencias(experiencias, recompensa_final=-1.0)
    assert agente.policy["estado"]["pasar"] == pytest.approx(0.25)  # 2/3 + (1/4)(-5/3)
    assert agente.visit_counts["estado"]["pasar"] == 3


def test_rl_agent_serializa_visitas_y_version() -> None:
    agente = RLAgent(
        agent_id="rl_v2",
        state_encoder_version="v2",
        model_version="tabular_v2",
        learning_rate=0.5,
    )
    agente.actualizar_desde_experiencias(
        [ExperienceStep(state_key="estado", action_key="quiero")],
        recompensa_final=1.0,
    )

    payload = agente.to_state_dict()
    restaurado = RLAgent.from_state_dict(payload)

    assert restaurado.model_version == "tabular_v2"
    assert restaurado.state_encoder_version == "v2"
    assert restaurado.visit_counts == {"estado": {"quiero": 1}}
    assert restaurado.policy == {"estado": {"quiero": 0.5}}


def test_rl_agent_v3_distingue_informacion_publica_de_pares() -> None:
    agente = RLAgent(agent_id="rl_v3", state_encoder_version="v3", model_version="tabular_v3")
    base = {
        "fase": "pares",
        "lance_actual": "pares",
        "indice_turno": 1,
        "diferencial_marcador": 0,
        "marcador_propio": 20,
        "marcador_rival": 20,
        "categoria_pares": "pares",
        "tiene_juego": False,
        "valor_punto": 28,
        "valores_mus": [7, 7, 2, 1],
        "legal_action_labels": ["pasar", "envidar:2", "ordago"],
        "detalle_envite_pendiente": None,
        "conteo_pares_propios": 1,
        "conteo_pares_rivales": 1,
        "conteo_juego_propios": 0,
        "conteo_juego_rivales": 0,
        "ultimo_evento_publico": "j2:paso:chica",
        "conteo_eventos_publicos": 3,
    }

    solo_pares_mios = {
        **base,
        "conteo_pares_propios": 2,
        "conteo_pares_rivales": 0,
    }

    assert agente.state_key(base) != agente.state_key(solo_pares_mios)


def test_rl_agent_v4_distingue_pares_altos_de_medias_debiles() -> None:
    agente = RLAgent(agent_id="rl_v4", state_encoder_version="v4", model_version="tabular_v4")
    base = {
        "fase": "pares",
        "lance_actual": "pares",
        "indice_turno": 0,
        "diferencial_marcador": 0,
        "marcador_propio": 20,
        "marcador_rival": 20,
        "fuerza_grande": 0.82,
        "fuerza_chica": 0.24,
        "conteo_pares_propios": 1,
        "conteo_pares_rivales": 1,
        "conteo_juego_propios": 1,
        "conteo_juego_rivales": 1,
        "ultimo_evento_publico": "j2:paso:chica",
        "conteo_eventos_publicos": 5,
        "legal_action_labels": ["pasar", "envidar:2", "ordago"],
        "detalle_envite_pendiente": None,
    }
    pares_altos = {
        **base,
        "categoria_pares": "pares",
        "fuerza_pares": 0.74,
        "tiene_juego": True,
        "valor_juego": 31,
        "fuerza_juego": 1.0,
        "fuerza_punto": None,
    }
    medias_flojas = {
        **base,
        "categoria_pares": "medias",
        "fuerza_pares": 0.45,
        "tiene_juego": False,
        "valor_juego": None,
        "fuerza_juego": None,
        "fuerza_punto": 0.30,
    }

    assert agente.state_key(pares_altos) != agente.state_key(medias_flojas)


def _obs_v5_base() -> dict[str, object]:
    return {
        "fase": "grande",
        "lance_actual": "grande",
        "es_mano": True,
        "fuerza_grande": 0.85,
        "fuerza_chica": 0.20,
        "fuerza_pares": None,
        "fuerza_juego": None,
        "fuerza_punto": None,
        "tiene_pares": False,
        "categoria_pares": None,
        "tiene_juego": False,
        "valor_juego": None,
        "diferencial_marcador": 0,
        "envite_pendiente": None,
        "detalle_envite_pendiente": None,
    }


def test_rl_agent_v5_genera_clave_compacta_de_ocho_campos() -> None:
    agente = RLAgent(agent_id="rl_v5", state_encoder_version="v5", model_version="tabular_v5")
    clave = agente.state_key(_obs_v5_base())

    # fase=1(grande), mano=1, fuerza=2(alta), pares=0, juego=0,
    # marcador=1(igualado), envite=0, respondedor=0
    assert clave == "1|1|2|0|0|1|0|0"


def test_rl_agent_v5_distingue_fuerza_del_lance_actual() -> None:
    agente = RLAgent(agent_id="rl_v5", state_encoder_version="v5", model_version="tabular_v5")
    fuerte = _obs_v5_base()
    debil = {**_obs_v5_base(), "fuerza_grande": 0.10}

    assert agente.state_key(fuerte) != agente.state_key(debil)


def test_rl_agent_v5_distingue_envite_pendiente_y_respondedor() -> None:
    agente = RLAgent(agent_id="rl_v5", state_encoder_version="v5", model_version="tabular_v5")
    sin_envite = _obs_v5_base()
    con_envite = {
        **_obs_v5_base(),
        "envite_pendiente": "envite:grande:5",
        "detalle_envite_pendiente": {"me_toca_responder": True},
    }

    assert agente.state_key(sin_envite) != agente.state_key(con_envite)


def test_rl_agent_v5_marcador_relativo_buckets() -> None:
    agente = RLAgent(agent_id="rl_v5", state_encoder_version="v5", model_version="tabular_v5")
    perdiendo = {**_obs_v5_base(), "diferencial_marcador": -8}
    igualado = {**_obs_v5_base(), "diferencial_marcador": 2}
    ganando = {**_obs_v5_base(), "diferencial_marcador": 8}

    claves = {
        agente.state_key(perdiendo),
        agente.state_key(igualado),
        agente.state_key(ganando),
    }
    assert len(claves) == 3


def test_rl_agent_epsilon_decay_respeta_minimo() -> None:
    agente = RLAgent(agent_id="rl_v5", epsilon=1.0)

    agente.decay_epsilon(decay_rate=0.5, epsilon_min=0.05)
    assert agente.epsilon == 0.5

    for _ in range(50):
        agente.decay_epsilon(decay_rate=0.5, epsilon_min=0.05)
    assert agente.epsilon == 0.05


def test_rl_agent_v5_roundtrip_serializacion() -> None:
    agente = RLAgent(
        agent_id="rl_v5",
        state_encoder_version="v5",
        model_version="tabular_v5",
        epsilon=0.42,
    )
    agente.actualizar_desde_experiencias(
        [ExperienceStep(state_key="1|1|2|0|0|1|0|0", action_key="pasar")],
        recompensa_final=1.0,
    )

    restaurado = RLAgent.from_state_dict(agente.to_state_dict())

    assert restaurado.model_version == "tabular_v5"
    assert restaurado.state_encoder_version == "v5"
    assert restaurado.epsilon == 0.42
    assert restaurado.policy == {"1|1|2|0|0|1|0|0": {"pasar": 0.5}}
