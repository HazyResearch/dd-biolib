import itertools

class Corpus(object):
    '''Simple iterator class for loading and parsing documents'''
    def __init__(self, doc_parser, text_parser=None, attributes={}):
        self.doc_parser = doc_parser
        self.text_parser = text_parser
        self.attributes = attributes
        
    def __getitem__(self,key):
        doc = self.doc_parser.__getitem__(key)
        doc.sentences = self.text_parser.parse(doc.text,doc.doc_id) if self.text_parser else []
        return doc
    
    def __iter__(self):
        for doc in self.doc_parser:
            doc.sentences = self.text_parser.parse(doc.text,doc.doc_id) if self.text_parser else []
            yield doc
    
    def get_sentences(self,doc_ids=None):
        sentences = [doc.sentences for doc in self if not doc_ids or doc.doc_id in doc_ids]
        return list(itertools.chain.from_iterable(sentences)) 


