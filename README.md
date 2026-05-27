# TPO Grupo 7 — Sistema F1 Multi-Base de Datos

Sistema de gestión de Fórmula 1 utilizando SQL Server, Cassandra, MongoDB, Neo4j y Redis.

## Arquitectura

| Base de datos | Responsabilidad | Casos de uso |
|---------------|----------------|--------------|
| **SQL Server** | Fuente de verdad — esquema completo del DER | Base de la que todas las demás leen |
| **Cassandra** | Resultados históricos desnormalizados para analítica | CU1: pilotos multicampeones / CU2: equipos con más victorias |
| **MongoDB** | Pit stops y penalizaciones como documentos | CU3: vuelta más rápida / CU4: promedio de pit stops |
| **Neo4j** | Grafo de relaciones piloto↔temporada, país↔circuito | CU5 / CU6 |
| **Redis** | Sesiones de usuario con TTL | Login / logout / expiración de sesión |

> **Regla de oro:** ninguna base NoSQL tiene datos que no existan en SQL Server. Todas consultan SQL para obtener IDs consistentes antes de insertar.

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

El proyecto usa Docker para las bases de datos. Si ya tenés contenedores de Cassandra, MongoDB y Neo4j de clases anteriores, podés reutilizarlos — están en los mismos puertos.

**Levantar SQL Server y Redis** (los que no vienen de clases):
```bash
docker compose up -d
```

**Levantar los contenedores de clases** (Cassandra, MongoDB, Neo4j):
```bash
docker start <nombre-contenedor-cassandra> <nombre-contenedor-mongo> <nombre-contenedor-neo4j>
```

Verificar que todo esté corriendo:
```bash
docker ps
```

> SQL Server tarda ~30 segundos en estar listo la primera vez. Si el script falla al conectar, esperar un momento y volver a ejecutar.

---

## Ejecución

**El orden importa** — SQL Server tiene que estar cargado antes que las demás bases.

### 1. SQL Server — crea todas las tablas y carga los datos base
```bash
python sql.py
```
Crea 12 tablas (Equipos, Usuarios, Auditoria, Pilotos, Circuitos, Temporadas, Carreras, Resultados, PitStops, Penalizaciones, Participacion, Rendimiento) y las pobla con datos de prueba.

### 2. Cassandra — resultados históricos
```bash
python cassandraDB.py
```
Consulta SQL Server, carga 75 resultados históricos (25 carreras × top 3) y ejecuta CU1 y CU2.

### 3. MongoDB — pit stops y penalizaciones
```bash
python mongoDB.py
```

### 4. Neo4j — grafo de relaciones
```bash
python neo4jDB.py
```

### 5. Redis — sesiones de usuario
```bash
python redisDB.py
```

### 6. Aplicación principal
```bash
python main.py
```

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

| Servicio | Puerto |
|----------|--------|
| SQL Server | 1433 |
| MongoDB | 27017 |
| Cassandra | 9042 |
| Neo4j (web) | 7474 |
| Neo4j (bolt) | 7687 |
| Redis | 6379 |

---

## Usuarios del sistema

| Email | Password | Rol |
|-------|----------|-----|
| admin@f1.com | admin123 | admin |
| director@f1.com | dir456 | director |
| prensa@f1.com | prensa789 | prensa |

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
- Las temporadas 2016-2018 se agregan para que CU5 (`>10 podios AND >5 temporadas`) devuelva resultados reales
