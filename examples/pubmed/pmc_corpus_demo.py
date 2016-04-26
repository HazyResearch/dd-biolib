import codecs
import itertools
from ddlite import *
from datasets import PubMedCentralCorpus

#
# PubMedCentral Corpus
#
inputdir = "/Users/fries/Dropbox/deepdive-biomed/corpora/raw/pmc_orthopedics_subset/"

parser = SentenceParser()
corpus = PubMedCentralCorpus(inputdir, parser, cache_path="/Users/fries/desktop/cache/")

sentences = [corpus[uid]["sentences"] for uid in corpus.documents.keys()[0:1000]]
sentences = list(itertools.chain.from_iterable(sentences))

# dictionary matcher
dictfile = "/Users/fries/Code/fma_anatomy.txt"
anatomy = {line.strip().split("\t")[0]:1 for line in codecs.open(dictfile,"rU","utf-8").readlines()}

# remove stopwords
dictfile = "../datasets/dictionaries/chemdner/stopwords.txt"
stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
anatomy = {word:1 for word in anatomy if word not in stopwords}

matcher = DictionaryMatch(label='A', dictionary=anatomy, ignore_case=True)

# dump candidates
candidates = Entities(sentences, matcher)
candidates.dump_candidates("/users/fries/desktop/anatomy-pmc-ortho-candidates.pkl")

print "Found %d candidates" % len(candidates)
for i in range(100):
    print candidates[i]

sys.exit()
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
