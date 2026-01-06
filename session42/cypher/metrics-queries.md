### CCC

Class Connectivity Coverage (CCC): Fraction of classes that participate in at least one object property (as domain or range) 


```cypher
MATCH (c:owl__Class)
with c.uri as c, 
     size([(c)-[:rdfs__domain|rdfs__range*2]-(connected) | connected]) as connected_count,
     size([(c)-[:rdfs__subClassOf*0..]->()-[:rdfs__domain|rdfs__range*2]-(connected) | connected]) as connected_count_extended
return avg(ancestor_count + related_count) as CCC, 
       avg(ancestor_count + related_count_extended) as CCC_ext
```

### ANOnto

Annotation Richness (ANOnto): Mean number of annotation properties (label and comments) per class. 

```cypher
MATCH (c:owl__Class)
WITH count(c) as c_count
MATCH (c:owl__Class) where c.rdfs__comment is not null or c.rdfs__label is not null
RETURN c_count, count(c) as ac_count, count(c) * 100 /c_count as AN_Onto
```

### PROnto

Properties Richness (PROnto): Number of properties defined in the ontology divided by the
number of relationships and properties. 

```cypher
MATCH (p:owl__DatatypeProperty)
WITH count(p) as p_count
MATCH (r:owl__ObjectProperty) 
RETURN p_count, count(r) as r_count, count(r) * 100 /(count(r) + p_count) as PR_Onto
```

JB's variant (class centric)
```cypher
MATCH (c:owl__Class) 
WITH c.uri as c, size([(c)<-[:rdfs__domain]-(dtp:owl__DatatypeProperty) | dtp]) as p_count,
     size([(c)<-[:rdfs__domain]-(op:owl__ObjectProperty) | op]) as r_count
with c , p_count, r_count, 
CASE p_count + r_count
  WHEN 0 THEN 0
  ELSE p_count * 100 / (p_count + r_count)
END  as local_pr_onto
return avg(local_pr_onto) as PR_Onto
```


### LCOMOnto

Lack of Cohesion in Methods (LCOMOnto): Mean lenght of all paht from leaf classes to Thing.

```cypher
MATCH path = (leaf:owl__Class)-[:rdfs__subClassOf*0..]->(top)
where not ()-[:rdfs__subClassOf]->(leaf) and not (top)-[:rdfs__subClassOf]->()
with length(path) + 1 as path_length
return sum(path_length), count(*), sum(path_length)/count(*) as LCOMOnto
```


### CBOOnto

Coupling between Objects (CBOOnto): Number of related classes

```
MATCH (c:owl__Class)
with c.uri as c, 
     size([(c)-[:rdfs__subClassOf]->(parent) | parent]) as ancestor_count
return avg(ancestor_count) as CBOOnto
```

```cypher
MATCH (c:owl__Class)
with c.uri as c, size([(c)-[:rdfs__subClassOf]->(parent) | parent]) as ancestor_count
with c, 
     CASE ancestor_count
      WHEN 0 THEN 1
      ELSE ancestor_count
     END  as ancestor_count         
return avg(ancestor_count) as CBOOnto
```

JB's variant (including non-taxonomic relations)
```cypher
MATCH (c:owl__Class)
with c.uri as c, 
     size([(c)-[:rdfs__subClassOf]->(parent) | parent]) as ancestor_count, 
     size([(c)-[:rdfs__domain|rdfs__range*2]-(related) | related]) as related_count,
     size([(c)-[:rdfs__subClassOf*0..]->()-[:rdfs__domain|rdfs__range*2]-(related) | related]) as related_count_extended
return avg(ancestor_count) as CBOOnto,
       avg(ancestor_count + related_count) as CBOOnto_1, 
       avg(ancestor_count + related_count_extended) as CBOOnto_2
```
