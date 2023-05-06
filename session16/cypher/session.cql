//Initialise graph for RDF import
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

call n10s.graphconfig.init({ handleVocabUris: "IGNORE"});


//Import a simple taxonomy (Ontology generated with Protégé)
call n10s.onto.import.fetch("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session16/taxonomies/vw.ttl","Turtle")

// Compute the different similiarity metrics for two "sibling" categories
match (a:Class { name : "Electric"}), (b:Class { name: "Tiguan"})
return n10s.sim.pathsim.value(a,b) as path, 
n10s.sim.lchsim.value(a,b) as lch, 
n10s.sim.wupsim.value(a,b) as wup

// We can also get the path view for the two categories
match (a:Class { name : "Golf"}), (b:Class { name: "Tiguan"})
return n10s.sim.pathsim.path(a,b) 

// We explored what happens when you compare categories higher up / lower down in the 
// taxonomy and how the different metrics behave in these cases

match (a:Class { name: "Convertible"}), (b:Class { name: "SUV"})
return n10s.sim.lchsim.value(a,b)


// Extending the taxonomy in a way that modifies its overall depth has an impact in the
// Leacock-Chodorow metric. You can add an extra class to the taxonomy with this snippet
call n10s.onto.import.inline('
    @prefix : <http://localhost/ontologies/2019/1/10/automobile#> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    :TiguanSpecial rdf:type owl:Class ;
            rdfs:subClassOf :Tiguan ;
            rdfs:label "Tiguan Special" .
',"Turtle")


// We completed the exercise by trying the same thing with a larger taxonomy
// the one about software concepts extracted from Wikidata that we used in 
// Episode#2

// first we empty the graph
match (n:Resource) detach delete n

// and we load the new taxonomy
call n10s.skos.import.fetch("https://github.com/jbarrasa/goingmeta/raw/main/session2/resources/goingmeta-skos.ttl","Turtle")

// Look up items by "name" (wikidata identifier) to compare Neo4j (wikidata name: Q1628290) and MongoDB (wikidata name: Q1165204)
match (a:Class { name : "Q1628290"}), (b:Class { name: "Q1165204"})
return n10s.sim.pathsim.path(a,b) as path

// or lookup by prefLabel (human friendly name)
match (neo:Class) where neo.prefLabel contains "Neo4j" 
match (mdb:Class) where mdb.prefLabel contains "Mongo"
return n10s.sim.pathsim.value(neo,mdb) as path,
n10s.sim.lchsim.value(neo,mdb) as lch,
n10s.sim.wupsim.value(neo,mdb) as wup

// and Neo4j vs Java 
match (neo:Class) where neo.prefLabel contains "Neo4j" 
match (j:Class) where j.prefLabel = "Java"
return n10s.sim.pathsim.value(neo,j) as path,
n10s.sim.lchsim.value(neo,j) as lch,
n10s.sim.wupsim.value(neo,j) as wup
