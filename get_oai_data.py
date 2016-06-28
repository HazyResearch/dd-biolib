import re
import os
import random
import codecs
import mechanize
import cookielib
import numpy as np

def Browser():
    '''virtual web browser'''
    user_agents = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9"]
    browser = mechanize.Browser()
    cookies = cookielib.LWPCookieJar()
    browser.set_cookiejar(cookies)
    browser.set_handle_equiv(True)
    browser.set_handle_gzip(True)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False) 
    browser.addheaders = [('User-agent', user_agents[0])]
    return browser

####################################################################
# Fetch PMC XML documents
####################################################################

URL = "http://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:{}&metadataPrefix={}"
INFILE = "/Users/fries/Desktop/hilda-demo/corpora/pmc-ortho-subset-files.txt"
OUTDIR = "/Users/fries/Desktop/hilda-demo/corpora/pmc-ortho/"
NUM_DOCS = 1000

# load target journal subset
pmcfiles = [x.strip().split("\t") for x in open(INFILE,"rU").readlines()]
pmcfiles = [x[2] for x in pmcfiles if len(x) >= 3]

urls = []
for uid in pmcfiles:
    m  = re.search("(PMID|PMC):*(\d+)",uid)
    if not m:
        continue
    idtype,uid = m.group(1),m.group(2)
    if idtype != "PMC":
        continue
    query = URL.format(uid,idtype.lower())
    urls += [(uid,query)]
    
# select random subset
np.random.seed(123456)    
np.random.shuffle(urls)

# query from PMC site
browser = Browser()
for i in range(0,NUM_DOCS):
    uid,url = urls[i]
    outfname = "{}{}.xml".format(OUTDIR,uid)
    if os.path.exists(outfname):
        continue
    
    try:
        response = browser.open(url)
        xml = response.read().decode("utf-8")
        with codecs.open(outfname,"w","utf-8") as f:
            f.write(xml)
    except Exception as e:
        print("ERROR downloading PMC {} - {}".format(uid,e))
    
print("Downloaded {} PMC articles".format(NUM_DOCS))
