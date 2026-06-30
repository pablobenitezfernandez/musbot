---
name: entrenar-cfr
description: >-
  Entrena una estrategia de mus por MCCFR (Counterfactual Regret Minimization),
  el modelo recomendado por fuerza de juego: estrategia aleatorizada de
  información imperfecta que supera al heurístico. Úsala cuando interese el bot
  más fuerte, no solo iterar sobre tabular.
---

# Entrenar una estrategia CFR (MCCFR)

Lanza `scripts/train_cfr.py`. Entrena por external-sampling MCCFR sobre las
apuestas (grande/chica/pares/juego/punto); la fase de mus se corta siempre y el
pago es el diferencial de piedras (suma cero). Guarda la **estrategia media**.

## Comando base

```bash
python scripts/train_cfr.py \
  --iterations 6000 \
  --seed 0 \
  --eval-interval 1500 \
  --eval-hands 500 \
  --output data/cfr/strategy.json
```

Coste aproximado: ~0.2 s/iteración (las 4 posiciones por iteración). 6000
iteraciones ≈ 17 min. **Lánzalo en segundo plano** y sigue el log; no bloquees.

## Parámetros clave

- `--iterations` iteraciones de MCCFR. Más iteraciones → estrategia más afinada
  (rendimientos decrecientes). 4000-10000 es un buen rango.
- `--eval-interval` cada cuántas iteraciones evalúa e imprime win_rate vs los tres
  oponentes (sirve para ver la curva de mejora).
- `--eval-hands` manos por evaluación intermedia.
- `--output` ruta de la estrategia JSON (por defecto `data/cfr/strategy.json`).

## Procedimiento

1. Acuerda iteraciones (por defecto 6000) y semilla.
2. Lanza en segundo plano y monitoriza el log: el win_rate vs `heuristic` debería
   superar ~0.47 (techo tabular) ya en pocas miles de iteraciones.
3. Al terminar, confirma con `evaluar-modelo --cfr` usando ≥1000 manos y semilla
   distinta a la de entrenamiento.
4. Reporta iteraciones, nº de information sets y la tabla de win_rate.

## Salidas

`data/cfr/strategy.json` con `{version, policy, iterations}`. La política mapea
cada information set a una distribución sobre acciones abstractas
(`pasar`, `quiero`, `no_quiero`, `ordago`, `envidar_chico`, `envidar_grande`).
El `CFRAgent` la carga para jugar y el UI web puede usarla con `bot_mode="cfr"`.
