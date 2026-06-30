"""Motor de juego de alto nivel, separado del entorno RL."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import combinations
from random import Random
from uuid import uuid4

from musbot.core.baraja import Baraja
from musbot.core.cartas import Carta
from musbot.core.estado_partida import (
    EnvitePendiente,
    EstadoLance,
    EstadoPartida,
    FaseMano,
    LanceMus,
    ResultadoLance,
)
from musbot.core.evaluacion import (
    comparacion_chica,
    comparacion_grande,
    comparacion_juego,
    comparacion_pares,
    comparacion_punto,
    evaluar_chica,
    evaluar_grande,
    evaluar_juego,
    evaluar_pares,
    evaluar_punto,
    mejor_jugador,
)
from musbot.core.jugador import Jugador
from musbot.core.puntuacion import aplicar_anotaciones, resolver_puntuacion_mano
from musbot.core.reglas import RutasReglas
from musbot.env.acciones import AccionLegal, AccionMus


@dataclass(slots=True)
class MotorMus:
    """Motor base de mus para jugadas normales y legales.

    Esta version evita la capa de arbitraje humano. El motor calcula
    automaticamente pares, juego, punto, ganadores y tanteos ordenados.
    """

    rutas_reglas: RutasReglas = field(default_factory=RutasReglas)
    piedras_objetivo: int = 40
    juegos_objetivo: int = 4

    def iniciar_partida(
        self,
        partida_id: str | None = None,
        marcador_inicial: Mapping[str, int] | None = None,
        juegos_iniciales: Mapping[str, int] | None = None,
        orden_turnos: Sequence[str] | None = None,
        manos_iniciales: Mapping[str, Sequence[Carta]] | None = None,
        seed: int | None = None,
    ) -> EstadoPartida:
        """Crea una partida lista para empezar a decidir el mus."""

        orden = tuple(orden_turnos or ("j1", "j2", "j3", "j4"))
        if len(orden) != 4:
            raise ValueError("El motor base requiere exactamente 4 jugadores.")

        equipos = self._crear_equipos(orden)
        jugadores = self._crear_jugadores(orden, equipos)
        baraja = Baraja.espanola_40()
        mazo_restante = list(baraja.cartas)
        rng = Random(seed)
        rng.shuffle(mazo_restante)

        if manos_iniciales is not None:
            self._asignar_manos_fijas(jugadores, mazo_restante, manos_iniciales)
        else:
            self._repartir_manos(jugadores, mazo_restante)

        estado = EstadoPartida(
            partida_id=partida_id or str(uuid4()),
            mano_id=1,
            fase=FaseMano.PREPARACION,
            marcador={
                equipo_id: int(valor) for equipo_id, valor in (marcador_inicial or {}).items()
            },
            juegos_ganados={
                equipo_id: int(valor) for equipo_id, valor in (juegos_iniciales or {}).items()
            },
            jugadores=jugadores,
            equipos_por_jugador=equipos,
            orden_turnos=orden,
            indice_mano=0,
            orden_descarte=tuple(reversed(orden)),
            mazo_restante=mazo_restante,
            rng=rng,
        )

        for equipo_id in set(equipos.values()):
            estado.marcador.setdefault(equipo_id, 0)
            estado.juegos_ganados.setdefault(equipo_id, 0)

        self._registrar_historial(estado, "partida_iniciada")
        self._avanzar_flujo_automatico(estado)
        return estado

    def acciones_legales(self, estado: EstadoPartida) -> list[AccionLegal]:
        """Devuelve las acciones legales para el jugador activo."""

        if estado.jugador_activo is None:
            return []

        if estado.fase is FaseMano.DECISION_MUS:
            return [
                AccionLegal.simple(AccionMus.PEDIR_MUS),
                AccionLegal.simple(AccionMus.CORTAR_MUS),
            ]

        if estado.fase is FaseMano.DESCARTE:
            return self._acciones_descarte(estado.jugador_activo, estado)

        if estado.fase in {
            FaseMano.GRANDE,
            FaseMano.CHICA,
            FaseMano.PARES,
            FaseMano.JUEGO,
            FaseMano.PUNTO,
        }:
            lance = estado.lance_en_curso
            if lance is None:
                return []
            if lance.envite_pendiente is None:
                return [
                    AccionLegal.simple(AccionMus.PASAR),
                    AccionLegal.envidar(cantidad_minima=1),
                    AccionLegal.simple(AccionMus.ORDAGO),
                ]
            if lance.envite_pendiente.es_ordago:
                return [
                    AccionLegal.simple(AccionMus.QUIERO),
                    AccionLegal.simple(AccionMus.NO_QUIERO),
                ]
            return [
                AccionLegal.simple(AccionMus.QUIERO),
                AccionLegal.simple(AccionMus.NO_QUIERO),
                AccionLegal.envidar(cantidad_minima=1),
                AccionLegal.simple(AccionMus.ORDAGO),
            ]

        return []

    def aplicar_accion(
        self,
        estado: EstadoPartida,
        accion: AccionLegal | AccionMus,
        jugador_id: str,
    ) -> EstadoPartida:
        """Aplica una accion del jugador activo y devuelve un nuevo estado."""

        accion_materializada = self._materializar_accion(accion)
        nuevo_estado = deepcopy(estado)

        if nuevo_estado.jugador_activo != jugador_id:
            raise ValueError("Solo el jugador activo puede actuar.")

        legales = self.acciones_legales(nuevo_estado)
        if not any(legal.coincide_con(accion_materializada) for legal in legales):
            raise ValueError(f"Accion ilegal para el estado actual: {accion_materializada}")

        if nuevo_estado.fase is FaseMano.DECISION_MUS:
            self._aplicar_decision_mus(nuevo_estado, jugador_id, accion_materializada)
        elif nuevo_estado.fase is FaseMano.DESCARTE:
            self._aplicar_descarte(nuevo_estado, jugador_id, accion_materializada)
        elif nuevo_estado.fase in {
            FaseMano.GRANDE,
            FaseMano.CHICA,
            FaseMano.PARES,
            FaseMano.JUEGO,
            FaseMano.PUNTO,
        }:
            self._aplicar_accion_lance(nuevo_estado, jugador_id, accion_materializada)
        else:
            raise ValueError(f"La fase {nuevo_estado.fase} no admite acciones manuales.")

        self._avanzar_flujo_automatico(nuevo_estado)
        return nuevo_estado

    def siguiente_mano(
        self,
        estado_previo: EstadoPartida,
        seed: int | None = None,
    ) -> EstadoPartida:
        """Inicia la siguiente mano preservando marcador y juegos ganados.

        El marcador (piedras) se reinicia si el juego anterior se cerro; de lo
        contrario, se transfiere intacto. El indice_mano rota un puesto en el
        sentido de las agujas del reloj y el orden_descarte se recalcula.
        """

        if estado_previo.fase is not FaseMano.FINALIZADA:
            raise ValueError("Solo se puede avanzar si la mano actual ha finalizado.")

        if estado_previo.ganador_partida is not None:
            raise ValueError("La partida ya tiene un ganador; no se puede iniciar otra mano.")

        orden = estado_previo.orden_turnos
        nuevo_indice_mano = (estado_previo.indice_mano + 1) % len(orden)

        baraja = Baraja.espanola_40()
        mazo_restante = list(baraja.cartas)
        rng = Random(seed)
        rng.shuffle(mazo_restante)

        jugadores = self._crear_jugadores(orden, estado_previo.equipos_por_jugador)
        self._repartir_manos(jugadores, mazo_restante)

        # postre first, mano last — generalised for any indice_mano
        n = len(orden)
        orden_descarte = tuple(orden[(nuevo_indice_mano + n - 1 - i) % n] for i in range(n))

        # Reset piedras only when a juego was closed in the previous hand
        if estado_previo.ganador_juego_actual is not None:
            marcador_nuevo: dict[str, int] = {eq: 0 for eq in estado_previo.marcador}
        else:
            marcador_nuevo = dict(estado_previo.marcador)

        estado = EstadoPartida(
            partida_id=estado_previo.partida_id,
            mano_id=estado_previo.mano_id + 1,
            fase=FaseMano.PREPARACION,
            marcador=marcador_nuevo,
            juegos_ganados=dict(estado_previo.juegos_ganados),
            jugadores=jugadores,
            equipos_por_jugador=dict(estado_previo.equipos_por_jugador),
            orden_turnos=orden,
            indice_mano=nuevo_indice_mano,
            orden_descarte=orden_descarte,
            mazo_restante=mazo_restante,
            rng=rng,
        )

        self._registrar_historial(estado, "mano_iniciada")
        self._avanzar_flujo_automatico(estado)
        return estado

    def _crear_equipos(self, orden_turnos: Sequence[str]) -> dict[str, str]:
        return {
            orden_turnos[0]: "equipo_1",
            orden_turnos[2]: "equipo_1",
            orden_turnos[1]: "equipo_2",
            orden_turnos[3]: "equipo_2",
        }

    def _crear_jugadores(
        self,
        orden_turnos: Sequence[str],
        equipos_por_jugador: Mapping[str, str],
    ) -> dict[str, Jugador]:
        return {
            jugador_id: Jugador(
                jugador_id=jugador_id,
                nombre=jugador_id,
                equipo_id=equipos_por_jugador[jugador_id],
            )
            for jugador_id in orden_turnos
        }

    def _asignar_manos_fijas(
        self,
        jugadores: dict[str, Jugador],
        mazo_restante: list[Carta],
        manos_iniciales: Mapping[str, Sequence[Carta]],
    ) -> None:
        if set(manos_iniciales) != set(jugadores):
            raise ValueError("Las manos iniciales deben cubrir exactamente a los 4 jugadores.")

        usadas = {carta.codigo for mano in manos_iniciales.values() for carta in mano}
        if len(usadas) != 16:
            raise ValueError("Las manos iniciales deben contener 16 cartas distintas.")

        for jugador_id, mano in manos_iniciales.items():
            if len(mano) != 4:
                raise ValueError("Cada jugador debe empezar con 4 cartas.")
            jugadores[jugador_id].mano = list(mano)

        mazo_restante[:] = [carta for carta in mazo_restante if carta.codigo not in usadas]

    def _repartir_manos(
        self,
        jugadores: dict[str, Jugador],
        mazo_restante: list[Carta],
    ) -> None:
        for jugador in jugadores.values():
            jugador.mano = []

        for _ in range(4):
            for jugador_id in jugadores:
                jugadores[jugador_id].mano.append(mazo_restante.pop(0))

    def _avanzar_flujo_automatico(self, estado: EstadoPartida) -> None:
        while True:
            if estado.fase is FaseMano.PREPARACION:
                estado.fase = FaseMano.DECISION_MUS
                estado.jugador_activo = estado.orden_turnos[estado.indice_mano]
                return

            if (
                estado.fase
                in {
                    FaseMano.GRANDE,
                    FaseMano.CHICA,
                    FaseMano.PARES,
                    FaseMano.JUEGO,
                    FaseMano.PUNTO,
                }
                and estado.lance_en_curso is None
            ):
                if self._preparar_lance(estado):
                    continue
                return

            if estado.fase is FaseMano.TANTEO:
                self._resolver_tanteo(estado)
                estado.fase = FaseMano.FINALIZADA
                estado.jugador_activo = None
                return

            return

    def _preparar_lance(self, estado: EstadoPartida) -> bool:
        if estado.fase is FaseMano.GRANDE:
            estado.lance_en_curso = EstadoLance(
                lance=LanceMus.GRANDE,
                participantes=estado.orden_turnos,
            )
            estado.jugador_activo = estado.orden_turnos[0]
            return False

        if estado.fase is FaseMano.CHICA:
            estado.lance_en_curso = EstadoLance(
                lance=LanceMus.CHICA,
                participantes=estado.orden_turnos,
            )
            estado.jugador_activo = estado.orden_turnos[0]
            return False

        if estado.fase is FaseMano.PARES:
            jugadores_con_pares = tuple(
                jugador_id
                for jugador_id in estado.orden_turnos
                if evaluar_pares(estado.mano(jugador_id)) is not None
            )
            estado.jugadores_con_pares = jugadores_con_pares
            equipos = {estado.equipos_por_jugador[jugador_id] for jugador_id in jugadores_con_pares}

            if not jugadores_con_pares:
                estado.fase = FaseMano.JUEGO
                return True

            if len(equipos) == 1:
                resultado = self._resolver_lance_automatico(
                    estado,
                    LanceMus.PARES,
                    jugadores_con_pares,
                )
                estado.resultados_lances[LanceMus.PARES] = resultado
                estado.fase = FaseMano.JUEGO
                return True

            estado.lance_en_curso = EstadoLance(
                lance=LanceMus.PARES,
                participantes=jugadores_con_pares,
            )
            estado.jugador_activo = jugadores_con_pares[0]
            return False

        if estado.fase is FaseMano.JUEGO:
            jugadores_con_juego = tuple(
                jugador_id
                for jugador_id in estado.orden_turnos
                if evaluar_juego(estado.mano(jugador_id)) is not None
            )
            estado.jugadores_con_juego = jugadores_con_juego
            equipos = {estado.equipos_por_jugador[jugador_id] for jugador_id in jugadores_con_juego}

            if not jugadores_con_juego:
                estado.fase = FaseMano.PUNTO
                return True

            if len(equipos) == 1:
                resultado = self._resolver_lance_automatico(
                    estado,
                    LanceMus.JUEGO,
                    jugadores_con_juego,
                )
                estado.resultados_lances[LanceMus.JUEGO] = resultado
                estado.fase = FaseMano.TANTEO
                return True

            estado.lance_en_curso = EstadoLance(
                lance=LanceMus.JUEGO,
                participantes=jugadores_con_juego,
            )
            estado.jugador_activo = jugadores_con_juego[0]
            return False

        if estado.fase is FaseMano.PUNTO:
            estado.lance_en_curso = EstadoLance(
                lance=LanceMus.PUNTO,
                participantes=estado.orden_turnos,
            )
            estado.jugador_activo = estado.orden_turnos[0]
            return False

        return False

    def _aplicar_decision_mus(
        self,
        estado: EstadoPartida,
        jugador_id: str,
        accion: AccionLegal,
    ) -> None:
        if accion.tipo is AccionMus.CORTAR_MUS:
            self._registrar_historial(estado, f"{jugador_id}:corta_mus")
            estado.decisiones_mus.clear()
            estado.fase = FaseMano.GRANDE
            estado.jugador_activo = None
            return

        estado.decisiones_mus.append(jugador_id)
        self._registrar_historial(estado, f"{jugador_id}:mus")

        if len(estado.decisiones_mus) == len(estado.orden_turnos):
            estado.decisiones_mus.clear()
            estado.fase = FaseMano.DESCARTE
            estado.jugador_activo = estado.orden_descarte[0]
            return

        siguiente = estado.orden_turnos[len(estado.decisiones_mus)]
        estado.jugador_activo = siguiente

    def _acciones_descarte(self, jugador_id: str, estado: EstadoPartida) -> list[AccionLegal]:
        indices = tuple(range(len(estado.mano(jugador_id))))
        acciones: list[AccionLegal] = []
        for cantidad in range(len(indices) + 1):
            for combinacion in combinations(indices, cantidad):
                acciones.append(AccionLegal.descartar(combinacion))
        return acciones

    def _aplicar_descarte(
        self,
        estado: EstadoPartida,
        jugador_id: str,
        accion: AccionLegal,
    ) -> None:
        mano = list(estado.mano(jugador_id))
        descartadas = [mano[indice] for indice in accion.cartas_descartadas]
        indices_descartados = set(accion.cartas_descartadas)
        restantes = [
            carta for indice, carta in enumerate(mano) if indice not in indices_descartados
        ]
        robadas = self._robar_del_mazo(estado, len(descartadas))

        estado.descarte.extend(descartadas)
        estado.jugadores[jugador_id].mano = restantes + robadas
        self._registrar_historial(
            estado,
            f"{jugador_id}:descarta:{len(descartadas)}",
        )

        indice_actual = estado.orden_descarte.index(jugador_id)
        if indice_actual == len(estado.orden_descarte) - 1:
            estado.fase = FaseMano.DECISION_MUS
            estado.jugador_activo = estado.orden_turnos[0]
            return

        estado.jugador_activo = estado.orden_descarte[indice_actual + 1]

    def _robar_del_mazo(self, estado: EstadoPartida, cantidad: int) -> list[Carta]:
        if cantidad <= 0:
            return []

        if cantidad > len(estado.mazo_restante):
            nueva_baraja = list(estado.descarte)
            estado.descarte.clear()
            estado.rng.shuffle(nueva_baraja)
            estado.mazo_restante.extend(nueva_baraja)

        if cantidad > len(estado.mazo_restante):
            raise ValueError("No hay suficientes cartas para reponer descartes.")

        robadas = estado.mazo_restante[:cantidad]
        del estado.mazo_restante[:cantidad]
        return robadas

    def _aplicar_accion_lance(
        self,
        estado: EstadoPartida,
        jugador_id: str,
        accion: AccionLegal,
    ) -> None:
        lance = estado.lance_en_curso
        if lance is None:
            raise ValueError("No hay lance en curso.")

        if lance.envite_pendiente is None:
            if accion.tipo is AccionMus.PASAR:
                lance.jugadores_que_pasaron.append(jugador_id)
                self._registrar_historial(estado, f"{jugador_id}:paso:{lance.lance.value}")
                if len(lance.jugadores_que_pasaron) == len(lance.participantes):
                    self._cerrar_lance(estado, ordago_aceptado=False)
                    return

                lance.indice_turno += 1
                estado.jugador_activo = lance.participantes[lance.indice_turno]
                return

            if accion.tipo is AccionMus.ENVIDAR:
                if accion.cantidad is None or accion.cantidad <= 0:
                    raise ValueError("El envite requiere una cantidad positiva.")

                equipo = estado.equipos_por_jugador[jugador_id]
                lance.envite_pendiente = EnvitePendiente(
                    lance=lance.lance,
                    jugador_apostador=jugador_id,
                    equipo_apostador=equipo,
                    cantidad=accion.cantidad,
                    cantidad_previa=0,
                )
                estado.jugador_activo = self._primer_oponente_en_lance(estado, lance, jugador_id)
                self._registrar_historial(
                    estado,
                    f"{jugador_id}:envida:{accion.cantidad}:{lance.lance.value}",
                )
                return

            if accion.tipo is AccionMus.ORDAGO:
                equipo = estado.equipos_por_jugador[jugador_id]
                lance.envite_pendiente = EnvitePendiente(
                    lance=lance.lance,
                    jugador_apostador=jugador_id,
                    equipo_apostador=equipo,
                    cantidad_previa=0,
                    es_ordago=True,
                )
                estado.jugador_activo = self._primer_oponente_en_lance(estado, lance, jugador_id)
                self._registrar_historial(estado, f"{jugador_id}:ordago:{lance.lance.value}")
                return

            raise ValueError(f"Accion no soportada en lance abierto: {accion.tipo}")

        pendiente = lance.envite_pendiente
        if accion.tipo is AccionMus.NO_QUIERO:
            if pendiente.es_ordago:
                self._registrar_historial(
                    estado,
                    f"{jugador_id}:no_quiere_ordago:{lance.lance.value}",
                )
            else:
                self._registrar_historial(
                    estado,
                    f"{jugador_id}:no_quiere_envite:{pendiente.cantidad}:{lance.lance.value}",
                )
            self._cerrar_lance(estado, ordago_aceptado=False, apuesta_rechazada=True)
            return

        if accion.tipo is AccionMus.ENVIDAR:
            if pendiente.es_ordago:
                raise ValueError("No se puede resubir un ordago con un envite normal.")
            if accion.cantidad is None or accion.cantidad <= 0:
                raise ValueError("El reenvite requiere una cantidad positiva.")

            total_previo = pendiente.cantidad or 0
            total_nuevo = total_previo + accion.cantidad
            equipo = estado.equipos_por_jugador[jugador_id]
            lance.envite_pendiente = EnvitePendiente(
                lance=lance.lance,
                jugador_apostador=jugador_id,
                equipo_apostador=equipo,
                cantidad=total_nuevo,
                cantidad_previa=total_previo,
            )
            estado.jugador_activo = self._primer_oponente_en_lance(estado, lance, jugador_id)
            self._registrar_historial(
                estado,
                f"{jugador_id}:reenvite:{accion.cantidad}:total:{total_nuevo}:{lance.lance.value}",
            )
            return

        if accion.tipo is AccionMus.ORDAGO:
            total_previo = pendiente.cantidad or 0
            equipo = estado.equipos_por_jugador[jugador_id]
            lance.envite_pendiente = EnvitePendiente(
                lance=lance.lance,
                jugador_apostador=jugador_id,
                equipo_apostador=equipo,
                cantidad_previa=total_previo,
                es_ordago=True,
            )
            estado.jugador_activo = self._primer_oponente_en_lance(estado, lance, jugador_id)
            self._registrar_historial(estado, f"{jugador_id}:ordago:{lance.lance.value}")
            return

        if accion.tipo is not AccionMus.QUIERO:
            raise ValueError("La accion no esta soportada para responder al envite pendiente.")

        if pendiente.es_ordago:
            self._registrar_historial(estado, f"{jugador_id}:quiere_ordago:{lance.lance.value}")
            self._cerrar_lance(estado, ordago_aceptado=True)
            return

        self._registrar_historial(
            estado,
            f"{jugador_id}:quiere_envite:{pendiente.cantidad}:{lance.lance.value}",
        )
        self._cerrar_lance(estado, ordago_aceptado=False)

    def _primer_oponente_en_lance(
        self,
        estado: EstadoPartida,
        lance: EstadoLance,
        jugador_id: str,
    ) -> str:
        equipo = estado.equipos_por_jugador[jugador_id]
        indice_origen = lance.participantes.index(jugador_id)
        total = len(lance.participantes)

        for salto in range(1, total + 1):
            candidato = lance.participantes[(indice_origen + salto) % total]
            if estado.equipos_por_jugador[candidato] != equipo:
                return candidato

        raise ValueError("No se encontro rival para responder al envite.")

    def _cerrar_lance(
        self,
        estado: EstadoPartida,
        ordago_aceptado: bool,
        apuesta_rechazada: bool = False,
    ) -> None:
        if estado.lance_en_curso is None:
            raise ValueError("No hay lance que cerrar.")

        if apuesta_rechazada:
            resultado = self._resolver_apuesta_rechazada(estado)
        else:
            resultado = self._resolver_lance_actual(estado, ordago_aceptado=ordago_aceptado)
        estado.resultados_lances[resultado.lance] = resultado
        lance_cerrado = resultado.lance
        estado.lance_en_curso = None
        estado.jugador_activo = None

        if ordago_aceptado or lance_cerrado in {LanceMus.JUEGO, LanceMus.PUNTO}:
            estado.fase = FaseMano.TANTEO
            return

        estado.fase = {
            LanceMus.GRANDE: FaseMano.CHICA,
            LanceMus.CHICA: FaseMano.PARES,
            LanceMus.PARES: FaseMano.JUEGO,
        }[lance_cerrado]

    def _resolver_lance_automatico(
        self,
        estado: EstadoPartida,
        lance: LanceMus,
        participantes: Sequence[str],
    ) -> ResultadoLance:
        estado_lance = EstadoLance(lance=lance, participantes=tuple(participantes))
        estado.lance_en_curso = estado_lance
        resultado = self._resolver_lance_actual(estado, ordago_aceptado=False)
        estado.lance_en_curso = None
        return resultado

    def _resolver_apuesta_rechazada(self, estado: EstadoPartida) -> ResultadoLance:
        lance = estado.lance_en_curso
        if lance is None or lance.envite_pendiente is None:
            raise ValueError("No hay apuesta pendiente que resolver como rechazada.")

        pendiente = lance.envite_pendiente
        ganador_lance = self._resolver_ganador_lance(estado, lance.lance, lance.participantes)
        puntos_apuesta = self._puntos_apuesta_rechazada(lance)
        tipo_apuesta = "ordago" if pendiente.es_ordago else "envite"
        descripcion = f"{tipo_apuesta} no querido en {lance.lance.value}"
        return ResultadoLance(
            lance=lance.lance,
            ganador_jugador=ganador_lance,
            ganador_equipo=estado.equipos_por_jugador[ganador_lance],
            participantes=lance.participantes,
            puntos_base_ganador=self._puntos_propios_lance(
                estado,
                lance,
                ganador_lance,
                hubo_apuesta=True,
            ),
            puntos_apuesta=puntos_apuesta,
            equipo_apuesta=pendiente.equipo_apostador,
            descripcion=descripcion,
            apuesta_rechazada=True,
        )

    def _resolver_lance_actual(
        self,
        estado: EstadoPartida,
        ordago_aceptado: bool,
    ) -> ResultadoLance:
        lance = estado.lance_en_curso
        if lance is None:
            raise ValueError("No hay lance en curso para resolver.")

        participantes = lance.participantes
        ganador = self._resolver_ganador_lance(estado, lance.lance, participantes)
        puntos_base = self._puntos_propios_lance(
            estado,
            lance,
            ganador,
            hubo_apuesta=lance.envite_pendiente is not None,
        )
        puntos_apuesta = 0
        equipo_apuesta: str | None = None

        if ordago_aceptado:
            descripcion = f"ordago aceptado en {lance.lance.value}"
        elif lance.envite_pendiente is None:
            descripcion = f"{lance.lance.value} resuelto en paso"
        else:
            puntos_apuesta = lance.envite_pendiente.cantidad or 0
            equipo_apuesta = estado.equipos_por_jugador[ganador]
            descripcion = f"{lance.lance.value} con envite aceptado por {puntos_apuesta} puntos"

        return ResultadoLance(
            lance=lance.lance,
            ganador_jugador=ganador,
            ganador_equipo=estado.equipos_por_jugador[ganador],
            participantes=participantes,
            puntos_base_ganador=puntos_base,
            puntos_apuesta=puntos_apuesta,
            equipo_apuesta=equipo_apuesta,
            descripcion=descripcion,
            ordago_aceptado=ordago_aceptado,
        )

    def _resolver_ganador_lance(
        self,
        estado: EstadoPartida,
        lance: LanceMus,
        participantes: Sequence[str],
    ) -> str:
        if lance is LanceMus.GRANDE:
            evaluaciones = {
                jugador_id: evaluar_grande(estado.mano(jugador_id)) for jugador_id in participantes
            }
            return mejor_jugador(estado.orden_turnos, evaluaciones, comparacion_grande)

        if lance is LanceMus.CHICA:
            evaluaciones = {
                jugador_id: evaluar_chica(estado.mano(jugador_id)) for jugador_id in participantes
            }
            return mejor_jugador(estado.orden_turnos, evaluaciones, comparacion_chica)

        if lance is LanceMus.PARES:
            evaluaciones = {
                jugador_id: evaluar_pares(estado.mano(jugador_id))
                for jugador_id in participantes
                if evaluar_pares(estado.mano(jugador_id)) is not None
            }
            return mejor_jugador(estado.orden_turnos, evaluaciones, comparacion_pares)

        if lance is LanceMus.JUEGO:
            evaluaciones = {
                jugador_id: evaluar_juego(estado.mano(jugador_id))
                for jugador_id in participantes
                if evaluar_juego(estado.mano(jugador_id)) is not None
            }
            return mejor_jugador(estado.orden_turnos, evaluaciones, comparacion_juego)

        evaluaciones = {
            jugador_id: evaluar_punto(estado.mano(jugador_id)) for jugador_id in participantes
        }
        return mejor_jugador(estado.orden_turnos, evaluaciones, comparacion_punto)

    def _puntos_propios_lance(
        self,
        estado: EstadoPartida,
        lance: EstadoLance,
        ganador_jugador: str,
        *,
        hubo_apuesta: bool,
    ) -> int:
        if lance.lance is LanceMus.GRANDE:
            return 0 if hubo_apuesta else 1

        if lance.lance is LanceMus.CHICA:
            return 0 if hubo_apuesta else 1

        if lance.lance is LanceMus.PARES:
            pares = evaluar_pares(estado.mano(ganador_jugador))
            if pares is None:
                raise ValueError("El ganador de pares debe tener pares.")
            equipos = {estado.equipos_por_jugador[jugador_id] for jugador_id in lance.participantes}
            if hubo_apuesta or len(equipos) == 1:
                return pares.puntos
            return pares.puntos + 1

        if lance.lance is LanceMus.JUEGO:
            juego = evaluar_juego(estado.mano(ganador_jugador))
            if juego is None:
                raise ValueError("El ganador de juego debe tener juego.")
            equipos = {estado.equipos_por_jugador[jugador_id] for jugador_id in lance.participantes}
            if hubo_apuesta or len(equipos) == 1:
                return juego.puntos
            return juego.puntos + 1

        return 1

    @staticmethod
    def _puntos_apuesta_rechazada(lance: EstadoLance) -> int:
        """Calcula los tantos del no quiero.

        Regla fijada por el usuario:
        - si se rechaza la primera apuesta del lance, vale `1`
        - si se rechaza una resubida, vale la cantidad previamente en litigio
        """

        if lance.envite_pendiente is None:
            raise ValueError("No hay apuesta pendiente rechazada.")
        if lance.envite_pendiente.cantidad_previa > 0:
            return lance.envite_pendiente.cantidad_previa
        return 1

    def _resolver_tanteo(self, estado: EstadoPartida) -> None:
        anotaciones = resolver_puntuacion_mano(
            estado.resultados_lances,
            estado.marcador,
            piedras_objetivo=self.piedras_objetivo,
        )
        estado.marcador = aplicar_anotaciones(estado.marcador, anotaciones)
        for anotacion in anotaciones:
            self._registrar_historial(
                estado,
                f"tanteo:{anotacion.lance.value}:{anotacion.equipo_id}:{anotacion.puntos}",
            )
            if anotacion.cierra_juego:
                estado.ganador_juego_actual = anotacion.equipo_id
                break

        if estado.ganador_juego_actual is not None:
            estado.juegos_ganados[estado.ganador_juego_actual] = (
                estado.juegos_ganados.get(estado.ganador_juego_actual, 0) + 1
            )
            if estado.juegos_ganados[estado.ganador_juego_actual] >= self.juegos_objetivo:
                estado.ganador_partida = estado.ganador_juego_actual

    def _materializar_accion(self, accion: AccionLegal | AccionMus) -> AccionLegal:
        if isinstance(accion, AccionLegal):
            if accion.tipo is AccionMus.ENVIDAR and accion.cantidad is None:
                return AccionLegal.envidar(accion.cantidad_minima)
            return accion
        return AccionLegal.simple(accion)

    @staticmethod
    def _registrar_historial(estado: EstadoPartida, evento: str) -> None:
        estado.historial_publico.append(evento)
