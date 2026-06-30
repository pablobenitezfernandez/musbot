from __future__ import annotations

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


@contextmanager
def workspace_tmp_dir() -> Iterator[Path]:
    raiz = Path(".test_artifacts")
    raiz.mkdir(exist_ok=True)
    directorio = raiz / str(uuid4())
    directorio.mkdir()

    try:
        yield directorio
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
        try:
            raiz.rmdir()
        except OSError:
            pass
