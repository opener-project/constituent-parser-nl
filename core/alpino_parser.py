#!/usr/bin/env python

import sys
import getopt
import codecs
import os
from VUKafParserPy import KafParser
from lxml import etree
import tempfile
from subprocess import Popen,PIPE
import shutil
import glob
import logging

from tree import Tree

NOTER='nonter'
TER='ter'
EDGE='edge'
noter_cnt=0
ter_cnt=0
edge_cnt=0


#### SET THIS VARIABLE TO YOUR LOCAL FOLDER OF ALPINO
ALPINO_HOME = '/Users/ruben/NLP_tools/Alpino'

logging.basicConfig(stream=sys.stderr,format='%(asctime)s - %(levelname)s - %(message)s',level=logging.DEBUG)

__module_dir = os.path.dirname(__file__)

## Function to convert to penn treebank bracketd format 
def node_to_penn(node):
  children = node.getchildren()
  if len(children) == 0:
    word = node.get('word',None)
    if word is not None:
      if node.get('rel') == 'hd': 
        head = '=H'
      else: 
        head = ''
      return '('+node.get('pos')+head+' '+word+')'
    else:
      return ''
  else:
    str = '('+node.get('cat')+' '
    for n in children:
      str+=node_to_penn(n)
    str+=')'
    return str

    
def xml_to_penn(filename):
  tree = etree.parse(filename)
  str = node_to_penn(tree.find('node'))
  return str



def create_constituency_layer(tree_str,term_ids):
    global NOTER, TER, EDGE, noter_cnt,ter_cnt,edge_cnt

    this_tree = Tree(tree_str)
    
    for num, token in enumerate(this_tree.leaves()):
        position = this_tree.leaf_treeposition(num)
        token_id = term_ids[num]
        this_tree[position] = token_id
    

    linking_id, nodes = generate_nodes(this_tree)
    
    ## TO include a root node
    my_noter_id = 'nter'+str(noter_cnt)
    my_noter  = (NOTER,my_noter_id,'ROOT')
    noter_cnt+=1
    nodes.insert(0,my_noter)
    
    my_edge = (EDGE,'tre'+str(edge_cnt),my_noter_id,linking_id)
    edge_cnt+=1
    nodes.insert(0,my_edge)
    
    
   
    ## non terminals
    nonter_nodes = []
    edges_nodes=  []
    ter_nodes = []
    nonter_heads = set()
    for n in nodes:
        if n[0] == NOTER:            
            _,nonter_id,label = n
            ##Checking the head
            if len(label)>=2 and label[-1]=='H' and label[-2]=='=':
                nonter_heads.add(nonter_id)
                label = label[:-2]
            ele = etree.Element('nt', attrib={'id':nonter_id,'label':label})
            nonter_nodes.append(ele)
        elif n[0] == EDGE:
            _,edge_id,node_to,node_from = n
            ele = etree.Element('edge',attrib={'id':edge_id,'from':node_from,'to':node_to})
            edges_nodes.append(ele)
        elif n[0] == TER:
            _,ter_id,span_ids = n
            ele = etree.Element('t',attrib={'id':ter_id})
            span = etree.Element('span')
            ele.append(span)
            for termid in span_ids.split(' '):
                target = etree.Element('target',attrib={'id':termid})
                span.append(target)
            ter_nodes.append(ele)
            
    root = etree.Element('tree')
    for nt in nonter_nodes:
        root.append(nt)
    
    for t in ter_nodes:
        root.append(t)
        
    for ed in edges_nodes:
        if ed.get('from') in nonter_heads:
            ed.set('head','yes')
        root.append(ed)        
    return root
        
##This is the recursive function to generate all the nodes behind a node
def generate_nodes(node):
    global NOTER, TER, EDGE, noter_cnt,ter_cnt,edge_cnt

    if isinstance(node, str):  ## is a leaf
        # This is just a text (a token id)
        my_ter_id = "ter"+str(ter_cnt)
        ter_cnt+=1
        my_ter = (TER,my_ter_id,str(node))
        return my_ter_id,[my_ter]
    else:
        nodes = []
        my_nonter_id = 'nter'+str(noter_cnt)
        noter_cnt+=1
        my_nonter = (NOTER,my_nonter_id,node.node)
        nodes.append(my_nonter)
        
        for child in node:
            linking_id, subnodes = generate_nodes(child)
            nodes.extend(subnodes)
            
            my_edge_id = 'tre'+str(edge_cnt)
            edge_cnt += 1
            my_edge = (EDGE,my_edge_id,my_nonter_id,linking_id)
            nodes.append(my_edge)
            
        return my_nonter_id,nodes
            
'''           
s = '(S (NP (DET The) (NN dog)) (VP (V ate) (NP (DET the) (NN cat))) (. .))'
ids = ['t0 t1','t2','t3','t4','t5','t6']
tree_node = create_constituency_layer(s, ids)
e = etree.ElementTree(element=tree_node)
e.write(sys.stdout,pretty_print=True)
sys.exit(0)
'''

if not sys.stdin.isatty(): 
    ## READING FROM A PIPE
    pass
else:
    print>>sys.stderr,'Input stream required in KAF format at least with the text layer.'
    print>>sys.stderr,'The language encoded in the KAF has to be Dutch, otherwise it will raise an error.'
    print>>sys.stderr,'Example usage: cat myUTF8file.kaf.xml |',sys.argv[0]
    sys.exit(-1)

my_time_stamp = True
try:
  opts, args = getopt.getopt(sys.argv[1:],"",["no-time"])
  for opt, arg in opts:
    if opt == "--no-time":
      my_time_stamp = False
except getopt.GetoptError:
  pass
  
  
logging.debug('Loading and parsing KAF file ...')
my_kaf = KafParser(sys.stdin)

lang = my_kaf.getLanguage()
if lang != 'nl':
  print>>sys.stdout,'ERROR! Language is ',lang,' and must be nl (Dutch)'
  sys.exit(-1)
  
logging.debug('Extracting sentences from the KAF')
sentences = []
current_sent = [] 
term_ids = []
current_sent_tid = []

termid_for_token = {}

for term in my_kaf.getTerms():
    tokens_id = term.get_list_span()
    for token_id in tokens_id:
        termid_for_token[token_id] = term.getId()
 

previous_sent = None
for token,sent,token_id in my_kaf.getTokens():
  if sent != previous_sent and previous_sent!=None:
    sentences.append(current_sent)
    current_sent = [token]
    term_ids.append(current_sent_tid)
    current_sent_tid = [termid_for_token[token_id]]
  else:
    current_sent.append(token)
    current_sent_tid.append(termid_for_token[token_id])
  previous_sent = sent
  
if len(current_sent) !=0:
  sentences.append(current_sent)
  term_ids.append(current_sent_tid)
  
out_folder_alp = tempfile.mkdtemp()


logging.debug('Calling to Alpino parser in '+ALPINO_HOME)
## CALL TO ALPINO
alpino_bin = os.path.join(ALPINO_HOME,'bin','Alpino')
cmd = alpino_bin+' -fast end_hook=xml -flag treebank '+out_folder_alp+' -parse'
os.environ['ALPINO_HOME']=ALPINO_HOME
alpino_pro = Popen(cmd,stdout=PIPE,stdin=PIPE,stderr=PIPE,shell=True)

for sentence in sentences:
  for token in sentence:
    alpino_pro.stdin.write(token.encode('utf-8')+' ')
  alpino_pro.stdin.write('\n')
alpino_pro.stdin.close()

print>>sys.stderr,alpino_pro.stderr.read()

# As we are not reading the stdout or stderr of the process, if we dont wait to it to be done
# the parent will keep running without alpino be completed, and we will get empty XML files
# If the parent reads from stdout or stderr, it waits to the child to be completed before keep running
alpino_pro.wait()


## There should be as many files as number of sentences in the KAF

num_xml = 0
const = etree.Element('constituents')
for xml_file in glob.glob(os.path.join(out_folder_alp,'*.xml')):
  logging.debug('Converting alpino XML to pennTreebank, file num '+str(num_xml+1))
  penn_str = xml_to_penn(xml_file)
  
  tree_node = create_constituency_layer(penn_str,term_ids[num_xml])
  const.append(tree_node)
  num_xml+=1

my_kaf.tree.getroot().append(const)
this_name = 'alpino kaf constituency parser'
this_version = '1.0_20dec2013'
this_layer = 'constituents'

my_kaf.addLinguisticProcessor(this_name, this_version, this_layer, my_time_stamp)
my_kaf.saveToFile(sys.stdout)
  

logging.debug('Number of sentences in the input KAF:                            '+str(len(sentences)))
logging.debug('Number of alpino XML generated (must be equal to num. sentences):'+str(num_xml))
logging.debug('PROCESS DONE')

##Remove temporary stuff
shutil.rmtree(out_folder_alp)
sys.exit(0)