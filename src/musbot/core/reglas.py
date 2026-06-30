"""Puntos de entrada para reglas verificadas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RutasReglas:
    """Ubicaciones esperadas para reglamento oficial y especificacion tecnica."""

    directorio_reglamento_oficial: Path = Path("docs/reglas_federacion")
    archivo_reglas_extraidas: Path = Path("docs/reglas_extraidas.md")

    def reglamento_oficial_disponible(self, base_dir: Path | None = None) -> bool:
        """Indica si hay algun archivo real de reglamento cargado en el repositorio."""

        raiz = base_dir if base_dir is not None else Path(".")
        directorio = raiz / self.directorio_reglamento_oficial
        if not directorio.exists() or not directorio.is_dir():
            return False

        return any(path.is_file() and path.name != ".gitkeep" for path in directorio.iterdir())

    def especificacion_tecnica_disponible(self, base_dir: Path | None = None) -> bool:
        """Indica si existe el documento de reglas extraidas."""

        raiz = base_dir if base_dir is not None else Path(".")
        return (raiz / self.archivo_reglas_extraidas).is_file()


def cargar_reglas_verificadas() -> None:
    """Placeholder para futura carga de reglas verificadas.

    TODO: parsear `docs/reglas_extraidas.md` o una fuente estructurada equivalente
    una vez exista una extraccion fiable del reglamento oficial.
    """

    raise NotImplementedError(
        "TODO: cargar reglas verificadas desde docs/reglas_federacion/ y docs/reglas_extraidas.md."
    )
