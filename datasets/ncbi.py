import os
import sys
import codecs
import cPickle
import itertools
#from ddlite.ddbiolib.datasets import *
#from ddlite.ddbiolib.utils import unescape_penn_treebank
from .base import *
from .tools import unescape_penn_treebank

import operator
from cgitb import text

class NcbiDiseaseCorpus(Corpus):
    '''The NCBI disease corpus is fully annotated at the mention and concept level 
    to serve as a research resource for the biomedical natural language processing 
    community. 
                    -- from http://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/
                    
        793 PubMed abstracts
        6,892 disease mentions
        790 unique disease concepts
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
            self.documents[pmid]["title"] = self.documents[pmid]["title"]
            self.documents[pmid]["body"] = self.documents[pmid]["body"]
            
            # align gold annotations
            title = self.documents[pmid]["title"]
            body = self.documents[pmid]["body"]
            doc_str = "%s %s" % (title,body)
            self.documents[pmid]["sentences"] = [s for s in self.parser.parse(doc_str,doc_id=pmid)]
            
            self.documents[pmid]["tags"] = []
            if pmid in self.annotations:
                self.documents[pmid]["tags"] = self._label(self.annotations[pmid],self.documents[pmid]["sentences"])
            else:
                self.documents[pmid]["tags"] += [[] for _ in range(len(self.documents[pmid]["sentences"]))]   
                
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[pmid], f)
        
        return self.documents[pmid]
    
    def _ground_truth(self,doc_ids):
        '''Build ground truth (doc_id,sent_id,char_offset) mentions'''
        documents = [(doc_id, self.__getitem__(doc_id)["sentences"], 
                      self.__getitem__(doc_id)["tags"]) for doc_id in doc_ids]     
          
        ground_truth = []
        for pmid,doc,labels in documents:
            for sent_id in range(0,len(doc)):
                for tag in labels[sent_id]:
                
                    # assess ground truth on token
                    label = tag[0] # gold standard annotation text
                    span = tag[-1]
                    char_idx = doc[sent_id].token_idxs[span[0]]
                    char_span = tuple([char_idx, char_idx+len(label)])
                    
                    # normalize for tokenization differences by removing whitespace
                    #text = doc[sent_id].words[tag[-1][0]:tag[-1][1]]
                    #text = unescape_penn_treebank(text)
                    
                    # match doc,sentence,char span and text (without tokenization)
                    ground_truth += [(pmid, sent_id, tuple(range(*span)), char_span, label.replace(" ",""))] 
                    
        
        return ground_truth
    
    def gold_labels(self,candidates):
        '''Given a set of candidates, generate -1,1 labels using internal
        gold label data
        '''
        doc_ids = {c.doc_id:1 for c in candidates} 
        true_labels = set(self._ground_truth(doc_ids))
        
        gold = [0] * len(candidates)
        for idx,c in enumerate(candidates):
            text = "".join([c.words[i] for i in c.idxs])
            char_span = [c.token_idxs[i] for i in c.idxs]
            char_span = (char_span[0], char_span[-1] + len(c.words[c.idxs[-1]]))
            mention = (c.doc_id, c.sent_id, tuple(c.idxs), char_span, text)
            gold[idx] = 1 if mention in true_labels else -1
        
        return gold
    
    def score(self, candidates, prediction, doc_ids=None):
        '''Given a set of candidates, compute true precision, recall, f1
        using gold labeled benchmark data (this includes non-candidate entities,
        which aren't captured by ddlite metrics). If holdout (a list of 
        document PMIDs) is provided, us that as the document collection for scoring.
        '''
        # create doc set from candidate pool OR a provided doc_id set
        doc_ids = {c.doc_id:1 for c in candidates} if not doc_ids else dict.fromkeys(doc_ids)
        # compute original document character offsets for each mention
        mentions = []
        for c in candidates:
            if c.doc_id not in doc_ids:
                continue
            text = "".join([c.words[i] for i in c.idxs])
            char_span = [c.token_idxs[i] for i in c.idxs]
            char_span = (char_span[0], char_span[-1] + len(c.words[c.idxs[-1]]))
            mentions += [(c.doc_id, c.sent_id, tuple(c.idxs), char_span, text)]
        
        mentions = set(mentions) 
        true_labels = set(self._ground_truth(doc_ids))
        
        tp = true_labels.intersection(mentions)
        fp = mentions.difference(tp)
        fn = true_labels.difference(tp)
          
        r = len(tp) / float(len(true_labels))
        p = len(tp) / float(len(tp) + len(fp))
        f1 = 2.0 * (p * r) / (p + r)

        return {"precision":p, "recall":r,"f1":f1, 
                "tp":len(tp), "fp":len(fp), "fn":len(fn)}
    
    def error_analysis(self,candidates, prediction, doc_ids=None):
        ''' Specific types of errors
        1: subsequence candidate: "hereditary breast cancers" vs. "breast cancers"
        2: tokenization error / subcharacter sequence 
        '''
        doc_ids = {c.doc_id:1 for c in candidates} if not doc_ids else dict.fromkeys(doc_ids)
        
        # ground truth annotation index
        label_idx = {}
        for doc_id in self.annotations:
            label_idx[doc_id] = {}
            for label in self.annotations[doc_id]:
                label_idx[doc_id][(label.start,label.end)] = (label.text, label.mention_type)
        
        # mention offsets
        mentions = []
        for c in candidates:
            if c.doc_id not in doc_ids:
                continue
            text = "".join([c.words[i] for i in c.idxs])
            char_span = [c.token_idxs[i] for i in c.idxs]
            char_span = (char_span[0],char_span[-1] + len(c.words[c.idxs[-1]]))
            mentions += [(c.doc_id, c.sent_id, tuple(c.idxs), char_span, text)]
        
        mentions = set(mentions) 
        true_labels = set(self._ground_truth(doc_ids))
        
        tp = true_labels.intersection(mentions)
        fp = mentions.difference(tp)
        fn = true_labels.difference(tp)
        
        print "tp:{} fp:{} fn:{}".format(len(tp),len(fp),len(fn))
        
        # False Negatives
        errors = {"tokenization":0,"oov":0,"subsequence":0}
        for item in fn:    
            pmid,sent_id,idxs,char_span,txt = item    
            text = "{} {}".format(self.documents[pmid]["title"],self.documents[pmid]["body"])
            tokenized = self.documents[pmid]["sentences"][sent_id].words[min(idxs):max(idxs)+1]
            tokenized = unescape_penn_treebank(tokenized)
            true_mention = text[char_span[0]:char_span[1]]
            
            if true_mention.replace(" ","") != "".join(tokenized):
                errors["tokenization"] += 1
            

        # False Positives
        overlap = {}
        for item in fp:
            pmid,sent_id,idxs,char_span,txt = item
            text = "{} {}".format(self.documents[pmid]["title"],self.documents[pmid]["body"])
            # does the provided character span overlap
            i,j = char_span
            for cspan in label_idx[pmid]:
                if i >= cspan[0] and i <= cspan[1]:
                    m = text[char_span[0]:char_span[1]]
                    errors["subsequence"] += 1
                    key = (pmid,cspan)
                    overlap[key] = overlap.get(key,0) + 1
        print len(overlap)
        print errors
        return 
    
        '''
        # aggregate errors by category
        # ------------------------------------------
        mention_type_freq = {"fn":{}}
        for item in fn:
            doc_id,_,_,char_span = item
            text,mention_type = label_idx[doc_id][char_span] 
            mention_type_freq["fn"][mention_type] = mention_type_freq["fn"].get(mention_type,0) + 1
            
        mention_type_freq["tp"] = {}
        for item in tp:
            doc_id,_,_,char_span = item
            text,mention_type = label_idx[doc_id][char_span] 
            mention_type_freq["tp"][mention_type] = mention_type_freq["tp"].get(mention_type,0) + 1
        
        for category in mention_type_freq:
            print category, mention_type_freq[category]
        # ------------------------------------------
        '''
             
    
    
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
                
                debug = []
                # determine span match (assume potentially overlapping spans)
                if label.start >= start and label.start <= end:
                    
                    span = [label.start, label.start + len(label.text)]
                    
                    idx = len(sents[start].words)-1
                    for j in range(0,len(sents[start].words)-1):
                        if span[0] >= sents[start].token_idxs[j] and span[0] < sents[start].token_idxs[j+1]:
                            idx = j
                            break
                    
                    s_start = idx
                    s_end = len(sents[start].words)
                    for j in range(idx,len(sents[start].words)):
                        if span[1] > sents[start].token_idxs[j]:
                            s_end = j + 1
                        else:
                            break
                            
                    tags[i] += [ (label.text, (s_start,s_end)) ]
                   
                    
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
                
                if pmid in self.documents:
                    print "Warning: duplicate {} PMID {}".format(setname,pmid)
                    
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
                    
                    label = Annotation(text_type, start, end, text, mention_type)
                    self.annotations[pmid] += [label]
            
            # validate there are no duplicate annotations
            labels = [ map(lambda x:(pmid,x), self.annotations[pmid]) for pmid in self.cv[setname]]
            labels = list(itertools.chain.from_iterable(labels))
            if len(labels) != len(set(labels)):
                print "Warning: duplicate annotations found"
                freq = {l:labels.count(l) for l in labels}
                freq = {l:n for l,n in freq.items() if n != 1}
                
            print setname,len(labels)
        
            