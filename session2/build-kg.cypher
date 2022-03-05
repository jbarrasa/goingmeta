:params key => ("<insert-key-here>")

// Load articles from CSV file
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session2/resources/devto-articles.csv' AS row
CREATE (a:Article { uri: row.uri})
SET a.title = row.title, a.body = row.body, a.datetime = datetime(row.date);


// Load the concept scheme using n10s
CREATE CONSTRAINT n10s_unique_uri ON (r:Resource) ASSERT r.uri IS UNIQUE;

call n10s.graphconfig.init({ handleVocabUris: "IGNORE", classLabel: "Concept", subClassOfRel: "broader"});

call n10s.skos.import.fetch("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session2/resources/goingmeta-skos.ttl","Turtle");

// Remove redundant 'broader' relationships (from Wikidata extract)
match (s:Concept)-[shortcut:broader]->(:Concept)<-[:broader*2..]-(s)
delete shortcut;


CALL apoc.periodic.iterate(
  "MATCH (a:Article)
   WHERE not(exists(a.processed))
   RETURN a",
  "CALL apoc.nlp.gcp.entities.stream([item in $_batch | item.a], {
     nodeProperty: 'body',
     key: $key
   })
   YIELD node, value
   SET node.processed = true
   WITH node, value
   UNWIND value.entities AS entity
   WITH entity, node
   WHERE not(entity.metadata.wikipedia_url is null)
   MATCH (c:Concept {altLabel: entity.metadata.wikipedia_url})
   MERGE (node)-[:refers_to]->(c)",
  {batchMode: "BATCH_SINGLE", batchSize: 10, params: {key: $key}})
YIELD batches, total, timeTaken, committedOperations
RETURN batches, total, timeTaken, committedOperations;


# import another ontology (software stack onto)

CALL n10s.onto.import.fetch("http://www.nsmntx.org/2020/08/swStacks","Turtle");

