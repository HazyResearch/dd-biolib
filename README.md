# Snorkel Biomedical Tools

This module consists of Snorkel tools for iterating over biomedical document collections, interacting with biomedical ontologies, and creating dictionaries for labeling entities.

## Installing ddbiolib

The fastest way to use ddbiolib is to create a workspace folder and install the following python modules:

```
mkdir ddbio-workspace
cd ddbio-workspace
git clone https://github.com/HazyResearch/ddlite.git
git -C ddlite submodule init
git -C ddlite submodule update
cp ddbiolib/examples/notebooks/* .
```

### Dependencies 

* [mysql-connector-python](https://dev.mysql.com/downloads/connector/python/)
* [psycopg2](http://initd.org/psycopg/)
* [networkx](https://networkx.github.io)
* [sklearn](https://github.com/scikit-learn/scikit-learn)
* [gensim](https://github.com/piskvorky/gensim)


We provide a simple way to install everything using `virtualenv`:

```bash
### set up a Python virtualenv
virtualenv .virtualenv
source .virtualenv/bin/activate

pip install --requirement python-package-requirement.txt
```
