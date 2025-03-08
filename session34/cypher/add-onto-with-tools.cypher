#ADDS a BASIC ONTOLOGY ANNOTATED WITH Tool Definitions

create (aw:Class { name: "Artwork"})
create (a:Class { name: "Artist"})
create (s:Class { name: "Subject"})
create (aw)-[:has_subject]->(s)
create (aw)-[:created_by]->(a)
create (s)-[:broader]->(s) ;

with {
    tools: [
      {
        name: "get_artist_works",
        description: "Retrieve all artwork titles for a given artist_name.",
        cypher_query: "MATCH (a:Artist {name: $input})<-[:created_by]-(aw:Artwork) RETURN aw.title as artwork_title, aw.dateText as creation_date",
        for_class: "Artwork"
      },
      {
        name: "get_artist_by_subject",
        description: "Retrieve artist that most frequently use a topic in their work.",
        cypher_query: "MATCH (a:Artist)<-[:created_by]-(aw:Artwork)-[:has_subject]->(:Subject { name: $input } ) RETURN a.name as artist_name , count(aw) as number_of_artworks order by count(aw) desc limit 5",
        for_class: "Artist"
      }
    ]
  } as defs
unwind defs.tools as t
merge (tool:Tool { name: t.name , description: t.description, cypher_query: t.cypher_query })
with tool, t.for_class as clref
match (c:Class { name: clref })
merge (tool)-[:for_class]->(c)



