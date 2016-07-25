import bz2
import sys
import csv
import re
import codecs
import numpy as np
import itertools
import cPickle
import ddlite
from ddlite import SentenceParser,Entities
from ddlite import Union, DictionaryMatch, RegexNgramMatch, CandidateExtractor
from utils import unescape_penn_treebank
from datasets import NcbiDiseaseCorpus

class NounPhraseMatcher(CandidateExtractor):
    
    def init(self):
        self.pattern = re.compile("(NN[SP]*|JJ[S]*|DT|CC)") 
        self.label         = self.opts['label']
        self.match_attrib  = self.opts.get('match_attrib', 'words')
        self.ignore_case   = self.opts.get('ignore_case', True)
        self.longest_match = self.opts.get('longest_match', True) 
       
    def _apply(self, s, idxs=None):
        
        noun_phrases = []
        np = []
        for i,tag in enumerate(s.poses):
            if self.pattern.search(tag):
                np += [(i,tag)]
            elif np:
                noun_phrases += [np]
                np = []
         
        for np in noun_phrases:
            
            while np and re.search("(CC|[PW]*DT)",np[0][1]):
                np.pop(0)
                
            while np and re.search("(CC|[PW]*DT)",np[-1][1]):
                np.pop()
            
            if not np or re.search("JJ[RS]*",np[0][1]):
                continue
            
            idxs,poses = zip(*np)
            
            #print np, s.words[min(idxs):max(idxs)+1]
            #print "----"
            yield list(idxs), 'x'


np_regex = re.compile("^((NN[SP]*|JJ[S]*|DT|CC)\s*)+$") 
pos_regex = re.compile("(NN[SP]*|JJ[S]*|DT|CC)")

np_regex = re.compile("^((NN[SP]*|JJ[S]*|DT)\s*)+$")
pos_regex = re.compile("(NN[SP]*|JJ[S]*|DT)") 

np_regex = re.compile("^((NN[SP]*|JJ[S]*|DT)\s*)+$")
pos_regex = re.compile("(NN[SP]*|JJ[S]*|DT)") 




def is_noun_phrase(t):
    seq = " ".join(t)
    return np_regex.search(seq) is not None


def multiset_intersection(a,b):
    a = [t for t in a]
    b = [t for t in b]
    c = []
    while len(a) > 0 and len(b) > 0:
        i = a.pop(0)
        if i in b:
            c += [i]
            b.remove(i)
    return c
    
    
    

def noun_phrases(s):    
    
    noun_phrases = []
    np = []
    for i,tag in enumerate(s.poses):
        if pos_regex.search(tag):
            np += [(i,tag)]
        elif np:
            noun_phrases += [np]
            np = []
    
    for np in noun_phrases:
        while np and re.search("(CC|[PW]*DT)",np[0][1]):
            np.pop(0)
        while np and re.search("(CC|[PW]*DT)",np[-1][1]):
            np.pop()

        if not np:
            continue
        idxs,_ = zip(*np)
        
        
        # remove stopwords
        idxs = list(idxs)
        while idxs and s.lemmas[idxs[0]] in left_args:
            idxs.pop(0)
        while idxs and s.lemmas[idxs[-1]] in right_args:
            idxs.pop()
        
        if not idxs:
            continue
        
        yield [s.words[i] for i in idxs]



ROOT = "/Users/fries/dd-bio-examples/"
INDIR = "/Users/fries/Desktop/ncbi/"
OUTDIR = "/Users/fries/Desktop/ncbi/candidates/"


pubterms = ["background","methods","introduction"]

left_args = ["novel","symptomatic","common","severe","major","primary",
             "distinct","gross","progressive","late-onset","classical",
             "recurrent","significant","moderate","mild","subsequent"]
left_args += ["dog","mouse","human"]
left_args += pubterms


right_args = ["gene","mutation","locus","allele","cell","line", "heterozygotes","pairs",
              "type","protein","phenotype","deletion", "region","codon", "inhibition","inhibitor",
              "chromosome", "gene", "expression","suppressor","wild-type"]

right_args += ["individual","patient","carrier","parent",'offspring',"cases"]
right_args += ["dog","mouse","human","female","male","model"]
right_args += pubterms
#consistent, associated, caused,characterized


# <Qualitative Concept>


# --------------------------------------------
# Load/Parse Corpus
# --------------------------------------------

cache = "{}/cache/".format(INDIR)
infile = "{}/corpora/".format(INDIR)
holdouts = ["training"]

corpus = NcbiDiseaseCorpus(infile, parser=None, cache_path=cache)

dev_set = list(itertools.chain.from_iterable([corpus.cv[setdef].keys() for setdef in holdouts]))
tagged  = [(corpus[doc_id]["sentences"],corpus[doc_id]["tags"]) for doc_id in dev_set]

n,p,N = 0.0,0.0,0.0
num_noun_phrases = 0

for doc,labels in tagged:
    
    sentences = zip(doc,labels)
    for s,tags in zip(doc,labels):
        np_ners,ners = [],[]
        for text,span in tags:
            seq = s.poses[min(span):max(span)]
            if is_noun_phrase(seq):
                phrase = s.words[min(span):max(span)]
                np_ners += [phrase]
                n += 1
            ners += [s.words[min(span):max(span)]]
            N += 1
        
        # extract sentence noun phrases
        np = [np for np in noun_phrases(s)]
        np = map(tuple,np)
        num_noun_phrases += len(np)
        
        # NERs vs. NP NERs
        np_ners = map(tuple,np_ners)
        ners = map(tuple,ners)
        
        # exact NER / NP sequence match
        intersection = multiset_intersection(np,np_ners)
        p += len(intersection)
        
        # missed noun phrases
        mismatched = [x for x in np_ners if x not in intersection]
        difference = [x for x in np if x not in intersection]
        if mismatched:
        
            print "MISSED", mismatched  
            print "FP NP ", difference
            print zip(s.words, s.poses)
            print "----------"
        
        
            
#Population Group
#Family Group   
        
print n/N, n, N
print p/N, p, N
print num_noun_phrases

# --------------------------------------------
# Match Candidates
# --------------------------------------------
longest_match = True

matcher = NounPhraseMatcher(label='NP')

gold_labels = []
scores = {"num_candidates":0, "num_cand_tokens":0,"class_balance":{}}

for cv_set in ["training"]:
  
    sentences = [corpus[doc_id]["sentences"] for doc_id in corpus.cv[cv_set]]
    sentences = list(itertools.chain.from_iterable(sentences))
    