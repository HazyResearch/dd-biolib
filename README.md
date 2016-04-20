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

### Corpus Tools

We provide 2 basic corpus object for iterating and parsing document collections: `PubMedAbstractCorpus` for PubMed Abstracts and `PubMedCentralCorpus` for XML documents from the [PMC Open Access Subset](http://www.ncbi.nlm.nih.gov/pmc/tools/ftp/). Please see
`ddbiolib/examples` for examples of how to use these objects. 

## Jupyter Notebooks

### UMLS Metathesauraus Tools 
`examples/UmlsMetathesaurus.ipynb`

This notebook provides an overview of how to interact with the UMLS for 
creating dictionaries or accessing concepts and their synonym sets, navigating
onotologies, etc. 

See the dd-bio-examples repo for some example taggers
