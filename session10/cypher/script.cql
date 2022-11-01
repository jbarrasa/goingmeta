//there's data in your KG that you want to enrich...

MERGE (n:Organization { ticker:"CAT" });
MERGE (n:Organization { ticker:"ACN" });
MERGE (n:Organization { ticker:"FTNT" });
MERGE (n:Organization { ticker:"WDAY" });
MERGE (n:Organization { ticker:"SNOW" });
MERGE (n:Organization { ticker:"AVGO" });
MERGE (n:Organization { ticker:"FB" });
MERGE (n:Organization { ticker:"DUOL" });



//get some additional info for companies using DBPedia SPARQL endpoing
// and consume as you would consume any other csv file
with 'https://dbpedia.org/sparql/?format=text%2Fcsv&query=' as endpoint,
'select (?company as ?uri) (?name as ?companyname)
where {
  # match company by ticker
  ?company a dbo:Company ;
        dbp:symbol "<<ticker>>"@en ;
        rdfs:label ?name .

  filter(lang(?name) = "en")
}
' as query

match (o:Organization) where o.ticker is not null

load csv with headers from endpoint + apoc.text.urlencode(replace(query,"<<ticker>>", o.ticker)) as row

return o.ticker, row.companyname, row.uri

// we can use the results to set the name property...

// if we replace the return fragment with this, we can create an RDF twin in
// our graph to have the import merging things for me
merge (r:Resource { uri: row.uri })
merge (o)-[:wikidata_twin]->(r)


//we're going to be importing RDF so let's configure:
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE
call n10s.graphconfig.init({handleVocabUris:"IGNORE"})


// if we replace the return fragment with this, we can create an RDF twin in
// our graph to have the import merging things for me
merge (r:Resource { uri: row.uri })
merge (o)-[:wikidata_twin]->(r)

// or we can even reuse the Organization nodes
SET o:Resource , o.uri = row.uri

//get all

WITH '
construct {
    ?company a dbo:Company ;  ?cpred ?cobj ; ?relToPerson ?person ; ?relToPlace ?place .
    ?person a dbo:Person ; rdfs:label ?pobj ; ?relToPersonInv ?company .
    ?place a dbo:Place ;  rdfs:label ?plobj ; ?relToPlaceInv ?place .
}
where {
  # match company by ticker
  ?company a dbo:Company ; dbp:symbol "<<ticker>>"@en .

  ?company ?cpred ?cobj .
      filter(isLiteral(?cobj) && (lang(?cobj)="en" || lang(?cobj)="") && (strStarts(str(?cpred), "http://dbpedia.org/ontology/") || strStarts(str(?cpred), "http://www.w3.org/2000/01/rdf-schema#label") ))
#related people
optional {
         { ?company ?relToPerson ?person  . filter(strStarts(str(?relToPerson), "http://dbpedia.org/ontology/") && ?relToPerson != dbo:wikiPageWikiLink) }
          union
         { ?person ?relToPersonInv ?company .  filter(strStarts(str(?relToPersonInv), "http://dbpedia.org/ontology/") && ?relToPersonInv != dbo:wikiPageWikiLink) }

         ?person a dbo:Person ;
                       rdfs:label ?pobj .
        filter(lang(?pobj)="en" || lang(?pobj)="")
  }

#related places
optional {
        {  ?company ?relToPlace ?place  . filter(strStarts(str(?relToPlace), "http://dbpedia.org/ontology/") && ?relToPlace != dbo:wikiPageWikiLink) }
         union
        { ?place ?relToPlaceInv ?company . filter(strStarts(str(?relToPlaceInv), "http://dbpedia.org/ontology/") && ?relToPlaceInv != dbo:wikiPageWikiLink) }

         ?place a dbo:Place ;
                       rdfs:label ?plobj .
         filter(lang(?plobj)="en" || lang(?plobj)="")

  }
}

' as sparql,
'http://dbpedia.org/sparql?format=text/plain&query=' as endpoint

match (o:Organization) where o.ticker is not null

CALL n10s.rdf.import.fetch(
  endpoint + apoc.text.urlencode(replace(sparql,"<<ticker>>", o.ticker)),
  'Turtle'
) yield terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo
return o.ticker, terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo
