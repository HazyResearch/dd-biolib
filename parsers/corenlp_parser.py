'''
CoreNLP wrapper
@authors Alex Ratner, Henry Ehrenberg, Others

'''
import os
import sys
import json
import atexit
import signal
import requests
from subprocess import Popen
from collections import defaultdict
from .base import Sentence,SentenceParser

def sort_X_on_Y(X, Y):
    return [x for (y,x) in sorted(zip(Y,X), key=lambda t : t[0])]    

def corenlp_cleaner(words):
    d = {'-RRB-': ')', '-LRB-': '(', '-RCB-': '}', '-LCB-': '{',
       '-RSB-': ']', '-LSB-': '['}
    return map(lambda w: d[w] if w in d else w, words)

class CoreNlpParser(SentenceParser):
    def __init__(self, tok_whitespace=False):
        super(CoreNlpParser, self).__init__(tok_whitespace)
        # http://stanfordnlp.github.io/CoreNLP/corenlp-server.html
        # Spawn a StanfordCoreNLPServer process that accepts parsing requests at an HTTP port.
        # Kill it when python exits.
        # This makes sure that we load the models only once.
        # In addition, it appears that StanfordCoreNLPServer loads only required models on demand.
        # So it doesn't load e.g. coref models and the total (on-demand) initialization takes only 7 sec.
        self.port = 12345
        self.tok_whitespace = tok_whitespace
        loc = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'parser')
        cmd = ['java -Xmx4g -cp "%s/*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer --port %d > /dev/null' % (loc, self.port)]
        self.server_pid = Popen(cmd, shell=True).pid
        atexit.register(self._kill_pserver)
        props = "\"tokenize.whitespace\": \"true\"," if self.tok_whitespace else "" 
        self.endpoint = 'http://127.0.0.1:%d/?properties={%s"annotators": "tokenize,ssplit,pos,lemma,depparse", "outputFormat": "json"}' % (self.port, props)

        # Following enables retries to cope with CoreNLP server boot-up latency
        # See: http://stackoverflow.com/a/35504626
        from requests.packages.urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        self.requests_session = requests.Session()
        retries = Retry(total=None,
                        connect=20,
                        read=0,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        self.requests_session.mount('http://', HTTPAdapter(max_retries=retries))


    def _kill_pserver(self):
        if self.server_pid is not None:
            try:
                os.kill(self.server_pid, signal.SIGTERM)
            except:
                sys.stderr.write('Could not kill CoreNLP server. Might already got killt...\n')

    def parse(self, s, doc_id=None, doc_name=None):
        """Parse a raw document as a string into a list of sentences"""
        if len(s.strip()) == 0:
            return
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        resp = self.requests_session.post(self.endpoint, data=s, allow_redirects=True)
        s = s.decode('utf-8')
        content = resp.content.strip()
        if content.startswith("Request is too long") or content.startswith("CoreNLP request timed out"):
            raise ValueError("File {} too long. Max character count is 100K".format(doc_id))
        blocks = json.loads(content, strict=False)['sentences']
        sent_id = 0
        for block in blocks:
            parts = defaultdict(list)
            dep_order, dep_par, dep_lab = [], [], []
            for tok, deps in zip(block['tokens'], block['basic-dependencies']):
                parts['words'].append(tok['word'])
                parts['lemmas'].append(tok['lemma'])
                parts['poses'].append(tok['pos'])
                parts['char_offsets'].append(tok['characterOffsetBegin'])
                dep_par.append(deps['governor'])
                dep_lab.append(deps['dep'])
                dep_order.append(deps['dependent'])
            parts['dep_parents'] = sort_X_on_Y(dep_par, dep_order)
            parts['dep_labels'] = sort_X_on_Y(dep_lab, dep_order)
            parts['sent_id'] = sent_id
            parts['doc_id'] = doc_id
            parts['text'] = s[block['tokens'][0]['characterOffsetBegin'] : 
                                block['tokens'][-1]['characterOffsetEnd']]
            parts['doc_name'] = doc_name
            parts['id'] = "%s-%s" % (parts['doc_id'], parts['sent_id'])
            sent = Sentence(**parts)
            sent_id += 1
            yield sent
    
    def parse_docs(self, docs):
        """Parse a list of Document objects into a list of pre-processed Sentences."""
        sents = []
        for doc in docs:
            for sent in self.parse(doc.text, doc.id, doc.file):
                sents.append(sent)
        return sents
        
 



