CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

call n10s.graphconfig.init({handleVocabUris:"IGNORE"});

unwind ['https://raw.githubusercontent.com/jbarrasa/datasets/refs/heads/master/ontos/gmtest/football.ttl',
'https://raw.githubusercontent.com/jbarrasa/datasets/refs/heads/master/ontos/gmtest/books.ttl',
'https://raw.githubusercontent.com/jbarrasa/datasets/refs/heads/master/ontos/gmtest/art.ttl'] as url
call n10s.onto.import.fetch(url,'Turtle') yield terminationStatus,triplesLoaded,triplesParsed, extraInfo, callParams
return *


unwind ['https://raw.githubusercontent.com/jbarrasa/datasets/refs/heads/master/ontos/gmtest/football.ttl',
'https://raw.githubusercontent.com/jbarrasa/datasets/refs/heads/master/ontos/gmtest/books.ttl',
'https://raw.githubusercontent.com/jbarrasa/datasets/refs/heads/master/ontos/gmtest/art.ttl'] as url
call n10s.rdf.stream.fetch(url,'Turtle') yield subject, predicate, object
where predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"	and 
      (object = "http://www.w3.org/2002/07/owl#Class" or object = "http://www.w3.org/2002/07/owl#ObjectProperty")
with distinct url, subject
match (r:Resource { uri: subject })
set r.prov = url ;



MATCH (r:Resource)
WHERE r.label IS NOT NULL 
WITH r, r.label || ' ' || coalesce(r.comment, '') as label_and_desc
WITH r, genai.vector.encode(label_and_desc, 'OpenAI', { token: $token }) AS propertyVector
CALL db.create.setNodeVectorProperty(r, 'embedding', propertyVector)
RETURN r.embedding AS embedding





CREATE VECTOR INDEX `label_and_desc`
FOR (n:Resource) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}

with {
  categories: [
    "Person",
    "Equipe",
    "Company"
  ],
  relationshipTypes: [
    {
      name: "works at",
      fromCat: "Person",
      to: "Company"
    },
    {
      name: "collaborates with",
      fromCat: "Person",
      to: "Person"
    }
  ]
} as rough_sch
unwind rough_sch.categories as cat
call db.index.vector.queryNodes("label_and_desc", 3, genai.vector.encode(cat, 'OpenAI', { token: $token })) yield node, score
where score > 0.92
with rough_sch.categories as lookup_cats, collect({cat: cat, matching_uri: node.uri, score: score, prov: node.prov }) as results
return lookup_cats, results,  size(results) * 1.0 / size(lookup_cats) as coverage


