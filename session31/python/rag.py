from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings import OpenAIEmbeddings

# 1. Neo4j driver
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "")

INDEX_NAME = "chunk-index"

# Connect to Neo4j database
driver = GraphDatabase.driver(URI, auth=AUTH)

# 2. Retriever
# Create Embedder object, needed to convert the user question (text) to a vector
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize the retriever
retriever = VectorRetriever(driver, INDEX_NAME, embedder)

# 3. LLM
# Note: the OPENAI_API_KEY must be in the env vars
llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})

# Initialize the RAG pipeline
rag = GraphRAG(retriever=retriever, llm=llm)

# Query the graph
query_text = "who painted 'La Femme qui pleure' ?"
response = rag.search(query_text=query_text, retriever_config={"top_k": 1})
print(response.answer)