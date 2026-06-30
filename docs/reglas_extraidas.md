# Reglas extraidas del reglamento oficial

Estado: especificacion tecnica inicial construida a partir de
`docs/reglas_federacion/ReglamentoFEM.9.pdf`, version `16-02-2025 V.7`.

Criterio de este documento:

- Solo se consolidan como reglas tecnicas las que aparecen en el PDF oficial o
  las que el usuario ya ha fijado expresamente para esta variante del proyecto.
- Si una regla tradicional del mus no aparece suficientemente clara en el PDF
  consultado, se deja como `TODO` y no se implementa todavia.
- Cuando una decision de producto simplifica el reglamento para el bot, se
  marca como `Decision de alcance del proyecto`.

## Baraja

- Fuente oficial:
  - Art. 3
  - Art. 4
- Regla extraida:
  - La partida se juega con baraja espanola de 40 naipes.
  - La modalidad objetivo usa ocho reyes y ocho ases.
  - Los treses valen como reyes.
  - Los doses valen como ases.
  - La partida completa la gana la pareja que consiga 4 juegos de 40 piedras.
  - Si durante la partida se detecta que la baraja tiene cartas de mas, de
    menos, duplicadas o defectuosas:
    - Si aun no ha terminado el lance de grande de esa mano, se corrige el
      error y se vuelve a repartir.
    - Si ya se ha sobrepasado grande o son dadas posteriores, la mano en curso
      continua y el problema se resuelve al finalizarla.
- Especificacion tecnica:
  - El motor debe modelar una baraja base de 40 cartas.
  - La evaluacion de jugadas debe normalizar `3 -> rey` y `2 -> as`.
  - La condicion de victoria de partida debe parametrizarse como
    `4 juegos x 40 piedras`.
- TODOs:
  - Confirmar si conviene representar las cartas reales y las equivalencias por
    separado, o trabajar solo con valor normalizado para la logica del mus.

## Valor de cartas

- Fuente oficial:
  - Art. 3
  - Art. 45
  - Art. 46
  - Art. 73
- Regla extraida:
  - Equivalencias confirmadas:
    - `3 == rey`
    - `2 == as`
  - Valor confirmado para sumar juego o punto:
    - `as = 1`
    - `2 = 1` porque vale como as
    - `3 = 10` porque vale como rey
    - `4 = 4`
    - `5 = 5`
    - `6 = 6`
    - `7 = 7`
    - `sota = 10`
    - `caballo = 10`
    - `rey = 10`
  - Jugadas maximas explicitamente confirmadas por el reglamento:
    - Grande maxima: `cuatro reyes`
    - Chica maxima: `cuatro ases`
    - Juego maximo: `31`
    - Punto maximo: `30`
  - Jugadas minimas explicitamente citadas por el reglamento:
    - Pares minimos: `dos ases`
    - Juego minimo: `33`
  - El reglamento tambien referencia explicitamente `29` como jugada con sena
    oficial y `30` como mejor punto.
- Especificacion tecnica:
  - El motor debe distinguir entre:
    - valor fisico de carta
    - valor normalizado para mus
    - valor para suma de juego/punto
  - Para juego y punto la suma debe hacerse con la tabla anterior.
- TODOs:
  - Ninguno bloqueante en esta seccion.

## Jugadores y equipos

- Fuente oficial:
  - Art. 1
  - Art. 2
  - Art. 63
- Regla extraida:
  - Juegan cuatro personas organizadas en dos parejas.
  - Los asientos de la mesa quedan fijos durante toda la partida.
  - Antes de comenzar debe quedar fijado que jugador tantea por cada pareja.
  - El companero del tanteador conserva los amarracos.
- Especificacion tecnica:
  - El estado de partida debe modelar:
    - `4` jugadores
    - `2` equipos
    - posicion relativa estable en mesa
    - rol de tanteador por equipo
- TODOs:
  - Precisar si el modelo base necesitara una abstraccion explicita de puestos
    (`mano`, `segunda mano`, `tercero`, `postre`) o si basta con indice circular.

## Fases de una mano

- Fuente oficial:
  - Art. 7
  - Art. 23 a 28
  - Art. 62
  - Art. 69
- Regla extraida:
  - Flujo de alto nivel de una mano:
    - reparto inicial
    - mus y posibles descartes
    - lances en este orden: grande, chica, pares, juego o punto
    - tanteo al final de la mano
  - El tanteo y la forma de hablar siguen el mismo orden de lances:
    `grande -> chica -> pares -> juego o punto`.
  - Una vez terminado el lance de juego o punto, los cuatro jugadores deben
    ensenar sus cartas.
- Decision de alcance del proyecto:
  - No se anunciara quien gana cada lance antes de terminar la secuencia
    completa de los cuatro lances de la mano.
- Especificacion tecnica:
  - El motor debe separar:
    - fases de reparto y mus
    - lances
    - resolucion final de tanteo
  - El entorno RL no debe resolver tanteos parciales por fuera del motor.
- TODOs:
  - Determinar si conviene modelar cada lance como subestado independiente.

## Mus y descartes

- Fuente oficial:
  - Art. 7
  - Art. 11
  - Art. 13
  - Art. 21
  - Art. 22
  - Art. 23 a 28
- Regla extraida:
  - Las cartas se reparten siempre por arriba, de una en una y de derecha a
    izquierda.
  - En descartes, las nuevas cartas se sirven de una vez a cada jugador y por
    el mismo orden.
  - Ningun jugador puede ver sus cartas hasta que se haya completado todo el
    reparto.
  - En un descarte, el primero en descartarse es quien reparte; el orden sigue
    de izquierda a derecha hasta el mano, que descarta el ultimo.
  - Si se acaban las cartas del mazo durante descartes, se recoge el descarte,
    se baraja, se da a cortar y se reparten las cartas pedidas.
  - Esta prohibido contar o mover el mazo para saber cuantas cartas quedan.
  - Cada pareja dispone de un maximo de un minuto para decidir cortar o dar mus.
  - El mus se puede cortar con cualquier clase de naipes.
  - Se permite juego de boquilla hasta que se corte el mus.
  - El mano de la pareja postre no puede cortar el mus hasta que el mano lo
    haya dado.
  - El tercer jugador puede cortar el mus en cualquier momento, incluso sin
    contar con su companero.
  - El cuarto jugador puede cortar el mus una vez que la pareja mano haya dado
    mus, tambien sin contar con su companero.
  - Cuando una pareja esta a falta de 5 piedras o menos, cualquier jugador
    puede cortar el mus en cualquier momento, incluso repartiendo.
  - El mano de cada pareja puede comunicar a su companero la conveniencia de
    dar o cortar mus, incluso despues de haber dado mus y aunque ya haya
    habido descartes.
- Decision de alcance del proyecto:
  - Para esta primera version del bot se asume que nunca se descubre una carta;
    por tanto, no se modela `mus visto`.
- Decision del usuario sobre la interfaz:
  - Aunque haya consejo del companero, la decision efectiva cuando llega el
    turno pertenece al jugador activo.
- Especificacion tecnica:
  - `pedir_mus` y `cortar_mus` deben evaluarse en orden de turno.
  - En esta primera version no se modelan interrupciones fuera de turno ni las
    excepciones federativas de corte de mus en cualquier momento.
  - La politica del agente puede recibir consejos simulados del companero en el
    futuro, pero la accion legal final siempre la emite el jugador activo.
  - Las reglas especiales de mus a 5 piedras o menos quedan fuera del alcance
    actual y se modelarian aparte si mas adelante hicieran falta.
- TODOs:
  - Formalizar la mecanica de descarte como accion parametrizada.
  - Decidir si la fase inicial implementara limite de tiempo real o solo logico.

## Grande

- Fuente oficial:
  - Art. 45
  - Art. 52
  - Art. 54
  - Art. 62
- Regla extraida:
  - La mayor jugada confirmada para grande es `cuatro reyes`.
  - Orden completo de grande, de mayor a menor:
    - `rey > caballo > sota > 7 > 6 > 5 > 4 > as`
  - Los naipes pueden cantarse total o parcialmente de mayor a menor o de menor
    a mayor, pero sin omitir una carta de igual valor a la ultima cantada.
  - Si grande queda en paso, su valor se apunta al final de la mano.
- Decision de alcance del proyecto:
  - La Real no vale en la variante objetivo.
- Especificacion tecnica:
  - Grande debe resolverse como lance independiente.
  - Si no hay envite aceptado, su valor debe sumarse al final del tanteo.
  - Grande en paso vale `1` piedra para la mano ganadora del lance.
  - Si hay empate exacto de jugada, gana el jugador empatado que aparezca antes
    en el orden de turno empezando por mano.
- TODOs:
  - Ninguno bloqueante en esta seccion.

## Chica

- Fuente oficial:
  - Art. 45
  - Art. 52
  - Art. 54
  - Art. 62
- Regla extraida:
  - La mejor jugada confirmada para chica es `cuatro ases`.
  - Orden completo de chica, de menor a mayor:
    - `as < 4 < 5 < 6 < 7 < sota < caballo < rey`
  - Si chica queda en paso, su valor se apunta al final de la mano.
- Especificacion tecnica:
  - Chica debe resolverse como lance independiente.
  - Si no hay envite aceptado, su valor debe sumarse al final del tanteo.
  - Chica en paso vale `1` piedra para la mano ganadora del lance.
  - Si hay empate exacto de jugada, gana el jugador empatado que aparezca antes
    en el orden de turno empezando por mano.
- TODOs:
  - Ninguno bloqueante en esta seccion.

## Pares

- Fuente oficial:
  - Art. 43
  - Art. 45
  - Art. 46
  - Art. 55
  - Art. 61
  - Art. 62
  - Art. 70
- Regla extraida:
  - Primero se declara en orden de turno si cada jugador tiene pares.
  - Despues solo juegan el lance quienes si tienen pares.
  - Si solo un equipo tiene pares, se pasa al siguiente lance y el valor de esos
    pares se cuenta al final de la mano.
  - El reglamento distingue explicitamente:
    - pares simples
    - medias
    - duples
  - Definicion operativa de categorias:
    - `pares simples = una pareja`
    - `medias = tres cartas del mismo valor`
    - `duples = dos parejas o cuatro cartas del mismo valor`
  - No existe categoria separada de `poker`; cuatro cartas iguales cuentan como
    `duples`.
  - Si un jugador lleva medias o duples, no puede declarar pares simples.
  - Si se declara la clase de pares o las cartas que los forman, debe decirse la
    verdad.
  - El jugador que no lleva pares no puede cerrar jugada en ese lance.
  - Los pares no tienen deje.
  - La jugada maxima explicitamente confirmada es `cuatro reyes`.
  - La jugada minima explicitamente confirmada es `dos ases`.
  - Los puntos de pares pertenecen a la mano ganadora del lance; no deben
    modelarse como puntos del paso.
  - Jerarquia de pares:
    - `duples > medias > pares simples`
    - en pares simples gana la pareja de mayor valor
    - en medias gana el trio de mayor valor
    - en duples se compara primero la pareja mayor y despues la pareja menor
  - Ejemplos normativos de duples:
    - `dos reyes y dos ases` gana a `cuatro sietes`
    - `dos reyes y dos ases` gana a `cuatro caballos`
    - `cuatro sietes` se comparan como si fueran `sietes y sietes`
    - `cuatro caballos` se comparan como si fueran `caballos y caballos`
  - Valor propio de pares:
    - `pares simples = 1`
    - `medias = 2`
    - `duples = 3`
- Especificacion tecnica:
  - El motor debe separar:
    - deteccion de que un jugador `lleva pares`
    - categoria de pares
    - resolucion del lance entre solo quienes lleven pares
  - La capa de acciones legales debe impedir cerrar pares a un jugador que no
    los tenga.
  - Si solo un equipo tiene pares, anota solo el valor propio de sus pares.
  - Si ambos equipos tienen pares y el lance queda en paso, el ganador anota
    `valor_de_sus_pares + 1`.
  - Si hay empate exacto de pares, gana el jugador empatado que aparezca antes
    en el orden de turno empezando por mano.
- TODOs:
  - Ninguno bloqueante en esta seccion.

## Juego / punto

- Fuente oficial:
  - Art. 43
  - Art. 45
  - Art. 46
  - Art. 47
  - Art. 48
  - Art. 49
  - Art. 58
  - Art. 60
  - Art. 61
  - Art. 62
  - Art. 69
  - Art. 70
  - Art. 73
  - Art. 88
  - Art. 89
- Regla extraida:
  - En la ronda de juego primero se declara en orden de turno si cada jugador
    tiene juego.
  - Despues juegan el lance solo quienes si tienen juego.
  - Si solo un equipo tiene juego, se pasa al siguiente tramo de la mano y su
    valor se cuenta al final.
  - Si nadie tiene juego, se juega a punto.
  - El jugador que no lleva juego no puede cerrar jugada en ese lance.
  - Juego y punto no tienen deje.
  - La mejor jugada confirmada de juego es `31`.
  - La jugada minima explicitamente citada de juego es `33`.
  - Orden completo de juego:
    - `31 > 32 > 40 > 37 > 36 > 35 > 34 > 33`
  - La mejor jugada confirmada de punto es `30`.
  - Orden completo de punto:
    - `30 > 29 > 28 > 27 > 26 > 25 > 24 > 23 > 22 > 21 > 20 > 19 > 18 > 17 >
      16 > 15 > 14 > 13 > 12 > 11 > 10 > 9 > 8 > 7 > 6 > 5 > 4`
  - Si los cuatro jugadores dicen `no juego` pero al ensenar las cartas alguien
    si tenia juego:
    - los envites al no juego quedan anulados
    - el mejor juego anota sus tantos sin negada
  - Si un jugador canta juego y luego se descubre que no lo tenia:
    - su jugada queda anulada
    - la pareja contraria anota `punto + negada de punto` en todos los casos
  - Valor propio del juego:
    - `31 = 3`
    - cualquier otro juego = `2`
  - El punto en paso vale `1` para el ganador del lance.
- Especificacion tecnica:
  - El motor debe distinguir explicitamente entre:
    - mano con juego
    - mano sin juego, que entra en punto
  - La resolucion de punto debe activarse solo si ningun jugador tiene juego.
  - Las sanciones por cantar juego incorrectamente deben modelarse como reglas
    de anulacion, no como excepciones genericas.
  - Si solo un equipo tiene juego, anota solo el valor propio de su juego.
  - Si ambos equipos tienen juego y el lance queda en paso, el ganador anota
    `valor_de_su_juego + 1`.
  - Si nadie tiene juego y el lance queda en paso, el ganador del punto anota
    `1`.
  - Si hay empate exacto de juego o de punto, gana el jugador empatado que
    aparezca antes en el orden de turno empezando por mano.
- TODOs:
  - Ninguno bloqueante en esta seccion.

## Envites

- Fuente oficial:
  - Art. 38 a 44
  - Art. 50
  - Art. 56 a 59
- Regla extraida:
  - Si dos miembros de una misma pareja envidan cantidades distintas al mismo
    tiempo, o uno envida y otro dice ordago, la pareja contraria elige el
    envite que mas le convenga.
  - Si hay un envite en litigio, el companero no puede subirlo hasta que el
    contrario lo haya revocado.
  - Ante un envite singular, el companero puede rectificar y revocar.
  - Para aceptar o revocar un envite ordinario hay un maximo de 30 segundos.
  - Para un ordago, o un envite que por tanteo equivalga a ordago, hay un
    maximo de 2 minutos.
  - Si un jugador dice `quiero` y su companero `no quiero`, vale el `quiero`.
  - Si uno responde en singular y el companero en plural al mismo tiempo, vale
    la forma plural.
  - Las formas en plural o imperativo obligan a toda la pareja, salvo la
    limitacion de pares y juego para quien no lleve el lance.
  - Los tantos de envites, aceptados o no, se cuentan al final de la mano y por
    orden de lances.
  - Si un envite sigue pendiente cuando ya deberia hablarse del siguiente
    lance, mandar abrir el siguiente lance equivale a no aceptar el envite
    pendiente.
  - Si un jugador no tiene pares o juego, no puede abrir otro lance mientras
    queden pendientes los envites de su companero.
  - Un jugador puede aconsejar a su companero pasar, envidar, revocar,
    ordaguear, querer o no querer.
  - La ultima decision corresponde al jugador que lleva la jugada.
- Decision de alcance del proyecto:
  - No habra habla libre; los envites y respuestas se modelaran como acciones
    discretas de interfaz o del entorno.
  - No se modelan respuestas de pareja en singular/plural ni revoques por
    companero; la decision efectiva la emite un unico jugador activo.
- Especificacion tecnica:
  - El motor debe modelar el estado `envite_pendiente`.
  - El conjunto de acciones legales depende de:
    - si hay envite abierto
    - si el jugador tiene o no el lance de pares/juego
    - si la respuesta posible es `quiero`, `no quiero`, resubida u `ordago`
  - La observacion del agente debe exponer, como minimo:
    - tipo de apuesta (`envite` u `ordago`)
    - lance actual
    - cantidad actual y cantidad previa en litigio
    - valor efectivo de `no quiero`
    - jugador y equipo apostador
  - El logger debe registrar tanto el lance como el estado del envite pendiente.
  - Inferencia tecnica usada en esta primera implementacion:
    - `no quiero` se modela como rechazo explicito de la apuesta pendiente
    - la primera apuesta de un lance puede abrirse por cualquier cantidad
      positiva
    - un `no quiero` a la primera apuesta vale `1` tanto
    - si se rechaza una resubida, el `no quiero` vale la cantidad que ya estaba
      previamente en litigio
    - los tantos propios de `pares`, `juego` y `punto` se mantienen separados
      de los tantos de apuesta, porque pueden corresponder a equipos distintos
  - TODOs:
    - Formalizar limites o convenciones de interfaz para cantidades de envite en
      el entorno RL.
    - Decidir si la interfaz mostrara botones por accion atomica o por respuesta
      contextual.

## Comunicacion y senas

- Fuente oficial:
  - Art. 25
  - Art. 53
  - Art. 56
  - Art. 59
  - Art. 72 a 77
- Regla extraida:
  - El reglamento permite juego de boquilla hasta cortar el mus.
  - Durante un lance se puede hablar de otro, anterior o posterior, diciendo la
    verdad.
  - El reglamento define senas oficiales cerradas.
  - El reglamento permite aconsejar al companero, pero la decision final es del
    jugador que lleva la jugada.
- Decision de alcance del proyecto:
  - Por ahora no se modelaran senas.
  - Tampoco se modelara conversacion libre.
  - Las declaraciones se sustituiran por acciones estructuradas.
- Especificacion tecnica:
  - Las reglas de comunicacion quedan fuera del primer motor jugable.
  - Si mas adelante se implementan senas, deberan modelarse como informacion
    privada entre companeros y nunca como mutacion directa del estado.
- TODOs:
  - Decidir si las senas formaran parte de una variante posterior o quedaran
    fuera definitivamente del alcance.

## Ordago

- Fuente oficial:
  - Art. 41
  - Art. 44
  - Art. 47 a 50
  - Art. 60
  - Art. 70
  - Art. 71
- Regla extraida:
  - El ordago tiene una ventana maxima de respuesta de 2 minutos.
  - Solo un ordago aceptado permite ensenar cartas y resolver inmediatamente.
  - Ante un ordago aceptado, los cuatro jugadores deben ensenar sus cartas.
  - Un ordago aceptado en cualquier lance anula todos los envites aceptados en
    lances anteriores.
  - Esta prohibido querer ordago a juego con `33` siendo postre, salvo usando
    la formula `quiero y no pierdo`.
  - Si el postre con juego y companero sin juego acepta con `quiero y no
    pierdo`, su aceptacion no es valida.
  - Si una pareja postre acepta ordago a pares o a juego teniendo ambos `2
    ases` o `33`, ese ordago no es valido y la pareja correcta anota sus tantos
    mas las negadas.
- Especificacion tecnica:
  - `ordago` debe modelarse como accion especial y no como un envite normal.
  - La aceptacion de ordago debe disparar revelacion inmediata de cartas.
  - El tanteo debe aplicarse en orden de lances hasta el lance del ordago.
  - Si una pareja alcanza `40` piedras antes de que llegue el turno de contar
    el propio ordago, esa pareja gana el juego y el ordago ya no cambia el
    resultado.
  - Ejemplo normativo:
    - marcador antes de la mano: `equipo_1 = 39`, `equipo_2 = 25`
    - en grande se envidan `2` y los gana `equipo_1`
    - en chica se acepta un ordago que iba a ganar `equipo_2`
    - primero se cuentan los `2` puntos de grande para `equipo_1`
    - `equipo_1` llega a `41`
    - el juego lo gana `equipo_1` antes de contar el ordago de chica
- TODOs:
  - Formalizar todos los casos invalidos de ordago de pares y juego como reglas
    de validacion previas a la aceptacion.

## Puntuacion

- Fuente oficial:
  - Art. 44
  - Art. 61 a 69
  - Art. 71
- Regla extraida:
  - Pares, juego y punto no tienen deje.
  - El tanteo se hace por el orden de lances:
    `grande -> chica -> pares -> juego o punto`.
  - En cada lance se apuntan:
    - las negadas
    - los tantos de envites revocados o no aceptados
  - Al final de la mano se apuntan:
    - los envites aceptados
    - el valor de las jugadas de grande y chica si quedaron en paso
    - el valor del punto
    - el valor de los pares
    - el valor del juego
  - Valor en paso por lance:
    - `grande = 1`
    - `chica = 1`
    - `punto = 1`
  - En `pares`:
    - si solo un equipo tiene pares, suma solo el valor propio de sus pares
    - si ambos equipos tienen pares y queda en paso, el ganador suma
      `valor_de_sus_pares + 1`
  - En `juego`:
    - si solo un equipo tiene juego, suma solo el valor propio de su juego
    - si ambos equipos tienen juego y queda en paso, el ganador suma
      `valor_de_su_juego + 1`
  - El tanteo debe ser aprobado por la pareja contraria.
  - No se pueden mezclar ni recoger las cartas hasta terminar el tanteo de las
    dos parejas.
  - Una vez tanteado y devueltas las cartas al mazo, no se puede reclamar un
    tanto omitido o mal sumado sin permiso de la pareja contraria.
  - Cuando a una pareja le faltan cuatro o menos tantos para cerrar un juego,
    debe anunciarlo.
  - Una vez terminadas las cuatro fases de la mano, los cuatro jugadores
    muestran todas sus cartas para verificar el tanteo y por que se ha perdido
    cada lance.
  - Si se acepta un ordago, las cartas se muestran tambien al cerrar ese ordago.
  - Los puntos se muestran y se cuentan al final; no debe cerrarse el estado de
    ganador de cada lance intermedio antes de completar el ciclo de la mano.
- Especificacion tecnica:
  - El motor debe separar:
    - `resultado_del_lance`
    - `tanteo_aplicado`
  - La aplicacion efectiva de piedras debe hacerse al final de la mano siguiendo
    el orden reglamentario.
  - En empate exacto de cualquier lance gana el primer jugador empatado segun el
    orden natural de turno desde mano.
  - El logger debe poder registrar:
    - negadas
    - envites aceptados
    - valor propio del lance en paso
    - tanteo final agregado por mano
- TODOs:
  - Confirmar si quieres reflejar en la interfaz el tanteo parcial por lance
    mientras internamente se mantiene oculto hasta el cierre de la mano.

## Condiciones de victoria

- Fuente oficial:
  - Art. 3
  - Art. 29
  - Art. 36
  - Art. 67
- Regla extraida:
  - La partida ordinaria se gana al conseguir 4 juegos de 40 piedras.
  - En competicion federativa hay reglas adicionales de tiempo que pueden
    modificar el inicio de juegos finales a `20` o `30` piedras segun el reloj
    de ronda.
  - Cuando a una pareja le faltan 4 o menos piedras para cerrar un juego, debe
    anunciarlo.
- Especificacion tecnica:
  - El motor base puede tomar como condicion estandar:
    - `juego_objetivo = 40 piedras`
    - `partida_objetivo = 4 juegos`
  - Las reglas federativas de control de tiempo conviene tratarlas como capa de
    torneo o competicion, no como regla nuclear del motor.
- TODOs:
  - Decidir si el primer motor ignora por completo reglas de reloj y rondas de
    torneo.

## Errores y anulaciones

- Fuente oficial:
  - Art. 78 a 90
- Regla extraida:
  - Error en pares:
    - si se detecta antes de cerrarse, debe rectificarse
    - si se detecta despues de empezar pero antes de respuesta efectiva, la
      jugada se reinicia sin sancion posterior
    - con envites ya contestados, la jugada errante no participa en pares
    - si el error se descubre ya cerrada la jugada, la jugada queda anulada y
      los envites posteriores solo valen si los gana la pareja correcta
  - Error en juego:
    - misma estructura general que en pares
    - la jugada errante no participa en juego
    - si el error se descubre cerrada la jugada, los envites solo valen si los
      gana la pareja correcta
  - No juego:
    - si todos dicen `no juego` y alguien si tenia juego, los envites a no
      juego se anulan y el mejor juego anota sin negada
    - si un jugador canta juego sin tenerlo, su jugada se anula y la pareja
      contraria anota `punto + negada de punto`
  - Regla general:
    - si una jugada anulada habia propiciado negadas o envites favorables a la
      jugada anulada, esos efectos favorables tambien se anulan
- Especificacion tecnica:
  - Estas reglas deben vivir en una capa de validacion/arbitraje del motor.
  - No deben mezclarse con la evaluacion normal de lances.
- TODOs:
  - Formalizar cada error como transicion legal del estado o como sancion de
    arbitraje separada.
  - Decidir si la primera version del motor ignora estas penalizaciones y las
    deja para una segunda fase ya documentada.

## Ambiguedades pendientes

- TODO: decidir que parte del reglamento de errores y arbitraje entra en el
  primer motor y cual queda para una capa posterior de validacion.
- TODO: revisar si queremos modelar desde la primera version las reglas
  federativas de reloj o dejarlas fuera del motor base.
