def strip_unicode_chars(s):
    pass

        
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

def overlaps(a,b):
    return len(set(a).intersection(b)) != 0
    
#
# Terminal Span Highlighting
#
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def highlight_span(text, char_span, window=10):
    
    #print char_span
    pre = text[char_span[0]-window:char_span[0]]
    span = text[char_span[0]:char_span[1]]
    post = text[char_span[1]:char_span[1]+window]
    s = "{}{}{}{}{}{}\n".format(pre,bcolors.BOLD, bcolors.WARNING,span,bcolors.ENDC,post)
    return s