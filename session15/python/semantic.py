import streamlit as st
from graphdatascience import GraphDataScience

neo = GraphDataScience("neo4j://localhost:7687", auth=("neo4j", "neoneoneo"), database="movies2")

def list_categories():
    query = """
    call db.labels() yield label
    match hierarchy = (:Class { name: label })-[:SCO*0..]->(p) where size([(p)-[s:SCO]->() | s]) = 0
    unwind [n in nodes(hierarchy) | n.name ] as name return distinct name
    """
    return neo.run_cypher(query)

def cat_details(cat_name):
    query = """
    match (c:Class { name: $name})
    optional match (c)-[:SCO*0..]->()<-[:DOMAIN]-(outgoing_rel:Relationship)-[:RANGE]->(related_cat:Class)
    with c, collect({ name: outgoing_rel.name, comment: coalesce(outgoing_rel.comment,''), other: related_cat.name }) as outgoing
    optional match (c)-[:SCO*0..]->()<-[:RANGE]-(incoming_rel:Relationship)-[:DOMAIN]->(related_cat:Class)    
    with c, [x in outgoing where x.name is not null| x]  as outgoing, collect({ name: incoming_rel.name, comment: coalesce(incoming_rel.comment,''), other: related_cat.name }) as incoming
    optional match (c)-[:SCO*0..]->()<-[:DOMAIN]-(prop:Property)-[:RANGE]->(datatype)    
    with c, outgoing, [x in incoming where x.name is not null| x] as incoming, collect({ name: prop.name, comment: coalesce(prop.comment,''), type: datatype.name }) as props
    return c.name as name, coalesce(c.comment,'') as def, outgoing, incoming, [x in props where x.name is not null| x] as props
    """
    result = neo.run_cypher(query, params={ "name": cat_name })
    return result.iloc[0]

def cat_instances(cat_info):
    query_parts = [" call n10s.inference.nodesLabelled($name) yield node return id(node) as id"]
    for prop in cat_info['props']:
        query_parts.append(" node['" + prop['name']+ "'] as `" + prop['name'] + "`")
    for outgoing in cat_info['outgoing']:
        query_parts.append("size([(node)-[:`" + outgoing['name'] + "`]->(x:`" + outgoing['other'] +"`)|x]) + ' " + outgoing['other'] + "' as `" + outgoing['name'] + " - " + outgoing['other'] +"`")
    #print(','.join(query_parts))
    return neo.run_cypher(','.join(query_parts), params={ "name": cat_info['name'] })


st.header('Semantic Explorer')
cats = list_categories()
if cats.empty:
    st.error("No ontology found")
else:
    selected_class = st.radio(
            "In this DB you will find nodes of the following types 👇",
            [row['name'] for index, row in cats.iterrows()],
            horizontal=True
        )
    if selected_class:
        class_info = cat_details(selected_class)
        #debug: st.write(class_info)
        with st.sidebar:
            st.markdown("# **:blue[" + selected_class + "]** ")
            st.markdown("_" + class_info['def'] + "_")
            st.markdown("**Properties:**")
            for prop in class_info['props']:
                st.markdown("**:blue[" +prop['name'] + "]** _(" + prop['type']+ ")_ : " + prop['comment'] )
            st.markdown("**Relationships:**")
            for outgoing in class_info['outgoing']:
                st.markdown("➡️ **:blue[" + outgoing['name'] + "]** _(connects " + selected_class + " to " + outgoing['other'] + ")_ : " + outgoing['comment'] )
            for incoming in class_info['incoming']:
                st.markdown("⬅️ **:blue[" + incoming['name'] + "]** _(connects " + incoming['other'] + " to " + selected_class+ ")_ : " + incoming['comment'] )

        st.markdown("### Instances of **:blue[" + selected_class + "]**:")

        st.dataframe(cat_instances(class_info))