| Test Name | SPARQL Query |
|-----------|--------------|
| **All Jaguars** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK {
{ SELECT (COUNT(DISTINCT ?needle) AS ?c) WHERE {
    VALUES ?needle {
        "el jefe" "macho b" "sombra" "oko" "cochise" 
        "kudam" "mariposa" "xam" "isa" "fera" "amanaci" 
        "ben" "f11" "pixana" "levantina"  "mariua" 
    }
    ?u a onto:Jaguar ; rdfs:label ?n .
    FILTER(CONTAINS(LCASE(STR(?n)), ?needle))
} }
FILTER(?c = 16)
}
``` |
| **Jefe-props** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK 
{ ?jefe a onto:Jaguar ; rdfs:label ?jname ; onto:hasGender "Male" ; 
      onto:hasLastSightingDate "2021-11-27"^^xsd:date; 
      onto:hasMonitoringStartDate "2011-11-19"^^xsd:date .
  FILTER CONTAINS(LCASE(STR(?jname)), "el jefe")            
}
``` |
| **Jefe-obS** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK 
{ ?jefe a onto:Jaguar ; rdfs:label ?jname .  
  FILTER CONTAINS(LCASE(STR(?jname)), "el jefe") .
  ?jefe onto:hasObservation [ a onto:Observation; 
                              onto:observedDate "2011-11-19"^^xsd:date ; 
                              onto:observedBy [ rdfs:label ?df ] ] ;
         onto:hasObservation [ a onto:Observation; 
                              onto:observedDate "2021-11-27"^^xsd:date ; 
                              onto:observedBy [ rdfs:label ?pf ] ] .
  FILTER CONTAINS(LCASE(STR(?df)), "donnie fenn") .
  FILTER CONTAINS(LCASE(STR(?pf)), "profauna") .
}
``` |
| **Jefe-monitoring** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK 
{ ?jefe a onto:Jaguar ; rdfs:label ?jname .  
  FILTER CONTAINS(LCASE(STR(?jname)), "el jefe") .        
  ?jefe onto:monitoredByOrg [ rdfs:label ?orgName1 ; a onto:NGO ] ; 
         onto:monitoredByOrg [ rdfs:label ?orgName2 ; a onto:GovernmentAgency ] ; 
         onto:monitoredByOrg [ rdfs:label ?orgName3 ; a onto:AcademicInstitution ] . 
  FILTER CONTAINS(LCASE(STR(?orgName1)), "conservation catalyst") .
  FILTER CONTAINS(LCASE(STR(?orgName2)), "arizona game and fish department") .
  FILTER CONTAINS(LCASE(STR(?orgName3)), "university of arizona") .
}
``` |
| **Jefe-named** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK 
{ ?jefe a onto:Jaguar ; rdfs:label ?jname .  
  FILTER CONTAINS(LCASE(STR(?jname)), "el jefe") .        
  ?jefe onto:namedBy [ a onto:Person; rdfs:label ?pers ] .                 
  FILTER (CONTAINS(LCASE(STR(?pers)), "felizardo valencia") 
          && CONTAINS(LCASE(STR(?pers)), "students"))
}
``` |
| **Llanos region found** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK { 
  ?l a onto:Region ; rdfs:label ?lname . 
  FILTER CONTAINS(LCASE(STR(?lname)), "llanos")
} 
``` |
| **Llanos region linked to jaguar** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK { 
  ?l a onto:Region ; rdfs:label ?lname . 
  FILTER CONTAINS(LCASE(STR(?lname)), "llanos") .
  [] onto:occursIn ?l ; rdfs:label ?jname . 
  FILTER CONTAINS(LCASE(STR(?jname)), "mariposa")
} 
``` |
| **Llanos region linked to country** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK { 
  ?l a onto:Region ; rdfs:label ?lname . 
  FILTER CONTAINS(LCASE(STR(?lname)), "llanos") .
  ?l onto:locatedInCountry ?c . 
  ?c rdfs:label ?cname . 
  FILTER CONTAINS(LCASE(STR(?cname)), "colombia")
} 
``` |
| **Mariposa** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK 
{ [] a onto:Jaguar ; rdfs:label ?jname ; onto:hasGender "Female" .                
  FILTER CONTAINS(LCASE(STR(?jname)), "mariposa")
}
``` |
| **Mariposa-Cayenita** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK 
{ ?m a onto:Jaguar ; rdfs:label ?jname ; onto:occursIn ?p .
  FILTER CONTAINS(LCASE(STR(?jname)), "mariposa") .
  ?m onto:hasOffspring [ a onto:Jaguar; rdfs:label ?oname ; onto:occursIn ?p ] .           
  FILTER CONTAINS(LCASE(STR(?oname)), "cayenita") .
}
``` |
| **offspring count** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK {
    {
        SELECT ?m (COUNT(?off) AS ?count)
        WHERE { 
            ?m a onto:Jaguar ; rdfs:label ?jname ; onto:hasOffspring ?off .
            FILTER CONTAINS(LCASE(STR(?jname)), "f11-9") .
        }
        GROUP BY ?m
        HAVING (COUNT(?off) = 3)
    }
}
``` |
| **observation count** |
```sparql
PREFIX onto: <http://example.org/ontology#>
ASK {
    {
        SELECT (COUNT(?o) AS ?count)
        WHERE { 
            ?o a onto:Observation .
        }
        HAVING (COUNT(?o) >= 5)
    }
}
``` |
