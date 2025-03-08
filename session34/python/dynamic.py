import json
import os
from neo4j import GraphDatabase
from pydantic import create_model, Field
from langchain.tools import StructuredTool
from langchain.agents import initialize_agent
from langchain.chat_models import ChatOpenAI

# Set your Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neoneoneo")

# Create a Neo4j driver instance
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), database="art")


def create_tool_from_config(tool_config: dict, driver) -> StructuredTool:
    """
    Given a tool config dictionary, create a StructuredTool that
    executes the specified Cypher query.
    """

    name = tool_config["name"]
    description = tool_config.get("description", "")
    cypher_query = tool_config["cypher_query"]

    InputModel = create_model( name + "InformationInput", 
                              input=(str, Field(..., description="input parameter as string")))

    # Define the function that will execute the Cypher query
    def tool_func(data) -> str:
        if isinstance(data, str):
            data = InputModel.model_validate({ 'input': str(data) })
        # If data is a dict, convert it using the InputModel.
        elif isinstance(data, dict):
            data = InputModel.model_validate(data)
    
        params = data.model_dump()
        with driver.session() as session:
            result = session.run(cypher_query, **params)
            records = []
            for record in result:
                # Convert each record to a string representation
                record_dict = dict(record)
                record_str = ", ".join(f"{k}: {v}" for k, v in record_dict.items())
                records.append(record_str)
            return "\n".join(records) if records else "No results found."

    # Create and return the StructuredTool instance
    tool = StructuredTool(
        name=name,
        description=description,
        args_schema=InputModel,
        func=tool_func
    )
    return tool

def load_tools_from_ontology(driver) -> list:
    """
    Reads tool configurations from the ontology.
    """
    onto_query = "match (t:Tool) return t.name as name, t.description as description, t.cypher_query as cypher_query"

    with driver.session() as session:
        result = session.run(onto_query)
        records = []
        for record in result:
            record_dict = dict(record)
            records.append(record_dict)
                
        tools = []
        for record in records:
            tool = create_tool_from_config(record, driver)
            tools.append(tool)
        return tools

def main():
    # Load tools from the ontology
    tools = load_tools_from_ontology(driver)

    # Initialize the language model (e.g., ChatGPT-style)
    llm = ChatOpenAI(temperature=0, model="gpt-4o")

    # Initialize the agent with the dynamically created tools
    agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

    # Simple interactive loop
    print("Welcome to the Neo4j Chatbot with Ontology defined Tools!")
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
