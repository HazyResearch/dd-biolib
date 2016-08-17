import bz2
import sys
import csv
import codecs
import numpy as np
import itertools
import cPickle
from ddlite import SentenceParser,DictionaryMatch,Entities,Union
from utils import unescape_penn_treebank
from datasets import PubMedCentralCorpus

def load_stopwords():
    dictfile = "dicts/stopwords.txt"
    return [line.strip().split("\t")[0] for line in open(dictfile).readlines()]

def load_dictionary(filename, stopwords=[]):  

    if filename.split("/")[-1].split(".")[-1] == "bz2":
        d = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(filename, 'rb').readlines()}
    else:
        d = {line.strip().split("\t")[0]:1 for line in codecs.open(filename, 'rb',"utf-8", errors="ignore").readlines()}
    d = {word:1 for word in d if not word.isupper() and word.lower() not in stopwords}
    return d
    
def load_acronym_dictionary(filename):    
    
    if filename.split("/")[-1].split(".")[-1] == "bz2":
        d = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(filename, 'rb').readlines()}
    else:
        d = {line.strip().split("\t")[0]:1 for line in codecs.open(filename, 'rb',"utf-8", errors="ignore").readlines()}
    
    # filter by char length and stopwords
    d = {word:1 for word in d if len(word) > 1 and word.isupper()}
    return d


# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------
cache = "/Users/fries/Desktop/pmc_cache/"
inputdir = "/Users/fries/Desktop/articles.I-N/"

# orthopedics subset
cache = "/Users/fries/workspace/dd-bio-examples/data/documents/pmc-ortho-cache/"
inputdir = "/Users/fries/workspace/dd-bio-examples/data/documents/pmc-ortho/"

parser = SentenceParser()
corpus = PubMedCentralCorpus(inputdir,parser,cache_path=cache)
sentences = [corpus[uid]["sentences"] for uid in corpus.documents.keys()[0:1000]] #
sentences = list(itertools.chain.from_iterable(sentences))

# --------------------------------------------
# Match Candidates
# --------------------------------------------

stopwords = load_stopwords()
entities = load_dictionary("dicts/fma_human_anatomy.bz2",stopwords)
acronyms = load_acronym_dictionary("dicts/umls_human_anatomy.bz2")

matcher_d = DictionaryMatch(label='A', dictionary=entities, ignore_case=True)
matcher_a = DictionaryMatch(label='A', dictionary=acronyms, ignore_case=False)
matcher = Union(matcher_a, matcher_d)

candidates = Entities(sentences, matcher)
candidates.dump_candidates("candidates/ortho-candidates.{}.pkl".format(len(sentences)))

