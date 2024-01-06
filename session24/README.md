## Session 24 outline:

- The flow of the session is driven from the [Python notebook](https://github.com/jbarrasa/goingmeta/blob/main/session24/python_notebooks/Ontology_Driven_RAG_patterns.ipynb).
  - Populate the graph
  - Run test vector searches
  - Run RAG chains 
- Create an ontology in your tool of choice (I used Protégé in the session) extending the RAG patterns ontology (http://www.nsmntx.org/2024/01/rag).
  - If you prefer, you can use [the one I created in the session](https://github.com/jbarrasa/goingmeta/blob/main/session24/gm24-onto-legislation.ttl).  
- Load the onto into Neo4j using neosemantics.
  ```
  call n10s.onto.import.fetch("https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session24/gm24-onto-legislation.ttl","Turtle")
  ```
  - **NOTE:** Make sure you do it before testing the dynamic generation of cypher code. It's marked in the notebook with a comment *(LOAD THE ONTOLOGY...*
