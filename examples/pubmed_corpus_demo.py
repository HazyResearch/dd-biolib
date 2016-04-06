import itertools
from ddlite import *
from datasets import PubMedAbstractCorpus

#
# PubMed Abstract Corpus
#
inputdir = "../datasets/chemdner_corpus/silver.abstracts.txt"
parser = SentenceParser()
corpus = PubMedAbstractCorpus(inputdir, parser, cache_path="cache/pubmed/")

sentences = [corpus[uid]["sentences"] for uid in corpus.documents.keys()[0:10]]
sentences = list(itertools.chain.from_iterable(sentences))

# matchers
dictfile = "../datasets/dictionaries/umls/anatomy.txt"
anatomy = [line.strip().split("\t")[0] for line in open(dictfile,"rU").readlines()]
matcher = DictionaryMatch('C', anatomy, ignore_case=True)

# dump candidates
candidates = Entities(sentences, matcher)
candidates.dump_candidates("cache/pmc-ortho-candidates.pkl")

print "Found %d candidates" % len(candidates)
for i in range(100):
    print candidates[i]
