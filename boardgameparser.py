#!/home/carl/.bgparser/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#pip install python-Levenshtein
#fuzzywuzzy

# Selenium firefox geckodriver
# https://github.com/mozilla/geckodriver/releases

#wget "https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && tar -C /opt -xzf /tmp/geckodriver.tar.gz && chmod 755 /opt/geckodriver && ln -fs /opt/geckodriver /usr/bin/geckodriver && ln -fs /opt/geckodriver /usr/local/bin/geckodriver


import sys
import os
#sys.path.append("/home/carl/.local_python3/lib/python3.4/site-packages/")
import collections
import re
from bs4 import BeautifulSoup
from urllib import parse
import urllib.request
import time
from operator import methodcaller
# from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

# xml
import xml.dom.minidom
from xml.dom.minidom import Node
import tempfile

# django
#django settings
import django
sys.path.append("/home/carl/Code/boardgameparser")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bgindex.settings')
from django.core.wsgi import get_wsgi_application
django.setup()
#end django settings
from bgs.models import *

# Selenium
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# local imports
from bglib.lib import *
from  bglib.httpbplate import *
import stores

# debugging
debug = False

# logging
import logging
import traceback
LOGFORMAT = "%(asctime)s %(levelname)s: line:%(lineno)d  func:%(funcName)s;  %(message)s"
bgparselogger = logging.StreamHandler(stream=sys.stderr)
logger = logging.getLogger('root')
logger.addHandler(bgparselogger)
if debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
logformatter = logging.Formatter(LOGFORMAT)
bgparselogger.setFormatter(logformatter)


filterlistfile = 'filterlist'
WISHDICT = {'1': 'Must have', '2': 'Love to have', '3': 'Like to have', '4': 'Thinking about it'}
WISHURL = 'https://www.boardgamegeek.com/xmlapi/collection/carl77?wishlist=1&%20wishlistpriority='

WEBHALLENURL = 'https://www.webhallen.com/se/category/3777-Bradspel?f=stock%5E0&page=1&sort=latest'

# Database stuff
# game, wishlist, shop

# end Database stuff

# Webhallen
def parseWebhallenGames(soup):
    gamelist = []
    games = soup.find_all("div", {"class": "col-md-4 col-sm-6 col-xs-6"})
    for game in games:
        name = game.find("span", {"class": "fixed-lines"}).next_element.strip()
        price = game.find("div", {"class": "relative d-block price"})
        campaign = price.find("span", {"class": "price-value _regular"})
        if campaign:
            logger.debug("webhallen campaign:!!!")
            logger.debug("Campaignprice!! : ", price.text.split("\n")[3].strip())
            price = price.text.split("\n")[3].strip()
            campaign = None
        else:
            price = price.find("span", {"class": "price-value _right"}).text.strip()
        price = price.replace(u"\xa0", u"").replace("kr", "")

        game = GameItem(name=name, stock=True, price=price)
        gamelist.append(game)
        logger.debug("webhallen game %s" % str(game))
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
    SCROLL_PAUSE_TIME = 0.2

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
        logger.debug("scroll: ", scrolled)

        html = driver.page_source
        html = html.encode("UTF-8")
        soup = getUrlSoupData(html, "UTF-8")
        gamelist.extend(parseWebhallenGames(soup))
        if debug:
            print(html)


    driver.close()
    return gamelist


def soupExtractor(soup,extractions):
    pass


def matchGamesWithWishes():

    # todo show unmatched wishes
    # todo show lowest price

    #allgames = GameProduct.objects.filter(stock=True)
    allgames = GameProduct.objects.filter()

    with open(filterlistfile) as flfile:
        filterwords = [ l.strip() for l in flfile.readlines()]

    for wish in Wishlist.objects.all():
        wishname = wish.name.lower()
        wishmatch = False
        for game in allgames:
            gamename = game.name.lower()
            
            # handle colons ':' (usually implies expansion or other item)
            if (':' in gamename and not ':' in wishname) or (':' in wishname and not ':' in gamename):
                continue

            # handle expansions explicitly
            if ('exp' in gamename.lower() and not 'exp' in wishname.lower()) or\
                    ('exp' in wishname.lower() and not 'exp' in gamename):
                continue

            # handle filterwords - if we explicitly have these in our wish then dont filter them out
            for word in filterwords:
                gamename = gamename.replace(word, '')
                #print('replaced %s !!!!!!!!!!!!!!!!!!!' % word, gamename)
                    
            #matchRatio = fuzz.WRatio(game.name, wish.name)
            #matchRatio = fuzz.partial_ratio(game.name, wish.name)
            #matchRatio = fuzz.token_sort_ratio(game.name, wish.name)
            matchRatio = fuzz.ratio(gamename, wishname)

            logger.debug('Matching: %s with %s' % (wish.name, game.name))
            # todo . examine different ratios depending on nr of words in product
            if (matchRatio > 72 and len(game.name.split(" ")) > 1) or (matchRatio > 81 and len(game.name.split(" ")) == 1) :
                if not wishmatch:
                    print('\nGame: %s' % (wish.name))
                    wishmatch = True
                print('\t%s:\n\tStore: %s\n\tStock: %s\n\tPrice: %s' % (game.name, game.shop.name, game.stock, game.price))
                print('Match ratio: %s; %s ---> %s' % (matchRatio, wishname, gamename))


def genWishlist():
    # todo make it wait for the request to generate 
    wishes = []
    for want,wantname in WISHDICT.items():
        wishurl = WISHURL + want

        xmlresp, charset = createHttpRequest(wishurl)
        xmlresp = xmlresp.decode(charset or "UTF-8")
        tempfilename = tempfile.mktemp()
        with open(tempfilename, "w") as fhw:
            fhw.write(xmlresp)
            fhw.close()
        doc = xml.dom.minidom.parse(tempfilename)
            
        for node in doc.getElementsByTagName("item"):
            name = node.getElementsByTagName("name")
            imageurl = node.getElementsByTagName("image")[0].firstChild.data
            priority = node.getElementsByTagName("status")[0].attributes["wishlistpriority"].value
            wishname = name[0].firstChild.data
            wishes.append(wishname)
            w, created = Wishlist.objects.update_or_create(name=wishname, priority=priority, imageurl=imageurl)
            try:
                w.save()
            except django.db.utils.IntegrityError:
                logger.warning('Failed to save entry: name:%s : prio:%s' % (wishname, priority))
    logger.debug("Wishlist: %s" % wishes)

    return wishes


def save_gameProducts(stores):
    #for store,gamelist in stores.items():
    for store in stores.__all__:
        shop, created = Shop.objects.update_or_create(defaults={"name": store, "scrapetime": int(time.time())}, name=store)

        try:
            storeobj = getattr(stores, store)()
        except:
            print("Store %s failed to initialize" % store)
            raise
        if not created:
            shop.save()
        # else: Shop.save(update_fields=['updated'])
        for game in storeobj.games:
            logger.debug("saving game: ", game)
            print("!!!!!!! saving game: ", game)
            game_name = game.name.replace("\n", "", -1)
            game_name = game_name.strip()
            game_name = " ".join(game_name.split())
            g, created = GameProduct.objects.update_or_create(name=game_name, shop=shop, defaults={"stock": game.stock, "price": game.price})
            g.save()

def getStoreData():
    # Stores todo ( spelexperten, midgård games, storochliten, http://www.unispel.com,  www.spelochsant.se )
    #stores = {}
    #stores["Alphaspel"] = alphaGamelist()
    #stores["DragonsLair"] = dragonslairGamelist()
    #stores["Worldofboardgames"] = wordlofboardgamesGamelist()
    #stores["AlltPaEttkortGames"] = alltpaettkortGamelist()
    #stores["RetroSpelbutiken"] = retrospelbutikenGamelist()
    #stores["Playoteket"] = playoteketGamelist()
    #stores["Webhallen"] = webhallenGamelist()
    return stores.__all__

def main():
    #stores = getStoreData()
    #A = AlphaSpel()
    #D = DragonsLair()
    #W = WorldOfBoardGames()
    #A = AlltPaEttkort()
    #R = RetroSpelButiken()
    #P = Playoteket()
    #four = FourGames()
    #F = FirstPlayer()
    #G = GamesMania()

    save_gameProducts(stores)
    #wishlist = genWishlist() # make a collector function

    matchGamesWithWishes()

if __name__ == "__main__":
    #application = get_wsgi_application()
    main()

