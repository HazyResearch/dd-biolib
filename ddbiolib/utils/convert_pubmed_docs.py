

#227508|t|Naloxone reverses the antihypertensive effect of clonidine.
#227508|a|In unanesthetized, spontaneously hypertensive rats the decrease in blood pressure and heart rate produced by intravenous clonidine, 5 to 20 micrograms/kg, was inhibited or reversed by nalozone, 0.2 to 2 mg/kg. The hypotensive effect of 100 mg/kg alpha-methyldopa was also partially reversed by naloxone. Naloxone alone did not affect either blood pressure or heart rate. In brain membranes from spontaneously hypertensive rats clonidine, 10(-8) to 10(-5) M, did not influence stereoselective binding of [3H]-naloxone (8 nM), and naloxone, 10(-8) to 10(-4) M, did not influence clonidine-suppressible binding of [3H]-dihydroergocryptine (1 nM). These findings indicate that in spontaneously hypertensive rats the effects of central alpha-adrenoceptor stimulation involve activation of opiate receptors. As naloxone and clonidine do not appear to interact with the same receptor site, the observed functional antagonism suggests the release of an endogenous opiate by clonidine or alpha-methyldopa and the possible role of the opiate in the central control of sympathetic tone.

import re
import codecs

def fix(s):
    matches = re.findall("[a-z]{2}[.][A-Z]{1,}[a-z]*",s)
    if matches:
        for m in matches:
            s = s.replace(m, m.replace(u".", u". "))
    return s

samples = 10000

infile = "/users/fries/query_pubmed.100000.txt"
outfile = "/users/fries/pubmed.unlabled.{}.txt".format(samples)

with codecs.open(infile,"rU","utf-8") as fp, codecs.open(outfile,"w","utf-8") as op:
    for i,line in enumerate(fp):
        row = line.strip().split("\t")
        pid,title,abstract,mesh = row

        title = fix(title)
        abstract = fix(abstract)

        op.write(u"{}|t|{}\n".format(pid, title))
        op.write(u"{}|a|{}\n\n".format(pid, abstract))

        fix(line)
        if i > samples:
            break