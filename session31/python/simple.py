import asyncio, os
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver
from rdflib import Graph
from utils import getSchemaFromOnto, getPKs

NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = ""

# Connect to the Neo4j database
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

g = Graph()
neo4j_schema = getSchemaFromOnto(g.parse("ontos/art.ttl"))
#print(neo4j_schema)

# Create a Splitter object
splitter = FixedSizeSplitter(chunk_size=2500, chunk_overlap=10)

# Create an Embedder object
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# Instantiate the LLM
llm = OpenAILLM(
    model_name="gpt-4o",
    model_params={
        "max_tokens": 3000,
        "response_format": {"type": "json_object"},
        "temperature": 0,
    },
)

#Instantiate the SimpleKGPipeline
kg_builder = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    text_splitter=splitter,
    embedder=embedder,
    entities=neo4j_schema.entities.values(),
    relations=neo4j_schema.relations.values(),
    potential_schema=neo4j_schema.potential_schema,
    on_error="IGNORE",
    from_pdf=False,
)

directory_path = "data"

for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            print("processing file: ", filename)
            asyncio.run(kg_builder.run_async(text=file.read()))


for pk in getPKs(g):
    resolver = SinglePropertyExactMatchResolver(driver=driver, resolve_property=pk)
    asyncio.run(resolver.run())

driver.close()