# Diario de experimentos

Plantilla ligera para registrar pruebas y decisiones de desarrollo.

## Entrada

- Fecha:
- Objetivo:
- Cambio realizado:
- Fuente de reglas usada:
- Resultado:
- Proximos pasos:

## Entrada 2026-04-30

- Fecha: 2026-04-30
- Objetivo: fijar primeras reglas operativas para seguir construyendo el bot sin
  inventar comportamiento.
- Cambio realizado:
  - Se copio `ReglamentoFEM.9.pdf` a `docs/reglas_federacion/`.
  - Se documento que La Real no vale.
  - Se documento que no se modelara mus visto en esta fase porque se asume que
    nunca se descubre una carta.
  - Se fijo que la decision de mus va en orden de turno y que la decision final
    siempre la toma el jugador activo.
  - Se fijo que por ahora no se modelaran senas ni conversacion libre.
  - Se documento que pares y juego se declaran primero en orden y que, si solo
    un equipo los tiene, se pasa al siguiente lance y se cuenta al final.
  - Se documento que los puntos se muestran al final y no se anuncia antes el
    ganador de cada lance.
- Fuente de reglas usada:
  - `docs/reglas_federacion/ReglamentoFEM.9.pdf`
  - Aclaraciones del usuario sobre la variante objetivo del proyecto
- Resultado: especificacion parcial actualizada en
  `docs/reglas_extraidas.md`.
- Proximos pasos:
  - Anadir referencias de pagina exactas del reglamento.
  - Extraer valores de cartas, jerarquias, tanteo, ordago y condiciones de
    victoria.

## Entrada 2026-04-30-b

- Fecha: 2026-04-30
- Objetivo: aclarar el modelo de tanteo en paso para no mezclarlo con los
  puntos propios de la mano ganadora.
- Cambio realizado:
  - Se documento que el punto en paso se considera correcto.
  - Se documento que en pares y punto los puntos extra pertenecen a la mano
    ganadora del lance y no deben modelarse como puntos del paso.
- Fuente de reglas usada:
  - Aclaracion directa del usuario sobre la variante objetivo del proyecto
- Resultado: `docs/reglas_extraidas.md` refinado para guiar la implementacion
  del tanteo.
- Proximos pasos:
  - Confirmar con el PDF los valores exactos de pares, juego y punto.

## Entrada 2026-04-30-c

- Fecha: 2026-04-30
- Objetivo: extraer del PDF oficial una primera especificacion tecnica util para
  implementar el motor sin inventar reglas.
- Cambio realizado:
  - Se revisaron los articulos del reglamento sobre baraja, mus, envites,
    tanteo, ordago y errores.
  - Se reescribio `docs/reglas_extraidas.md` con referencias por articulo y
    reglas tecnicas accionables.
  - Se consolidaron las reglas confirmadas y se marcaron como `TODO` los huecos
    donde el PDF consultado no explicita aun el detalle suficiente.
- Fuente de reglas usada:
  - `docs/reglas_federacion/ReglamentoFEM.9.pdf`
  - Version visible en portada: `16-02-2025 V.7`
- Resultado:
  - Ya existe una especificacion tecnica inicial para el motor.
  - Siguen pendientes, por falta de explicitud suficiente en lo extraido del
    PDF, la jerarquia completa de grande/chica, el valor numerico exacto para
    juego/punto y el valor detallado de pares.
- Proximos pasos:
  - Ver si esos detalles aparecen en otras paginas, anexos o documentos
    oficiales de la misma federacion.
  - Empezar a convertir las reglas ya confirmadas en modelos y tests del motor.

## Entrada 2026-04-30-d

- Fecha: 2026-04-30
- Objetivo: cerrar las ultimas ambiguedades necesarias para poder programar el
  motor sin inventar jerarquias ni tanteos.
- Cambio realizado:
  - Se confirmo el orden completo de grande.
  - Se confirmo el orden completo de chica.
  - Se confirmo la tabla de valores para sumar juego y punto.
  - Se confirmo el orden completo de juego y de punto.
  - Se fijo que no existe categoria separada de poker; cuatro iguales cuentan
    como duples.
  - Se fijo la jerarquia de duples comparando primero la pareja mayor y despues
    la menor.
  - Se fijaron los valores de pares: `1/2/3`.
  - Se fijo que todos los juegos valen `2` excepto `31`, que vale `3`.
  - Se fijo que en empate exacto gana el primer jugador empatado segun el orden
    de turno desde mano.
  - Se documento el caso normativo de ordago aceptado que no llega a contarse
    porque un lance anterior ya cierra el juego al alcanzar `40` piedras.
- Fuente de reglas usada:
  - Aclaraciones directas del usuario sobre la variante objetivo del proyecto
- Resultado:
  - `docs/reglas_extraidas.md` queda casi completamente programable para el
    motor base.
  - Lo pendiente se reduce sobre todo a decidir el alcance de errores,
    anulaciones y reglas de competicion.
- Proximos pasos:
  - Convertir estas reglas ya fijadas en tipos, evaluadores y tests.

## Entrada 2026-04-30-e

- Fecha: 2026-04-30
- Objetivo: convertir la especificacion tecnica ya fijada en un motor base de
  juego normal sin capa de arbitraje humano.
- Cambio realizado:
  - Se anadieron valores normalizados de cartas y suma para juego/punto.
  - Se implementaron evaluadores puros para grande, chica, pares, juego y
    punto.
  - Se formalizo el estado de partida con fases reales de mano.
  - Se implemento un motor que resuelve:
    - decision de mus
    - descartes
    - lances en orden
    - deteccion automatica de pares/juego/punto
    - tanteo final en orden
    - cierre de juego antes de contar un ordago posterior si ya se alcanza 40
  - Se anadieron tests deterministas para flujo normal y para el ejemplo del
    ordago con tanteo previo.
- Fuente de reglas usada:
  - `docs/reglas_extraidas.md`
  - Aclaraciones directas del usuario sobre la variante objetivo
- Resultado:
  - El repositorio ya tiene un motor base jugable para manos normales y
    legales.
  - La capa de arbitraje, errores y negadas sigue separada y pendiente.
- Proximos pasos:
  - Conectar agentes al motor mediante acciones legales concretas.
  - Completar negadas/rechazos y, si interesa, la capa de arbitraje federativo.

## Entrada 2026-04-30-f

- Fecha: 2026-04-30
- Objetivo: dejar preparada la infraestructura para entrenar, guardar,
  reanudar y comparar varios modelos distintos.
- Cambio realizado:
  - Se amplio la interfaz de agentes para trabajar sobre acciones legales
    concretas del motor.
  - Se implemento un `RLAgent` tabular serializable con politica, epsilon y
    actualizacion incremental.
  - Se anadio un gestor de runs con carpetas `run_XXXX`, checkpoints
    intermedios, `latest`, `best`, `metrics.jsonl` y `resumen.md`.
  - Se anadieron flujos de entrenamiento y evaluacion contra rivales aleatorios.
  - Se anadieron modos de `resume` y `fork` para relanzar entrenamiento desde
    el ultimo checkpoint o desde otro run.
  - Se documentaron comandos base en `README.md`.
- Fuente de reglas usada:
  - Arquitectura y restricciones del propio proyecto
  - Motor base ya implementado en el repositorio
- Resultado:
  - El proyecto ya puede conservar varios modelos con historico de evolucion y
    reanudar su entrenamiento en cualquier momento.
  - La capa de RL sigue siendo minima; sirve para iterar en infraestructura
    antes de pasar a observaciones y recompensas mas ricas.
- Proximos pasos:
  - Sustituir la observacion minima por una codificacion mas informativa.
  - Definir recompensas mejores y ampliar el espacio de decisiones entrenables.
  - Pasar de entrenamiento contra random a self-play real.

## Entrada 2026-04-30-g

- Fecha: 2026-04-30
- Objetivo: permitir elegir mejor entre modelos entrenados y preparar la base
  para convivir con varias familias RL.
- Cambio realizado:
  - Se anadio un registro de familias de entrenamiento con `trainer_version`.
  - Se desacoplo `train/evaluate` del agente tabular concreto.
  - Se anadio un catalogo de runs para listar modelos guardados y detectar el
    mejor segun metrica.
  - Se anadio `scripts/list_models.py`.
  - Se anadio opcion para listar trainers y reanudar el mejor run desde
    `scripts/train_agent.py`.
- Fuente de reglas usada:
  - Arquitectura interna del proyecto
- Resultado:
  - Ya se puede ver que modelos existen, cual parece mejor y seguir
    entrenandolo con mas episodios.
  - Solo hay una familia RL real implementada por ahora, pero la estructura ya
    permite anadir otras sin rehacer los runs existentes.
- Proximos pasos:
  - Implementar `MusEnv` y observaciones/recompensas mas formales.
  - Anadir una segunda familia RL cuando la API del entorno este cerrada.

## Entrada 2026-04-30-h

- Fecha: 2026-04-30
- Objetivo: cerrar una primera API de entorno RL reutilizable por distintas
  familias de entrenamiento.
- Cambio realizado:
  - Se implemento un catalogo canonico de acciones discretas para RL.
  - Se anadio mascara de acciones legales y conversion estable `action_id <->
    accion legal`.
  - Se implemento `MusEnv` con `reset()` y `step()` orientado a controlar un
    equipo completo.
  - Se anadieron observaciones estructuradas del jugador activo y una
    recompensa terminal configurable por mano.
  - Se anadieron tests con flujo real de mano y tanteo terminal.
- Fuente de reglas usada:
  - `docs/reglas_extraidas.md`
  - Motor base ya implementado en el repositorio
- Resultado:
  - El proyecto ya tiene una API de entorno apta para conectar trainers mas
    serios sin mezclar la estrategia con la logica del motor.
  - Queda pendiente pasar de trainer tabular a familias RL mas potentes sobre
    esta nueva interfaz.
- Proximos pasos:
  - Hacer que los trainers usen `MusEnv` directamente.
  - Anadir una segunda familia RL sobre esta API.
  - Definir mejor el shaping de recompensas.

## Entrada 2026-04-30-i

- Fecha: 2026-04-30
- Objetivo: ampliar el motor y el entorno para soportar rechazo de envites y
  ordagos sin dejar ese hueco fuera del espacio RL.
- Cambio realizado:
  - Se anadio la respuesta `no_quiero` como accion legal real del motor.
  - Se implemento cierre de lance por apuesta rechazada.
  - Se anadio tanteo de negada para rechazo simple.
  - Se documento la inferencia tecnica usada para `pares`, `juego` y `punto`
    al rechazar una apuesta.
  - Se amplio el action space del entorno RL para incluir `no_quiero`.
- Fuente de reglas usada:
  - `docs/reglas_extraidas.md`
  - Reglamento FEM, especialmente Art. 49 y Art. 62
- Resultado:
  - El proyecto ya soporta un subconjunto mucho mas util de decisiones de
    apuesta para RL.
  - Siguen pendientes los revoques complejos, respuestas de pareja y negadas
    mas finas de capa federativa.
- Proximos pasos:
  - Meter reenvites de forma controlada.
  - Rehacer los trainers para que aprendan sobre `MusEnv`.

## Entrada 2026-04-30-j

- Fecha: 2026-04-30
- Objetivo: corregir la semantica del `no quiero` para que siga la regla real
  de apuestas previas y resubidas.
- Cambio realizado:
  - Se separaron en el modelo los puntos de apuesta y los puntos propios del
    lance.
  - Se permitio abrir un envite por cualquier cantidad positiva en el motor.
  - Se permitieron resubidas con cantidades adicionales.
  - Se corrigio la regla de `no quiero`:
    - si rechaza la primera apuesta, vale `1`
    - si rechaza una resubida, vale la cantidad que ya estaba en litigio
- Fuente de reglas usada:
  - Aclaracion directa del usuario sobre la variante objetivo
  - Reglamento FEM para el conteo separado de envites y valor del lance
- Resultado:
  - El tanteo del motor ya no mezcla negadas con valor propio de `pares`,
    `juego` o `punto`.
  - El entorno RL sigue limitado a `envidar:2` en su catalogo discreto, aunque
    el motor ya soporte cantidades arbitrarias.
- Proximos pasos:
  - Expandir el action space discreto para cantidades de envite mas ricas.
  - Conectar los trainers al nuevo flujo de apuestas del entorno.

## Entrada 2026-04-30-k

- Fecha: 2026-04-30
- Objetivo: cerrar discrepancias entre la especificacion tecnica y el alcance
  real del motor/entorno.
- Cambio realizado:
  - Se fijo que el corte de mus de esta v1 es secuencial por turno, como ya
    modela el motor.
  - Se excluyeron del alcance actual las respuestas de pareja en singular/plural
    y los revoques por companero.
  - Se aclaro la politica de revelacion de cartas:
    - al final de la mano normal, tras completar las cuatro fases
    - tambien tras un ordago aceptado
- Fuente de reglas usada:
  - Aclaraciones directas del usuario sobre la variante objetivo
- Resultado:
  - La documentacion ya refleja mejor el comportamiento real que estamos
    entrenando y testeando.
- Proximos pasos:
  - Enriquecer la observacion RL del `envite_pendiente` para que el agente vea
    mejor aperturas, resubidas y coste real del `no quiero`.

## Entrada 2026-04-30-l

- Fecha: 2026-04-30
- Objetivo: mejorar la observacion RL de apuestas sin tocar la logica del motor.
- Cambio realizado:
  - Se mantuvo `envite_pendiente` como resumen legible.
  - Se anadio un detalle estructurado con:
    - tipo de apuesta
    - cantidad actual
    - cantidad previa
    - valor efectivo de `no_quiero`
    - jugador y equipo apostador
    - banderas para distinguir si es resubida y si al jugador observado le toca
      responder
- Fuente de reglas usada:
  - Aclaraciones del usuario sobre aperturas, resubidas y negadas
  - `docs/reglas_extraidas.md`
- Resultado:
  - El entorno RL ya puede distinguir mejor entre una apertura y una resubida,
    que era la principal carencia para aprender decisiones de apuesta.
- Proximos pasos:
  - Empezar a usar este detalle dentro de politicas heuristicas o RL mas ricas.

## Entrada 2026-04-30-m

- Fecha: 2026-04-30
- Objetivo: mejorar de verdad la familia RL tabular sin romper compatibilidad
  con runs anteriores.
- Cambio realizado:
  - Se mantuvo `tabular_v1` como variante legacy.
  - Se anadio `tabular_v2` como nueva familia recomendada.
  - `tabular_v2` usa una clave de estado mas rica con:
    - contexto de envite y resubida
    - rol del jugador frente a la apuesta
    - posicion en el turno
    - presion de cierre de juego
    - contexto de acciones legales
    - resumen mas util de cartas y juego/punto
  - La actualizacion tabular paso de suma acumulativa simple a una forma
    estable de aproximacion hacia la recompensa final, con conteo de visitas.
  - Los nuevos runs pasan a usar `tabular_v2` por defecto.
- Fuente de reglas usada:
  - Observacion estructurada del entorno RL
  - Aclaraciones del usuario sobre envites, negadas y flujo de la mano
- Resultado:
  - El agente ya puede distinguir mejor situaciones estrategicamente distintas
    que antes colapsaban en la misma clave tabular.
- Proximos pasos:
  - Empezar a comparar `tabular_v1` y `tabular_v2` con runs reales.

## Entrada 2026-04-30-n

- Fecha: 2026-04-30
- Objetivo: completar el siguiente bloque practico para que el proyecto ya
  pueda avanzar con baselines mas utiles y comparaciones reproducibles.
- Cambio realizado:
  - Se implemento `HeuristicAgent` como baseline determinista mejor que random.
  - Se mejoro `self_play` para expandir plantillas de envite a cantidades
    concretas durante entrenamiento y evaluacion.
  - Se anadieron rivales configurables `random`, `heuristic` y `mixed`.
  - Se creo benchmark reproducible para comparar `tabular_v1` contra
    `tabular_v2`.
- Resultado:
  - El proyecto ya no depende solo de `RandomAgent` para entrenar o evaluar.
  - `tabular_v1` y `tabular_v2` se pueden comparar sin montar pruebas manuales.
- Proximos pasos:
  - Lanzar benchmarks reales con varias seeds.
  - Revisar si `tabular_v2` gana de forma consistente y ajustar heuristicas si
    el baseline rival queda demasiado debil o demasiado fuerte.

## Entrada 2026-04-30-o

- Fecha: 2026-04-30
- Objetivo: dejar una receta operativa clara para entrenar, evaluar y comparar
  modelos sin depender de memoria o instrucciones sueltas del chat.
- Cambio realizado:
  - Se documento en `README.md` una bateria recomendada de comandos con `1000`
    manos para:
    - entrenamiento
    - evaluacion por baseline
    - benchmark `tabular_v1` vs `tabular_v2`
  - Se documento tambien donde mirar:
    - `config.json`
    - `state.json`
    - `metrics.jsonl`
    - `resumen.md`
    - checkpoints
- Resultado:
  - El proyecto ya tiene una receta reproducible de uso practico para comparar
    modelos y seguir su evolucion.

## Entrada 2026-04-30-p

- Fecha: 2026-04-30
- Objetivo: ejecutar el primer benchmark serio `tabular_v1` vs `tabular_v2`
  con `1000` manos de entrenamiento y `1000` de evaluacion por baseline.
- Configuracion:
  - trainers: `tabular_v1`, `tabular_v2`
  - seeds: `0`, `1`, `2`
  - rival de entrenamiento: `mixed`
  - rivales de evaluacion: `random`, `heuristic`, `mixed`
  - episodios de entrenamiento por run: `1000`
  - manos de evaluacion por baseline: `1000`
- Runs generados:
  - `run_0001 = tabular_v1, seed 0`
  - `run_0002 = tabular_v1, seed 1`
  - `run_0003 = tabular_v1, seed 2`
  - `run_0004 = tabular_v2, seed 0`
  - `run_0005 = tabular_v2, seed 1`
  - `run_0006 = tabular_v2, seed 2`
- Resultado agregado:
  - `tabular_v1 vs random`:
    - `avg_win_rate = 0.569`
    - `avg_reward = 0.140`
    - `avg_score_diff = 11.719`
  - `tabular_v1 vs heuristic`:
    - `avg_win_rate = 0.476`
    - `avg_reward = -0.011`
    - `avg_score_diff = -4.845`
  - `tabular_v1 vs mixed`:
    - `avg_win_rate = 0.558`
    - `avg_reward = 0.128`
    - `avg_score_diff = 6.226`
  - `tabular_v2 vs random`:
    - `avg_win_rate = 0.517`
    - `avg_reward = 0.035`
    - `avg_score_diff = 2.937`
  - `tabular_v2 vs heuristic`:
    - `avg_win_rate = 0.441`
    - `avg_reward = -0.071`
    - `avg_score_diff = -5.625`
  - `tabular_v2 vs mixed`:
    - `avg_win_rate = 0.500`
    - `avg_reward = 0.016`
    - `avg_score_diff = 0.069`
- Conclusiones:
  - En este benchmark inicial, `tabular_v1` supero a `tabular_v2` en los tres
    baselines de evaluacion.
  - La hipotesis inmediata es que `tabular_v2` esta sufriendo mas dispersion del
    espacio de estados y necesita simplificar su representacion, mas episodios o
    una actualizacion mejor.
- Proximos pasos:
  - Revisar y simplificar la clave de estado de `tabular_v2`.
  - Repetir benchmark con una variante `v2b` o con mas entrenamiento.

## Entrada 2026-04-30-q

- Fecha: 2026-04-30
- Objetivo: enriquecer la observacion publica del RL, crear una tercera
  variante tabular y dejar informes de comportamiento legibles por modelo.
- Cambio realizado:
  - Se ampliaron las observaciones RL con informacion publica resumida:
    - conteo de pares por equipo
    - conteo de juego por equipo
    - ultimo evento publico
    - numero total de eventos publicos
  - Se anadio `tabular_v3` para aprovechar mejor:
    - informacion publica de pareja y rivales
    - historial resumido
    - detalle mas comprimido de pares y contexto de envite
  - Se anadio generacion automatica de informes:
    - `comportamiento.md`
    - `comportamiento_random.md`
    - `comportamiento_heuristic.md`
    - `comportamiento_mixed.md`
  - Los informes incluyen:
    - metricas del checkpoint evaluado
    - frecuencias de acciones
    - tendencia de envites
    - acciones por fase
    - patrones aprendidos de la politica tabular
- Resultado:
  - Cada run ya guarda no solo metricas, sino tambien una lectura humana del
    estilo de juego del modelo.
  - Esto permite detectar si el agente:
    - corta demasiado el mus
    - ordaguea en exceso
    - acepta o rechaza demasiado
    - apuesta cantidades raras o poco consistentes

## Entrada 2026-04-30-r

- Fecha: 2026-04-30
- Objetivo: reentrenar y comparar `tabular_v1`, `tabular_v2` y `tabular_v3`
  con la misma receta de `1000` episodios y `1000` manos de evaluacion.
- Configuracion:
  - trainers: `tabular_v1`, `tabular_v2`, `tabular_v3`
  - seeds: `0`, `1`, `2`
  - rival de entrenamiento: `mixed`
  - rivales de evaluacion: `random`, `heuristic`, `mixed`
  - episodios de entrenamiento por run: `1000`
  - manos de evaluacion por baseline: `1000`
- Runs generados:
  - `run_0007 = tabular_v1, seed 0`
  - `run_0008 = tabular_v1, seed 1`
  - `run_0009 = tabular_v1, seed 2`
  - `run_0010 = tabular_v2, seed 0`
  - `run_0011 = tabular_v2, seed 1`
  - `run_0012 = tabular_v2, seed 2`
  - `run_0013 = tabular_v3, seed 0`
  - `run_0014 = tabular_v3, seed 1`
  - `run_0015 = tabular_v3, seed 2`
- Resultado agregado:
  - `tabular_v1 vs random`:
    - `avg_win_rate = 0.569`
    - `avg_reward = 0.140`
    - `avg_score_diff = 11.719`
  - `tabular_v1 vs heuristic`:
    - `avg_win_rate = 0.476`
    - `avg_reward = -0.011`
    - `avg_score_diff = -4.845`
  - `tabular_v1 vs mixed`:
    - `avg_win_rate = 0.558`
    - `avg_reward = 0.128`
    - `avg_score_diff = 6.226`
  - `tabular_v2 vs random`:
    - `avg_win_rate = 0.517`
    - `avg_reward = 0.035`
    - `avg_score_diff = 2.937`
  - `tabular_v2 vs heuristic`:
    - `avg_win_rate = 0.441`
    - `avg_reward = -0.071`
    - `avg_score_diff = -5.625`
  - `tabular_v2 vs mixed`:
    - `avg_win_rate = 0.500`
    - `avg_reward = 0.016`
    - `avg_score_diff = 0.069`
  - `tabular_v3 vs random`:
    - `avg_win_rate = 0.502`
    - `avg_reward = 0.006`
    - `avg_score_diff = 0.889`
  - `tabular_v3 vs heuristic`:
    - `avg_win_rate = 0.452`
    - `avg_reward = -0.059`
    - `avg_score_diff = -5.227`
  - `tabular_v3 vs mixed`:
    - `avg_win_rate = 0.518`
    - `avg_reward = 0.050`
    - `avg_score_diff = 2.054`
- Conclusiones:
  - `tabular_v1` sigue siendo el baseline mas fuerte del proyecto.
  - `tabular_v3` mejora parcialmente a `tabular_v2` frente a `heuristic` y
    `mixed`, pero todavia no alcanza a `tabular_v1`.
  - `tabular_v2` y `tabular_v3` parecen sufrir mas dispersion del espacio de
    estados y necesitan mas simplificacion o una familia RL distinta.
- Decisiones posteriores:
  - Se deja `tabular_v1` como trainer por defecto para nuevos runs.
  - `tabular_v2` y `tabular_v3` quedan como variantes experimentales para
    seguir iterando sin perder comparabilidad.

## Entrada 2026-04-30-s

- Fecha: 2026-04-30
- Objetivo: abrir una via rapida para jugar contra el bot desde navegador y
  observar sus decisiones durante una mano real.
- Cambio realizado:
  - Se anadio una UI web local en `src/musbot/ui/web_app.py`.
  - Se anadio un HTML servido por Python en
    `src/musbot/ui/static/human_vs_bot.html`.
  - Se anadio el script `scripts/play_web.py` para arrancar el servidor local.
  - La UI:
    - pone al humano en `j1`
    - deja `j2`, `j3` y `j4` como bots
    - muestra acciones legales del humano
    - autojuega los turnos de bots
    - enseña el historial publico
    - enseña las acciones que toman los bots
    - revela todas las cartas al final de la mano
  - Se integra `DecisionLogger` para guardar un JSONL por sesion en
    `data/logs_decisiones/web/`.
- Resultado:
  - Ya se puede inspeccionar visualmente si el bot:
    - corta mus raro
    - envida demasiado
    - usa mucho ordago
    - responde mal a envites
  - La primera version queda centrada en una mano interactiva; la partida
    multi-mano se dejara para una iteracion posterior del motor.

## Entrada 2026-04-30-t

- Fecha: 2026-04-30
- Objetivo: traducir una mano humana bien jugada a mejoras concretas del
  baseline y reiniciar el entrenamiento desde cero.
- Lectura estrategica de la mano:
  - La mano del humano fue fuerte y coherente:
    - `grande` muy alta
    - `chica` floja
    - `pares` simples altos
    - `31` en juego
  - La linea:
    - cortar mus
    - presionar `grande`
    - pasar `chica`
    - presionar `pares`
    - presionar `juego`
    se considero razonable y util como referencia de producto.
- Cambio realizado:
  - Se anadieron fuerzas relativas exactas por lance a la observacion RL:
    - `fuerza_grande`
    - `fuerza_chica`
    - `fuerza_pares`
    - `fuerza_juego`
    - `fuerza_punto`
  - Se mejoro `HeuristicAgent` para usar:
    - fuerza exacta de pares simples altos
    - fuerza exacta de grande/chica
    - mejor calibracion de apertura y respuesta a envites
  - Se anadio `tabular_v4`:
    - estado mas compacto
    - fuerza real del lance actual
    - perfil de mano mas interpretable
    - menos ruido que `v2`/`v3`
  - Se borraron los runs anteriores de `data/modelos/` para reiniciar desde
    cero.
- Resultado:
  - El repositorio quedo listo para un benchmark limpio nuevo empezando otra
    vez en `run_0001`.

## Entrada 2026-04-30-u

- Fecha: 2026-04-30
- Objetivo: reentrenar desde cero el baseline actual fuerte (`tabular_v1`) y
  la variante nueva (`tabular_v4`) con la misma receta de `1000` episodios.
- Configuracion:
  - trainers: `tabular_v1`, `tabular_v4`
  - seeds: `0`, `1`, `2`
  - rival de entrenamiento: `mixed`
  - rivales de evaluacion: `random`, `heuristic`, `mixed`
  - episodios de entrenamiento por run: `1000`
  - manos de evaluacion por baseline: `1000`
- Runs generados:
  - `run_0001 = tabular_v1, seed 0`
  - `run_0002 = tabular_v1, seed 1`
  - `run_0003 = tabular_v1, seed 2`
  - `run_0004 = tabular_v4, seed 0`
  - `run_0005 = tabular_v4, seed 1`
  - `run_0006 = tabular_v4, seed 2`
- Resultado agregado:
  - `tabular_v1 vs random`:
    - `avg_win_rate = 0.564`
    - `avg_reward = 0.128`
    - `avg_score_diff = 10.862`
  - `tabular_v1 vs heuristic`:
    - `avg_win_rate = 0.479`
    - `avg_reward = 0.001`
    - `avg_score_diff = -3.042`
  - `tabular_v1 vs mixed`:
    - `avg_win_rate = 0.544`
    - `avg_reward = 0.104`
    - `avg_score_diff = 4.943`
  - `tabular_v4 vs random`:
    - `avg_win_rate = 0.511`
    - `avg_reward = 0.024`
    - `avg_score_diff = 3.195`
  - `tabular_v4 vs heuristic`:
    - `avg_win_rate = 0.441`
    - `avg_reward = -0.082`
    - `avg_score_diff = -4.781`
  - `tabular_v4 vs mixed`:
    - `avg_win_rate = 0.494`
    - `avg_reward = 0.004`
    - `avg_score_diff = 0.381`
- Conclusiones:
  - El cambio conceptual de `v4` es mejor y mas interpretable, pero en esta
    primera iteracion sigue sin superar a `tabular_v1`.
  - `tabular_v1` continua siendo el mejor modelo disponible para seguir
    entrenando hoy.
  - La mejora mas prometedora no parece ser meter mas estado sin mas, sino
    seguir compactando la representacion o saltar a una familia no tabular.

## Entrada 2026-04-30-v

- Fecha: 2026-04-30
- Objetivo: ensenar al baseline tabular que el `ordago` frecuente no siempre
  compensa, penalizando especialmente los ordagos lanzados fuera de contexto.
- Cambios realizados:
  - El entrenamiento dejo de usar una recompensa puramente binaria por mano.
  - `self_play` paso a usar una recompensa terminal mas rica:
    - victoria o derrota de mano
    - diferencial de piedras
    - bonus o penalizacion por cerrar o perder juego
  - Se anadio una penalizacion base por lanzar `ordago`.
  - Se anadio una penalizacion adicional cuando el `ordago` aparece en un mal
    contexto:
    - lejos del cierre
    - sin fuerza alta en el lance actual
  - Se expuso una nueva metrica de comportamiento:
    - `ordago_bad_context_rate`
- Referencia anterior:
  - `run_0003` contra `mixed`:
    - `win_rate = 0.524`
    - `avg_score_diff = 4.408`
    - `ordago_rate = 0.186`
    - `ordago_bad_context_rate = 0.920`
- Primera iteracion de ajuste:
  - Runs: `run_0007`, `run_0008`, `run_0009`
  - Efecto:
    - bajo el `ordago_rate` en parte
    - pero los ordagos restantes seguian apareciendo mayoritariamente en mal
      contexto
  - Ejemplos frente a `mixed`:
    - `run_0007`: `ordago_rate = 0.061`,
      `ordago_bad_context_rate = 0.945`
    - `run_0008`: `ordago_rate = 0.145`,
      `ordago_bad_context_rate = 0.956`
    - `run_0009`: `ordago_rate = 0.138`,
      `ordago_bad_context_rate = 0.969`
- Segunda iteracion, penalizacion reforzada:
  - Runs: `run_0010`, `run_0011`, `run_0012`
  - Configuracion:
    - trainer: `tabular_v1`
    - seeds: `0`, `1`, `2`
    - rival de entrenamiento: `mixed`
    - episodios por run: `1000`
    - evaluacion: `1000` manos contra `random`, `heuristic` y `mixed`
  - Resultado agregado:
    - `vs random`:
      - `avg_win_rate = 0.593`
      - `avg_reward = 1.079`
      - `avg_score_diff = 22.485`
    - `vs heuristic`:
      - `avg_win_rate = 0.414`
      - `avg_reward = -0.527`
      - `avg_score_diff = -4.326`
    - `vs mixed`:
      - `avg_win_rate = 0.523`
      - `avg_reward = 0.198`
      - `avg_score_diff = 6.891`
  - Comportamiento frente a `mixed`:
    - `run_0010`:
      - `ordago_rate = 0.067`
      - `ordago_bad_context_rate = 0.998`
    - `run_0011`:
      - `ordago_rate = 0.022`
      - `ordago_bad_context_rate = 0.973`
    - `run_0012`:
      - `ordago_rate = 0.031`
      - `ordago_bad_context_rate = 0.874`
- Conclusiones:
  - La penalizacion reforzada si ha servido para reducir mucho la frecuencia de
    `ordago`.
  - El salto mas claro se ve comparando `run_0003` con `run_0011`:
    - `ordago_rate`: `0.186 -> 0.022`
  - Aun no se ha resuelto del todo el problema importante:
    - cuando el modelo lanza los pocos ordagos que le quedan, sigue haciendolo
      demasiadas veces en mal contexto
  - La agresividad se esta desplazando a envites altos normales:
    - por ejemplo `run_0011` frente a `mixed` tiene `envite_rate = 0.686`
  - El mejor resultado de esta iteracion no es "ya entiende bien el ordago",
    sino "ya no lo spamea, pero todavia no lo selecciona con suficiente
    criterio".

## Entrada 2026-04-30-w

- Fecha: 2026-04-30
- Objetivo: frenar no solo el `ordago` flojo, sino tambien los envites altos
  desproporcionados fuera de contexto.
- Cambios realizados:
  - Se anadio penalizacion especifica a `envidar` cuando:
    - la cantidad es alta
    - no hay cierre cercano
    - la fuerza del lance actual no es alta
  - Se anadieron metricas nuevas:
    - `aggressive_envite_bad_context_rate`
    - `avg_aggressive_envite_amount`
  - Se creo `docs/comandos_entrenamiento.md` con recetas reproducibles para:
    - instalar
    - entrenar
    - reanudar
    - bifurcar
    - evaluar
    - benchmarkear
    - seguir metricas en caliente
- Referencia previa usada para comparar:
  - `run_0011` reevaluado contra `mixed` con el analizador nuevo:
    - `win_rate = 0.500`
    - `avg_score_diff = 8.743`
    - `ordago_rate = 0.022`
    - `aggressive_envite_bad_context_rate = 0.764`
    - `avg_aggressive_envite_amount = 24.862`
- Comando usado:
  - `python scripts/benchmark_trainers.py --trainer-versions tabular_v1 --seeds 0 1 2 --episodes 1000 --checkpoint-interval 100 --evaluation-interval 100 --evaluation-hands 1000 --training-opponent mixed --evaluation-opponents random heuristic mixed`
- Runs generados:
  - `run_0013 = tabular_v1, seed 0`
  - `run_0014 = tabular_v1, seed 1`
  - `run_0015 = tabular_v1, seed 2`
- Resultado agregado:
  - `vs random`:
    - `avg_win_rate = 0.548`
    - `avg_reward = -0.553`
    - `avg_score_diff = 12.364`
  - `vs heuristic`:
    - `avg_win_rate = 0.384`
    - `avg_reward = -0.932`
    - `avg_score_diff = -2.302`
  - `vs mixed`:
    - `avg_win_rate = 0.483`
    - `avg_reward = -0.642`
    - `avg_score_diff = 6.496`
- Comportamiento frente a `mixed`:
  - `run_0013`:
    - `ordago_rate = 0.170`
    - `aggressive_envite_bad_context_rate = 0.731`
    - `avg_aggressive_envite_amount = 14.259`
  - `run_0014`:
    - `ordago_rate = 0.066`
    - `aggressive_envite_bad_context_rate = 0.787`
    - `avg_aggressive_envite_amount = 13.356`
  - `run_0015`:
    - `ordago_rate = 0.006`
    - `aggressive_envite_bad_context_rate = 0.752`
    - `avg_aggressive_envite_amount = 22.664`
- Conclusiones:
  - El cambio si reduce el tamano medio de varios envites altos en algunos
    runs, sobre todo `run_0014`.
  - No ha resuelto bien el criterio de contexto:
    - el ratio de envites altos en mal contexto sigue muy alto
  - El coste en rendimiento ha sido claro:
    - cae la `avg_reward`
    - cae el `win_rate` medio frente a `mixed` y `heuristic`
  - La penalizacion nueva ha movido el estilo, pero por ahora parece demasiado
    dura o demasiado ciega.
  - A corto plazo, la leccion no es "ya sabe envidar mejor", sino "hemos
    detectado una senal util, pero necesita una calibracion mas fina".
