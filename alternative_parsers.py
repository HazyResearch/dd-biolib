'''
Alterative parser implemenations. 
1: A dumb rule-based tokenizer. No parsing or sentence boundary detection. 
   Only use for debugging.
2: Spacy parser. Faster than CorenNLP. For ChemDNER extraction, tokenization
   performs slightly better.
   
'''
from collections import namedtuple
from spacy.en import English
import re

# python -m spacy.en.download

Sentence = namedtuple('Sentence', 'words, lemmas, poses, dep_parents, dep_labels, sent_id, doc_id')

def dependency_labels_to_root(token):
    '''Walk up the syntactic tree, collecting the arc labels.'''
    dep_labels = []
    while token.head is not token:
        dep_labels.append(token.dep)
        token = token.head
    return dep_labels


class SentenceParser:
    
    def __init__(self):
        pass
    
    def parse(self, f):
        raise NotImplementedError()


class RuleParser:
    
    def __init__(self, num_threads=4):
        pass

    def parse(self, doc, doc_id=None):

        doc = re.sub("([;:])+",r" \1 ", doc)
        doc = re.sub(" \("," ( ",doc)
        doc = re.sub("\)([ .])",r" ) \1",doc)
        doc = re.sub("/"," / ", doc)
        doc = re.sub("([?!])",r" \1 ", doc)
        
        words = doc.strip().split()
        tokens = []
     
        for w in words:
            if w[-1] in [".",","] and len(w[:-1]) > 2 and not w[:-1].isdigit():
                tokens += re.sub("([.,])+",r" \1",w).split() 
            else:
                tokens += [w]
                
        s = Sentence(words=tokens, lemmas=tokens, poses=tokens, 
                         dep_parents=['0'] * len(tokens), dep_labels=tokens, 
                         sent_id=1, doc_id=doc_id)
        yield s
        
        
class SpacyParser:
    '''https://spacy.io/#example-use
    '''
    def __init__(self, num_threads=4):
        
        self.nlp = English(tokenizer=True, parser=None, tagger=True,
                           entity=None, matcher=None)
    
    def parse(self, doc, doc_id=None):
        """Parse a raw document as a string into a list of sentences"""
        if len(doc.strip()) == 0:
            return
        
        doc = doc.decode("utf-8")
        
        for i, doc in enumerate(self.nlp.pipe([doc], batch_size=50, n_threads=4)):
            assert doc.is_parsed
                    
        for sent_id, sent in enumerate(doc.sents):
            
            tokens = [t for t in sent]
            lemmas = [self.nlp.vocab.strings[t.lemma] for t in tokens]
            poses = [self.nlp.vocab.strings[t.tag] for t in tokens]
            dep_labels = [self.nlp.vocab.strings[t.dep] for t in tokens]
            dep_parents = [t.head.idx for t in tokens]
            words = [t.text for t in sent]
            
            words = [t.encode("ascii",errors="ignore") for t in words]
            lemmas = [t.encode("ascii",errors="ignore") for t in lemmas]
            poses = [t.encode("ascii",errors="ignore") for t in poses]
            
            s = Sentence(words=words,lemmas=lemmas,poses=poses, 
                         dep_parents=dep_parents, dep_labels=dep_labels, 
                         sent_id=sent_id, doc_id=doc_id)

            yield s
