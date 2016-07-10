import os
from urllib2 import urlopen, URLError, HTTPError

def download(url,outfname):
    try: 
        data = urlopen(url)
        with open(outfname, "wb") as f:
            f.write(data.read())
    except HTTPError, e:
        print "HTTP Error:", e.code, url
    except URLError, e:
        print "URL Error:", e.reason, url



def unescape_penn_treebank(words):
    '''Replace PennTreeBank tags and other CoreNLP modifications. This is
    pretty much a hack. '''
    
    repl = dict([('-LRB-',u'('), ('-RRB-',u')'), ('-LCB-',u'{'), ('-RCB-',u'}'),("`",u"'"),
                 ('-LSB-',u'['),('-RSB-',u']')]) #,("``",'"'),("''",'"')
    words = [repl[w] if w in repl else w for w in words]
    
    # deal with quotation marks
    rm = False
    for i in range(0,len(words)):
        if words[i] == "``":
            rm = True
            words[i] = '"'
        if rm and words[i] == "''":
            words[i] = '"'
            rm = False        
    return words