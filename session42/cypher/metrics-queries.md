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
WITH c.uri as c, size([(c)<-[:rdfs__domain]-(dtp:owl__DatatypeProperty) | dtp]) as p_count, size([(c)<-[:rdfs__domain]-(op:owl__ObjectProperty) | op]) as r_count
with c , p_count, r_count, 
CASE p_count + r_count
  WHEN 0 THEN 0
  ELSE p_count * 100 / (p_count + r_count)
END  as local_pr_onto
return avg(local_pr_onto) as PR_Onto
```
