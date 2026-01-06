### ANOnto

Annotation Richness (ANOnto): Mean number of annotation properties (label and comments) per class. 

```cypher
MATCH (c:owl__Class)
WITH count(c) as c_count
MATCH (c:owl__Class) where c.rdfs__comment is not null or c.rdfs__label is not null
RETURN c_count, count(c) as ac_count, count(c) * 100 /c_count as AN_Onto
```

