// extract an onto
:GET /rdf/<your_DB>/onto

// edit it manually or with ontology editor and annotate entities

//pick a namespace
@prefix talk: <http://www.neo4j.org/2022/07/talkable#> .

// ...and give classes a talk:name

mv:Movie a owl:Class;
  rdfs:label "Movie" ;
  talk:name "title" .
  

// ... relationships a talk:direct and talk:inverse (also use language tags to indicate style)

mv:ACTED_IN rdf:type owl:ObjectProperty ;
        rdfs:domain <neo4j://graph.schema#Person> ;
        rdfs:range <neo4j://graph.schema#Movie> ;
        talk:direct "acted in"@default ,
                    "is in"@short ,
                    "is in the cast of"@long ;
        talk:inverse "has in it"@default ,
                     "includes"@short ,
                     "includes in the cast"@long ;
        rdfs:label "ACTED_IN" .

// ... properties a talk:direct 


// The usual config to import RDF 

CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

call n10s.graphconfig.init({ handleVocabUris: "IGNORE" , keepLangTag: true , handleMultival: "ARRAY"});


// Import the annotated ontology (fetch or inline)

call n10s.rdf.import.inline('','Turtle');


// have a look at the onto and see how patterns are stored with their style tag

match onto = (:Class)--()
return onto
                            
                            
// Query onto and data to generate NL

step 1

// select rel direction

match (n)-[r]-(o) where id(n) = 17
match (cn:Class)<-[:domain|range]-(op:ObjectProperty)-[:domain|range]->(co:Class)
where type(r) in op.label  // a relationship definition
      and (exists(op.direct) or exists(op.inverse))   // annotated
      and  cn.label[0] in labels(n)
      and co.label[0] in labels(o)
return n[cn.name[0]] as subj ,
     op[case when startNode(r) = n then "direct" else "inverse" end] as pred ,
     o[co.name[0]] as obj

//step 2: select speech style

match (n)-[r]-(o) where id(n) = 17
match (cn:Class)<-[:domain|range]-(op:ObjectProperty)-[:domain|range]->(co:Class)
where type(r) in op.label  // a relationship definition
      and (exists(op.direct) or exists(op.inverse))   // annotated
      and  cn.label[0] in labels(n)
      and co.label[0] in labels(o)
return n[cn.name[0]] as subj ,
     n10s.rdf.getLangValue("default" ,op[case when startNode(r) = n then "direct" else "inverse" end]) as pred ,
     o[co.name[0]] as obj


step 3

match (n)-[r]-(o) where id(n) = 17
match (cn:Class)<-[:domain|range]-(op:ObjectProperty)-[:domain|range]->(co:Class)
where type(r) in op.label  // a relationship definition
      and (exists(op.direct) or exists(op.inverse))   // annotated
      and  cn.label[0] in labels(n)
      and co.label[0] in labels(o)
with n[cn.name[0]] as subj ,
     n10s.rdf.getLangValue("default" ,op[case when startNode(r) = n then "direct" else "inverse" end]) as pred ,
     o[co.name[0]] as obj
// aggregation and some formatting     
with  subj ,
      case when pred contains '$' then replace(pred,'$',toString(obj)) else pred end  as pred,
      substring(reduce(r="",x in collect(case when pred contains '$' then '' else toString(obj) end)| r + ", " + x),2) as obj
return subj + " " + pred + " " + obj  as sentence

