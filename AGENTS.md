# AGENTS

Estas instrucciones son obligatorias para futuros agentes que trabajen en este repositorio.

- Este proyecto implementa un bot de mus.
- Las reglas oficiales deben venir de `docs/reglas_federacion/`.
- Las reglas ya transformadas a especificacion tecnica deben estar en `docs/reglas_extraidas.md`.
- Si falta una regla, no se debe inventar.
- Toda logica de juego debe tener tests.
- El motor del juego debe estar separado del entorno de reinforcement learning.
- Los agentes no deben modificar directamente el estado de partida; deben elegir acciones legales.
- Las decisiones del bot deben registrarse mediante `analysis/decision_logger.py`.

Reglas de trabajo adicionales:

- Si una regla no esta documentada o es ambigua, dejar un `TODO` explicito en codigo y documentacion.
- Antes de anadir logica compleja, verificar que existe soporte documental en `docs/reglas_federacion/`.
- Priorizar modulos pequenos, testeables y con type hints.
