'''
This script fetches data from the PMC ftp site
for FULL articles (images + PDFs + XML)
'''
import sys
from ftplib import FTP

HOST = "ftp.ncbi.nlm.nih.gov"
OUTDIR = "/Users/fries/Desktop/hilda-demo/corpora/test/"
INFILE = "/Users/fries/Desktop/hilda-demo/corpora/pmc-ortho-subset-files.txt"

# connect to PMC ftp service
# see http://www.ncbi.nlm.nih.gov/pmc/tools/ftp/
ftp = FTP(HOST) 
ftp.login() 
ftp.cwd('pub/pmc/') 

# load target journal subset
datfiles = [x.split("\t")[0] for x in open(INFILE,"rU").readlines()]

for fname in datfiles:
    with open("{}{}".format(OUTDIR,fname.split("/")[-1]), "w") as f:
        ftp.retrbinary("RETR " + fname ,f.write)
    print fname

ftp.close()