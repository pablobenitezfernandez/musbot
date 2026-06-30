---
name: entrenar-tabular
description: >-
  Entrena o reanuda un agente tabular Q-learning de musbot (tabular_v1..v5).
  Úsala para lanzar un run nuevo, continuar uno existente (resume) o bifurcar
  (fork) desde un checkpoint, eligiendo episodios, oponente e hiperparámetros.
---

# Entrenar un agente tabular Q-learning

Lanza `scripts/train_agent.py`. La variante recomendada es **`tabular_v5`**
(encoder compacto, epsilon decay 0.995/episodio, learning rate adaptativo
1/(1+n), early stopping por meseta). Recuerda el techo conocido: el tabular **no**
bate al heurístico (~0.47); para fuerza real usa la skill `entrenar-cfr`.

## Comando base

```bash
python scripts/train_agent.py \
  --trainer-version tabular_v5 \
  --episodes 2500 \
  --opponent mixed \
  --evaluation-interval 250 --checkpoint-interval 250 \
  --evaluation-hands 500 \
  --seed 0 \
  --patience 0
```

Si `python` no está en el PATH, usa la ruta completa del intérprete del usuario;
si falla el import de `musbot`, exporta `PYTHONPATH=src`.

## Parámetros clave

- `--trainer-version` `tabular_v1..v5` (lista con `--list-trainers`). Por defecto v5.
- `--episodes` número de episodios. 2000-3000 suele bastar (el espacio v5 es pequeño).
- `--opponent` `random|heuristic|mixed`. `mixed` para generalizar; `heuristic` para
  especializar contra el baseline fuerte.
- `--epsilon` arranque de exploración (por defecto 1.0; decae solo).
- `--patience` early stopping: episodios sin mejora antes de parar. `0` lo desactiva
  (recomendado para comparaciones justas); 300 para runs exploratorios.
- Reanudar: `--resume-run-id run_XXXX` o `--resume-best --trainer-version vX`.
- Bifurcar: `--fork-from-run-id run_XXXX --fork-checkpoint best`.

## Procedimiento

1. Confirma variante, episodios y oponente (pregunta solo si es ambiguo; si no, usa
   v5 / 2500 / mixed).
2. Si el run es largo, lánzalo en segundo plano y luego usa `monitorizar-entrenamiento`.
3. Al terminar, reporta `run_id`, `best_checkpoint` y `best_metric`.
4. Confirma la calidad real con `evaluar-modelo` (≥1000 manos, semilla distinta).

## Salidas

`data/modelos/run_XXXX/` con `config.json`, `state.json`, `metrics.jsonl`
(incluye `epsilon` y `states_visited`), `resumen.md`, `comportamiento*.md`,
`best_checkpoint.json` y `latest_checkpoint.json`.
