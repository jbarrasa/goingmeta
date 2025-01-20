import asyncio, os
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver
from rdflib import Graph
from RAGSchemaFromOnto import getSchemaFromOnto

NEO4J_URI = "neo4j+s://20bf15ba.databases.neo4j.io" #"neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "c3EaVckJnDo_LLmvbMXfdALQMxgOvtuXDMncivc1NYU" #"neoneoneo"

# Connect to the Neo4j database
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

neo4j_schema = getSchemaFromOnto("ontos/sales-onto.ttl")
# print(neo4j_schema)

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
    entities=list(neo4j_schema.entities.values()),
    relations=list(neo4j_schema.relations.values()),
    potential_schema=neo4j_schema.potential_schema,
    on_error="IGNORE",
    from_pdf=True,
)

# LOAD PRODUCT DESCRIPTIONS
directory_path = "data/prod_desc"
for filename in os.listdir(directory_path):
    # if filename.endswith("6.pdf"):
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            print("processing file: ", filename)
            asyncio.run(kg_builder.run_async(file_path=str(file_path)))

# LOAD CREDIT NOTES
directory_path = "data/credit_notes"
for filename in os.listdir(directory_path):
    # if filename.endswith("3.pdf"):
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            print("processing file: ", filename)
            asyncio.run(kg_builder.run_async(file_path=str(file_path)))

driver.close()