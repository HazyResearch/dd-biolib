import codecs
import itertools
from ddlite import *
from ddlite.ddbiolib.datasets import PubMedCentralCorpus

#
# PubMedCentral Corpus
#
ROOT = "/users/fries/pmc-sample/"
inputdir = "/Users/fries/Desktop/articles.I-N/"
parser = SentenceParser()
corpus = PubMedCentralCorpus(inputdir, parser, cache_path="/Users/fries/Desktop/pmc_cache/")

for uid in corpus.documents.keys()[0:10]:
    sentences = corpus[uid]["sentences"]
    #print "parsed {}".format(uid)
    outfile = uid.replace("/Users/fries/Desktop/","{}".format(ROOT))
    print outfile
    
    
    