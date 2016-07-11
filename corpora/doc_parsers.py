import os
import glob
import codecs

class Document(object):
    def __init__(self, doc_id, text, sentences=[], attributes={}, annotations=[]):
        self.doc_id = doc_id
        self.text = text
        self.sentences = sentences
        self.annotations = annotations
        self.attributes = attributes
        
    def __repr__(self):
        return "Document [{}] {}...".format(self.doc_id,self.text[0:10])
        
                
class DocParser(object):
    def __init__(self, inputpath, encoding="utf-8"):
        self.inputpath = inputpath
        self.encoding=encoding
          
    def __iter__(self):
        for fpath in self._get_files(self.inputpath):
            for doc in self._parse_file(fpath):
                yield doc
    
    def _parse_file(self, filename):
        raise NotImplementedError

    def _get_files(self, file_input):
        if type(file_input) is list:
            return file_input
        elif os.path.isfile(file_input):
            return [file_input]
        else:
            return glob.glob(file_input)

    def _filename2uid(self, s):
        return os.path.basename(s).split(".")[0]
    
    
class TextFileParser(DocParser):
    '''Parse plain text documents, assuming one document per file'''
    def __init__(self, inputpath, doc_id_func=None, encoding="utf-8"):
        super(TextFileParser, self).__init__(inputpath, encoding)
        self.doc_id_func = self._filename2uid if not doc_id_func else doc_id_func
    
    def _parse_file(self, filename):
        uid = self.doc_id_func(filename)
        text = u''.join(codecs.open(filename,"rU",self.encoding).readlines())
        yield Document(doc_id=uid, text=text)


class RowParser(DocParser):
    '''One document per tab delimited row'''
    def __init__(self, inputpath, doc_id_func=None, delimiter="\t", header=False, 
                 text_columns=['text'], encoding="utf-8"):
        super(RowParser, self).__init__(inputpath, encoding)
        self.header = header
        self.doc_id_func = (lambda row:row[0]) if not doc_id_func else doc_id_func
        self.delimiter = delimiter
        self.text_columns = text_columns
        
    def _parse_file(self, filename):
        with codecs.open(filename,"rU",self.encoding) as f:
            for i,line in enumerate(f):
                row = line.split(self.delimiter)
                if i == 0 and self.header:
                    colnames = row
                    continue
                uid = self.doc_id_func(row)
                text = u' '.join([row[col if not self.header else colnames.index(col)] \
                                  for col in self.text_columns])
                attributes = dict(zip(colnames if self.header else range(len(row)),row))
                yield Document(doc_id=uid, text=text, attributes=attributes)
                           
                 


class BioCParser(DocParser):
    '''
    "BioC is a simple format to share text data and annotations. It allows a large 
    number of different annotations to be represented. We provide simple code to 
    hold this data, read it and write it back to XML, and perform some 
    sample processing."
    
    http://bioc.sourceforge.net/
    '''
    pass