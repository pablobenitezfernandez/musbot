"""UI web ligera para jugar una mano contra bots en local."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from random import Random
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from musbot.agents.base_agent import BaseAgent
from musbot.agents.heuristic_agent import HeuristicAgent
from musbot.agents.random_agent import RandomAgent
from musbot.analysis.decision_logger import DecisionLogger, DecisionRecord
from musbot.core.cartas import Carta
from musbot.core.estado_partida import EstadoPartida, FaseMano, LanceMus, ResultadoLance
from musbot.core.motor import MotorMus
from musbot.env.acciones import MAX_ENVITE_CANONICO, AccionLegal, AccionMus
from musbot.env.observaciones import construir_observacion_agente
from musbot.training.self_play import expandir_acciones_para_agente

HTML_APP_PATH = Path(__file__).with_name("static") / "human_vs_bot.html"
PLAYER_LABELS = {
    "j1": "Tu",
    "j2": "Rival izquierda",
    "j3": "Compañero bot",
    "j4": "Rival derecha",
}
TEAM_LABELS = {
    "equipo_1": "Tu pareja",
    "equipo_2": "Pareja rival",
}
LANCE_ORDER: tuple[LanceMus, ...] = (
    LanceMus.GRANDE,
    LanceMus.CHICA,
    LanceMus.PARES,
    LanceMus.JUEGO,
    LanceMus.PUNTO,
)


@dataclass(slots=True)
class HumanVsBotSession:
    """Sesion local de una mano `humano vs bots`."""

    human_player_id: str = "j1"
    bot_mode: str = "heuristic"
    logs_root: Path = Path("data/logs_decisiones/web")
    seed: int | None = None
    motor: MotorMus = field(default_factory=MotorMus)
    session_id: str = field(init=False)
    state: EstadoPartida | None = field(init=False, default=None)
    _bots: dict[str, BaseAgent] = field(init=False, repr=False)
    _rng: Random = field(init=False, repr=False)
    _decision_log_path: Path = field(init=False, repr=False)
    _decision_logger: DecisionLogger = field(init=False, repr=False)
    _bot_actions: list[dict[str, object]] = field(
        init=False,
        default_factory=list,
        repr=False,
    )

    def __post_init__(self) -> None:
        self.session_id = uuid4().hex
        self._rng = Random(self.seed)
        self._bots = self._crear_bots()
        self._decision_log_path = self.logs_root / f"web_{self.session_id}.jsonl"
        self._decision_logger = DecisionLogger(self._decision_log_path)
        self._bot_actions: list[dict[str, object]] = []
        self.state: EstadoPartida | None = None

    def new_hand(
        self,
        *,
        seed: int | None = None,
        manos_iniciales: dict[str, list[Carta]] | None = None,
    ) -> dict[str, object]:
        """Arranca una mano nueva y avanza bots hasta el turno humano."""

        self._bot_actions.clear()
        self.state = self.motor.iniciar_partida(
            partida_id=f"web-{self.session_id}",
            seed=self._seed_for_hand(seed),
            manos_iniciales=manos_iniciales,
        )
        self._autoplay_bots()
        return self.snapshot()

    def apply_human_action(self, payload: dict[str, object]) -> dict[str, object]:
        """Aplica una accion del humano y vuelve a avanzar bots."""

        if self.state is None:
            raise ValueError("No hay mano activa. Crea una nueva antes de jugar.")
        if self.state.fase is FaseMano.FINALIZADA:
            raise ValueError("La mano ya ha terminado. Crea una nueva para seguir.")
        if self.state.jugador_activo != self.human_player_id:
            raise ValueError("Ahora mismo no es el turno del humano.")

        accion = self._parse_human_action(payload)
        self._registrar_decision(self.human_player_id, accion, source="web_ui_human")
        self.state = self.motor.aplicar_accion(self.state, accion, self.human_player_id)
        self._autoplay_bots()
        return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        """Serializa el estado actual para el frontend."""

        if self.state is None:
            raise ValueError("La sesion aun no tiene una mano cargada.")

        state = self.state
        human_turn = state.jugador_activo == self.human_player_id
        legal_actions = self.motor.acciones_legales(state) if human_turn else []
        return {
            "session_id": self.session_id,
            "bot_mode": self.bot_mode,
            "human_player_id": self.human_player_id,
            "phase": state.fase.value,
            "active_player": state.jugador_activo,
            "active_player_label": (
                None if state.jugador_activo is None else PLAYER_LABELS.get(state.jugador_activo)
            ),
            "finalized": state.fase is FaseMano.FINALIZADA,
            "human_can_act": human_turn and state.fase is not FaseMano.FINALIZADA,
            "scoreboard": dict(state.marcador),
            "games_won": dict(state.juegos_ganados),
            "game_winner": state.ganador_juego_actual,
            "match_winner": state.ganador_partida,
            "hand_id": state.mano_id,
            "partida_id": state.partida_id,
            "discard_count": len(state.descarte),
            "remaining_deck": len(state.mazo_restante),
            "decision_log_path": str(self._decision_log_path),
            "players": self._serialize_players(reveal_all=state.fase is FaseMano.FINALIZADA),
            "human_hand": self._serialize_cards(state.mano(self.human_player_id)),
            "legal_actions": self._serialize_human_controls(legal_actions),
            "history": list(state.historial_publico),
            "bot_actions": list(self._bot_actions[-20:]),
            "results": self._serialize_results(),
        }

    def _seed_for_hand(self, seed: int | None) -> int:
        if seed is not None:
            return seed
        return self._rng.randint(0, 10_000_000)

    def _crear_bots(self) -> dict[str, BaseAgent]:
        bots: dict[str, BaseAgent] = {}
        for player_id in ("j2", "j3", "j4"):
            if self.bot_mode == "random":
                bots[player_id] = RandomAgent(
                    agent_id=f"random_{player_id}",
                    seed=self._rng.randint(0, 10_000_000),
                )
            elif self.bot_mode == "mixed":
                kind = self._rng.choice(("random", "heuristic"))
                if kind == "random":
                    bots[player_id] = RandomAgent(
                        agent_id=f"random_{player_id}",
                        seed=self._rng.randint(0, 10_000_000),
                    )
                else:
                    bots[player_id] = HeuristicAgent(agent_id=f"heuristic_{player_id}")
            else:
                bots[player_id] = HeuristicAgent(agent_id=f"heuristic_{player_id}")
        return bots

    def _autoplay_bots(self) -> None:
        if self.state is None:
            return

        while (
            self.state.fase is not FaseMano.FINALIZADA
            and self.state.jugador_activo is not None
            and self.state.jugador_activo != self.human_player_id
        ):
            player_id = self.state.jugador_activo
            legal_actions = expandir_acciones_para_agente(self.motor.acciones_legales(self.state))
            observation = construir_observacion_agente(
                self.state,
                player_id,
                legal_actions,
            ).to_agent_dict()
            bot = self._bots[player_id]
            action = bot.elegir_accion(legal_actions, observation)
            materialized = action if isinstance(action, AccionLegal) else AccionLegal.simple(action)
            self._registrar_decision(player_id, materialized, source=f"web_ui_bot:{bot.agent_id}")
            self._bot_actions.append(
                {
                    "player_id": player_id,
                    "player_label": PLAYER_LABELS.get(player_id, player_id),
                    "team_id": self.state.equipos_por_jugador[player_id],
                    "team_label": TEAM_LABELS.get(self.state.equipos_por_jugador[player_id]),
                    "phase": self.state.fase.value,
                    "lance": (
                        None
                        if self.state.lance_en_curso is None
                        else self.state.lance_en_curso.lance.value
                    ),
                    "action": str(materialized),
                    "legal_actions": [str(legal_action) for legal_action in legal_actions],
                }
            )
            self.state = self.motor.aplicar_accion(self.state, materialized, player_id)

    def _registrar_decision(
        self,
        player_id: str,
        action: AccionLegal,
        *,
        source: str,
    ) -> None:
        if self.state is None:
            return

        legal_actions = expandir_acciones_para_agente(self.motor.acciones_legales(self.state))
        record = DecisionRecord(
            partida_id=self.state.partida_id,
            mano_id=self.state.mano_id,
            jugador_id=player_id,
            fase=self.state.fase.value,
            cartas_propias=[carta.codigo for carta in self.state.mano(player_id)],
            marcador=dict(self.state.marcador),
            historial_publico=list(self.state.historial_publico),
            acciones_legales=[str(legal_action) for legal_action in legal_actions],
            accion_elegida=str(action),
            comentario=source,
        )
        self._decision_logger.registrar(record)

    def _parse_human_action(self, payload: dict[str, object]) -> AccionLegal | AccionMus:
        action_type = str(payload.get("type") or "").strip()
        if not action_type:
            raise ValueError("La accion del frontend debe incluir un campo 'type'.")

        if action_type == AccionMus.ENVIDAR.value:
            amount = payload.get("amount")
            if amount is None:
                raise ValueError("Envidar requiere una cantidad.")
            return AccionLegal.envidar(int(amount))

        if action_type == AccionMus.DESCARTAR.value:
            raw_indices = payload.get("indices", [])
            if not isinstance(raw_indices, list):
                raise ValueError("El descarte requiere una lista de indices.")
            indices = tuple(sorted({int(index) for index in raw_indices}))
            return AccionLegal.descartar(indices)

        return AccionMus(action_type)

    def _serialize_human_controls(
        self,
        legal_actions: list[AccionLegal],
    ) -> dict[str, object]:
        buttons: list[dict[str, str]] = []
        envite_form: dict[str, object] | None = None
        discard_form: dict[str, object] | None = None

        envite_action = next(
            (action for action in legal_actions if action.tipo is AccionMus.ENVIDAR),
            None,
        )
        if envite_action is not None:
            envite_form = {
                "enabled": True,
                "type": AccionMus.ENVIDAR.value,
                "min": envite_action.cantidad_minima,
                "max": envite_action.cantidad_maxima or MAX_ENVITE_CANONICO,
            }

        if any(action.tipo is AccionMus.DESCARTAR for action in legal_actions):
            discard_form = {
                "enabled": True,
                "type": AccionMus.DESCARTAR.value,
                "cards": (
                    self._serialize_cards(self.state.mano(self.human_player_id))
                    if self.state
                    else []
                ),
            }

        for action in legal_actions:
            if action.tipo in {AccionMus.ENVIDAR, AccionMus.DESCARTAR}:
                continue
            buttons.append(
                {
                    "type": action.tipo.value,
                    "label": self._human_action_label(action.tipo),
                }
            )

        return {
            "buttons": buttons,
            "envite": envite_form,
            "discard": discard_form,
            "raw": [str(action) for action in legal_actions],
        }

    def _serialize_players(self, *, reveal_all: bool) -> list[dict[str, object]]:
        if self.state is None:
            return []

        players: list[dict[str, object]] = []
        for player_id in self.state.orden_turnos:
            team_id = self.state.equipos_por_jugador[player_id]
            hidden = not reveal_all and player_id != self.human_player_id
            cards = (
                [{"hidden": True} for _ in self.state.mano(player_id)]
                if hidden
                else self._serialize_cards(self.state.mano(player_id))
            )
            players.append(
                {
                    "player_id": player_id,
                    "player_label": PLAYER_LABELS.get(player_id, player_id),
                    "team_id": team_id,
                    "team_label": TEAM_LABELS.get(team_id, team_id),
                    "is_human": player_id == self.human_player_id,
                    "is_active": self.state.jugador_activo == player_id,
                    "cards_hidden": hidden,
                    "cards": cards,
                }
            )
        return players

    def _serialize_cards(self, cards: list[Carta]) -> list[dict[str, object]]:
        return [
            {
                "code": card.codigo,
                "label": self._card_label(card),
                "mus_name": card.nombre_normalizado_mus,
                "mus_value": card.valor_normalizado_mus,
                "game_value": card.valor_juego_punto,
            }
            for card in cards
        ]

    def _serialize_results(self) -> list[dict[str, object]]:
        if self.state is None:
            return []

        results: list[dict[str, object]] = []
        for lance in LANCE_ORDER:
            result = self.state.resultados_lances.get(lance)
            if result is None:
                continue
            results.append(self._serialize_result(result))
        return results

    def _serialize_result(self, result: ResultadoLance) -> dict[str, object]:
        return {
            "lance": result.lance.value,
            "winner_player": result.ganador_jugador,
            "winner_player_label": PLAYER_LABELS.get(
                result.ganador_jugador,
                result.ganador_jugador,
            ),
            "winner_team": result.ganador_equipo,
            "winner_team_label": TEAM_LABELS.get(result.ganador_equipo, result.ganador_equipo),
            "participants": list(result.participantes),
            "points_base": result.puntos_base_ganador,
            "points_bet": result.puntos_apuesta,
            "bet_team": result.equipo_apuesta,
            "description": result.descripcion,
            "ordago_accepted": result.ordago_aceptado,
            "bet_rejected": result.apuesta_rechazada,
        }

    @staticmethod
    def _human_action_label(action_type: AccionMus) -> str:
        labels = {
            AccionMus.PASAR: "Pasar",
            AccionMus.PEDIR_MUS: "Mus",
            AccionMus.CORTAR_MUS: "Cortar mus",
            AccionMus.QUIERO: "Quiero",
            AccionMus.NO_QUIERO: "No quiero",
            AccionMus.ORDAGO: "Órdago",
        }
        return labels.get(action_type, action_type.value)

    @staticmethod
    def _card_label(card: Carta) -> str:
        return f"{card.figura.value.title()} de {card.palo.value}"


@dataclass(slots=True)
class MusWebApplication:
    """Contenedor de sesiones y recursos del servidor HTTP."""

    logs_root: Path = Path("data/logs_decisiones/web")
    _html: str = field(init=False, repr=False)
    _sessions: dict[str, HumanVsBotSession] = field(
        init=False,
        default_factory=dict,
        repr=False,
    )
    _lock: threading.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.logs_root.mkdir(parents=True, exist_ok=True)
        self._html = HTML_APP_PATH.read_text(encoding="utf-8")
        self._sessions: dict[str, HumanVsBotSession] = {}
        self._lock = threading.Lock()

    def new_session(
        self,
        *,
        bot_mode: str = "heuristic",
        seed: int | None = None,
    ) -> dict[str, object]:
        session = HumanVsBotSession(
            bot_mode=bot_mode,
            logs_root=self.logs_root,
            seed=seed,
        )
        snapshot = session.new_hand()
        with self._lock:
            self._sessions[session.session_id] = session
        return snapshot

    def new_hand(self, session_id: str) -> dict[str, object]:
        session = self.get_session(session_id)
        return session.new_hand()

    def get_state(self, session_id: str) -> dict[str, object]:
        return self.get_session(session_id).snapshot()

    def apply_action(self, session_id: str, payload: dict[str, object]) -> dict[str, object]:
        return self.get_session(session_id).apply_human_action(payload)

    def get_session(self, session_id: str) -> HumanVsBotSession:
        with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                raise KeyError("Sesion no encontrada o ya reiniciada.") from exc

    @property
    def html(self) -> str:
        return self._html


class MusWebHandler(BaseHTTPRequestHandler):
    """Handler HTTP sencillo para la UI web local."""

    server: MusThreadingHTTPServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(self.server.app.html)
            return

        if parsed.path == "/api/state":
            session_id = parse_qs(parsed.query).get("session_id", [None])[0]
            if not session_id:
                self._send_json({"ok": False, "error": "Falta session_id."}, HTTPStatus.BAD_REQUEST)
                return
            try:
                payload = self.server.app.get_state(session_id)
            except KeyError as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            self._send_json({"ok": True, "state": payload})
            return

        self._send_json({"ok": False, "error": "Ruta no encontrada."}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        body = self._read_json_body()

        if parsed.path == "/api/new-game":
            bot_mode = str(body.get("bot_mode") or "heuristic")
            seed = body.get("seed")
            payload = self.server.app.new_session(
                bot_mode=bot_mode,
                seed=None if seed in {None, ""} else int(seed),
            )
            self._send_json({"ok": True, "state": payload})
            return

        if parsed.path == "/api/new-hand":
            session_id = str(body.get("session_id") or "")
            if not session_id:
                self._send_json({"ok": False, "error": "Falta session_id."}, HTTPStatus.BAD_REQUEST)
                return
            try:
                payload = self.server.app.new_hand(session_id)
            except KeyError as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            self._send_json({"ok": True, "state": payload})
            return

        if parsed.path == "/api/action":
            session_id = str(body.get("session_id") or "")
            action = body.get("action")
            if not session_id or not isinstance(action, dict):
                self._send_json(
                    {"ok": False, "error": "La accion requiere session_id y action."},
                    HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                payload = self.server.app.apply_action(session_id, action)
            except (KeyError, ValueError) as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"ok": True, "state": payload})
            return

        self._send_json({"ok": False, "error": "Ruta no encontrada."}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("El cuerpo JSON no es valido.") from exc
        if not isinstance(payload, dict):
            raise ValueError("El cuerpo JSON debe ser un objeto.")
        return payload

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class MusThreadingHTTPServer(ThreadingHTTPServer):
    """Servidor HTTP con acceso a la aplicacion."""

    def __init__(
        self,
        server_address: tuple[str, int],
        app: MusWebApplication,
    ) -> None:
        self.app = app
        super().__init__(server_address, MusWebHandler)


def create_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    logs_root: str | Path = "data/logs_decisiones/web",
) -> MusThreadingHTTPServer:
    """Crea un servidor listo para servir la UI web."""

    app = MusWebApplication(logs_root=Path(logs_root))
    return MusThreadingHTTPServer((host, port), app)
