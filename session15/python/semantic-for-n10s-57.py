import streamlit as st
from graphdatascience import GraphDataScience

neo = GraphDataScience("neo4j://localhost:7687", auth=("neo4j", "neoneoneo"), database="movies")

def list_categories():
    return neo.run_cypher("call n10s.inference.labels()")

def cat_details(cat_name):
    query = """
    match (c:Class { name: $name}) RETURN c as category, 
     [rel in n10s.inference.class_incoming_rels(c) |  { rel: rel, others: n10s.inference.rel_source_classes(rel)}] as incoming,
     [rel in n10s.inference.class_outgoing_rels(c) |  { rel: rel, others: n10s.inference.rel_target_classes(rel)}] as outgoing,
     [rel in n10s.inference.class_props(c) |  { prop: rel, others: [(rel)-[:RANGE]->(r) | r.name ] }] as props
    """
    return neo.run_cypher(query, params={ "name": cat_name }).iloc[0]

def cat_instances(cat_info):
    query_parts = [" call n10s.inference.nodesLabelled($name) yield node return id(node) as id"]
    for prop in cat_info['props']:
        query_parts.append(" node['" + prop['prop']['name']+ "'] as `" + prop['prop']['name'] + "`")
    for outgoing in cat_info['outgoing']:
        relname = outgoing['rel']['name']
        for other in outgoing['others']:
            query_parts.append("size([(node)-[:`" + relname + "`]->(x:`" + other['name'] +"`)|x]) + ' " + other['name'] + "' as `" + relname + " - " + other['name'] +"`")
    print(','.join(query_parts))
    return neo.run_cypher(','.join(query_parts), params={ "name": cat_info['category']['name'] })


st.header('Semantic Explorer')
cats = list_categories()
if cats.empty:
    st.error("No ontology found")
else:
    selected_class = st.radio(
            "Categories defined in the semantic layer 👇",
            [row['label'] for index, row in cats.iterrows()],
            horizontal=True
        )
    if selected_class:
        class_info = cat_details(selected_class)
        with st.sidebar:
            st.markdown("# **:blue[" + selected_class + "]** ")
            st.markdown("_" + (class_info['category']['comment'] or "") + "_")
            st.markdown("**Properties:**")
            for prop in class_info['props']:
                st.markdown("**:blue[" +prop['prop']['name'] + "]** _(" + (prop['others'][0] or "-")+ ")_ : " + (prop['prop']['comment'] or "") )
            st.markdown("**Relationships:**")
            for outgoing in class_info['outgoing']:
                st.markdown("➡️ **:blue[" + outgoing['rel']['name'] + "]** _(connects " + selected_class + " to " + ",".join([x['name'] for x in outgoing['others']]) + ")_ : " + (outgoing['rel']['comment'] or "" ))
            for incoming in class_info['incoming']:
                st.markdown("⬅️ **:blue[" + incoming['rel']['name'] + "]** _(connects " + ",".join([x['name'] for x in incoming['others']]) + " to " + selected_class+ ")_ : " + (incoming['rel']['comment'] or ""))
        st.markdown("### Instances of **:blue[" + selected_class + "]**:")
        st.dataframe(cat_instances(class_info))