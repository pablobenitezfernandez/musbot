from __future__ import annotations

import pytest

from musbot.agents.cfr_agent import (
    ENVIDAR_CHICO,
    ENVIDAR_GRANDE,
    CFRAgent,
    acciones_abstractas,
    acciones_descarte_abstractas,
    infoset_key,
    probabilidades_desde_politica,
    rondas_mus_jugadas,
)
from musbot.core.motor import MotorMus
from musbot.env.acciones import AccionLegal, AccionMus
from musbot.training.cfr import CFRTrainer, entrenar_cfr
from musbot.training.self_play import jugar_mano


def test_acciones_abstractas_colapsa_envites_en_apertura() -> None:
    legales = [
        AccionLegal.simple(AccionMus.PASAR),
        AccionLegal.envidar(),  # plantilla sin cantidad
        AccionLegal.simple(AccionMus.ORDAGO),
    ]
    abstractas = dict(acciones_abstractas(legales, obs=None))

    assert set(abstractas) == {"pasar", "ordago", ENVIDAR_CHICO, ENVIDAR_GRANDE}
    # Apertura (pendiente 0): chico sube al nivel 2, grande al nivel 20.
    assert abstractas[ENVIDAR_CHICO].cantidad == 2
    assert abstractas[ENVIDAR_GRANDE].cantidad == 20


def test_acciones_abstractas_respeta_apuesta_pendiente() -> None:
    legales = [
        AccionLegal.simple(AccionMus.QUIERO),
        AccionLegal.simple(AccionMus.NO_QUIERO),
        AccionLegal.envidar(),
        AccionLegal.simple(AccionMus.ORDAGO),
    ]
    obs = {"detalle_envite_pendiente": {"cantidad_actual": 6}}
    abstractas = dict(acciones_abstractas(legales, obs))

    # Con pendiente 6 quedan dos niveles superiores (10 y 20): chico sube al 10
    # (incremento 4) y grande al 20 (incremento 14).
    assert abstractas[ENVIDAR_CHICO].cantidad == 4
    assert abstractas[ENVIDAR_GRANDE].cantidad == 14
    assert {"quiero", "no_quiero", "ordago"} <= set(abstractas)


def test_acciones_abstractas_sin_subida_si_pendiente_alto() -> None:
    legales = [
        AccionLegal.simple(AccionMus.QUIERO),
        AccionLegal.simple(AccionMus.NO_QUIERO),
        AccionLegal.envidar(),
    ]
    obs = {"detalle_envite_pendiente": {"cantidad_actual": 20}}
    abstractas = dict(acciones_abstractas(legales, obs))

    assert ENVIDAR_CHICO not in abstractas
    assert ENVIDAR_GRANDE not in abstractas
    assert set(abstractas) == {"quiero", "no_quiero"}


def test_infoset_key_es_estable_y_distingue_fuerza() -> None:
    base = {
        "fase": "grande",
        "lance_actual": "grande",
        "indice_turno": 0,
        "fuerza_grande": 0.9,
        "categoria_pares": None,
        "tiene_juego": False,
        "valor_juego": None,
        "diferencial_marcador": 0,
        "detalle_envite_pendiente": None,
    }
    debil = {**base, "fuerza_grande": 0.1}

    assert infoset_key(base) == infoset_key(dict(base))
    assert infoset_key(base) != infoset_key(debil)


def test_regret_matching_uniforme_y_proporcional() -> None:
    trainer = CFRTrainer()
    # Sin regret previo -> uniforme.
    uniforme = trainer._regret_matching("nuevo", ["a", "b", "c", "d"])
    assert all(abs(p - 0.25) < 1e-9 for p in uniforme.values())

    trainer.regret_sum["I"] = {"a": 3.0, "b": 1.0, "c": -5.0}
    dist = trainer._regret_matching("I", ["a", "b", "c"])
    assert dist["a"] == pytest.approx(0.75)
    assert dist["b"] == pytest.approx(0.25)
    assert dist["c"] == pytest.approx(0.0)


def test_probabilidades_respaldo_evita_ordago() -> None:
    labels = ["pasar", "envidar_chico", "ordago"]
    # Sin política -> uniforme sobre no agresivas (sin ordago).
    dist = probabilidades_desde_politica(None, labels)
    assert dist["ordago"] == 0.0
    assert dist["pasar"] == pytest.approx(0.5)
    assert dist["envidar_chico"] == pytest.approx(0.5)


def test_probabilidades_normaliza_politica_parcial() -> None:
    labels = ["pasar", "quiero"]
    dist = probabilidades_desde_politica({"pasar": 3.0, "quiero": 1.0}, labels)
    assert dist["pasar"] == pytest.approx(0.75)
    assert dist["quiero"] == pytest.approx(0.25)


def test_entrenar_cfr_produce_politica_valida() -> None:
    motor = MotorMus()
    trainer = entrenar_cfr(motor, iteraciones=12, seed=0)
    politica = trainer.average_strategy()

    assert politica  # se visitaron information sets
    for distribucion in politica.values():
        assert distribucion
        assert sum(distribucion.values()) == pytest.approx(1.0)


def test_cfr_agent_juega_acciones_legales_vs_random() -> None:
    motor = MotorMus()
    trainer = entrenar_cfr(motor, iteraciones=12, seed=1)
    agente = trainer.build_agent(seed=7)

    # jugar_mano valida la legalidad de cada acción contra el motor.
    resultado = jugar_mano(
        motor,
        {
            "j1": agente,
            "j3": agente,
            "j2": agente,
            "j4": agente,
        },
        seed=99,
    )
    assert resultado.final_state.fase.value == "finalizada"


def test_entrenar_cfr_modelando_mus_juega_legal() -> None:
    # El camino modelar_mus=True (mus + descartes) entrena y juega sin acciones
    # ilegales (jugar_mano valida contra el motor).
    motor = MotorMus()
    trainer = entrenar_cfr(motor, iteraciones=10, seed=2, modelar_mus=True)
    agente = trainer.build_agent(seed=5)
    assert agente.modelar_mus is True

    resultado = jugar_mano(
        motor,
        {"j1": agente, "j3": agente, "j2": agente, "j4": agente},
        seed=123,
    )
    assert resultado.final_state.fase.value == "finalizada"


def _obs_mus(historial: list[str] | None = None) -> dict[str, object]:
    return {
        "fase": "decision_mus",
        "lance_actual": None,
        "indice_turno": 0,
        "fuerza_grande": 0.5,
        "fuerza_chica": 0.5,
        "categoria_pares": None,
        "tiene_juego": False,
        "valor_juego": None,
        "diferencial_marcador": 0,
        "detalle_envite_pendiente": None,
        "historial_publico": historial or [],
    }


def test_cfr_agent_decide_mus_segun_politica() -> None:
    obs = _obs_mus()
    clave = infoset_key(obs)
    legales = [
        AccionLegal.simple(AccionMus.PEDIR_MUS),
        AccionLegal.simple(AccionMus.CORTAR_MUS),
    ]

    pide = CFRAgent(
        agent_id="cfr",
        seed=0,
        modelar_mus=True,
        policy={clave: {"pedir_mus": 1.0, "cortar_mus": 0.0}},
    )
    corta = CFRAgent(
        agent_id="cfr",
        seed=0,
        modelar_mus=True,
        policy={clave: {"pedir_mus": 0.0, "cortar_mus": 1.0}},
    )

    assert pide.elegir_accion(legales, obs).tipo is AccionMus.PEDIR_MUS
    assert corta.elegir_accion(legales, obs).tipo is AccionMus.CORTAR_MUS


def test_cfr_agent_por_defecto_corta_mus() -> None:
    # Sin modelar el mus (default), corta siempre aunque la política diga pedir.
    obs = _obs_mus()
    clave = infoset_key(obs)
    agente = CFRAgent(agent_id="cfr", seed=0, policy={clave: {"pedir_mus": 1.0, "cortar_mus": 0.0}})
    legales = [
        AccionLegal.simple(AccionMus.PEDIR_MUS),
        AccionLegal.simple(AccionMus.CORTAR_MUS),
    ]
    assert agente.elegir_accion(legales, obs).tipo is AccionMus.CORTAR_MUS


def test_cfr_agent_corta_al_alcanzar_tope_de_rondas() -> None:
    # 2 rondas completadas (8 descartes) -> corta pase lo que pase la política.
    historial = [f"j{(i % 4) + 1}:descarta:1" for i in range(8)]
    obs = _obs_mus(historial)
    clave = infoset_key(obs)
    agente = CFRAgent(
        agent_id="cfr",
        seed=0,
        modelar_mus=True,
        policy={clave: {"pedir_mus": 1.0, "cortar_mus": 0.0}},
    )
    legales = [
        AccionLegal.simple(AccionMus.PEDIR_MUS),
        AccionLegal.simple(AccionMus.CORTAR_MUS),
    ]
    assert agente.elegir_accion(legales, obs).tipo is AccionMus.CORTAR_MUS


def test_acciones_descarte_abstractas_ofrece_patrones() -> None:
    # Mano sin parejas con altas y bajas -> ofrece tirar bajas, tirar altas y todo.
    menu = dict(acciones_descarte_abstractas([7, 6, 2, 1]))  # rey, caballo, cinco, cuatro
    assert menu["descartar_bajas"] == (2, 3)  # tira cinco(2) y cuatro(1)
    assert menu["descartar_altas"] == (0, 1)  # tira rey(7) y caballo(6)
    assert menu["descartar_todo"] == (0, 1, 2, 3)


def test_acciones_descarte_conserva_parejas() -> None:
    # Par de reyes (idx 0,1): nunca se descartan; solo entran las sueltas.
    menu = dict(acciones_descarte_abstractas([7, 7, 6, 1]))  # rey, rey, caballo, cuatro
    assert 0 not in menu["descartar_bajas"] and 1 not in menu["descartar_bajas"]
    assert menu["descartar_bajas"] == (3,)  # cuatro(1) es baja suelta
    assert menu["descartar_altas"] == (2,)  # caballo(6) es alta suelta


def test_rondas_mus_jugadas_cuenta_descartes() -> None:
    assert rondas_mus_jugadas({"historial_publico": []}) == 0
    assert rondas_mus_jugadas({"historial_publico": ["j1:descarta:2", "j2:descarta:0"]}) == 0
    cuatro = [f"j{i + 1}:descarta:1" for i in range(4)]
    assert rondas_mus_jugadas({"historial_publico": cuatro}) == 1


def test_cfr_agent_roundtrip_serializacion() -> None:
    agente = CFRAgent(
        agent_id="cfr",
        seed=3,
        policy={"1|0|3|0|0|1|abre": {"pasar": 0.6, "envidar_chico": 0.4}},
    )
    restaurado = CFRAgent.from_state_dict(agente.to_state_dict())

    assert restaurado.model_version == "cfr_v1"
    assert restaurado.policy == agente.policy
