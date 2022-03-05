
0. Install n10s in your neo4j installation: You can do it in a couple of clicks from the neo4j desktop (plugins section of your DB) 

    <img src="https://raw.githubusercontent.com/neo4j-labs/rdflib-neo4j/master/img/install-n10s.png" height="400">

Or you can do it manually following the [instructions in the manual](https://neo4j.com/labs/neosemantics/4.0/install/)

1. Build the KG with the script in [build-kg.cypher](https://github.com/jbarrasa/goingmeta/blob/main/session2/build-kg.cypher)
2. Semantic search on the KG
  * Articles on _"NoSQL database management system"_: Directly or indirectly connected to that category.
```
MATCH path = (:Concept {prefLabel: "NoSQL database management system"})<-[:broader*0..]-(sc)<-[:refers_to]-(art:Article)
return art.title, [x in nodes(path) where x:Concept | coalesce(x.prefLabel,"") + coalesce(x.label,"") ]
```
  * Same query using n10s inferencing method
```
match (c:Concept {prefLabel: "NoSQL database management system"})
call n10s.inference.nodesInCategory(c, { inCatRel: "refers_to"}) yield node as article
return article.title as result
```
  * Articles on _RDBMSs_ and _Document DBs_
```
MATCH path = (a:Concept)<-[:broader*0..]-()<-[:refers_to]-(art:Article)-[:refers_to]->()-[:broader*0..]->(b:Concept)
WHERE a.prefLabel = "document-oriented database" and 
b.prefLabel = "relational database management system"
return art.title
```
  * _"Read next"_ type of queries. Recommendation/personalisation. Use this query to create a search phrase in Bloom and visually explore recommendation paths.
```
match simpath = (a:Article)-[:refers_to]->(cat)-[:broader*0..1]->()<-[:broader*0..1]-()<-[:refers_to]-(other)
where a.uri = "https://dev.to/qainsights/performance-testing-neo4j-database-using-bolt-protocol-in-apache-jmeter-1oa9"
return other.title, [x in nodes(simpath) where x:Concept | coalesce(x.prefLabel,x.label) ]
```
