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

### 2. Incorporación de la entidad USUARIOS
**Cambio:** se agregó la entidad USUARIOS al DER con los atributos:
`id_usuario`, `email`, `password`, `nombre_completo`, `rol`.

**Justificación:** el sistema requiere autenticación para operar. USUARIOS no estaba
en el DER original porque el enunciado no especifica gestión de acceso, pero es
necesaria para implementar el manejo de sesiones con Redis (TTL por usuario).
El rol permite diferenciar permisos entre administrador, director de carrera y prensa.

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
| Neo4j | Grafo de relaciones piloto↔temporada, equipo↔circuito | SQL Server |
| Redis | Sesiones de usuario con TTL | SQL Server (valida credenciales) |

**Justificación:** ninguna base NoSQL tiene datos que no existan en SQL Server.
Esto garantiza consistencia y permite reconstruir cualquier base NoSQL desde cero
en caso de pérdida de datos.

---

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

*(completar cuando se implemente mongoDB.py)*

### Neo4j → CU5 y CU6 (relaciones M:N complejas)

*(completar cuando se complete neo4jDB.py)*

### Redis → Sesiones de usuario

Redis es la opción correcta porque:
- Las sesiones son datos **temporales** — no tienen sentido en una base persistente
- Redis soporta TTL (Time To Live) nativo por clave, sin necesidad de jobs de limpieza
- Lectura/escritura en memoria: verificar si una sesión está activa es O(1)
- Cuando el TTL expira, Redis borra la clave automáticamente

**Flujo implementado:**
1. Usuario ingresa email y password
2. Se validan contra la tabla `Usuarios` de SQL Server (fuente de verdad)
3. Si son correctas, se crea la sesión en Redis con TTL:
   - Dispositivo de confianza → 600 segundos (10 minutos)
   - Dispositivo no confiable → 5 segundos
4. El valor guardado en Redis es el **rol** del usuario (admin/director/prensa)
5. Al hacer logout → se elimina la clave manualmente

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

- [ ] Definir si PARTICIPACION registra atributos adicionales (ej: puntos por temporada)
- [ ] Confirmar estructura de documentos MongoDB para PitStops y Penalizaciones
- [ ] Confirmar atributos de relaciones en Neo4j (PARTICIPO_EN ya tiene `podios`)
- [ ] Completar justificación de MongoDB (CU3, CU4) cuando se implemente
- [ ] Completar justificación de Neo4j (CU5, CU6) cuando se complete

- [ ] Definir si PARTICIPACION registra atributos adicionales (ej: puntos por temporada)
- [ ] Confirmar estructura de documentos MongoDB para PitStops y Penalizaciones
- [ ] Confirmar atributos de relaciones en Neo4j (PARTICIPO_EN ya tiene `podios`)
