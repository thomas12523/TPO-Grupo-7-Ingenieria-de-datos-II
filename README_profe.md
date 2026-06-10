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

