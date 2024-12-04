// set param (node id and style)

:params {node_id : , speech_style: "default"}


// natural language generator 


call {
      match (n) where id(n) = $node_id
      match (cn:Class)<-[:domain]-(op:DatatypeProperty)
      where op.label[0] in keys(n)
            and (exists(op.direct))
            and  [x in labels(n) where x <> "Resource"][0] in cn.label
      with n[cn.name[0]] as subj ,
           n10s.rdf.getLangValue($speech_style, op.direct) as pred ,
           n[op.label[0]] as obj
      // some formatting     
      with  case when pred contains '$s' then '' else subj end as subj,
            replace(replace(pred,'$s',toString(subj)),'$o',toString(obj))   as pred,
            case when pred contains '$o' then '' else obj end as obj
      return subj + " " + pred + " " + obj  as sentence

union

      match (n)-[r]-(o) where id(n) = $node_id
      match (cn:Class)<-[:domain|range]-(op:ObjectProperty)-[:domain|range]->(co:Class)
      where type(r) in op.label
            and (exists(op.direct) or exists(op.inverse))
            and  [x in labels(n) where x <> "Resource"][0] in cn.label
            and [x in labels(o) where x <> "Resource"][0] in co.label
      with n[cn.name[0]] as subj ,
           n10s.rdf.getLangValue($speech_style ,op[case when startNode(r) = n then "direct" else "inverse" end]) as pred ,
           substring(reduce(result="", x in collect(o[co.name[0]]) | result+","+x),1) as obj
      // some formatting     
      with  case when pred contains '$s' then '' else subj end as subj ,
            replace(replace(pred,'$o',obj),'$s',subj) as pred,
            case when pred contains '$o' then '' else obj end as obj
      return subj + " " + pred + " " + obj  as sentence

}

return distinct sentence


