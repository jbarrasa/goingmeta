from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from utils import getNLOntology
from rdflib import Graph

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "")

# Connect to Neo4j database
driver = GraphDatabase.driver(URI, auth=AUTH)

# Create LLM object
llm = OpenAILLM(model_name="gpt-4o")
g = Graph()
neo4j_schema = getNLOntology(g.parse("ontos/art.ttl"))
#print(neo4j_schema)

# Initialize the retriever
retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,  # type: ignore
    neo4j_schema=neo4j_schema,
    # examples=examples,
)

# Generate a Cypher query using the LLM, send it to the Neo4j database, and return the results
query_text = "Who painted 'The Master Printer of Los Angeles'?"
result = retriever.search(query_text=query_text)
print("generated query: \n", result.metadata['cypher'])
for item in result.items:
    print("answer:", item.content)