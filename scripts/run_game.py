"""Script inicial para lanzar una partida manual."""

from __future__ import annotations

from musbot.core.motor import MotorMus


def main() -> None:
    motor = MotorMus()
    estado = motor.iniciar_partida()
    acciones = ", ".join(str(accion) for accion in motor.acciones_legales(estado))
    print(f"Partida: {estado.partida_id}")
    print(f"Fase actual: {estado.fase}")
    print(f"Jugador activo: {estado.jugador_activo}")
    print(f"Acciones legales: {acciones}")


if __name__ == "__main__":
    main()
