import re
import sys
import lxml
import cPickle
from datasets import *
from collections import namedtuple

class PubMedAbstractCorpus(Corpus):
    
    def __init__(self, path, parser, cache_path=None):
        '''
        PubMed abstracts corpus. File format assumed to be
        PMID title body
        '''
        super(PubMedAbstractCorpus, self).__init__(path, parser)
        
        self.documents = {}
        self._load_files()
        self.cache_path = cache_path
        
    def __iter__(self):
        for pmid in self.documents:
            yield self.__getitem__(pmid)
            
    def __getitem__(self,pmid):
        """Use PMID as key and load parsed document object"""
        pkl_file = "%s/%s.pkl" % (self.cache_path, pmid)
        
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
               
        return self.documents[pmid]
        
    def _load_files(self):
        
        docs = [d.strip().split("\t") for d in open(self.path,"r").readlines()]
        docs = {pmid:{"title":title,"body":body,"pmid":pmid} for pmid,title,body in docs}
        self.documents.update(docs)
        
        
        
class PubMedCentralCorpus(Corpus):
    '''PubMed Central Open Access Subset
    '''
    def __init__(self, path, parser, cache_path="/tmp"):
        
        super(PubMedCentralCorpus, self).__init__(path, parser)
        
        self.documents = {}
        self._load_files()
        self.cache_path = cache_path
        
    def __iter__(self):
        
        for uid in self.documents:
            yield self.__getitem__(uid)
            
    def __getitem__(self, uid):
        
        # load cached version
        pkl_file = "%s/%s.pkl" % (self.cache_path,uid.split("/")[-1]) if self.cache_path else None
        
        if pkl_file and os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                document = cPickle.load(f)
                
        elif pkl_file:
            document = self._parse_xml(uid)
            self._preprocess(document)
            
            with open(pkl_file, 'w+') as f:
                cPickle.dump(document, f)
                
        else:
            document = self._parse_xml(uid)
            self._preprocess(document)
        
        return document    
        
    def _preprocess(self,document):  
        
        if "abstract-text" in document:
            content = document["abstract-text"]#.decode("utf-8","ignore").encode("utf-8")
            #print(type(content))
            document["abstract"] = [s for s in self.parser.parse(content)]
        
        if "abstract-short-text" in document:
            content = document["abstract-short-text"]#.encode("utf-8","ignore")
            document["abstract-short"] = [s for s in self.parser.parse(content)]
        
        document["sections"] = []
        for section in document["section-text"]:
            section = section.strip()
            try:
                section = [s for s in self.parser.parse(section)] #.encode("utf-8","ignore")
                document["sections"] += [section]
            except Exception as e:
                print "CoreNLP parsing exception %s" % section     
                print e  
                #sys.exit()
                
        # merge all sentences into a single array
        document["sentences"] = []
        if "abstract" in document:
            for section in document["abstract"]:
                document["sentences"] += section
            
        for section in document["sections"]:
            document["sentences"] += section
        
        
    def _parse_xml(self,uid):
        '''Parse PMC XML format, pull out relevant metadata
        '''
        doc = lxml.etree.parse(uid)
        document = {"section-text":[],"section-titles":[],"metadata":{}}
        
        #
        # Article metadata is more complicated -- we just pull out a small subset
        #
        root = doc.xpath("//article/front/journal-meta")
        if root:        
            for node in root[0].iter('*'):
                if len(node) == 0:
                    document["metadata"][node.tag] = node.text
    
        root = doc.xpath("//article/front/article-meta")
        if root:
            article_ids = doc.xpath("//article/front/article-meta/article-id")
            for node in article_ids:
                tag = node.attrib["pub-id-type"]
                document["metadata"][tag] = node.text
            
            article_title = doc.xpath("//article/front/article-meta/title-group/article-title")
            for node in article_title:
                document["metadata"][node.tag] = node.text
            
            authors = doc.xpath("//article/front/article-meta/contrib-group/contrib")
            document["metadata"]["authors"] = []
            for node in authors:
                if node.attrib and node.attrib["contrib-type"] == "author":
                    author = []
                    for child in node.iter('*'):
                        if child.tag not in ["email","xref"] and child.text:
                            author += [child.text]
                    document["metadata"]["authors"] += [tuple(author)]
        
        #
        # Abstract
        #
        abstract = doc.xpath("//article/front/article-meta/abstract")
        if abstract:
            
            for node in abstract:
                content = []
                abstract_name = "abstract-text"
                if node.attrib and "abstract-type" in node.attrib:
                    abstract_name = "abstract-short-text" # % node.attrib["abstract-type"]
                
                for sec in node.iter('*'):
                    if not sec.text:
                        continue
                    content += [sec.text]
                    
                document[abstract_name] = " ".join(content)
                
        #
        # Document sections (always use first title as label)
        #
        sections = doc.xpath("//article/body/sec")
        for sec in sections:
            xpath = doc.getpath(sec)
            titles,content = [],[]
            
            for node in sec.iter('*'):
                node_xpath = doc.getpath(node)
                node_xpath = node_xpath.split("/") 
                
                if "title" in node.tag and node.text:
                    titles += [node.text]
                    content += [node.text]
                    
                # ignore tables
                #elif ("table" not in node_xpath or "caption" in node_xpath) and node.text:
                #    content += [node.text]
                
                elif node.text:
                    content += [node.text]
                
            content = " ".join( map(lambda x:re.sub("\s{2,}"," ",x), content)) 
            title = titles[0] if len(titles) > 0 else ""
            document["section-titles"] += [title]
            document["section-text"] += [content]
        
        return document
       
    def _load_files(self):
        
        self.documents = {fname:0 for fname in glob.glob("%s/*/*.nxml" % self.path)}
          
