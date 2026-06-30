from pathlib import Path

from musbot.core.cartas import Carta, Figura, Palo
from musbot.ui.web_app import HumanVsBotSession
from tests._tmp_utils import workspace_tmp_dir


def _carta(figura: Figura, palo: Palo) -> Carta:
    return Carta(figura=figura, palo=palo)


def test_web_session_expone_estado_inicial_para_el_humano() -> None:
    with workspace_tmp_dir() as tmp_path:
        session = HumanVsBotSession(logs_root=tmp_path, bot_mode="heuristic", seed=7)

        snapshot = session.new_hand(seed=13)

        assert snapshot["session_id"]
        assert snapshot["active_player"] == "j1"
        assert snapshot["human_can_act"] is True
        assert snapshot["phase"] == "decision_mus"
        assert any(
            button["type"] == "pedir_mus" for button in snapshot["legal_actions"]["buttons"]
        )
        rivals = [player for player in snapshot["players"] if player["player_id"] != "j1"]
        assert all(player["cards_hidden"] for player in rivals)


def test_web_session_autojuega_bots_y_registra_log() -> None:
    with workspace_tmp_dir() as tmp_path:
        session = HumanVsBotSession(logs_root=tmp_path, bot_mode="heuristic", seed=3)
        manos = {
            "j1": [
                _carta(Figura.REY, Palo.OROS),
                _carta(Figura.CABALLO, Palo.COPAS),
                _carta(Figura.CINCO, Palo.ESPADAS),
                _carta(Figura.CUATRO, Palo.BASTOS),
            ],
            "j2": [
                _carta(Figura.REY, Palo.COPAS),
                _carta(Figura.SOTA, Palo.OROS),
                _carta(Figura.CINCO, Palo.BASTOS),
                _carta(Figura.CUATRO, Palo.ESPADAS),
            ],
            "j3": [
                _carta(Figura.CABALLO, Palo.OROS),
                _carta(Figura.SOTA, Palo.COPAS),
                _carta(Figura.SEIS, Palo.ESPADAS),
                _carta(Figura.CINCO, Palo.COPAS),
            ],
            "j4": [
                _carta(Figura.REY, Palo.ESPADAS),
                _carta(Figura.CABALLO, Palo.BASTOS),
                _carta(Figura.SEIS, Palo.OROS),
                _carta(Figura.CUATRO, Palo.COPAS),
            ],
        }

        session.new_hand(seed=5, manos_iniciales=manos)
        snapshot = session.apply_human_action({"type": "pedir_mus"})

        assert snapshot["active_player"] == "j1"
        assert snapshot["phase"] in {"descarte", "decision_mus", "grande"}
        assert snapshot["bot_actions"]
        log_path = Path(str(snapshot["decision_log_path"]))
        assert log_path.is_file()
        contenido = log_path.read_text(encoding="utf-8")
        assert "web_ui_bot" in contenido
