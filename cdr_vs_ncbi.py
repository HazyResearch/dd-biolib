'''
Created on Jun 16, 2016

@author: fries
'''
from ddlite import SentenceParser
from datasets import NcbiDiseaseCorpus

infile = "/users/fries/dropbox/cdr_full_corpus.txt"
cdr = [line.strip().split("|")[0] for line in open(infile,"rU").readlines() if "\t" not in line]
cdr = set(cdr)
cdr.remove("")


INDIR = "/Users/fries/Desktop/ddlite_corpora/dnorm/"
cache = "{}/cache3/".format(INDIR)
infile = "{}/disease_names/".format(INDIR)

parser = SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

for pmid in corpus.cv["training"]:
    doc = "{} {}".format(corpus.documents[pmid]["title"],corpus.documents[pmid]["body"])
    print doc

'''
ncbi = set(corpus.documents.keys())

print len(cdr)
print len(ncbi)
print cdr.intersection(ncbi)
'''