import os
import glob
import cPickle
import codecs
from collections import namedtuple

Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])
#CdrAnnotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type', "mesh_ids", "mesh_names"])

CdrEntity = namedtuple('CdrEntity', ['text_type','start','end','text','mention_type', "mesh_ids", "mesh_names"])

Document = namedtuple('Document',['doc_id','title','body','sentences'])

class Corpus(object):
    
    def __init__(self, path, parser, encoding="utf-8"):
        self.path = path
        self.parser = parser
        self.encoding = encoding

    def _get_files(self):
        if os.path.isfile(self.path):
            return [self.path]
        elif os.path.isdir(self.path):
            return [os.path.join(self.path, f) for f in os.listdir(self.path)]
        else:
            return glob.glob(self.path)

class PlainTextCorpus(Corpus):
    
    def __init__(self, path, parser, cache_path=None):
        '''
        PubMed abstracts corpus. File format assumed to be
        PMID title body
        '''
        super(PlainTextCorpus, self).__init__(path, parser)
        
        self.documents = {}
        self._load_files()
        self.cache_path = cache_path
        
    def __iter__(self):
        for pmid in self.documents:
            yield self.__getitem__(pmid)
            
    def __getitem__(self, uid):
        
        pkl_file = "%s/%s.pkl" % (self.cache_path, uid)
        # load cached parse if it exists  
        if os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                self.documents[uid] = cPickle.load(f)
        else:
            sentences = [s for s in self.parser.parse(self.documents[uid]["text"])]
            self.documents[uid]["sentences"] = sentences
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[uid], f)
               
        return self.documents[uid]
        
    def _load_files(self):
        
        filelist = glob.glob("{}/*.txt".format(self.path))
        for fname in filelist:
            uid = fname.split("/").rstrip(".txt")
            self.documents[uid] = {}
            self.documents[uid]["text"] = "".join(codecs.open(self.path,"r").readlines())
