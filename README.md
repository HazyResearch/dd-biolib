# DeepDive Biomedical Library

This module consists of tools for iterating over biomedical document collections, interacting with biomedical ontologies, creating dictionaries for labeling entity candidates, and writing learning functions for use in distant supervision tasks. 

## Installing dd-biolib

### Dependencies 

* [mysql-connector-python](https://dev.mysql.com/downloads/connector/python/)
* [psycopg2](http://initd.org/psycopg/)
* [networkx](https://networkx.github.io)
* [sklearn](https://github.com/scikit-learn/scikit-learn)
* [gensim](https://github.com/piskvorky/gensim)

We provide a simple way to install everything using `virtualenv`:

```bash
# set up a Python virtualenv
virtualenv .virtualenv
source .virtualenv/bin/activate

pip install --requirement python-package-requirement.txt
```

### Setup ddlite/treedlib tools

Make certain you've pulled the most current version of ddlite from github. Then copy (or symlink) `ddlite` into `dd-biolib/ddlite` and `ddlite/treedlib/treedlib/` into `dd-biolib/treedlib`.

### Corpus Tools

We provide 2 basic corpus object for iterating and parsing document collections: `PubMedAbstractCorpus` for PubMed Abstracts and `PubMedCentralCorpus` for XML documents from the [PMC Open Access Subset](http://www.ncbi.nlm.nih.gov/pmc/tools/ftp/). Please see
`dd-biolib/examples` for examples of how to use these objects. 

## Jupyter Notebooks

### UMLS Metathesauraus Tools 
This notebook provides an overview of how to interact with the UMLS for 
creating dictionaries or accessing concepts and their synonym sets, navigating
onotologies, etc. 

### Chemical Name Extraction Demo
The `ChemicalExtractor.ipynb` notebook looks at a real benchmark data set for tagging chemical named entities
in biomedical literature. We show a simple walk-through on how to generate candidates
and write learning functions for `ddlite`.

