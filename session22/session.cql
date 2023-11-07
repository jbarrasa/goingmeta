/////// Rebuild the graph from episode 21 in one go ///////////////////////////

// Load articles from CSV file
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session21/resources/data/devto-articles.csv' AS row
CREATE (a:Article { uri: row.uri})
SET a.title = row.title, a.body = row.body, a.datetime = datetime(row.date);

// Load the ontology
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

call n10s.graphconfig.init({ handleVocabUris: "IGNORE" });

call n10s.skos.import.fetch("https://github.com/jbarrasa/goingmeta/raw/main/session21/resources/ontos/dbpedia-sw.ttl","Turtle");

match (s:Class)-[shortcut:SCO]->(p:Class)<-[:SCO*2..]-(s)
delete shortcut;

// NEE and Linking (simplified)
load csv with headers from "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session21/resources/data/extracted-entities.csv" as row
match (a:Article { uri: row.articleuri})
MATCH (c:Class {uri: row.concepturi })
MERGE (a)-[:refers_to]->(c);

//create vector index
CALL db.index.vector.createNodeIndex('article-embeddings', 'Article', 'embedding', 1536, 'cosine');

//populate (embedding done offline)
call apoc.load.json("https://github.com/jbarrasa/goingmeta/raw/main/session21/resources/data/article-embeddings.json") yield value
match (a:Article { uri: value.id })
call db.create.setNodeVectorProperty(a,'embedding',value.vector);


///////////////////////////////////////////////////////////////////////////////



// graph based semantic similarity with RAG-ready output
match (a:Article { uri: "https://dev.to/qainsights/performance-testing-neo4j-database-using-bolt-protocol-in-apache-jmeter-1oa9"})-[rt1:refers_to]->(c1)
call n10s.sim.pathsim.search(c1,0.2,{ simulateRoot: false }) yield node as relatedTopic
with a,c1,collect(relatedTopic) + [c1] as topics
unwind topics as c2
match (similarArticle:Article )-[rt2:refers_to]->(c2) //where similarArticle <> a
with a.title as original, similarArticle.title as similar,
[x in collect(n10s.sim.pathsim.value(c1,c2, { simulateRoot: false})) where x > 0 ] as sims ,
collect(n10s.sim.pathsim.path(c1,c2, { simulateRoot: false})) as paths,
collect(["the original article mentions explicitly " + nodes(n10s.sim.pathsim.path(c1,c2, { simulateRoot: false}))[0].prefLabel ]  +
 [" the recommended article mentions explicitly " + nodes(n10s.sim.pathsim.path(c1,c2, { simulateRoot: false}))[-1].prefLabel]  + [r in relationships(n10s.sim.pathsim.path(c1,c2, { simulateRoot: false})) | startNode(r).prefLabel + " is a type of " + endNode(r).prefLabel]) as paths_as_text
where sims <> []
return original, similar, apoc.coll.avg(sims) as sim, sims, reduce(result="", x in paths_as_text | result + reduce(inner="", y in x | inner + "\n"+y)) //, paths
order by sim desc limit 4



// vector based semantic search with RAG-ready output
match (a:Article { uri: "https://dev.to/qainsights/performance-testing-neo4j-database-using-bolt-protocol-in-apache-jmeter-1oa9"})
call db.index.vector.queryNodes('article-embeddings', 7, a.embedding)
yield node AS similarArticle, score
where  similarArticle <> a
return a.title as original, similarArticle.title as similar, score



// Changes in the KG have an impact in the results
// Loading another ontology
CALL n10s.onto.import.fetch("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session21/resources/ontos/swstacks.ttl","Turtle");





//vector based semantic search
match (a:Article { uri: "https://dev.to/qainsights/performance-testing-neo4j-database-using-bolt-protocol-in-apache-jmeter-1oa9"})
call db.index.vector.queryNodes('article-embeddings', 5, a.embedding)
yield node AS similarArticle, score
where  similarArticle <> a
return a.title as original, similarArticle.title as similar, score

//path based semantic similarity
match (a:Article { uri: "https://dev.to/qainsights/performance-testing-neo4j-database-using-bolt-protocol-in-apache-jmeter-1oa9"})-[rt1:refers_to]->(c1)
match (similarArticle:Article)-[rt2:refers_to]->(c2) where similarArticle <> a
return a.title as original, similarArticle.title as similar, avg(n10s.sim.pathsim.value(c1,c2)) as sim, collect(n10s.sim.pathsim.value(c1,c2)) order by sim desc limit 4
