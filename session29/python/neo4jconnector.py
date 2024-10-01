from neo4j import GraphDatabase

# Define the Neo4j database connection class
class Neo4jConnection:

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def run_cypher(self, cypher_query):
        with self._driver.session() as session:
            result = session.run(cypher_query)
            return result.data()  # Fetch all results

