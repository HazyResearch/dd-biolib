'''
UMLS Metathesaurus

Current Functionality
+ Simple Concept object (interface for definitions, term sets, etc.)
+ Build dictionaries of UMLS semantic types
+ Build positive examples of UMLS relations

There are many other tools that do similar things, though none have a 
distant supervision focus (and there is a bias towards Perl-based tools)

UMLS::Interface    http://search.cpan.org/~btmcinnes/UMLS-Interface-1.47/
UMLS::Similarity   http://search.cpan.org/~btmcinnes/UMLS-Similarity-1.45/

This functionality should be eventually incorporated into bio-ddlib, esp.
the graph and path-based similarity measures.

TODO
+ implement similarity and relatedness measures from UMLS::Similarity
+ path-based feature generator
+ keyword expansion/similarity using word embeddings

@author Jason Alan Fries

'''
from __future__ import print_function

import sys
import ontologies.umls as umls
from ontologies.umls.graph import pprint_tree

meta = umls.Metathesaurus()
norm = umls.MetaNorm(function=lambda x:x.lower())


#
# UMLS Concepts and Relations
#

# UMLS Semantic Network 
taxonomy = meta.semantic_network.graph(relation="isa")
root_nodes = ([node for node in taxonomy if not taxonomy.predecessors(node)])
for node in root_nodes:
    pprint_tree(taxonomy,node)

# UMLS semantic groups

print( meta.semantic_network.groups["Anatomy"] )


# UMLS normalizes concepts with a CUI (Concept Unique Identifier)
# e.g., C0002645 is 'Amoxycillin'
concept = meta.concept(cui='C3539739') 
concept.print_summary()

# List all relations on a specific concept
relations = meta.relations_on_cui("C0002645",source_vocab=["SNOMEDCT_US"])
rel = list(set([rela[2] for rela in relations]))
print(rel)

# Search for concepts (CUIs) by string. This is a noisy match. We don't perform
# any disambiguation so CUIs are not guaranteed to actually be related.
matches = meta.match_concepts("Cu", match_substring=False) 
print("Found %d string->concept matches" % len(matches))
for cui in matches:
    concept = meta.concept(cui=cui) 
    concept.print_summary()


#
# Building Dictionaries and Relation Tuples
#

'''
# List all semantic types, relations, and source vocabularies
print(meta.get_source_vocabulary_defs())
print(sorted(meta.get_semtypes_list()))
print(sorted(meta.get_relations_list()))
'''
'''
# Build dictionaries for a given semantic type (i.e., entity)
d = meta.dictionary("Disease or Syndrome")
d = map(norm.normalize,d)
for term in sorted(d,key=lambda x:len(x.split()),reverse=1):
    print(term)
'''


# Generate relation examples from given semantic types. This is 
# highly dependent on the choice of source vocabulary. 
attribute ="may_prevent"
relations = meta.relations("Substance","Biologic Function",attribute)
print("Found %d distinct relation pairs" % len(relations))

# Print concept terms (this can be expanded by using concept.all_terms() 
# rather than just the preferred term).
for cui1,cui2 in relations:

    terms_cui1 = map(norm.normalize, meta.concept(cui1).all_terms())
    terms_cui2 = map(norm.normalize, meta.concept(cui2).all_terms())
    
    terms_cui1 = "|".join(terms_cui1)
    terms_cui2 = "|".join(terms_cui2)
    
    row= [cui1, terms_cui1, attribute, cui2, terms_cui2 ]
    print("\t".join(row).encode("utf-8",errors="ignore"))




