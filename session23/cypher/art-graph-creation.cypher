//load text attributes of artworks
call apoc.load.json("https://github.com/jbarrasa/goingmeta/raw/main/session23/data/collection_extra_info.json") yield value
with value where value.display_caption is not null
create (a:Artwork)
    set a.url = value.url,
        a.display_caption = value.display_caption,
        a.catalogue_entry = value.catalogue_entry,
        a.subjects = value.subjects ;

//load rest of attributes for artworks
load csv with headers from "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session23/data/the-tate-collection.csv" as row fieldterminator ";"
match (a:Artwork { url: row.url }) set a+= row ;

//refactor subjects as separate nodes
match (a:Artwork) unwind a.subjects as subj
merge (s:Subject { name: subj})
merge (a)-[:has_subject]->(s)
remove a.subjects ;

//refactor artists as separate nodes
match (a:Artwork)
merge (ar:Artist { aid: a.artistId}) on create set ar.name = a.artist
merge (a)-[:created_by]->(ar) ;


//load soft taxonomy for subjects
load csv with headers from "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session23/data/soft_taxonomy.csv" as row
match (parent:Subject { name: row.parent_subject })
match (child:Subject { name: row.child_subject })
merge (child)-[:broader]->(parent) ;
