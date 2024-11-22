# importing required modules
from pypdf import PdfReader
from openai import OpenAI
from utils import getNLOntology
from rdflib import Graph
from rdflib_neo4j import Neo4jStore, Neo4jStoreConfig, HANDLE_VOCAB_URI_STRATEGY
import os

####### STEP1: GET THE UNSTRUCTURED CONTENT #########################

filename = "data/SimplicityEsportsGamingCompany.pdf"
reader = PdfReader(filename)
#print(len(reader.pages), "pages read from PDF document")

text = ""
for page in reader.pages:
    text+=page.extract_text()    

####### STEP2: GET THE ONTOLOGY #####################################
g = Graph()
g.parse("ontos/contract.ttl")

# OPTION 1 : Ontology in standard serialisation
ontology = g.serialize(format="ttl")

# OPTION 2 : Natural language description of the ontology
ontology = getNLOntology(g)


####### STEP3: PROMPT THE LLM ####################################### 

client = OpenAI(
    api_key=os.environ.get("MY_OPENAI_KEY"),
)

system = (
    "You are an expert in extracting structured information out of natural language text. "
    "You extract entities with their attributes and relationships between entities. "
    "You can produce the output as RDF triples or as Cypher write statements on request. "      
)

prompt = '''Given the ontology below run your best entity extraction over the content.
 The extracted entities and relationships must be described using exclusively the terms in the ontology 
 and in the way they are defined. This means that for attributes and relationships you will respect the domain and range constraints.
 You will never use terms not defined in the ontology. 
Return the output as RDF triples serialised using the Turtle format. 
Absolutely no comments on the output. Just the structured output. ''' + '\n\nONTOLOGY: \n ' + ontology + '\n\nCONTENT: \n ' + text 


# if you want to inspect...
#print(prompt)

chat_completion = client.chat.completions.create(
    messages=[
        {
          'role': 'system',
          'content': system,
        },
        {
          'role': 'user',
          'content': prompt ,
        }
          ],
    model="gpt-4o",
)

triples = chat_completion.choices[0].message.content
print(triples)
if triples.startswith("```turtle"):
    triples = triples[len("```turtle"):-len("```")]

print(triples)

####### STEP4: WRITE CONTENT TO THE DB ##############################

uri = "bolt://localhost:7687"
user = "neo4j"  # Change if you've modified the default username
password = "neoneoneo"  # Change to your actual password
dbname = "gm3"

AURA_DB_URI="bolt://localhost:7687"
AURA_DB_USERNAME="neo4j"
AURA_DB_PWD="neoneoneo"
AURA_DB_NAME="gm3"

auth_data = {'uri': AURA_DB_URI,
             'database': AURA_DB_NAME,
             'user': AURA_DB_USERNAME,
             'pwd': AURA_DB_PWD}

config = Neo4jStoreConfig(auth_data=auth_data,
                          custom_prefixes={},
                          handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE,
                          batching=True)

neo4j_aura = Graph(store=Neo4jStore(config=config))
neo4j_aura.parse(data=triples, format="ttl")
neo4j_aura.close(True)