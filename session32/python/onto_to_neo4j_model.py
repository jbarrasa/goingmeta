import streamlit as st
from rdflib import Graph
import requests 
from DIMNodeDef import getLocalPart
from DIModelBuilder import DIModelBuilder
import json

st.title('Use Ontology')

onto_url = st.text_input("Ontology url", "")

serialisation = st.radio(
    "Serialisation format",
    ["turtle", "xml", "json-ld","ntriples"],
    index=0,
    horizontal=True
)
if onto_url and serialisation: 
    resp = requests.get(onto_url)
    theonto = resp.text
    g = Graph()
    g.parse(data=theonto, format=serialisation)
    all_classes = {}

    catsQuery = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        select distinct ?c ?cl
        where {
            ?c a ?cat .
            optional { ?c rdfs:label ?cl }
            filter(?cat in (rdfs:Class, owl:Class) && isIRI(?c)) 
            }"""

    for record in g.query(catsQuery):
        all_classes[record.c] = record.cl or getLocalPart(record.c)


    selected_classes = st.multiselect(
        "Select classes",
        key=["ALL CLASSES"] + list(all_classes.keys()),
        options=["ALL CLASSES"] + list(all_classes.values())
    )

    selected_uris = []
    for c in selected_classes:
        if c == "ALL CLASSES":
            selected_uris = []
            break
        selected_uris.append(list(all_classes.keys())[list(all_classes.values()).index(c)])


    if selected_classes:
        try: 
            mb = DIModelBuilder()

            params = {}
            if len(selected_uris) > 0:
                params["classList"] = selected_uris

            mb.build_di_model(theonto, serialisation, params)

            text_contents = json.dumps(mb.get_model_as_serialisable_object_v2())
            st.download_button(label="Download model",
                                data=text_contents,
                                file_name=getLocalPart(onto_url).split(".")[0] + ".json",
                                mime="application/json",)
        except RuntimeError as e:
            st.write("Problems... " , e.args)


    st.write("_____________________________")
    if selected_classes:
        for k,v in mb.model_def.items():
            st.write(k)
            st.write(v.summary(mb.g))