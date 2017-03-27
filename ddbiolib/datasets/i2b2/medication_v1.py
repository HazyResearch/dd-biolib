'''
Messy i2b2 Medication Extraction Challenge data set parser

@author: fries
'''

import re
import logging
import codecs
import glob
import csv
import sys
import os
import numpy as np
import operator
from gensim.models.word2vec import Word2Vec

logger = logging.getLogger('corpora.i2b2corpus')
    
# regular expressions for normalizing common entities
date_regex = re.compile("\d{1,2}/\d{1,2}/\d{1,4}")
telephone_regex = re.compile("\d{3}-\d{3}-\d{4}|\(\d{3}\) \d{3}[ -]+\d{4}")

prepositions = ['aboard', 'about', 'above', 'across', 'after', 'against', 
                'along', 'alongside', 'amid', 'among', 'around', 'at', 'atop', 
                'barring', 'before', 'behind', 'below', 'beneath', 'beside', 
                'besides', 'between', 'beyond', 'but', 'by', 'concerning', 
                'considering', 'despite', 'down', 'during', 'except', 'for', 
                'from', 'in', 'inside', 'into', 'like', 'near', 'nearby', 
                'of', 'off', 'on', 'onto', 'opposite', 'out', 'outside', 
                'over', 'past', 'per', 'regarding', 'round', 'since', 
                'through', 'throughout', 'till', 'to', 'towards', 'under',"than", 
                'underneath', 'until', 'unto', 'up', 'upon', 'with', 'within', 
                'without', "final"]

prepositions = {x:1 for x in prepositions}

def discharge_summary_parser(f,normalize):
    '''
    i2b2 2009 discharge summaries are split on line
    and tokenized by whitespace. Line and term offsets
    are used by the annotation format.
    '''
    doc = []
    for line in f:
        
        line = line.replace("&gt;",">")
        line = line.replace("&lt;","<")
        line = line.replace("&amp;","&")

        tokens = line.strip().split()

        doc += [tokens]
    
    return doc
        
def annotation_parser(f,rm_tags=[]):
    '''i2b2 annotation format'''
    #m="cisplatin." 26:5 26:5||do="nm"||mo="nm"||f="nm"||du="nm"||r="nm"||ln="narrative"
    annotations = []
    
    for line in f:
        row = line.strip().split("||")
        mention = []
        
        for item in row:
            m = re.search('(m|do|mo|f|du|r|ln)="(.+)"',item)
            if not m:
                logger.error("Failed to parse annotation line")
                
            entity_type = m.group(1)
            text_span = m.group(2) 
            
            if entity_type in rm_tags:
                continue
            
            offsets = item.replace(m.group(0),"").strip()
            if offsets:
                offsets = offsets.split(",")
                for i in range(len(offsets)):
                    offsets[i] = map(lambda x:map(int,x.split(":")),offsets[i].split())
                     
            mention += [ (entity_type, text_span, offsets) ]
        annotations += [mention]
        
    return annotations

def annotate_doc(annotations,doc,uid):
    '''
    Create document sequence and labels. i2b2 offsets
    are of the form <LINE>:<TOKEN> where LINE offsets begin
    at 1 and TOKEN offsets begin at 0 (ugh).
    Use IOB format (inside, outside, beginning)
    Example medication mention
    B-m, I-m, O
    '''
    labels = [ ['O' for _ in line] for line in doc ]
    
    for mention in annotations:
        for item in mention:
            
            entity_label = item[0]
            
            # if there is a mention, determine the text span
            if item[-1]:
                
                for offset in item[-1]:
                    begin,end = offset
                    
                    if begin[0] != end[0]: 
                        span_n = len(doc[begin[0] - 1][begin[1]:]) 
                        span_n += len(doc[end[0] - 1][:end[1]+1])
                        
                        # generate IOB labels
                        span = ["I-%s" % entity_label] * span_n
                        span[0] = "B-%s" % entity_label
                        
                        span_n = len(doc[begin[0] - 1][begin[1]:]) 
                        labels[begin[0] - 1][begin[1]:] = span[0:span_n]
                        labels[end[0] - 1][:end[1] + 1] = span[span_n:]   
                          
                    else:
                        # generate IOB labels
                        span = ["I-%s" % entity_label] * (end[1] - begin[1] + 1)
                        span[0] = "B-%s" % entity_label
                        labels[begin[0] - 1][begin[1]:end[1]+1] = span
                        
    return labels


class i2b2MedicationCorpus(object):
    
    def __init__(self, inputdir, labeldir, encoding="latin2", rm_tags=[],
                 normalize=True, abbrv=[] ):
        '''
        Parameters
        ----------
        filename : string
            The input dir
        processes: int, optional
            The number of worker processes to use
        dictionary:  optional
            
        '''
        self.normalize = normalize
        self.encoding = encoding
        self.inputdir = inputdir
        self.labeldir = labeldir
        
        self.index2token = {}
        self.token2index = {}
        self.index2label = {}
        self.label2index = {}
        
        #self.uid2index = {}
        #self.index2uid = {}
        
        self.annotations = {}
        self.documents = {}
        self.labels= {}
        self.rm_tags = rm_tags
        self.abbrv = abbrv
        
        self.freq_regex = re.compile("q\.\d+h\.")
        self.qty_regex = re.compile("\d,\d+")
        
        
        self.load_texts()
    
    
    def __expand_tokens(self, sentences, tags):
        '''
        Several heuristics for dealing with noisy tokens in the i2b2
        medication challenge data set. This includes 
        '''
        updated = False
        for i in range(len(sentences)):
            s,t = [],[]
            
            for idx,word in enumerate(sentences[i]):
               
                if len(word) == 1 or self.freq_regex.match(word):
                    s += [sentences[i][idx]]
                    t += [tags[i][idx]]
                    continue
                
                #if word.count("/") > 1 and not date_regex.match(word) and \
                #  not telephone_regex.match(word) and re.sub("[0-9./]","",word).strip() != "" and \
                #  re.match("([A-Za-z0-9]+[/])+",word):
                #    print word
                
                
                if re.match("^([*]+[A-Za-z0-9]+$)|([A-Za-z0-9]+?[*]+)$",word):
                    
                    subseq = [x for x in re.split("([*]+)",word) if x]
                    
                    if tags[i][idx].split("-") == ["O"]:
                        s += subseq
                        t += ['O','O']

                    else:
                        prefix = tags[i][idx].split("-")[0]
                        etype = tags[i][idx].split("-")[-1]
                        s += subseq
                        t += ['%s-%s' % (prefix,etype),'I-%s' % (etype)]

                    updated = 1
     
                # split training puncutation
                elif (word[-1] in ["."] and word not in self.abbrv) or word[-1] in [",",":",";","(",")","/"]:
                    s += [sentences[i][idx][0:-1], word[-1]]
                    t += [tags[i][idx], 'O'  ]
                    updated = 1

                # split words consisting of concatenated tokens
                elif re.search("^[a-zA-Z]{4,}[/.;:][a-zA-Z]{4,}$",word) or \
                     re.search("^[a-zA-Z0-9]{2,}[=>][a-zA-Z0-9%.]{2,}$",word):
                    
                    #subseq = re.split("([/.;:=])",word)
                    # split on first matched split token
                    sidx = [word.index(ch) for ch in re.findall("([/.;:=>])",word)][0]
                    subseq = [word[0:sidx], word[sidx], word[sidx+1:]]
                    
                    if tags[i][idx].split("-") == ["O"]:
                        s += subseq
                        t += ['O','O','O']
                    else:
                        prefix = tags[i][idx].split("-")[0]
                        etype = tags[i][idx].split("-")[-1]
                        s += subseq
                        t += ['%s-%s' % (prefix,etype),'I-%s' % (etype),'I-%s' % (etype)]
                    
                    updated = 1
                        
                # leave word as-is   
                else:
                    s += [sentences[i][idx]]
                    t += [tags[i][idx]]
            
            sentences[i] = s
            tags[i] = t
            
        return updated
    
    def __repair(self,sentences,tags):
        '''
        HACK function to fix sentence boundaries and word tokenization issues
        in original corpus release. This is just a bunch of rules and observations
        specific to the i2b2 corpus. If we don't fix sentences, then BIO
        tagging breaks in several instances. 
        '''
        # 1: Expand tokens
        while self.__expand_tokens(sentences, tags):
            pass
        
        # 2: Create new sentence boundaries by merging sentences
        dangling = [",","Dr.",'as','of','and','at'] + prepositions.keys()
        sentence_fragments = ["Please see","The"]
        
        m_sentences, m_tags = [],[]
        curr_sentence, curr_tags = [],[]
        dangler = False
        
        for i in range(len(sentences)):
            
            if not sentences[i]:
                continue
            
            # ends if a preposition or other known dangling word
            if dangler:
                curr_sentence += [sentences[i]]
                curr_tags += [tags[i]]
               
            elif sentences[i][0][0].islower() and curr_sentence:
                curr_sentence += [sentences[i]]
                curr_tags += [tags[i]]
            
            elif curr_sentence:
                curr_sentence = reduce(lambda x,y:x+y, curr_sentence)
                curr_tags = reduce(lambda x,y:x+y, curr_tags)
                
                m_sentences += [curr_sentence]
                m_tags += [curr_tags]
                
                curr_sentence,curr_tags = [],[]
                curr_sentence += [sentences[i]]
                curr_tags += [tags[i]]
            
            else:
                curr_sentence = [sentences[i]]
                curr_tags = [tags[i]]
                
            dangler = sentences[i][-1] in dangling
                
        if curr_sentence:
            m_sentences += [reduce(lambda x,y:x+y, curr_sentence)]
            m_tags += [reduce(lambda x,y:x+y, curr_tags)]
        
        #:3 split sentences 
        dangling = False
        f_sentences, f_tags = [], []
        
        for i in range(len(m_sentences)):
            
            splits = []
            for j in range(len(m_sentences[i])-1):
                if m_sentences[i][j] == "." and m_sentences[i][j+1][0].isupper():
                    splits += [j+1]
            splits += [len(m_sentences[i])]
            
            curr = 0
            
            for idx in splits:
                sentence = m_sentences[i][curr:idx]
                tags = m_tags[i][curr:idx]
                
                if dangling:
                    f_sentences[-1] += sentence
                    f_tags[-1] += tags
                    dangling = False
                    
                else:     
                    f_sentences += [sentence]
                    f_tags += [tags]
                    
                if " ".join(sentence).strip() in sentence_fragments:
                    dangling = True
                
                curr = idx
         
        return f_sentences, f_tags       
    
    
    def embedding_weights(self, filename, emb_type="word2vec", top_n=None):
        '''
        Load embedding model and create weight matrix for words. Use some
        heuristics to match words not directly found in our model vocabulary.
        If top_n is provided, only use top N words from embedding vocabulary.
        '''
        model = Word2Vec.load(filename)
        model.init_sims()    
   
        vocab = [(word,model.vocab[word].count) for word in model.vocab]
        vocab = sorted(vocab, key=operator.itemgetter(1),reverse=1)
        vocab = zip(*vocab[0:top_n])[0] if top_n else zip(*vocab)[0] 
        
        token2index = {word:idx for word,idx in self.token2index.items()}
        for word in vocab:
            if word not in token2index:
                token2index[word] = len(token2index)
        
        dim = model.syn0norm.shape[1]
        weights = np.zeros((len(token2index)+1,dim),dtype=np.int32)
        
        for word in token2index:
            idx = token2index[word]
            if word not in model.vocab:
                weights[idx] = 0.2 * np.random.uniform(-1.0, 1.0,(1, dim))
            else:
                jdx = model.vocab[word].index
                weights[idx] = model.syn0norm[jdx]
        
        weights[-1] = 0.2 * np.random.uniform(-1.0, 1.0,(1, dim))
        
        self.token2index = token2index
        self.index2token = {idx:term for term,idx in self.token2index.items()}
        
        print(len(self.token2index))
        print(len(self.index2token))
        return weights
        
    def __iter__(self):
        """
        The function that defines a corpus.
        Iterating over the corpus must yield sparse vectors, one for each document.
        """
        for uid in self.labels:
            
            doc_idx = [[self.token2index[w] for w in sentence] for sentence in self.documents[uid] if sentence]
            lbl_idx = [[self.label2index[w] for w in sentence] for sentence in self.labels[uid] if sentence]
            
            yield doc_idx, lbl_idx
    
    def __getitem__(self,uid):

        doc_idx = [[self.token2index[w] for w in sentence] for sentence in self.documents[uid]]
        lbl_idx = [[self.label2index[w] for w in sentence] for sentence in self.labels[uid]] if uid in self.labels else []
            
        return doc_idx,lbl_idx
        
    def __len__(self):
    
        if not hasattr(self, 'length'):
            # cache the corpus length
            self.length = len(self.labels)
        return self.length
    
    def load_texts(self):
        '''
        Yield one document at a time (required by gensim). All 
        pre-processing and tokenization must be done here. 
        '''
        length = 0
        docfiles = glob.glob("%s*" % self.inputdir)
        labelfiles = glob.glob("%s*" % self.labeldir)
        
        docfiles = [x for x in docfiles if ".py" not in x]
        labelfiles = [x for x in labelfiles if ".py" not in x]
      
        # match annotations with documents
        labelmap = {fname.split("/")[-1].split(".")[0]:fname for fname in labelfiles}
        docmap = {fname.split("/")[-1]:fname for fname in docfiles}
        
        # Load annotations
        for uid in labelmap:
            with codecs.open(labelmap[uid],"rU",self.encoding) as f:
                self.annotations[uid] = annotation_parser(f,self.rm_tags)
        
        # Load documents / normalize terms    
        for uid in docmap:
            with codecs.open(docmap[uid],"rU",self.encoding) as f:
                self.documents[uid] = discharge_summary_parser(f,normalize=self.normalize)
                            
        # create labeled documents
        for idx,uid in enumerate(self.annotations):
            self.labels[uid] = annotate_doc(self.annotations[uid], self.documents[uid], uid) 


        #
        # HACK repair sentence boundaries and abbreviations
        #
        for uid in self.documents:
            if uid not in self.labels:
                continue
            sentences, tags = self.documents[uid], self.labels[uid]
            m_sentences, m_tags = self.__repair(sentences,tags)
            
            # sanity check
            if len(reduce(lambda x,y:x+y, m_sentences)) != len(reduce(lambda x,y:x+y, sentences)):
                print len(reduce(lambda x,y:x+y, m_sentences)), len(reduce(lambda x,y:x+y, sentences))
                print "FATAL ERROR"
                sys.exit()




            self.documents[uid] = m_sentences
            self.labels[uid] = m_tags
            
        # index labels and 
        for uid in self.labels:
            tags = {t:1 for t in reduce(lambda x,y:x+y,self.labels[uid])}
            # use sorted tokens to that 'O' has index 0
            for t in sorted(tags.keys(),reverse=1):
                if t not in self.label2index:
                    self.label2index[t] = len(self.label2index)
        
        # index document terms
        for uid in self.documents:
            tokens = {t:1 for t in reduce(lambda x,y:x+y,self.documents[uid])}
            for t in tokens:
                if t not in self.token2index:
                    self.token2index[t] = len(self.token2index)
        
        # create reverse indices
        self.index2token = {idx:term for term,idx in self.token2index.items()}
        self.index2label = {idx:term for term,idx in self.label2index.items()}
        #self.index2uid = {idx:uid for uid,idx in self.uid2index.items()}
  
        
def load_data(rm_tags=[]):
    
    module_path = os.path.dirname(__file__)
    document_dir = "%s/data/medication/documents/" % (module_path)
    annotation_dir = "%s/data/medication/annotations/" % (module_path) 
 
    abbrv = open("%s/data/medication/abbreviations.txt" % (module_path),"rU")
    abbrv = map(lambda x:x.strip(), abbrv.readlines() )
   
    corpus = i2b2MedicationCorpus(document_dir,annotation_dir,
                                  rm_tags=rm_tags,abbrv=abbrv)
    
    return corpus
