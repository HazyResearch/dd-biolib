import re
import os
import sys
import lxml
import codecs
import cPickle
from collections import namedtuple
from .base import *
from .tools import unescape_penn_treebank
from collections import defaultdict

class PubMedAbstractCorpus(Corpus):
    
    def __init__(self, path, parser, cache_path=None):
        '''
        PubMed abstracts corpus. File format assumed to be
        PMID title body'''
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
            doc_str = u"{} {}".format(self.documents[pmid]["title"],self.documents[pmid]["body"])
            sentences = [s for s in self.parser.parse(doc_str,doc_id=pmid)]
            self.documents[pmid]["sentences"] = sentences
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[pmid], f)
               
        return self.documents[pmid]
    
    def _clean(self,s):
        # remove non-breaking spaces
        s = re.sub(u'(\x00|\u00A0)',u' ',s).strip()
        return s
        
    
    def _load_files(self):
        docs = [self._clean(d.strip()).split("\t") for d in codecs.open(self.path,"rU",self.encoding).readlines()]
        docs = {pmid:{"title":title,"body":body,"pmid":pmid} for pmid,title,body in docs}
        #docs = {"23878724":docs["23878724"]}
        #print docs
        self.documents.update(docs)
       
        
        
class PubMedCentralCorpus(Corpus):
    '''PubMed Central Open Access Subset
    '''
    def __init__(self, path, parser, cache_path="/tmp"):
        
        super(PubMedCentralCorpus, self).__init__(path, parser)
        
        self.documents = {}
        self._load_files()
        self.cache_path = cache_path
        self.MAX_SENTENCE_LENGTH = 100 # in tokens
        
    def __iter__(self):
        
        for uid in self.documents:
            try:
                yield self.__getitem__(uid)
            except:
                print("Error parsing document %s" % uid)
            
    def __getitem__(self, uid):
        
        # load cached version
        pkl_file = "%s/%s.pkl" % (self.cache_path,uid.split("/")[-1]) if self.cache_path else None
        
        if pkl_file and os.path.exists(pkl_file): 
            #print pkl_file
            with open(pkl_file, 'rb') as f:
                document = cPickle.load(f)
           
        elif pkl_file and self.parser:
            document = self._parse_xml(uid)
            self._preprocess(document)
            with open(pkl_file, 'w+') as f:
                cPickle.dump(document, f)     
                  
        elif self.parser:
            document = self._parse_xml(uid)
            self._preprocess(document)
        else:
            document = self._parse_xml(uid)
        
        return document    
        
    def _preprocess(self,document):  
        '''Parse documents'''
        # determine unique doc ID
        if "pmid" in document["metadata"]:
            doc_id = "PMID:{}".format(document["metadata"]["pmid"])
        elif "pmc" in document["metadata"]:
            doc_id = "PMC:{}".format(document["metadata"]["pmc"]) 
        else:
            # just use a hashed journal title
            doc_id = "{}".format(hash(document["metadata"]["journal-title"])/1000000000)
             
        if "abstract-text" in document:
            content = document["abstract-text"]
            document["abstract"] = [s for s in self.parser.parse(content,doc_id=doc_id)]
            
        if "abstract-short-text" in document:
            content = document["abstract-short-text"]
            document["abstract-short"] = [s for s in self.parser.parse(content,doc_id=doc_id)]
            
        document["sections"] = []
        for section in document["section-text"]:
            try:
                section = [s for s in self.parser.parse(section.strip(),doc_id=doc_id)]
                document["sections"] += [section]
            except Exception as e:
                print "CoreNLP parsing exception %s" % section     
        
        document["sentences"] = []
        for section in document["sections"]:
            # HACK -- don't include really long sentences
            document["sentences"] += [s for s in section if len(s.words) <= self.MAX_SENTENCE_LENGTH]
            
    
    def tounicode(self,s):
        '''Clean up string input. This deals with various annoying text encoding problems.
        '''
        if not s:
            return ""
        s = s.encode("utf-8","ignore").decode("ascii","ignore")
        s = s.rstrip(' \t\r\n\0').strip('\0')
        return s
        
    def _parse_xml(self,uid):
        '''Parse PMC XML format, pull out relevant metadata. 
        NOTE: lxml + unicode is a major pain.
        '''
        #
        doc = lxml.etree.parse(uid)
        document = {"section-text":[],"section-titles":[],"metadata":{}}
        
        #
        # Article metadata is more complicated -- we just pull out a small subset
        #
        root = doc.xpath("//article/front/journal-meta")
        if root:        
            for node in root[0].iter('*'):
                if len(node) == 0:
                    document["metadata"][node.tag] = self.tounicode(node.text)
                    
    
        root = doc.xpath("//article/front/article-meta")
        if root:
            article_ids = doc.xpath("//article/front/article-meta/article-id")
            for node in article_ids:
                tag = node.attrib["pub-id-type"]
                document["metadata"][tag] = self.tounicode(node.text)
            
            article_title = doc.xpath("//article/front/article-meta/title-group/article-title")
            for node in article_title:
                document["metadata"][node.tag] = self.tounicode(node.text)
            
            authors = doc.xpath("//article/front/article-meta/contrib-group/contrib")
            document["metadata"]["authors"] = []
            for node in authors:
                if node.attrib and node.attrib["contrib-type"] == "author":
                    author = []
                    for child in node.iter('*'):
                        if child.tag not in ["email","xref"] and child.text:
                            author += [self.tounicode(child.text)]
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
                    abstract_name = "abstract-short-text"
                
                for sec in node.iter('*'):
                    if not sec.text:
                        continue
                    content += [self.tounicode(sec.text)]
                    
                document[abstract_name] = u" ".join(content)
                
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
                    titles += [self.tounicode(node.text)]
                    content += [self.tounicode(node.text)]
                    
                # ignore tables
                #elif ("table" not in node_xpath or "caption" in node_xpath) and node.text:
                #    content += [node.text]
                
                elif node.text:
                    content += [self.tounicode(node.text)]
                
            content = u" ".join( map(lambda x:re.sub("\s{2,}"," ",x), content)) 
            title = titles[0] if len(titles) > 0 else ""
            document["section-titles"] += [self.tounicode(title)]
            document["section-text"] += [self.tounicode(content)]
        
        #
        # References
        #
        references = doc.xpath("//article/back/ref-list/ref")
        document["references"] = []
        for ref in references:
            refdict = {}
           
            for node in ref.iter('*'):
                if node.tag in ["given-names","name","mixed-citation"]:
                    continue
                
                value = node.text
                pub_id_type = node.get("pub-id-type")
                if pub_id_type:
                    value = (pub_id_type,node.text)
                   
                refdict[node.tag] = refdict.get(node.tag,[]) + [value]
            document["references"] += [refdict]
        
        return document
       
    def _load_files(self):
        self.documents = {fname:0 for fname in glob.glob("%s/*/*.nxml" % self.path)}
          
