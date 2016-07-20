import os
import glob
import codecs
import subprocess
from collections import namedtuple
from ..utils import download
from ..corpora import Corpus,Document,DocParser
from ..parsers import CoreNlpParser,PickleSerializedParser

class NcbiDiseaseParser(DocParser):
    '''
    The NCBI disease corpus is fully annotated at the mention and concept level 
    to serve as a research resource for the biomedical natural language processing 
    community.     -- from http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/
                    
        793 PubMed abstracts
        6,892 disease mentions
        790 unique disease concepts
    
    '''
    def __init__(self, inputpath=None):
        super(NcbiDiseaseParser, self).__init__(inputpath, "utf-8")
        if not inputpath:
            self.inputpath = "{}/data/ncbi_disease_corpus/".format(os.path.dirname(__file__))
        else:
            self.inputpath = inputpath
        self._docs = {}
        self._download()
        self._preload()
        
    def _download(self):
        '''If corpus files aren't available, automatically download them'''
        url = "http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/"
        filelist = ["NCBItrainset_corpus.zip","NCBItestset_corpus.zip","NCBIdevelopset_corpus.zip"]
        for fname in filelist:
            outfname = "{}{}".format(self.inputpath,fname)
            if os.path.exists(outfname):
                continue
            print("Downloading NCBI Disease Corpus dataset [{}]...".format(os.path.basename(outfname)))
            download(url+fname,outfname)
            cwd = os.getcwd()
            os.chdir(self.inputpath)
            subprocess.call(["unzip", outfname])
            os.chdir(cwd)
            
    def _preload(self):
        '''Load entire corpus into memory'''
        Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])
        
        cvdefs = {"NCBIdevelopset_corpus.txt":"development",
                  "NCBItestset_corpus.txt":"testing",
                  "NCBItrainset_corpus.txt":"training"}
        
        filelist = glob.glob("%s/*.txt" % self.inputpath)

        for fname in filelist:
            setname = cvdefs[fname.split("/")[-1]]
            documents = []
            with codecs.open(fname,"rU",self.encoding) as f:
                doc = []
                for line in f:
                    row = line.strip()
                    if not row and doc:
                        documents += [doc]
                        doc = []
                    elif row:
                        row = row.split("|") if (len(row.split("|")) > 1 and 
                                                 row.split("|")[1] in ["t","a"]) else row.split("\t")
                        doc += [row]
                documents += [doc]
      
            for doc in documents:
                pmid,title,abstract = doc[0][0],doc[0][2],doc[1][2]
                text = "%s %s" % (title, abstract)
                attributes = {"set":setname,"title":title,"abstract":abstract}            
                attributes["annotations"] = []
                
                # load annotation tuples
                for row in doc[2:]:
                    pmid, start, end, mention, mention_type, duid = row
                    start,end = int(start),int(end)
                    text_type = "T" if end <= len(title) else "A" 
                    label = Annotation(text_type, start, end, mention, mention_type)
                    attributes["annotations"] += [label]

                doc = Document(pmid,text,attributes=attributes)
                self._docs[pmid] = doc
    
    def __getitem__(self,key):
        return self._docs[key]
    
    def _load(self, filename):
        for pmid in self._docs:
            yield self._docs[pmid]


def load_corpus():
    '''Load NCBI Disease Corpus
    '''
    # init cache directory and parsers
    cache_dir = "{}/data/ncbi_disease_corpus/cache/".format(os.path.dirname(__file__))
    doc_parser = NcbiDiseaseParser()
    text_parser = PickleSerializedParser(CoreNlpParser(),rootdir=cache_dir)
    
    # create cross-validation set information
    attributes = {"sets":{"testing":[],"training":[],"development":[]}}
    for pmid in doc_parser._docs:
        setname = doc_parser._docs[pmid].attributes["set"]
        attributes["sets"][setname]+= [pmid]
      
    return Corpus(doc_parser,text_parser,attributes)


