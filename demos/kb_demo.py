'''
Simple demonstration of instantiating a concept graph and 
computing some concept similarty measures

'''
from __future__ import print_function

import umls
import metrics
import networkx as nx

def pprint_path(path, ontology):
    """Print UMLS CUI paths using preferred terms"""
    terms = []
    for cui in path:
        terms += [ "%s (%s)" % (cui, ontology.concept(cui).preferred_term()[0]) ]
    print("=>".join(terms))

meta = umls.Metathesaurus()

cui1 = "C0016129" # finger
cui2 = "C0446516" # arm

cui1 = "C0546866"  # Gentamicin Sulfate (USP) C0017436
cui2 = "C0035204"  # Respiration Disorders

c1 = meta.concept(cui=cui1)  
c1.print_summary()

c2 = meta.concept(cui=cui2)  
c2.print_summary()

#cui = "C0023822"
#c1 = meta.concept(cui=cui)  
#c1.print_summary()

# build CUI-level concept graph using MeSH (Medical Subject Headings)
cui_graph = meta.concept_graph(level="CUI",source_vocab=["MSH","RXNORM","SNOMEDCT-US"])

#
# Similarity Measures
#
print("Simple Path Similarity:", 
      metrics.path_similarity(nx.Graph(cui_graph), c1.cui, c2.cui))

# shortest path connecting concepts
path = nx.shortest_path(nx.Graph(cui_graph), c1.cui, c2.cui)
print(path)
pprint_path(path,meta)
