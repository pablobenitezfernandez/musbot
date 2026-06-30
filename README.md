# mus

Proyecto base para desarrollar un bot de mus en Python con una arquitectura modular,
testeable y preparada para evolucionar hacia reinforcement learning sin mezclar capas.

## Objetivo

El proyecto busca:

- Implementar un motor de juego de mus.
- Basar las reglas en documentacion oficial de federacion.
- Evitar suposiciones: si una regla no esta clara, se deja un `TODO` explicito.
- Empezar con agentes simples (`random` y despues `heuristic`).
- Preparar una capa separada para un entorno de reinforcement learning.
- Registrar decisiones del bot para poder auditarlas y analizarlas despues.

## Estado actual

Esta base inicial incluye:

- Estructura de proyecto con `src/` layout.
- Configuracion para `pytest` y `ruff`.
- Modelos basicos de cartas y baraja.
- Evaluadores de `grande`, `chica`, `pares`, `juego` y `punto`.
- Acciones legales base para mus, descartes, paso, envite y ordago.
- Rechazo explicito de envites y ordagos (`no_quiero`) con tanteo de negadas y
  soporte base de resubidas en el motor.
- Interfaz base de agentes y un agente aleatorio.
- Logger de decisiones en formato JSONL.
- Motor base de mano normal:
  - reparto inicial
  - decision de mus
  - descartes
  - lances en orden
  - deteccion automatica de pares/juego/punto
  - tanteo final en orden
- Infraestructura base de entrenamiento RL tabular:
  - runs versionados en `data/modelos/run_XXXX/`
  - checkpoints `latest`, `best` e intermedios
  - reanudacion de entrenamiento
  - bifurcacion de runs desde un checkpoint previo
  - metricas JSONL y `resumen.md` por modelo
- Entorno RL v1:
  - API `reset/step` separada del motor
  - observaciones estructuradas por jugador activo
  - mascara de acciones legales sobre action space discreto
  - envites discretizados por cantidad en el action space
  - recompensa terminal configurable por mano
- Stubs claros para UI, entorno RL completo y capa de arbitraje.

Todavia no se implementa la capa completa de arbitraje federativo
(errores/anulaciones/negadas), ni un entorno RL completo estilo Gym.
La especificacion tecnica viva sigue en `docs/reglas_extraidas.md`.

## Instalacion

Instalacion minima editable:

```bash
pip install -e .
```

Instalacion recomendada para desarrollo:

```bash
pip install -r requirements.txt
```

Si prefieres crear un entorno virtual antes:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Tests

Ejecutar todos los tests:

```bash
python -m pytest
```

Lint y formato con `ruff`:

```bash
python -m ruff check .
python -m ruff format .
```

## Ejecucion

Scripts iniciales disponibles:

```bash
python scripts/run_game.py
python scripts/train_agent.py
python scripts/evaluate_agent.py
python scripts/list_models.py
python scripts/play_web.py
```

Estos scripts son placeholders operativos y dejan claro que faltan reglas verificadas
y logica completa antes de jugar, entrenar o evaluar de verdad.

## UI web local

Hay una UI web ligera para jugar una mano contra bots y ver sus acciones:

```bash
python scripts/play_web.py
```

Despues abre `http://127.0.0.1:8000` en tu navegador.

Esta primera version:

- te pone como jugador `j1`
- deja a `j2`, `j3` y `j4` como bots
- ensena el historial publico y las acciones automáticas del bot
- revela todas las cartas al final de la mano
- guarda un log JSONL de decisiones en `data/logs_decisiones/web/`

Limitacion actual:

- la UI juega una mano interactiva cada vez
- la partida multi-mano completa quedara para una iteracion posterior, cuando el
  motor rote la mano sin cambiar equipos

## Entrenamiento y modelos

El entrenamiento actual usa familias RL tabulares con rivales configurables
(`random`, `heuristic`, `mixed`) para dejar lista la infraestructura de
experimentacion:

```bash
python scripts/train_agent.py --list-trainers
python scripts/train_agent.py --episodes 50
python scripts/train_agent.py --episodes 50 --opponent mixed
python scripts/train_agent.py --episodes 50 --opponent heuristic
python scripts/train_agent.py --resume-run-id run_0001 --episodes 50
python scripts/train_agent.py --resume-best --trainer-version tabular_v1 --episodes 50
python scripts/train_agent.py --fork-from-run-id run_0001 --fork-checkpoint best --episodes 50
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 30
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 30 --opponent heuristic
python scripts/benchmark_trainers.py --episodes 20 --evaluation-hands 20
python scripts/list_models.py
python scripts/list_models.py --best-only
```

Si quieres una guia mas operativa y reproducible de comandos, mira
`docs/comandos_entrenamiento.md`.

## Receta 1000

Comandos recomendados para una comparacion seria con `1000` manos de
entrenamiento y `1000` manos de evaluacion:

```bash
# Entrenar el baseline legacy
python scripts/train_agent.py --trainer-version tabular_v1 --episodes 1000 --opponent mixed --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000

# Entrenar el baseline recomendado hoy
python scripts/train_agent.py --trainer-version tabular_v1 --episodes 1000 --opponent mixed --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000

# Entrenar variantes experimentales
python scripts/train_agent.py --trainer-version tabular_v2 --episodes 1000 --opponent mixed --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000
python scripts/train_agent.py --trainer-version tabular_v3 --episodes 1000 --opponent mixed --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000
python scripts/train_agent.py --trainer-version tabular_v4 --episodes 1000 --opponent mixed --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000

# Ver que runs se han creado y localizar sus run_id
python scripts/list_models.py
python scripts/list_models.py --best-only

# Evaluar un run concreto contra cada baseline con 1000 manos
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 1000 --opponent random
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 1000 --opponent heuristic
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 1000 --opponent mixed

# Benchmark reproducible recomendado hoy entre v1 y v4
python scripts/benchmark_trainers.py --trainer-versions tabular_v1 tabular_v4 --seeds 0 1 2 --episodes 1000 --evaluation-hands 1000 --training-opponent mixed --evaluation-opponents random heuristic mixed
```

Si quieres monitorizar el entrenamiento en caliente, usa la carpeta del run que
te devuelva `train_agent.py`.

## Donde Ver Cada Cosa

- `data/modelos/run_XXXX/config.json`
  Aqui ves con que parametros se lanzo el run: trainer, seed, rival, intervalos
  y notas.
- `data/modelos/run_XXXX/state.json`
  Aqui ves el estado vivo del run: episodios completados, mejor checkpoint,
  ultimo checkpoint y metrica actual.
- `data/modelos/run_XXXX/metrics.jsonl`
  Aqui ves las metricas historicas por bloque de evaluacion:
  - `win_rate`
  - `avg_reward`
  - `avg_score_diff`
- `data/modelos/run_XXXX/resumen.md`
  Aqui tienes un resumen legible de la evolucion del modelo.
- `data/modelos/run_XXXX/comportamiento.md`
  Informe general del checkpoint evaluado: tendencias, frecuencia de acciones,
  envites y patrones aprendidos.
- `data/modelos/run_XXXX/comportamiento_random.md`
- `data/modelos/run_XXXX/comportamiento_heuristic.md`
- `data/modelos/run_XXXX/comportamiento_mixed.md`
  Informes por baseline para ver si un modelo juega agresivo, conservador,
  abusa del ordago, corta mucho el mus o toma malas decisiones de envite.
- `data/modelos/run_XXXX/latest_checkpoint.json`
  Ultimo estado guardado del agente.
- `data/modelos/run_XXXX/best_checkpoint.json`
  Mejor checkpoint del run segun la mejor evaluacion registrada.

En PowerShell puedes seguir las metricas asi:

```powershell
Get-Content .\data\modelos\run_0001\metrics.jsonl -Wait
Get-Content .\data\modelos\run_0001\state.json
Get-Content .\data\modelos\run_0001\resumen.md
Get-Content .\data\modelos\run_0001\comportamiento.md
```

Para comparar modelos ya terminados:

- `python scripts/list_models.py`
  Lista todos los runs guardados.
- `python scripts/list_models.py --best-only`
  Te ayuda a localizar rapido los runs con mejor metrica.
- `python scripts/evaluate_agent.py ...`
  Imprime en terminal el resultado agregado de una evaluacion puntual.
- `python scripts/benchmark_trainers.py ...`
  Imprime resultados individuales y agregados del benchmark en terminal, y
  ademas deja todos los runs generados dentro de `data/modelos/`.

Cada run crea una carpeta en `data/modelos/` con esta estructura:

```text
data/modelos/
  run_0001/
    config.json
    state.json
    metrics.jsonl
    resumen.md
    latest_checkpoint.json
    best_checkpoint.json
    checkpoints/
      episode_000000.json
      episode_000010.json
      ...
```

`resumen.md` documenta la evolucion del modelo, `metrics.jsonl` permite hacer
analisis mas finos o graficas despues, y `comportamiento*.md` te deja auditar
si el modelo esta jugando de forma razonable o si se esta desviando.

Ahora mismo hay cuatro variantes tabulares:

- `tabular_v1`: baseline mas fuerte por ahora en los benchmarks de `1000`
  episodios y opcion recomendada hoy para seguir entrenando.
- `tabular_v2`: variante mas rica en contexto de envites y acciones, pero con
  peor rendimiento agregado que `tabular_v1` en los benchmarks actuales.
- `tabular_v3`: variante experimental que anade informacion publica de
  pareja/rivales e historial resumido; mejora parte de `v2`, pero todavia no
  supera a `v1`.
- `tabular_v4`: variante compacta orientada a fuerza exacta por lance y perfil
  de mano; tras el reset y el reentrenamiento desde cero sigue por debajo de
  `tabular_v1`, aunque deja una base mas interpretable para seguir iterando.

La capa de entrenamiento ya esta separada para poder anadir despues otras
familias como `dqn_v1` o `ppo_v1` sin rehacer el catalogo de modelos ni los
scripts.

Tambien hay tres baselines rivales configurables para entrenamiento y
evaluacion:

- `random`
- `heuristic`
- `mixed`

El siguiente salto natural es conectar nuevas familias RL a `MusEnv` en vez de
depender solo del trainer tabular actual.

## Orden recomendado de desarrollo

1. Anadir el PDF o documento oficial del reglamento en `docs/reglas_federacion/`.
2. Extraer reglas verificadas a `docs/reglas_extraidas.md`.
3. Implementar representacion formal de reglas y acciones legales.
4. Completar el motor del juego sin dependencias del entorno RL.
5. Anadir agentes `random` y `heuristic` sobre acciones legales reales del motor.
6. Expandir el logger de decisiones y la capa de analisis.
7. Hacer crecer el entrenamiento tabular hacia self-play y un entorno RL mas rico.

## Principios del proyecto

- No inventar detalles del reglamento.
- Toda logica de juego debe ser facil de probar.
- Mantener separacion estricta entre motor del juego y entorno RL.
- Registrar decisiones relevantes para poder auditarlas despues.
