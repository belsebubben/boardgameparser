#!/home/carl/.pyvenv3/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#pip install python-Levenshtein
#fuzzywuzzy

# Selenium firefox geckodriver
# https://github.com/mozilla/geckodriver/releases

#wget "https://github.com/mozilla/geckodriver/releases/download/v0.21.0/geckodriver-v0.21.0-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && tar -C /opt -xzf /tmp/geckodriver.tar.gz && chmod 755 /opt/geckodriver && ln -fs /opt/geckodriver /usr/bin/geckodriver && ln -fs /opt/geckodriver /usr/local/bin/geckodriver


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

# Selenium
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


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
WEBHALLENURL = "https://www.webhallen.com/se/category/3777-Bradspel?f=stock%5E0&page=1&sort=latest"


GameItem = collections.namedtuple('GameItem', 'name, stock, price')

# Webhallen

def parseWebhallenGames(soup):
    # div.product-list-page:nth-child(1)
    # div.col-sm-6:nth-child(1)
    # div class="panel mb-4 panel-thin-blue product-grid-item"
    # div.col-md-4:nth-child(3)
    gamelist = []
    #contenttable = soup.find("div", {"class": "product-list-page"})
    #print("contenttable", contenttable.__dict__)
    games = soup.find_all("div", {"class": "col-md-4 col-sm-6 col-xs-6"})
    for game in games:
        name = game.find("span", {"class": "fixed-lines"}).next_element.strip()
        price = game.find("div", {"class": "relative d-block price"})
        campaign = price.find("span", {"class": "_campaign price-value _right"})
        if campaign is not None:
            print("Price: ", price.__dict__)
            print("Campaign:", campaign.__dict__)
            print()
            print("_" * 70)
        campaign = None
        # html body div#app div div#site-container.d-sm-flex.flex-column.align-items-end.container.px-0 main.container.relative.pb-5.section-7 div.row div.main-col.col-sm-12.col-lg-8.col-md-9.pl-0-lg.pr-0-md div#main-container.main-container article.category.child-view div.product-browser div.mt-4 div.product-list-page div.col-md-4.col-sm-6.col-xs-6 div.panel.mb-4.panel-thin-blue.product-grid-item div.panel-body.p-4 div.panel-bottom.ap-br.mr-4.mb-0 div.relative.d-block.price span._campaign.price-value._right

        game = GameItem(name=name, stock=True, price="100")
        gamelist.append(game)
    return gamelist

def webhallenGamelist():
    gamelist = []
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox
    driver = webdriver.Firefox(firefox_options=options)
    driver.get(WEBHALLENURL)
    driver.implicitly_wait(3)

    # scroller
    SCROLL_PAUSE_TIME = 0.1

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolled = 0
    while scrolled < 14:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scrolled += 1
        if debug:
            print("scroll: ", scrolled)

        html = driver.page_source
        html = html.encode("UTF-8")
        soup = httpbplate.getUrlSoupData(html, "UTF-8")
        gamelist.extend(parseWebhallenGames(soup))

    for game in gamelist:
        print(game)

    driver.close()
    #print(html)


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

    stores_dict["Webhallen"] = webhallenGamelist()
#    stores_dict["Alphaspel"] = alphaGamelist()
#    stores_dict["DragonsLair"] = dragonslairGamelist()
#    stores_dict["EuroGames"] = eurogamesGamelist()
#    stores_dict["Worldofboardgames"] = wordlofboardgamesGamelist()
    #stores_dict["AlltPaEttkortGames"] = alltpaettkortGamelist()

#    for k,v in stores_dict.items():
#        matchGamesWithWishes(v, wishlist, storename=k)

if __name__ == "__main__":
    main()

