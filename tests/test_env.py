from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from musbot.agents.base_agent import BaseAgent, LegalAction, Observacion
from musbot.agents.random_agent import RandomAgent
from musbot.core.cartas import Carta, Figura, Palo
from musbot.core.motor import MotorMus
from musbot.env import ACTION_SPACE_SIZE, MusEnv
from musbot.env.acciones import AccionLegal, AccionMus
from musbot.env.observaciones import construir_observacion_agente


@dataclass(slots=True)
class PreferActionAgent(BaseAgent):
    preferencias: tuple[AccionMus, ...]

    def elegir_accion(
        self,
        acciones_legales: Sequence[LegalAction],
        observacion: Observacion = None,
    ) -> LegalAction:
        del observacion

        for preferida in self.preferencias:
            for accion in acciones_legales:
                materializada = (
                    accion if isinstance(accion, AccionLegal) else AccionLegal.simple(accion)
                )
                if materializada.tipo is preferida:
                    return accion

        if not acciones_legales:
            raise ValueError("El agente necesita al menos una accion legal.")
        return acciones_legales[0]


def test_random_agent_elige_accion_legal() -> None:
    agent = RandomAgent(agent_id="random", seed=123)
    acciones = [AccionMus.PASAR, AccionMus.ENVIDAR, AccionMus.ORDAGO]

    accion = agent.elegir_accion(acciones)

    assert accion in acciones


def test_random_agent_falla_si_no_hay_acciones_legales() -> None:
    agent = RandomAgent(agent_id="random")

    with pytest.raises(ValueError):
        agent.elegir_accion([])


def test_mus_env_reset_expone_acciones_legales_y_mascara() -> None:
    env = MusEnv(
        uncontrolled_agents={
            "j2": PreferActionAgent(agent_id="j2", preferencias=(AccionMus.PEDIR_MUS,)),
            "j4": PreferActionAgent(agent_id="j4", preferencias=(AccionMus.PEDIR_MUS,)),
        }
    )

    observacion, info = env.reset(seed=123)

    assert observacion is not None
    assert observacion.jugador_id == "j1"
    assert observacion.fase == "decision_mus"
    assert len(observacion.action_mask) == ACTION_SPACE_SIZE
    assert sum(observacion.action_mask) == 2
    assert set(observacion.legal_action_labels) == {"pedir_mus", "cortar_mus"}
    assert info["controlled_team_id"] == "equipo_1"


def test_mus_env_step_avanza_hasta_siguiente_jugador_controlado() -> None:
    env = MusEnv(
        uncontrolled_agents={
            "j2": PreferActionAgent(agent_id="j2", preferencias=(AccionMus.PEDIR_MUS,)),
            "j4": PreferActionAgent(agent_id="j4", preferencias=(AccionMus.PEDIR_MUS,)),
        }
    )

    observacion, _ = env.reset(seed=7)
    assert observacion is not None

    observacion, reward, terminated, truncated, _ = env.step(env.encode_action(AccionMus.PEDIR_MUS))

    assert observacion is not None
    assert reward == 0.0
    assert not terminated
    assert not truncated
    assert observacion.jugador_id == "j3"
    assert observacion.fase == "decision_mus"

    observacion, reward, terminated, truncated, _ = env.step(env.encode_action(AccionMus.PEDIR_MUS))

    assert observacion is not None
    assert reward == 0.0
    assert not terminated
    assert not truncated
    assert observacion.jugador_id == "j3"
    assert observacion.fase == "descarte"
    assert "descartar:[]" in observacion.legal_action_labels


def test_mus_env_expone_no_quiero_ante_un_envite_pendiente() -> None:
    env = MusEnv(
        controlled_players=("j2", "j4"),
        uncontrolled_agents={
            "j1": PreferActionAgent(
                agent_id="j1",
                preferencias=(AccionMus.CORTAR_MUS, AccionMus.ENVIDAR),
            ),
            "j3": PreferActionAgent(agent_id="j3", preferencias=(AccionMus.PASAR,)),
        },
    )

    observacion, _ = env.reset(
        manos_iniciales={
            "j1": [
                _carta(Figura.REY, Palo.OROS),
                _carta(Figura.SIETE, Palo.COPAS),
                _carta(Figura.SEIS, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.BASTOS),
            ],
            "j2": [
                _carta(Figura.CABALLO, Palo.OROS),
                _carta(Figura.CINCO, Palo.COPAS),
                _carta(Figura.CUATRO, Palo.ESPADAS),
                _carta(Figura.AS, Palo.BASTOS),
            ],
            "j3": [
                _carta(Figura.SOTA, Palo.OROS),
                _carta(Figura.SEIS, Palo.COPAS),
                _carta(Figura.CINCO, Palo.BASTOS),
                _carta(Figura.CUATRO, Palo.OROS),
            ],
            "j4": [
                _carta(Figura.SIETE, Palo.OROS),
                _carta(Figura.CINCO, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.COPAS),
                _carta(Figura.AS, Palo.ESPADAS),
            ],
        }
    )

    assert observacion is not None
    assert observacion.jugador_id == "j2"
    assert "quiero" in observacion.legal_action_labels
    assert "no_quiero" in observacion.legal_action_labels
    assert "ordago" in observacion.legal_action_labels
    assert "envidar:1" in observacion.legal_action_labels
    assert "envidar:40" in observacion.legal_action_labels
    assert observacion.envite_pendiente == "envite:grande:1"
    assert observacion.detalle_envite_pendiente is not None
    assert observacion.detalle_envite_pendiente.tipo_apuesta == "envite"
    assert observacion.detalle_envite_pendiente.lance == "grande"
    assert observacion.detalle_envite_pendiente.cantidad_actual == 1
    assert observacion.detalle_envite_pendiente.cantidad_previa == 0
    assert observacion.detalle_envite_pendiente.es_reenvite is False
    assert observacion.detalle_envite_pendiente.valor_no_quiero == 1
    assert observacion.detalle_envite_pendiente.jugador_apostador == "j1"
    assert observacion.detalle_envite_pendiente.equipo_apostador == "equipo_1"
    assert observacion.detalle_envite_pendiente.soy_equipo_apostador is False
    assert observacion.detalle_envite_pendiente.me_toca_responder is True


def test_observacion_envite_expone_detalle_de_resubida() -> None:
    motor = MotorMus()
    manos = {
        "j1": [
            _carta(Figura.REY, Palo.OROS),
            _carta(Figura.SIETE, Palo.COPAS),
            _carta(Figura.SEIS, Palo.ESPADAS),
            _carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j2": [
            _carta(Figura.CABALLO, Palo.OROS),
            _carta(Figura.CINCO, Palo.COPAS),
            _carta(Figura.CUATRO, Palo.ESPADAS),
            _carta(Figura.AS, Palo.BASTOS),
        ],
        "j3": [
            _carta(Figura.SOTA, Palo.OROS),
            _carta(Figura.SEIS, Palo.COPAS),
            _carta(Figura.CINCO, Palo.BASTOS),
            _carta(Figura.CUATRO, Palo.OROS),
        ],
        "j4": [
            _carta(Figura.SIETE, Palo.OROS),
            _carta(Figura.CINCO, Palo.ESPADAS),
            _carta(Figura.CUATRO, Palo.COPAS),
            _carta(Figura.AS, Palo.ESPADAS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(5), "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(7), "j2")

    observacion = construir_observacion_agente(estado, "j3", motor.acciones_legales(estado))
    detalle = observacion.detalle_envite_pendiente

    assert observacion.envite_pendiente == "envite:grande:12"
    assert detalle is not None
    assert 0.0 <= observacion.fuerza_grande <= 1.0
    assert 0.0 <= observacion.fuerza_chica <= 1.0
    assert detalle.tipo_apuesta == "envite"
    assert detalle.lance == "grande"
    assert detalle.cantidad_actual == 12
    assert detalle.cantidad_previa == 5
    assert detalle.es_reenvite is True
    assert detalle.valor_no_quiero == 5
    assert detalle.jugador_apostador == "j2"
    assert detalle.equipo_apostador == "equipo_2"
    assert detalle.soy_equipo_apostador is False
    assert detalle.me_toca_responder is True
    assert observacion.to_agent_dict()["detalle_envite_pendiente"] == {
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
    }
    payload = observacion.to_agent_dict()
    assert 0.0 <= float(payload["fuerza_grande"]) <= 1.0
    assert 0.0 <= float(payload["fuerza_chica"]) <= 1.0


def test_mus_env_filtra_envites_de_apertura_desde_dos() -> None:
    env = MusEnv(
        uncontrolled_agents={
            "j2": PreferActionAgent(agent_id="j2", preferencias=(AccionMus.PASAR,)),
            "j4": PreferActionAgent(agent_id="j4", preferencias=(AccionMus.PASAR,)),
        }
    )

    observacion, _ = env.reset(
        manos_iniciales={
            "j1": [
                _carta(Figura.REY, Palo.OROS),
                _carta(Figura.SIETE, Palo.COPAS),
                _carta(Figura.SEIS, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.BASTOS),
            ],
            "j2": [
                _carta(Figura.CABALLO, Palo.OROS),
                _carta(Figura.CINCO, Palo.COPAS),
                _carta(Figura.CUATRO, Palo.ESPADAS),
                _carta(Figura.AS, Palo.BASTOS),
            ],
            "j3": [
                _carta(Figura.SOTA, Palo.OROS),
                _carta(Figura.SEIS, Palo.COPAS),
                _carta(Figura.CINCO, Palo.BASTOS),
                _carta(Figura.CUATRO, Palo.OROS),
            ],
            "j4": [
                _carta(Figura.SIETE, Palo.OROS),
                _carta(Figura.CINCO, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.COPAS),
                _carta(Figura.AS, Palo.ESPADAS),
            ],
        }
    )

    assert observacion is not None
    observacion, _, terminado, truncado, _ = env.step(env.encode_action(AccionMus.CORTAR_MUS))
    assert observacion is not None
    assert not terminado
    assert not truncado
    assert observacion.fase == "grande"
    assert "envidar:1" in observacion.legal_action_labels
    assert "envidar:2" in observacion.legal_action_labels


def test_mus_env_recompensa_terminal_desde_el_equipo_controlado() -> None:
    env = MusEnv(
        uncontrolled_agents={
            "j2": PreferActionAgent(
                agent_id="j2",
                preferencias=(AccionMus.PASAR, AccionMus.QUIERO),
            ),
            "j4": PreferActionAgent(
                agent_id="j4",
                preferencias=(AccionMus.PASAR, AccionMus.QUIERO),
            ),
        }
    )

    observacion, _ = env.reset(
        manos_iniciales={
            "j1": [
                _carta(Figura.REY, Palo.OROS),
                _carta(Figura.SEIS, Palo.COPAS),
                _carta(Figura.CINCO, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.BASTOS),
            ],
            "j2": [
                _carta(Figura.CABALLO, Palo.OROS),
                _carta(Figura.SIETE, Palo.COPAS),
                _carta(Figura.SEIS, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.COPAS),
            ],
            "j3": [
                _carta(Figura.SOTA, Palo.OROS),
                _carta(Figura.AS, Palo.COPAS),
                _carta(Figura.CUATRO, Palo.ESPADAS),
                _carta(Figura.CINCO, Palo.BASTOS),
            ],
            "j4": [
                _carta(Figura.CABALLO, Palo.BASTOS),
                _carta(Figura.AS, Palo.OROS),
                _carta(Figura.CINCO, Palo.COPAS),
                _carta(Figura.SEIS, Palo.BASTOS),
            ],
        }
    )

    assert observacion is not None
    assert observacion.jugador_id == "j1"

    secuencia = [
        env.encode_action(AccionMus.CORTAR_MUS),
        env.encode_action(AccionMus.PASAR),
        env.encode_action(AccionMus.PASAR),
        env.encode_action(AccionMus.PASAR),
        env.encode_action(AccionMus.PASAR),
        env.encode_action(AccionMus.PASAR),
        env.encode_action(AccionMus.PASAR),
    ]

    recompensa_final = 0.0
    terminado = False
    info_final: dict[str, object] = {}
    for action_id in secuencia:
        observacion, recompensa, terminado, truncado, info = env.step(action_id)
        assert not truncado
        recompensa_final = recompensa
        info_final = info
        if terminado:
            break

    assert terminado
    assert observacion is None
    assert recompensa_final == pytest.approx(1.1)
    assert info_final["reward_breakdown"] == {
        "total": pytest.approx(1.1),
        "resultado_mano": pytest.approx(1.0),
        "diferencial_piedras": pytest.approx(0.1),
        "cierre_juego": pytest.approx(0.0),
    }
    estado_final = info_final["state"]
    assert estado_final is not None
    assert estado_final.marcador == {"equipo_1": 2, "equipo_2": 1}


def _carta(figura: Figura, palo: Palo) -> Carta:
    return Carta(figura=figura, palo=palo)
