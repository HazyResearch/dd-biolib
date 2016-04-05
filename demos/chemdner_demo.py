# -*- coding: utf-8 -*-
import sys
import umls
import codecs
from ddlite import *
from datasets import *
from utils import unescape_penn_treebank
from lexicons.matchers import DistributionalSimilarityMatcher
import operator

def rule_tokenizer(s):
    
    s = re.sub("([,?!:;] )",r" \1",s)
    s = re.sub("([.]$)",r" .",s)
    return s.split()

class RuleTokenizedDictionaryMatch(DictionaryMatch):
    '''Match entities using a simpler tokenizer rule than 
    what's provided by CoreNLP
    '''
    def __init__(self, label, dictionary, ignore_case=True,
                 tokenizer=lambda x:x.split()):
        super(RuleTokenizedDictionaryMatch, self).__init__(label, dictionary,
                                                             'words', ignore_case)
        self.tokenizer = tokenizer
        
    def align(self, a, b):
        
        #if len(a_offsets) != len(b_offsets):
        a_offsets = reduce(lambda x,y:x+y,[[i] * len(w) for i,w in enumerate(a)])
        b_offsets = reduce(lambda x,y:x+y,[[i] * len(w) for i,w in enumerate(b)])
        
        mapping = {}
        for i,j in zip(a_offsets,b_offsets):
            if i not in mapping:
                mapping[i] = {}
            mapping[i][j] = 1
            
        return {i:mapping[i].keys() for i in mapping}
        
    
    def apply(self, s):
        '''
        # create offset mapping between chars and tokens
        # parser token offsets mapping top rule offsets. 
        '''
        # apply tokenizer to raw text
        seq = self.tokenizer(s.text.strip())
        offsets = [idx - s.token_idxs[0] for idx in s.token_idxs]
        tokens = unescape_penn_treebank(s.words)
        mapping = self.align(seq,tokens)
                
        # Loop over all ngrams
        for l in self.ngr:
            for i in range(0, len(seq)-l+1):
                phrase = ' '.join(seq[i:i+l])
                phrase = phrase.lower() if self.ignore_case else phrase
                if phrase in self.dl[l]:
                    '''
                    print(" ".join(s.words))
                    print(phrase)
                    print("OFFSET"," ".join(s.words[i:i+l]))
                    print(" ".join(seq[i:i+l]))
                    
                    offsets = reduce(lambda x,y:x+y,[mapping[idx] for idx in range(i, i+l)])
                    print min(offsets),max(offsets)
                    print tokens[min(offsets):max(offsets)+1]
                    print("-----")
                    '''
                    offsets = reduce(lambda x,y:x+y,[mapping[idx] for idx in range(i, i+l)])
                    yield list(range(min(offsets), max(offsets)+1)), self.label
                    #yield list(range(i, i+l)), self.label


# ==========================================================================================

# parse our corpus, saving CoreNLP results at cache_path
parser = SentenceParser()
corpus = ChemdnerCorpus('../datasets/chemdner_corpus/', parser=parser, 
                        cache_path="/users/fries/desktop/cache/")

train_set = [pmid for pmid in corpus.cv["training"].keys()[:100]]
#dev_set = [pmid for pmid in corpus.cv["development"].keys()[:100]]

'''
d = {}
for pmid in train_set:
    annotations = corpus.annotations[pmid] if pmid in corpus.annotations else []
    d.update({label.text:1 for label in  annotations})

for word in d:
    print word
'''
'''
for pmid in train_set:
    sentences = corpus[pmid]["sentences"]
    annotations = corpus.annotations[pmid] if pmid in corpus.annotations else []
    print len(sentences)
    print len(annotations)
    print [s.token_idxs for s in sentences]
    if annotations:
        print annotations[0]
'''
for pmid in train_set:
    sentences = corpus[pmid]["sentences"]
    for sent in sentences:
        if "DINCH" in sent.text:
            print sent.text
            print " ".join(sent.words)
            
sys.exit()


# load the first 100 training documents and collapse all sentences into a single list

documents = {pmid:corpus[pmid]["sentences"] for pmid in train_set}
sentences = reduce(lambda x,y:x+y, documents.values())

# load gold annotation tags
annotations = [corpus.annotations[pmid] for pmid in train_set if pmid in corpus.annotations]
annotations = reduce(lambda x,y:x+y, annotations)
annotations = [a.text for a in annotations]

print("%d PubMed abstracts" % len(documents))
print("%d true chemical entity mentions" % len(annotations))
word_n = sum([len(sent.words) for sent in sentences])
print("%d tokens" % word_n)









regex_fnames = ["../datasets/regex/chemdner/patterns.txt"]

# dictionaries from tmChem & the UMLS
dict_fnames = ["../datasets/dictionaries/chemdner/mention_chemical.txt",
              "../datasets/dictionaries/chemdner/chebi.txt",
              "../datasets/dictionaries/chemdner/addition.txt",
              "../datasets/dictionaries/umls/substance-sab-all.txt",
              "../datasets/dictionaries/chemdner/train.chemdner.vocab.txt"]

chemicals = []
for fname in dict_fnames:
    chemicals += [line.strip().split("\t")[0] for line in open(fname,"rU").readlines()]
    
regexes = []
for fname in regex_fnames:
    regexes += [line.strip() for line in open(fname,"rU").readlines()]   

# create matchers and extract candidates
extr1 = DictionaryMatch('C', chemicals, ignore_case=True)
extr2 = RuleTokenizedDictionaryMatch('C', chemicals, ignore_case=True, tokenizer=rule_tokenizer)
#extr2 = AllUpperNounsMatcher('C')
#extr3 = RegexMatch('C', regexes[0], ignore_case=True)
#extr4 = RegexMatch('C', regexes[1], ignore_case=False)
#extr5 = RegexMatch('C', regexes[2], ignore_case=False)
matcher = MultiMatcher(extr2)#, extr2) #, extr4, extr5)

candidates = Entities(sentences, matcher)

# Crude recall estimate (ignores actual span match and tokenization problems)
mentions = [" ".join(unescape_penn_treebank([e.words[i] for i in e.idxs])) for e in candidates]
gold_mentions = [term for term in annotations]

for m in mentions:
    if m in gold_mentions:
        gold_mentions.remove(m)
tp = len(annotations) - len(gold_mentions)

print("Found %d candidate entities" % len(candidates))
print("Candidates: %.2f%% of all tokens" % (len(candidates)/float(word_n) * 100) )
print("Annotations %.2f%% of all tokens" % (len(annotations)/float(word_n) * 100) )

print("~recall: %.2f (%d/%d)" % (float(tp) / len(annotations), tp, len(annotations)))

#for m in mentions:
#    print(m)

mentions = {term:1 for term in mentions}
missed = [term for term in annotations if term not in mentions]
missed = {term:missed.count(term) for term in missed}

for term in sorted(missed.items(),key=operator.itemgetter(1),reverse=1):
    print("%s: %d" % (term[0], missed[term[0]]))

sys.exit()

'''
regex_fnames = ["../datasets/regex/chemdner/patterns.txt"]

# dictionaries from tmChem
dict_fnames = ["../datasets/dictionaries/chemdner/mention_chemical.txt",
              "../datasets/dictionaries/chemdner/chebi.txt",
              "../datasets/dictionaries/chemdner/addition.txt"]

chemicals = []
for fname in dict_fnames:
    chemicals += [line.split("\t")[0] for line in open(fname,"rU").readlines()]

regexes = []
for fname in regex_fnames:
    regexes += [line.strip() for line in open(fname,"rU").readlines()] 

# build UMLS dictionary of substances (rather than query DB)
dfile = "../datasets/dictionaries/umls/substance-sab-all.txt"
if os.path.exists(dfile):
    d = {term.strip():1 for term in open(dfile,"rU").readlines()}
else:
    meta = umls.Metathesaurus()
    norm = umls.MetaNorm(function=lambda x:x.lower())
    d = meta.dictionary("Substance")
    d = map(norm.normalize,d)
    print("Found %d distinct terms" % len(d))
    with codecs.open(dfile,"w","utf-8") as f:
        for term in d:
            if term.strip() != "":
                try:
                    f.write(term)
                    f.write("\n")
                except:
                    print term
                    
chemicals += d.keys()

extr1 = DictionaryMatch('C', chemicals, ignore_case=True)
extr2 = RuleTokenizedDictionaryMatcher('C', chemicals, ignore_case=True)
#extr2 = RegexMatch('C',regexes[0], ignore_case=True)
#extr3 = RegexMatch('C',regexes[2], ignore_case=False)


# slow -- also need to compute better embeddings
#embeddings = "/Users/fries/Desktop/chemdner_embeddings/embeddings/words.d128.w10.m0.i10.bin"
#extr4 = DistributionalSimilarityMatcher('C', embeddings, chemicals, 
#                                        knn=10, match_threshold=0.3, ignore_case=False)
matcher = MultiMatcher(extr1,extr2)

'''

n,N = 0.0, 0.0
cand_n = 0
missed = []
'''



for pmid in documents:
    sentences = documents[pmid]
    candidates = [m for m in Entities(sentences,matcher)]
    
    if pmid not in corpus.annotations:
        continue
    
    #print [m.text for m in corpus.annotations[pmid]]
    #mentions = get_mention_text(candidates)
    
    annotations = [m.text for m in corpus.annotations[pmid]]
    counter = len(annotations)
    
    for m in mentions:
        if m in annotations:
            annotations.remove(m)
  
    n += counter - len(annotations)
    N += counter
    missed += annotations
    cand_n += len(candidates)
   
    if mentions:
        for m in  mentions:
            print m

missed = {term:missed.count(term) for term in missed}
'''

'''
regex = re.compile("^[αβΓγΔδεϝζηΘθικΛλμνΞξοΠπρΣστυΦφχΨψΩω]+[-]")
for term in missed:
    if regex.match(term):
        print "*",term
#    print term #, missed[term]
'''

print n, N, len(missed)
print "%.3f" % (n/N)
print "candidates: %d" % cand_n
