import cPickle
#from ddlite import *
from datasets import *
from collections import namedtuple

Annotation = namedtuple('Annotation', 'text_type start end text mention_type')

class PubMedAbstract(object):

    def __init__(self, pmid, title, body):
        self.pmid = pmid
        self.title = title
        self.body = body
        self._entities = {}
        
        
class ChemdnerCorpus(Corpus):
        
    def __init__(self, path, parser):
        super(ChemdnerCorpus, self).__init__(path, parser)
        self.path = path
        self.cv = {"training":{},"development":{},"evaluation":{}}
        self.documents = {}
        self.annotations = {}
        
        self._load_files()
        
    
    def __getitem__(self,pmid):
        """Use PMID as key and load parsed document object"""
        
        
        pkl_file = "%scache/%s.pkl" % (self.path,pmid)
        
        # load cached parse if it exists
        if os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                self.documents[pmid] = cPickle.load(f)
        else:
            title = [s for s in self.parser.parse(self.documents[pmid]["title"])]
            body = [s for s in self.parser.parse(self.documents[pmid]["body"])]
            self.documents[pmid]["sentences"] = title + body
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[pmid], f)
                print('wrote', pmid, "at", pkl_file)
    
        return self.documents[pmid]
        
    
    def __iter__(self):
        
        for pmid in self.documents:
            yield self.__getitem__(pmid)
            
        
    def _load_files(self):
        '''
        ChemDNER corpus format (tab delimited)
        1- Article identifier (PMID)
        2- Type of text from which the annotation was derived (T: Title, A: Abstract)
        3- Start offset
        4- End offset
        5- Text string of the entity mention
        6- Type of chemical entity mention (ABBREVIATION,FAMILY,FORMULA,IDENTIFIERS,MULTIPLE,SYSTEMATIC,TRIVIAL)
        '''
        filelist = [(x,"%s%s.abstracts.txt" % (self.path,x)) for x in self.cv.keys()]
        for cv,fname in filelist:
            docs = [d.strip().split("\t") for d in open(fname,"r").readlines()]
            docs = {pmid:{"title":title,"body":body} for pmid,title,body in docs}
            self.cv[cv] = {pmid:1 for pmid in docs} 
            self.documents.update(docs)
        
        # load annotations
        filelist = [(x,"%s%s.annotations.txt" % (self.path,x)) for x in self.cv.keys()]
        for cv,fname in filelist:
            anno = [d.strip().split("\t") for d in open(fname,"r").readlines()]
           
            for item in anno:
                pmid, text_type, start, end, text, mention_type = item
                start = int(start)
                end = int(end)
                if pmid not in self.annotations:
                    self.annotations[pmid] = []
                self.annotations[pmid] += [Annotation(text_type, start, end, text, mention_type)]
            