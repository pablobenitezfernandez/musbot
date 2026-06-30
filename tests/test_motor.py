import json

from musbot.analysis.decision_logger import DecisionLogger, DecisionRecord
from musbot.core.cartas import Carta, Figura, Palo
from musbot.core.estado_partida import FaseMano, LanceMus
from musbot.core.motor import MotorMus
from musbot.env.acciones import AccionLegal, AccionMus
from tests._tmp_utils import workspace_tmp_dir


def test_motor_inicia_partida_en_decision_mus() -> None:
    motor = MotorMus()

    estado = motor.iniciar_partida(
        partida_id="partida-demo",
        marcador_inicial={"equipo_1": 0, "equipo_2": 0},
    )

    assert estado.partida_id == "partida-demo"
    assert estado.fase == FaseMano.DECISION_MUS
    assert estado.jugador_activo == "j1"
    assert all(len(jugador.mano) == 4 for jugador in estado.jugadores.values())
    assert estado.marcador == {"equipo_1": 0, "equipo_2": 0}


def test_decision_logger_guarda_jsonl() -> None:
    with workspace_tmp_dir() as tmp_path:
        output_path = tmp_path / "decisiones.jsonl"
        logger = DecisionLogger(output_path)
        record = DecisionRecord(
            partida_id="p1",
            mano_id=1,
            jugador_id="j1",
            fase="mus",
            cartas_propias=["as_de_oros", "rey_de_bastos"],
            marcador={"equipo_a": 10, "equipo_b": 8},
            historial_publico=["mus"],
            acciones_legales=["pedir_mus", "cortar_mus"],
            accion_elegida="pedir_mus",
            probabilidades_accion={"pedir_mus": 0.6, "cortar_mus": 0.4},
            valor_estimado=0.25,
            recompensa_posterior=None,
            comentario="baseline aleatorio",
        )

        logger.registrar(record)

        contenido = output_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(contenido) == 1
        assert json.loads(contenido[0])["accion_elegida"] == "pedir_mus"


def test_motor_resuelve_mano_normal_en_paso() -> None:
    motor = MotorMus()
    manos = {
        "j1": [
            Carta(Figura.AS, Palo.OROS),
            Carta(Figura.DOS, Palo.COPAS),
            Carta(Figura.CUATRO, Palo.ESPADAS),
            Carta(Figura.CINCO, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.SIETE, Palo.OROS),
            Carta(Figura.SEIS, Palo.COPAS),
            Carta(Figura.CINCO, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j3": [
            Carta(Figura.REY, Palo.ESPADAS),
            Carta(Figura.CABALLO, Palo.BASTOS),
            Carta(Figura.SIETE, Palo.COPAS),
            Carta(Figura.CUATRO, Palo.OROS),
        ],
        "j4": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.SIETE, Palo.BASTOS),
            Carta(Figura.SEIS, Palo.ESPADAS),
            Carta(Figura.CINCO, Palo.COPAS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    assert estado.fase == FaseMano.FINALIZADA
    assert estado.marcador["equipo_1"] == 6
    assert estado.marcador["equipo_2"] == 0
    assert estado.resultados_lances[LanceMus.GRANDE].ganador_equipo == "equipo_1"
    assert estado.resultados_lances[LanceMus.CHICA].ganador_equipo == "equipo_1"
    assert estado.resultados_lances[LanceMus.PARES].ganador_equipo == "equipo_1"
    assert estado.resultados_lances[LanceMus.JUEGO].ganador_equipo == "equipo_1"


def test_motor_cierra_el_juego_antes_de_contar_un_ordago_posterior() -> None:
    motor = MotorMus()
    manos = {
        "j1": [
            Carta(Figura.REY, Palo.OROS),
            Carta(Figura.CABALLO, Palo.COPAS),
            Carta(Figura.SIETE, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.AS, Palo.OROS),
            Carta(Figura.DOS, Palo.COPAS),
            Carta(Figura.CUATRO, Palo.ESPADAS),
            Carta(Figura.CINCO, Palo.BASTOS),
        ],
        "j3": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.SIETE, Palo.COPAS),
            Carta(Figura.SEIS, Palo.ESPADAS),
            Carta(Figura.CINCO, Palo.OROS),
        ],
        "j4": [
            Carta(Figura.AS, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.OROS),
            Carta(Figura.CINCO, Palo.COPAS),
            Carta(Figura.SEIS, Palo.BASTOS),
        ],
    }

    estado = motor.iniciar_partida(
        manos_iniciales=manos,
        marcador_inicial={"equipo_1": 39, "equipo_2": 25},
    )
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(2), "j1")
    estado = motor.aplicar_accion(estado, AccionMus.QUIERO, "j2")
    estado = motor.aplicar_accion(estado, AccionMus.PASAR, "j1")
    estado = motor.aplicar_accion(estado, AccionMus.ORDAGO, "j2")
    estado = motor.aplicar_accion(estado, AccionMus.QUIERO, "j3")

    assert estado.fase == FaseMano.FINALIZADA
    assert estado.ganador_juego_actual == "equipo_1"
    assert estado.marcador["equipo_1"] == 41
    assert estado.marcador["equipo_2"] == 25
    assert estado.resultados_lances[LanceMus.CHICA].ordago_aceptado is True


def test_motor_permite_no_quiero_y_anota_negada_en_grande() -> None:
    motor = MotorMus()
    manos = {
        "j1": [
            Carta(Figura.REY, Palo.OROS),
            Carta(Figura.SIETE, Palo.COPAS),
            Carta(Figura.SEIS, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.CABALLO, Palo.OROS),
            Carta(Figura.CINCO, Palo.COPAS),
            Carta(Figura.CUATRO, Palo.ESPADAS),
            Carta(Figura.AS, Palo.BASTOS),
        ],
        "j3": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.SEIS, Palo.COPAS),
            Carta(Figura.CINCO, Palo.BASTOS),
            Carta(Figura.CUATRO, Palo.OROS),
        ],
        "j4": [
            Carta(Figura.SIETE, Palo.OROS),
            Carta(Figura.CINCO, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.COPAS),
            Carta(Figura.AS, Palo.ESPADAS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(2), "j1")

    assert {accion.tipo for accion in motor.acciones_legales(estado)} == {
        AccionMus.QUIERO,
        AccionMus.NO_QUIERO,
        AccionMus.ENVIDAR,
        AccionMus.ORDAGO,
    }

    estado = motor.aplicar_accion(estado, AccionMus.NO_QUIERO, "j2")

    assert estado.fase == FaseMano.CHICA
    assert estado.resultados_lances[LanceMus.GRANDE].ganador_equipo == "equipo_1"
    assert estado.resultados_lances[LanceMus.GRANDE].puntos_base_ganador == 0
    assert estado.resultados_lances[LanceMus.GRANDE].puntos_apuesta == 1
    assert estado.resultados_lances[LanceMus.GRANDE].equipo_apuesta == "equipo_1"
    assert estado.resultados_lances[LanceMus.GRANDE].apuesta_rechazada is True


def test_motor_rechazo_en_pares_suma_negada_mas_valor_propio() -> None:
    motor = MotorMus()
    manos = {
        "j1": [
            Carta(Figura.REY, Palo.OROS),
            Carta(Figura.TRES, Palo.COPAS),
            Carta(Figura.SOTA, Palo.ESPADAS),
            Carta(Figura.AS, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.CABALLO, Palo.OROS),
            Carta(Figura.CABALLO, Palo.COPAS),
            Carta(Figura.SIETE, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.OROS),
        ],
        "j3": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.SEIS, Palo.COPAS),
            Carta(Figura.CINCO, Palo.BASTOS),
            Carta(Figura.AS, Palo.ESPADAS),
        ],
        "j4": [
            Carta(Figura.AS, Palo.OROS),
            Carta(Figura.DOS, Palo.COPAS),
            Carta(Figura.SIETE, Palo.BASTOS),
            Carta(Figura.SEIS, Palo.OROS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    assert estado.fase == FaseMano.PARES
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(2), "j1")
    estado = motor.aplicar_accion(estado, AccionMus.NO_QUIERO, "j2")

    resultado_pares = estado.resultados_lances[LanceMus.PARES]
    assert resultado_pares.ganador_jugador == "j1"
    assert resultado_pares.puntos_base_ganador == 1
    assert resultado_pares.puntos_apuesta == 1
    assert resultado_pares.equipo_apuesta == "equipo_1"
    assert resultado_pares.apuesta_rechazada is True
    assert estado.fase == FaseMano.JUEGO


def test_motor_no_quiero_a_reenvite_devuelve_la_apuesta_anterior() -> None:
    motor = MotorMus()
    manos = {
        "j1": [
            Carta(Figura.REY, Palo.OROS),
            Carta(Figura.SIETE, Palo.COPAS),
            Carta(Figura.SEIS, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.CABALLO, Palo.OROS),
            Carta(Figura.CINCO, Palo.COPAS),
            Carta(Figura.CUATRO, Palo.ESPADAS),
            Carta(Figura.AS, Palo.BASTOS),
        ],
        "j3": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.SEIS, Palo.COPAS),
            Carta(Figura.CINCO, Palo.BASTOS),
            Carta(Figura.CUATRO, Palo.OROS),
        ],
        "j4": [
            Carta(Figura.SIETE, Palo.OROS),
            Carta(Figura.CINCO, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.COPAS),
            Carta(Figura.AS, Palo.ESPADAS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(5), "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(7), "j2")
    estado = motor.aplicar_accion(estado, AccionMus.NO_QUIERO, "j3")

    resultado = estado.resultados_lances[LanceMus.GRANDE]
    assert resultado.apuesta_rechazada is True
    assert resultado.puntos_apuesta == 5
    assert resultado.equipo_apuesta == "equipo_2"
    assert resultado.puntos_base_ganador == 0


def test_motor_ordago_aceptado_en_pares_conserva_puntos_propios() -> None:
    """Ordago aceptado en pares: puntos_base_ganador refleja el valor real de pares."""
    motor = MotorMus()
    # j1 (equipo_1): pares de REY (valor 7) → pares=1 punto, gana el lance
    # j2 (equipo_2): pares de CABALLO (valor 6) → pares=1 punto, pierde ante j1
    # j3, j4: sin pares
    manos = {
        "j1": [
            Carta(Figura.REY, Palo.OROS),
            Carta(Figura.REY, Palo.COPAS),
            Carta(Figura.SIETE, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.CABALLO, Palo.OROS),
            Carta(Figura.CABALLO, Palo.COPAS),
            Carta(Figura.CINCO, Palo.ESPADAS),
            Carta(Figura.SEIS, Palo.BASTOS),
        ],
        "j3": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.SEIS, Palo.COPAS),
            Carta(Figura.CINCO, Palo.BASTOS),
            Carta(Figura.SIETE, Palo.OROS),
        ],
        "j4": [
            Carta(Figura.CUATRO, Palo.OROS),
            Carta(Figura.CINCO, Palo.COPAS),
            Carta(Figura.SEIS, Palo.ESPADAS),
            Carta(Figura.AS, Palo.ESPADAS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    assert estado.fase == FaseMano.PARES
    estado = motor.aplicar_accion(estado, AccionMus.ORDAGO, "j1")
    estado = motor.aplicar_accion(estado, AccionMus.QUIERO, "j2")

    resultado = estado.resultados_lances[LanceMus.PARES]
    assert resultado.ordago_aceptado is True
    assert resultado.ganador_equipo == "equipo_1"
    assert resultado.puntos_base_ganador == 1


def test_motor_ordago_aceptado_en_juego_31_conserva_puntos_propios() -> None:
    """Ordago aceptado en juego 31: puntos_base_ganador == 3."""
    motor = MotorMus()
    # j1 (equipo_1): AS+REY+REY+REY = 1+10+10+10 = 31 → juego 31 (3 pts), medias de REY → pares auto
    # j2 (equipo_2): SOTA+CABALLO+SIETE+CUATRO = 10+10+7+4 = 31 → juego 31, j1 gana por turno
    # j3, j4: sin juego
    manos = {
        "j1": [
            Carta(Figura.AS, Palo.OROS),
            Carta(Figura.REY, Palo.COPAS),
            Carta(Figura.REY, Palo.ESPADAS),
            Carta(Figura.REY, Palo.BASTOS),
        ],
        "j2": [
            Carta(Figura.SOTA, Palo.OROS),
            Carta(Figura.CABALLO, Palo.COPAS),
            Carta(Figura.SIETE, Palo.ESPADAS),
            Carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j3": [
            Carta(Figura.CUATRO, Palo.OROS),
            Carta(Figura.CINCO, Palo.COPAS),
            Carta(Figura.SEIS, Palo.ESPADAS),
            Carta(Figura.DOS, Palo.BASTOS),
        ],
        "j4": [
            Carta(Figura.CINCO, Palo.OROS),
            Carta(Figura.SEIS, Palo.COPAS),
            Carta(Figura.CUATRO, Palo.COPAS),
            Carta(Figura.SIETE, Palo.OROS),
        ],
    }

    estado = motor.iniciar_partida(manos_iniciales=manos)
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    # Pass grande y chica; pares auto-resuelve (solo j1/equipo_1 tiene medias de REY)
    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    for jugador_id in ("j1", "j2", "j3", "j4"):
        estado = motor.aplicar_accion(estado, AccionMus.PASAR, jugador_id)

    assert estado.fase == FaseMano.JUEGO
    estado = motor.aplicar_accion(estado, AccionMus.ORDAGO, "j1")
    estado = motor.aplicar_accion(estado, AccionMus.QUIERO, "j2")

    resultado = estado.resultados_lances[LanceMus.JUEGO]
    assert resultado.ordago_aceptado is True
    assert resultado.ganador_equipo == "equipo_1"
    assert resultado.puntos_base_ganador == 3
