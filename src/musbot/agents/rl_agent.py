"""Agente RL tabular sencillo y serializable."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from random import Random
from typing import Any

from musbot.agents.base_agent import BaseAgent, LegalAction, Observacion
from musbot.env.acciones import AccionLegal, AccionMus


@dataclass(frozen=True, slots=True)
class ExperienceStep:
    """Decision del agente usada para aprendizaje posterior."""

    state_key: str
    action_key: str


def action_key(accion: LegalAction) -> str:
    """Clave estable de una accion legal para politica tabular."""

    if isinstance(accion, AccionLegal):
        return str(accion)
    return accion.value


@dataclass(slots=True)
class RLAgent(BaseAgent):
    """Agente RL tabular minimo.

    Esta primera version no pretende ser el algoritmo final del proyecto, pero
    ya permite:

    - entrenar una politica simple
    - guardar checkpoints
    - reanudar o bifurcar runs
    - comparar modelos entre si
    """

    epsilon: float = 0.1
    learning_rate: float = 0.1
    seed: int | None = None
    state_encoder_version: str = "v2"
    model_version: str = "tabular_v2"
    policy: dict[str, dict[str, float]] = field(default_factory=dict)
    visit_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    update_count: int = 0
    _rng: Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = Random(self.seed)

    def elegir_accion(
        self,
        acciones_legales: Sequence[LegalAction],
        observacion: Observacion = None,
    ) -> LegalAction:
        opciones = list(acciones_legales)
        if not opciones:
            raise ValueError("El agente RL necesita al menos una accion legal.")

        state_key = self.state_key(observacion)
        if self._rng.random() < self.epsilon:
            return self._rng.choice(opciones)

        puntuaciones = self.policy.get(state_key, {})
        mejor_valor = max(puntuaciones.get(action_key(accion), 0.0) for accion in opciones)
        mejores = [
            accion
            for accion in opciones
            if puntuaciones.get(action_key(accion), 0.0) == mejor_valor
        ]
        return self._rng.choice(mejores)

    def state_key(self, observacion: Observacion) -> str:
        """Resume la observacion en una clave tabular estable."""

        if observacion is None:
            return "sin_observacion"

        if self.state_encoder_version == "v1":
            return self._state_key_v1(observacion)
        if self.state_encoder_version == "v3":
            return self._state_key_v3(observacion)
        if self.state_encoder_version == "v4":
            return self._state_key_v4(observacion)
        return self._state_key_v2(observacion)

    def _state_key_v1(self, observacion: Mapping[str, object]) -> str:
        fase = str(observacion.get("fase", "desconocida"))
        es_mano = "mano" if observacion.get("es_mano") else "no_mano"
        tiene_pares = "pares" if observacion.get("tiene_pares") else "sin_pares"
        tiene_juego = "juego" if observacion.get("tiene_juego") else "sin_juego"
        diferencial = int(observacion.get("diferencial_marcador", 0))
        bucket = self._bucket_marcador(diferencial)
        return "|".join((fase, es_mano, tiene_pares, tiene_juego, bucket))

    def _state_key_v2(self, observacion: Mapping[str, object]) -> str:
        fase = str(observacion.get("fase", "desconocida"))
        lance_actual = str(observacion.get("lance_actual") or fase)
        posicion = self._bucket_posicion(observacion.get("indice_turno"))
        es_mano = "mano" if observacion.get("es_mano") else "no_mano"
        diferencial = int(observacion.get("diferencial_marcador", 0))
        marcador_bucket = self._bucket_marcador(diferencial)
        presion_cierre = self._bucket_presion_cierre(
            observacion.get("marcador_propio"),
            observacion.get("marcador_rival"),
        )
        pares = str(observacion.get("categoria_pares") or "sin_pares")
        juego = self._bucket_juego_punto(observacion)
        cartas = self._bucket_cartas(observacion)
        acciones = self._bucket_contexto_acciones(observacion.get("legal_action_labels"))
        envite = self._bucket_envite(observacion.get("detalle_envite_pendiente"))
        return "|".join(
            (
                fase,
                lance_actual,
                posicion,
                es_mano,
                marcador_bucket,
                presion_cierre,
                pares,
                juego,
                cartas,
                acciones,
                envite,
            )
        )

    def _state_key_v3(self, observacion: Mapping[str, object]) -> str:
        fase = str(observacion.get("fase", "desconocida"))
        lance_actual = str(observacion.get("lance_actual") or fase)
        posicion = self._bucket_posicion(observacion.get("indice_turno"))
        diferencial = int(observacion.get("diferencial_marcador", 0))
        marcador_bucket = self._bucket_marcador(diferencial)
        presion_cierre = self._bucket_presion_cierre(
            observacion.get("marcador_propio"),
            observacion.get("marcador_rival"),
        )
        pareja_publica = self._bucket_control_publico(observacion)
        pares = self._bucket_pares_detallados(observacion)
        juego = self._bucket_juego_punto(observacion)
        cartas = self._bucket_cartas_compacto(observacion)
        historial = self._bucket_historial_publico(observacion)
        acciones = self._bucket_contexto_acciones(observacion.get("legal_action_labels"))
        envite = self._bucket_envite(observacion.get("detalle_envite_pendiente"))
        return "|".join(
            (
                fase,
                lance_actual,
                posicion,
                marcador_bucket,
                presion_cierre,
                pareja_publica,
                pares,
                juego,
                cartas,
                historial,
                acciones,
                envite,
            )
        )

    def _state_key_v4(self, observacion: Mapping[str, object]) -> str:
        fase = str(observacion.get("fase", "desconocida"))
        lance_actual = str(observacion.get("lance_actual") or fase)
        posicion = self._bucket_posicion(observacion.get("indice_turno"))
        diferencial = int(observacion.get("diferencial_marcador", 0))
        marcador_bucket = self._bucket_marcador(diferencial)
        presion_cierre = self._bucket_presion_cierre(
            observacion.get("marcador_propio"),
            observacion.get("marcador_rival"),
        )
        perfil = self._bucket_perfil_mano_v4(observacion)
        fuerza_actual = self._bucket_fuerza_lance_actual(observacion)
        pareja_publica = self._bucket_control_publico(observacion)
        historial = self._bucket_historial_publico(observacion)
        acciones = self._bucket_contexto_acciones(observacion.get("legal_action_labels"))
        envite = self._bucket_envite_v4(observacion.get("detalle_envite_pendiente"))
        return "|".join(
            (
                fase,
                lance_actual,
                posicion,
                marcador_bucket,
                presion_cierre,
                perfil,
                fuerza_actual,
                pareja_publica,
                historial,
                acciones,
                envite,
            )
        )

    def actualizar_desde_experiencias(
        self,
        experiencias: Sequence[ExperienceStep],
        recompensa_final: float,
    ) -> None:
        """Actualiza la politica tabular con una recompensa final."""

        for paso in experiencias:
            estado = self.policy.setdefault(paso.state_key, {})
            visitas_estado = self.visit_counts.setdefault(paso.state_key, {})
            visitas = visitas_estado.get(paso.action_key, 0) + 1
            visitas_estado[paso.action_key] = visitas
            valor_actual = estado.get(paso.action_key, 0.0)
            alpha = self._effective_learning_rate(visitas)
            estado[paso.action_key] = valor_actual + alpha * (recompensa_final - valor_actual)
            self.update_count += 1

    def to_state_dict(self) -> dict[str, Any]:
        """Serializa el estado del agente."""

        return {
            "agent_id": self.agent_id,
            "epsilon": self.epsilon,
            "learning_rate": self.learning_rate,
            "seed": self.seed,
            "state_encoder_version": self.state_encoder_version,
            "policy": self.policy,
            "visit_counts": self.visit_counts,
            "update_count": self.update_count,
            "version": self.model_version,
        }

    @classmethod
    def from_state_dict(cls, payload: Mapping[str, Any]) -> RLAgent:
        """Reconstruye el agente desde un checkpoint."""

        agent = cls(
            agent_id=str(payload["agent_id"]),
            epsilon=float(payload.get("epsilon", 0.1)),
            learning_rate=float(payload.get("learning_rate", 0.1)),
            seed=payload.get("seed"),
            state_encoder_version=str(
                payload.get(
                    "state_encoder_version",
                    {
                        "tabular_v1": "v1",
                        "tabular_v3": "v3",
                        "tabular_v4": "v4",
                    }.get(str(payload.get("version")), "v2"),
                )
            ),
            model_version=str(payload.get("version", "tabular_v1")),
            policy={
                str(state_key): {str(k): float(v) for k, v in value.items()}
                for state_key, value in dict(payload.get("policy", {})).items()
            },
            visit_counts={
                str(state_key): {str(k): int(v) for k, v in value.items()}
                for state_key, value in dict(payload.get("visit_counts", {})).items()
            },
            update_count=int(payload.get("update_count", 0)),
        )
        return agent

    def snapshot(self) -> dict[str, Any]:
        """Alias semantico para usar desde entrenamiento."""

        return self.to_state_dict()

    @staticmethod
    def materializar_accion(accion: LegalAction) -> AccionLegal | AccionMus:
        """Normaliza el tipo de retorno del agente."""

        if isinstance(accion, AccionLegal):
            return accion
        return accion

    @staticmethod
    def _bucket_marcador(diferencial: int) -> str:
        if diferencial <= -10:
            return "muy_por_detras"
        if diferencial < 0:
            return "por_detras"
        if diferencial == 0:
            return "empatado"
        if diferencial < 10:
            return "por_delante"
        return "muy_por_delante"

    @staticmethod
    def _bucket_posicion(indice_turno: object) -> str:
        if not isinstance(indice_turno, int):
            return "pos_desconocida"
        return {
            0: "mano",
            1: "segunda",
            2: "tercera",
            3: "postre",
        }.get(indice_turno, f"pos_{indice_turno}")

    @staticmethod
    def _bucket_presion_cierre(
        marcador_propio: object,
        marcador_rival: object,
    ) -> str:
        propios = int(marcador_propio or 0)
        rival = int(marcador_rival or 0)
        faltan_propios = max(0, 40 - propios)
        faltan_rival = max(0, 40 - rival)
        if faltan_propios <= 4 and faltan_rival <= 4:
            return "ambos_en_cierre"
        if faltan_propios <= 4:
            return "cierre_propio"
        if faltan_rival <= 4:
            return "cierre_rival"
        return "sin_cierre_inmediato"

    @staticmethod
    def _bucket_juego_punto(observacion: Mapping[str, object]) -> str:
        if observacion.get("tiene_juego"):
            return f"juego_{observacion.get('valor_juego', 'desconocido')}"
        return f"punto_{observacion.get('valor_punto', 'desconocido')}"

    def _bucket_pares_detallados(self, observacion: Mapping[str, object]) -> str:
        categoria = str(observacion.get("categoria_pares") or "sin_pares")
        if categoria == "sin_pares":
            return categoria

        valores = observacion.get("valores_mus")
        if not isinstance(valores, Sequence):
            return categoria

        valores_int = [int(valor) for valor in valores]
        frecuencias: dict[int, int] = {}
        for valor in valores_int:
            frecuencias[valor] = frecuencias.get(valor, 0) + 1

        grupos = sorted(
            ((cantidad, valor) for valor, cantidad in frecuencias.items() if cantidad >= 2),
            reverse=True,
        )
        if not grupos:
            return categoria

        valor_principal = grupos[0][1]
        rango = self._bucket_valor_mus(valor_principal)
        if categoria == "duples" and len(grupos) > 1:
            valor_secundario = grupos[1][1]
            rango_secundario = self._bucket_valor_mus(valor_secundario)
            return f"duples_{rango}_{rango_secundario}"
        return f"{categoria}_{rango}"

    @staticmethod
    def _bucket_cartas(observacion: Mapping[str, object]) -> str:
        valores = observacion.get("valores_mus")
        if not isinstance(valores, Sequence):
            return "cartas_desconocidas"

        valores_int = [int(valor) for valor in valores]
        altas = sum(1 for valor in valores_int if valor == 7)
        figuras = sum(1 for valor in valores_int if valor >= 5)
        bajas = sum(1 for valor in valores_int if valor == 0)
        chicas = sum(1 for valor in valores_int if valor <= 1)
        suma = int(observacion.get("suma_cartas", 0))
        return f"reyes_{altas}|figuras_{figuras}|ases_{bajas}|bajas_{chicas}|suma_{suma}"

    @staticmethod
    def _bucket_cartas_compacto(observacion: Mapping[str, object]) -> str:
        valores = observacion.get("valores_mus")
        if not isinstance(valores, Sequence):
            return "cartas_desconocidas"

        valores_int = [int(valor) for valor in valores]
        altas = sum(1 for valor in valores_int if valor == 7)
        bajas = sum(1 for valor in valores_int if valor == 0)
        medias = sum(1 for valor in valores_int if 1 <= valor <= 4)
        figuras = sum(1 for valor in valores_int if valor >= 5)
        return f"altas_{altas}|bajas_{bajas}|medias_{medias}|figuras_{figuras}"

    def _bucket_contexto_acciones(self, legal_action_labels: object) -> str:
        if not isinstance(legal_action_labels, Sequence):
            return "acciones_desconocidas"

        etiquetas = {str(label) for label in legal_action_labels}
        if "pedir_mus" in etiquetas or "cortar_mus" in etiquetas:
            return "decision_mus"
        if any(label.startswith("descartar:") for label in etiquetas):
            return "descarte"
        if "quiero" in etiquetas and "no_quiero" in etiquetas:
            if "ordago" in etiquetas and not any(
                label.startswith("envidar:") for label in etiquetas
            ):
                return "respuesta_ordago"
            return "respuesta_envite"
        if "pasar" in etiquetas and any(label.startswith("envidar:") for label in etiquetas):
            return "apertura_lance"
        if "pasar" in etiquetas:
            return "paso_simple"
        return "acciones_variadas"

    def _bucket_perfil_mano_v4(self, observacion: Mapping[str, object]) -> str:
        grande = self._bucket_fuerza(observacion.get("fuerza_grande"))
        chica = self._bucket_fuerza(observacion.get("fuerza_chica"))
        pares = self._bucket_pares_v4(observacion)
        juego = self._bucket_juego_v4(observacion)
        return f"g_{grande}|c_{chica}|p_{pares}|j_{juego}"

    def _bucket_fuerza_lance_actual(self, observacion: Mapping[str, object]) -> str:
        lance = str(observacion.get("lance_actual") or observacion.get("fase") or "")
        if lance == "grande":
            return f"f_{self._bucket_fuerza(observacion.get('fuerza_grande'))}"
        if lance == "chica":
            return f"f_{self._bucket_fuerza(observacion.get('fuerza_chica'))}"
        if lance == "pares":
            return f"f_{self._bucket_fuerza(observacion.get('fuerza_pares'))}"
        if lance == "juego":
            return f"f_{self._bucket_fuerza(observacion.get('fuerza_juego'))}"
        if lance == "punto":
            return f"f_{self._bucket_fuerza(observacion.get('fuerza_punto'))}"
        return "f_desconocida"

    @staticmethod
    def _bucket_control_publico(observacion: Mapping[str, object]) -> str:
        propios_pares = int(observacion.get("conteo_pares_propios") or 0)
        rivales_pares = int(observacion.get("conteo_pares_rivales") or 0)
        propios_juego = int(observacion.get("conteo_juego_propios") or 0)
        rivales_juego = int(observacion.get("conteo_juego_rivales") or 0)
        return f"pares_{propios_pares}_{rivales_pares}|juego_{propios_juego}_{rivales_juego}"

    def _bucket_envite_v4(self, detalle_envite: object) -> str:
        if not isinstance(detalle_envite, Mapping):
            return "sin_envite"

        tipo_apuesta = str(detalle_envite.get("tipo_apuesta", "desconocida"))
        actual = self._bucket_cantidad_envite(detalle_envite.get("cantidad_actual"))
        no_quiero = self._bucket_cantidad_envite(detalle_envite.get("valor_no_quiero"))
        rol = "propia" if detalle_envite.get("soy_equipo_apostador") else "rival"
        turno = "responde" if detalle_envite.get("me_toca_responder") else "espera"
        return f"tipo_{tipo_apuesta}|act_{actual}|noq_{no_quiero}|{rol}|{turno}"

    def _bucket_historial_publico(self, observacion: Mapping[str, object]) -> str:
        ultimo = str(observacion.get("ultimo_evento_publico") or "sin_historial")
        conteo = int(observacion.get("conteo_eventos_publicos") or 0)
        bucket_eventos = self._bucket_cantidad_eventos(conteo)
        tipo = self._bucket_tipo_evento(ultimo)
        return f"{bucket_eventos}|{tipo}"

    def _bucket_envite(self, detalle_envite: object) -> str:
        if not isinstance(detalle_envite, Mapping):
            return "sin_envite"

        tipo_apuesta = str(detalle_envite.get("tipo_apuesta", "desconocida"))
        actual = self._bucket_cantidad_envite(detalle_envite.get("cantidad_actual"))
        previa = self._bucket_cantidad_envite(detalle_envite.get("cantidad_previa"))
        no_quiero = self._bucket_cantidad_envite(detalle_envite.get("valor_no_quiero"))
        es_reenvite = "reenvite" if detalle_envite.get("es_reenvite") else "apertura"
        rol = "apuesta_propia" if detalle_envite.get("soy_equipo_apostador") else "respuesta_rival"
        respuesta = "me_toca_responder" if detalle_envite.get("me_toca_responder") else "espera"
        return "|".join(
            (
                f"tipo_{tipo_apuesta}",
                f"actual_{actual}",
                f"previa_{previa}",
                f"noq_{no_quiero}",
                es_reenvite,
                rol,
                respuesta,
            )
        )

    @staticmethod
    def _bucket_cantidad_envite(cantidad: object) -> str:
        if cantidad is None:
            return "none"

        valor = int(cantidad)
        if valor <= 7:
            return str(valor)
        if valor <= 15:
            return "8_15"
        if valor <= 30:
            return "16_30"
        return "31_40"

    @staticmethod
    def _bucket_fuerza(valor: object) -> str:
        if not isinstance(valor, (float, int)):
            return "desconocida"
        fuerza = float(valor)
        if fuerza >= 0.90:
            return "muy_alta"
        if fuerza >= 0.75:
            return "alta"
        if fuerza >= 0.55:
            return "media"
        if fuerza >= 0.35:
            return "baja"
        return "muy_baja"

    def _bucket_pares_v4(self, observacion: Mapping[str, object]) -> str:
        categoria = str(observacion.get("categoria_pares") or "sin_pares")
        if categoria == "sin_pares":
            return categoria
        fuerza = self._bucket_fuerza(observacion.get("fuerza_pares"))
        if categoria == "pares":
            return f"pares_{fuerza}"
        return categoria

    def _bucket_juego_v4(self, observacion: Mapping[str, object]) -> str:
        if observacion.get("tiene_juego"):
            valor_juego = int(observacion.get("valor_juego") or 0)
            if valor_juego == 31:
                return "31"
            return f"juego_{self._bucket_fuerza(observacion.get('fuerza_juego'))}"
        return f"punto_{self._bucket_fuerza(observacion.get('fuerza_punto'))}"

    @staticmethod
    def _bucket_valor_mus(valor: int) -> str:
        if valor == 7:
            return "muy_alto"
        if valor >= 5:
            return "alto"
        if valor >= 2:
            return "medio"
        return "bajo"

    @staticmethod
    def _bucket_cantidad_eventos(cantidad: int) -> str:
        if cantidad <= 1:
            return "hist_0_1"
        if cantidad <= 3:
            return "hist_2_3"
        if cantidad <= 6:
            return "hist_4_6"
        return "hist_7_plus"

    @staticmethod
    def _bucket_tipo_evento(evento: str) -> str:
        if ":reenvite:" in evento or ":envida:" in evento:
            return "evento_envite"
        if ":quiere_" in evento:
            return "evento_quiero"
        if ":no_quiere_" in evento:
            return "evento_no_quiero"
        if ":ordago:" in evento:
            return "evento_ordago"
        if ":mus" in evento or ":corta_mus" in evento:
            return "evento_mus"
        if ":descarta:" in evento:
            return "evento_descarte"
        if ":paso:" in evento:
            return "evento_paso"
        return "evento_otro"

    def _effective_learning_rate(self, visit_count: int) -> float:
        if 0.0 < self.learning_rate <= 1.0:
            return self.learning_rate
        return 1.0 / max(visit_count, 1)
