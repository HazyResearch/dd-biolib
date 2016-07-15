from __future__ import print_function
import re
import sys
import itertools
import numpy as np

from ddlite import *
from ddlite_candidates import Candidates
from ddlite_candidates import Ngrams,Ngram
from ddlite_matchers import DictionaryMatch,Union,Concat

from datasets import ncbi_disease
from versioning import CandidateVersioner
from ontologies.umls import UmlsNoiseAwareDict
from ontologies.ctd import load_ctd_dictionary
from ontologies.bioportal import load_bioportal_csv_dictionary
from tools import load_disease_dictionary,load_acronym_dictionary

from matchers import NcbiDiseaseDictionaryMatch

def clean_dictionary(d):
    '''Remove some stopwords'''
    pass

def get_gold_labels(corpus,doc_ids=None):
    '''Generate gold labels for the provided corpus. Note: requires an "annotations"
    attribute'''
    labels = []
    for doc in corpus:
        if not doc_ids or doc.doc_id not in doc_ids:
            continue
         
        sent_offsets = [s._asdict()["char_offsets"][0] for s in doc.sentences]
        for label in doc.attributes["annotations"]:
            sidx = -1
            for i in range(len(sent_offsets) - 1):
                if label.start >= sent_offsets[i] and label.end - 1 < sent_offsets[i+1]:
                    sidx = i
                    break
            if label.start >= sent_offsets[-1]:
                sidx = len(sent_offsets) - 1
                
            # label crosses multiple sentence boundaries
            if sidx == -1:
                print("WARNING sentence boundary error",file=sys.stderr)
            
            metadata = {"mention_type":label.mention_type}
            labels += [Ngram(label.start, label.end - 1, doc.sentences[sidx], metadata=metadata)]
            if labels[-1].get_span() == "":
                print(labels[-1])
                print(label)
                print(doc.sentences[sidx])
                print("--------")
            
    return labels

# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------
corpus = ncbi_disease.load_corpus()

# --------------------------------------------
# Load Dictionaries / Ontologies
# --------------------------------------------
# UMLS semantic types that map to diseases or disorders
positive = ["Acquired Abnormality",
            "Anatomical Abnormality",
            "Congenital Abnormality",
            "Disease or Syndrome",
            "Experimental Model of Disease",
            "Finding",
            "Injury or Poisoning",
            "Mental or Behavioral Dysfunction",
            "Neoplastic Process",
            "Pathologic Function",
            "Sign or Symptom"]

umls_terms = UmlsNoiseAwareDict(positive=positive, prefix="terms", ignore_case=False)
umls_abbrv = UmlsNoiseAwareDict(positive=positive, prefix="abbrvs", ignore_case=False)

#diseases = umls_terms.dictionary() # create stand alone dictionaries
#abbrvs = umls_abbrv.dictionary()

diseases = load_disease_dictionary()
abbrvs = load_acronym_dictionary()

if "A" in diseases:
    del diseases["A"]

# Load various other disease ontologies
ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
ctd = load_ctd_dictionary("dicts/CTD_diseases.tsv") # CTD's MEDIC disease vocabulary

diseases.update(ordo)
diseases.update(doid)
diseases.update(ctd)

print("DICTIONARY Disease Terms: {}".format(len(diseases)))
print("DICTIONARY Abbreviation/Acronym Terms: {}".format(len(abbrvs)))

# --------------------------------------------
# Match Candidates
# --------------------------------------------
# Define a candidate space
ngrams = Ngrams(n_max=8)

longest_match = True

dict_diseases = DictionaryMatch(label='disease', d=diseases, 
                            ignore_case=True, longest_match=longest_match)
dict_abbrvs = DictionaryMatch(label='disease_acronyms', d=abbrvs, 
                            ignore_case=False, longest_match=longest_match)

stem_forms = DictionaryMatch(label='disease_stems', d=dict.fromkeys(diseases.keys() + abbrvs.keys()),
                             ignore_case=False, longest_match=longest_match)

# prefix concatenatior matchers
suffixes = DictionaryMatch(label="prefixes", d=['deficiency', 'deficient', 'deficienty', 'syndrome'],
                           ignore_case=True, longest_match=longest_match)
disease_deficiency = Concat(stem_forms, suffixes)

# disease types 
digits = map(unicode,range(1,20))
types = DictionaryMatch(label="prefixes", d=['type', 'class', 'stage', 'factor'],
                        ignore_case=True, longest_match=longest_match)
type_nums = DictionaryMatch(label="prefixes", d=['i', 'ii', 'iii', 'vi', 'v', 'vi', '1a', 'iid', 'a', 'b', 'c', 'd'] + digits,
                            ignore_case=True, longest_match=longest_match)
disease_types = Concat(stem_forms, Concat(types,type_nums))

# deficiency of
prefixes = DictionaryMatch(label="prefixes",d=['deficiency of',"inherited"],
                           ignore_case=True, longest_match=longest_match)
deficiency_of = Concat(prefixes,stem_forms)


matcher = Union(dict_diseases, dict_abbrvs, disease_deficiency,
                disease_types, deficiency_of)

matcher = Union(dict_diseases, dict_abbrvs)


holdouts = ["training","development","testing"]
for setname in holdouts:
    
    doc_ids = corpus.attributes["sets"][setname]
    cs = Candidates(ngrams, matcher, corpus.get_sentences(doc_ids))
    candidates = cs.get_candidates()
    gold = frozenset(get_gold_labels(corpus,doc_ids))
    
    print("----------------------------------")
    print(setname)
    print("----------------------------------")
    print("%d PubMed abstracts" % len(doc_ids))
    print("%d Disease gold entities" % len(gold))
    print("%d Candidates" % len(candidates)) 
    
    cs.gold_stats(gold)
    '''
    for label in gold:
        if "type" in label.get_span().lower():
            print("*",label)
    
    for c in candidates:
        print(c)
    '''
sys.exit()


