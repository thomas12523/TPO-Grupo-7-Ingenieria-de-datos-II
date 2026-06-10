# TPO Grupo 7 — Sistema de Gestión F1 Multi-Base de Datos

Sistema de consulta y gestión de datos de Fórmula 1 implementado sobre cinco bases de datos heterogéneas: SQL Server, Apache Cassandra, MongoDB, Neo4j y Redis. El objetivo es demostrar el uso de distintos paradigmas de almacenamiento en un contexto real, aplicando consistencia eventual, tolerancia a fallos y gestión de sesiones.

> Las decisiones de diseño y justificaciones técnicas se encuentran en [`docs/DISEÑO.md`](docs/DISEÑO.md).

---

## Arquitectura

| Base de datos | Paradigma | Responsabilidad | Casos de uso |
|---------------|-----------|----------------|--------------|
| **SQL Server** | Relacional | Fuente de verdad — esquema completo del DER | — |
| **Cassandra** | Columnar | Resultados históricos desnormalizados | CU1: pilotos multicampeones · CU2: equipos con más victorias |
| **MongoDB** | Documental | Pit stops y vueltas rápidas | CU3: vuelta más rápida · CU4: promedio de pit stops |
| **Neo4j** | Grafo | Relaciones piloto↔equipo↔temporada↔circuito↔país | CU5: pilotos eficientes · CU6: países con más carreras |
| **Redis** | Clave-valor en memoria | Sesiones de usuario con TTL por rol | Login / logout / expiración por inactividad |

**Principio de diseño:** toda escritura entra por SQL Server (ACID). Las bases NoSQL son entornos de lectura que se sincronizan automáticamente desde SQL. Ningún dato existe en una base NoSQL sin existir primero en SQL.

---

## Requisitos previos

| Herramienta | Versión mínima | Descarga |
|-------------|---------------|---------|
| Docker Desktop | Cualquier versión reciente | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Python | 3.10 o superior | [python.org](https://www.python.org/downloads/) |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd TPO-Grupo-7-Ingenieria-de-datos-II
```

### 2. Crear el entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

| Sistema operativo | Comando |
|-------------------|---------|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| macOS / Linux / WSL | `source .venv/bin/activate` |

> **Windows PowerShell:** si aparece el error `running scripts is disabled`, ejecutar primero:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Instalar dependencias del sistema (solo Linux / WSL)

```bash
sudo apt-get install -y python3-dev libev-dev libffi-dev
```

> En macOS: `brew install libev`. En Windows nativo este paso no es necesario.

### 5. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 6. Levantar los contenedores Docker

```bash
docker compose up -d
```

Verificar que los cinco contenedores estén activos:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

> **Importante — Cassandra:** tarda entre 1 y 2 minutos en estar lista. Esperar hasta que el siguiente comando devuelva la versión del servidor antes de ejecutar la aplicación:
> ```bash
> docker exec f1_cassandra cqlsh -e "SELECT release_version FROM system.local"
> ```

---

## Ejecución

```bash
python main.py
```

Al iniciarse, la aplicación realiza automáticamente:
1. Verificación de conectividad con las cinco bases de datos
2. Creación del esquema SQL (13 tablas) y carga del dataset de prueba — operación idempotente
3. Sincronización de Cassandra, MongoDB y Neo4j desde SQL Server

---

## Acceso directo a las bases de datos

Para verificar los datos en cada base durante la demostración, abrir una terminal por base:

```bash
# SQL Server
docker exec -it f1_sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Password123!" -C -d master

# Redis
docker exec -it f1_redis redis-cli

# Cassandra
docker exec -it f1_cassandra cqlsh
# Dentro de cqlsh: USE f1_keyspace;

# MongoDB
docker exec -it f1_mongodb mongosh
# Dentro de mongosh: use f1_db

# Neo4j — interfaz web
# Abrir en el navegador: http://localhost:7474
# Usuario: neo4j   Contraseña: password123
```

---

## Guía de demostración

### Bloque 1 — Arranque y sesiones Redis

**Iniciar la aplicación:**
```
python main.py
→ 5/5 bases conectadas
→ 3/3 bases sincronizadas
→ Login: admin@f1.com / admin123
```

**Verificar sesión en Redis:**
```
KEYS sesion:*
GET  sesion:admin@f1.com    → "admin"
TTL  sesion:admin@f1.com    → -1  (sin límite de tiempo)
```

**Abrir una segunda sesión (otra terminal):**
```
python main.py  →  login: director@f1.com / dir456
```
```
TTL sesion:director@f1.com  → 600  (expira por inactividad)
TTL sesion:admin@f1.com     → -1   (permanente)
```

**Historial de auditoría en SQL:**
```sql
SELECT u.Email, a.Accion, a.FechaHora
FROM Auditoria a JOIN Usuarios u ON a.IdUsuario = u.IdUsuario
ORDER BY a.FechaHora DESC; GO
```

---

### Bloque 2 — Casos de uso

**CU1 — Pilotos con múltiples campeonatos** `[Cassandra]`

Opción 1 en la app. Verificar en Cassandra:
```sql
SELECT nombre_piloto, anio FROM campeonatos_por_piloto WHERE fue_campeon = true ALLOW FILTERING;
```

**CU2 — Equipos con más victorias históricas** `[Cassandra]`

Opción 2 en la app. Verificar en Cassandra:
```sql
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Red Bull Racing';
SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Mercedes AMG';
```

**CU3 — Pilotos con la vuelta más rápida** `[MongoDB]`

Opción 3 en la app — lista interactiva: seleccionar piloto por número, ver detalle, presionar 0 para volver. Verificar en MongoDB:
```javascript
db.vueltas_rapidas.countDocuments({nombre_piloto: "Lewis Hamilton"})
```

**CU4 — Promedio de pit stops por carrera** `[MongoDB]`

Opción 4 en la app. Verificar en MongoDB:
```javascript
db.pit_stops.aggregate([{$group: {_id: "$id_carrera", total: {$sum: 1}}}])
```

**CU5 — Pilotos eficientes (>10 podios y >5 temporadas)** `[Neo4j]`

Opción 5 en la app. Verificar en Neo4j browser:
```cypher
MATCH (p:Piloto)-[r:PARTICIPO_EN]->(t:Temporada)
WITH p, sum(r.podios) AS total, count(t) AS temps
WHERE total > 10 AND temps > 5
RETURN p.nombre, total, temps ORDER BY total DESC
```

Historial de equipos por piloto (relación `CORRIO_PARA`):
```cypher
MATCH (p:Piloto)-[r:CORRIO_PARA]->(e:Equipo)
RETURN p.nombre, e.nombre, r.desde, r.hasta
```

**CU6 — Países con más carreras y circuitos** `[Neo4j]`

Opción 6 en la app. Verificar en Neo4j browser:
```cypher
MATCH (ca:Carrera)-[:REALIZADO_EN]->(c:Circuito)-[:UBICADO_EN]->(p:Pais)
RETURN p.nombre, count(ca) AS carreras ORDER BY carreras DESC
```

---

### Bloque 3 — CRUD con propagación a NoSQL

Las carreras ID 41–55 (temporadas 2024–2026) no tienen resultados pre-cargados y están disponibles para demostrar la propagación en tiempo real.

**Objetivo:** registrar una victoria de Sergio Pérez en 2024 y observar el impacto inmediato en tres bases de datos.

**Estado inicial — verificar antes del CRUD:**

| Consulta | Resultado esperado |
|----------|-------------------|
| App opción 2 (CU2) | Red Bull Racing: 19 victorias |
| App opción 5 (CU5) | Pérez NO aparece (5 temporadas, umbral >5) |
| `SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Red Bull Racing';` | 19 |
| `db.vueltas_rapidas.countDocuments({nombre_piloto: "Sergio Perez"})` | 0 |

**Registrar resultado (opción 7 → 1):**
```
Temporadas: 2016 | ... | 2026
Año: 2024
→ muestra carreras ID 41-45

ID de la Carrera : 41   (2024 - Monza)
ID del Piloto    : 2    (Sergio Pérez)
Posición final   : 1
→ Puntos automáticos: 25
→ 3/3 bases sincronizadas
```

**Verificar propagación:**

| Base | Consulta | Resultado esperado |
|------|----------|--------------------|
| App CU2 | opción 2 | Red Bull Racing: **20 victorias** |
| App CU3 | opción 3 | Sergio Pérez aparece con 1 vuelta rápida |
| App CU5 | opción 5 | Sergio Pérez: 16 podios en **6 temporadas** |
| Cassandra | `SELECT COUNT(*) FROM victorias_por_equipo WHERE nombre_equipo = 'Red Bull Racing';` | **20** |
| MongoDB | `db.vueltas_rapidas.countDocuments({nombre_piloto: "Sergio Perez"})` | **1** |
| SQL Server | `SELECT * FROM Resultados WHERE IdCarrera = 41; GO` | fila insertada visible |

**Eliminar resultado (opción 7 → 2) — revertir el cambio:**
```
Año: 2024 → Carrera ID: 41 → Piloto ID: 2
→ 3/3 bases sincronizadas
→ CU2 vuelve a 19 · Pérez desaparece de CU3 y CU5
```

**Probar validación de errores (opción 7 → 1):**
```
ID de la Carrera: 999
→ [❌] ID inexistente — verificá que el ID ingresado exista en la lista.
→ No se dispara sincronización. Sistema estable.
```

---

### Bloque 4 — Tolerancia a fallos

```bash
# Bajar Cassandra mientras la app sigue corriendo
docker stop f1_cassandra
```

- Opción 1 (CU1) → error limpio, la app no se detiene
- Opción 5 (CU5) → responde normalmente desde Neo4j
- CRUD → escribe en SQL, informa `⚠️ 2/3 sincronizados`, continúa funcionando

```bash
# Recuperar Cassandra
docker start f1_cassandra
# Esperar ~60 segundos
```

- Siguiente operación CRUD → `3/3 sincronizados` — Cassandra se actualiza con todos los cambios acumulados.

---

## Usuarios del sistema

| Email | Contraseña | Rol | Sesión |
|-------|-----------|-----|--------|
| admin@f1.com | admin123 | admin | Permanente (sin TTL) |
| director@f1.com | dir456 | director | 600 s de inactividad |
| prensa@f1.com | prensa789 | prensa | 600 s de inactividad |

El TTL es deslizante: cada acción dentro del menú reinicia el contador. Si el usuario no interactúa durante 600 segundos, Redis expira la clave y el sistema cierra la sesión automáticamente.

---

## Gestión de contenedores

```bash
docker compose up -d      # levantar (primera vez o tras down)
docker compose start      # reanudar contenedores detenidos
docker compose stop       # pausar sin borrar datos
docker compose down       # eliminar contenedores (los volúmenes persisten)
docker compose down -v    # eliminar contenedores y datos (reset completo)
```

---

## Puertos

| Servicio | Puerto | Interfaz web |
|----------|--------|-------------|
| SQL Server | 1433 | — |
| MongoDB | 27017 | — |
| Cassandra | 9042 | — |
| Neo4j | 7687 (Bolt) | http://localhost:7474 |
| Redis | 6379 | — |

---

## Dataset incluido

| Entidad | Cantidad |
|---------|---------|
| Equipos | 5 (Red Bull Racing, Mercedes AMG, Ferrari, McLaren, Alpine) |
| Pilotos | 5 (Verstappen, Pérez, Hamilton, Russell, Leclerc) |
| Circuitos | 5 (Monza, Silverstone, Spa, Suzuka, Interlagos) |
| Temporadas con resultados | 8 (2016–2023) |
| Temporadas sin resultados | 3 (2024–2026, disponibles para demo del CRUD) |
| Carreras totales | 55 (5 por temporada) |
| Resultados históricos | 120 (top 3 por carrera, temporadas 2016–2023) |
| Usuarios del sistema | 3 |
