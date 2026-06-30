from __future__ import annotations

from musbot.core.cartas import Carta, Figura, Palo
from musbot.core.motor import MotorMus
from musbot.env.acciones import AccionLegal, AccionMus
from musbot.env.observaciones import construir_observacion_agente


def _carta(figura: Figura, palo: Palo) -> Carta:
    return Carta(figura=figura, palo=palo)


def _manos_base() -> dict[str, list[Carta]]:
    return {
        "j1": [
            _carta(Figura.REY, Palo.OROS),
            _carta(Figura.REY, Palo.COPAS),
            _carta(Figura.SIETE, Palo.ESPADAS),
            _carta(Figura.CUATRO, Palo.BASTOS),
        ],
        "j2": [
            _carta(Figura.CABALLO, Palo.OROS),
            _carta(Figura.CABALLO, Palo.COPAS),
            _carta(Figura.CINCO, Palo.ESPADAS),
            _carta(Figura.SEIS, Palo.BASTOS),
        ],
        "j3": [
            _carta(Figura.SOTA, Palo.OROS),
            _carta(Figura.SEIS, Palo.COPAS),
            _carta(Figura.CINCO, Palo.BASTOS),
            _carta(Figura.SIETE, Palo.OROS),
        ],
        "j4": [
            _carta(Figura.CUATRO, Palo.OROS),
            _carta(Figura.CINCO, Palo.COPAS),
            _carta(Figura.SEIS, Palo.ESPADAS),
            _carta(Figura.AS, Palo.ESPADAS),
        ],
    }


def test_compact_key_devuelve_ocho_dimensiones() -> None:
    motor = MotorMus()
    estado = motor.iniciar_partida(manos_iniciales=_manos_base())
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    observacion = construir_observacion_agente(estado, "j1", motor.acciones_legales(estado))
    clave = observacion.compact_key()

    assert isinstance(clave, tuple)
    assert len(clave) == 8
    assert all(isinstance(x, int) for x in clave)


def test_compact_key_es_mano_y_fase_grande() -> None:
    motor = MotorMus()
    estado = motor.iniciar_partida(manos_iniciales=_manos_base())
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    observacion = construir_observacion_agente(estado, "j1", motor.acciones_legales(estado))
    fase_bucket, es_mano, *_ = observacion.compact_key()

    assert fase_bucket == 1  # grande
    assert es_mano == 1  # j1 es mano


def test_compact_key_marca_envite_pendiente_y_respondedor() -> None:
    motor = MotorMus()
    estado = motor.iniciar_partida(manos_iniciales=_manos_base())
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")
    estado = motor.aplicar_accion(estado, AccionLegal.envidar(5), "j1")

    # j2 debe responder al envite de j1.
    observacion = construir_observacion_agente(estado, "j2", motor.acciones_legales(estado))
    clave = observacion.compact_key()
    envite_bucket = clave[6]
    respondedor = clave[7]

    assert envite_bucket == 1
    assert respondedor == 1


def test_compact_key_sin_envite_no_marca_respondedor() -> None:
    motor = MotorMus()
    estado = motor.iniciar_partida(manos_iniciales=_manos_base())
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    observacion = construir_observacion_agente(estado, "j1", motor.acciones_legales(estado))
    clave = observacion.compact_key()

    assert clave[6] == 0  # sin envite
    assert clave[7] == 0  # nadie responde


def test_compact_key_fuerza_bucket_segun_lance_actual() -> None:
    motor = MotorMus()
    estado = motor.iniciar_partida(manos_iniciales=_manos_base())
    estado = motor.aplicar_accion(estado, AccionMus.CORTAR_MUS, "j1")

    # j1 (dos reyes) tiene grande muy fuerte; j4 (cartas bajas) muy débil.
    obs_fuerte = construir_observacion_agente(estado, "j1", motor.acciones_legales(estado))
    fuerza_fuerte = obs_fuerte.compact_key()[2]

    # j4 no es el jugador activo, pero podemos construir su observación igualmente.
    obs_debil = construir_observacion_agente(estado, "j4", ())
    fuerza_debil = obs_debil.compact_key()[2]

    assert fuerza_fuerte > fuerza_debil
