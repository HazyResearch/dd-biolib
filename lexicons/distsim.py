import re
from sklearn.neighbors import *
from collections import defaultdict
from gensim.models.word2vec import Word2Vec
from ddlite import Matcher, DictionaryMatch

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