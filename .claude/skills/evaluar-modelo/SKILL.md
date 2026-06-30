---
name: evaluar-modelo
description: >-
  Evalúa un modelo entrenado de musbot contra los baselines (random, heuristic,
  mixed) y reporta win_rate. Cubre tanto runs tabulares (por run_id/checkpoint)
  como estrategias CFR (por archivo JSON). Úsala para medir la fuerza real de un
  modelo de forma independiente del entrenamiento.
---

# Evaluar un modelo

Evaluación honesta = muchas manos (≥1000) y **semilla distinta** a la del
entrenamiento. La métrica de selección de checkpoint (pocas manos) es ruidosa;
no la confundas con la calidad real.

## Tabular (run guardado)

```bash
python scripts/evaluate_agent.py \
  --run-id run_XXXX \
  --checkpoint best \
  --episodes 1000 \
  --opponent heuristic
```

- `--checkpoint` `best` o `latest` (o un `episode_*`).
- `--opponent` `random|heuristic|mixed`. Repite por los tres para una foto completa.
- Lista runs disponibles con `python scripts/list_models.py` (`--best-only`).

## CFR (estrategia JSON)

```bash
python scripts/evaluate_cfr.py \
  --strategy data/cfr/strategy.json \
  --episodes 1000 \
  --seed 12345
```

Evalúa de una vez contra `random heuristic mixed` (configurable con `--opponents`).

## Procedimiento

1. Identifica el modelo (run_id tabular o ruta de estrategia CFR).
2. Evalúa con ≥1000 manos contra los tres oponentes.
3. Reporta una tabla: win_rate (y avg_score_diff) por oponente.
4. Compara contra las referencias conocidas:
   - Tabular v5: ~0.62 random, ~0.43-0.47 heuristic, ~0.53 mixed.
   - CFR: debe **superar** al heurístico (>0.47, idealmente >0.52).
5. Si el resultado contradice la métrica de entrenamiento, fíate de esta
   evaluación independiente y dilo.

Si quieres comparar varios modelos de forma sistemática, usa `comparar-modelos`.
