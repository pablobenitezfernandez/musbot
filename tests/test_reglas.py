from musbot.core.reglas import RutasReglas
from tests._tmp_utils import workspace_tmp_dir


def test_reglamento_oficial_no_cuenta_gitkeep() -> None:
    rutas = RutasReglas()

    with workspace_tmp_dir() as tmp_path:
        reglamento_dir = tmp_path / rutas.directorio_reglamento_oficial
        reglamento_dir.mkdir(parents=True)
        (reglamento_dir / ".gitkeep").write_text("", encoding="utf-8")

        assert rutas.reglamento_oficial_disponible(tmp_path) is False


def test_reglamento_oficial_detecta_archivo_real() -> None:
    rutas = RutasReglas()

    with workspace_tmp_dir() as tmp_path:
        reglamento_dir = tmp_path / rutas.directorio_reglamento_oficial
        reglamento_dir.mkdir(parents=True)
        (reglamento_dir / "reglamento.pdf").write_text("pdf-placeholder", encoding="utf-8")

        assert rutas.reglamento_oficial_disponible(tmp_path) is True
