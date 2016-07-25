from collections import namedtuple
'''
Sentence = namedtuple('Sentence', ['words', 'lemmas', 'poses', 'dep_parents',
                                   'dep_labels', 'sent_id', 'doc_id', 'text',
                                   'token_idxs', 'doc_name'])
'''
Sentence = namedtuple('Sentence', ['id', 'words', 'lemmas', 'poses', 'dep_parents',
                                   'dep_labels', 'sent_id', 'doc_id', 'text',
                                   'char_offsets', 'doc_name'])

class SentenceParser(object):
    def __init__(self, tok_whitespace=False):
        self.tok_whitespace = tok_whitespace
    
    def parse(self, s, doc_id=None, doc_name=None):
        raise NotImplementedError()
    
    def parse_docs(self, docs):
        raise NotImplementedError()