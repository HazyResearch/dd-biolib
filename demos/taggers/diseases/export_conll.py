'''
Given a parse and aligned gold annotations, export
CoNLL format files
'''

import sys
import codecs
import numpy as np
import cPickle
from ddlite import SentenceParser
from datasets import NcbiDiseaseCorpus

INDIR = "/Users/fries/Desktop/dnorm/"

cache = "{}/cache3/".format(INDIR)
infile = "{}/disease_names/".format(INDIR)
holdouts = ["training","development","testing"]

parser = None#SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

for cvset in holdouts:
    doc_ids = corpus.cv[cvset].keys()
    print len(doc_ids)
    conll = corpus.conll(doc_ids)
    outfile = "data/{}.conll.txt".format(cvset)
    with codecs.open(outfile,"w","utf-8") as f:
        f.write(conll)
    