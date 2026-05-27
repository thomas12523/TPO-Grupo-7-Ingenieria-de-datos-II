# TPO Grupo 7 — Sistema F1 Multi-Base de Datos

Sistema de gestión de Fórmula 1 utilizando SQL Server, Cassandra, MongoDB, Neo4j y Redis.

## Arquitectura

| Base de datos | Responsabilidad | Casos de uso |
|---------------|----------------|--------------|
| **SQL Server** | Fuente de verdad — esquema completo del DER | Base de la que todas las demás leen |
| **Cassandra** | Resultados históricos desnormalizados para analítica | CU1: pilotos multicampeones / CU2: equipos con más victorias |
| **MongoDB** | Pit stops y penalizaciones como documentos | CU3: vuelta más rápida / CU4: promedio de pit stops |
| **Neo4j** | Grafo de relaciones piloto↔temporada, país↔circuito | CU5 / CU6 |
| **Redis** | Sesiones de usuario con TTL por rol | Login / logout / expiración de sesión |

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

Siempre trabajar dentro del `.venv` para no mezclar dependencias entre proyectos.

```bash
# Crear (solo la primera vez)
python3 -m venv .venv

# Activar
source .venv/bin/activate          # Mac / Linux / WSL / Git Bash
.venv\Scripts\activate.bat         # Windows CMD
.venv\Scripts\Activate.ps1         # Windows PowerShell
```

Cuando está activo aparece `(.venv)` al inicio del prompt. Para desactivar: `deactivate`.

### 3. Instalar dependencias del sistema (WSL / Linux)

Necesario para que el driver de Cassandra compile correctamente en Python 3.12:

```bash
sudo apt-get install -y python3-dev libev-dev libffi-dev
```

> En Mac: `brew install libev`
> En Windows nativo no es necesario.

### 4. Instalar dependencias Python

Con el `.venv` activado:

```bash
pip install -r requirements.txt
```

> Si `pymssql` falla en Mac: `brew install freetds` y volver a intentar.

### 5. Levantar los contenedores Docker

Todas las bases están definidas en `docker-compose.yml`.

```bash
docker compose up -d
```

Verificar que los 5 contenedores estén corriendo:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

> **Cassandra tarda ~30 segundos** en estar lista después de iniciarse.
> Para confirmar: `docker logs f1_cassandra 2>&1 | tail -5`
> Buscar la línea: `Starting listening for CQL clients`

---

## Ejecución

### Paso 1 — Inicializar SQL Server (solo la primera vez o después de `down -v`)

```bash
python sql.py
```

Crea 12 tablas (Equipos, Usuarios, Auditoria, Pilotos, Circuitos, Temporadas, Carreras, Resultados, PitStops, Penalizaciones, Participacion, Rendimiento) y las pobla con datos de prueba.

### Paso 2 — Correr la aplicación

```bash
python main.py
```

Al iniciar, `main.py` verifica las conexiones, valida el esquema SQL y **sincroniza automáticamente** los datos hacia Cassandra, MongoDB y Neo4j. No es necesario correr los otros `.py` por separado.

> Los scripts individuales (`cassandraDB.py`, `mongoDB.py`, etc.) siguen siendo ejecutables de forma independiente para pruebas o desarrollo.

---

## Manejo de contenedores

```bash
# Uso diario — solo pausa y reanuda, no borra nada ni re-descarga nada
docker compose start         # arrancar
docker compose stop          # pausar

# Primera vez o si se hizo down
docker compose up -d         # crea e inicia los contenedores (descarga imágenes solo la 1ra vez)

# Solo si querés resetear todo desde cero
docker compose down          # para y elimina los contenedores (imágenes y datos quedan)
docker compose down -v       # para, elimina contenedores Y borra los datos guardados
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

**Neo4j Browser** → http://localhost:7474 — usuario: `neo4j` / password: `password123`

---

## Usuarios del sistema

| Email | Password | Rol | TTL de sesión |
|-------|----------|-----|--------------|
| admin@f1.com | admin123 | admin | 600 s |
| director@f1.com | dir456 | director | 600 s |
| prensa@f1.com | prensa789 | prensa | 5 s |

El TTL se asigna automáticamente según el rol: `prensa` es no confiable (5 s), el resto es confiable (600 s). Cuando la sesión expira, el sistema cierra el menú automáticamente.

---

## CRUD — Gestión de datos maestros

Toda escritura pasa por **SQL Server** (fuente de verdad). Al confirmar un cambio, el sistema propaga automáticamente a Cassandra, MongoDB y Neo4j.

| Operación | Descripción |
|-----------|-------------|
| `L` — Listar | Muestra todos los pilotos y equipos con sus IDs |
| `1` — Insertar piloto | Alta de un nuevo piloto en el sistema |
| `2` — Actualizar director | Cambia el director técnico de un equipo |
| `3` — Transferir piloto | Mueve un piloto de un equipo a otro |
| `4` — Eliminar piloto | Baja de un piloto (retiro, pérdida de asiento) |

> Los NoSQL **no se escriben directamente**: son entornos de lectura optimizados.
> Si un NoSQL falla durante la propagación, SQL ya tiene el dato correcto.
> Re-ejecutar cualquier CRUD vuelve a intentar la sincronización (operación idempotente).

---

## Tolerancia a fallos

El sistema implementa **consistencia eventual**: cada NoSQL se sincroniza de forma independiente. Si una base falla, las demás continúan operando.

**Probar con Cassandra caída:**
```bash
# Terminal 1 — bajar Cassandra
docker stop f1_cassandra

# Terminal 2 — correr el sistema
python main.py
# → Arranque: "Entornos de lectura listos: 2/3."
# → CU1 y CU2 muestran error, CU3-CU6 funcionan normal
# → CRUD escribe en SQL, propaga a MongoDB y Neo4j, avisa que Cassandra no se actualizó

# Recuperación
docker start f1_cassandra
# → El siguiente CRUD sincroniza Cassandra automáticamente
```

---

## Notas técnicas

### Cassandra + Python 3.12
Python 3.12 eliminó el módulo `asyncore` que usaba el driver de Cassandra por defecto.
Fix aplicado en `cassandraDB.py`:
```python
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())
from cassandra.io.asyncioreactor import AsyncioConnection
cluster = Cluster(['localhost'], connection_class=AsyncioConnection)
```
Requiere además instalar las dependencias de sistema del paso 3.

### Datos de prueba
- 5 equipos, 5 pilotos, 5 circuitos, **8 temporadas (2016–2023)**
- **40 carreras históricas** (5 por temporada)
- **120 resultados** (top 3 por carrera)
- 3 usuarios del sistema para autenticación
- Las temporadas 2016–2018 permiten que CU5 (`>10 podios AND >5 temporadas`) devuelva resultados con el umbral real del enunciado
