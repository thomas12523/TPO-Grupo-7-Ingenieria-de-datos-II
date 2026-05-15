from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)



with driver.session() as session:

    result = session.run("""

        RETURN "Hello World" AS mensaje

    """)

    for record in result:

        print(record["mensaje"])

driver.close()