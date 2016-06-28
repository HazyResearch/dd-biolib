import os
import re
import sys
import codecs
import cPickle
import operator
import itertools
import numpy as np
from .base import *
from ddlite import SentenceParser
from .tools import unescape_penn_treebank,overlaps

class CdrCorpus(Corpus):
    '''The CDR corpus 
                    -- f
                    
        1500 PubMed abstracts
        X disease mentions
        X chemical mentions
    '''
    def __init__(self, path, parser=SentenceParser(), cache_path="/tmp/"):
        super(CdrCorpus, self).__init__(path, parser)
        self.path = path
        self.cv = {"training":{},"development":{},"testing":{}}
        self.documents = {}
        self.annotations = {}
        # hack
        self.relations = {}
        self.entities = {}
     
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
            
            self.documents[pmid]["tags"] = {}
            if pmid in self.annotations:
                diseases = [i for i in self.annotations[pmid] if i.mention_type=="Disease"]  
                chemicals = [i for i in self.annotations[pmid] if i.mention_type=="Chemical"]  
                self.documents[pmid]["tags"]["diseases"] = self._label(diseases,self.documents[pmid]["sentences"])
                self.documents[pmid]["tags"]["chemicals"] = self._label(chemicals,self.documents[pmid]["sentences"])
            else:
                self.documents[pmid]["tags"]["diseases"] += [[] for _ in range(len(self.documents[pmid]["sentences"]))]  
                self.documents[pmid]["tags"]["chemicals"] += [[] for _ in range(len(self.documents[pmid]["sentences"]))]   
             
            self.documents[pmid]["relations"] = self.relations[pmid]
              
            with open(pkl_file, 'w+') as f:
                cPickle.dump(self.documents[pmid], f)
        
        return self.documents[pmid]
    
    def _ground_truth(self,doc_ids,entity_type="chemicals"):
        '''Build ground truth (doc_id,sent_id,char_offset) mentions'''
        ground_truth = []
        for pmid in doc_ids:
            doc = self.__getitem__(pmid)["sentences"]
            labels = self.__getitem__(pmid)["tags"][entity_type]
            #print len(labels), labels
            for sent_id in range(0,len(doc)):
                for tag in labels[sent_id]:
                    # assess ground truth on token
                    label = tag[0] # gold standard annotation text
                    span = tag[1]
                    char_idx = doc[sent_id].token_idxs[span[0]]
                    char_span = tuple([char_idx, char_idx+len(label)])
                    
                    ground_truth += [(pmid, sent_id, tuple(range(*span)), char_span, label.replace(" ",""))]
                    #ground_truth += [(pmid, sent_id, tuple(range(*span)),label.replace(" ",""))]
                    
        return ground_truth
    
    def gold_labels(self,candidates,entity_type):
        '''Given a set of candidates, generate -1,1 labels 
        using internal gold label data'''
        doc_ids = {c.doc_id:1 for c in candidates} 
        true_labels = set(self._ground_truth(doc_ids,entity_type))
        
        gold = [0] * len(candidates)
        for idx,c in enumerate(candidates):
            text = "".join([c.words[i] for i in c.idxs])
            
            char_span = [c.token_idxs[i] for i in c.idxs]
            char_span = (char_span[0], char_span[-1] + len(c.words[c.idxs[-1]]))
            char_span = tuple(char_span)
            
            mention = (c.doc_id, c.sent_id, tuple(c.idxs), char_span, text)
            #mention = (c.doc_id, c.sent_id, tuple(c.idxs), text)
            
            gold[idx] = 1 if mention in true_labels else -1
        
        return np.array(gold)
    
    def score(self, candidates, prediction, entity_type="chemicals", doc_ids=None):
        '''Given a set of candidates, compute true precision, recall, f1
        using gold labeled benchmark data (this includes non-candidate entities,
        which aren't captured by ddlite metrics). If holdout (a list of 
        document PMIDs) is provided, us that as the document collection for scoring.
        '''
        
        print "Candidates N:{}".format(len(candidates))
        # create doc set from candidate pool or a provided doc_id set
        doc_ids = {c.doc_id:1 for c in candidates} if not doc_ids else dict.fromkeys(doc_ids)
        
        # compute original document character offsets for each mention
        mentions = {}
        for i,c in enumerate(candidates):
            if c.doc_id not in doc_ids:
                continue
            if prediction[i] != 1:
                continue  
            mentions[self.getkey(c)] = 1
        
        # score
        mentions = set(mentions.keys())
        true_labels = set(self._ground_truth(doc_ids,entity_type))
        tp = true_labels.intersection(mentions)
        fp = mentions.difference(tp)
        fn = true_labels.difference(tp)
        
        print "-----------------------------"
        print "TP:{} FP:{} FN:{} True_N:{}".format(len(tp),len(fp),len(fn),len(true_labels))
        print "-----------------------------"
        
        r = len(tp) / float(len(true_labels))
        p = len(tp) / float(len(tp) + len(fp))
        f1 = 2.0 * (p * r) / (p + r)

        return {"precision":p, "recall":r,"f1":f1, 
                "tp":len(tp), "fp":len(fp), "fn":len(fn)}
        

    def classification_errors(self, candidates, prediction, entity_type="chemicals", doc_ids=None):
        # create doc set from candidate pool or a provided doc_id set
        doc_ids = {c.doc_id:1 for c in candidates} if not doc_ids else dict.fromkeys(doc_ids)
        
        # compute original document character offsets for each mention
        mentions = {}
        for i,c in enumerate(candidates):
            if c.doc_id not in doc_ids:
                continue
            if prediction[i] != 1:
                continue
            mentions[self.getkey(c)] = 1
    
        #score
        mentions = set(mentions.keys()) 
        true_labels = set(self._ground_truth(doc_ids,entity_type))
        tp = true_labels.intersection(mentions)
        fp = mentions.difference(tp)
        fn = true_labels.difference(tp)
        
        return (tp,fp,fn)
    
    def _label_index(self,doc_ids,entity_type):
        '''Ground truth annotation index'''
        label_idx = {}
        for pmid in doc_ids:
            label_idx[pmid] = {}
            doc = self.__getitem__(pmid)
            for sentence,tags in zip(doc["sentences"],doc["tags"][entity_type]):
                if sentence.sent_id not in label_idx[pmid]:
                    label_idx[pmid][sentence.sent_id] = {}
                for text,offset in tags:
                    label_idx[pmid][sentence.sent_id][offset] = text
        return label_idx
    
    
    def _candidate_index(self,candidates):
        
        candidate_idx = {}
        for i,c in enumerate(candidates):
            if c.doc_id not in candidate_idx:
                candidate_idx[c.doc_id] = {}
            if c.sent_id not in candidate_idx[c.doc_id]:
                candidate_idx[c.doc_id][c.sent_id] = {}
            span = (min(c.idxs),max(c.idxs)+1)
            candidate_idx[c.doc_id][c.sent_id][span] = c 
            
        return candidate_idx
    
    
    def match(self, label, candidates, c_index=None, partial=True):
        
        m = []
        c_index = self._candidate_index(candidates) if not c_index else c_index
        
        doc_id,sent_id,idxs,_,_ = label
        #doc_id,sent_id,idxs,_ = label
        if doc_id in c_index and sent_id in c_index[doc_id]:
            lspan = (min(idxs),max(idxs)+1)
            if lspan in c_index[doc_id][sent_id]:
                m += [c_index[doc_id][sent_id][lspan]]
                
            if partial:
                for cspan in c_index[doc_id][sent_id]:
                    if overlaps(range(*lspan),range(*cspan)) and lspan!=cspan:
                        m += [c_index[doc_id][sent_id][cspan]]
                
        return m
    
    def getkey(self,c):
        txt = " ".join(c.mention())
        char_span = [c.token_idxs[i] for i in c.idxs]
        char_span = (min(char_span),min(char_span)+len(txt))
        return (c.doc_id, c.sent_id, tuple(c.idxs), char_span, "".join(c.mention()))
        #return (c.doc_id, c.sent_id, tuple(c.idxs), "".join(c.mention()))
    
    def force_longest_match(self, candidates, probability, entity_type="chemicals", doc_ids=None):
        '''Only use longest correct match for any set of overlapping or 
        adjoining mentions'''
    
        c_index = self._candidate_index(candidates)
        true_labels = set(self._ground_truth(doc_ids,entity_type))
        pred_idx = {self.getkey(c):i for i,c in enumerate(candidates)}
        
        mapping = {}
        for label in true_labels:
            mapping[label] = self.match(label,candidates,c_index)
            
        for label in mapping:
            lengths = [len(c.mention()) for c in mapping[label]]
            proba = [probability[pred_idx[self.getkey(c)]] for c in mapping[label]]
            scores = zip(proba,lengths,mapping[label])
            print [(x,y,z.mention()) for (x,y,z) in sorted(scores,reverse=1)]
            #scores = [c for _,c,p in sorted(zip(lengths,mapping[label],proba),reverse=1) if p > 0.5]
            scores = [c for p,l,c, in sorted(zip(proba,lengths,mapping[label]),reverse=1) if p > 0.499]
            
            if not scores:
                continue
            
            mapping[label].remove(scores[0])
            probability[pred_idx[self.getkey(scores[0])]] = 1
            
            for c in mapping[label]:
                probability[pred_idx[self.getkey(c)]] = -1

    
    def error_analysis_v1(self, candidates, prediction, entity_type="chemicals", doc_ids=None):
        
        c_index = self._candidate_index(candidates)
        true_labels = set(self._ground_truth(doc_ids,entity_type))
        
        mapping,claimed = {},{}
        for label in true_labels:
            # NOTE: candidates can touch multiple labels
            mapping[label] = self.match(label,candidates,c_index)
            claimed.update({self.getkey(c):1 for c in mapping[label]})
        
      
    def error_analysis(self, candidates, prediction, entity_type="chemicals", doc_ids=None):
        
        c_index = self._candidate_index(candidates)
        l_index = self._label_index(doc_ids,entity_type)
        true_labels = set(self._ground_truth(doc_ids,entity_type))
        
        mapping,claimed = {},{}
        for label in true_labels:
            # NOTE: candidates can touch multiple labels
            mapping[label] = self.match(label,candidates,c_index)
            claimed.update({self.getkey(c):1 for c in mapping[label]})     
        
        partial,complete = [],[]
        for label in true_labels:
            matches = self.match(label, candidates, c_index)
            mentions = [" ".join(c.mention()) for c in mapping[label]]
            
            # true label
            doc_id,sent_id,idxs,char_span,_ = label
            span = (min(idxs),max(idxs)+1)
            mtext = l_index[doc_id][sent_id][span]
            
            # partial match
            if mtext not in mentions and len(matches) != 0:
                partial += [list(label)[0:-1] + [mtext]]
            
            # missed entirely
            elif mtext not in mentions:
                complete += [list(label)[0:-1] + [mtext]]
        
        return (partial,complete)
        
        
        
        
    def conll(self,doc_ids):
        '''Export docs to CoNLL format'''
        
        outstr = []
        for doc_id in doc_ids:
            doc = self.__getitem__(doc_id)
            tagged = zip(doc["sentences"], doc["tags"])
            for sentence,labels in tagged:
                # create label index
                idx = {}
                for term,(i,j) in labels:
                    if i not in idx:
                        idx[i] = {}
                    idx[i][term] = j
                
                # fix overlapping gold entity spans (due to tokenziation errors)
                words = sentence.words
                tags = [u'O'] * len(words)
                for i in idx:
                    for label in idx[i]:
                        bio2 = [u"<B-DISEASE>"]
                        bio2 += [u"<I-DISEASE>"] * (len(label.split())-1)
                        tags[i:idx[i][label]] = bio2
                
                s = zip(words,tags)
                for word,tag in s:
                    outstr += [u"{} {}".format(word,tag)]
                outstr += [u""] 
                
        return "\n".join(outstr)
    
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
                    
                    s_start = idx
                    s_end = len(sents[start].words)
                    for j in range(idx,len(sents[start].words)):
                        if span[1] > sents[start].token_idxs[j]:
                            s_end = j + 1
                        else:
                            break
                    
                    uids = tuple(label.mesh_ids)
                    tags[i] += [ (label.text, (s_start,s_end), label.mention_type, uids) ]
                    
        return tags           

    def __iter__(self):
        for pmid in self.documents:
            yield self.__getitem__(pmid)
              
    def _load_files(self):
        '''
        '''
        cvdefs = {"CDR_DevelopmentSet.PubTator.txt":"development",
                  "CDR_TestSet.PubTator.txt":"testing",
                  "CDR_TrainingSet.PubTator.txt":"training"}
        
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
                if doc:
                    documents += [doc]
            
            
            for doc in documents:
                pmid,title,body = doc[0][0],doc[0][2],doc[1][2]
                
                if pmid in self.documents:
                    print "Warning: duplicate {} PMID {}".format(setname,pmid)
                    
                self.cv[setname][pmid] = 1
                self.documents[pmid] = {"title":title,"body":body}
                doc_str = "%s %s" % (title, body)
              
                for row in doc[2:]:
                    
                    # relation
                    # ----------------------------
                    if len(row) <= 4:# or row[4] == "Chemical":
                        pmid,rela,m1,m2 = row
                        self.relations[pmid] = self.relations.get(pmid,[]) + [(m1,m2)]
                        continue
                    
                    # entity
                    # ----------------------------
                    if len(row) == 6:
                        pmid, start, end, text, mention_type, duid = row
                        norm_names = []
                    elif len(row) == 7:
                        pmid, start, end, text, mention_type, duid, norm_names = row
                    duid = duid.split("|")
                    
                    start = int(start)
                    end = int(end)
                    # title or abstract mention?
                    text_type = "T" if end <= len(title) else "A"
                    if pmid not in self.annotations:
                        self.annotations[pmid] = []
                    
                    label = CdrEntity(text_type, start, end, text, mention_type, duid, norm_names)
                    
                    self.annotations[pmid] += [label]
                
                # create entity 
                #for label in self.annotations[pmid]:
                #    print "ADD TO MAPPING"
                
            # validate there are no duplicate annotations
            labels = [ map(lambda x:(pmid,x), self.annotations[pmid]) for pmid in self.cv[setname]]
            labels = list(itertools.chain.from_iterable(labels))
      
            # validation
            # See "Annotating chemicals, diseases and their interactions in biomedical literature"
            diseases_v = {"testing":4424, "development":4244, "training":4182}
            chemicals_v = {"testing":5385 , "development":5347, "training":5203}
            
            print "Gold Labels", setname, len(labels), (diseases_v[setname] + chemicals_v[setname]) == len(labels)
        
            