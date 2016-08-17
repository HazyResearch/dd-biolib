import re

# Originally from http://effbot.org/zone/unicode-gremlins.htm
# Replaced definitions to conform to:
# ftp://ftp.unicode.org/Public/MAPPINGS/VENDORS/MICSFT/WINDOWS/CP1250.TXT
# http://www.microsoft.com/typography/unicode/1252.htm

cp1252 = {
    u"\x80": u"\u20AC",    # EURO SIGN
    u"\x81": u"",          # UNDEFINED
    u"\x82": u"\u201A",    # SINGLE LOW-9 QUOTATION MARK
    u"\x83": u"",          # UNDEFINED
    u"\x84": u"\u201E",    # DOUBLE LOW-9 QUOTATION MARK
    u"\x85": u"\u2026",    # HORIZONTAL ELLIPSIS
    u"\x86": u"\u2020",    # DAGGER
    u"\x87": u"\u2021",    # DOUBLE DAGGER
    u"\x88": u"",          # UNDEFINED
    u"\x89": u"\u2030",    # PER MILLE SIGN
    u"\x8A": u"\u0160",    # LATIN CAPITAL LETTER S WITH CARON
    u"\x8B": u"\u2039",    # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    u"\x8C": u"\u015A",    # LATIN CAPITAL LETTER S WITH ACUTE
    u"\x8D": u"\u0164",    # LATIN CAPITAL LETTER T WITH CARON
    u"\x8E": u"\u017D",    #LATIN CAPITAL LETTER Z WITH CARON
    u"\x8F": u"\u0179",    # LATIN CAPITAL LETTER Z WITH ACUTE
    u"\x90": u"",          # UNDEFINED
    u"\x91": u"\u2018",    # LEFT SINGLE QUOTATION MARK
    u"\x92": u"\u2019",    # RIGHT SINGLE QUOTATION MARK
    u"\x93": u"\u201C",    # LEFT DOUBLE QUOTATION MARK
    u"\x94": u"\u201D",    # RIGHT DOUBLE QUOTATION MARK
    u"\x95": u"\u2022",    # BULLET
    u"\x96": u"\u2013",    # EN DASH
    u"\x97": u"\u2014",    # EM DASH
    u"\x98": u"",          # UNDEFINED
    u"\x99": u"\u2122",    # TRADE MARK SIGN
    u"\x9A": u"\u0161",    # LATIN SMALL LETTER S WITH CARON
    u"\x9B": u"\u203A",    # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    u"\x9C": u"\u015B",    # LATIN SMALL LETTER S WITH ACUTE
    u"\x9D": u"\u0165",    # LATIN SMALL LETTER T WITH CARON
    u"\x9E": u"\u017E",    # LATIN SMALL LETTER Z WITH CARON
    u"\x9F": u"\u017A",    # LATIN SMALL LETTER Z WITH ACUTE
}

def kill_gremlins(text):
    # map cp1252 gremlins to real unicode characters
    if re.search(u"[\x80-\x9f]", text):
        def fixup(m):
            s = m.group(0)
            return cp1252.get(s, s)
        if isinstance(text, type("")):
            # make sure we have a unicode string
            text = unicode(text, "iso-8859-1")
        text = re.sub(u"[\x80-\x9f]", fixup, text)
        # remove ASCII control chars
    return text

def rm_ascii_control_chars(t):
    return re.sub(u"[\x00-\x1F]|[\x7F]", u"", t)
    

def to_conll(corpus, labels, label_key, doc_ids=None):
    '''
    Given a corpus and label key, generate a CoNLL format document
    '''
    # index labels by doc/sent
    idx = {}
    for l in labels:
        doc_id = l.sentence["doc_id"]
        sent_id = l.sentence["sent_id"]
        if doc_id not in idx:
            idx[doc_id] = {}
        if sent_id not in idx[doc_id]:  
            idx[doc_id][sent_id] = []
        idx[doc_id][sent_id] += [l.idxs]
        
    
    n = 0
    sentences = []
    for doc in corpus:
        if doc_ids and doc.doc_id not in doc_ids:
            continue
        for i,sent in enumerate(doc.sentences):
            tags = len(sent.words) * ['O']
            if sent.doc_id in idx and i in idx[sent.doc_id]:
                labels = idx[sent.doc_id][i]
                for lbl in labels:
                    t  = [u"B-{}".format(label_key)]
                    t += [u"I-{}".format(label_key)] * (len(lbl)-1)
                    tags[min(lbl):max(lbl)+1] = t
                    n += 1
            # HACK unicode whitespace character fix (for conlleval script compatibility)
            words = map(lambda x:x.replace(u'\xa0',u'_'), sent.words)
            sentences += [zip(words,tags) ]
           
            
    outstr = []       
    for sent in sentences:
        outstr += ["\n".join(map(lambda x: u"{} {}".format(*x),sent))]
        outstr += [""]
    
    print n
    return "\n".join(outstr)

