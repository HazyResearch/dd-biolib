import bz2
import sys
import numpy as np
import itertools
from ddlite import SentenceParser,DictionaryMatch,Entities
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus

ROOT = "../../../"
INDIR = "/Users/fries/Desktop/dnorm/"
OUTDIR = "/users/fries/desktop/dnorm/"

def load_disease_dictionary():    
    dictfile = "{}/datasets/dictionaries/chemdner/stopwords.txt".format(ROOT)
    stopwords = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    
    dictfile = "{}/datasets/dictionaries/umls/umls_disease_syndrome.bz2".format(ROOT)
    diseases = {line.strip().split("\t")[0]:1 for line in bz2.BZ2File(dictfile, 'rb').readlines()}
    diseases = {word:1 for word in diseases if word not in stopwords}
    
    dictfile = "{}/datasets/dictionaries/ncbi/ncbi_training_diseases.txt".format(ROOT)
    terms = [line.strip().split("\t")[0] for line in open(dictfile).readlines()]
    diseases.update({word:1 for word in terms if word not in stopwords})
    
    return diseases


def create_corpus_dict(corpus, setdef="training"):
    '''Create dictionary using annotated corpus data'''
    
    dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in [setdef]]))
    documents = [(doc_id,corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set]
    
    print len(dev_set),len(corpus.documents)
    
    d = {}
    for pmid,doc,labels in documents:
        for i in range(0,len(doc)):
            for tag in labels[i]:
                mention = doc[i].words[tag[-1][0]:tag[-1][1]]
                v1 = "".join(unescape_penn_treebank(mention))
                v2 = tag[0].replace(" ","")
                if v1 != v2:
                    # problem with tokenization
                    #print " ".join(unescape_penn_treebank(mention)), tag
                    pass
                else:
                    d[" ".join(mention)] = 1                    
    return d

#
# Corpus
#

cache = "{}/cache3/".format(INDIR)
infile = "{}/disease_names/".format(INDIR)
holdouts = ["training","development","testing"]

parser = SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in holdouts]))
documents, gold_entities = zip(*[(corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set])

# summary statistics
gold_entity_n = sum([len(s) for s in list(itertools.chain.from_iterable(gold_entities))])
word_n = sum([len(sent.words) for sent in list(itertools.chain.from_iterable(documents))])
print("%d PubMed abstracts" % len(documents))
print("%d Disease gold entities" % gold_entity_n)
print("%d tokens" % word_n)

# training set dictionary
td = create_corpus_dict(corpus,"training")
create_corpus_dict(corpus,"development")
create_corpus_dict(corpus,"testing")
print len(td)

#
# Match Candidates
#
diseases = load_disease_dictionary()
matcher = DictionaryMatch(label='D', dictionary=diseases, ignore_case=True)

#
# Candidate Recall
#
num_candidates = 0
candidate_doc_index = []
candidate_gold_labels = []
tp, fn, gold = [],[],[]

splits = {}
# compute matched mention spans for each document
for pmid,sentences,labels in zip(dev_set,documents, gold_entities):
    
    holdout = "training"
    if pmid in corpus.cv["development"]:
        holdout = "development"
    elif pmid in corpus.cv["testing"]:
        holdout = "testing"
    
    match_idx = {i:{} for i in range(len(sentences))}
    matches = Entities(sentences, matcher)
    num_candidates += matches.num_candidates()
    
    # group candidates by sentence
    candidates = {}
    for idx,m in enumerate(matches):
        text = [m.words[i] for i in m.idxs]
        c = (" ".join(text), (m.idxs[0], m.idxs[0] + len(text))) 
        candidates[m.sent_id] = candidates.get(m.sent_id,[]) + [c]
        match_idx[m.sent_id][c] = idx
 
    # match to gold labels
    gold_labels = [0] * len(matches)
    for sent_id in range(len(sentences)):
        hits = [m for m in candidates[sent_id] if m in labels[sent_id]] if sent_id in candidates else []
        fn += [m for m in labels[sent_id] if m not in hits]
        tp += hits
        gold += labels[sent_id]
        # create gold labels for candidates
        for c in hits:
            gold_labels[match_idx[sent_id][c]] = 1
            
    candidate_gold_labels += gold_labels
    
    splits[holdout] = len(candidate_gold_labels)
    
print("Found %d candidate entities (%.2f%% of all tokens)" % (num_candidates, num_candidates/float(word_n)*100)) 
print("Candidate Recall: %.2f (%d/%d)" % (len(tp)/float(len(gold)), len(tp), len(gold)))
print("Candidate False Negative Rate (FNR) %.2f" % (1.0 - len(tp)/float(len(gold))))
print(splits.items())

candidate_gold_labels = np.asarray(candidate_gold_labels)
candidate_gold_labels = 2 * candidate_gold_labels - 1
np.save("{}/ncbi-candidates-gold.npy".format(OUTDIR),candidate_gold_labels)

# dump all candidates to a pickle file
sentences = list(itertools.chain.from_iterable(documents))
candidates = Entities(sentences, matcher)
candidates.dump_candidates("{}/all-ncbi-candidates.pkl".format(OUTDIR))


pred = [1] * len(candidates)
corpus.score(candidates,pred,corpus.cv["development"].keys())

