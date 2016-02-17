__author__ = 'linanqiu'

from bs4 import BeautifulSoup
from icd9 import ICD9
import grequests
import re
import csv
import itertools

import logging, os, sys

logger = logging.getLogger('root')

program = os.path.basename(sys.argv[0])
logger = logging.getLogger(program)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
logging.root.setLevel(level=logging.INFO)
logger.info("running %s" % ' '.join(sys.argv))

URL = 'http://pwas.tmu.edu.tw/index.php/associations'

tree = ICD9('codes.json')


def traverse_tree(root):
  stack = []
  stack.append(root)
  while (len(stack) is not 0):
    node = stack.pop()
    yield node
    stack.extend(node.children)


maps = ['females0-9', 'females10-19', 'females20-29', 'females30-39', 'females40-49', 'females50-59', 'females60-69', 'females70-79', 'females80-89', 'females90+',
        'males0-9', 'males10-19', 'males20-29', 'males30-39', 'males40-49', 'males50-59', 'males60-69', 'males70-79', 'males80-89', 'males90+']
# removes E, V and dashed codes
icd9s = [node.code for node in traverse_tree(tree) if not re.search('[a-zA-Z\-]', node.code)]

header = ['disease_2', 'disease_name', 'category', 'count', 'co_occurrence', 'odds_ratio', 'p_value', '95_ci_lower', '95_ci_upper']


def scrape_page(response, *args, **kwargs):
  logger.info('Scraping %s %s' % (map_select, icd9_select))
  print response.url
  soup = BeautifulSoup(response.text, 'html.parser')
  rows = soup.findAll('tr', id=re.compile('^row-'))

  entries = []

  for row in rows:
    values = row.findChildren('td')
    values = [value.text for value in values]
    entry = dict(zip(header, values))
    entries.append(entry)

  with open('./scraped_data/%s_%s.csv' % (map_select, icd9_select), 'wb') as output_file:
    dict_writer = csv.DictWriter(output_file, header)
    dict_writer.writeheader()
    dict_writer.writerows(entries)
    logger.info('Written ./scraped_data/%s_%s.csv' % (map_select, icd9_select))


map_icd9_tuples = itertools.product(maps, icd9s)

rs = (grequests.post(URL, hooks={'response': scrape_page}, data={'map_Select': map_select, 'icd9_Select': icd9_select}) for map_select, icd9_select in map_icd9_tuples)
grequests.map(rs, size=2)
