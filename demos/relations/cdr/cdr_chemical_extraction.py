# -*- coding: utf-8 -*-
import bz2
import sys
import codecs
import itertools
from ddlite import *
from datasets import CdrCorpus


def build_hypenated_dict(labels,stopwords={}):
    hypenated = {}
    for label in labels:
        pmid,sent_id,idxs,span,text = label
        mention = [corpus[pmid]["sentences"][sent_id].words[i] for i in idxs]
        m = re.search("\w+[-]([A-Za-z]{3,})"," ".join(mention))
        if m:
            t = m.group(1).lower()
            if t in stopwords:
                continue
            hypenated[t] = hypenated.get(t,0) + 1
    
    return [phrase for phrase,n in sorted(hypenated.items(),key=lambda x:x[1],reverse=1)]

def load_dictionary(filename, col_idx=0, delimiter="\t", stopwords={}):
    '''Load dictionary file (optionally compressed with bzip2)'''
    if filename.split("/")[-1].split(".")[-1] == "bz2":
        d = {line.strip().split(delimiter)[col_idx]:1 for line in 
             bz2.BZ2File(filename, 'rb').readlines()}
    else:
        d = {line.strip().split(delimiter)[col_idx]:1 for line in 
             codecs.open(filename, 'rb',"utf-8", errors="ignore").readlines()}
    d = {word:1 for word in d if not word.isupper() and word.lower() not in stopwords}
    return d

####################################################################
# Load/Parse Corpus
####################################################################
SET = "training"

corpus = CdrCorpus(path="corpus/", cache_path="corpus/cache/")
sentences = [corpus[doc_id]["sentences"] for doc_id in corpus.cv[SET]]
sentences = list(itertools.chain.from_iterable(sentences))

'''
terms = []
for doc_id in corpus.cv[SET]:
    terms += [t.text for t in corpus.annotations[doc_id]]
oracle = dict.fromkeys(terms)
'''

####################################################################
# Match Candidates
####################################################################

stopwords = load_dictionary("dicts/stopwords.txt")
stopwords.update(dict.fromkeys(["V","IV","III","II","I","cm","mg","pH"]))

#ChEBI chemical ontology and UMLS substances
dictionary = load_dictionary("dicts/chemicals/names.tsv", col_idx=5, stopwords=stopwords)
dictionary.update(load_dictionary("dicts/chemicals/umls.all.substances.bz2", 
                                  stopwords=stopwords))
dictionary.update(load_dictionary("dicts/chemicals/umls.all.substances.penn-treebank.txt",
                                  stopwords=stopwords))

# filter out some noisy dictionary matches
for phrase in dictionary.keys():
    if re.search("(^[A-Za-z0-9][.-]*$)",phrase):
        del dictionary[phrase]

matcher = DictionaryMatch(label='Ch', dictionary=dictionary, ignore_case=True)

candidates = Entities(sentences, matcher)
num_cands = candidates.num_candidates()
num_sents = len(sentences)
outfname = "candidates/chemicals/chemical-candidates.s{}.c{}.pkl".format(num_sents,num_cands)
candidates.dump_candidates(outfname)
print("Wrote {}".format(outfname))


####################################################################
# Candidate Recall
####################################################################

holdout_ids = corpus.cv[SET].keys()
prediction = [1] * len(candidates)
scores = corpus.score(candidates, prediction, "chemicals", holdout_ids )
print "Candidate Recall:  {:.3f}".format(scores["recall"])

tp,fp,fn = corpus.classification_errors(candidates, prediction, "chemicals", holdout_ids)
print "TP: {} FP: {} FN: {}".format(len(tp),len(fp),len(fn))

# print out some missed entities
for label in fn:
    pmid,sent_id,idxs,span,text = label
    mention = [corpus[pmid]["sentences"][sent_id].words[i] for i in idxs]
    #print text, mention

    
