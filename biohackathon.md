# Biohackathon Instructions

####Friday April 8th  9AM - 6PM

**HanaHaus**
Conference Room #2

456 University Ave, Palo Alto, CA 94301

## Software

Please download [ddlite](https://github.com/HazyResearch/ddlite) and [dd-biolib](https://github.com/HazyResearch/dd-biolib) and install any dependecies as needed (natively or via virtualenv.) Specific issues are outlined at each packages github page. 

## Examples 

We provide several [Jupyter](http://jupyter.org) notebooks that nicely combine code and text to outline the extraction workflow. Please familiarize yourself with these, especially the *Learning notebooks, which we'll use during the hackathon. If you prefer working with just python scripts, then there are several code skeletons in dd-biolib/examples/

#### Entity Extraction Notebooks

`ddlite/examples/`

- GeneTaggerExample_Extraction.ipynb
- GeneTaggerExample_Learning.ipynb

`dd-biolib/`

- ChemicalExtractor.ipynb
- ChemicalLearning.ipynb

#### Entity Extraction Python Skeletons

`dd-biolib/examples/`

- chemical_extraction_demo.py
- pmc_corpus_demo.py
- pubmed_corpus_demo.py

## Hackathon Preparation

Before the hackathon, please write your own extractor and pre-generate a candidate entity pickle file. It's best to directly follow one of the notebooks or python skeleton files, but this is the broad overview:

#### 1. Download a Dataset

Several biomedical corpora, dictionaries, and word embedding datasets are available in this dropbox folder. For target tasks, it's best to stick with PMC or PubMed data 

 [bio-datasets](https://www.dropbox.com/sh/dtn6sqqgrgc0dda/AADdZB23vv_JKTja922KdoCua?dl=0)


#### 2. Create Dictionaries

Several example dictionaries are provided in the bio-datasets folder. You can provide your own or create new ones using UMLS dictionary building tool. A list of all *semantic types* (STYs) is available in dd-biolib/umls/docs/

`python create_dictionary.py --target "Bacterium" > bacterium.txt`

you can also create an expanded dictionary using word embeddings (see bio-datasets)

`python create_dictionary.py --target "Bacterium" --embeddings pubmed-17k/contextwin5/words.d128.w5.m0.i10.bin --knn 2 > bacterium.knn2.txt`

#### 3. Build Matchers

The easiest way to identify candidates is through simple string matching using a dictionary of known entity names. 

- **DictionaryMatch** Match to an existing dictionary of known entity names.

- **RegexMatcher** Match words according to simple regular expressions. Here we just match Greek letters and  simple patterns of the form -3,4- which tend to indicate chemical names.

- **RuleTokenizedDictionaryMatch** Match a dictionary under a different tokenization scheme (in this case we provide a whitespace tokenizer. The resulting labels are mapped back into our primary CoreNLP token space.

- **AllUpperNounsMatcher** (From the Gene Tagger example) Identify all uppercase nouns in text.

#### 4. Extract Candidates
Run your extraction code, creating CoreNLP parse dumps of your documents and a pickle file of all candidate entities. Parsing documents with CoreNLP can take some time, so please make certain this is done before the hackathon!

