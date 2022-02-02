
1. Download the catalog from the [British Library downloads page](https://www.bl.uk/collection-metadata/downloads) and unzip. I selected the British National Bibliography (BNB) Books LOD in NT format. 
2. Install n10s in your neo4j installation: You can do it in a couple of clicks from the neo4j desktop (plugins section of your DB) 

    <img src="https://raw.githubusercontent.com/neo4j-labs/rdflib-neo4j/master/img/install-n10s.png" height="400">

Or you can do it manually following the [instructions in the manual](https://neo4j.com/labs/neosemantics/4.0/install/)

3. Connect to your database and either from the browser or the console and run the following:

    1. Create a uniqueness constraint on Resources' uri by running the following cypher fragment:
        ```cypher
        CREATE CONSTRAINT n10s_unique_uri ON (r:Resource)
        ASSERT r.uri IS UNIQUE;
        ```

    2. Set the configuration of the graph. This is what I did for the going meta session but if you want to know more about additional config options, have a look at the [n10s reference](https://neo4j.com/labs/neosemantics/4.0/reference/#_rdf_config).
        ```cypher
        CALL n10s.graphconfig.init({ handleVocabUris: "IGNORE" });
        ```
    3. Import the RDF files. Note that there is an absolute path to the location on your drive where you downloaded the files
        ```cypher
        unwind range(101,149) as id with "BNBLODB_202112_f" + substring(tostring(id),1) + ".nt" as filename
        call n10s.rdf.import.fetch("file:///<absolute path to your downloads folder>/bnb/" + filename,"N-Triples") yield terminationStatus, triplesLoaded, triplesParsed, extraInfo
        return filename, terminationStatus, triplesLoaded, triplesParsed, extraInfo ;
        ```
