"""Lanza una UI web local para jugar una mano contra bots."""

from __future__ import annotations

import argparse

from musbot.ui.web_app import create_server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--logs-root", default="data/logs_decisiones/web")
    args = parser.parse_args()

    server = create_server(
        host=args.host,
        port=args.port,
        logs_root=args.logs_root,
    )
    print(f"UI web disponible en http://{args.host}:{args.port}")
    print("Abre esa URL en tu navegador para jugar una mano contra los bots.")
    print("Pulsa Ctrl+C para cerrar el servidor.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
