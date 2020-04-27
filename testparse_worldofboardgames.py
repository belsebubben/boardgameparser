#!/usr/bin/python3

from bs4 import BeautifulSoup
import sys
from bglib import httpbplate

URL = 'https://www.worldofboardgames.com/strategispel/nya_produkter%s#kategori'

html, charset = httpbplate.createHttpRequest(URL)

soup = httpbplate.getUrlSoupData(html, charset)

soup.find('nav', {'class': 'woocommerce-pagination'})

pagemaxnr = {'funcs':(lambda x: int(x.find('div', {'style': 'float: left; width: 34%; text-align: center;'}).text.strip().split()[-1]),)}

def findprice(x):
    try:
        price = game.find("div", {"class": "xlarge"}).next_element.next_element
    except:
        price = None
    return price

class WorldOfBoardGames(GenericScraper):
    def __init__(self):

        self.startpagenr = 1
        self.firstpageurl = 'https://www.worldofboardgames.com/strategispel/nya_produkter#kategori'
        self.gamesoup = {'name': {'funcs': (lambda x: x.findChild("a")["title"],\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (findprice,)},\
                'stock':{'funcs': (lambda x: x.find("a", {"class": "button green buttonshadow saveScrollPostion"}) is not None ,)}}

        self.gamelistsoup = {'funcs':(lambda x: x.find_all("div", {"class": "product"}),)}
        self.pagemaxnr = {'funcs':(lambda x: int(x.find('div', {'style': 'float: left; width: 34%; text-align: center;'}).text.strip().split()[-1]),)}

        self.parsetype = 'soup'
        super().__init__()
~
