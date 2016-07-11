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
    return text

