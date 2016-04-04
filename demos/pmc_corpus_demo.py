#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from ddlite import *
from datasets import PubMedCentralCorpus
import codecs

#
# PubMedCentral Corpus
#
inputdir = "/Users/fries/Desktop/pmc/"
parser = SentenceParser()
#corpus = PubMedCentralCorpus(inputdir, parser, cache_path="/tmp")


s = u"The growth of Staphylococcus aureus with the IC50 value of Staphylococcus aureus with the IC50 value of 87.81 µg mL(-1)."
sentences = [x for x in parser.parse(s)]
for s in sentences:
    print " ".join(s.words)
sys.exit()

corpus = [x.strip().split("\t") for x in open("/Users/fries/Code/dd-biolib/datasets/chemdner_corpus/training.abstracts.txt","rU").readlines()]

for s in corpus:
    
    try:
        doc = parser.parse(s[2].decode("ascii").encode("utf-8"))
        for sent in doc:
            print sent
    except Exception as e:
        print e
        sys.exit()


# we iterate through documents
for i,doc in enumerate(corpus):
    for sentence in doc["sentences"]:
        print sentence
    break

# look at specific metadata
for i,doc in enumerate(corpus):
    for attribute in doc["metadata"]:
        print "%s: %s" % (attribute, doc["metadata"][attribute])
    break

# PMC articles also have structure which is useful to consider
# e.g., only looking at text from the "Methods and Materials" section 
for i,doc in enumerate(corpus):
    for title,section in zip(doc["section-titles"],doc["sections"]):
        for sentence in section:
            print "******%s******" % title, sentence 
    break
