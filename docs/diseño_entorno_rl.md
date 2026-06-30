# Diseno del entorno RL

Documento de trabajo para definir el entorno de reinforcement learning sin mezclarlo con
la logica base del motor del juego.

## Observaciones

- `MusEnv` v1 expone observacion desde la perspectiva del jugador activo de un
  equipo controlado.
- La observacion estructurada vive en `src/musbot/env/observaciones.py`.
- Campos principales:
  - `jugador_id`, `equipo_id`, `fase`, `es_mano`
  - cartas propias en orden de mano
  - valores normalizados para mus
  - valores de juego/punto y suma total
  - deteccion automatica de pares y juego
  - marcador y juegos ganados
  - historial publico
  - lance actual y envite pendiente
  - detalle estructurado del `envite_pendiente`:
    - tipo de apuesta
    - cantidad actual
    - cantidad previa
    - valor efectivo de `no_quiero`
    - apostador y equipo apostador
  - `legal_action_ids`, `legal_action_labels`, `action_mask`
- El orden de las cartas propias se preserva porque las acciones de descarte se
  definen por indices.

## Acciones

- El entorno usa un catalogo discreto y estable definido en
  `src/musbot/env/acciones.py`.
- Action space actual:
  - `pasar`
  - `pedir_mus`
  - `cortar_mus`
  - `quiero`
  - `no_quiero`
  - `ordago`
  - `envidar:1` hasta `envidar:40`
  - todos los descartes posibles sobre indices `0..3`
- Las acciones ilegales se filtran con `action_mask`.
- La mascara hace el filtrado contextual:
  - al abrir un lance, solo deja `envidar` con cantidades `>=2`
  - al resubir, permite cantidades adicionales `>=1`
- `TODO`: revisar si conviene ampliar el maximo canonico mas alla de `40` o si
  esa discretizacion ya captura toda la estrategia relevante del juego.

## Recompensas

- En `v1` la recompensa es terminal por mano.
- Componentes actuales:
  - `+1 / -1 / 0` por ganar, perder o empatar la mano desde la perspectiva del
    equipo controlado
  - componente suave `factor_diferencial_piedras * (delta_propio - delta_rival)`
  - bonus opcional por cerrar un juego de `40`
- `TODO`: experimentar con shaping intermedio cuando el espacio de acciones sea
  mas rico y el trainer deje de ser tabular.

## Informacion oculta

- Cartas rivales.
- Informacion parcial del companero.
- El entorno solo expone cartas propias y estado publico derivable del motor.
- Durante la mano no se revelan cartas del rival ni del companero.
- Al cerrar la mano normal se pueden revelar todas las cartas para auditoria del
  tanteo.
- Si se acepta un `ordago`, las cartas se revelan al cerrar ese ordago.

## Self-play

- `MusEnv` v1 controla por defecto al equipo `j1/j3`.
- Los jugadores no controlados se resuelven automaticamente con agentes
  auxiliares, por ahora normalmente `RandomAgent`.
- Esto deja lista la API para pasar despues a self-play real con copias de
  checkpoints.
- En la capa de entrenamiento actual, ademas del baseline aleatorio ya existe
  un baseline `HeuristicAgent`.
- El entrenamiento y la evaluacion aceptan tres modos de rival:
  - `random`
  - `heuristic`
  - `mixed`
- En `self_play`, las plantillas de envite del motor se expanden a un conjunto
  discreto de cantidades candidatas para que los agentes puedan aprender o
  decidir mas alla del minimo implicito.

## Evaluacion

- Baselines contra `RandomAgent`.
- Baselines contra `HeuristicAgent`.
- El catalogo de modelos y familias RL vive en `src/musbot/training/`.
- Hay benchmark reproducible entre familias tabulares mediante
  `scripts/benchmark_trainers.py`.
- `TODO`: anadir evaluacion cruzada entre familias RL y trazas mas ricas para
  analisis de decisiones.
