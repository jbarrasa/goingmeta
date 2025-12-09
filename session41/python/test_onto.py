from openai import OpenAI
import requests, time, os
from utils import getNLOntology, processResults

# ---------- Client setup ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ---------- Import corpus and onto ----------

onto_url = 'https://raw.githubusercontent.com/nemegrod/graph_RAG/refs/heads/main/data/jaguar_ontology.ttl'
data_url = 'https://raw.githubusercontent.com/nemegrod/graph_RAG/refs/heads/main/data/jaguar_corpus.txt'

try:
    response = requests.get(onto_url)
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    ontology = response.text
    print(f"Successfully loaded ontology from {onto_url}. Content length: {len(ontology)} characters.")
except requests.exceptions.RequestException as e:
    print(f"Error fetching ontology from {onto_url}: {e}")

try:
    response = requests.get(data_url)
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    corpus = response.text
    print(f"Successfully loaded text from {data_url}. Content length: {len(corpus)} characters.")
except requests.exceptions.RequestException as e:
    print(f"Error fetching ontology from {data_url}: {e}")


tests = [{"test_id": "owl_onto", "prompt_body": """Extract relevant named entities, their relations and related information from this text. 
Think deep and analyze all information in the relevant text thoroughly. 
Try to infer relevant relationships between entities if not directly mentioned in the text.
Return the results as RDF triples using Turtle serialisation that align with the ontology for the found entities and relationships. 
Make sure to give all entities relevant rdfs:label. Use the namespace '"http://example.org/resource#' for extracted entities.""", 
"onto_prefix": "##ONTOLOGY: ", "ontology": ontology, "corpus_prefix": "##TEXT: ", "corpus": corpus},
{"test_id": "nl_onto", "prompt_body": """Extract relevant named entities, their relations and related information from this text. 
Think deep and analyze all information in the relevant text thoroughly. 
Try to infer relevant relationships between entities if not directly mentioned in the text.
Return the results as RDF triples using Turtle serialisation that align with the ontology for the found entities and relationships. 
Make sure to give all entities relevant rdfs:label. Use the namespace '"http://example.org/resource#' for extracted entities and '"http://example.org/ontology#' for the vocabulary terms.""", 
"onto_prefix": "##ONTOLOGY: ", "ontology": getNLOntology(ontology), "corpus_prefix": "##TEXT: ", "corpus": corpus},
# {"test_id": "pydantic_onto", "prompt_prefix": "Given this ontology: ", "ontology": ontology, "prompt_body": """Extract relevant named entities, their relations and related information from this text. 
# Think deep and analyze all information in the relevant text thoroughly. 
# Try to infer relevant relationships between entities if not directly mentioned in the text.
# Return the results as RDF triples using Turtle serialisation that align with the ontology for the found entities and relationships. 
# Make sure to give all entities relevant rdfs:label.""", "corpus": corpus}
]

for iteration in range(1, 10):

    results = {}

    for t in tests:
        print(f"\n=== Testing {t["test_id"]+ "__" + str(iteration)} ===")
        start = time.time()
        try:
            prompt = f"""{t["prompt_body"]}\n\n{t["onto_prefix"]}\n\n{t["ontology"]}\n\n{t["corpus_prefix"]}\n\n{t["corpus"]}
            """
            with open("ontoproject/output/" + t["test_id"] + ".prompt", "w", encoding="utf-8") as f:
                f.write(prompt)
    # gpt-4.1, gpt-5-mini
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=30000    
            )

            elapsed = time.time() - start

            # Token info lives under response.usage
            usage = getattr(response, "usage", None)
            usage_info = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            } if usage else {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

            

            print(f"✅ Success in {elapsed:.2f}s | tokens: {usage_info['total_tokens']}")
            
            with open("ontoproject/output/" + t["test_id"] + "__" + str(iteration) + ".ttl", "w", encoding="utf-8") as f:
                f.write(response.choices[0].message.content)

            print(processResults(response.choices[0].message.content))

            results[t["test_id"]] = {
                "status": "success",
                "time": elapsed,
                "usage": usage_info,
                "output": response,
            }

        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ {t["test_id"]} failed in {elapsed:.2f}s: {e}")
            results[t["test_id"]] = {"status": "error", "time": elapsed, "error": str(e)}

    # Print the response content
    #print(response.choices[0].message.content)