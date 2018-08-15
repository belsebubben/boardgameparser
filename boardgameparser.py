#!/home/carl/.pyvenv3/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#pip install python-Levenshtein
#fuzzywuzzy

import sys
import os
import collections
#sys.path.append("/home/carl/.local_python3/lib/python3.4/site-packages/")
from bs4 import BeautifulSoup
from urllib import parse
import urllib.request
import time
import httpbplate
# from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

import xml.dom.minidom
from xml.dom.minidom import Node
import tempfile

debug = False

filterlistfile = "filterlist"
WISHURLMUST = "https://www.boardgamegeek.com/xmlapi/collection/carl77?wishlist=1&%20wishlistpriority=1"
WISHURLLOVE = "https://www.boardgamegeek.com/xmlapi/collection/carl77?wishlist=1&%20wishlistpriority=2"
WISHURLS = [WISHURLMUST, WISHURLLOVE]

ALPHAURL = "https://alphaspel.se/491-bradspel/news/?page=%s"
DRAGONSLAIRURL = "https://www.dragonslair.se/product/boardgame/sort:recent/strategy"
EUROGAMESURL = "http://www.eurogames.se/butik/?swoof=1&filter_attribut=butik-sortiment&orderby=date"
WORLDOFBOARDGAMESURL = "https://www.worldofboardgames.com/strategispel/nya_produkter%s#kategori"
ALLTPAETTKORTURL = "https://www.alltpaettkort.se/butik/?orderby=date"
ALLTPAETTKORTURLPAGED =  "https://www.alltpaettkort.se/butik/page/%s/?orderby=date"


GameItem = collections.namedtuple('GameItem', 'name, stock, price')

# Alphaspel
def parseAlphaGames(soup):
    gamelist = []
    contenttable = soup.find("div", {"id": "main"})
    games = contenttable.find_all("div", {"class": "product"})
    for game in games:
        name = game.find("div", {"class": "product-name"}).text.strip()
        stock = not any(word in game.find("div", {"class": "stock"}).text.strip().lower() for word in ("slut", "kommande"))
        game = GameItem(name=name, stock=stock, price="")
        gamelist.append(game)
    return gamelist

def alphaGamelist():
    gamelist = []
    for i in range(1,5): # iterate over paginated pages of new games
        html, charset = httpbplate.createHttpRequest(ALPHAURL % i)
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseAlphaGames(soup))

    if debug:
        print("Alphaspel gamelist:")
        for g in gamelist:
            print(g)

    return gamelist
# End Alphaspel

# Dragons lair
def parseDragonslairGames(soup):
    gamelist = []
    contenttable = soup.find("div", {"id": "product-list"})
    games = contenttable.find_all("div", {"class": "container"})
    for game in games:
        name = game.find("a", {"class": "label"}).text.strip()
        stock = "I lager: Ja" in game.find("div", {"class": "controls"}).text.strip()
        price = game.find("span", {"class": "price"}).text.strip() or None # !!!!!!!!!!!!!!!!!!!!! price
        game = GameItem(name=name, stock=stock, price=price)
        gamelist.append(game)
    return gamelist

def dragonslairGamelist():
    gamelist = []
    html, charset = httpbplate.createHttpRequest(DRAGONSLAIRURL) 
    soup = httpbplate.getUrlSoupData(html, charset)
    gamelist.extend(parseDragonslairGames(soup))

    for i in range(2,5): # iterate over paginated pages of new games
        html, charset = httpbplate.createHttpRequest(DRAGONSLAIRURL + "/%d" % i )
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseDragonslairGames(soup))

    if debug:
        print("Dragons lair gamelist:")
        for g in gamelist:
            print(g)

    return gamelist
# End Dragons lair

# Eurogames
def parseEurogamesGames(soup):
    gamelist = []
    contenttable = soup.find("ul", {"class": "products columns-3"})
    #games = contenttable.find_all("h2", {"class": "woocommerce-loop-product__title"})
    games = contenttable.find_all("li", None)
    for game in games:
        name = game.find("h2", {"class": "woocommerce-loop-product__title"}).text.strip()
        stock = game.find("a", {"class": "button product_type_simple ajax_add_to_cart"}) == None
        price = game.find("span", {"class": "woocommerce-Price-amount amount"}).text.strip()
        game = GameItem(name=name, stock=stock, price=price)
        gamelist.append(game)
    return gamelist

def eurogamesGamelist():
    gamelist = []

    html, charset = httpbplate.createHttpRequest(EUROGAMESURL)
    soup = httpbplate.getUrlSoupData(html, charset)
    gamelist.extend(parseEurogamesGames(soup))

    if debug:
        print("Eurogames gamelist:")
        for g in gamelist:
            print(g)

    return gamelist
# End Eurogames

# Wordlofboardgames
def parseWordlofboardgamesGames(soup):
    gamelist = []
    games = soup.find_all("div", {"class": "product"})
    for game in games:
        name = game.findChild("a")["title"]
        try:
            price = game.find("div", {"class": "xlarge"}).next_element.next_element
        except:
            price = None
        stock = game.find("a", {"class": "button green buttonshadow saveScrollPostion"}) is not None
        game = GameItem(name=name, stock=stock, price=price)
        gamelist.append(game)
    return gamelist

def wordlofboardgamesGamelist():
    gamelist = []
    for count in ("", "/40", "/80"):
        html, charset = httpbplate.createHttpRequest(WORLDOFBOARDGAMESURL % count)
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseWordlofboardgamesGames(soup))

    if debug:
        print("WorldOfBoardGames gamelist:")
        for g in gamelist:
            print(g)

    return gamelist
# End Wordlofboardgames

# Alltpaettkort
def parseAlltpaettkortGames(soup):
    gamelist = []
    contenttable = soup.find("ul", {"class": "products"})
    #print(contenttable)
    games = contenttable.find_all("h3")
    for game in games:
        gamelist.append(game.text.strip())
    return gamelist

def alltpaettkortGamelist():
    gamelist = []
    html, charset = httpbplate.createHttpRequest(ALLTPAETTKORTURL)
    soup = httpbplate.getUrlSoupData(html, charset)
    gamelist.extend(parseAlltpaettkortGames(soup))
    for count in ("2", "3", "4"):
        html, charset = httpbplate.createHttpRequest(ALLTPAETTKORTURLPAGED % count)
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseAlltpaettkortGames(soup))

    if debug:
        print("Allt På Ett Kort gamelist:")
        for g in gamelist:
            print(g)

    return gamelist
# End Allt på ett kort

def matchGamesWithWishes(gamelist, wishlist, storename="Unknown Store"):
    with open(filterlistfile) as flfile:
        filterlist = flfile.readlines()
    
    for game in gamelist:
        skip = False
        for filterentry in filterlist:
            if fuzz.token_sort_ratio(game.name, filterentry) > 90:
                skip = True
        if skip:
            continue
        name = ''.join([c for c in game.name if c.isalnum() or c.isspace()])
        for wish in wishlist:
            if debug:
                print("Matching: ", wish, "with: ", game.name)
            wish = ''.join([c for c in wish if c.isalnum() or c.isspace()])
            #matchRatio = SequenceMatcher(lambda x: x == ' ', game.lower(), wish.lower()).ratio()
            #matchRatio = SequenceMatcher(None, game.lower(), wish.lower()).ratio()
            matchRatio = fuzz.token_sort_ratio(game.name, wish)
            if matchRatio > 65:
                print("Match!!!: ", "Game: ", game, "Wish: ", wish, "Storename: ", storename )
                print("Match ratio: ", matchRatio)
                print()

def genWishlist():
    wishes = []
    for wishurl in WISHURLS:

        xmlresp, charset = httpbplate.createHttpRequest(wishurl)
        xmlresp = xmlresp.decode(charset or "UTF-8")
        tempfilename = tempfile.mktemp()
        with open(tempfilename, "w") as fhw:
            fhw.write(xmlresp)
            fhw.close()
        doc = xml.dom.minidom.parse(tempfilename)
            
        for node in doc.getElementsByTagName("item"):
            name = node.getElementsByTagName("name")
            wishes.append(name[0].firstChild.data)
    if debug:
        print("Wishlist:", wishes)

    return wishes


def main():
    stores_dict = {}

    wishlist = genWishlist()

    stores_dict["Alphaspel"] = alphaGamelist()
    stores_dict["DragonsLair"] = dragonslairGamelist()
    stores_dict["EuroGames"] = eurogamesGamelist()
    stores_dict["Worldofboardgames"] = wordlofboardgamesGamelist()
    #stores_dict["AlltPaEttkortGames"] = alltpaettkortGamelist()

    for k,v in stores_dict.items():
        matchGamesWithWishes(v, wishlist, storename=k)

if __name__ == "__main__":
    main()

