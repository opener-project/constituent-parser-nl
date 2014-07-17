#!/usr/bin/env python

import sys
import getopt
import os

this_folder = os.path.dirname(os.path.realpath(__file__))

# This updates the load path to ensure that the local site-packages directory
# can be used to load packages (e.g. a locally installed copy of lxml).
sys.path.append(os.path.join(this_folder, 'site-packages/pre_install'))

import codecs
from VUKafParserPy import KafParser
from lxml import etree
import tempfile
from subprocess import Popen,PIPE
import shutil
import glob
import logging

from convert_penn_to_kaf import convert_penn_to_kaf_with_numtokens
## LAST CHANGES ##
# 20-dec-2013: modified to generate KAF output
# 15-jan-2014: order in alpino XML does not math the order of tokens
#       so the label "begin" in the xml is used to know which is the number of token of each <node>


last_modified='21Jan2014'
version="1.4"
this_name = 'alpino kaf constituency parser'
this_layer = 'constituents'

#### SET THIS VARIABLE TO YOUR LOCAL FOLDER OF ALPINO
os.environ['SP_CTYPE']='utf8'
os.environ['SP_CSETLEN']='212'
os.environ['ALPINO_HOME']='/usr/local/src/Alpino/'
ALPINO_HOME = os.environ['ALPINO_HOME']

logging.basicConfig(stream=sys.stderr,format='%(asctime)s - %(levelname)s - %(message)s',level=logging.DEBUG)

__module_dir = os.path.dirname(__file__)

## Function to convert to penn treebank bracketd format 
def node_to_penn(node):
  children = node.getchildren()
  if len(children) == 0:
    word = node.get('word',None)
    if word is not None:
      #The attribute begin gives you the number of the token
      word = word.replace('(','-LRB')
      word = word.replace(')','-RRB-')
      
      
      num_token = node.get('begin')

      word = num_token+'#'+word
      if node.get('rel') == 'hd': 
        head = '=H'
      else: 
        head = ''
      return '('+node.get('pos')+head+' '+word.encode('utf-8')+')'
    else:
      return ''
  else:
    str = '('+node.get('cat')+' '
    for n in children:
      str+=node_to_penn(n)
    str+=')'
    return str

    
def xml_to_penn(filename):
    
  ## Under certain condition, there is know bug of Alpino, it sets the encoding in the XML
  ## to iso-8859-1, but the real encoding is UTF-8. So we need to force to use this encoding
  
  parser = etree.XMLParser(encoding='UTF-8')
  #parser = etree.XMLParser(encoding='ISO-8859-1')
  tree = etree.parse(filename,parser)
  
  str = node_to_penn(tree.find('node'))
  return str

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

    
lemma_for_termid = {}
termid_for_token = {}

for term in my_kaf.getTerms():
    lemma_for_termid[term.getId()] = term.getLemma()
    tokens_id = term.get_list_span()
    for token_id in tokens_id:
        termid_for_token[token_id] = term.getId()
 

previous_sent = None
for token,sent,token_id in my_kaf.getTokens():
  ##To avoid using tokens that have no term linked
  if token_id not in termid_for_token:
    continue
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
logging.debug('Temporary folder: '+out_folder_alp)


## CALL TO ALPINO
alpino_bin = os.path.join(ALPINO_HOME,'bin','Alpino')
cmd = alpino_bin+' end_hook=xml -flag treebank '+out_folder_alp+' -parse'
alpino_pro = Popen(cmd,stdout=PIPE,stdin=PIPE,stderr=PIPE,shell=True)

for sentence in sentences:
  for token in sentence:
    token = token.replace('[','\[')
    token = token.replace(']','\]')
    token = token.replace('|','\|')
    alpino_pro.stdin.write(token.encode('utf-8')+' ')
  alpino_pro.stdin.write('\n')
  #print>>sys.stderr
alpino_pro.stdin.close()

error_log = alpino_pro.stderr.read()
#print>>sys.stderr,alpino_pro.stderr.read()

# As we are not reading the stdout or stderr of the process, if we dont wait to it to be done
# the parent will keep running without alpino be completed, and we will get empty XML files
# If the parent reads from stdout or stderr, it waits to the child to be completed before keep running
alpino_pro.wait()


## There should be as many files as number of sentences in the KAF

const = etree.Element('constituency')

#for xml_file in glob.glob(os.path.join(out_folder_alp,'*.xml')):
cnt_t = cnt_nt = cnt_edge = 0
some_error = False
for num_sent in range(len(sentences)):
  xml_file = os.path.join(out_folder_alp,str(num_sent+1)+'.xml')    
  if os.path.exists(xml_file):
    logging.debug('Converting alpino XML to pennTreebank, sentence num '+str(num_sent+1))
    penn_str = xml_to_penn(xml_file)
    tree_node,cnt_t,cnt_nt,cnt_edge = convert_penn_to_kaf_with_numtokens(penn_str,term_ids[num_sent],logging,lemma_for_termid,cnt_t,cnt_nt,cnt_edge)
  else:
    tree_node = etree.Element('tree') #empty
    some_error = True
  const.append(tree_node)

if some_error:
  print>>sys.stderr,'POSSIBLE ERROR',error_log
  value = -1
else:
  value = 0

my_kaf.tree.getroot().append(const)
my_kaf.addLinguisticProcessor(this_name, version+'_'+last_modified, this_layer, my_time_stamp)
my_kaf.saveToFile(sys.stdout)
  

logging.debug('Number of sentences in the input KAF:  '+str(len(sentences)))
logging.debug('PROCESS DONE')

##Remove temporary stuff
shutil.rmtree(out_folder_alp)
#print out_folder_alp
sys.exit(value)