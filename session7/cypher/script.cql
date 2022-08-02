CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

call n10s.graphconfig.init({ handleVocabUris: "IGNORE" , keepLangTag: true , handleMultival: "ARRAY"});

call n10s.rdf.import.inline('','Turtle);

match (n)-[r]-(o) where id(n) = $node_id
match (cn:Class)<-[:domain|range*1]-(op:ObjectProperty)-[:domain|range*1]->(co:Class)
where type(r) in op.label
      and (exists(op.direct) or exists(op.inverse))
and  [x in labels(n) where x <> "Resource"][0] in cn.label
and [x in labels(o) where x <> "Resource"][0] in co.label
with n[cn.name[0]] as subj ,
n10s.rdf.getLangValue($speech_style ,op[case when startNode(r) = n then "direct" else "inverse" end]) as pred ,
o[co.name[0]] as obj
with  subj ,
case when pred contains '$' then replace(pred,'$',toString(obj)) else pred end  as pred,
substring(reduce(r="",x in collect(case when pred contains '$' then '' else toString(obj) end)| r + ", " + x),2) as obj
return subj + " " + pred + " " + obj  as sentence




