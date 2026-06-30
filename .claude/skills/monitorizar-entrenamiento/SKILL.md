---
name: monitorizar-entrenamiento
description: >-
  Sigue y resume el progreso de un entrenamiento de musbot en marcha (tabular o
  CFR): curva de win_rate, epsilon, estados visitados y si está mejorando o en
  meseta. Úsala para decidir si dejar correr, parar pronto o ajustar.
---

# Monitorizar un entrenamiento

## Tabular (run en `data/modelos/run_XXXX/`)

Sigue las métricas en vivo (PowerShell):

```powershell
Get-Content .\data\modelos\run_XXXX\metrics.jsonl -Wait
Get-Content .\data\modelos\run_XXXX\state.json
Get-Content .\data\modelos\run_XXXX\resumen.md
Get-Content .\data\modelos\run_XXXX\comportamiento.md
```

Cada línea de `metrics.jsonl` trae `episode`, `win_rate`, `avg_reward`,
`avg_score_diff`, `epsilon` y `states_visited`.

## CFR (proceso/log)

Si lo lanzaste con `entrenar-cfr` redirigiendo a un log, sigue ese archivo; el
script imprime por intervalo: `iter`, `infosets` y win_rate vs los tres oponentes.

## Qué mirar (diagnóstico)

- **Aprende**: `win_rate` sube y `avg_score_diff` mejora con las iteraciones.
- **Exploración (tabular)**: `epsilon` debe decaer hacia 0.05; si sigue alto, faltan
  episodios.
- **Cobertura (tabular)**: `states_visited` se estabiliza (~168 en v5). Si crece sin
  parar, el encoder es demasiado fino y reparte mal los datos.
- **Meseta**: si `win_rate` no mejora en muchas evaluaciones seguidas, considera
  parar (early stopping) o cambiar de enfoque.
- **CFR**: el win_rate vs `heuristic` debería cruzar ~0.47 (techo tabular) pronto;
  si no, revisa la abstracción o sube iteraciones.

## Procedimiento

1. Localiza el run/log (último `data/modelos/run_*` o el log del CFR).
2. Lee las últimas métricas y describe la tendencia en 2-3 frases.
3. Recomienda: seguir, parar, o ajustar (episodios/iteraciones/oponente).
4. No bloquees esperando: lee el estado actual y reporta; vuelve a consultar luego.
