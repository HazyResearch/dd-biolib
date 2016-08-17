'''
Simple demonstration of instantiating a concept graph and 
computing some concept similarity measures

'''
from __future__ import print_function

import networkx as nx
from ddbiolib.ontologies.umls import Metathesaurus
from ddbiolib.ontologies.umls.config import DatabaseConfig

def pprint_path(path, ontology):
    """Print UMLS CUI paths using preferred terms"""
    terms = []
    for cui in path:
        terms += [ "%s (%s)" % (cui, ontology.concept(cui).preferred_term()[0]) ]
    print("=>".join(terms))

# local database connection configuration
config = DatabaseConfig(host="127.0.0.1",username="umls",
                        dbname="2014AB", password="")
meta = Metathesaurus(config)

# some example unique identifiers for UMLS concepts
cui1 = "C0016129" # finger
cui2 = "C0446516" # arm
cui1 = "C0028643" # numbness
cui2 = "C0030193" # pain
cui2 = "C0085624" # burning

c1 = meta.concept(cui="C0016129")  # Finger
c1.print_summary()

c2 = meta.concept(cui="C0446516")  # Arm
c2.print_summary()

# build CUI-level concept graph using MeSH (Medical Subject Headings)
cui_graph = meta.concept_graph(level="CUI",source_vocab=["MSH","RXNORM","SNOMEDCT-US"])

# shortest path connecting concepts
# Finger and Arm
path = nx.shortest_path(nx.Graph(cui_graph), c1.cui, c2.cui)
pprint_path(path,meta)
