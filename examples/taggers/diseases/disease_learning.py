import bz2
import sys
import cPickle
import numpy as np
import itertools
from ddlite import SentenceParser,DictionaryMatch,Entities,CandidateModel
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus
from sklearn.metrics import precision_score,recall_score

def find_duplicates(candidates):
    
    for i in range(0,len(candidates)):
        for j in range(i+1,len(candidates)):
            
            a = candidates[i]
            b = candidates[j]
            
            if a.idxs==b.idxs and a.doc_id==b.doc_id and a.sent_id==b.sent_id:
                print a.doc_id, a.sent_id, a.mention()
                print b.doc_id, b.sent_id, b.mention()
                print
           

def corpus_mention_summary(corpus):
    '''The raw corpus doesn't match the statistics provided at
    http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/corpus.html
    they report: 5148/791/961  we get 5145/787/960. The original stats
    are either from a different version of the corpus or wrong. Note errors:
        1) duplicate document in training data: PMID 8528200 (11 labels)
    '''
    # verify number of annotations
    for holdout in corpus.cv:
        doc_ids = corpus.cv[holdout]
        num_mentions = sum([len(corpus.annotations[doc_id]) for doc_id in doc_ids])
        print holdout,num_mentions, len(doc_ids)


ROOT = "../../../"
OUTDIR = "/users/fries/desktop/dnorm/"
CANDIDATE_DIR = "/Users/fries/debug/dd-bio-examples/candidates/jason/diseases/v4-oracle/"

cache = "/Users/fries/Desktop/dnorm/cache3/"
infile = "/Users/fries/Desktop/dnorm/disease_names/"

parser = None# SentenceParser()
corpus = NcbiDiseaseCorpus(infile, parser, cache_path=cache)

num_training = len(Entities("{}{}-ncbi-candidates.pkl".format(CANDIDATE_DIR,"training"))) 
num_developent = len(Entities("{}{}-ncbi-candidates.pkl".format(CANDIDATE_DIR,"development")))
num_testing = len(Entities("{}{}-ncbi-candidates.pkl".format(CANDIDATE_DIR,"testing")))


print num_training, num_developent
#candidates/jason/diseases/{}/training-ncbi-candidates.pkl


'''
# -------------------------------------------------------
# candidate recall
print "CANDIDATE RECALL"
prediction = len(candidates) * [1]
scores = corpus.score(candidates,prediction,holdout)
print scores
# -------------------------------------------------------
'''

cv = "development"
candidates = Entities("{}{}-ncbi-candidates.pkl".format(CANDIDATE_DIR,cv))
holdout = corpus.cv[cv].keys() 

prediction = np.load("/users/fries/desktop/ncbi-dev-predictions.npy")
prediction = prediction[num_training:]
gold_labels = corpus.gold_labels(candidates)

#prediction = [1] * len(candidates)

print len(candidates._candidates), len(prediction), len(gold_labels)

'''
# sklearn santity check (should match ddlite scores)
# -------------------------------------------------------
gold_labels = [1 if x==1 else 0 for x in gold_labels]
prediction = [1 if x==1 else 0 for x in prediction]
print "ddlite precision:", precision_score(gold_labels, prediction)
print "ddlite recall:   ", recall_score(gold_labels, prediction)
# -------------------------------------------------------
'''


#scores = corpus.score(candidates,prediction,holdout)
#print scores
corpus.error_analysis(candidates,prediction,holdout)


#774
#TP:637 FP:137 FN:150 True_N:787
