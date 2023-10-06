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
MERGE (a)-[:refers_to]->(c)


// Loading another ontology
CALL n10s.onto.import.fetch("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session21/resources/ontos/swstacks.ttl","Turtle");


//create vector index 
CALL db.index.vector.createNodeIndex('article-embeddings', 'Article', 'embedding', 1536, 'cosine')

//populate (embedding done offline)
call apoc.load.json("https://github.com/jbarrasa/goingmeta/raw/main/session21/resources/data/article-embeddings.json") yield value
match (a:Article { uri: value.id }) set a.embedding = value.vector

  
//vector based semantic similarity
match (a:Article { title: "Performance Testing Neo4j Database using Bolt Protocol in Apache JMeter"})
match (b:Article { title: "Couchbase GeoSearch with ASP.NET Core"})
return gds.similarity.cosine(a.embedding,b.embedding)

// graph based semantic similarity
match (a:Article { title: "Performance Testing Neo4j Database using Bolt Protocol in Apache JMeter"})-[rt1:refers_to]->(c1)
match (b:Article { title: "Couchbase GeoSearch with ASP.NET Core"	})-[rt2:refers_to]->(c2)
return n10s.sim.pathsim.value(c1,c2, { simulateRoot:false }) as sim, [n in nodes(n10s.sim.pathsim.path(c1,c2, { simulateRoot: false})) | n.prefLabel]
//return *, n10s.sim.pathsim.path(c1,c2, { simulateRoot:false })


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



