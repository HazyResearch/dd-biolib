# -*- coding: utf-8 -*-
import sys
import umls
import codecs
from ddlite import *
from datasets import *
from utils import unescape_penn_treebank
from lexicons.matchers import DistributionalSimilarityMatcher

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
        
    def _create_mapping(self,seq1,seq2):
        assert "".join(seq1) == "".join(seq2)
        pass
        
    def align(self, a, b):
        
        if not "".join(a) == "".join(b):
            print " ".join(a)
            print "".join(a)
            print "".join(b)
        
        assert "".join(a) == "".join(b)
        
        a = " ".join(a)
        b = " ".join(b)

        j = 0
        offsets = []
        for i in range(0,len(a)):
            if a[i] in [" "]:
                continue
            matched = False
            
            while not matched and j < len(b):
                if a[i] == b[j]:
                    offsets += [(i,j,a[i],b[j])]
                    matched = True
                j += 1
                
        return offsets
    
    def apply(self, s):
        # apply tokenizer to raw text
        seq = self.tokenizer(s.text.strip())
        # create offset mapping between chars and tokens
        offsets = [idx - s.token_idxs[0] for idx in s.token_idxs]
        tokens = unescape_penn_treebank(s.words)
        
        
        mapping = self.align(tokens,seq)
        print mapping
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
                    print("-----")
                    '''
                    yield list(range(i, i+l)), self.label


# ==========================================================================================

# parse our corpus, saving CoreNLP results at cache_path
parser = SentenceParser()
corpus = ChemdnerCorpus('../datasets/chemdner_corpus/', parser=parser, cache_path="/users/fries/desktop/cache/")

# load the first 100 training documents and collapse all sentences into a single list
pmids = [pmid for pmid in corpus.cv["training"].keys()[:100]]
documents = {pmid:corpus[pmid]["sentences"] for pmid in pmids}
sentences = reduce(lambda x,y:x+y, documents.values())

# load gold annotation tags
annotations = [corpus.annotations[pmid] for pmid in pmids if pmid in corpus.annotations]
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
              "../datasets/dictionaries/umls/substance-sab-all.txt"]

chemicals = []
for fname in dict_fnames:
    chemicals += [line.strip().split("\t")[0] for line in open(fname,"rU").readlines()]
    
regexes = []
for fname in regex_fnames:
    regexes += [line.strip() for line in open(fname,"rU").readlines()]   

# create matchers and extract candidates
#extr1 = DictionaryMatch('C', chemicals, ignore_case=True)
extr1 = RuleTokenizedDictionaryMatch('C', chemicals, ignore_case=True, tokenizer=rule_tokenizer)
#extr2 = AllUpperNounsMatcher('C')
#extr3 = RegexMatch('C', regexes[0], ignore_case=True)
#extr4 = RegexMatch('C', regexes[1], ignore_case=False)
#extr5 = RegexMatch('C', regexes[2], ignore_case=False)
matcher = MultiMatcher(extr1)#,extr2)#, extr3, extr4, extr5)

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

for m in mentions:
    print(m)

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
