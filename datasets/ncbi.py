import sys
import codecs
import cPickle
from datasets import *
from collections import namedtuple
from utils import unescape_penn_treebank

Annotation = namedtuple('Annotation', ['text_type','start','end','text','mention_type'])

class NcbiDiseaseCorpus(Corpus):
    '''The NCBI disease corpus is fully annotated at the mention and concept level 
    to serve as a research resource for the biomedical natural language processing 
    community. 
                    -- from http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/
    '''
    def __init__(self, path, parser, cache_path="/tmp/"):
        super(NcbiDiseaseCorpus, self).__init__(path, parser)
        self.path = path
        self.cv = {"training":{},"development":{},"testing":{}}
        self.documents = {}
        self.annotations = {}
     
        self._load_files()
        self.cache_path = cache_path
      
     
    def __getitem__(self,pmid):
        """Use PMID as key and load parsed document object"""
        pkl_file = "%s/%s.pkl" % (self.cache_path, pmid)
        # load cached parse if it exists
        if os.path.exists(pkl_file):
            with open(pkl_file, 'rb') as f:
                self.documents[pmid] = cPickle.load(f)
        else:
            self.documents[pmid]["title"] = self.documents[pmid]["title"].encode("ascii","ignore")
            self.documents[pmid]["body"] = self.documents[pmid]["body"].encode("ascii","ignore")
            
            # align gold annotations
            # -----------------------------------------------------------------
            title = [s for s in self.parser.parse(self.documents[pmid]["title"])]
            body = [s for s in self.parser.parse(self.documents[pmid]["body"])]
            
            # initialize annotations   
            self.documents[pmid]["tags"] = []
            self.documents[pmid]["sentences"] = title + body
            
            if pmid in self.annotations:
                title_labels = [label for label in self.annotations[pmid] if label.text_type=='T']
                body_labels = [label for label in self.annotations[pmid] if label.text_type=='A']
                self.documents[pmid]["tags"] = self._label(title_labels,title)
                self.documents[pmid]["tags"] += self._label(body_labels,body)
            else:
                self.documents[pmid]["tags"] += [[] for _ in range(len(self.documents[pmid]["sentences"]))]
            # -----------------------------------------------------------------
            
            #with open(pkl_file, 'w+') as f:
            #    cPickle.dump(self.documents[pmid], f)
        
        '''
        # initialize annotations  
        title = [s for s in self.parser.parse(self.documents[pmid]["title"])]
        body = [s for s in self.parser.parse(self.documents[pmid]["body"])]
        
        self.documents[pmid]["tags"] = []
        self.documents[pmid]["sentences"] = title + body
        
        if pmid in self.annotations:
            title_labels = [label for label in self.annotations[pmid] if label.text_type=='T']
            body_labels = [label for label in self.annotations[pmid] if label.text_type=='A']
            self.documents[pmid]["tags"] = self._label(title_labels,title)
            self.documents[pmid]["tags"] += self._label(body_labels,body)
        else:
            self.documents[pmid]["tags"] += [[] for _ in range(len(self.documents[pmid]["sentences"]))]
        '''
        
        return self.documents[pmid]
           
    def _label(self,annotations,sentences):
        '''Convert annotations from NCBI offsets to parsed token offsets. 
        NOTE: This isn't perfect, since tokenization can fail to correctly split
        some tags. 
        '''
        tags = [[] for i,_ in enumerate(sentences)]
        
        sents = {min(sent.token_idxs):sent for sent in sentences}
        sent_offsets = sorted(sents)
        
        for label in annotations:
            # find target sentence
            for i in range(len(sent_offsets)):
                start = sent_offsets[i]  
                end = sents[start].token_idxs[-1] + 1
                
                # determine span match (assume potentially overlapping spans)
                if label.start >= start and label.start <= end:
                    
                    span = [label.start, label.start + len(label.text)]
                    
                    idx = len(sents[start].words)-1
                    for j in range(0,len(sents[start].words)-1):
                        if span[0] >= sents[start].token_idxs[j] and span[0] < sents[start].token_idxs[j+1]:
                            idx = j
                            break
                    
                    #print label.text
                    #print " ".join(sents[start].words[idx:])
                    #print 
                    #while sents[start].token_idxs[idx] < span[0]:
                    #   idx = idx + 1
                    
                    s_start = idx
                    text = label.text.replace(" ","")
                    while text:
                        t = sents[start].words[idx].replace("-LRB-","(").replace("-RRB-",")")
                        text = text.lstrip(t)
                        #print t, "|",text
                        idx += 1
                    
                    tags[i] += [ (label.text,(s_start,idx)) ]
                    
                    mention = "".join(sents[start].words[s_start:idx]).replace("-LRB-","(").replace("-RRB-",")")
                    
                    if label.text.replace(" ","") != mention:
                        print span
                        print tags[i][-1]
                        print zip(sents[start].token_idxs,sents[start].words)
                        print " ".join(sents[start].words)
                        print " ".join(sents[start].words[s_start:idx]).replace("-LRB-","(").replace("-RRB-",")")
                        print label.text
                        print
                    '''
                    idx = -1
                    s_end = sents[start].token_idxs[-1]
                    
                    while s_end > span[1]:
                        idx = idx - 1
                        s_end = sents[start].token_idxs[idx]
                    
                    
                    s_start = sents[start].token_idxs[idx]
                    while s_start > span[0]:
                        idx = idx - 1
                        s_start = sents[start].token_idxs[idx]  
                    
                    ii = sents[start].token_idxs.index(s_start)
                    jj = max(ii + 1,sents[start].token_idxs.index(s_end))
                  
                    # HACK -- some offset issues to resolve
                    jj = max(jj-ii, ii+len(label.text.split()))
                    
                    mention = "".join(sents[start].words[ii:jj])
                    mention = mention.replace("-LRB-","(").replace("-RRB-",")")
                        
                    if label.text.replace(" ","") != mention:
                        
                        print "*", span
                        print label
                        print start, end
                        print zip(sents[start].token_idxs,sents[start].words)
                        print zip(sents[start].token_idxs,sents[start].words)[ii:]
                        print ii, jj
                        print "length of label", len(label.text), label.text
                        print " ".join(sents[start].words)
                        mention = " ".join(sents[start].words[ii:jj])
                        mention = mention.replace("-LRB-","(").replace("-RRB-",")")
                        
                        print ii, jj, (jj-ii), label.text, "||", mention
                        print  "----------------------------------------"
                        
                    tags[i] += [ (label.text,(ii,jj+1)) ]
                    '''
                
        return tags           

    def __iter__(self):
        for pmid in self.documents:
            yield self.__getitem__(pmid)
              
    def _load_files(self):
        '''
        '''
        cvdefs = {"NCBIdevelopset_corpus.txt":"development",
                  "NCBItestset_corpus.txt":"testing",
                  "NCBItrainset_corpus.txt":"training"}
        
        filelist = glob.glob("%s/*.txt" % self.path)
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
                        row = row.split("|") if (len(row.split("|")) > 1 and row.split("|")[1] in ["t","a"]) else row.split("\t")
                        doc += [row]
                documents += [doc]
            
            for doc in documents:
                pmid,title,body = doc[0][0],doc[0][2],doc[1][2]
                self.cv[setname][pmid] = 1
                self.documents[pmid] = {"title":title,"body":body}
                doc_str = "%s %s" % (title, body)
              
                for row in doc[2:]:
                    pmid, start, end, text, mention_type, duid = row
                    start = int(start)
                    end = int(end)
                    # title or abstract mention?
                    text_type = "T" if end <= len(title) else "A"
                    
                    # sanity check
                    if text != doc_str[start:end]:
                        print pmid
                        print text
                        print doc_str[start:end]
                        print "FATAL annotation alignment error!"
                        sys.exit()
                   
                    if pmid not in self.annotations:
                        self.annotations[pmid] = []
                    
                    if text_type == "A":
                        start -= len(title) + 1
                        end -= len(title) + 1
                        
                        if text != body[start:end]:
                            print "Fatal Error"
                            print  body[start:end]
                    
                    self.annotations[pmid] += [Annotation(text_type, start, end, text, mention_type)]
        
              