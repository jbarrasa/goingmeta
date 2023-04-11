// Load movies
call apoc.load.json("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session15/data/movies.json") yield value
create (:Movie { title: value.title, released: value.released, tagline: value.tagline });

// Load people
call apoc.load.json("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session15/data/people.json") yield value
unwind value.people as person
merge (p { name: person.name }) on create set p.born = person.born
with p,person
call apoc.create.addLabels(p,person.labels) yield node
FOREACH ( mov IN person.directed | merge (m:Movie {title: mov}) merge (m)<-[:DIRECTED]-(p))
FOREACH ( mov IN person.acted | merge (m:Movie {title: mov}) merge (m)<-[:ACTED_IN]-(p))
FOREACH ( mov IN person.produced | merge (m:Movie {title: mov}) merge (m)<-[:PRODUCED]-(p))
FOREACH ( mov IN person.reviewed | merge (m:Movie {title: mov}) merge (m)<-[:REVIEWED]-(p))
FOREACH ( mov IN person.wrote | merge (m:Movie {title: mov}) merge (m)<-[:WROTE]-(p))
FOREACH ( loc IN person.pob | merge (pl:Place {country: loc.country, region: loc.region, location: loc.location}) merge (pl)<-[:PLACE_OF_BIRTH]-(p));

// Let's look at the graph first: This query should give a good overview of what's in it
match pattern = (a:Actor)-[:ACTED_IN]->(:Movie)<-[:DIRECTED]-(:Director)-[:PLACE_OF_BIRTH]->(pob)<-[:PLACE_OF_BIRTH]-(a)
return pattern limit 2;

// What if we look at the schema? output is a bit confusing...
call db.schema.visualization();

// How about adding a semantic layer?

// Let's set up the config to import the ontology
call n10s.graphconfig.init({ handleVocabUris: "IGNORE"})

// Now let's import it
call n10s.onto.import.fetch("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session15/onto/complete-movies-goingmeta.ttl","Turtle", { languageFilter: "en"})

//The semantic layer (the ontology) drives the exploration of the graph from the app
run the following in your python environment and explore in the browser
streamlit run semantic.py

//And don't forget we still can export the graph as RDF if needed
:post http://localhost:7474/rdf/movies/cypher
{"cypher": "match subgraph = (sw:ScreenWriter)-[:WROTE]->(:Movie { title: 'Top Gun' }) return subgraph "}
