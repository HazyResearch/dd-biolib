from collections import namedtuple

DatabaseConfig = namedtuple("DatabaseConfig",["host","username","dbname","password"])

DEFAULT_UMLS_CONFIG = DatabaseConfig(host="127.0.0.1",
                                     username="umls",
                                     dbname="2014AB",
                                     password="")

STANFORD_UMLS_CONFIG = DatabaseConfig(host="rocky.stanford.edu",
                                     username="umls_guest",
                                     dbname="publicUMLSsnapshot",
                                     password="umls")
