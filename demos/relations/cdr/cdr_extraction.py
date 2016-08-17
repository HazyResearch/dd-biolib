'''
This demo requires access to the  "BioCreative V Chemical-Disease Relation (CDR) Task Corpus"
(http://www.biocreative.org/resources/corpora/biocreative-v-cdr-corpus/) available after 
signing up for an account at http://www.biocreative.org 

This script extracts candidate relations from sentences. It assumes we  
already have an input candidate set of entities for diseases and chemicals. 
This can either be an:

1) Oracle set (all gold/true mentions)

2) Pretagged set using PubTator, DNorm, tmChem, etc. 

@author: jason-fries [at] stanford [dot] edu
'''
import sys
import itertools
from ddlite import *
from datasets import CdrCorpus


class AnnotationMatcher(CandidateExtractor):
    '''Use a set of pre-tagged named entities to create candidate matches.'''
    def init(self):
        # Load opts- this is from the kwargs dict
        self.label          = self.opts['label']
        self.annotations    = self.opts['annotations']
        # create label index

    def _(self,doc):
        '''Ground truth annotation index'''
        entity_idx = {}
        for doc_id in self.annotations:
            entity_idx[doc_id] = {}
            doc = self.__getitem__(pmid)
            for sentence,tags in zip(doc["sentences"],doc["tags"]):
                if sentence.sent_id not in label_idx[pmid]:
                    label_idx[pmid][sentence.sent_id] = {}
                for text,offset in tags:
                    label_idx[pmid][sentence.sent_id][offset] = text
        return label_idx
    

    def _apply(self, s, idxs=None):
        ''' '''
        if doc_id not in self.annotations:
            return
            

SET = "training"
ORACLE = False

corpus = CdrCorpus(path="corpus/", cache_path="corpus/cache/")

for doc_id in corpus.cv[SET]:
    print corpus[doc_id]["tags"]
    print corpus[doc_id]["relations"]
    for s in corpus[doc_id]["sentences"]:
        print s
    #for label in corpus.annotations[doc_id]:
    #    print label
    
sys.exit()

sentences = [corpus[doc_id]["sentences"] for doc_id in corpus.cv[SET]]
sentences = sentences = list(itertools.chain.from_iterable(sentences))

for s in sentences:
    print s.doc_id, s.sent_id, s.words
    break

#if ORACLE:
    