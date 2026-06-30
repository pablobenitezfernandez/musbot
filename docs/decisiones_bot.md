# Auditoria de decisiones del bot

Usa este documento para definir el formato, criterios de revision y ejemplos de auditoria
de decisiones registradas por el bot.

## Campos minimos

- `partida_id`
- `mano_id`
- `jugador_id`
- `fase`
- `cartas_propias`
- `marcador`
- `historial_publico`
- `acciones_legales`
- `accion_elegida`
- `probabilidades_accion`
- `valor_estimado`
- `recompensa_posterior`
- `comentario`

## Plantilla sugerida

```json
{
  "partida_id": "",
  "mano_id": "",
  "jugador_id": "",
  "fase": "",
  "cartas_propias": [],
  "marcador": {},
  "historial_publico": [],
  "acciones_legales": [],
  "accion_elegida": "",
  "probabilidades_accion": {},
  "valor_estimado": null,
  "recompensa_posterior": null,
  "comentario": ""
}
```

## Preguntas de auditoria

- La accion elegida estaba dentro de las acciones legales.
- La informacion usada por el agente respetaba la informacion oculta del juego.
- La explicacion de la decision es reproducible a partir del estado registrado.
- La recompensa posterior permite revisar si la decision fue util a medio plazo.
