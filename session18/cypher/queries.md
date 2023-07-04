# Stardog
## Run the first part of the notebook to populate the graph
[notebook (see part 1 on Stardog)](../Easy_full_graph_migration_from_triple_stores.ipynb)
## Exploring the database with SPARQL

Exploring Nirvana...

```
select ?p ?o 
where {

<http://stardog.com/tutorial/Nirvana_(band)>  ?p ?o 

}
```

## Complete the migration from the notebook and check data on both sides is identical

## SPARQL on Stardog Studio: All about 'Shake it off'

```
select  ?s ?p ?o 
where {
    
    ?s ?p ?o 
    
    filter (?s = <http://stardog.com/tutorial/Shake_It_Off>
     || ?o = <http://stardog.com/tutorial/Shake_It_Off> )

}
```

## Cypher on Neo4j browser: All about 'Shake it off'

```
match  subgraph = (:Resource { uri: "http://stardog.com/tutorial/Shake_It_Off"})--()
return subgraph
```

## Cypher: All about 'Shake it off' exported as RDF (N-Triples)

```
:post /rdf/neo4j/cypher
{"cypher": " match (r:Resource {uri: 'http://stardog.com/tutorial/Shake_It_Off'})-[rel]-() return r, rel ", "format": "N-Triples"}
```

# Ontotext

## Complete the migration from the notebook and check data on both sides is identical
[notebook (see part 2 on Ontotext)](../Easy_full_graph_migration_from_triple_stores.ipynb)

## SPARQL: Triples with sto:StandardOrganization as subject
Test on [Ontotext SPARQL endpoint](https://i40kg.ontotext.com/graphdb/sparql)
```
PREFIX sto: <https://w3id.org/i40/sto#>
select distinct ?s ?p ?o 
WHERE { ?s ?p ?o 
    filter (?s = sto:StandardOrganization )}
```

## Cypher: sto:StandardOrganization and outgoing rels exported as RDF (N-Triples)
```
:post /rdf/i40kg/cypher
{"cypher": " match (r:Resource {uri: 'https://w3id.org/i40/sto#StandardOrganization'})-[rel]->() return r, rel ", "format": "N-Triples"}
```
