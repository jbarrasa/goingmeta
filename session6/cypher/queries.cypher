// indexes
CREATE INDEX ON :Author(name);
CREATE INDEX ON :Book(id);
CREATE INDEX ON :Genre(name);


// import from csv
LOAD CSV WITH HEADERS FROM "https://github.com/jbarrasa/goingmeta/raw/main/session6/data/books-2000.csv" AS row
MERGE (b:Book { id : row.itemUrl})
SET b.description = row.description, b.title = row.itemTitle
WITH b, row
UNWIND split(row.genres,';') AS genre
MERGE (g:Genre { name: substring(genre,8)})
MERGE (b)-[:HAS_GENRE]->(g)
WITH b, row
UNWIND split(row.author,';') AS author
MERGE (a:Author { name: author})
MERGE (b)-[:HAS_AUTHOR]->(a)


// profile the dataset (books-genres)
MATCH (n:Book)
WITH id(n) AS bookid, size((n)-[:HAS_GENRE]->()) AS genreCount
RETURN AVG(genreCount) AS avgNumGenres, MAX(genreCount) AS maxNumGenres, MIN(genreCount) AS minNumGenres


// approach 1: node similarity algo

// create projection
CALL gds.graph.project(
    'genreSimGraph',
    ['Book', 'Genre'],
    {
        genre: {
            type: 'HAS_GENRE' , orientation: 'REVERSE'
        }
    }
);


// run algo
CALL gds.nodeSimilarity.stream('genreSimGraph')
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).name AS Genre1, gds.util.asNode(node2).name AS Genre2, similarity
ORDER BY similarity DESCENDING, Genre1, Genre2

// materialise the similarities found as relationships
match (g1:Genre { name: "money"}), (g2:Genre { name: "entrepreneurship"})
merge (g1)-[:similar_to]-(g2)

// approach 2: overlap (Barrasa Algo)

// compute (directional) coocurence score
match (g1:Genre)<-[:HAS_GENRE]-(:Book)-[:HAS_GENRE]->(g2:Genre)
with distinct g1,g2 where id(g1)<id(g2)
with g1,g2, size((g1)<-[:HAS_GENRE]-()) as degree1, size((g2)<-[:HAS_GENRE]-()) as degree2, size((g1)<-[:HAS_GENRE]-()-[:HAS_GENRE]->(g2)) as overlap
merge (g1)-[:COOC { score: overlap * 1.0 / degree1 }]->(g2)
merge (g2)-[:COOC { score: overlap * 1.0 / degree2 }]->(g1)


// equivalent genres
MATCH (g1:Genre)-[:COOC { score: 1 }]->(g2:Genre)-[:COOC { score: 1 }]->(g1)
return g1.name, g2.name limit 10

// subgenres?
match (g1:Genre)-[:COOC { score: 1 }]->(g2:Genre)-[c:COOC]->(g1)
where c.score < 1
return g1.name, g2.name , c.score as sc order by sc desc limit 100

// let's materialize them with narrower_than relationships
match (g1:Genre)-[:COOC { score: 1 }]->(g2:Genre)-[c:COOC]->(g1)
where c.score < 1
merge (g1)-[:narrower_than]->(g2)

// remove shortcuts
MATCH (g1)-[:narrower_than*2..]->(g3),
      (g1)-[d:narrower_than]->(g3)
DELETE d


// explore classification scheme (taxonomies of depth 3)
MATCH taxonomy = (:Genre)-[:narrower_than*3..]->()
return taxonomy limit 3
