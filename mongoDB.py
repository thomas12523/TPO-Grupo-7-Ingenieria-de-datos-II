import pymssql
from pymongo import MongoClient, ASCENDING, DESCENDING
from collections import defaultdict

# ==========================================
# CONFIG
# ==========================================

sql_config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master'
}

mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['f1_db']


# ==========================================
# CREAR COLECCIONES E ÍNDICES
# ==========================================

def crear_colecciones_e_indices():
    """
    En MongoDB no se "crean tablas" explícitamente como en SQL,
    pero sí se definen índices para optimizar las consultas de cada caso de uso.

    Colecciones:
      - vueltas_rapidas   → CU3: vuelta más rápida por carrera/piloto
      - pit_stops         → CU4: pit stops por carrera para calcular promedio
    """

    # --- Colección: vueltas_rapidas ---
    # CU3 necesita buscar la vuelta más rápida por carrera y agrupar por piloto.
    # Índice compuesto (id_carrera, tiempo_vuelta) para ordenar rápido dentro de cada carrera.
    # Índice por nombre_piloto para contar cuántas vueltas rápidas tiene cada uno.
    col_vr = db['vueltas_rapidas']
    col_vr.create_index([('id_carrera', ASCENDING), ('tiempo_vuelta_seg', ASCENDING)],
                        name='idx_carrera_tiempo')
    col_vr.create_index([('nombre_piloto', ASCENDING)],
                        name='idx_piloto')

    # --- Colección: pit_stops ---
    # CU4 necesita contar pit stops por carrera para calcular promedios.
    # Índice por (id_carrera, anio) para agrupar eficientemente.
    col_ps = db['pit_stops']
    col_ps.create_index([('id_carrera', ASCENDING)], name='idx_carrera')
    col_ps.create_index([('anio', ASCENDING)], name='idx_anio')

    print("Colecciones e índices creados: vueltas_rapidas, pit_stops.")


# ==========================================
# POBLAR DESDE SQL SERVER
# ==========================================

def insertar_datos():
    """
    Lee los datos de SQL Server (fuente de verdad) y puebla las colecciones de MongoDB.

    Para vueltas_rapidas: usa la tabla Resultados como proxy del tiempo de vuelta.
    En un escenario real existiría una tabla VueltasRapidas con el tiempo exacto por vuelta;
    aquí derivamos el tiempo más rápido del TiempoFinal de cada carrera y asignamos
    el ganador (PosicionFinal=1) como el que marcó la vuelta rápida, siguiendo la
    lógica del dataset de ejemplo.

    Para pit_stops: usa directamente la tabla PitStops de SQL.
    """
    conn = pymssql.connect(**sql_config)
    cursor = conn.cursor(as_dict=True)

    # --- Leer datos para vueltas_rapidas ---
    # Trae el piloto que ganó cada carrera (pos=1) junto con su tiempo,
    # ya que en el dataset de ejemplo el ganador tiene el tiempo referencia.
    # También trae todos los resultados para poder simular una "vuelta rápida"
    # distinta al ganador (en F1 real la vuelta rápida la puede marcar cualquier piloto).
    # Aquí usamos el piloto con PosicionFinal=1 como marcador de vuelta rápida
    # (simplificación válida para este dataset de prueba).
    cursor.execute("""
        SELECT
            r.IdCarrera,
            t.Anio,
            c.Fecha,
            ci.Nombre  AS NombreCircuito,
            p.Nombre   AS NombrePiloto,
            e.Nombre   AS NombreEquipo,
            r.TiempoFinal,
            r.PosicionFinal
        FROM Resultados r
        JOIN Pilotos    p  ON r.IdPiloto    = p.IdPiloto
        JOIN Equipos    e  ON p.IdEquipo    = e.IdEquipo
        JOIN Carreras   c  ON r.IdCarrera   = c.IdCarrera
        JOIN Circuitos  ci ON c.IdCircuito  = ci.IdCircuito
        JOIN Temporadas t  ON c.IdTemporada = t.IdTemporada
        WHERE r.PosicionFinal = 1
        ORDER BY t.Anio, r.IdCarrera
    """)
    ganadores = cursor.fetchall()

    # --- Leer datos para pit_stops ---
    cursor.execute("""
        SELECT
            ps.IdPiloto,
            ps.IdCarrera,
            ps.NumeroParada,
            ps.TiempoParada,
            p.Nombre   AS NombrePiloto,
            e.Nombre   AS NombreEquipo,
            t.Anio,
            ci.Nombre  AS NombreCircuito
        FROM PitStops ps
        JOIN Pilotos    p  ON ps.IdPiloto   = p.IdPiloto
        JOIN Equipos    e  ON p.IdEquipo    = e.IdEquipo
        JOIN Carreras   c  ON ps.IdCarrera  = c.IdCarrera
        JOIN Circuitos  ci ON c.IdCircuito  = ci.IdCircuito
        JOIN Temporadas t  ON c.IdTemporada = t.IdTemporada
        ORDER BY t.Anio, ps.IdCarrera, ps.IdPiloto, ps.NumeroParada
    """)
    pit_stops = cursor.fetchall()
    conn.close()

    print(f"SQL Server → {len(ganadores)} vueltas rápidas, {len(pit_stops)} pit stops leídos.")

    # --- Insertar en vueltas_rapidas ---
    col_vr = db['vueltas_rapidas']
    col_vr.delete_many({})  # Limpiar antes de reinsertar (idempotente)

    docs_vr = []
    for row in ganadores:
        # Convertir TiempoFinal "H:MM:SS.mmm" a segundos para poder ordenar numéricamente
        tiempo_seg = _tiempo_a_segundos(row['TiempoFinal'])
        docs_vr.append({
            'id_carrera':      row['IdCarrera'],
            'anio':            row['Anio'],
            'fecha':           str(row['Fecha']),
            'nombre_circuito': row['NombreCircuito'],
            'nombre_piloto':   row['NombrePiloto'],
            'nombre_equipo':   row['NombreEquipo'],
            'tiempo_vuelta':   row['TiempoFinal'],      # legible
            'tiempo_vuelta_seg': tiempo_seg,            # para ordenamiento
        })
    if docs_vr:
        col_vr.insert_many(docs_vr)

    # --- Insertar en pit_stops ---
    col_ps = db['pit_stops']
    col_ps.delete_many({})

    docs_ps = []
    for row in pit_stops:
        docs_ps.append({
            'id_carrera':      row['IdCarrera'],
            'anio':            row['Anio'],
            'nombre_circuito': row['NombreCircuito'],
            'id_piloto':       row['IdPiloto'],
            'nombre_piloto':   row['NombrePiloto'],
            'nombre_equipo':   row['NombreEquipo'],
            'numero_parada':   row['NumeroParada'],
            'tiempo_parada':   float(row['TiempoParada']),
        })
    if docs_ps:
        col_ps.insert_many(docs_ps)

    print("Datos insertados correctamente en MongoDB desde SQL Server.")


def _tiempo_a_segundos(tiempo_str):
    """Convierte 'H:MM:SS.mmm' o 'MM:SS.mmm' a float de segundos."""
    try:
        partes = tiempo_str.strip().split(':')
        if len(partes) == 3:
            h, m, s = partes
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(partes) == 2:
            m, s = partes
            return int(m) * 60 + float(s)
    except Exception:
        pass
    return 0.0


# ==========================================
# CASOS DE USO
# ==========================================

def cu3_pilotos_vuelta_rapida():
    """
    CU3: ¿Qué pilotos han marcado la vuelta más rápida en diversas carreras?

    Estrategia MongoDB:
      1. Agrupa los documentos de vueltas_rapidas por nombre_piloto.
      2. Cuenta cuántas carreras distintas tiene cada piloto.
      3. Recolecta los años y circuitos donde lo logró.
      4. Ordena de mayor a menor cantidad de vueltas rápidas.

    La colección ya tiene un documento por carrera con el piloto más rápido,
    así que $group directamente da el conteo correcto.
    """
    col_vr = db['vueltas_rapidas']

    pipeline = [
        {
            '$group': {
                '_id': '$nombre_piloto',
                'total_vueltas_rapidas': {'$sum': 1},
                'equipo': {'$last': '$nombre_equipo'},
                'carreras': {
                    '$push': {
                        'anio': '$anio',
                        'circuito': '$nombre_circuito',
                        'tiempo': '$tiempo_vuelta'
                    }
                }
            }
        },
        {'$sort': {'total_vueltas_rapidas': DESCENDING}},
        {
            '$project': {
                '_id': 0,
                'piloto': '$_id',
                'equipo': 1,
                'total_vueltas_rapidas': 1,
                'carreras': 1
            }
        }
    ]

    resultado = list(col_vr.aggregate(pipeline))

    print("\n--- CU3: Pilotos con más vueltas rápidas ---")
    for r in resultado:
        detalle = ', '.join(
            f"{c['anio']} {c['circuito']} ({c['tiempo']})"
            for c in r['carreras']
        )
        print(f"  {r['piloto']} ({r['equipo']}): {r['total_vueltas_rapidas']} vuelta(s) rápida(s)")
        print(f"    → {detalle}")

    return resultado


def cu4_promedio_pit_stops_por_carrera():
    """
    CU4: ¿Cuántos pit stops se realizan en promedio por carrera?

    Estrategia MongoDB:
      1. Agrupa por id_carrera para contar el total de paradas en cada carrera.
      2. Calcula la media global de esos totales.
      3. También devuelve el desglose por carrera para mayor detalle.

    Retorna:
      - promedio_global: float con el promedio de pit stops por carrera
      - detalle_por_carrera: lista con el total de pit stops de cada carrera
    """
    col_ps = db['pit_stops']

    # Paso 1: total de pit stops por carrera
    pipeline_por_carrera = [
        {
            '$group': {
                '_id': '$id_carrera',
                'anio': {'$first': '$anio'},
                'circuito': {'$first': '$nombre_circuito'},
                'total_pit_stops': {'$sum': 1}
            }
        },
        {'$sort': {'anio': ASCENDING, '_id': ASCENDING}},
        {
            '$project': {
                '_id': 0,
                'id_carrera': '$_id',
                'anio': 1,
                'circuito': 1,
                'total_pit_stops': 1
            }
        }
    ]
    detalle = list(col_ps.aggregate(pipeline_por_carrera))

    # Paso 2: promedio global
    pipeline_promedio = [
        {
            '$group': {
                '_id': '$id_carrera',
                'total_pit_stops': {'$sum': 1}
            }
        },
        {
            '$group': {
                '_id': None,
                'promedio_global': {'$avg': '$total_pit_stops'},
                'total_carreras': {'$sum': 1},
                'total_pit_stops': {'$sum': '$total_pit_stops'}
            }
        }
    ]
    resumen = list(col_ps.aggregate(pipeline_promedio))
    promedio = resumen[0]['promedio_global'] if resumen else 0

    print("\n--- CU4: Pit stops por carrera ---")
    for d in detalle:
        print(f"  Carrera {d['id_carrera']} ({d['anio']} - {d['circuito']}): {d['total_pit_stops']} pit stops")
    if resumen:
        r = resumen[0]
        print(f"\n  Resumen global:")
        print(f"    Carreras con datos: {r['total_carreras']}")
        print(f"    Total pit stops:    {r['total_pit_stops']}")
        print(f"    Promedio por carrera: {r['promedio_global']:.2f}")

    return {'promedio_global': promedio, 'detalle_por_carrera': detalle}


# ==========================================
# CRUD
# ==========================================

def insertar_vuelta_rapida(id_carrera, anio, fecha, nombre_circuito,
                           nombre_piloto, nombre_equipo, tiempo_vuelta):
    """Inserta un registro de vuelta rápida en la colección."""
    db['vueltas_rapidas'].insert_one({
        'id_carrera':        id_carrera,
        'anio':              anio,
        'fecha':             fecha,
        'nombre_circuito':   nombre_circuito,
        'nombre_piloto':     nombre_piloto,
        'nombre_equipo':     nombre_equipo,
        'tiempo_vuelta':     tiempo_vuelta,
        'tiempo_vuelta_seg': _tiempo_a_segundos(tiempo_vuelta),
    })
    print(f"Vuelta rápida insertada: {nombre_piloto} en carrera {id_carrera} ({anio}).")


def actualizar_tiempo_vuelta_rapida(id_carrera, nombre_piloto, nuevo_tiempo):
    """Actualiza el tiempo de vuelta rápida de un piloto en una carrera."""
    resultado = db['vueltas_rapidas'].update_one(
        {'id_carrera': id_carrera, 'nombre_piloto': nombre_piloto},
        {'$set': {
            'tiempo_vuelta':     nuevo_tiempo,
            'tiempo_vuelta_seg': _tiempo_a_segundos(nuevo_tiempo)
        }}
    )
    if resultado.modified_count:
        print(f"Tiempo actualizado a {nuevo_tiempo} para {nombre_piloto} en carrera {id_carrera}.")
    else:
        print(f"No se encontró el registro para actualizar.")


def eliminar_vuelta_rapida(id_carrera):
    """Elimina el registro de vuelta rápida de una carrera."""
    resultado = db['vueltas_rapidas'].delete_one({'id_carrera': id_carrera})
    if resultado.deleted_count:
        print(f"Vuelta rápida de carrera {id_carrera} eliminada.")
    else:
        print(f"No se encontró registro para la carrera {id_carrera}.")


def leer_vueltas_rapidas_piloto(nombre_piloto):
    """
    Devuelve todos los registros de vuelta rápida de un piloto específico.
    Usa el índice idx_piloto → consulta eficiente.
    """
    docs = list(db['vueltas_rapidas'].find(
        {'nombre_piloto': nombre_piloto},
        {'_id': 0}
    ).sort('anio', ASCENDING))

    print(f"\n--- Vueltas rápidas de {nombre_piloto} ---")
    for d in docs:
        print(f"  {d['anio']} | Carrera {d['id_carrera']} | {d['nombre_circuito']} | {d['tiempo_vuelta']}")
    return docs


def insertar_pit_stop(id_carrera, anio, nombre_circuito, id_piloto,
                      nombre_piloto, nombre_equipo, numero_parada, tiempo_parada):
    """Inserta un pit stop individual."""
    db['pit_stops'].insert_one({
        'id_carrera':      id_carrera,
        'anio':            anio,
        'nombre_circuito': nombre_circuito,
        'id_piloto':       id_piloto,
        'nombre_piloto':   nombre_piloto,
        'nombre_equipo':   nombre_equipo,
        'numero_parada':   numero_parada,
        'tiempo_parada':   float(tiempo_parada),
    })
    print(f"Pit stop insertado: {nombre_piloto} parada #{numero_parada} en carrera {id_carrera}.")


def actualizar_tiempo_pit_stop(id_carrera, id_piloto, numero_parada, nuevo_tiempo):
    """Actualiza el tiempo de un pit stop específico."""
    resultado = db['pit_stops'].update_one(
        {'id_carrera': id_carrera, 'id_piloto': id_piloto, 'numero_parada': numero_parada},
        {'$set': {'tiempo_parada': float(nuevo_tiempo)}}
    )
    if resultado.modified_count:
        print(f"Tiempo de pit stop actualizado a {nuevo_tiempo}s.")
    else:
        print(f"No se encontró el pit stop para actualizar.")


def eliminar_pit_stops_carrera(id_carrera):
    """Elimina todos los pit stops de una carrera."""
    resultado = db['pit_stops'].delete_many({'id_carrera': id_carrera})
    print(f"{resultado.deleted_count} pit stop(s) eliminados de la carrera {id_carrera}.")


def leer_pit_stops_carrera(id_carrera):
    """
    Devuelve todos los pit stops de una carrera específica.
    Usa el índice idx_carrera → consulta eficiente.
    """
    docs = list(db['pit_stops'].find(
        {'id_carrera': id_carrera},
        {'_id': 0}
    ).sort([('id_piloto', ASCENDING), ('numero_parada', ASCENDING)]))

    print(f"\n--- Pit stops de carrera {id_carrera} ---")
    for d in docs:
        print(f"  {d['nombre_piloto']} | Parada #{d['numero_parada']} | {d['tiempo_parada']}s")
    return docs


# ==========================================
# EJECUCIÓN
# ==========================================

crear_colecciones_e_indices()
insertar_datos()
cu3_pilotos_vuelta_rapida()
cu4_promedio_pit_stops_por_carrera()

# Ejemplos de CRUD
leer_vueltas_rapidas_piloto('Max Verstappen')
leer_pit_stops_carrera(1)