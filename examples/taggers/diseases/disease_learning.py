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

#INDIR = "/Users/fries/workspace/dd-bio-examples/candidates/jason/diseases/v3/"
#OUTDIR = "/Users/fries/workspace/dd-bio-examples/candidates/jason/diseases/v3/"

cache = "{}/cache3/".format(INDIR)
infile = "{}/disease_names/".format(INDIR)

parser = None# SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

# score
candidates = Entities("{}{}-ncbi-candidates.pkl".format(OUTDIR,"training"))
candidates._candidates += Entities("{}{}-ncbi-candidates.pkl".format(OUTDIR,"development"))

prediction = np.load("/users/fries/desktop/debug_gold.npy")


gold_labels = corpus.gold_labels(candidates)


holdout = corpus.cv["development"].keys() 
scores = corpus.score(candidates,prediction,holdout)
print scores


corpus.error_analysis(candidates,prediction,holdout)

sys.exit()
'''
#
# Development 
#
candidates = Entities("{}development-ncbi-candidates.pkl".format(OUTDIR))
print "{} candidates".format(len(candidates))

pred = [1] * len(candidates)
scores = corpus.score(candidates,pred,corpus.cv["development"].keys())
print "development", scores

corpus.error_analysis(candidates,pred,corpus.cv["development"].keys())
'''