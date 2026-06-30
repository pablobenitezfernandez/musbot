# Comandos de Entrenamiento

Guia practica para reproducir los entrenamientos, benchmarks y evaluaciones del
proyecto sin depender de contexto previo.

## Convencion

- Si `python` no esta en tu `PATH`, sustituye `python` por la ruta de tu
  interprete o activa antes tu entorno virtual.
- En PowerShell, si quieres seguir exactamente el estilo usado en este repo,
  puedes ejecutar:

```powershell
python --version
```

o, si necesitas una ruta explicita:

```powershell
& 'C:\ruta\a\python.exe' --version
```

## Preparacion Inicial

Desde la raiz del repo:

```bash
pip install -r requirements.txt
pip install -e .
python -m pytest
python -m ruff check src tests scripts
```

## Ver Que Trainers Hay

```bash
python scripts/train_agent.py --list-trainers
```

## Entrenar Un Run Nuevo

Ejemplo corto:

```bash
python scripts/train_agent.py --trainer-version tabular_v1 --episodes 50 --opponent mixed
```

Ejemplo mas serio:

```bash
python scripts/train_agent.py --trainer-version tabular_v1 --episodes 1000 --opponent mixed --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000
```

## Reanudar Un Run Existente

```bash
python scripts/train_agent.py --resume-run-id run_0011 --episodes 500
```

Reanudar el mejor run conocido de una familia:

```bash
python scripts/train_agent.py --resume-best --trainer-version tabular_v1 --episodes 500
```

## Bifurcar Un Run Desde Un Checkpoint

```bash
python scripts/train_agent.py --fork-from-run-id run_0011 --fork-checkpoint best --episodes 500
```

## Evaluar Un Modelo Guardado

Contra `random`:

```bash
python scripts/evaluate_agent.py --run-id run_0011 --checkpoint best --episodes 1000 --opponent random
```

Contra `heuristic`:

```bash
python scripts/evaluate_agent.py --run-id run_0011 --checkpoint best --episodes 1000 --opponent heuristic
```

Contra `mixed`:

```bash
python scripts/evaluate_agent.py --run-id run_0011 --checkpoint best --episodes 1000 --opponent mixed
```

## Benchmark Reproducible

Comparar varias familias y seeds en una sola orden:

```bash
python scripts/benchmark_trainers.py --trainer-versions tabular_v1 tabular_v4 --seeds 0 1 2 --episodes 1000 --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000 --training-opponent mixed --evaluation-opponents random heuristic mixed
```

Benchmark especifico para medir cambios de recompensa o de estrategia sobre la
familia fuerte actual:

```bash
python scripts/benchmark_trainers.py --trainer-versions tabular_v1 --seeds 0 1 2 --episodes 1000 --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000 --training-opponent mixed --evaluation-opponents random heuristic mixed
```

## Ver Los Runs Que Ya Existen

```bash
python scripts/list_models.py
python scripts/list_models.py --best-only
```

## Seguir La Evolucion En Caliente

Sustituye `run_0011` por el run que te interese:

```powershell
Get-Content .\data\modelos\run_0011\metrics.jsonl -Wait
Get-Content .\data\modelos\run_0011\state.json
Get-Content .\data\modelos\run_0011\resumen.md
Get-Content .\data\modelos\run_0011\comportamiento.md
```

## Donde Mirar Despues

Dentro de `data/modelos/run_XXXX/`:

- `config.json`: parametros de lanzamiento
- `state.json`: estado del run y mejor checkpoint
- `metrics.jsonl`: historico de evaluaciones
- `resumen.md`: resumen humano del progreso
- `comportamiento.md`: fotografia general del estilo del modelo
- `comportamiento_random.md`: estilo contra random
- `comportamiento_heuristic.md`: estilo contra heuristic
- `comportamiento_mixed.md`: estilo contra mixed
- `best_checkpoint.json`: mejor checkpoint
- `latest_checkpoint.json`: ultimo checkpoint

## Receta De Trabajo Recomendada

1. Lanza un benchmark corto para comprobar que todo funciona.
2. Lanza un benchmark serio de `1000` episodios con `mixed`.
3. Mira `comportamiento_mixed.md` para ver si el bot:
   - abusa del ordago
   - mete envites demasiado altos
   - corta demasiado el mus
   - esta perdiendo valor frente a `heuristic`
4. Si el run es bueno, reanudalo.
5. Si el run aprende algo raro, bifurca desde un checkpoint anterior y cambia
   recompensa, rival o trainer.

## Comandos Exactos Usados En Las Ultimas Iteraciones

Reentrenamiento para medir el castigo al ordago:

```powershell
python scripts/benchmark_trainers.py --trainer-versions tabular_v1 --seeds 0 1 2 --episodes 1000 --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000 --training-opponent mixed --evaluation-opponents random heuristic mixed
```

Lo mismo vale para medir el castigo a envites agresivos fuera de contexto.
