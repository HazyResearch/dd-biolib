'''
Created on Jun 17, 2016

@author: fries
'''
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
from datasets import CdrCorpus

# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------

cache = "/Users/fries/Desktop/CDR_cache/"
infile = "/Users/fries/Desktop/CDR_Data/CDR.Corpus.v010516/"

parser = SentenceParser()
corpus = CdrCorpus(infile, parser, cache_path=cache)

for doc in corpus:
    print doc["annotations"]
print "DONE"
