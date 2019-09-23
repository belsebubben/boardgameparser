import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from bglib.scrapers import *

class AlphaSpel(GenericScraper):
    def __init__(self):

        self.startpagenr = 1
        self.url = 'https://alphaspel.se/491-bradspel/?ordering=desc&order_by=new&page=%d'
        self.firstpageurl = 'https://alphaspel.se/491-bradspel/?ordering=desc&order_by=new'
        self.gamesoup = {'name': {'funcs': (lambda x: x.find("div", {"class": "product-name"}),\
                lambda x: x.text.replace('\n', '', -1).strip(),\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)) )},\
            'price': {'funcs':(lambda x: x.find('div', {"class": "price text-success"}),\
            lambda x: x.text, lambda x: x.replace('\n', '', -1).strip())},\
            'stock':{'funcs': (lambda x: x.find("div", {"class": "stock"}),\
            lambda x: 'slut' not in x.text.strip().lower())}}

        self.gamelistsoup = {'funcs':(lambda x: x.find('div', {'id': 'main"'}),\
                lambda x: x.find_all('div', {'class': 'product'}))}

        self.pagemaxnr = {'funcs':(lambda x: x.find('ul', {'class': 'pagination pagination-sm pull-right'}).find_all('a'),\
                lambda x: max([int(pgnr.text) for pgnr in x if pgnr.text.isdigit()]))}

        self.parsetype = 'soup'
        super().__init__()

    @classmethod
    def url (cls, url):
        return url + '&page=%s'

