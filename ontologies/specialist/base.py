'''
The SPECIALIST Lexicon

"The SPECIALIST lexicon is a large syntactic lexicon of biomedical and general English, 
designed/developed to provide the lexical information needed for the SPECIALIST 
Natural Language Processing System (NLP) which includes SemRep, MetaMap, and the 
Lexical Tools. It is intended to be a general English lexicon that includes many 
biomedical terms. Coverage includes both commonly occurring English words and 
biomedical vocabulary from a variety of sources. These include (not limited to) 
MEDLINE citation records, terms in the Dorland's Illustrated Medical dictionary, 
the 10,000 most frequent words listed in the American Heritage Word Frequency book 
and the 2,000 lexical items used in the controlled definitions of Longman's Dictionary 
of Contemporary English. The lexicon entry for each lexical item (word or term) records 
the syntactic, morphological (inflection and derivation), and orthographic 
(spelling variants) information needed by the SPECIALIST NLP System."

https://lexsrv3.nlm.nih.gov/LexSysGroup/Projects/lexicon/current/web/index.html

@author: jason-fries [at] stanford [dot] edu
'''
import os
from ...utils import download
from urllib2 import urlopen, URLError, HTTPError

def download_dataset(version="2016"):
    '''Download SPECIALIST files. 
    TODO: get full dataset. for now only get abbreviations'''
    url = "https://lexsrv3.nlm.nih.gov/LexSysGroup/Projects/lexicon/{}/release/LEX/LRABR"
    url = url.format(version)
    outfname = "{}/data/{}".format(os.path.dirname(__file__),os.path.basename(url))   
    if not os.path.exists(outfname):
        download(url,outfname)

class SpecialistLexicon(object):
    
    def __init__(self):
        download_dataset()
        self._abbrv2text,self._text2abbrv = self._parse_lrabr()
    
    def _parse_lrabr(self):
        '''Load UMLS SPECIALIST Lexicon of abbreviations. Format:
            E0000048|AA|acronym|E0006859|achievement age|
        '''
        fname = "{}/data/{}".format(os.path.dirname(__file__),"LRABR")
        d = [line.strip().strip("|").split("|") for line in open(fname, 'rb').readlines()]
        abbrv2text,text2abbrv =  {},{}
        for row in d:
            uid1,abbrv,atype,uid2,text = row
            text = text.lower()
            if atype not in ["acronym","abbreviation"]:
                continue
            if abbrv not in abbrv2text:
                abbrv2text[abbrv] = {}
            if text not in text2abbrv:
                text2abbrv[text] = {}
                
            abbrv2text[abbrv][text] = 1
            text2abbrv[text][abbrv] = 1
        
        return abbrv2text,text2abbrv
    
    @property
    def abbrv2text(self):
        return self._abbrv2text

    @property
    def text2abbrv(self):
        return self._text2abbrv

if __name__ == "__main__":
   
    s = SpecialistLexicon()
    print len(s.abbrv2text)
    print len(s.text2abbrv)
    print s.abbrv2text["AMOX"]
    