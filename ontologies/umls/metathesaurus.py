import sys
import re
import os
import ontologies.umls
from ontologies.umls import config
import database
import networkx as nx


module_path = os.path.dirname(__file__)

class Metathesaurus(object):
    """
    This class hides a bunch of messy SQL queries that interface with a UMLS
    Metathesaurus database instance, snapshots available at:
    
    https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html
    
    The NLM also provides a REST API for similar functionality, but since we
    look at global term sets, network structures, etc. its better to query 
    from a local UMLS database instance. 
    
    All source abbreviations:
    https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/abbreviations.html
    
    TODO: optimize queries. make less hacky overall
    
    """
    def __init__(self, source_vocab=[], cache=True):
        
        self.conn = database.MySqlConn(config.HOST, config.USER, 
                                       config.DATABASE, config.PASSWORD)
        self.conn.connect()
        self.norm = MetaNorm()
        self.semantic_network = ontologies.umls.SemanticNetwork(self.conn)
        
        # source vocabularies (SAB)
        self.source_vocab = source_vocab
        self._concepts = {}
        self._networks = {}
        

    def concept_graph(self, level="CUI", relation=["CHD"],  
                      source_vocab=[], simulate_root=True):
        
        """Build a concept graph for the target relation. 
        
        The REL field contains the relation type and RELA encodes the relation 
        attribute (e.g., may_treat, part_of). Note - relationships are 
        incomplete and under-specified in many cases. 
            
        Parameters
        ----------
        level : string, optional (default=CUI)
            Define nodes as concepts (CUI) or atoms (AUI). 
            
        relation : array, optional (default=["PAR","CHD"])
            Relationship type. Common relation sets include heirarchical
            relations: PAR/CHD (parent/child) and RB/RN (related broadly/narrowly)
            or non-heirarchical SY/RQ (synonym). 
            
        source_vocab : array, optional (default=[])
            Choice of source vocabulary (SAB) impacts network structure. By 
            default, use all UMLS source vocabularies. Useful isolated sets 
            include: MSH, SNOMEDCT_US, RXNORM
        
        simulate_root : Some concept graphs lack a shared root node which
            breaks several measures. This adds a simulated root.
            
        """
        # load cached graph
        key = "%s_%s_%s" % (level,".".join(source_vocab),".".join(relation))
        if key in self._networks:
            return self._networks[key]
        
        # source vocabulary (override class default)
        sab = self._source_vocab_sql(source_vocab) if source_vocab else \
              self._source_vocab_sql(self.source_vocab)
        sab = "" if not sab else sab + " AND"
        
        rel_types ="(%s)" % " OR ".join(["REL='%s'" % rel for rel in relation])

        sql = """SELECT %s1,%s2,REL,RELA FROM MRREL 
                 WHERE %s %s;"""
                 
        sql = sql % (level,level,sab,rel_types)
        results = self.conn.query(sql)
        
        G = nx.DiGraph()
        for row in results:
            parent,child,rel,rela = row
            G.add_edge(parent,child,rel=rel,attribute=rela)
      
        self._networks[key] = G
        return G
        
        
    def _source_vocab_sql(self,source_vocab):
        """Build source vocabulary sql"""
        if source_vocab:
            sab = " OR ".join(["SAB='%s'" % x for x in source_vocab])
            sab = "(%s)" % sab
        else:
            sab = ""
            
        return sab
    
    
    def get_source_vocabulary_defs(self):
        """Return dictionary of UMLS source vocabularies descriptions."""
        sql = "SELECT RSAB,SON,SF,SVER,CENC FROM MRSAB"    
        results = self.conn.query(sql)
        summary = {}
        
        for row in results:
            sab,name,key,ver,enc = row
            summary[sab] = summary.get(sab,[]) + [name]
            
        return summary
    
                
    def get_relations_list(self, counts=False):
        """"Get distinct UMLS relation types and their occurrence count."""
        sql = "SELECT DISTINCT(RELA),count(RELA) FROM MRREL %s GROUP BY RELA"
        
        # restrict source vocabularies
        if self.source_vocab:
            sab = " OR ".join(["SAB='%s'" % x for x in self.source_vocab])
            sql = sql % ("WHERE (%s)" % sab)
        else:
            sql = sql % ""
        
        results = self.conn.query(sql)
        return results if counts else zip(*results)[0]
    
    
    def get_semtypes_list(self, counts=False):
        """ Get distinct UMLS semantic types and their occurrence counts."""
        sql = "SELECT DISTINCT(STY),count(STY) FROM MRSTY GROUP BY STY"
        results = self.conn.query(sql)
        return results if counts else zip(*results)[0]
    
    
    def match_concepts(self, s, source_vocab=[], match_substring=False):
        """Find exact matches to provided string and return CUI set"""
        if not match_substring:
            sql = "SELECT DISTINCT(CUI) FROM MRCONSO WHERE %s STR='%s'"
        else:
            sql = "SELECT DISTINCT(CUI) FROM MRCONSO WHERE %s STR LIKE '%s%%'"
        
        # override object default source vocabulary?
        if source_vocab:
            sab = self._source_vocab_sql(source_vocab)
        else:
            sab = self._source_vocab_sql(self.source_vocab)
        sab = "" if not sab else sab + " AND"
        sql = sql % (sab,s)
        
        results = self.conn.query(sql)
        return [cui[0] for cui in results]
    
    
    def dictionary(self, semantic_type, source_vocab=[], cui_dict=False, 
                   exclude_subtrees=[],
                   ignore_tty=['OAS','OAP','OAF','OAS','FN','OF','MTH_OF',
                               'MTH_IS','LPN','CSN','PCE','N1','AUN','IS']):
        """Build dictionary of UMLS entities 
        
        Parameters
        ----------
        semantic_type: string
            Target UMLS semantic type root
        
        source_vocab: array
            Override object source vocabularies (SAB) used for building
            lexical variations dictionary.
        
        exclude_subtrees: array
            List of subtree root nodes to remove from ontology
        
        cui_dict: boolean
            Instead of strings, return dictionary of CUIs
        
        include_children: boolean
            Include all child nodes from target semantic type. This should
            always remain True
             
        ignore_tty: array
            Ignore certain term types (see docs/concept_schema.txt)
            
        """
        # get all children of provided semantic type
        network = self.semantic_network.graph("isa")
        
        # exclude subtrees
        children = [node for node in nx.bfs_tree(network, semantic_type)]
        if exclude_subtrees:
            rm = [nx.bfs_tree(network, subtree_root).nodes() for subtree_root in exclude_subtrees]
            children = [node for node in children if node not in reduce(lambda x,y:x+y,rm)]
        children = " OR ".join(map(lambda x:"STY='%s'" % x, children))
        
        # override object default source vocabulary?
        if source_vocab:
            sab = self._source_vocab_sql(source_vocab)
        else:
            sab = self._source_vocab_sql(self.source_vocab)
        
        tty = "" if not ignore_tty else "(%s)" % " AND ".join(map(lambda x:"TTY!='%s'" % x, ignore_tty))
        terms = " AND ".join([x for x in [sab,tty] if x])
        
        sql = """SELECT C.CUI,TTY,STR,STY FROM MRCONSO AS C, MRSTY AS S 
                 WHERE %s C.CUI=S.CUI AND (%s)"""
        
        sql = sql % (terms + " AND", children) if terms else sql % (terms,children)
        results = self.conn.query(sql)
        
        # collapse to unique strings
        if not cui_dict:
            vocab = {self.norm.normalize(row[2]):1 for row in results}
        else:
            vocab = {row[0]:1 for row in results}
            
        return vocab.keys()
    
    
    def concept(self, cui, source_vocab=[]):
        """Build UMLS concept, including abbreviations, synonyms, and preferred 
        forms."""
        if cui in self._concepts:
            return self._concepts[cui]
        else: 
            return Concept(cui, self.conn, source_vocab)
    
        
    def relations_on_cui(self, cui, source_vocab=[]):
        """Return set of relations associated with this concept."""
        sql = """SELECT RUI,SL,RELA,CUI1,CUI2 FROM MRREL R 
                 WHERE %s (R.CUI1="%s" OR R.CUI2="%s")
                 AND RELA!='NULL';"""
        
        # override object default source vocabulary?
        if source_vocab:
            sab = self._source_vocab_sql(source_vocab)
        else:
            sab = self._source_vocab_sql(self.source_vocab)
        sab = "" if not sab else sab + " AND"
        
        sql = sql %  (sab,cui,cui)
        results = self.conn.query(sql)
        return results
            
            
    def relations_between_cui(self, cui1, cui2):
        """
        Return set of relations between provided concepts
        TODO
        """
        pass


    def relations(self, sty1, sty2, rela, source_vocab=[]):
        """Return set of relations between provided semantic types"""
        # collect descendant/child types for each semantic type
        network = self.semantic_network.graph("isa")
        sty1 = [node for node in nx.bfs_tree(network, sty1)]
        sty2 = [node for node in nx.bfs_tree(network, sty2)]
        sty1 = " OR ".join(map(lambda x:"STY='%s'" % x, sty1))
        sty2 = " OR ".join(map(lambda x:"STY='%s'" % x, sty2))
        
        # override object default source vocabulary?
        if source_vocab:
            sab = self._source_vocab_sql(source_vocab)
        else:
            sab = self._source_vocab_sql(self.source_vocab)
        sab = "" if not sab else sab + " AND"
        
        sql = """
        SELECT DISTINCT CUI2,CUI1 FROM 
        (SELECT * FROM MRREL WHERE RELA='%s') AS R,
        (SELECT L.CUI FROM MRCONSO AS L, MRSTY AS LS WHERE (%s) AND L.CUI=LS.CUI) AS LARG,
        (SELECT R.CUI FROM MRCONSO AS R, MRSTY AS RS WHERE (%s) AND R.CUI=RS.CUI) AS RARG
        WHERE %s ((LARG.CUI=CUI2) AND (RARG.CUI=CUI1));"""
       
        sql = sql % (rela,sty1,sty2,sab)
        results = self.conn.query(sql)
        
        return results
    
    
class MetaNorm(object):
    """
    Normalize UMLS Metathesaurus concept strings. 
    """
    def __init__(self, function=lambda x:x):
        self.function = function
    
    def normalize(self,s):
        """Heuristics for stripping non-essential UMLS string clutter"""
        s = s.replace("--"," ")
        s = re.sub("[(\[<].+[>)\]]$", "", s)
        s = re.sub("(\[brand name\]|[,]* NOS)+","", s).strip()
        s = s.strip().strip("_").strip(":")
        
        # custom normalize function
        s = self.function(s)
        return s


class Concept(object):
    
    def __init__(self, cui, conn, source_vocab=[]):
        
        self.cui = cui
        self.source_vocab = source_vocab
        self.conn = conn
        
        # see docs/concept_schema for an explanation of these term type flags
        self.ignore_tty ={x:0 for x in ['OAS','OAP','OAF','OAS','FN','OF',
                                        'MTH_OF','MTH_IS','LPN','CSN',
                                        'PCE','N1','AUN','IS']}
        self.synset = {x:0 for x in ['SY','SYN','SS','VSY','USY','RSY']}
        self.abbrvset = {x:0 for x in ['AA','AB','ACR']}
        self.term_types = ",".join(["'%s'" % tty for tty in self.ignore_tty])
        
        sql = """SELECT TTY,STR,ISPREF FROM MRCONSO 
                 WHERE CUI='%s' AND TTY NOT IN (%s)"""
        sql = sql % (self.cui,self.term_types)
        results = self.conn.query(sql)
        
        self._definition = {}
        self._preferred, self._terms = {},{}
        
        for row in results:
            tty,string,ispref = row
            self._terms[string] = tty
            
        #print(self._terms.keys()) 
               
    def definition(self,source_vocab=[]):
        """There are often multiple definitions conditioned on source vocabulary."""
        source_vocab = self.source_vocab if not source_vocab else source_vocab
        sab = "(%s)" % (" OR ".join(["SAB='%s'" % x for x in source_vocab]))
        sab = "" if not source_vocab else sab + " AND"
          
        sql = "SELECT DEF FROM MRDEF WHERE %s CUI='%s'" % (sab,self.cui)
       
        results = self.conn.query(sql)
        return results
        
                
    def preferred_term(self):
        """Preferred name. Don't know what this practically translates too since
        it isn't unique with concepts, atoms or source ontologies."""
        
        sql = """SELECT STR FROM MRCONSO WHERE CUI='%s' AND 
                 STT='PF' AND ISPREF='Y' AND TS='P';""" % self.cui
        results = self.conn.query(sql)
        return [x[0] for x in results]
        
        
    def synonyms(self):
        """UMLS defines several classes of synonymy, use only subset"""
        return [s for s in self._terms 
                     if self._terms[s] in self.synset]
    
    
    def abbrvs(self):
        """Abbreviations and acronyms"""
        return [s for s in self._terms 
                     if self._terms[s] in self.abbrvset]
        
        
    def all_terms(self):
        """All unique terms linked to this concept"""
        return list(set(self._terms))
    
    
    def print_summary(self):
        """Ugly function to print concept object attributes."""
        print("-----------------------------")
        # use longest string for description
        definition = self.definition()
        if definition:
            definition = sorted(definition,key=lambda x:len(x[0]),reverse=1)[0][0]
        else: 
            definition = "N/A"
            
        fmt = '{0:16} {1:>1}'
        print(fmt.format("CUI:",self.cui))
        print(fmt.format("Definition:", definition))
        print(fmt.format("Preferred Term:", ", ".join(self.preferred_term())))
        print(fmt.format("Synonyms:", ", ".join(self.synonyms())))
        print(fmt.format("Abbreviations:", ", ".join(self.abbrvs())))
        print(fmt.format("TERMS:", ", ".join(self.all_terms()) ))
        print("-----------------------------")
        
