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

def parse_record(r):
    d = {}
    for line in r:
        if re.search("^\w+\s+=\s+",line):
            m = re.split("(^\w+)\s+=\s+",line.strip())[1:]
            key,value = m
            value = value.split("|")
            if key in d:
                d[key] += value
            else:
                d[key] = value
                
    return d
            
def load_mesh_defs(filename="d2015.bin"):
    mesh = {}
    record = []
    for line in open(filename,"rU"):
        line = line.strip()
        if not line:
            r = parse_record(record)
            mesh[r["UI"][0]] = r
            record = []
            continue
        record += [line]
    return mesh
        
   

mesh = load_mesh_defs("/Users/fries/Dropbox/Datasets/mesh_headings/2015/d2015.bin")
mesh_ids = {uid:mesh[uid]["MH"][0] for uid in mesh}
mesh_names = {name.lower():uid for uid,name in mesh_ids.items()}


# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------

cache = "/Users/fries/Desktop/CDR_cache/"
infile = "/Users/fries/Desktop/CDR_Data/CDR.Corpus.v010516/"

parser = SentenceParser()
corpus = CdrCorpus(infile, parser, cache_path=cache)

n,N = [],[]
print corpus
for pmid in corpus.annotations:
    for mention in corpus.annotations[pmid]:
        if len(mention.mesh_ids) > 1:
            t =  mention.text.lower()
            N += [t]
            
            if "and" in t or "or" in t or "and/or" in t:
                n += [t]
             
# multi-ids        
print len(n),len(N)
print len(set(N).difference(n))
print "DONE"

n = 0
N = 0
for pmid in corpus.annotations:
    for mention in corpus.annotations[pmid]:
        N += 1
        if mention.text.lower() in mesh_names:
            n += 1.0
            
print n,N, n/N * 100
        



