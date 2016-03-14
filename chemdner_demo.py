import umls
from ddlite import *
from datasets import *

# ChemDNER Corpus v1.0
parser = SentenceParser(absolute_path=True)
corpus = ChemdnerCorpus('datasets/chemdner_corpus/',parser=parser)

documents = {pmid:corpus[pmid]["sentences"] for pmid in corpus.cv["training"].keys()[:10]}
print("Loaded %s training documents" % len(documents))

# We can label candidates in two ways:
# 1: Use a dictionary, either loaded from a text file


# 2: Or we can dynamically use the UMLS as our dictionary. The disadvantage
# beyond a speed hit, is that the UMLS is noisy, resulting in a many false
# positive matches that then need to be filtered out. 
extractor1 = umls.UmlsMatch('C',semantic_types=["Substance"],ignore_case=True)
#extractor2 = DictionaryMatch('C',ignore_case=True)

for pmid in documents:
    doc = documents[pmid]
    entities = Entities(extractor1,doc)
    
    
    #if pmid in corpus.annotations:
    #    print [x.text for x in corpus.annotations[pmid] ]



def rule1(s):
    return 0

def rule2(s):
    return 1


# Positive examples


# Negative examples

