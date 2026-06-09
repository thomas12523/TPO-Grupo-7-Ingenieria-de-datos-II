# TPO Grupo 7 — Sistema F1 Multi-Base de Datos

Sistema de gestión de Fórmula 1 utilizando SQL Server, Cassandra, MongoDB, Neo4j y Redis.

## Arquitectura

| Base de datos | Responsabilidad | Casos de uso |
|---------------|----------------|--------------|
| **SQL Server** | Fuente de verdad — esquema completo del DER | Base de la que todas las demás leen |
| **Cassandra** | Resultados históricos desnormalizados para analítica | CU1: pilotos multicampeones / CU2: equipos con más victorias |
| **MongoDB** | Pit stops y vueltas rápidas como documentos | CU3: vuelta más rápida / CU4: promedio de pit stops |
| **Neo4j** | Grafo de relaciones piloto↔temporada, país↔circuito | CU5 / CU6 |
| **Redis** | Sesiones con TTL deslizante por rol | Login / logout / expiración por inactividad |

> **Regla de oro:** ninguna base NoSQL tiene datos que no existan en SQL Server. Toda escritura entra por SQL y se propaga a los NoSQL automáticamente.

> Ver decisiones de diseño y justificaciones en [`docs/DISEÑO.md`](docs/DISEÑO.md).

---

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Python 3.10 o superior

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd TPO-Grupo-7-Ingenieria-de-datos-II
```

### 2. Crear y activar el entorno virtual

```bash
# Crear (solo la primera vez)
python3 -m venv .venv

# Activar
source .venv/bin/activate          # Mac / Linux / WSL / Git Bash
.venv\Scripts\activate.bat         # Windows CMD
.venv\Scripts\Activate.ps1         # Windows PowerShell
```

### 3. Instalar dependencias del sistema (WSL / Linux)

```bash
sudo apt-get install -y python3-dev libev-dev libffi-dev
```

> En Mac: `brew install libev` — En Windows nativo no es necesario.

### 4. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 5. Levantar los contenedores Docker

```bash
docker compose up -d
```

Verificar que los 5 contenedores estén corriendo:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

> **Cassandra tarda ~30 segundos** en estar lista. Confirmar con:
> `docker logs f1_cassandra 2>&1 | tail -3`

---

## Ejecución

```bash
source .venv/bin/activate
python main.py
```

`main.py` hace todo automáticamente al arrancar:
1. Verifica conexiones a las 5 bases
2. Crea las 12 tablas SQL y carga los datos de prueba (idempotente)
3. Sincroniza Cassandra, MongoDB y Neo4j desde SQL

---

## Paso a paso para la demo / presentación

### Terminales necesarias

Abrí 5 terminales y el browser antes de empezar:

```bash
# T2 — SQL Server
docker exec -it f1_sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Password123!" -C -d master

# T3 — Redis
docker exec -it f1_redis redis-cli

# T4 — Cassandra
docker exec -it f1_cassandra cqlsh
# dentro: USE f1_keyspace;

# T5 — MongoDB
docker exec -it f1_mongodb mongosh
# dentro: use f1_db

# Browser — Neo4j
# http://localhost:7474  usuario: neo4j  password: password123
```

---

### Bloque 1 — Arranque y verificación de conexiones

**T1:** `python main.py`
- Verificar que las 5 bases digan `✅ Conectado`
- Sync muestre `3/3 bases sincronizadas`
- Login: `admin@f1.com` / `admin123`

**T3 — Redis:**
```
KEYS sesion:*
GET sesion:admin@f1.com       → "admin"
TTL sesion:admin@f1.com       → -1 (sin límite)
```

---

### Bloque 2 — Casos de uso

**CU1 — T1 opción 1** `[Cassandra]`
```sql
-- T4 verificar origen
SELECT nombre_piloto, anio FROM campeonatos_por_piloto WHERE fue_campeon = true ALLOW FILTERING;
```

**CU2 — T1 opción 2** `[Cassandra]`
```sql
-- T4 verificar
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Red Bull Racing';
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Mercedes AMG';
```

**CU3 — T1 opción 3** `[MongoDB]`
- Seleccioná piloto → revisá detalle → elegí otro → presioná 0
```javascript
// T5 verificar
db.vueltas_rapidas.countDocuments({nombre_piloto: "Lewis Hamilton"})
```

**CU4 — T1 opción 4** `[MongoDB]`
```javascript
// T5 verificar
db.pit_stops.aggregate([{$group: {_id: "$id_carrera", total: {$sum: 1}}}])
```

**CU5 — T1 opción 5** `[Neo4j]`
```cypher
// Browser Neo4j verificar
MATCH (p:Piloto)-[r:PARTICIPO_EN]->(t:Temporada)
WITH p, sum(r.podios) AS total, count(t) AS temps
WHERE total > 10 AND temps > 5
RETURN p.nombre, total, temps ORDER BY total DESC
```

**CU6 — T1 opción 6** `[Neo4j]`
```cypher
// Browser Neo4j verificar
MATCH (ca:Carrera)-[:REALIZADO_EN]->(c:Circuito)-[:UBICADO_EN]->(p:Pais)
RETURN p.nombre, count(ca) AS carreras ORDER BY carreras DESC
```

---

### Bloque 3 — CRUD con sincronización visible

**Objetivo: transferir a Verstappen a McLaren y mostrar el cambio en Cassandra.**

**Paso 1 — Estado antes (T4):**
```sql
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Red Bull Racing';
-- → 19
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'McLaren';
-- → 0
```

**Paso 2 — Insertar piloto nuevo (T1: opción 7 → 1):**
```
Nombre: Carlos Sainz / Fecha: 1994-09-01 / Nacionalidad: Española / Equipo: 3
```
Verificar en T2:
```sql
SELECT IdPiloto, Nombre, IdEquipo FROM Pilotos; GO
```

**Paso 3 — Transferir Verstappen a McLaren (T1: opción 7 → 3):**
```
Piloto ID: 1 → Equipo ID: 4
```

**Paso 4 — Verificar sync en Cassandra (T4):**
```sql
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Red Bull Racing';
-- → 0  (cambió)
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'McLaren';
-- → 19 (sincronizado)
```

**Paso 5 — Confirmar con CU2 desde la app (T1: opción 2):**
- McLaren ahora aparece con victorias — dato consistente entre SQL, Cassandra y la app.

**Paso 6 — Eliminar Carlos Sainz (T1: opción 7 → 4):**
- Verificar con `L` que desapareció.

**Paso 7 — Probar validación (T1: opción 7 → 1):**
```
ID del Equipo: 99
→ [❌] ID inexistente — verificá que el ID ingresado exista en la lista.
→ Sin sync, sin crash.
```

---

### Bloque 4 — Sesiones Redis

**Dos sesiones simultáneas:**
```bash
# Segunda terminal
python main.py   # login con director@f1.com / dir456
```
```
# T3 — Redis
KEYS sesion:*
TTL sesion:director@f1.com    → número positivo (600s)
TTL sesion:admin@f1.com       → -1 (sin límite)
```

**Auditoria en SQL (T2):**
```sql
SELECT u.Email, a.Accion, a.FechaHora
FROM Auditoria a JOIN Usuarios u ON a.IdUsuario = u.IdUsuario
ORDER BY a.FechaHora DESC; GO
```
Muestra el historial permanente de logins/logouts — complementa las sesiones activas de Redis.

---

### Bloque 5 — Tolerancia a fallos

```bash
# Bajar Cassandra en vivo
docker stop f1_cassandra
```
- T1 opción 1 (CU1) → error limpio, app no crashea
- T1 opción 5 (CU5) → sigue funcionando
- T1 CRUD → muestra `2/3 sincronizados`, SQL sigue escribiendo

```bash
# Recuperar
docker start f1_cassandra
# Esperar ~30 segundos
```
- Siguiente CRUD → `3/3` — Cassandra sincronizada automáticamente.

---

## Manejo de contenedores

```bash
docker compose start         # arrancar (uso diario)
docker compose stop          # pausar
docker compose up -d         # primera vez o después de down
docker compose down          # elimina contenedores (datos quedan)
docker compose down -v       # elimina contenedores Y datos
```

---

## Puertos

| Servicio | Puerto | Interfaz web |
|----------|--------|-------------|
| SQL Server | 1433 | — |
| MongoDB | 27017 | — |
| Cassandra | 9042 | — |
| Neo4j | 7687 (bolt) | http://localhost:7474 |
| Redis | 6379 | — |

---

## Usuarios del sistema

| Email | Password | Rol | TTL de inactividad |
|-------|----------|-----|-------------------|
| admin@f1.com | admin123 | admin | sin límite |
| director@f1.com | dir456 | director | 600 s |
| prensa@f1.com | prensa789 | prensa | 600 s |

TTL deslizante: cada acción resetea el contador. `admin` no tiene expiración.

---

## Notas técnicas

### Cassandra + Python 3.12
Python 3.12 eliminó el módulo `asyncore`. Fix aplicado en `cassandraDB.py`:
```python
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())
from cassandra.io.asyncioreactor import AsyncioConnection
cluster = Cluster(['localhost'], connection_class=AsyncioConnection)
```

### Datos de prueba
- 5 equipos, 5 pilotos, 5 circuitos, **8 temporadas (2016–2023)**
- **40 carreras históricas** (5 por temporada)
- **120 resultados** (top 3 por carrera)
- 3 usuarios del sistema
- Temporadas 2016–2018 incluidas para que CU5 (`>10 podios AND >5 temporadas`) devuelva resultados reales
