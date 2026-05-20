**Meeting with MOSQUERA PRADA DIEGO-20251113_151352-Meeting Recording 1**

0:03  
Bueno, buenas chicos, qué tal cómo están antes que nada la bienvenida acá a este video que simula ser un poco lo que sería la presentación del TP. Sí, algo bastante sencillo, pero más o menos para irlos guiando e irles mostrando más o menos que espero yo con lo que es la presentación del TP, sí.

0:28  
Con pasar tarde no hacerlo tan largo me voy acá a compartir pantalla, ahí creo que se ve sí por acá la quinta y bueno acá primero que nada lo que vemos es bueno, tengo la del lado izquierdo, tengo el navegador con diferentes bases de datos y en y en el lado derecho tengo lo que sería la consola con.

0:58  
¿La ejecución que vamos a ir haciendo para ir mostrando? Sí, para poner un poco de contexto, porque esto seguramente dure varios cuatrimestres. Puse el mismo vídeo y para que se entienda tanto si están comenzando la cursada como ya la parte final de la cursada que es la presentación del TP, sí recuerden que ustedes van a tener 1 t. P que programar sí, puede que sea el que ustedes hayan realizado o el que hayamos rotado durante clases o vaya o vayamos a rotar durante clases.

1:22  
¿Que este lo van a tener que codificar? Se lo van a tener que codear y integrar las diferentes bases de datos para el TP en base a lo que son los casos de uso. Sí, recuerden que van a tener que utilizar una base de datos relacional y las bases de datos no relacionadas que vemos en la cursada. Puede que utilicemos 345, depende de las que veamos. Sí, por lo general siempre vamos a usar Mongo Cassandra.

1:48  
Neo, pues seguramente. Y si llegamos a ver también redis, además de lo que es la base de datos relacional. Sí, bueno, primero que nada recuerden que ustedes van a tener un der. Sí, el diagrama, entidad de relación, ese diagrama, entidad de relación del negocio que les tocó o del caso de de Del caso que les tocó, van a tener que crear las entidades con sus atributos y todo, digamos todo lo que es la parte de ese diagramado en en su base.

2:18  
Esto es relacionar, recuerden que puedo utilizar la que ustedes quieran, sí pueden utilizar maíz, pueden utilizar ese puede ser, pueden utilizar pobre la que ustedes quieran, siempre y cuando sea una basada relacional, yo acá en este caso, para hacer una demostración bastante completa y mostrarles que en realidad se puede hacer de todo. Yo tengo pogres tanto local como remoto, tengo mongo local y remoto, cassandra local y remoto, neo local y remoto y redis local y remoto. Cuando hablo de remoto me refiero a plataforma clave, sí.

2:45  
Local lo tengo instalado en un contenedor tocker que se lo voy a mostrar por acá, tengo acá sí lo que serían mi mi proyecto que se llama Urbango y acá tengo los diferentes contenedores con la base de datos que estoy utilizando. ¿Sí, acá está rossandra el neo Postgre rent y Move sí, y que De hecho si hacemos acá un comando que es para ver los contenedores que están se están ejecutando, acá están sí vemos el nombre del contenedor hace cuántos se levantó todo ese tipo de cosas? Sí.

3:14  
Y también tengo todo en su parte cloud, sí, acá tengo pogres en parte cloud que estoy usando un sistema que se llama Railway, lo podemos utilizar, lo único más es que le da solamente 30 días gratis, se puede compartir, pueden parece usar la cuenta así que se pueden compartir la cuenta o bueno, si no hacer contar el plan que te cuesta 5 dólares mensuales nada más es una opción, no es la única, sí hay más, hay son los de a ustedes para que investiguen redway, estoy usando postgres, estoy utilizando acá en remoto mongo o Atlas.

3:43  
Sí que también tengo la versión en Mongo Compact, que es como el el aplicativo en en en local. Sí, este acá de mongo de mongo. Si ves ahí actualizar porque ya ahora está vaciado, vacié todo antes de de empezar a grabar. Acá tengo acá abstract, recordemos que abstract es donde usamos kassandra en su versión cloud. Sí, acá tenemos abstract.

4:07  
Redis que bueno, redis acá en realidad tengo el cliente acá instalado que se lo voy a ir mostrando también a que vaya progresando, que hasta que el revis database igual Eh conectados, parte remota y el neo se me acabó la Cámara y tengo el neo, el remoto y el neo local sí que lo vamos a ir viendo, sí, así que bueno, eso más que nada. ¿En qué se basa este?

4:36  
Por el pequeño ejemplito que yo estoy haciendo es básicamente una especie de de casa inteligentes, sí, de smartphone donde solamente tengo sensores o creo sensores con que registran humedad y temperatura de la de la habitación en la que he estado o la ubicación están en una casa. Sí, toda esa información yo las guardo en las bases de datos y las puedo ir consultando de acuerdo a los casos de uso. Sí, bueno, para mostrarles primero que nada más que nada acá tengo por ejemplo, Redwing tengo.

5:04  
Dos tablas, que es dispositivo y usuario, sí, de base y user. Ambas tablas, si se fijan, están vacías. Sí, tanto la remota como la local, que que es el contenedor de docker, que yo estoy usando, un un cliente tercero, que se llama de Viber, que muestro acá, se ven exactamente igual. Sí, se ve gastry cof from. User, que estaba hacia la tabla, y full. Device, que estaba hacia la tabla también, sí, así que bueno.

5:34  
Pongo, tenemos tren que está vacía la de Cassandra, no recuerdo. Tengo el nombre del caso de uso que usamos acá, History, sensors\* perdón, history sensor que está vacía. Si ven la estructura es el nombre de sensor, fecha, humedad y temperatura, nada más. ¿La de redis está vacía también? Sí, y bueno, el azeneo, obviamente.

6:00  
Y la d n a que bueno, vemos que está vacío. Sí Eh, estoy preocupando para ejecutar acá porque yo tengo ya ya había creado en su momento este tipo de nodos, pero si hacían no, no tengo nada, la aplico acá, sigo loca entre paréntesis la cantidad de nodos que tenemos acá, no aquí como no tengo nada como está vacía lo muestra como si es todo en cero, sí bien, entonces acá simplemente lo que puede hacer es empezar a ejecutar acá el programa sí smartphone CDIY bajo 3. Pi, sí.

6:28  
Y acá lo primero, lo primero que estoy haciendo es conectarme a las bases de datos. Sí, tiro como que un check de que me logré conectar exitosamente a la base de datos. Sí, acá pueden ver que tengo conexión a poget local, exitoso conexión a poget red Wid, que es el remoto exitoso acassandra hasta que es el remoto exitoso acassandra local exitoso mongo local mongo cloud red local neo local neocloud, sí.

6:52  
Ya acá verifiqué que estoy conectado a todas las bases de datos, tanto local como remota. Si se tiene, estoy generando acá 10 conexiones a base de datos, sí, 5 locales y 5 remotas. Sí, yo por lo menos acá interactúo con lo que es la base de datos. Sí, como no tengo usuarios registrados en la plataforma, voy a quevoyahacerprimerovoyavoyacrearunusuariosisinoquebuscá<isunsinopingresaatutuemailsupongamosquevoyaregistraradiego@mail.com> sí.

7:21  
¿Contraseña 1234 nombre completo y le vamos era y dice registro de usuario dice registro usuario registrado en Postgre tanto local como en postgre esclavo, sí, qué quiere decir esto? Si yo me voy acá a mi postgress local que vimos que estaba vacía anteriormente voy a call user.

7:41  
Y se establecenting actualiza y ahí esta usar I D 3 el nombre contraseña full name. ¿Cuándo fue creado? Si se fijan tiene la fecha exactamente ahora que es 13 de noviembre 2025 sí, y si consulta también mi postgres local acá está exactamente igual, acá tiene otro I user ID porque acá tenía 2 horas más creado, sí, pero funciona exactamente igual el I user ID 12, el email, el Password, el nombre y cuándo fue creado se fijan tiene gran exactamente una fecha y hora sí.

8:11  
Así que bueno, Chao, por lo menos tengo mi usuario creado. Sí, sí, ahora voy a <loguearmeconmiusuariosiingresatumaildiego@mail.com> 1, 2, 3, 4 y se lo veo exitoso. Sí, qué me pregunta ahora me dice Log in o K tanto en la parte local como en la parte clavo. Esto lo hago validar solamente variación para mostrarles que lo puedo hacer.

8:34  
¿Cuando a ustedes les toque hacerlo no es necesario que lo hagan en las dos, sí van a escoger una sola para que les sea más cómodo, más práctico, puede ser local, puede ser cloud, qué les recomiendo? Yo tapada la parte cloud porque la pueden interactuar todos, cada 1 desde su casa, lo que hacen los locales es un poco más complicado. ¿Sí, pero bueno, acá me me lanza la pregunta, si el dispositivo es de confianza, sí, 1, si sí, cero, si no esto para qué lo hago? Es solamente para un caso de uso de Redis, sí, de manejar sesiones.

9:04  
¿Qué quiere decir esto? Yo lo tengo sitiado solamente para fines didácticos, la materia, que si yo lo ecólogo que no es un dispositivo de confianza. Imagínense que estamos, no sé en un aeropuerto o en una cafetería o conectados a la computadora, y entramos al home banking con la aplicación bancaria y nos pregunta si queremos Guardar como esta red segura o no, que nos recomienda que si es una red pública lo hacemos como no segura, para que para cosas de seguridad, si para el tema de seguridad.

9:30  
Acá con fines eléctricos, si no propongo que no me va a crear una sesión solamente de 5 segundos. ¿Qué sucede? ¿Que a los 5 segundos me va a cerrar la sesión? Sí, entonces yo te doy acá que no me dice TTL que es el tiempo de la sesión, me va a durar 5 segundos nada más cuando pasen los estos 5 segundos que se van a cumplir, ahora nomás que yo quiera ejecutar una acción, no voy a poder hacerlo porque ya me sacó de la sesión, sí, ahora para que esto se pueda ver acá en.

9:58  
En redis no sé si lo vamos a llegar a ver bien porque son 5 segundos muy rápidos, los los vamos a ver bien, pero para la próxima parte sí, cuando yo ejecute acá una nueva opción que yo quiera. Por ejemplo, registrar un nuevo sensor que me dice sesión terminada para este usuario. Sí, no puedo hacer más, así que voy a tener que loguearme de nuevo usuario y contraseña. ¿Me va a preguntar de nuevo si tuve confianza? Le voy a decir que sí.

10:26  
Y ahora me dice que tengo 600 segundos que serían 10 minutos sí, y ahora acá en reds si se fijan dice que no hay nada, pero si hago un refresh tengo ahora el Usuariovendiego@enel. ¿om es un TTLY acá dices cuánto tiempo me va quedando? Sí si hago acá time to Live y me cambio dice el tiempo que me queda de este de este usuario a ver si hago un refresh acá me da 9, 9 minutos, 34 segundos si refresh acá.

10:56  
9 minutos, 30 segundos y así hasta que pasen los 10 minutos. Sí, entonces ya estamos viendo que estamos utilizando el raidy. Sí, recuerden que he usado tanto el local como remoto, así que bueno, eso por ahora ahora veamos los casos que tenemos acá sí, Ah, bueno, aquí otra cosa que yo tengo acá por lo menos es registrar un sensor en smartphone. Sí, voy a registrar un sensor acción 1, nombre del sensor voy a colocarle, por ejemplo, no sé.

11:29  
Dispensa\_ cocina, hazlo solo dispensa ubicación del sensor en la cocina que me dice acá, dispositivo registrado en postgre local y cloud. ¿Qué quiere decir esto? Si yo me voy a a data y a device, que antes estaba vacía, ahora acá me sale, ven.

11:52  
Dos dispensa location, cocina bueno, laca. No me agregó cuando fue creado, pero bueno, lo debió haber hecho, pero bueno, ya tengo por lo menos ese tanto en su parte remota creo que fue el tipo de data como en su parte local, la casa del mes 17 dispensa cocina cuando fue creado, que justamente hoy este momento de por ahí sí, así que bueno, ya tengo por es menos 1 usuario registrado.

12:19  
Ya tengo un sensor registrado, sí, vamos a crear otro sensor para empezar eso, otro ejemplo o bueno lo podemos ir viendo acá. ¿Qué tengo yo acá en Casandra? Yo registré un sensor. Ahora si ustedes se fijan en el sistema, automáticamente yo registro un dispositivo, me empieza a crear registros con y si se fijan fecha en el que está cargando un registro que lo tengo cada dos segundos, si no me equivoco 2 o 3 segundos y ya va agregando la humedad y la temperatura y valores aleatorios, pero ya lo va haciendo.

12:47  
Si ustedes se fijan todos dicen dispensa ahora si yo coloco registrar otro dispositivo y le coloco no sé barra en la sala por ejemplo, sí ahí registra el dispositivo y lo vemos acá acá un refresh acá en redware ahora lo veo, ves barra en sala y si me voy a Cassandra el mismo se le gaste el compro en la tabla, chaca lo ve barra acaba saliendo, sí, ya me ya me ya me empieza a cargar ese.

13:15  
Ese nuevo ahora tengo 3. Si yo espero un par de segundos más y además puedo puedo hacer pongo el filtro. Pues no recuerdo cómo se llama la ubicación. Sensor name es igual a barra, sensor name a la barra. Ahí lo vemos bien y ahí va creando cada dos segundos va agregando.

13:45  
¿Registros nuevos a la tabla de Cassandra? Sí, esto lo está corriendo por detrás, así que capaces, estaré a ustedes de ver cómo de repente se puede hacer esto. Sí, porque si ustedes se fijan yo registro un dispositivo en la tabla de base de datos relacional. Y qué es lo que estoy haciendo yo cada dos segundos consulto todos los name que hay en esta tabla, agarro 1 de forma aleatoria, puede ser, compensas, puede ser barra, eso lo lo decido lo decir el sistema de forma aleatoria.

14:11  
Crea un valor de humedad y temperatura también aleatorio y lo guardo en Casandra. Sí, pero estoy consultando esta tabla de postgres constantemente, es más, si vamos a las métricas a clase de Del sistema, vemos que empieza a haber como que bastante movimiento ven si lo ven acá, acá hay tanto ingreso como egreso de de los datos, sí, porque estoy consultando la tabla, así que bueno, eso por lo menos por este lado. Sí, ya tenemos un usuario, tenemos dos dispositivos.

14:39  
Sí, ahora qué tenemos acá la tenemos ver historial de temperatura y humedad de algún dispositivo en específico. Sí, caso de uso dos, este es un caso de uso, sí dice ver historial de temperatura y humedad a algún dispositivo en específico. Sí, esto yo lo tengo que ya tener en alguna base de datos. Sí, ya sabemos en cuál la tenemos, obviamente sí que es obviamente la de Cassandra, ahora selecciono la opción dos, me dice sensores disponibles, además me va a mostrar una tabla de cuáles son las que tengo y yo tengo que escribir el nombre de sensor para ver su historial.

15:09  
Si yo escribo una barra vemos que acá me sale el sensor, la fecha, humedad y temperatura, que serían los mismos que tenemos acá. ¿Sí, recordemos que acá están, EH? ¿Los voy, los voy, los voy creando, los voy, me voy creando con el historial de estos de estos sensores? Sí, así que este.

15:34  
Ese sería, por ejemplo, un caso de buzo. Sí que en mi caso de uso yo lo defino de acuerdo a este caso de uso en Cassandra. Bueno, consulto la entre la table en Cassandra y muestro el resultado final. Sí bien, caso de uso número 3 dice ver historial de Logins sí, si yo subí el chat de Logins Selecciono la opción 3 que me dice acá historial de <loginsmesalediego@m.com>, <diego@m.com>, Subsis Subsis y la fecha en la que lo hice.

16:01  
¿Dónde estoy guardando esto? ¿Lo estoy guardando en en mongo, sí, acá no hay nada, si yo hago un refresh de acá creo que acá están Eh Logins tengo dos logins dos subsis dos subsis Sí, qué quiere decir esto? Si yo me hago un me salgo, hago un <logincolocodiego@mail.com> pero coloco 1 de cuatro 5 que no es la contraseña que dice Login fallido.

16:31  
Y si yo actualizo acá este documento de mongo a ver no me está saliendo, sale nuevo. Ah, acá tengo solo los subsis, no sé, no recuerdo por qué tengo los los files yo los guardaba De hecho aquí en otro documento que a ver si lo podemos ver acá en mongo Compass.

17:10  
¿Sherlock means están los subsis? Este me parece que se me olvidó colocar la parte de los files, pero bueno, la idea sería acá que saliera también cuando un usuario intentó ingresar mal su contraseña o ese tipo de cosas, más que nada para cosas de auditoría o monitoreo y ese tipo de cosas SIM. Pero bueno, ahora también se puede ver que bueno.

17:38  
Los 3 subsis que he tenido, los 3 logueos, pues se pueden ver acá en la base de datos. Sí bien, ya tengo, ya ya registré usuarios, ya registré sensores, ya habéis visto de temperatura, de humedad y de algún dispositivo. El historial de Logins ya también sucedió. ¿Sí, el tiempo de expiración de la sesión, esto es solamente para consultar en red, si si algún cuatro acá que me dice acá cuánto tiempo me queda? 526 segundos de esta sesión.

18:07  
Si yo vuelvo a ejecutar el mismo caso de uso 519 ve que va corriendo el tiempo, si yo vuelvo a ejecutar 515 y así que es lo que yo veo en redis. ¿Sí que es cuando yo entro acá a redis y actualizo en qué queda 508 segundos ahora sí después podemos crear otro usuario y podemos ver que también se va, se va a pedir no? Pero bueno, si te fijan todo está pasando detrás de la aplicación, o sea para el usuario es invisible todo lo que sucede, el usuario no sabe dónde está consultando.

18:37  
Yo cuando estoy consultando, por ejemplo, historial de temperatura y humedad, no le pregunto a tu usuario si es de Cassandra, si es de mongo, no, no, el usuario ni sabe dónde está consultando, si es relacional, si es en Cassandra, si es en Mongo, si es lo que sea. Yo solamente quiero saber el historial de humedad y temperatura y ya está el caso de uso, sí es específicamente lo hace en Cassandra, lo hace la aplicación, sí, pero para mí es invisible. Eso si ustedes ven, lo hago con el historial de Logins 3.

19:03  
¿Me muestra el historial de lo que dice, no me dice, esto es el mongo, dónde quieres consultarlo? No solo quiero saberlo, ya está, lo estoy buscando de mongo, nada más, sí, pero esto es invisible al usuario sí, al usuario no le importa dónde lo consulta, sí, la lógica de la aplicación está en esa sí, acá vamos de nuevo con este tiempo consulto, redis no te dice, no te pregunta dónde quieres consultar, o sea, simplemente lo consulta en Redis y ya está. Sí, bueno.

19:30  
Caso número 5 que dice que ver qué usuarios registraron, qué dispositivos y cuandolohicieronsicasonumerocincosiyocolocoacasonumerocincoquequesucedeacamediceusuariosregistradosobviamentetengounsolousuarioconloquellego@mail. ¿om que es el único usuario que tengo por ahora, me dice qué tengo? Ah, bueno, acá hay 1 porque intenté registrar 1 y no, no lo pude registrar bien, pero bueno, si se fijan tengo el dispensa y tengo el barra sí, y la fecha en la que se registró.

20:00  
¿Sí, dónde veo esto en neo? Sí, si ustedes se fijan este es mi neo, mi neo local, ahora sale el cuatro acá sí, porque tengo usuarios YY dispositivos, en realidad 1 está mal pero bueno que es el false, pero acá estaba <endiego@mail.com> y acá está el de dispensa, sí está el de barra y el y el otro que me quedó mal sí, pero bueno, a estas existen acá sí, si yo si yo copio esta consulta.

20:28  
¿Y las ejecuto acá en en el remoto, en el cloud sucede lo mismo, Eh? Yo veo acá el el, el el grafo, acá esta barra sí dispensa el que cree mal y el usuario sí, y eso todo lo puedo ver ahí también. ¿Sí, y esto lo hace consultando neo? Sí, la consulta detrás de la aplicación está haciendo la consulta en NEO para ejecutar esa esa consulta.

20:58  
Sí va por ese lado más que nada y bueno este que dice limpiar toda la base de datos, simplemente lo que hace es un drop de <todosientoncesquevamosahacervamosahacerlosiguientevamosasalirdesdelaaplicacionvamosaregistraraotrousuariovamosmaria@mail.com> 1234 vamos a probarnos a 4 5 nombre completo María Pérez solo registrado sí, si me voy acá a rairway.

21:31  
<Estaelusuariobenmaria@mail.com> 1345 María Pérez, ahora voy a <loguearmeconmaria@mail.com> 134 Ah no espera 1845 @Mail. ¿om 212345 ahora sin dispositivo de confianza le voy a dar que sí?

21:55  
Ya estamos acá, sí, si ustedes se fijan acá ahora en Redis me creó otro para María, si se fijan, el Diego sigue corriendo, capaz no debería, eso lo podemos manejar nosotros de cuando ya lo fuera. ¿Ese logout elimine la sesión de Redis, también lo podemos manejar, Eh? ¿Debería de ser así y crea la sesión de María y ahora acá lo vemos, EH? Esta es la sesión de María.

22:20  
Sí, ya está María entrengy registrada tanto en la parte local como en la parte remota. Si yo actualizo acá mongo tengo debería tener otro documento, ahora lo vemos en el de María, un array con su SIS cuando se lo vio sí, y ahora supongamos que yo hago acá, selecciono la opción siendo sensores de María registro un sensor que sea no sé supongemos coloco acá.

22:50  
Humedad\_ Ah, no de baño, sí, ubicación del Descensor en el baño, dispositivo registrado vuelva a Rewind Device hasta el mes cuatro, humedad, baño, el baño. ¿Si se ustedes se fijan que no dice quién lo creó, entonces de dónde obtengo yo esa información? Me voy a Neo.

23:18  
Y <acacuandoyoactualicequeyahayseisenrealidadyacasalemaria@mail.com> tiene el dispositivo de humedad, baño. ¿Sí, acá en Astra cuando consultemos el en\* from así yo le Quito todo capaz de voy a salir del ese número de los primeros siempre va a salir barra, ahora humedad, baño, Eh? Y ahí la va creando o simplemente activo.

23:49  
Humedad español y ahí me salen. ¿Sí, si ustedes se fijan, el único gestor de base de datos que tiene una información que relaciona amarilla con el con el sensor del baño es neo, entonces por eso es que cuando yo algo, por ejemplo en el caso de uso 5 que dice qué dispositivos registraron, qué usaron, registraron tal dispositivo? ¿Ahora si ustedes se fijan mis usuarios registrados Diego y María y necesito escribir qué usuario?

24:16  
Quiero consultar información simeequivocasmaria@mail. ¿om y sale, me da baño y la fecha en la que el dispositivo fue registrado? Sí y así tal cual todo lo demás. Si yo por ejemplo dos veo los dispositivos que están cuándo fue creado, yo quiero. Por ejemplo, María quiere saber cuándo los los de dispensa.

24:43  
Salen acá en dispensa la fecha, la humedad, la temperatura, el historial de Logins, si ustedes saben salen acá ven, salen 3 veces Diego y una vez María que se ha hecho los ha hecho lo indecitos en la aplicación y así sucesivamente. Ven esto es de repente algo bastante básico de más o menos lo que yo espero que se presente en la aplicación. Sí, si yo ejecuto acá la la el la función 9 que es limpiar todas las bases de datos si ustedes se fijan.

25:10  
Le doy al 9, me vuelve a preguntar. Deseo limpiar todas las bases de datos, si yo selecciono que sí me dice limpiando base de datos sí, y si yo me voy acá acá me me desloquea porque incluso me me borro como usuario porque ya la tabla de base está vacía. Ahora la tabla user que tenía estos usuarios ahora está vacía. Pongo si yo refresco la tabla, perdón, la colección no tengo documentos.

25:40  
Sandra, si ustedes se fijan ahora, si le Quito el where, incluso para que me muestre todo, no tengo registros nuevos, ven historicensos no hay neo en ese mejor ustedes se fijan que dice acá no records sí chance, no records ya no hay y redis acá se ven y si yo hago refresh no está.

26:10  
Sí me limpió todas las bases de datos, sí, tanto local como remota. Por qué que si yo me voy acá al e viver, que es mi cliente de base de datos relacional, se le da\* from si te ven a casa de device cuando lo consulté en su momento y ejecuto ahora está vacío de usuario, aquí está vacío. Sí, entonces.

26:33  
Eso me limpió todas las bases de datos, tanto locales como remotas. Para nada, para para la próxima vez que otro ejemplo, cosa así lo pueda, lo pueda ir haciendo todo desde cero, bien en limpio, sí, pero más que nada es esto chico. Sí espero que les haya gustado que les haya servido, que les sea útil para que preparen su presentación. ¿Sí, recuerden que ustedes van a tener que mostrar primero que nada, el der sí, el der que ustedes recibieron, si si llegamos a hacer el intercambio, bueno, qué der recibí yo?

27:02  
¿Y qué modificaciones hice? Sí me van a tener que justificar esas modificaciones porque pudieron haber surgido modificaciones a a lo largo que están codeando, incluso la aplicación. Entonces, bueno, por ejemplo, no sé, un usuario no tenía registrada la dirección y yo se la tuve que agregar al d r o lo que tuve que era como entidad o estaba como atributo y lo tuve que cambiar. Bueno, y todo ese tipo de cosas la tenía que justificar en la presentación. Sí, y segundo, hacer este tipo de presentación sí, recuerden que hay en una aplicación, no les voy a evaluar código.

27:30  
Si lo hicieron en Python, en Java, en javascript, en lengua de programación que ustedes quieran, no hace a la materia de eso sí, lo que sí me interesa ver es esto, que es cómo interactúan las bases de datos entre sí. Sí, si ustedes se fijan, yo consulto en postgres para para llenar la tabla de Cassandra.

27:48  
Y consulten postgres para llenar la la el documento de Mongo y consulte en Postgres para llenar el el el grafo Neo y así voy haciendo. Sí hago que una que una base de datos, consulte la otra base de datos y así voy voy. Voy haciendo que ellos interactúen entre sí. Sí, no tengo datos aislados de que por ejemplo un usuario está un usuario registró un dispositivo, por ejemplo Pedro registró un dispositivo, pero Pedro no existe en la tabla de usuarios.

28:13  
Eso no, eso no puede ser porque no tengo coherencia, no tengo consistencia en la información, sí, no tengo consistencia en los datos, todo debe mantener una consistencia, eso es lo que a mí más me interesa. Sí, recuerden que debe sí o sí, es motivo de desaprobar que la base de datos interactúen entre sí. Ya les mostré acá lo hice tanto de forma local como forma remota. No es difícil, hay que investigar un poco, hay que estudiar un poco, sí, pero bueno, espero les sirva cualquier cosa me pueden ir consultando.

28:43  
¿Pero bueno, para que se hagan una idea de más o menos, qué es lo que espero? Sí, así que bueno, chicos, espero que les haya gustado y les voy a subir la grabación apenas la revise y vea que todo haya corrido bastante bien. Bueno, cualquier cosa me ponen consultando, sí, así que bueno chicos, este un abrazo y nos vemos en la cocina.