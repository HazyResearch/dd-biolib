import bz2
import sys
import cPickle
import numpy as np
import itertools
from ddlite import SentenceParser,DictionaryMatch,Entities,CandidateModel
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus

def corpus_mention_summary(corpus):
    '''The raw corpus doesn't match the statistics provided at
    http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/corpus.html
    they report: 5148/791/961  we get 5145/787/960. The original stats
    are either from a different version of the corpus or wrong. Note errors:
        1) duplicate document in training data: PMID 8528200 (11 labels)
    '''
    # verify number of annotations
    for holdout in corpus.cv:
        doc_ids = corpus.cv[holdout]
        num_mentions = sum([len(corpus.annotations[doc_id]) for doc_id in doc_ids])
        print holdout,num_mentions, len(doc_ids)

ROOT = "../../../"
INDIR = "/Users/fries/Desktop/dnorm/"
OUTDIR = "/users/fries/desktop/dnorm/"


cache = "{}/cache3/".format(INDIR)
infile = "{}/disease_names/".format(INDIR)

parser = SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

#
# Training 
#
candidates = Entities("{}training-ncbi-candidates.pkl".format(OUTDIR))
print "{} candidates".format(len(candidates))
pred = [1] * len(candidates)
scores = corpus.score(candidates,pred,corpus.cv["training"].keys())
print "training", scores

#
# Development 
#
candidates = Entities("{}development-ncbi-candidates.pkl".format(OUTDIR))
print "{} candidates".format(len(candidates))

pred = [1] * len(candidates)
scores = corpus.score(candidates,pred,corpus.cv["development"].keys())
print "development", scores




corpus.error_analysis(candidates,pred,corpus.cv["development"].keys())