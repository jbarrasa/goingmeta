//Create one database per version and one composite to query across all of them

create database ontov0;
:use ontov0;
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
call n10s.graphconfig.init({handleMultival: "ARRAY", multivalPropList : ['http://www.w3.org/2000/01/rdf-schema#label','http://www.w3.org/2000/01/rdf-schema#comment'], keepLangTag: true});

create database ontov1;
:use ontov1;
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
call n10s.graphconfig.init({handleMultival: "ARRAY", multivalPropList : ['http://www.w3.org/2000/01/rdf-schema#label','http://www.w3.org/2000/01/rdf-schema#comment'], keepLangTag: true});

create database ontov2;
:use ontov2;
CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
call n10s.graphconfig.init({handleMultival: "ARRAY", multivalPropList : ['http://www.w3.org/2000/01/rdf-schema#label','http://www.w3.org/2000/01/rdf-schema#comment'], keepLangTag: true});


CREATE COMPOSITE DATABASE ontos;
CREATE ALIAS ontos.v0 FOR DATABASE ontov0;
CREATE ALIAS ontos.v1 FOR DATABASE ontov1;
CREATE ALIAS ontos.v2 FOR DATABASE ontov2;

SHOW DATABASES;

// Import the data in the different DBs using the Pypthon notebook in the session19 folder

// Compute the delta between versions 0 and 1
:use ontos
  
call{ 
    use ontos.v0
    match (c0:owl__Class)
    return collect(c0.uri) as v0_class_uris
} with v0_class_uris
call{ 
    use ontos.v1
    match (c1:owl__Class)
    return collect(c1.uri) as v1_class_uris
}
unwind [x in v1_class_uris where not x in v0_class_uris ] as new_class
return new_class

