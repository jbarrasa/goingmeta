from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from ollama import chat
from ollama import ChatResponse
import re, json, os, asyncio
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver
from rdflib import Graph
from onto_utils import getSchemaFromOnto, getPKs

# Define the state for our workflow.
class State(TypedDict, total=False):
    user_text: str               # The input text provided by the user
    extracted_ontology: str      # Results from the first LLM call to extract key categories/relationships
    text_coverage: float         # Coverage rate by existing ontos
    matched_ontologies: str        # The matching ontology (if one was found in the catalog)
    validation_response: str     # User validation for candidate ontology inclusion

# Node 1: Extract key categories and relationship types (ontology extraction)
def extract_ontology(state: State):
    """
    Call an LLM to parse the user text and extract key categories and relationship types.
    """

    PROMPT = f"""
    Analyze the following text and extract a rudimentary ontology:
    1. Categories of entities mentioned in the text (persons, objects, locations, events, etc). 
    2. Relationship types between these categories.

    Format:
    {{ "categories": [ "category1", "category2", "category3"...],
       "relationshipTypes" : [
        {{ name: "relType1", fromCat: "category1", to: "category2" }},
        {{ name: "relType2", fromCat: "category3", to: "category1" }},
       ]
    }}
    Do not generate any additional notes or comments. 

    Examples: 
     Input: "Cristiano Ronaldo plays for the Spanish club Real Madrid"
     {{ "categories": [ "Football Player", "Football Club", "Country"],
       "relationshipTypes" : [
        {{ name: "plays for", fromCat: "Football Player", to: "Football Club" }},
        {{ name: "based in ", fromCat: "Football Club", to: "Country" }},
       ]
     }}
     Input: "The Eiffel Tower is a landmark in Paris named after the engineer Gustave Eiffel"
     {{ "categories": [ "Landmark", "City", "Person"],
       "relationshipTypes" : [
        {{ name: "located in", fromCat: "Landmark", to: "City" }},
        {{ name: "named after", fromCat: "Landmark", to: "Person" }},
       ]
     }}

    Text:
    \"\"\"{state['user_text']}\"\"\"
    """
    
    response: ChatResponse = chat(model='gemma3:4b', messages=[
    {
        'role': 'user',
        'content': PROMPT ,
    },
    ])

    cleaned = re.sub(r"```json\s*([\s\S]+?)\s*```", r"\1", response['message']['content'].strip(), flags=re.IGNORECASE)
    
    # Optionally handle cases without code fences, just try to parse
    try:
        json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("Failed to parse as JSON:", e)
        cleaned = "{}"

    return {"extracted_ontology":  cleaned }

# Node 2: Look up the most relevant ontology from a catalog
def lookup_ontology(state: State):
    """
    Lookup the catalog to find a matching ontology based on the extracted details.
    """
    if state["extracted_ontology"]:
        #entities successfully extracted in the previous step.
    
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USERNAME = "neo4j"
        NEO4J_PASSWORD = "neoneoneo"

        # Connect to the Neo4j database
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD), database="onto")

        query = f"""
        unwind $categories as cat
        call db.index.vector.queryNodes("label_and_desc", 1, genai.vector.encode(cat, 'OpenAI', {{ token: \"{os.getenv("OPENAI_API_KEY")}\" }})) yield node, score
        where score > 0.92
        with $categories as lookup_cats, collect({{cat: cat, matching_uri: node.uri, score: score, prov: node.prov }}) as results
        return lookup_cats, results as detailed_results,  size(results) * 1.0 / size(lookup_cats) as coverage, apoc.convert.toSet([x in results | x.prov ]) as onto_list
        """        

        with driver.session() as session:
            query_result = session.run(query, json.loads(state["extracted_ontology"]) or {})
            result = [record.data() for record in query_result]
            print("Detailed results of Ontology lookup:")
            print(result)
        return {"matched_ontologies": result[0]['onto_list'] if len(result) > 0 else [], 
                "text_coverage": float(result[0]['coverage'] if len(result) > 0 else 0 )}
    else:
        return {"matched_ontologies": [], "text_coverage": 0 }

# Decision gate: Check whether a matching ontology was found.
def ontology_exists(state: State):
    """
    Conditional function to decide the next step:
    """
    return "PASS" if state.get("text_coverage") > 0.3 else "FAIL"

# Node 5: Run entity extraction with the selected ontology to produce structured output
def extract_graph(state: State):
    """
    Run KG builder pipeline to extract entities and structure the output according to the matched ontologies.
    """
    # Simulated LLM call – replace with your entity extraction implementation.
    prompt = (f"Extract entities and relationships from the following text following the ontology "
              f"{state['matched_ontologies']}: {state['user_text']}")
    simulated_output = f"StructuredGraph: (Person)-[WorksAt]->(Organization) extracted from text."
    
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = "neoneoneo"

    # Connect to the Neo4j database
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    g = Graph()
    for url in state['matched_ontologies']:
        print("Retrieving onto: ", url)
        g.parse(url)

    neo4j_schema = getSchemaFromOnto(g)
    print(neo4j_schema)

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
        from_pdf=False,
    )
    print("Running KG build pipeline on : ", state['user_text'])
    st = asyncio.run(kg_builder.run_async(text=state['user_text']))
    return {}


# Node 7: Propose a candidate ontology for user review when there is no match
def propose_candidate_ontology(state: State):
    """
    Return the candidate ontology (from the extraction step) to be added to the catalog.
    Request user validation before inclusion.
    """
    # In an interactive environment, you might want to wait for actual user input.
    candidate = state["extracted_ontology"]
    print("No matching ontology was found in the catalog.")
    print("Proposed candidate ontology for catalog inclusion:\n")
    PROMPT = f"""
    Analyze the following rudimentary ontology in the form of a list of 
    1. Categories 
    2. Relationship types between these categories

    The input format is as follows:
    {{ "categories": [ "category1", "category2", "category3"...],
       "relationshipTypes" : [
        {{ name: "relType1", fromCat: "category1", to: "category2" }},
        {{ name: "relType2", fromCat: "category3", to: "category1" }},
       ]
    }}
    Produce an OWL based serialisation in Turtle format for that description.
    Essentially create a owl:Class out of each category and an owl:ObjectProperty out of each relationship.
    Then add rdfs:domain to the category in 'fromCat' and rdfs:range to the category in 'to'.
    Do not generate any additional notes or comments. 

    Ontology:
    {state['extracted_ontology']}
    """
    
    response: ChatResponse = chat(model='gemma3:4b', messages=[
    {
        'role': 'user',
        'content': PROMPT ,
    },
    ])

    cleaned = re.sub(r"```turtle\s*([\s\S]+?)\s*```", r"\1", response['message']['content'].strip(), flags=re.IGNORECASE)
    print (cleaned)
    
    # For simulation purposes, we use input(). In a real chain, this could be a UI prompt.
    response = input("Do you want to add this ontology to the catalog? (yes/no): ")
    return {"validation_response": response}

# ------------------------------------------------------------------------------
# Build the workflow (state graph)

workflow = StateGraph(State)

# Add nodes to the workflow
workflow.add_node("extract_ontology", extract_ontology)
workflow.add_node("lookup_ontology", lookup_ontology)
workflow.add_node("extract_graph", extract_graph)
workflow.add_node("propose_candidate_ontology", propose_candidate_ontology)

# Connect the nodes with edges:
# Step 1 is assumed to be the initial state ('user_text' provided by the user)
workflow.add_edge(START, "extract_ontology")
workflow.add_edge("extract_ontology", "lookup_ontology")
# Conditional branch based on whether a matching ontology was found
workflow.add_conditional_edges(
    "lookup_ontology",
    ontology_exists,
    {"PASS": "extract_graph", "FAIL": "propose_candidate_ontology"}
)
# If matched, run extraction to align the text with the ontology and insert into Neo4j.
workflow.add_edge("extract_graph",  END)
# If not matched, propose candidate ontology and ask for validation.
workflow.add_edge("propose_candidate_ontology", END)

# Compile the workflow
chain = workflow.compile()

# Display the workflow graph (rendered as a Mermaid diagram image)
flow_graph = Image(chain.get_graph().draw_mermaid_png())
with open("flow.png", "wb") as f:
    f.write(flow_graph.data)

# ------------------------------------------------------------------------------
# Invoke the workflow
# Provide initial user text as input; in a real case this could come from a web form or another input mechanism.
initial_state = {"user_text": 
                #    "Arsenal FC is a club based in London. "
                #    "Thierry Henry used to play for them."
                #"'1984' by George Orwell is a dystopian novel while 'Pride and Prejudice' by Jane Austen, on the other hand, is a classic romance and social satire."
                #"'The House of Beckham' is a book by Tom Bower. It's a non authorised biography of David Beckham, famous footballer who used to play for Manchester United."
                #"Alex Erdl and Jesus Barrasa work for Neo4j"
                 }

# Execute the chain
state = chain.invoke(initial_state)

print(state)
