# Decisiones de Diseño — TPO Grupo 7 F1

Documento de registro de decisiones arquitectónicas y de modelado, con sus justificaciones técnicas, para ser referenciado durante la presentación.

---

## DER original

El DER recibido (ver `consignas y der/DER-F1-GRUPO6.jpg`) define las siguientes entidades:
`EQUIPO`, `PILOTO`, `CIRCUITO`, `TEMPORADA`, `CARRERA`, `PARTICIPACION`, `RENDIMIENTO`, `RESULTADO`, `PIT_STOP`, `PENALIZACION`.

---

## Modificaciones al DER

### 1. Eliminación de `penalizacion_aplicada` de RESULTADO

**Cambio:** se eliminó el atributo `penalizacion_aplicada` de la entidad RESULTADO.

**Justificación:** el atributo era redundante. La entidad PENALIZACION ya registra la misma información con mayor detalle (`tipo` y `tiempo_adicional`), relacionada por `id_piloto` e `id_carrera`. Mantener ambos generaba riesgo de inconsistencia: si se actualizaba PENALIZACION, el campo en RESULTADO podía quedar desactualizado sin ninguna garantía de integridad.

---

### 2. Incorporación de la entidad USUARIOS

**Cambio:** se agregó USUARIOS con los atributos `id_usuario`, `email`, `password`, `nombre_completo`, `rol`, `id_equipo (nullable FK → Equipos)`.

**Justificación:** el sistema requiere autenticación para operar. El atributo `IdEquipo` (nullable) conecta USUARIOS al modelo F1: un usuario con rol `director` tiene asignado el equipo que gestiona, mientras que `admin` y `prensa` lo tienen en NULL. Esto permite consultas del tipo "qué equipo gestiona el director actualmente conectado" combinando Redis (sesión activa) con SQL (datos del equipo).

---

### 3. Incorporación de la entidad AUDITORIA

**Cambio:** se agregó AUDITORIA con los atributos `id_auditoria`, `id_usuario (FK → Usuarios)`, `accion`, `fecha_hora`.

**Justificación:** Redis registra la sesión *activa*, pero cuando el TTL expira ese dato desaparece automáticamente. AUDITORIA actúa como complemento persistente: cada login y logout queda registrado en SQL con marca temporal, independientemente de la expiración de la sesión. Esto demuestra la interacción Redis ↔ SQL:

- **Redis** → quién está conectado ahora (lectura O(1), expiración automática)
- **SQL** → quién se conectó históricamente (persistente, consultable)

Acciones registradas: `login`, `logout`, `expiro`.

---

### 4. Incorporación de la entidad HISTORIALEQUIPOS

**Cambio:** se agregó HISTORIALEQUIPOS con los atributos `id_historial`, `id_piloto (FK → Pilotos)`, `id_equipo (FK → Equipos)`, `anio_desde`, `anio_hasta (nullable)`.

**Justificación:** la tabla `Pilotos` solo registra el equipo actual de cada piloto. Para representar en el grafo Neo4j la relación histórica piloto↔equipo con su período de vigencia (necesaria para CU5), se incorporó esta tabla. `anio_hasta` en NULL indica que el piloto sigue activo en ese equipo. Esta información alimenta la relación `CORRIO_PARA` en Neo4j.

---

## Arquitectura multi-base

### SQL Server como fuente de verdad

Todas las entidades del DER se crean en SQL Server (13 tablas). Las bases NoSQL se pueblan consultando SQL Server para garantizar consistencia de IDs y datos.

| Base | Paradigma | Rol en el sistema | Poblada desde |
|------|-----------|------------------|--------------|
| SQL Server | Relacional | Fuente de verdad, esquema completo | — |
| Cassandra | Columnar | Resultados históricos desnormalizados para analítica | SQL Server |
| MongoDB | Documental | Pit stops y vueltas rápidas como documentos | SQL Server |
| Neo4j | Grafo | Relaciones piloto↔equipo↔temporada↔circuito↔país | SQL Server |
| Redis | Clave-valor | Sesiones de usuario con TTL | SQL Server (valida credenciales) |

Ninguna base NoSQL tiene datos que no existan previamente en SQL Server. Esto garantiza que cualquier base NoSQL pueda reconstruirse desde cero re-ejecutando la sincronización.

---

## Consistencia eventual y tolerancia a fallos

### Modelo de consistencia

El sistema implementa **consistencia eventual** (modelo BASE) para la capa NoSQL:

- **SQL Server es ACID**: toda escritura es atómica y durable. Es la única fuente de verdad.
- **Las bases NoSQL son entornos de lectura**: nunca se escriben directamente desde el flujo principal. Solo se actualizan vía sincronización desde SQL.
- **La sincronización es idempotente**: `_sincronizar_en_segundo_plano()` elimina todos los datos de cada NoSQL y los reinsertar desde SQL. Ejecutarla N veces produce el mismo resultado. MongoDB usa `delete_many({})` y Cassandra usa `TRUNCATE` antes de reinsertar.

### Flujo de escritura

```
Usuario → SQL Server (ACID, commit)
               └── _sincronizar_en_segundo_plano()
                         ├── Cassandra  (independiente)
                         ├── MongoDB    (independiente)
                         └── Neo4j      (independiente)
```

### Comportamiento ante fallos

Cada base NoSQL se sincroniza de forma **independiente**. Si una falla durante el sync:

- Las demás continúan y se sincronizan correctamente
- SQL ya tiene el dato correcto → no hay pérdida de datos
- El sistema informa cuántas bases se actualizaron (`⚠️ 2/3 sincronizados`)
- Al recuperarse la base caída, el siguiente CRUD dispara la sincronización completa automáticamente

### ¿Por qué no hay rollback distribuido?

Porque no es necesario. Si SQL confirma el cambio, el dato está persistido y es seguro. Si un NoSQL falla en el sync, es un problema de *disponibilidad de lectura eventual*, no de *integridad de datos*. La operación idempotente actúa como mecanismo de recuperación sin necesidad de coordinar entre bases.

---

## Justificación de cada base NoSQL

### Cassandra → CU1 y CU2

**CU1:** ¿Qué pilotos han ganado múltiples campeonatos mundiales?
**CU2:** ¿Qué equipos han tenido más victorias en la historia?

Cassandra es la opción correcta porque:

- Ambas consultas requieren procesar **grandes volúmenes de datos históricos** que crecen constantemente con cada nueva carrera
- Cassandra está optimizada para **escrituras masivas y lecturas por clave de partición** — el modelo se diseña por consulta, no por entidad
- `campeonatos_por_piloto`: partition key `nombre_piloto` → todas las temporadas de un piloto en una sola partición, lectura O(1)
- `victorias_por_equipo`: partition key `nombre_equipo` → contar victorias de un equipo es una lectura directa sin recorrer toda la tabla
- En SQL, CU2 requeriría un JOIN entre Resultados, Carreras y Equipos + GROUP BY. En Cassandra esa respuesta ya está pre-calculada en la estructura de la tabla

### MongoDB → CU3 y CU4

**CU3:** ¿Qué pilotos han marcado la vuelta más rápida en diversas carreras?
**CU4:** ¿Cuántos pit stops se realizan en promedio por carrera?

MongoDB es la opción correcta porque:

- Los pit stops y vueltas rápidas son datos **semiestructurados**: pueden tener atributos variables sin necesidad de un esquema rígido
- CU3 y CU4 requieren **agregaciones** (equivalentes a GROUP BY + AVG/COUNT en SQL), que MongoDB resuelve nativamente con su pipeline (`$group`, `$avg`, `$sum`)
- Con el índice `idx_carrera`, leer todos los pit stops de una carrera es O(log n) sin recorrer la colección completa

**Colecciones e índices:**

| Colección | Índice | Optimiza |
|-----------|--------|----------|
| `vueltas_rapidas` | `(id_carrera, tiempo_vuelta_seg)` | Ordenar por tiempo dentro de una carrera |
| `vueltas_rapidas` | `(nombre_piloto)` | Contar vueltas rápidas por piloto — CU3 |
| `pit_stops` | `(id_carrera)` | Agrupar pit stops de una carrera — CU4 |
| `pit_stops` | `(anio)` | Filtrar pit stops por temporada |

### Neo4j → CU5 y CU6

**CU5:** ¿Qué pilotos han tenido más de 10 podios Y han corrido en más de 5 temporadas?
**CU6:** ¿Qué países han tenido mayor cantidad de carreras? ¿Qué país tiene más de 1 circuito?

Neo4j es la opción correcta porque:

- Ambas consultas son **traversals de grafo**: navegar relaciones entre nodos es la operación natural de Neo4j, mientras que en SQL requeriría múltiples JOINs con subqueries y GROUP BY anidados
- CU5 recorre `(Piloto)-[:PARTICIPO_EN]->(Temporada)` acumulando podios por temporada — un simple `MATCH + WITH + WHERE` sin JOINs
- CU6 recorre `(Carrera)-[:REALIZADO_EN]->(Circuito)-[:UBICADO_EN]->(Pais)`, una cadena de 3 nodos que en SQL requeriría 2 JOINs + GROUP BY

**Nodos:**

| Nodo | Atributos |
|------|-----------|
| `Piloto` | `nombre` |
| `Equipo` | `nombre` |
| `Temporada` | `anio` |
| `Carrera` | `nombre` |
| `Circuito` | `nombre` |
| `Pais` | `nombre` |

**Relaciones:**

| Relación | Desde → Hasta | Atributos | Fuente SQL |
|----------|--------------|-----------|-----------|
| `PARTICIPO_EN` | Piloto → Temporada | `podios` | Resultados (COUNT pos ≤ 3) |
| `COMPITIO_EN` | Piloto → Carrera | `posicion`, `equipo` | Resultados |
| `CORRIO_PARA` | Piloto → Equipo | `desde`, `hasta` | HistorialEquipos |
| `REALIZADO_EN` | Carrera → Circuito | — | Carreras + Circuitos |
| `UBICADO_EN` | Circuito → Pais | — | Circuitos |

### Redis → Sesiones de usuario

Redis es la opción correcta porque:

- Las sesiones son datos **temporales** — no tienen sentido en una base persistente
- Redis soporta TTL nativo por clave, sin necesidad de jobs de limpieza externos
- Verificar si una sesión está activa es O(1) en memoria

**Flujo de sesión implementado:**

1. El usuario ingresa email y contraseña
2. Se validan contra la tabla `Usuarios` de SQL Server
3. Si son correctas, se crea la sesión en Redis según el rol:
   - `admin` → `r.set(clave, rol)` sin TTL — permanente hasta logout explícito
   - `director` / `prensa` → `r.setex(clave, 600, rol)` — TTL deslizante de 600 segundos
4. El valor almacenado en Redis es el **rol** del usuario (necesario para saber qué TTL aplicar al renovar)
5. Cada acción en el menú llama a `renovar_sesion()` → `r.expire(clave, 600)` — reinicia el contador
6. Si el usuario no interactúa por más de 600s → Redis expira la clave → el menú detecta TTL = -2 y cierra la sesión
7. Al hacer logout → se elimina la clave → se registra en Auditoria

**Por qué `admin` sin TTL:** el administrador del sistema puede estar monitoreando sin interactuar activamente. Expulsarlo por inactividad no tiene sentido operativo. Director y prensa son usuarios externos con acceso limitado, por lo que la expiración por inactividad sí aplica.

**Por qué TTL deslizante y no fijo:** un TTL fijo expira aunque el usuario esté activo. El TTL deslizante mantiene la sesión mientras el usuario opera y la cierra solo si deja de interactuar — comportamiento natural para un portal de consultas.

---

## CRUD — Gestión de datos maestros

### Toda escritura pasa por SQL

Las operaciones CRUD solo modifican SQL Server. Las bases NoSQL nunca reciben escrituras directas desde el flujo principal.

Si se permitiera escribir directamente en un NoSQL, se rompería la garantía de consistencia: un insert en Cassandra sin el correspondiente insert en SQL generaría un dato huérfano que desaparecería en la próxima sincronización.

### Operaciones y su impacto en los casos de uso

Las operaciones modifican `Resultados` y `PitStops` — exactamente las tablas que alimentan los casos de uso NoSQL. El impacto es inmediato y verificable tras el sync.

| Operación | Tabla SQL | CU impactado |
|-----------|-----------|-------------|
| Listar pilotos / carreras / resultados | — | Solo lectura, sin sync |
| Registrar resultado (pos = 1) | `Resultados` | CU2: equipo suma victoria · CU3: piloto aparece en vueltas rápidas |
| Registrar resultado (pos ≤ 3) | `Resultados` | CU5: piloto suma podio y/o temporada |
| Eliminar resultado | `Resultados` | Revierte CU2, CU3, CU5 |
| Registrar pit stop | `PitStops` | CU4: promedio de pit stops sube |
| Eliminar pit stops | `PitStops` | CU4: promedio de pit stops baja |

**Puntos F1 automáticos:** el sistema asigna puntos según la escala oficial (1→25, 2→18, 3→15, 4→12 …) sin pedirlos manualmente.

**Carreras de demo (2024–2026):** las carreras ID 41–55 no tienen resultados pre-cargados, permitiendo insertar datos frescos sin colisionar con registros históricos. En producción representarían las carreras de la temporada en curso.

### Validación de inputs

- **IDs:** se solicitan hasta recibir un entero válido (`_pedir_int`) — nunca llega un string a SQL
- **Decimales:** ídem con float (`_pedir_float`) — usado para tiempo de pit stop
- **Errores SQL:** FK violation, clave duplicada y errores de tipo se traducen a mensajes legibles (`_mensaje_error_sql`)
- **Deletes vacíos:** se verifica `cursor.rowcount` — si ninguna fila fue afectada, se informa y no se dispara el sync innecesariamente

---

## Decisiones técnicas

### Cassandra + Python 3.12

Python 3.12 eliminó el módulo `asyncore`, que el driver de Cassandra usaba por defecto. Solución aplicada en `cassandraDB.py`:

```python
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())
from cassandra.io.asyncioreactor import AsyncioConnection
cluster = Cluster(['localhost'], connection_class=AsyncioConnection)
```

### Conexión lazy en Cassandra

El objeto `cluster` y `session` de Cassandra no se inicializan al importar el módulo. Se usa una función `conectar()` que se llama explícitamente antes del primer uso. Esto evita que importar `cassandraDB` en `main.py` dispare una conexión automática y falle si Cassandra aún no está disponible.

### Neo4j driver v5 — `.consume()` obligatorio

El driver v5 de Neo4j no garantiza que una escritura se commitee hasta que el resultado sea consumido. Por eso todas las operaciones de escritura en el grafo usan `.consume()`:

```python
session.run("MERGE ...", params).consume()
```

Sin esto, el grafo aparece vacío aunque la query no lance errores.

### Sync idempotente en Cassandra

La sincronización de Cassandra ejecuta `TRUNCATE` en las tres tablas antes de reinsertar desde SQL. Esto garantiza que el sync sea idempotente: si un resultado fue insertado por CRUD y luego eliminado, el TRUNCATE asegura que Cassandra no conserve datos huérfanos. MongoDB aplica el mismo principio con `delete_many({})`.

### Entorno virtual (.venv)

El directorio `.venv/` está en `.gitignore`. Cada integrante debe crearlo localmente:

```bash
python -m venv .venv
source .venv/bin/activate   # o el equivalente en Windows
pip install -r requirements.txt
```
