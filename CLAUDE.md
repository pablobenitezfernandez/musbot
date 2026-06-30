# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`musbot` is a reinforcement learning bot for the Spanish card game **mus**. It is a Python package structured around three separate concerns: the game engine (`core`), the RL training environment (`env` + `training`), and the UI/analysis layer.

## Setup and install

```bash
pip install -e .[dev]   # installs the package + dev dependencies (pytest, ruff)
```

Python 3.11+ is required.

## Common commands

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_motor.py

# Run a single test by name
pytest tests/test_motor.py -k "nombre_del_test"

# Lint and format
ruff check .
ruff format .

# Launch a single game (prints initial state)
python scripts/run_game.py

# Train an RL agent
python scripts/train_agent.py --list-trainers
python scripts/train_agent.py --episodes 50 --opponent mixed
python scripts/train_agent.py --resume-run-id run_0001 --episodes 50
python scripts/train_agent.py --resume-best --trainer-version tabular_v1 --episodes 50
python scripts/train_agent.py --fork-from-run-id run_0001 --fork-checkpoint best --episodes 50

# Evaluate a trained model
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 100
python scripts/evaluate_agent.py --run-id run_0001 --checkpoint best --episodes 100 --opponent heuristic

# List saved model runs
python scripts/list_models.py
python scripts/list_models.py --best-only

# Benchmark trainers (recommended command for serious comparison)
python scripts/benchmark_trainers.py --trainer-versions tabular_v1 tabular_v4 --seeds 0 1 2 --episodes 1000 --evaluation-hands 1000 --training-opponent mixed --evaluation-opponents random heuristic mixed

# Launch web UI (human vs bots at http://127.0.0.1:8000)
python scripts/play_web.py
```

### Monitoring a run in progress (PowerShell)

```powershell
Get-Content .\data\modelos\run_0001\metrics.jsonl -Wait
Get-Content .\data\modelos\run_0001\state.json
Get-Content .\data\modelos\run_0001\resumen.md
Get-Content .\data\modelos\run_0001\comportamiento.md
```

## Architecture

### Core game engine (`src/musbot/core/`)

The engine is strictly separated from the RL environment. The key types are:

- `motor.py` — `MotorMus`: top-level game controller. Owns `iniciar_partida()`, `acciones_legales()`, and state transitions. **Never import the RL env from here.**
- `estado_partida.py` — `EstadoPartida`, `FaseMano`, `LanceMus`, `EnvitePendiente`: immutable-style game state dataclasses.
- `baraja.py` / `cartas.py` — deck and card representation. The deck uses doubles (eight aces, eight kings) and aliasing (3→king, 2→ace).
- `reglas.py` — `RutasReglas`: rule-path resolver. All game logic must trace back to `docs/reglas_federacion/`.
- `puntuacion.py` / `evaluacion.py` — scoring and hand evaluation for all four lances (grande, chica, pares, juego/punto).
- `jugador.py` / `equipo.py` — player and team state.

### RL environment (`src/musbot/env/`)

- `mus_env.py` — `MusEnv`: wraps `MotorMus` for RL. Controls team `j1/j3` by default; uncontrolled players advance automatically via auxiliary agents.
- `acciones.py` — discrete action catalogue: `pasar`, `pedir_mus`, `cortar_mus`, `quiero`, `no_quiero`, `ordago`, `envidar:1..40`, and discard combinations. Action IDs are stable across runs.
- `observaciones.py` — `ObservacionAgente`: structured observation built from public state + own cards. Rivals' cards are never exposed.
- `recompensas.py` — `EsquemaRecompensas`: terminal reward per hand (`±1` win/loss + soft differential component).

### Agents (`src/musbot/agents/`)

All agents extend `BaseAgent` and implement `elegir_accion(acciones_legales, observacion)`. **Agents must never mutate `EstadoPartida` directly.**

- `random_agent.py` — `RandomAgent`: uniform random over legal actions.
- `heuristic_agent.py` — `HeuristicAgent`: rule-based baseline.
- `rl_agent.py` — `RLAgent`: loads a checkpoint from `data/modelos/` and acts greedily.

### Training (`src/musbot/training/`)

- `train.py` — `train()`: main training loop; creates or resumes a `TrainingRunManager` run.
- `experiment_manager.py` — `TrainingRunManager`: manages run directories under `data/modelos/run_*/`, saves checkpoints, config, and state JSON.
- `catalog.py` — `list_model_runs()` / `best_model_run()`: queries saved runs.
- `evaluate.py` — `evaluate()`: runs episodes against a specified opponent and returns `EvaluationResult`.

Training supports three opponent modes: `random`, `heuristic`, `mixed`.

The training loop interleaves training in chunks (gcd of checkpoint/evaluation
intervals) so that periodic evaluation and `best_checkpoint` reflect the agent's
state *at that point*, not the final agent. Features: epsilon decay per episode
(`RLAgent.decay_epsilon`, 0.995/episode down to 0.05; start `epsilon=1.0`),
adaptive learning rate `1/(1+visits)`, early stopping by plateau (`patience`,
default 300 episodes; `patience=0` disables it), and metrics including `epsilon`
and `states_visited` in `metrics.jsonl`. There is **no reward shaping** — the
reward is terminal only (`±1` + soft score differential); the old hidden ordago/
envite penalties in `self_play.py` were removed (they hurt training). The
`_ordago_in_bad_context` / `_aggressive_envite_in_bad_context` helpers remain but
feed `resumir_decisiones` analytics only, never the reward.

Current trainer variant rankings:
- `tabular_v5` — **recommended**; compact 8-dim encoder via `ObservacionAgente.compact_key`
  (~864 theoretical states, ~168 visited). Converges fast and is the most
  interpretable. ~0.62 vs random, ~0.43-0.47 vs heuristic, ~0.53-0.56 vs mixed
  (3-seed benchmark / 1000-hand eval). Roughly tied with v1 on win-rate but far
  simpler and better-conditioned. Enriching the encoder (pares category, juego 31,
  envite amount) was tried and did **not** help — it splits the data over too many
  states. The ceiling (~0.47 vs heuristic) is shared by all tabular variants and is
  a limit of the Monte-Carlo terminal-reward algorithm, not the state encoding.
  Beating it materially needs a different algorithm (TD/Q-learning bootstrap or DQN).
- `tabular_v1` — previous best; larger implicit state space, comparable win-rate to v5
- `tabular_v3` — adds public partner/rival info and history; beats v2 but not v1
- `tabular_v2` — richer envite context; underperforms v1 overall
- `tabular_v4` — compact, per-lance strength profile; most interpretable but below v1

Each run saves to `data/modelos/run_XXXX/` with: `config.json`, `state.json`, `metrics.jsonl`, `resumen.md`, `comportamiento*.md` (one per opponent baseline), `latest_checkpoint.json`, `best_checkpoint.json`, and `checkpoints/episode_*.json`.

### Analysis (`src/musbot/analysis/`)

- `decision_logger.py` — all bot decisions must be logged here (to `data/logs_decisiones/`).
- `explain_decision.py` — human-readable decision explanations.
- `plots.py` — training curves and analysis plots.

### UI (`src/musbot/ui/`)

- `web_app.py` — HTTP server for human vs. bot play; serves `static/human_vs_bot.html`.
- `app_streamlit.py` — Streamlit-based alternative UI.

## Key invariants (from AGENTS.md)

- Game rules must come from `docs/reglas_federacion/` → `docs/reglas_extraidas.md`. If a rule is absent or ambiguous, leave a `TODO` in code and docs; do not invent behavior.
- All game logic must have tests in `tests/`.
- Agents choose from legal actions only; they do not write to `EstadoPartida`.
- Bot decisions must be logged via `analysis/decision_logger.py`.
- Before adding complex logic, verify documentary support exists in `docs/reglas_federacion/`.
- Prefer small, testable modules with type hints.
