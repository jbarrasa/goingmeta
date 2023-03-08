// Create constraint (required to import RDF with n10s)
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE (r.uri) IS UNIQUE ;

// Graph config (also required to import RDF with n10s)
CALL n10s.graphconfig.init({ handleVocabUris : "MAP"}) ;

// Import the taxonomy of infectious diseases (wd:Q18123741) in Wikidata
// the SPARQL query returns the disease nodes and the cross references to
// the disease ontology and MeSH when available

WITH '
PREFIX neo: <neo://voc#>
construct {
  ?dis a neo:WD_Disease ;
     neo:label ?disName ;
     neo:HAS_PARENT ?parentDisease ;
     neo:SAME_AS ?meshUri ;
     neo:SAME_AS ?diseaseOntoUri .
}
where {
  ?dis wdt:P31/wdt:P279* wd:Q18123741 ;
       rdfs:label ?disName . filter(lang(?disName) = "en")

  optional { ?dis wdt:P279 ?parentDisease .
             ?parentDisease wdt:P31/wdt:P279* wd:Q18123741 }
  optional { ?dis wdt:P486 ?meshCode . bind(URI(concat("http://id.nlm.nih.gov/mesh/",?meshCode))  as ?meshUri) }
  optional { ?dis wdt:P699 ?diseaseOntoId .  bind(URI(concat("http://purl.obolibrary.org/obo/",REPLACE(?diseaseOntoId, ":", "_")))  as ?diseaseOntoUri) }
}
'
AS query
CALL n10s.rdf.import.fetch(
  "https://query.wikidata.org/sparql?query=" + apoc.text.urlencode(query),
  "N-Triples",
  { headerParams: { Accept: "text/plain"}})
YIELD terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo
RETURN terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo


// Explore the Wikidata taxonomy: anaerobic cellulitis

MATCH taxonomy = (v:WD_Disease)-[:HAS_PARENT*]->(root)
WHERE v.label =  "anaerobic cellulitis"
     AND NOT (root)-[:HAS_PARENT]->()
RETURN taxonomy

// You can use the same query to create a search phrase in Bloom
// just set the disease name as a parameter

MATCH taxonomy = (v:WD_Disease)-[:HAS_PARENT*]->(root)
WHERE v.label =  $disease_name
     AND NOT (root)-[:HAS_PARENT]->()
RETURN taxonomy



// There are shortcuts in the data, you can find them with this simple cypher
// pattern

MATCH shortcutPattern = (v:WD_Disease)<-[co:HAS_PARENT*2..]-(child)-[shortcut:HAS_PARENT]->(v)
return shortcutPattern limit 2


// And you might as well remove them as they create noise for our analysis

MATCH (v:WD_Disease)<-[co:HAS_PARENT*2..]-(child)-[shortcut:HAS_PARENT]->(v) DELETE shortcut


// Import the second taxonomy of infectious diseases (mesh:D007239) from
// the MeSH SPARQL endpoint

WITH '
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
PREFIX mesh: <http://id.nlm.nih.gov/mesh/>
PREFIX neo: <neo://voc#>

CONSTRUCT {
?s a neo:Mesh_Disease;
     neo:label ?name ;
     neo:HAS_PARENT ?parentDescriptor .
}
FROM <http://id.nlm.nih.gov/mesh>
WHERE {
  {
    ?s meshv:broaderDescriptor* mesh:D007239
  }

  ?s rdfs:label ?name .

  optional {
    ?s meshv:broaderDescriptor ?parentDescriptor .
  }

}

' AS query
CALL n10s.rdf.import.fetch(
  "https://id.nlm.nih.gov/mesh/sparql?format=TURTLE&query=" + apoc.text.urlencode(query),
  "Turtle")
YIELD terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo
RETURN terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo


// Again, let's delete the shortcuts like we did for the Wikidata taxonomy

MATCH (v:Mesh_Disease)<-[co:HAS_PARENT*2..]-(child)-[shortcut:HAS_PARENT]->(v)
DELETE shortcut


// You can now compare Wikidata and MeSH side by side

MATCH taxonomy = (v:WD_Disease)-[:HAS_PARENT*]->(root)
WHERE v.label =  "anaerobic cellulitis"
     AND NOT (root)-[:HAS_PARENT]->()
unwind  nodes(taxonomy) as node
match mesh_twin = (node)-[:SAME_AS*0..1]->(:Mesh_Disease)-[:HAS_PARENT*0..]->(mesh_root:Mesh_Disease) where NOT (mesh_root)-[:HAS_PARENT]->()
return taxonomy, mesh_twin

// We will load the disease ontology in a different way because we have it as a file
// and no SPARQL access to it.

// We define mappings for the ontology: classes will be labeled as DO_Disease and
// the rdfs:subClassOf relationships will be persisted as HAS_PARENT
// This will make the taxonomy consistent with the other two

call n10s.nsprefixes.add("rdfs","http://www.w3.org/2000/01/rdf-schema#");
call n10s.mapping.add("http://www.w3.org/2000/01/rdf-schema#subClassOf","HAS_PARENT");
call n10s.nsprefixes.add("owl","http://www.w3.org/2002/07/owl#");
call n10s.mapping.add("http://www.w3.org/2002/07/owl#Class","DO_Disease");



// Now we can load the disease ontology but we want to filter the elements we don't care about
// we use n10s.rdf.stream to collect only the owl:Class definitions
// and then for those we just keep the rdf:type, the rdfs:label,
// the rdfs:subClassOf and the cross references :hasDbXref
// when you import with n10s.rdf.import.inline the mappings will be applied

call n10s.rdf.stream.fetch("http://purl.obolibrary.org/obo/doid.owl","RDF/XML", { limit : 999999}) yield subject, predicate, object
where predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" and object = "http://www.w3.org/2002/07/owl#Class"
with collect(subject) as class_uris
call n10s.rdf.stream.fetch("http://purl.obolibrary.org/obo/doid.owl","RDF/XML", { limit : 999999}) yield subject, predicate, object, isLiteral, literalType, literalLang, subjectSPO
where subject in class_uris and
      ( predicate in ["http://www.w3.org/1999/02/22-rdf-syntax-ns#type", "http://www.w3.org/2000/01/rdf-schema#label"]
       or
       predicate = "http://www.w3.org/2000/01/rdf-schema#subClassOf" and n10s.rdf.isIRI (object)
       or
       predicate = "http://www.geneontology.org/formats/oboInOwl#hasDbXref" and object starts with "MESH:" )

with n10s.rdf.collect.nt(subject, predicate, object, isLiteral, literalType, literalLang, subjectSPO) as taxonomy
call n10s.rdf.import.inline(taxonomy, "N-Triples") yield terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo, callParams
return terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo, callParams


// You want to transform the cross references stored as node properties into SAME_AS relationships
// again, we want to achieve consistency with the previous taxonomies.

match (doe:DO_Disease) where doe.hasDbXref is not null
merge (mesh:Resource { uri: "http://id.nlm.nih.gov/mesh/" + substring(doe.hasDbXref,5)})
merge (doe)-[:SAME_AS]->(mesh)
remove doe.hasDbXref



// Let's explore the taxonomies. Look for Toxoplasmosis in MeSH

match tox = (md:Mesh_Disease)-[:SAME_AS]-() where md.label = "Toxoplasmosis" return tox



// You can also run pairwise comparison to find patterns
// Pattern 1: Different granularities

MATCH topLink = (topDo:DO_Disease)-[:SAME_AS]-(topMesh:Mesh_Disease)
MATCH bottomLink = (bottomDo:DO_Disease)-[:SAME_AS]-(bottomMesh:Mesh_Disease)
MATCH txnDo = (topDo)<-[:HAS_PARENT*]-(bottomDo)
MATCH txnMesh = (topMesh)<-[:HAS_PARENT*]-(bottomMesh)
WHERE length(txnDo) <> length(txnMesh)
RETURN * limit 1



// Pattern 2: Generalisations. Multiple categories in a taxonomy matched to the
// same category in another taxonomy

MATCH multiXRef = (md1:DO_Disease)-[:SAME_AS]-(start:Mesh_Disease)-[:SAME_AS]-(md2:DO_Disease)
OPTIONAL MATCH link = (md1)-[r:HAS_PARENT*]->(md2)
RETURN multiXRef, link


MATCH multiXRef = (md1:WD_Disease)-[:SAME_AS]-(start:Mesh_Disease)-[:SAME_AS]-(md2:WD_Disease)
OPTIONAL MATCH link = (md1)-[r:HAS_PARENT*]->(md2)
RETURN multiXRef, link


// Pattern 3: Triangles! A triangle is a perfect match across all three taxonomies

MATCH triangle = (wdid:WD_Disease)-[:SAME_AS]-(do:DO_Disease)-[:SAME_AS]-(md:Mesh_Disease)-[:SAME_AS]-(wdid)
WHERE size([path = (wdid)-[:SAME_AS]-() | path ]) = size([ path = (do)-[:SAME_AS]-()| path ]) = size([path = (md)-[:SAME_AS]-() | path ]) = 2
RETURN triangle limit 50

// Taxonomy harmonisation: When you find an incomplete triangle with one leg missing
// you can infer that missing link.
// Use this to generate fixes to enrich the incomplete ontologies
// Here we can generate triples to add to wikidata

MATCH incomplete = (wdid:WD_Disease)-[:SAME_AS]-(do:DO_Disease)-[:SAME_AS]-(md:Mesh_Disease)
WHERE NOT (md)-[:SAME_AS]-(wdid)
      AND size([path = (wdid)-[:SAME_AS]-() | path]) = size([path = (md)-[:SAME_AS]-() | path ]) = 1
      AND size([path = (do)-[:SAME_AS]-() | path ]) = 2
RETURN wdid.uri as subject, "http://www.wikidata.org/prop/direct/P486" as predicate, n10s.rdf.getIRILocalName(md.uri) as object;
