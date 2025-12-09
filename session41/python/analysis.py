from __future__ import annotations
from typing import Dict, Iterable, Tuple, Any, Optional, Union
from rdflib import Graph
import pandas as pd

# ---------------- Core helpers ----------------

def run_ask(g: Graph, query: str) -> bool:
    res = g.query(query)
    if res.type != "ASK":
        raise ValueError("Non-ASK query detected. This harness only supports ASK queries.")
    return bool(res.askAnswer)

def decide_status(result: bool, expected: Optional[bool]) -> str:
    """
    PASS/FAIL rule:
      - If expected is None: True => PASS, False => FAIL
      - If expected is bool: result == expected => PASS else FAIL
    """
    if expected is None:
        return "PASS" if result else "FAIL"
    return "PASS" if (result == expected) else "FAIL"

def _expect_for_test(
    label: str,
    graph_name: str,
    expected: Optional[
        Dict[str, Union[bool, Dict[str, bool]]]
    ],
) -> Optional[bool]:
    """
    Resolve expected value for a given test label and graph name.

    Supports:
      expected = {
        "test A": True,                          # single expectation for all graphs
        "test B": {"G1": True, "G2": False},     # per-graph expectation
      }
    """
    if not expected or label not in expected:
        return None
    v = expected[label]
    if isinstance(v, dict):
        return v.get(graph_name, None)
    return bool(v)

# ---------------- Main API ----------------

def compare_ask_queries_on_many_graphs(
    queries: Iterable[Tuple[str, str]],        # (label, ask_query)
    graphs: Dict[str, Graph],                  # {"G1": Graph(), "G2": Graph(), ...}
    expected: Optional[
        Dict[str, Union[bool, Dict[str, bool]]]
    ] = None,                                  # optional expectations; see _expect_for_test
    to_excel_path: Optional[str] = None,       # optional export to Excel
) -> Dict[str, Any]:
    """
    Run ASK queries across N graphs and report PASS/FAIL.

    Returns a dictionary with:
      - "matrix_df": DataFrame with rows=tests and columns=graph names ("PASS"/"FAIL" cells)
      - "bool_df":   DataFrame mirroring matrix_df with True/False results (for debugging)
      - "summary":   per-graph PASS/FAIL counts and totals
      - "details":   nested structure with results per test and graph
    """
    # For nicer N3 render consistency, unify prefixes across graphs (optional)
    # We'll just bind graph[0]'s namespace manager with others for consistent parsing of queries
    # (Not strictly necessary for ASK.)

    # Collect results
    tests_order = []
    graph_names = list(graphs.keys())
    details = {}  # {label: {graph_name: {"result": bool, "status": "PASS"/"FAIL", "expected": Optional[bool]}}}

    for label, ask_query in queries:
        tests_order.append(label)
        details[label] = {}
        for gname, g in graphs.items():
            r = run_ask(g, ask_query)
            exp = _expect_for_test(label, gname, expected)
            st = decide_status(r, exp)
            details[label][gname] = {"result": r, "status": st, "expected": exp}

    # Build PASS/FAIL matrix and boolean matrix
    matrix_rows = []
    bool_rows = []
    exp_col = []   # optional human-readable expected (single value if uniform)
    for label in tests_order:
        row = {"Test": label}
        brow = {"Test": label}
        # Try to show a single Expected column if all expectations for this test are identical (or None)
        per_graph_exp = [details[label][g]["expected"] for g in graph_names]
        uniform = all(e == per_graph_exp[0] for e in per_graph_exp)
        exp_val = per_graph_exp[0] if uniform else None
        exp_col.append("True" if exp_val is True else ("False" if exp_val is False else ""))

        for gname in graph_names:
            row[gname] = details[label][gname]["status"]
            brow[gname] = details[label][gname]["result"]
        matrix_rows.append(row)
        bool_rows.append(brow)

    matrix_df = pd.DataFrame(matrix_rows).set_index("Test")
    bool_df = pd.DataFrame(bool_rows).set_index("Test")

    # Add an 'Expected' column (left-most) for readability
    matrix_df.insert(0, "Expected", exp_col)

    # Compute per-graph summaries
    summary = {}
    for gname in graph_names:
        col = matrix_df[gname]
        total = len(col)
        passed = int((col == "PASS").sum())
        failed = total - passed
        summary[gname] = {"total": total, "PASS": passed, "FAIL": failed}

    # Optional Excel
    if to_excel_path:
        with pd.ExcelWriter(to_excel_path, engine="xlsxwriter") as xw:
            matrix_df.to_excel(xw, sheet_name="ASK_tests", index=True)
            # Also write a summary sheet
            pd.DataFrame.from_dict(summary, orient="index").to_excel(xw, sheet_name="summary")
            # Optional raw booleans for debugging
            bool_df.to_excel(xw, sheet_name="raw_bools")

            # Add basic conditional formatting for PASS/FAIL
            ws = xw.sheets["ASK_tests"]
            nrows, ncols = matrix_df.shape
            # PASS = green, FAIL = red (Excel formatting)
            ws.conditional_format(1, 1, nrows, ncols-1, {
                "type": "text", "criteria": "containing", "value": "PASS",
                "format": xw.book.add_format({"font_color": "green"})
            })
            ws.conditional_format(1, 1, nrows, ncols-1, {
                "type": "text", "criteria": "containing", "value": "FAIL",
                "format": xw.book.add_format({"font_color": "red"})
            })

    return {
        "matrix_df": matrix_df,
        "bool_df": bool_df,
        "summary": summary,
        "details": details,
    }

# ---------------- Example usage ----------------
if __name__ == "__main__":
    from rdflib import Namespace, RDF, Literal

    EX = Namespace("http://example.org/")

    
    Gs: Dict[str, Graph] = {}

    for i in range(1, 9):
        g = Graph(); g.parse(f"ontoproject/output/owl_onto__{i}.ttl", format="turtle")        
        Gs[f"GOWL{i}"] = g
    
    for i in range(1, 9):
        g = Graph(); g.parse(f"ontoproject/output/nl_onto__{i}.ttl", format="turtle")        
        Gs[f"GNL{i}"] = g

    

    queries = [
        ("All Jaguars", """
            PREFIX onto: <http://example.org/ontology#>
            ASK {
            { SELECT (COUNT(DISTINCT ?needle) AS ?c) WHERE {
                VALUES ?needle {
                    "el jefe" "macho b" "sombra" "oko" "cochise" 
                    "kudam" "mariposa" "xam" "isa" "fera" "amanaci" 
                    "ben" "f11" "pixana" "levantina"  "mariua" 
                }
                ?u a onto:Jaguar ; rdfs:label ?n .
                FILTER(CONTAINS(LCASE(STR(?n)), ?needle))
            } }
            FILTER(?c = 16)
            }
        """),
        ("Jefe-props", """
            PREFIX onto: <http://example.org/ontology#>
            ASK 
         { ?jefe a onto:Jaguar ; rdfs:label ?jname ; onto:hasGender "Male" ; 
                onto:hasLastSightingDate "2021-11-27"^^xsd:date; onto:hasMonitoringStartDate "2011-11-19"^^xsd:date .
                FILTER CONTAINS(LCASE(STR(?jname)), "el jefe")            
         }
        """),  
        ("Jefe-obs", """
            PREFIX onto: <http://example.org/ontology#>
            ASK 
         { ?jefe a onto:Jaguar ; rdfs:label ?jname .  
            FILTER CONTAINS(LCASE(STR(?jname)), "el jefe") .
           ?jefe onto:hasObservation [ a onto:Observation; onto:observedDate "2011-11-19"^^xsd:date ; onto:observedBy [ rdfs:label ?df ] ] ;
                 onto:hasObservation [ a onto:Observation; onto:observedDate "2021-11-27"^^xsd:date ; onto:observedBy [ rdfs:label ?pf ] ] .
            FILTER CONTAINS(LCASE(STR(?df)), "donnie fenn") .
            FILTER CONTAINS(LCASE(STR(?pf)), "profauna") .
         }
        """),      
        ("Jefe-monitoring", """
            PREFIX onto: <http://example.org/ontology#>
            ASK 
         { ?jefe a onto:Jaguar ; rdfs:label ?jname .  
            FILTER CONTAINS(LCASE(STR(?jname)), "el jefe") .        
           ?jefe onto:monitoredByOrg [ rdfs:label ?orgName1 ; a onto:NGO ] ; 
                 onto:monitoredByOrg [ rdfs:label ?orgName2 ; a onto:GovernmentAgency ] ; 
                 onto:monitoredByOrg [ rdfs:label ?orgName3 ; a onto:AcademicInstitution ] . 
           FILTER CONTAINS(LCASE(STR(?orgName1)), "conservation catalyst") 
           FILTER CONTAINS(LCASE(STR(?orgName2)), "arizona game and fish department")  
           FILTER CONTAINS(LCASE(STR(?orgName3)), "university of arizona")  
         }
        """),   
        ("Jefe-named", """
            PREFIX onto: <http://example.org/ontology#>
            ASK 
         { ?jefe a onto:Jaguar ; rdfs:label ?jname .  
            FILTER CONTAINS(LCASE(STR(?jname)), "el jefe") .        
           ?jefe onto:namedBy [ a onto:Person; rdfs:label ?pers ] .                 
            FILTER (CONTAINS(LCASE(STR(?pers)), "felizardo valencia") && CONTAINS(LCASE(STR(?pers)), "students") )
         }
        """),   
        ("Llanos region found", """
            PREFIX onto: <http://example.org/ontology#>
            ASK { ?l a onto:Region ; rdfs:label ?lname . 
                   FILTER CONTAINS(LCASE(STR(?lname)), "llanos")
            } 
        """),
        ("Llanos region linked to jaguar", """
            PREFIX onto: <http://example.org/ontology#>
            ASK { ?l a onto:Region ; rdfs:label ?lname . 
                   FILTER CONTAINS(LCASE(STR(?lname)), "llanos")
                   [] onto:occursIn ?l ; rdfs:label ?jname . 
                   FILTER CONTAINS(LCASE(STR(?jname)), "mariposa")
            } 
        """),
        ("Llanos region linked to country", """
            PREFIX onto: <http://example.org/ontology#>
            ASK { ?l a onto:Region ; rdfs:label ?lname . 
                   FILTER CONTAINS(LCASE(STR(?lname)), "llanos")
                   ?l onto:locatedInCountry ?c . ?c rdfs:label ?cname . 
                   FILTER CONTAINS(LCASE(STR(?cname)), "colombia")
            } 
        """),
        ("Mariposa", """
            PREFIX onto: <http://example.org/ontology#>
            ASK 
         { [] a onto:Jaguar ; rdfs:label ?jname ; onto:hasGender "Female" .                
                FILTER CONTAINS(LCASE(STR(?jname)), "mariposa")            
         }
        """),  
        ("Mariposa-Cayenita", """
            PREFIX onto: <http://example.org/ontology#>
            ASK 
         { ?m a onto:Jaguar ; rdfs:label ?jname ; onto:occursIn ?p .
            FILTER CONTAINS(LCASE(STR(?jname)), "mariposa") .
           ?m onto:hasOffspring [ a onto:Jaguar; rdfs:label ?oname ; onto:occursIn ?p ] .           
            FILTER CONTAINS(LCASE(STR(?oname)), "cayenita") .
         }
        """),
        ("offspring count", """
            PREFIX onto: <http://example.org/ontology#>
            ASK {
                {
                    SELECT ?m (COUNT(?off) AS ?count)
                    WHERE { ?m a onto:Jaguar ; rdfs:label ?jname ; onto:hasOffspring ?off .
                            FILTER CONTAINS(LCASE(STR(?jname)), "f11-9") . }
                    GROUP BY ?m
                    HAVING (COUNT(?off) = 3)
                }
            }
        """),
        ("observation count", """
            PREFIX onto: <http://example.org/ontology#>
            ASK {
                {
                    SELECT (COUNT(?o) AS ?count)
                    WHERE { ?o a onto:Observation #; rdfs:label ?jname ; onto:hasOffspring ?off .
                            #FILTER CONTAINS(LCASE(STR(?jname)), "f11-9") . 
         }
                    #GROUP BY ?m
                    HAVING (COUNT(?o) >= 5)
                }
            }
        """)
        # ("more", """
        #     PREFIX onto: <http://example.org/ontology#>
        #     SELECT ?l ?lname ?jag ?jname ?c ?cname WHERE { ?l a onto:Region ; rdfs:label ?lname . 
        #            FILTER CONTAINS(LCASE(STR(?lname)), "llanos")
        #            ?jag onto:occursIn ?l ; rdfs:label ?jname .
        #            optional { ?l (onto:locatedInCountry | onto:locatedIn) ?c . ?c rdfs:label ?cname . } }
        # """),
    ]

    # Expectations:
    # - If omitted for a test, PASS means True by default.
    # - Here we show mixed usage: uniform expectation and per-graph override.
    expected = {
        # "has any person": True,                     # all graphs expected True
        # "alice has a name": {"G1": False, "G2": False, "G3": False, "G4": False},
        # "bob is a person": {"G1": False, "G2": True, "G3": False, "G4": False},
    }

    out = compare_ask_queries_on_many_graphs(queries, Gs, expected=expected, to_excel_path=None)

    print("\n=== PASS/FAIL Matrix ===")
    print(out["matrix_df"])
    print("\n=== Per-graph Summary ===")
    for gname, s in out["summary"].items():
        print(f"{gname}: {s}")
