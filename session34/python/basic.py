import os
from neo4j import GraphDatabase
from langchain.agents import initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool

# Set your Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neoneoneo")

# Create a Neo4j driver instance
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), database="art")


@tool
def get_artist_works(artist: str) -> str:
    """
    Retrieve all artwork titles for a given artist_name.
    """
    query = """
    MATCH (a:Artist {name: $artist_name})<-[:created_by]-(aw:Artwork)
    RETURN aw.title as artwork_title
    """
    with driver.session() as session:
        result = session.run(query, artist_name=artist)
        artworks = []
        for record in result:
            artworks.append(f"{record['artwork_title']}")
        if artworks:
            return "Artworks created: " + ", ".join(artworks)
        else:
            return f"No artworks found for artist with name: {artist}"

# not really useful, just to show that you can define multiple tools
# backed by basic cypher only or using the different indexes (fultext,vector,etc)
@tool
def search_topic(topic: str) -> str:
    """
    Search for a topic on the Neo4j vector index 'productsVectorIndex'
    and return matching nodes along with their neighbourhood.
    """
    query = """
    CALL db.index.fulltext.queryNodes('ft', $searchTopic)
    YIELD node, score
    MATCH (node)-[r]-(connectedNode:Chunk) with node, connectedNode limit 2
    RETURN node.text as content, collect(connectedNode.text) as neighbours
    """
    with driver.session() as session:
        result = session.run(query, searchTopic=topic)
        results = []
        for record in result:
            neighbours = record['neighbours']
            neighbours_str = ", ".join(neighbours) if neighbours else "None"
            results.append(f"Node: {record['content']}, Neighbours: {neighbours_str}")
        if results:
            return "\n".join(results)
        else:
            return f"No matching nodes found for topic: {topic}"


# Initialize the language model (using a ChatGPT-style model)
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

# Register the tools automatically via the decorator
tools = [get_artist_works, search_topic]

# Initialize the agent using a zero-shot agent approach with our tools
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)


def main():
    print("Welcome to the LangChain Neo4j Chatbot!")
    print("How can I help today?")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        try:
            response = agent.run(user_input)
            print("Chatbot:", response)
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
