---
name: comparar-modelos
description: >-
  Compara variantes de entrenamiento tabular de musbot de forma reproducible:
  entrena cada variante con varias semillas y las evalúa contra los baselines,
  devolviendo un agregado. Úsala para decidir qué variante/hiperparámetros son
  mejores con evidencia, no con una sola corrida.
---

# Comparar modelos (benchmark)

Lanza `scripts/benchmark_trainers.py`. Entrena cada variante con cada semilla bajo
una configuración idéntica y evalúa el **mejor checkpoint** contra los oponentes
indicados. Es la forma correcta de comparar: misma cuenta de episodios, mismas
semillas, mismos oponentes.

## Comando base

```bash
python scripts/benchmark_trainers.py \
  --trainer-versions tabular_v5 tabular_v1 \
  --seeds 0 1 2 \
  --episodes 2000 \
  --evaluation-interval 200 --checkpoint-interval 200 \
  --evaluation-hands 500 \
  --training-opponent mixed \
  --evaluation-opponents random heuristic mixed \
  --patience 0
```

Coste: lineal en `variantes × semillas`. Con 2 variantes × 3 semillas × 2000
episodios son ~9 min. **Lánzalo en segundo plano** si es grande.

## Parámetros clave

- `--trainer-versions` lista de variantes a comparar (`tabular_v1..v5`).
- `--seeds` varias semillas para promediar el ruido (mínimo 3).
- `--patience 0` para que todas entrenen el run completo (comparación justa).
- `--evaluation-opponents` normalmente los tres.

## Importante

- El benchmark cubre **variantes tabulares**. El CFR no entra aquí: entrénalo con
  `entrenar-cfr` y evalúalo con `evaluar-modelo`; luego compara esas cifras a mano
  contra la fila tabular ganadora.
- Reporta el bloque "Agregado" (avg_win_rate por variante y oponente) y nombra la
  ganadora. Recuerda: ningún tabular bate al heurístico; si el objetivo es eso, la
  conclusión es pasar a CFR.

## Salidas

Imprime resultados individuales (por variante/semilla/oponente) y un agregado.
Cada run entrenado queda en `data/modelos/run_XXXX/`.
