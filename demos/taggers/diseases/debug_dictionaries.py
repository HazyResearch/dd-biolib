import re
import os
import sys
import bz2
import csv
import codecs
import cPickle
import itertools
from operator import itemgetter
from itertools import groupby
sys.path.insert(1, "/users/fries/code/")

#import ddlite
from ddlite import *

rootdir = "/Users/fries/Code/HILDA-2016/candidates/"

#
# With training vocabulary
#

fname = "{}sen_v4/training-ncbi-candidates.pkl".format(rootdir)
#candidates = cPickle.load(open(fname,"rb"))
candidates = Entities(fname)
train_vocab = {}
for c in candidates:
    term = " ".join(c.mention()).lower()
    train_vocab[term] = train_vocab.get(term,0) + 1

#
# Without training vocabulary
#

fname = "{}sen_sans_training_v4/training-ncbi-candidates.pkl".format(rootdir)
#candidates = cPickle.load(open(fname,"rb"))
candidates = Entities(fname)
no_train_vocab = {}
for c in candidates:
    term = " ".join(c.mention()).lower()
    no_train_vocab[term] = train_vocab.get(term,0) + 1
    
missing = set(train_vocab.keys()).difference(set(no_train_vocab.keys()))
for item in missing:
    print item
    