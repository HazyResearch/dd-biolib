from ddlite import *
import itertools
from datasets import PubMedCentralCorpus

#
# PubMedCentral Corpus
#
inputdir = "../datasets/pmc_orthopedics_subset/"
parser = SentenceParser()
corpus = PubMedCentralCorpus(inputdir, parser, cache_path="cache/pmc_ortho/")

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


#
# If you need specifc parts of the PMC XML document, use these iteration patterns
#
'''        
# look at specific metadata
for i,doc in enumerate(corpus):
    for attribute in doc["metadata"]:
        print "%s: %s" % (attribute, doc["metadata"][attribute])
    break

# PMC articles also have structure which is useful to consider
# e.g., only looking at text from the "Methods and Materials" section 
for i,doc in enumerate(corpus):
    for title,section in zip(doc["section-titles"],doc["sections"]):
        for sentence in section:
            print "******%s******" % title, sentence 
    break
'''
