# Decisiones de Diseño — TPO Grupo 7 F1

Documento para registrar las decisiones tomadas sobre el DER y la arquitectura,
para justificarlas en la presentación.

---

## DER Original

El DER recibido (ver `consignas y der/DER-F1-GRUPO6.jpg`) define las siguientes entidades:
EQUIPO, PILOTO, CIRCUITO, TEMPORADA, CARRERA, PARTICIPACION, RENDIMIENTO,
RESULTADO, PIT_STOP, PENALIZACION.

---

## Modificaciones al DER

### 1. Eliminación de `penalizacion_aplicada` de RESULTADO
**Cambio:** se eliminó el atributo `penalizacion_aplicada` de la entidad RESULTADO.

**Justificación:** el atributo era redundante. La entidad PENALIZACION ya registra
la misma información con mayor detalle (tipo de penalización y tiempo adicional),
relacionada por `id_piloto` e `id_carrera`. Mantener ambos generaba inconsistencia:
si se actualizaba una penalización en PENALIZACION, `penalizacion_aplicada` en
RESULTADO quedaba desactualizado.

---

### 2. Incorporación de la entidad USUARIOS y FK con EQUIPOS
**Cambio:** se agregó la entidad USUARIOS al DER con los atributos:
`id_usuario`, `email`, `password`, `nombre_completo`, `rol`, `id_equipo (nullable FK → Equipos)`.

**Justificación:** el sistema requiere autenticación para operar. USUARIOS no estaba
en el DER original porque el enunciado no especifica gestión de acceso, pero es
necesaria para implementar el manejo de sesiones con Redis (TTL por usuario).
El atributo `IdEquipo` (nullable) conecta USUARIOS al modelo F1: un usuario con
rol `director` tiene asignado el equipo que gestiona, mientras que `admin` y
`prensa` lo tienen en NULL. Esto integra USUARIOS al grafo de entidades en lugar
de dejarlo aislado, y permite consultas del tipo "qué equipo gestiona el director
que inició sesión ahora mismo" combinando Redis (sesión activa) con SQL (datos del equipo).

---

### 3. Incorporación de la entidad AUDITORIA
**Cambio:** se agregó la entidad AUDITORIA con los atributos:
`id_auditoria`, `id_usuario (FK → Usuarios)`, `accion`, `fecha_hora`.

**Justificación:** Redis guarda la sesión **activa** pero cuando el TTL expira
ese dato desaparece para siempre. AUDITORIA actúa como complemento permanente:
cada vez que un usuario hace login o logout, se escribe un registro en SQL.
Esto demuestra la interacción Redis↔SQL requerida por la cátedra:
- **Redis** sabe quién está conectado ahora (lectura O(1), con expiración automática)
- **SQL** sabe quién se conectó históricamente (persistente, consultable)

Los tres tipos de acción registrados son: `login`, `logout`, `expiro`.

---

## Arquitectura Multi-Base

### Decisión: SQL Server como fuente de verdad
Todas las entidades del DER se crean en SQL Server. Las bases NoSQL se pueblan
consultando SQL Server para garantizar consistencia de IDs.

| Base | Rol | Poblada desde |
|------|-----|--------------|
| SQL Server | Fuente de verdad, esquema completo | — |
| Cassandra | Resultados históricos desnormalizados para analítica | SQL Server |
| MongoDB | Pit stops y penalizaciones como documentos | SQL Server |
| Neo4j | Grafo de relaciones piloto↔temporada, carrera↔circuito | SQL Server |
| Redis | Sesiones de usuario con TTL | SQL Server (valida credenciales) |

**Justificación:** ninguna base NoSQL tiene datos que no existan en SQL Server.
Esto garantiza consistencia y permite reconstruir cualquier base NoSQL desde cero
en caso de pérdida de datos, re-ejecutando la sincronización.

---

## Consistencia eventual y tolerancia a fallos

### Modelo de consistencia
El sistema implementa **consistencia eventual** (modelo BASE) para la capa NoSQL:

- **SQL Server es ACID**: toda escritura en SQL es atómica y durable. Es la única fuente de verdad.
- **Los NoSQL son entornos de lectura**: nunca se escriben directamente desde el flujo principal. Solo se actualizan vía sincronización desde SQL.
- **La sincronización es idempotente**: la función `_sincronizar_en_segundo_plano()` borra y reinsertta todos los datos en cada NoSQL. Ejecutarla N veces produce el mismo resultado. Esto permite recuperar la consistencia en cualquier momento sin lógica de reconciliación.

### Flujo de escritura
```
Usuario → SQL Server (ACID, commit) → _sincronizar_en_segundo_plano()
                                            ├── Cassandra (independiente)
                                            ├── MongoDB   (independiente)
                                            └── Neo4j     (independiente)
```

### Comportamiento ante fallos
Cada base NoSQL se sincroniza de forma **independiente**. Si una falla:
- Las demás continúan sincronizándose
- SQL ya tiene el dato correcto → no hay pérdida de datos
- El sistema avisa qué bases quedaron desactualizadas (`⚠️ Entornos de lectura listos: 2/3`)
- Al volver a levantar la base, el siguiente CRUD restaura la consistencia automáticamente

### ¿Por qué no hay rollback distribuido?
Porque no es necesario: si SQL confirma el cambio, el dato está seguro.
Si un NoSQL falla en el sync, es un problema de *lectura eventual*, no de *integridad*.
La operación idempotente hace las veces de mecanismo de recuperación.

---

## Por qué cada base NoSQL para cada caso de uso

### Cassandra → CU1 y CU2 (datos históricos y analítica masiva)

**CU1: ¿Qué pilotos han ganado múltiples campeonatos mundiales?**
**CU2: ¿Qué equipos han tenido más victorias en la historia?**

Cassandra es la opción correcta porque:
- Ambos casos requieren consultar **grandes volúmenes de datos históricos** (resultados de décadas de carreras)
- Cassandra está optimizada para **escrituras masivas y lecturas por rango** — ideal para series de datos que crecen constantemente con cada nueva carrera
- El modelo de datos se diseña **por consulta**: cada tabla está optimizada para responder exactamente una pregunta, sin JOINs
- `campeonatos_por_piloto` tiene como partition key `nombre_piloto` → todas las temporadas de un piloto están en una sola partición, leerlas es O(1)
- `victorias_por_equipo` tiene como partition key `nombre_equipo` → contar victorias de un equipo es una lectura directa sin recorrer toda la tabla
- En SQL, responder CU2 requeriría un JOIN entre Resultados, Carreras y Equipos + GROUP BY. En Cassandra esa respuesta ya está pre-calculada en la estructura de la tabla.

### MongoDB → CU3 y CU4 (documentos semiestructurados)

**CU3: ¿Qué pilotos han marcado la vuelta más rápida en diversas carreras?**
**CU4: ¿Cuántos pit stops se realizan en promedio por carrera?**

MongoDB es la opción correcta porque:
- Los pit stops y vueltas rápidas son datos **semiestructurados**: cada documento
  puede tener atributos distintos o anidados sin necesidad de un esquema rígido.
- Las consultas de CU3 y CU4 requieren **agregaciones** (GROUP BY + COUNT/AVG en SQL),
  que MongoDB resuelve nativamente con su pipeline de agregación (`$group`, `$avg`, `$sum`).
- Leer todos los pit stops de una carrera es una consulta por `id_carrera` —
  con el índice `idx_carrera` la búsqueda es O(log n) sin recorrer toda la colección.
- La colección `vueltas_rapidas` tiene un documento por carrera con el piloto más rápido,
  lo que hace que CU3 sea un simple `$group` por piloto sin JOINs.

**Colecciones y sus índices:**
| Colección | Índice | Optimiza |
|-----------|--------|----------|
| `vueltas_rapidas` | `(id_carrera, tiempo_vuelta_seg)` | ordenar por tiempo dentro de una carrera |
| `vueltas_rapidas` | `(nombre_piloto)` | contar vueltas rápidas por piloto (CU3) |
| `pit_stops` | `(id_carrera)` | agrupar pit stops de una carrera (CU4) |
| `pit_stops` | `(anio)` | filtrar pit stops por temporada |

### Neo4j → CU5 y CU6 (relaciones M:N complejas)

**CU5: ¿Qué pilotos han tenido más de 10 podios Y han corrido en más de 5 temporadas?**
**CU6: ¿Qué países han tenido mayor cantidad de carreras? ¿Qué país tiene más de 1 circuito?**

Neo4j es la opción correcta porque:
- Ambas preguntas son **consultas de grafos**: navegar relaciones entre nodos es
  la operación natural de Neo4j, mientras que en SQL requeriría múltiples JOINs
  con subqueries y GROUP BY anidados.
- CU5 recorre la relación `(Piloto)-[:PARTICIPO_EN]->(Temporada)` contando podios
  acumulados — en Neo4j esto es un `MATCH` + `WITH` + `WHERE`, sin JOINs.
- CU6 recorre `(Carrera)-[:REALIZADO_EN]->(Circuito)-[:UBICADO_EN]->(Pais)`,
  una cadena de 3 nodos que en SQL requeriría 2 JOINs + GROUP BY.
- La relación `PARTICIPO_EN` tiene el atributo `podios` que refleja los podios
  reales leídos desde SQL Server al momento de la sincronización.

**Nodos y relaciones:**
| Nodo | Atributos |
|------|-----------|
| `Piloto` | `nombre` |
| `Temporada` | `anio` |
| `Carrera` | `nombre` |
| `Circuito` | `nombre` |
| `Pais` | `nombre` |

| Relación | Desde→Hasta | Atributos |
|----------|------------|-----------|
| `PARTICIPO_EN` | Piloto→Temporada | `podios` |
| `REALIZADO_EN` | Carrera→Circuito | — |
| `UBICADO_EN` | Circuito→Pais | — |

### Redis → Sesiones de usuario

Redis es la opción correcta porque:
- Las sesiones son datos **temporales** — no tienen sentido en una base persistente
- Redis soporta TTL (Time To Live) nativo por clave, sin necesidad de jobs de limpieza
- Lectura/escritura en memoria: verificar si una sesión está activa es O(1)
- Cuando el TTL expira, Redis borra la clave automáticamente

**Flujo implementado:**
1. Usuario ingresa email y password
2. Se validan contra la tabla `Usuarios` de SQL Server (fuente de verdad)
3. Si son correctas, se crea la sesión en Redis según el **rol**:
   - `admin` → `r.set(clave, rol)` sin TTL — sesión permanente hasta logout explícito
   - `director` / `prensa` → `r.setex(clave, 600, rol)` — TTL deslizante de 600 segundos
4. El valor guardado en Redis es el **rol** del usuario (necesario para saber qué TTL aplicar al renovar)
5. Cada acción exitosa en el menú llama a `renovar_sesion()` → `r.expire(clave, 600)` — resetea el contador
6. Si el usuario no hace nada por más de 600s → Redis expira la clave automáticamente → el menú detecta TTL=-2 y cierra la sesión
7. Al hacer logout → se elimina la clave manualmente → se registra en Auditoria
8. Cada login/logout se registra en la tabla `Auditoria` de SQL (historial permanente)

**Por qué admin sin TTL:**
Admin es el operador del sistema. No tiene sentido expulsarlo por inactividad —
puede estar monitoreando sin interactuar. Director y prensa son usuarios externos
con acceso limitado, por lo que la expiración por inactividad sí aplica.

**Por qué TTL deslizante y no fijo:**
Un TTL fijo expira aunque el usuario esté activo. Para un portal de consultas,
lo natural es que la sesión se mantenga mientras el usuario opera y expire solo
si deja de interactuar. Redis devuelve -2 cuando la clave no existe (expirada)
y -1 cuando existe sin TTL (admin) — ambos casos se manejan en `verificar_sesion()`.

---

## CRUD — Gestión de datos maestros

### Decisión: toda escritura pasa por SQL
Las operaciones CRUD del sistema solo modifican **SQL Server**. Los NoSQL son
entornos de lectura y nunca reciben escrituras directas desde el flujo principal.

**Justificación:** si se permitiera escribir directamente en un NoSQL, se rompe
la garantía de consistencia. Un insert en Cassandra sin el correspondiente insert
en SQL generaría un dato huérfano que desaparecería en la próxima sincronización.

### Operaciones implementadas y su narrativa F1

| Operación SQL | Narrativa F1 | Propagación |
|---------------|--------------|-------------|
| Listar Pilotos/Equipos | Ver estado actual antes de operar | Solo lectura — sin sync |
| Insertar Piloto | Rookie firma contrato para la temporada | Sync → Cassandra, MongoDB, Neo4j |
| Actualizar Director | Cambio de director técnico del equipo | Sync → Cassandra, MongoDB, Neo4j |
| Transferir Piloto | Piloto cambia de equipo (ej: Hamilton a Ferrari) | Sync → victorias históricas cambian de equipo en Cassandra |
| Eliminar Piloto | Retiro o pérdida de asiento | Solo pilotos sin resultados (FK protege integridad) |

### Validación de inputs
Las operaciones CRUD validan el input antes de llegar a SQL:
- IDs: se piden hasta recibir un número válido (`_pedir_int`)
- Fechas: se validan con `datetime.strptime` formato `YYYY-MM-DD` (`_pedir_fecha`)
- Errores SQL (FK violation, duplicado) se traducen a mensajes legibles en lugar de mostrar el error crudo de pymssql

### Comportamiento ante fallo en el sync post-CRUD
- Si SQL confirma → el dato está seguro independientemente de lo que pase después
- Si un NoSQL falla en la propagación → SQL tiene el estado correcto
- El sistema informa cuántas bases se sincronizaron (`✅ Entornos NoSQL sincronizados: 2/3`)
- El siguiente CRUD vuelve a intentar la sincronización completa (operación idempotente)

### Limitación conocida: transferencias históricas
Cassandra desnormaliza el equipo del piloto al momento del sync (JOIN con `Pilotos.IdEquipo` actual).
Si se transfiere a un piloto, sus victorias históricas se reasignan al nuevo equipo.
En producción, `Resultados` debería incluir `IdEquipo` para preservar la atribución histórica.

---

## Decisiones técnicas

### Cassandra + Python 3.12
Python 3.12 eliminó el módulo `asyncore` que el driver de Cassandra usaba por defecto.
Solución aplicada:
- Instalar dependencias de sistema: `sudo apt-get install python3-dev libev-dev libffi-dev`
- Reinstalar el driver: `pip install cassandra-driver --no-cache-dir --force-reinstall`
- En el código, setear el event loop de asyncio antes de importar el cluster:
  ```python
  import asyncio
  asyncio.set_event_loop(asyncio.new_event_loop())
  from cassandra.io.asyncioreactor import AsyncioConnection
  cluster = Cluster(['localhost'], connection_class=AsyncioConnection)
  ```

### Conexión lazy en Cassandra
El objeto `cluster` y `session` de Cassandra **no se inicializan al importar el módulo**.
Se usa una función `conectar()` que se llama explícitamente antes del primer uso.
Esto evita que importar `cassandraDB` en `main.py` dispare una conexión automática
y falle si Cassandra no está disponible en ese momento.

### Neo4j driver v5 — `.consume()` obligatorio
El driver de Neo4j v5 no garantiza que una escritura se comitee hasta que el resultado
sea consumido. Por eso todas las operaciones de escritura usan `.consume()`:
```python
session.run("MERGE ...", params).consume()
```
Sin esto, el grafo aparece vacío aunque la query no lance errores.

### Entorno virtual (.venv)
Se usa un entorno virtual para aislar las dependencias del proyecto.
El directorio `.venv/` está en `.gitignore` — cada integrante debe crearlo localmente con:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Decisiones pendientes

- [x] Definir si PARTICIPACION registra atributos adicionales → sin atributos extra
- [x] Confirmar estructura de documentos MongoDB para PitStops → colecciones `pit_stops` y `vueltas_rapidas`
- [x] Confirmar atributos de relaciones en Neo4j → `PARTICIPO_EN` tiene `podios`
- [x] Completar justificación de MongoDB (CU3, CU4) → completado arriba
- [x] Completar justificación de Neo4j (CU5, CU6) → completado arriba
- [x] Implementar `poblar_desde_sql()` en Neo4j → implementado, lee desde SQL y puebla el grafo
- [x] Corregir bugs en `neo4jDB.py` → resueltos: `.consume()` en todas las escrituras, `count(ca)` en CU6
- [x] CU5 umbral `>5 temporadas` sin datos suficientes → resuelto agregando temporadas 2016-2018
