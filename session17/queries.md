## Prompts used on chat GPT

```
what commercial products are associated with Rafa Nadal?

provide the answer in JSON

produce a cypher statement to read that json and create a graph in neo4j

can you describe the same thing in cypher statements so I can populate my knowledge graph with them?

provide the list of commercial products associated with Rafa Nadal as RDF

now using schema.org as vocabulary

produce a cypher statement to import the previous rdf into neo4j using neosemantics (n10s)

when running that i'm getting this error "A Graph Config is required for RDF importing procedures to run" can you help?

regenerate the RDF using wikidata identifiers (uris)

add the wikidata id also for Rafa Nadal

provide some facts about Banco Sabadell as RDF using wikidata ids and schema.org vocabulary
```

## Usage of OpenAI API through APOC

### Initialise database to import RDF

```
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE

call n10s.graphconfig.init()
```

### Invocation of `apoc.ml.openai.chat` procedure

```
:param apiKey: "your-open-ai-key-..."

:param prompt: [
{role:"system", content:"Provide answers in RDF serialised as Turtle. Use schema.org and wikidata ids for resources"},
{role:"user", content:"What brands are associated with Rafa Nadal?"}
]

CALL apoc.ml.openai.chat($prompt,  $apiKey) yield value
```

Call to openAI followed by RDF import via neosemantics

```
CALL apoc.ml.openai.completion('What are the top 3 most populated cities in the UK. Answer in RDF Turtle and use schema.org and wikidata uris', $apiKey, { max_tokens: 300 }) yield value
with value.choices[0].text as rdf
call n10s.rdf.preview.inline(rdf,"Turtle") yield nodes, relationships
return *
```
