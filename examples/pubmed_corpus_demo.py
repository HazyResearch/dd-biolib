from ddlite import *
from datasets import PubMedAbstractCorpus

#
# PubMed Abstract Corpus
#
inputdir = "../datasets/chemdner_corpus/silver.abstracts.txt"
parser = SentenceParser()
corpus = PubMedAbstractCorpus(inputdir, parser, cache_path="/tmp/")

for i,doc in enumerate(corpus):
    for sentence in doc["sentences"]:
        print sentence
    break


