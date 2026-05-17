from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)


# funciones para crear los nodos de relaciones y atender a los CUs

def vincular_piloto_temporada(nombrePiloto,anioTemporada,podios):

    with driver.session() as session:
        query="""
        MERGE (p:Piloto {nombre: $nombre})
        MERGE (t:Temporada {anio: $anio})
        MERGE (p) -[r:PARTICIPO_EN]->(t)
        SET r.podios= $podios
        """
        session.run(query,nombre=nombrePiloto,anio=anioTemporada,podios=podios)
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



# ¿Qué pais han tenido mayor cantidad de carreras O que pais tiene mas de 1 circuito?

driver.close()