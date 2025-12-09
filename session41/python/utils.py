from rdflib import Graph, URIRef
from rdflib.namespace import RDF, OWL, RDFS, Namespace

def getLocalPart(uri):
  pos = -1
  pos = uri.rfind('#') 
  if pos < 0 :
    pos = uri.rfind('/')  
  if pos < 0 :
    pos = uri.rindex(':')
  return uri[pos+1:]


def getNLOntologyOld(text):
  g = Graph()
  g.parse(data=text)

  result = ''
  definedcats = []

  result += '\nCATEGORIES (some will have brief descriptions):\n'
  for cat in g.subjects(RDF.type, OWL.Class):  
    result += getLocalPart(cat)
    definedcats.append(cat)
    for super in g.objects(cat,RDFS.subClassOf):
        result += ' is a subcategory of ' + getLocalPart(super) 
    for desc in g.objects(cat,RDFS.comment):
        result += '. Description: ' + desc    
    result += '\n'
  extracats = {}
  for cat in g.objects(None,RDFS.domain):
     if not cat in definedcats:
        extracats[cat] = None
  for cat in g.objects(None,RDFS.range):
     if not (cat.startswith("http://www.w3.org/2001/XMLSchema#") or cat in definedcats):
        extracats[cat] = None   
  
  for xtracat in extracats.keys():
     result += getLocalPart(cat) + ":\n"

  result += '\nATTRIBUTES:\n'
  for att in g.subjects(RDF.type, OWL.DatatypeProperty):  
    result += getLocalPart(att)
    ranges = []
    for r in g.objects(att,RDFS.range):
      ranges.append(getLocalPart(r))
    if len(ranges) > 0:
     thetype = 'of type ' + ranges[0] + ' '
    else:
     thetype = ''
    for dom in g.objects(att,RDFS.domain):
        result += ': Attribute ' + thetype + 'that applies to entities of type ' + getLocalPart(dom)  
    for desc in g.objects(att,RDFS.comment):
        result += '. Description: ' + desc 
    result += '\n'
  result += '\nRELATIONSHIPS:\n'
  for att in g.subjects(RDF.type, OWL.ObjectProperty):  
    result += getLocalPart(att)
    for dom in g.objects(att,RDFS.domain):
        result += ': Relationship that connects entities of type ' + getLocalPart(dom)
    for ran in g.objects(att,RDFS.range):
        result += ' to entities of type ' + getLocalPart(ran)
    for desc in g.objects(att,RDFS.comment):
        result += '. Description: ' + desc 
    result += '\n'
  return result


def getNLOntology(text):
    g = Graph()
    g.parse(data=text)

    result = ''
    definedcats = []

    # Build a mapping: class -> list of datatype properties (attributes)
    class_to_attributes = {}

    for att in g.subjects(RDF.type, OWL.DatatypeProperty):
        for dom in g.objects(att, RDFS.domain):
            class_to_attributes.setdefault(dom, []).append(att)

    # --- CATEGORIES ---
    result += '### CATEGORIES\n'

    # Explicitly defined classes
    for cat in g.subjects(RDF.type, OWL.Class):
        label = getLocalPart(cat)
        supercats = [getLocalPart(s) for s in g.objects(cat, RDFS.subClassOf)]
        descs = [str(d) for d in g.objects(cat, RDFS.comment)]

        # Category header line
        if supercats:
            result += f"- {label} (subcategory of {', '.join(supercats)})\n"
        else:
            result += f"- {label}\n"

        # Optional description line (as plain text under the category)
        if descs:
            result += f"   - Description: {' '.join(descs)}\n"

        # Attributes for this category (from datatype properties)
        attrs = class_to_attributes.get(cat, [])
        if attrs:
            result += f"   - Attributes:\n"
            for att in attrs:
                att_label = getLocalPart(att)
                att_descs = [str(d) for d in g.objects(att, RDFS.comment)]
                # Use description if present, otherwise a generic stub
                att_desc = ""
                if att_descs:
                    att_desc = ' '.join(att_descs)
                # else:
                #     att_desc = "No description provided."
                result += f"        + {att_label}: {att_desc}\n"

        definedcats.append(cat)

    # Extra categories inferred only from domains/ranges (not explicitly declared as OWL.Class)
    extracats = {}
    for cat in g.objects(None, RDFS.domain):
        if cat not in definedcats:
            extracats[cat] = None
    for cat in g.objects(None, RDFS.range):
        if not (str(cat).startswith("http://www.w3.org/2001/XMLSchema#") or cat in definedcats):
            extracats[cat] = None

    for xtracat in extracats.keys():
        label = getLocalPart(xtracat)
        result += f"- {label}\n"
        attrs = class_to_attributes.get(xtracat, [])
        if attrs:
            result += f"   - Attributes:\n"
            for att in attrs:
                att_label = getLocalPart(att)
                att_descs = [str(d) for d in g.objects(att, RDFS.comment)]
                if att_descs:
                    att_desc = ' '.join(att_descs)
                else:
                    att_desc = "No description provided."
                result += f"        + {att_label}: {att_desc}\n"

    # --- RELATIONSHIPS ---
    result += '\n### RELATIONSHIPS:\n'
    for prop in g.subjects(RDF.type, OWL.ObjectProperty):
        prop_label = getLocalPart(prop)
        doms = [getLocalPart(d) for d in g.objects(prop, RDFS.domain)]
        rans = [getLocalPart(r) for r in g.objects(prop, RDFS.range)]
        descs = [str(d) for d in g.objects(prop, RDFS.comment)]

        # Build the relationship line like:
        # - hasObservation: Relationship that connects entities of type Animal to entities of type Observation. Description: ...
        line = f"- {prop_label}: Relationship"
        if doms:
            line += f" that connects entities of type {', '.join(doms)}"
        if rans:
            line += f" to entities of type {', '.join(rans)}"
        if descs:
            line += f". Description: {' '.join(descs)}"
        line += "\n"
        result += line

    return result


def processResults(rdf):
    g = Graph()
    g.parse(data=rdf, format="turtle")
    jaguarcount = 0
    for j in g.subjects(RDF.type, URIRef("http://example.org/ontology#Jaguar")):
        jaguarcount+=1
    print("Triples:",len(g), "Jaguars: ", jaguarcount)


