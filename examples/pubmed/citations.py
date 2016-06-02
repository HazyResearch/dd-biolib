import sys
from ddlite import SentenceParser
from datasets import PubMedCentralCorpus

# PubMedCentral Corpus
inputdir = "/Users/fries/bak/dd-bio-examples/data/documents/pmc-ortho/"

parser = SentenceParser()
corpus = PubMedCentralCorpus(inputdir, parser=None, cache_path=None)

for i,doc in enumerate(corpus):
    references = doc.get("references",[])
    references = [citation["pub-id"] for citation in references if "pub-id" in citation]
    print references[0:5]
