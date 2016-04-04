
def unescape_penn_treebank(words):
    '''Replace PennTreeBank tags'''
    repl = dict([('-LRB-','('), ('-RRB-',')'), ('-LCB-','{'), ('-RCB-','}'),
                 ('-LSB-','['),('-RSB-',']'),("``",'"'),("''",'"')])
    return [repl[w] if w in repl else w for w in words]