import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from cassandra.cluster import Cluster
from cassandra.io.asyncioreactor import AsyncioConnection
from collections import Counter
import pymssql

# Config de SQL Server (fuente de verdad)
sql_config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master'
}

cluster = None
session = None

def conectar():
    """Establece la conexión con Cassandra. Se llama explícitamente, no al importar."""
    global cluster, session
    cluster = Cluster(['localhost'], connection_class=AsyncioConnection)
    session = cluster.connect()


def crear_keyspace_y_tablas():
    # Conectar la primera vez que se usa (no al importar el módulo)
    if session is None:
        conectar()
    # Keyspace = base de datos en Cassandra
    # SimpleStrategy con replication_factor=1 es para desarrollo local (un solo nodo)
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS f1_keyspace
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
    """)
    session.set_keyspace('f1_keyspace')
    print("Keyspace f1_keyspace listo.")

    # Tabla principal: la tabla RESULTADO del DER
    # Partition key: (anio, id_carrera) -> todos los resultados de una carrera viven juntos
    # Clustering: posicion_final -> ordenados por posición dentro de la carrera
    session.execute("""
        CREATE TABLE IF NOT EXISTS resultados_historicos (
            anio             INT,
            id_carrera       INT,
            id_piloto        INT,
            nombre_piloto    TEXT,
            nombre_equipo    TEXT,
            posicion_inicial INT,
            posicion_final   INT,
            tiempo_final     TEXT,
            puntos           DECIMAL,
            PRIMARY KEY ((anio, id_carrera), posicion_final, id_piloto)
        )
    """)

    # Tabla para CU1: optimizada para contar títulos por piloto
    # Partition key: nombre_piloto -> todas las temporadas de ese piloto en una partición
    # Clustering: anio -> ordenadas cronológicamente
    session.execute("""
        CREATE TABLE IF NOT EXISTS campeonatos_por_piloto (
            nombre_piloto    TEXT,
            anio             INT,
            puntos_temporada DECIMAL,
            fue_campeon      BOOLEAN,
            PRIMARY KEY (nombre_piloto, anio)
        )
    """)

    # Tabla para CU2: optimizada para contar victorias por equipo
    # Partition key: nombre_equipo -> todas las victorias del equipo en una partición
    # Clustering: anio, id_carrera -> ordenadas por año y carrera
    session.execute("""
        CREATE TABLE IF NOT EXISTS victorias_por_equipo (
            nombre_equipo TEXT,
            anio          INT,
            id_carrera    INT,
            nombre_piloto TEXT,
            PRIMARY KEY (nombre_equipo, anio, id_carrera)
        )
    """)

    print("Tablas creadas: resultados_historicos, campeonatos_por_piloto, victorias_por_equipo.")


def insertar_datos():
    """
    Lee directamente la tabla Resultados de SQL Server (fuente de verdad)
    y puebla las tres tablas de Cassandra con esos datos reales.
    """
    session.set_keyspace('f1_keyspace')

    # Consulta única: trae todo lo necesario con un solo JOIN
    conn = pymssql.connect(**sql_config)
    cursor = conn.cursor(as_dict=True)
    cursor.execute("""
        SELECT
            r.IdPiloto,       p.Nombre  AS NombrePiloto,
            e.Nombre          AS NombreEquipo,
            r.IdCarrera,      t.Anio,
            r.PosicionInicial, r.PosicionFinal,
            r.TiempoFinal,    r.Puntos
        FROM Resultados r
        JOIN Pilotos  p ON r.IdPiloto  = p.IdPiloto
        JOIN Equipos  e ON p.IdEquipo  = e.IdEquipo
        JOIN Carreras c ON r.IdCarrera = c.IdCarrera
        JOIN Temporadas t ON c.IdTemporada = t.IdTemporada
        ORDER BY t.Anio, r.IdCarrera, r.PosicionFinal
    """)
    resultados = cursor.fetchall()
    # Calcular campeones desde SQL: el piloto con más puntos en cada temporada
    # Trae todos los pilotos con sus puntos por temporada, ordenados por año y puntos DESC
    # El primero de cada año es el campeón
    cursor.execute("""
        SELECT p.Nombre AS NombrePiloto, t.Anio, SUM(r.Puntos) AS TotalPuntos
        FROM Resultados r
        JOIN Pilotos    p ON r.IdPiloto    = p.IdPiloto
        JOIN Carreras   c ON r.IdCarrera   = c.IdCarrera
        JOIN Temporadas t ON c.IdTemporada = t.IdTemporada
        GROUP BY p.Nombre, t.Anio
        ORDER BY t.Anio, SUM(r.Puntos) DESC
    """)
    campeon_por_anio = {}
    for row in cursor.fetchall():
        anio = row['Anio']
        if anio not in campeon_por_anio:
            campeon_por_anio[anio] = (row['NombrePiloto'], float(row['TotalPuntos']))

    conn.close()
    print(f"Leídos desde SQL Server: {len(resultados)} resultados, {len(campeon_por_anio)} campeones.")

    stmt_resultado = session.prepare("""
        INSERT INTO resultados_historicos
        (anio, id_carrera, id_piloto, nombre_piloto, nombre_equipo,
         posicion_inicial, posicion_final, tiempo_final, puntos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    stmt_victoria = session.prepare("""
        INSERT INTO victorias_por_equipo (nombre_equipo, anio, id_carrera, nombre_piloto)
        VALUES (?, ?, ?, ?)
    """)
    stmt_campeon = session.prepare("""
        INSERT INTO campeonatos_por_piloto (nombre_piloto, anio, puntos_temporada, fue_campeon)
        VALUES (?, ?, ?, ?)
    """)

    for row in resultados:
        # Insertar en resultados_historicos
        session.execute(stmt_resultado, (
            row['Anio'], row['IdCarrera'],
            row['IdPiloto'], row['NombrePiloto'], row['NombreEquipo'],
            row['PosicionInicial'], row['PosicionFinal'],
            row['TiempoFinal'], float(row['Puntos'])
        ))

        # Si ganó la carrera → registrar victoria del equipo
        if row['PosicionFinal'] == 1:
            session.execute(stmt_victoria, (
                row['NombreEquipo'], row['Anio'],
                row['IdCarrera'], row['NombrePiloto']
            ))

    # Insertar campeones de cada temporada
    for anio, (campeon, puntos) in campeon_por_anio.items():
        session.execute(stmt_campeon, (campeon, anio, puntos, True))

    print("Datos insertados correctamente en Cassandra desde SQL Server.")


# ==========================================
# CASOS DE USO
# ==========================================

def cu1_pilotos_multicampeon():
    """
    CU1: ¿Qué pilotos han ganado múltiples campeonatos mundiales?
    Consulta campeonatos_por_piloto filtrando fue_campeon=True y agrupa por piloto.
    Retorna lista de dicts con nombre_piloto, total_titulos y anios.
    """
    session.set_keyspace('f1_keyspace')

    rows = session.execute(
        "SELECT nombre_piloto, anio FROM campeonatos_por_piloto WHERE fue_campeon = true ALLOW FILTERING"
    )

    titulos = Counter()
    anios_por_piloto = {}
    for row in rows:
        titulos[row.nombre_piloto] += 1
        anios_por_piloto.setdefault(row.nombre_piloto, []).append(row.anio)

    resultado = [
        {
            'piloto': piloto,
            'titulos': total,
            'anios': sorted(anios_por_piloto[piloto])
        }
        for piloto, total in titulos.items() if total > 1
    ]
    resultado.sort(key=lambda x: -x['titulos'])

    print("\n--- CU1: Pilotos con múltiples campeonatos ---")
    for r in resultado:
        print(f"  {r['piloto']}: {r['titulos']} títulos {r['anios']}")

    return resultado


def cu2_equipos_mas_victorias():
    """
    CU2: ¿Qué equipos han tenido más victorias en la historia?
    Consulta victorias_por_equipo y agrupa por equipo.
    Retorna lista de dicts con nombre_equipo y total_victorias ordenada de mayor a menor.
    """
    session.set_keyspace('f1_keyspace')

    rows = session.execute("SELECT nombre_equipo FROM victorias_por_equipo")

    victorias = Counter(row.nombre_equipo for row in rows)

    resultado = [
        {'equipo': equipo, 'victorias': total}
        for equipo, total in victorias.most_common()
    ]

    print("\n--- CU2: Equipos con más victorias históricas ---")
    for r in resultado:
        print(f"  {r['equipo']}: {r['victorias']} victorias")

    return resultado


# ==========================================
# CRUD
# ==========================================

def insertar_resultado(anio, id_carrera, id_piloto, nombre_piloto, nombre_equipo,
                       posicion_inicial, posicion_final, tiempo_final, puntos):
    """Inserta un resultado de carrera individual en resultados_historicos."""
    session.set_keyspace('f1_keyspace')
    session.execute("""
        INSERT INTO resultados_historicos
        (anio, id_carrera, id_piloto, nombre_piloto, nombre_equipo,
         posicion_inicial, posicion_final, tiempo_final, puntos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (anio, id_carrera, id_piloto, nombre_piloto, nombre_equipo,
          posicion_inicial, posicion_final, tiempo_final, puntos))
    print(f"Resultado insertado: {nombre_piloto} P{posicion_final} en carrera {id_carrera} ({anio}).")


def actualizar_puntos(anio, id_carrera, posicion_final, id_piloto, nuevos_puntos):
    """Actualiza los puntos de un resultado ya registrado."""
    session.set_keyspace('f1_keyspace')
    session.execute("""
        UPDATE resultados_historicos SET puntos = %s
        WHERE anio = %s AND id_carrera = %s AND posicion_final = %s AND id_piloto = %s
    """, (nuevos_puntos, anio, id_carrera, posicion_final, id_piloto))
    print(f"Puntos actualizados a {nuevos_puntos} para piloto {id_piloto} en carrera {id_carrera}.")


def eliminar_resultado(anio, id_carrera, posicion_final, id_piloto):
    """Elimina un resultado de una carrera."""
    session.set_keyspace('f1_keyspace')
    session.execute("""
        DELETE FROM resultados_historicos
        WHERE anio = %s AND id_carrera = %s AND posicion_final = %s AND id_piloto = %s
    """, (anio, id_carrera, posicion_final, id_piloto))
    print(f"Resultado eliminado: piloto {id_piloto}, carrera {id_carrera} ({anio}).")


def leer_resultados_carrera(anio, id_carrera):
    """
    Devuelve todos los resultados de una carrera específica ordenados por posición.
    Esta query es eficiente porque (anio, id_carrera) es el partition key.
    """
    session.set_keyspace('f1_keyspace')
    rows = session.execute(
        "SELECT * FROM resultados_historicos WHERE anio = %s AND id_carrera = %s",
        (anio, id_carrera)
    )
    resultado = list(rows)
    print(f"\n--- Resultados carrera {id_carrera} ({anio}) ---")
    for row in resultado:
        print(f"  P{row.posicion_final} {row.nombre_piloto} ({row.nombre_equipo}) - {row.puntos} pts")
    return resultado


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    crear_keyspace_y_tablas()
    insertar_datos()
    cu1_pilotos_multicampeon()
    cu2_equipos_mas_victorias()
    leer_resultados_carrera(2023, 1)
