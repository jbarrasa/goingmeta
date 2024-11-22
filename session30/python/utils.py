from rdflib import Graph
from rdflib.namespace import RDF, OWL, RDFS

def getLocalPart(uri):
  pos = -1
  pos = uri.rfind('#') 
  if pos < 0 :
    pos = uri.rfind('/')  
  if pos < 0 :
    pos = uri.rindex(':')
  return uri[pos+1:]



def getNLOntology(g):
  result = ''
  definedcats = []

  result += '\nCATEGORIES:\n'
  for cat in g.subjects(RDF.type, OWL.Class):  
    result += getLocalPart(cat)
    definedcats.append(cat)
    for desc in g.objects(cat,RDFS.comment):
        result += ': ' + desc + '\n'
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
    for dom in g.objects(att,RDFS.domain):
        result += ': Attribute that applies to entities of type ' + getLocalPart(dom)  
    for desc in g.objects(att,RDFS.comment):
        result += '. It represents ' + desc + '\n'

  result += '\nRELATIONSHIPS:\n'
  for att in g.subjects(RDF.type, OWL.ObjectProperty):  
    result += getLocalPart(att)
    for dom in g.objects(att,RDFS.domain):
        result += ': Relationship that connects entities of type ' + getLocalPart(dom)
    for ran in g.objects(att,RDFS.range):
        result += ' to entities of type ' + getLocalPart(ran)
    for desc in g.objects(att,RDFS.comment):
        result += '. It represents ' + desc + '\n'
  return result