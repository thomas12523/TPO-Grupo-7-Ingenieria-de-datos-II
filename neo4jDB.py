from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)


# funciones para crear los nodos de relaciones y atender a los CUs

def vincular_piloto_temporada(nombrePiloto,anioTemporada):
    # IMPORTANTE, en resultado obtenido cuando se registra en cassandra, si entro en el podio hacemos un incremento +1
    with driver.session() as session:
        query="""
        MERGE (p:Piloto {nombre: $nombre})
        MERGE (t:Temporada {anio: $anio})
        MERGE (p) -[r:PARTICIPO_EN]->(t)
        ON CREATE SET r.podios= 1
        ON MATCH SET r.podios= r.podios+1
        """
        session.run(query,nombre=nombrePiloto,anio=anioTemporada)
        print("Relacion Creada")

def vincular_carrera_circuito_pais(nombreCarrera,nombreCircuito,nombrePais):

    with driver.session() as session:
        query="""
        MERGE (p:Pais {nombre: $pais})
        MERGE (c:Circuito {nombre: $circuito})
        MERGE (ca:Carrera {nombre: $carrera})        
        MERGE (c)-[:UBICADO_EN]->(p)
        MERGE (ca)-[:REALIZADO_EN]->(c)
        """
        session.run(query,carrera=nombreCarrera,circuito=nombreCircuito,pais=nombrePais)
        print("Relacion creada")


# Casos de usos 5 y 6

# ¿Que pilotos han tenido más de 10 podios Y han corrido en más de 5 temporadas?

def pilotosEficientes():
    print("Los pilotos son:\n")
    with driver.session() as session:
        query="""
        MATCH (p:Piloto) -[r:PARTICIPO_EN]->(t:Temporada)
        WITH p,sum(r.podios) as totalPodios, count(t) as temporadas
        WHERE totalPodios>10 AND temporadas>5
        RETURN p.nombre as "Nombre Piloto",sum(r.podios) as "Podios Totales",count(t) as "Temporadas"
        """
    session.run(query)
    

# ¿Qué paises han tenido mayor cantidad de carreras O que pais tiene mas de 1 circuito?

def paisConMasCarreras():
    print("Los Paises en Raking son:\n")
    with driver.session() as session:
        query="""
        MATCH (ca:Carrera)-[:REALIZADO_EN]->(c:Circuito)-[:UBICADO_EN]->(p:Pais)
        WITH p,sum(ca) as CantidadCarreras
        RETURN p.nombre,CantidadCarreras
        ORDER BY CantidadCarreras DESC
        """
        session.run(query)

def paisConMas1Circuito():
    print("Los Paises son:\n")
    with driver.session() as session:
        query="""
        MATCH (c:Circuito)-[r:UBICADO_EN]->(p:Pais)
        WITH p,count(c) as CantidadCircuitos
        WHERE CantidadCircuitos>1
        RETURN p.nombre,CantidadCircuitos
        """
        session.run(query)

# BORRAR INFORMACION DE NEO4J
def borrarDatosNeo4j():
    
    with driver.session() as session:
        query="""
        MATCH (n)
        DETACH DELETE n
        """
        session.run(query)
        print("Datos borrados exitosamente\n")

# ACTUALIZAR NOMBRE DEL CIRCUITO
def actualizarNombreCircuito(nombreViejo, nombreNuevo):
    with driver.session() as session:
        query = """
        MATCH (c:Circuito {nombre: $viejo})
        SET c.nombre = $nuevo
        RETURN c
        """
        session.run(query, viejo=nombreViejo, nuevo=nombreNuevo)
        print(f"Circuito actualizado a: {nombreNuevo}")

driver.close()