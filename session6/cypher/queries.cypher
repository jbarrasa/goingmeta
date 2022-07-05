load the data

CREATE INDEX ON :Author(name);
CREATE INDEX ON :Book(id);
CREATE INDEX ON :Genre(name);



LOAD CSV WITH HEADERS FROM "https://raw.githubusercontent.com/jbarrasa/datasets/master/goodreads/booklist.csv" AS row
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



MATCH (n:Book)
WITH id(n) AS bookid, size((n)-[:HAS_GENRE]->()) AS genreCount
RETURN AVG(genreCount) AS avgNumGenres, MAX(genreCount) AS maxNumGenres, MIN(genreCount) AS minNumGenres



CALL gds.graph.project(
    'bookSimGraph',
    ['Book', 'Genre'],
    {
        genre: {
            type: 'HAS_GENRE'
        }
    }
);


CALL gds.nodeSimilarity.stream('bookSimGraph')
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).name AS Genre1, gds.util.asNode(node2).name AS Genre2, similarity
ORDER BY similarity DESCENDING, Genre1, Genre2


CALL gds.graph.project(
    'genreSimGraph',
    ['Book', 'Genre'],
    {
        genre: {
            type: 'HAS_GENRE' , orientation: 'REVERSE'
        }
    }
);

!3
