import pymssql
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)

# Config de SQL Server (fuente de verdad)
sql_config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master'
}


# ==========================================
# FUNCIONES DE ESCRITURA EN EL GRAFO
# ==========================================

def vincular_piloto_temporada(nombrePiloto, anioTemporada):
    with driver.session() as session:
        query = """
        MERGE (p:Piloto {nombre: $nombre})
        MERGE (t:Temporada {anio: $anio})
        MERGE (p)-[r:PARTICIPO_EN]->(t)
        ON CREATE SET r.podios = 1
        ON MATCH SET r.podios = r.podios + 1
        """
        session.run(query, nombre=nombrePiloto, anio=anioTemporada).consume()
        print("Relacion Creada")

def vincular_carrera_circuito_pais(nombreCarrera, nombreCircuito, nombrePais):
    with driver.session() as session:
        query = """
        MERGE (p:Pais {nombre: $pais})
        MERGE (c:Circuito {nombre: $circuito})
        MERGE (ca:Carrera {nombre: $carrera})
        MERGE (c)-[:UBICADO_EN]->(p)
        MERGE (ca)-[:REALIZADO_EN]->(c)
        """
        session.run(query, carrera=nombreCarrera, circuito=nombreCircuito, pais=nombrePais).consume()


# ==========================================
# POBLAR DESDE SQL SERVER
# ==========================================

def poblar_desde_sql():
    """
    Lee los datos reales de SQL Server y puebla el grafo Neo4j.

    Crea:
      - (Piloto)-[:PARTICIPO_EN {podios}]->(Temporada)
          con los podios reales por temporada (posición final <= 3)
      - (Carrera)-[:REALIZADO_EN]->(Circuito)-[:UBICADO_EN]->(Pais)
          con todas las carreras históricas y su ubicación

    Limpia el grafo antes de insertar para que sea idempotente.
    """
    conn = pymssql.connect(**sql_config)
    cursor = conn.cursor(as_dict=True)

    # Query 1: podios reales por piloto por temporada
    cursor.execute("""
        SELECT p.Nombre AS NombrePiloto, t.Anio, COUNT(*) AS Podios
        FROM Resultados r
        JOIN Pilotos    p ON r.IdPiloto    = p.IdPiloto
        JOIN Carreras   c ON r.IdCarrera   = c.IdCarrera
        JOIN Temporadas t ON c.IdTemporada = t.IdTemporada
        WHERE r.PosicionFinal <= 3
        GROUP BY p.Nombre, t.Anio
        ORDER BY t.Anio, p.Nombre
    """)
    podios = cursor.fetchall()

    # Query 2: carreras con circuito y país (nombre único: "GP {Ciudad} {Año}")
    cursor.execute("""
        SELECT
            'GP ' + ci.Ciudad + ' ' + CAST(t.Anio AS VARCHAR) AS NombreCarrera,
            ci.Nombre AS NombreCircuito,
            ci.Pais   AS NombrePais
        FROM Carreras   c
        JOIN Circuitos  ci ON c.IdCircuito  = ci.IdCircuito
        JOIN Temporadas t  ON c.IdTemporada = t.IdTemporada
        ORDER BY t.Anio, c.IdCarrera
    """)
    carreras = cursor.fetchall()
    conn.close()

    print(f"SQL Server → {len(podios)} relaciones piloto-temporada, {len(carreras)} carreras leídas.")

    # Limpiar grafo antes de insertar
    borrarDatosNeo4j()

    # Insertar relaciones piloto-temporada
    # Se abre una sesión por fila para garantizar el commit en neo4j driver v5
    for row in podios:
        with driver.session() as session:
            session.run("""
                MERGE (p:Piloto {nombre: $nombre})
                MERGE (t:Temporada {anio: $anio})
                MERGE (p)-[r:PARTICIPO_EN]->(t)
                SET r.podios = $podios
            """, nombre=row['NombrePiloto'], anio=row['Anio'], podios=row['Podios']).consume()

    # Insertar relaciones carrera-circuito-país
    for row in carreras:
        vincular_carrera_circuito_pais(
            row['NombreCarrera'],
            row['NombreCircuito'],
            row['NombrePais']
        )

    print(f"Neo4j poblado: {len(podios)} relaciones PARTICIPO_EN, {len(carreras)} carreras.")


# ==========================================
# CASOS DE USO 5 Y 6
# ==========================================

def pilotosEficientes():
    """
    CU5: Pilotos con más de 10 podios en total Y que corrieron en más de 5 temporadas.

    El dataset incluye 8 temporadas (2016-2023). Pilotos que califican:
    - Verstappen: ~37 podios en 8 temporadas
    - Hamilton:   ~31 podios en 7 temporadas (2022 sin podios)
    - Russell:    ~20 podios en 7 temporadas
    - Leclerc:    ~17 podios en 6 temporadas
    """
    print("\n--- CU5: Pilotos eficientes (>10 podios, >5 temporadas) ---")
    with driver.session() as session:
        query = """
        MATCH (p:Piloto)-[r:PARTICIPO_EN]->(t:Temporada)
        WITH p, sum(r.podios) AS totalPodios, count(t) AS temporadas
        WHERE totalPodios > 10 AND temporadas > 5
        RETURN p.nombre AS piloto, totalPodios, temporadas
        ORDER BY totalPodios DESC
        """
        resultado = session.run(query)
        pilotos = list(resultado)
        if not pilotos:
            print("  Sin datos.")
        for r in pilotos:
            print(f"  {r['piloto']}: {r['totalPodios']} podios en {r['temporadas']} temporadas")


def paisConMasCarreras():
    """CU6a: Ranking de países por cantidad de carreras históricas."""
    print("\n--- CU6: Ranking de países por cantidad de carreras ---")
    with driver.session() as session:
        query = """
        MATCH (ca:Carrera)-[:REALIZADO_EN]->(c:Circuito)-[:UBICADO_EN]->(p:Pais)
        WITH p, count(ca) AS cantidadCarreras
        RETURN p.nombre AS pais, cantidadCarreras
        ORDER BY cantidadCarreras DESC
        """
        resultado = session.run(query)
        paises = list(resultado)
        if not paises:
            print("  Sin datos.")
        for r in paises:
            print(f"  {r['pais']}: {r['cantidadCarreras']} carreras")

def paisConMas1Circuito():
    """CU6b: Países con más de 1 circuito registrado."""
    print("\n--- CU6: Países con más de 1 circuito ---")
    with driver.session() as session:
        query = """
        MATCH (c:Circuito)-[:UBICADO_EN]->(p:Pais)
        WITH p, count(c) AS cantidadCircuitos
        WHERE cantidadCircuitos > 1
        RETURN p.nombre AS pais, cantidadCircuitos
        ORDER BY cantidadCircuitos DESC
        """
        resultado = session.run(query)
        paises = list(resultado)
        if not paises:
            print("  Ningún país con más de 1 circuito en el dataset actual.")
        for r in paises:
            print(f"  {r['pais']}: {r['cantidadCircuitos']} circuitos")


# ==========================================
# CRUD
# ==========================================

def borrarDatosNeo4j():
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n").consume()
        print("Datos borrados exitosamente")

def actualizarNombreCircuito(nombreViejo, nombreNuevo):
    with driver.session() as session:
        session.run("""
            MATCH (c:Circuito {nombre: $viejo})
            SET c.nombre = $nuevo
        """, viejo=nombreViejo, nuevo=nombreNuevo).consume()
        print(f"Circuito actualizado a: {nombreNuevo}")


if __name__ == "__main__":
    poblar_desde_sql()
    pilotosEficientes()
    paisConMasCarreras()
    paisConMas1Circuito()
    driver.close()
