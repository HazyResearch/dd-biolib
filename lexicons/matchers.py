import re
import string
import bisect
import itertools
import numpy as np
from utils import *
from gensim.models.word2vec import Word2Vec
from sklearn.neighbors import *
from ddlite import Matcher,DictionaryMatch
from collections import defaultdict

class AllUpperNounsMatcher(Matcher):
    def __init__(self, label):
        self.label = label
        # Regex matcher to find named nouns in part-of-speech tags
        self._re_comp = re.compile("[A-Z]?NN[A-Z]?", flags=re.I)
    def apply(self, s):
        # Get parts-of-speech and words
        words = s.__dict__['words']
        pos = s.__dict__['poses']
        # Get all-cap words
        caps = set(idx for idx, w in enumerate(words) if w.upper() == w)
        # Convert character index to token index
        start_c_idx = [0]
        for s in pos:
            start_c_idx.append(start_c_idx[-1]+len(s)+1)
        # Find regex matches over phrase
        phrase = ' '.join(pos)
        for match in self._re_comp.finditer(phrase):
            # Get start index for tokens
            start = bisect.bisect(start_c_idx, match.start())-1
            # Check if word is capital, has more than two characters, and has a letter
            if start in caps and len(words[start]) > 2 and any(c.isalpha() for c in words[start]):
                yield [start], self.label




class RuleTokenizedDictionaryMatch(DictionaryMatch):
    '''Match entities using a simpler tokenizer rule than 
    what's provided by CoreNLP
    '''
    def __init__(self, label, dictionary, ignore_case=True,
                 tokenizer=lambda x:x.split()):
        super(RuleTokenizedDictionaryMatch, self).__init__(label, dictionary,
                                                             'words', ignore_case)
        self.tokenizer = tokenizer
        self.stopwords = {t:1 for t in ["on","can","is","to","a","was","at",
                                        "in","this","the","be","as","has"]}
        
    def align(self, a, b):

        #a_offsets = reduce(lambda x,y:x+y,[[i] * len(w) for i,w in enumerate(a)])
        #b_offsets = reduce(lambda x,y:x+y,[[i] * len(w) for i,w in enumerate(b)])
        a_offsets = list(itertools.chain.from_iterable([[i] * len(w) for i,w in enumerate(a)]))
        b_offsets = list(itertools.chain.from_iterable([[i] * len(w) for i,w in enumerate(b)]))
        
        mapping = {}
        for i,j in zip(a_offsets,b_offsets):
            if i not in mapping:
                mapping[i] = {}
            mapping[i][j] = 1
            
        return {i:mapping[i].keys() for i in mapping}
        
    
    def apply(self, s):
        '''
        # create offset mapping between chars and tokens
        # parser token offsets mapping top rule offsets. 
        '''
        # apply tokenizer to raw text
        seq = self.tokenizer(s.text.strip())
        offsets = [idx - s.token_idxs[0] for idx in s.token_idxs]
        tokens = unescape_penn_treebank(s.words)
        mapping = self.align(seq,tokens)
                
        # Loop over all ngrams
        for l in self.ngr:
            for i in range(0, len(seq)-l+1):
                phrase = ' '.join(seq[i:i+l])
                phrase = phrase.lower() if self.ignore_case else phrase
                
                if phrase in self.stopwords:
                    continue
                
                if phrase in self.dl[l]:
                    offsets = reduce(lambda x,y:x+y,[mapping[idx] for idx in range(i, i+l)])
                    yield list(range(min(offsets), max(offsets)+1)), self.label


class DistributionalSimilarityMatcher(Matcher):
    
    def __init__(self, label, embeddings, dictionary, knn=10, match_threshold=0.30,
                 metric='l2', ignore_case=True):
        
        self.label = label
        self.ignore_case = ignore_case
        self.match_threshold = int(match_threshold * knn)
        
        # load word embeddings
        if type(embeddings) is str:
            self.model = Word2Vec.load(embeddings)
        else:
            self.model = embeddings
        self.model.init_sims()  
    
        # build knn index
        self.knn = knn
        self.nbrs = NearestNeighbors(n_neighbors=self.knn+1, algorithm='ball_tree', metric=metric)
        self.nbrs.fit(self.model.syn0norm)
        
        # Split the dictionary up by phrase length (i.e. # of tokens)
        self.dl = defaultdict(lambda : set())
        for phrase in dictionary:
            self.dl[len(phrase.split())].add(phrase.lower() if ignore_case else phrase)
        self.dl.update((k, frozenset(v)) for k,v in self.dl.iteritems())
       
        max_ngr = max({len(term.split("_")):0 for term in self.model.vocab}.keys())
        self.ngr = range(1, max_ngr+1)
        self.ignore = re.compile("^[%s0-9]+$" % string.punctuation)
        self._cache = {}
        
    def apply(self, s):
         
        words = s.__dict__['words']
        poses = s.__dict__['poses']

        for l in self.ngr:
            for i in range(0, len(words)-l+1):
                phrase = ' '.join(words[i:i+l])
                pos_seq = set(poses[i:i+l])
                
                if not pos_seq.intersection(["NNS","NN","JJ"]):
                    continue
                
                phrase = phrase.lower() if self.ignore_case else phrase
                
                if phrase in self._cache and self._cache[phrase]:
                    yield list(range(i, i+l)), self.label
                elif phrase in self._cache:
                    continue
        
                # exclude punctuation
                if self.ignore.match(phrase):
                    continue
                
                if phrase in self.dl[l]:# or phrase.lower() in self.dl[l]:
                    continue
                
                m_phrase = phrase.replace(" ","_").strip()
                if m_phrase in self.model.vocab:
                    idx = self.model.vocab[m_phrase].index
                    
                    # predict it's semantic type 
                    vec = self.model.syn0norm[idx]
                    _,indices = self.nbrs.kneighbors(vec)
                    neighbors = [self.model.index2word[j] for j in indices.flatten()]
                    neighbors.remove(m_phrase)
                    
                    score = sum([1 for term in neighbors if term.lower() in self.dl[(len(term.split()))]])
                    
                    if score >= self.match_threshold:
                        self._cache[phrase] = True
                        yield list(range(i, i+l)), self.label
                    else:
                        self._cache[phrase] = False
        