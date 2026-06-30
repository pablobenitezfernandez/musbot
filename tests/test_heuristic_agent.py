from __future__ import annotations

from musbot.agents.heuristic_agent import HeuristicAgent
from musbot.env.acciones import AccionLegal, AccionMus


def test_heuristic_agent_corta_mus_con_juego_fuerte() -> None:
    agent = HeuristicAgent(agent_id="heuristic")
    accion = agent.elegir_accion(
        [AccionMus.PEDIR_MUS, AccionMus.CORTAR_MUS],
        {
            "fase": "decision_mus",
            "tiene_pares": False,
            "tiene_juego": True,
            "valor_juego": 31,
            "valores_mus": [7, 7, 4, 1],
        },
    )

    assert accion == AccionLegal.simple(AccionMus.CORTAR_MUS)


def test_heuristic_agent_no_quiere_con_respuesta_debil() -> None:
    agent = HeuristicAgent(agent_id="heuristic")
    accion = agent.elegir_accion(
        [
            AccionMus.QUIERO,
            AccionMus.NO_QUIERO,
            AccionLegal.envidar(cantidad_minima=1),
            AccionMus.ORDAGO,
        ],
        {
            "fase": "grande",
            "lance_actual": "grande",
            "es_mano": False,
            "indice_turno": 3,
            "tiene_pares": False,
            "categoria_pares": None,
            "tiene_juego": False,
            "valor_punto": 23,
            "suma_cartas": 23,
            "valores_mus": [1, 2, 3, 4],
            "diferencial_marcador": -6,
            "marcador_propio": 18,
            "marcador_rival": 24,
            "legal_action_labels": ["quiero", "no_quiero", "envidar:1", "ordago"],
            "detalle_envite_pendiente": {
                "tipo_apuesta": "envite",
                "lance": "grande",
                "cantidad_actual": 7,
                "cantidad_previa": 5,
                "es_reenvite": True,
                "valor_no_quiero": 5,
                "jugador_apostador": "j2",
                "equipo_apostador": "equipo_2",
                "soy_equipo_apostador": False,
                "me_toca_responder": True,
            },
        },
    )

    assert accion == AccionLegal.simple(AccionMus.NO_QUIERO)


def test_heuristic_agent_abre_envite_con_pares_fuertes() -> None:
    agent = HeuristicAgent(agent_id="heuristic")
    accion = agent.elegir_accion(
        [
            AccionMus.PASAR,
            AccionLegal.envidar(cantidad=2),
            AccionLegal.envidar(cantidad=5),
            AccionMus.ORDAGO,
        ],
        {
            "fase": "pares",
            "lance_actual": "pares",
            "es_mano": True,
            "indice_turno": 0,
            "tiene_pares": True,
            "categoria_pares": "duples",
            "puntos_pares": 3,
            "tiene_juego": False,
            "valor_punto": 28,
            "suma_cartas": 28,
            "valores_mus": [7, 7, 0, 0],
            "diferencial_marcador": 3,
            "marcador_propio": 30,
            "marcador_rival": 27,
            "legal_action_labels": ["pasar", "envidar:2", "envidar:5", "ordago"],
        },
    )

    assert accion == AccionLegal.envidar(5)


def test_heuristic_agent_abre_pares_altos_simples() -> None:
    agent = HeuristicAgent(agent_id="heuristic")
    accion = agent.elegir_accion(
        [
            AccionMus.PASAR,
            AccionLegal.envidar(cantidad=2),
            AccionLegal.envidar(cantidad=3),
            AccionMus.ORDAGO,
        ],
        {
            "fase": "pares",
            "lance_actual": "pares",
            "es_mano": True,
            "indice_turno": 0,
            "tiene_pares": True,
            "categoria_pares": "pares",
            "puntos_pares": 1,
            "tiene_juego": True,
            "valor_juego": 31,
            "valor_punto": None,
            "suma_cartas": 31,
            "valores_mus": [7, 7, 4, 1],
            "fuerza_pares": 0.74,
            "legal_action_labels": ["pasar", "envidar:2", "envidar:3", "ordago"],
        },
    )

    assert accion == AccionLegal.envidar(2)
