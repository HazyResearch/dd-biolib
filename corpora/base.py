from .doc_parsers import TextFileParser
    
class Corpus(object):
    '''Simple iterator class for loading and parsing documents'''
    def __init__(self, doc_parser, text_parser=None, 
                 attributes={}, encoding="utf-8"):
        self.doc_parser = doc_parser
        self.text_parser = text_parser
        self.attributes = attributes
        self.encoding = encoding
    
    def __getitem__(self,key):
        raise ValueError("Indexing not supported, use IndexedCorpus or DatabaseCorpus")
        
    def __iter__(self):
        for doc in self.doc_parser:
            doc.sentences = self.text_parser.parse(doc.text,doc.doc_id) if self.text_parser else []
            yield doc


