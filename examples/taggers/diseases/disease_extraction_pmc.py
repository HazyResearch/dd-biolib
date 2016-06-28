import bz2
import sys
import csv
import re
import os
import numpy as np
import itertools
import cPickle
import ddlite
from ddlite import SentenceParser,Entities
from ddlite import Union, DictionaryMatch, RegexNgramMatch
from utils import unescape_penn_treebank
from datasets import PubMedAbstractCorpus

def load_bioportal_csv_dictionary(filename):
    '''BioPortal Ontologies
    http://bioportal.bioontology.org/'''
    reader = csv.reader(open(filename,"rU"),delimiter=',', quotechar='"')
    d = [line for line in reader]
    
    dictionary = {}
    for line in d[1:]:
        row = dict(zip(d[0],line))
        dictionary[row["Preferred Label"]] = 1
        dictionary.update({t:1 for t in row["Synonyms"].split("|")})
        
    return dictionary
    
def load_disease_dictionary():  
      
    # UMLS SemGroup Disorders
    #dictfile = "dicts/umls_disorders.bz2"
    #dictfile = "dicts/umls_disorders_snomed_msh_mth.bz2"
    dictfile = "dicts/umls_disorders_v2.bz2"
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if not word.isupper()}

    # Orphanet Rare Disease Ontology
    ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
    ordo = {word:1 for word in ordo if not word.isupper()}
    diseases.update(ordo)
    
    # Human Disease Ontology 
    doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
    doid = {word:1 for word in doid if not word.isupper()}
    diseases.update(doid)
      
    # ------------------------------------------------------------
    # remove cell dysfunction terms
    dictfile = "dicts/cell_molecular_dysfunction.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word not in terms} 
    
    dictfile = "dicts/umls_geographic_areas.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word not in terms}
    # ------------------------------------------------------------
    
    # NCBI training set vocabulary
    dictfile = "dicts/ncbi_training_diseases.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    terms = {word:1 for word in terms if not word.isupper()}
    diseases.update(terms)
    
    # remove stopwords
    dictfile = "dicts/stopwords.txt"
    stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases = {word:1 for word in diseases if word.lower() not in stopwords}  
    
    return diseases

def load_acronym_dictionary():    
    
    #dictfile = "dicts/umls_disorders.bz2"
    #dictfile = "dicts/umls_disorders_snomed_msh_mth.bz2" # candidate recall: 74.59% (587/787)
    dictfile = "dicts/umls_disorders_v2.bz2"
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if word.isupper()}
    
    # Orphanet Rare Disease Ontology
    ordo = load_bioportal_csv_dictionary("dicts/ordo.csv")
    ordo = {word:1 for word in ordo if word.isupper()}
    diseases.update(ordo)
    
    # Human Disease Ontology 
    doid = load_bioportal_csv_dictionary("dicts/DOID.csv")
    doid = {word:1 for word in doid if word.isupper()}
    diseases.update(doid)
    
    dictfile = "dicts/ncbi_training_diseases.txt"
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    terms = {word:1 for word in terms if word.isupper()}
    diseases.update(terms)
    
    # filter by char length
    diseases = {word:1 for word in diseases if len(word) > 1}
    
    return diseases

def create_corpus_dict(corpus, setdef="training"):
    '''Create dictionary using annotated corpus data'''
    dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in [setdef]]))
    documents = [(doc_id,corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set]
    
    print len(dev_set),len(corpus.documents)
    
    d = {}
    for pmid,doc,labels in documents:
        for i in range(0,len(doc)):
            for tag in labels[i]:
                mention = doc[i].words[tag[-1][0]:tag[-1][1]]
                v1 = "".join(unescape_penn_treebank(mention))
                v2 = tag[0].replace(" ","")
                if v1 != v2:
                    # problem with tokenization
                    #print " ".join(unescape_penn_treebank(mention)), tag
                    pass
                else:
                    d[" ".join(mention)] = 1                    
    return d


# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------

OUTDIR = "/Users/fries/Desktop/pubmed_abstracts/"
cache = "/Users/fries/Desktop/pubmed_abstract_cache/"
infile = "../../../datasets/chemdner_corpus/silver.abstracts.txt"

parser = SentenceParser()
corpus = PubMedAbstractCorpus(infile, parser, cache_path=cache)

# --------------------------------------------
# Match Candidates
# --------------------------------------------

diseases = load_disease_dictionary()
acronyms = load_acronym_dictionary()

matcher_d = DictionaryMatch(label='D', dictionary=diseases, ignore_case=True)
matcher_a = DictionaryMatch(label='D', dictionary=acronyms, ignore_case=False)
matcher = Union(matcher_a, matcher_d)

#pattern = re.compile("((JJ|VBN)\s)+(NN[SP]*\s*)+")
#pattern = re.compile("((NN[SP]*|JJ)\s*){2,}")
#matcher_tags = RegexNgramMatch(label="D",match_attrib="poses",regex_pattern=pattern,ignore_case=False)
matcher = Union(matcher_a, matcher_d)#, matcher_tags)

N = 1000
sentences = [doc["sentences"] for i,doc in enumerate(corpus) if i < N]
sentences = list(itertools.chain.from_iterable(sentences))
candidates = Entities(sentences, matcher)

candidates.dump_candidates("{}/v4/pubmed-candidates-sample-{}.pkl".format(OUTDIR,N))

# candidate recall
print("Found {} candidate entities".format(len(candidates)))
