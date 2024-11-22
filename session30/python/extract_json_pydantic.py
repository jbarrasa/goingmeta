# importing required modules
from pypdf import PdfReader
from openai import OpenAI
from schema import Document
from neo4jconnector import Neo4jConnection
import os, json

####### STEP1: GET THE UNSTRUCTURED CONTENT #########################

filename = "data/SimplicityEsportsGamingCompany.pdf"
reader = PdfReader(filename)
#print(len(reader.pages), "pages read from PDF document")

text = ""
for page in reader.pages:
    text+=page.extract_text()    

####### STEP2: PROMPT THE LLM AND SET THE VALIDATIONS ################
####### DERIVED FROM THE ONTOLOGY                     ################

SYSTEM_PROMPT = "You are a contract information extraction assistant."
PROMPT_TEMPLATE = """ Extract the contract information from the following text:\n\n{text}"""

client = OpenAI(api_key=os.environ.get("MY_OPENAI_KEY"))
MODEL = "gpt-4o" # try with -mini

def extract_contract_info(text):
   response = client.beta.chat.completions.parse(
       model=MODEL,
       messages=[
           {"role": "system", "content": SYSTEM_PROMPT},
           {"role": "user", "content": PROMPT_TEMPLATE.format(text=text)},
       ],
       response_format=Document
   )
   return response.choices[0].message

contract_info = extract_contract_info(text)

data = json.loads(contract_info.content)
pretty_response = json.dumps(data, indent=2)
print(pretty_response)


####### STEP3: WRITE CONTENT TO THE DB ##############################

uri = "bolt://localhost:7687"
user = "neo4j"  # Change if you've modified the default username
password = "neoneoneo"  # Change to your actual password
dbname = "gm3"
conn = Neo4jConnection(uri, user, password, dbname)

with open("other/import.cypher", 'r', encoding='utf-8') as file:
    cypher_script = file.read()

# Run the Cypher script and get the results
result = conn.run_cypher(cypher_script, {"jsondata" : data })

# Close the connection
conn.close()
