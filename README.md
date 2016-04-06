# DeepDive Biomedical Library

This module consists of tools for interacting with biomedical ontologies, 
creating dictionaries for labeling entity candidates, and generating distant supervision rules.

## Dependencies 

* [networkx](https://networkx.github.io)
* [mysql-connector-python](https://dev.mysql.com/downloads/connector/python/)
* [psycopg2](http://initd.org/psycopg/)

We provide a simple way to install everything using `virtualenv`:

```bash
# set up a Python virtualenv
virtualenv .virtualenv
source .virtualenv/bin/activate

pip install --requirement python-package-requirement.txt
```
To initalize 
git submodule init --recursive

## Corpus Tools

We provide 2 basic corpus object for iterating and parsing document collections: PubMedAbstractCorpus for PubMed Abstracts and PubMedCentralCorpus for XML documents from the [PMC Open Access Subset](http://www.ncbi.nlm.nih.gov/pmc/tools/ftp/).

## Jupyter Notebooks

### UMLS Metathesauraus Tools 
This notebook provides an overview of how to interact with the UMLS for 
creating dictionaries or accessing concepts and their synonym sets, navigating
onotologies, etc. 

### Chemical Tagger Demo
This notebook looks at a real benchmark data set for tagging chemical named entites
in biomedical literature. We show a simple walkthrough on how to generate candidates
and write distance supervision rules for ddlite

