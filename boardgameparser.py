#!/home/carl/.bgparser/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#pip install python-Levenshtein
#fuzzywuzzy

# Selenium firefox geckodriver
# https://github.com/mozilla/geckodriver/releases

#wget "https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && tar -C /opt -xzf /tmp/geckodriver.tar.gz && chmod 755 /opt/geckodriver && ln -fs /opt/geckodriver /usr/bin/geckodriver && ln -fs /opt/geckodriver /usr/local/bin/geckodriver


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


filterlistfile = "filterlist"
WISHDICT = {'1': 'Must have', '2': 'Love to have', '3': 'Like to have', '4': 'Thinking about it'}
WISHURL = "https://www.boardgamegeek.com/xmlapi/collection/carl77?wishlist=1&%20wishlistpriority="

ALPHAURL = "https://alphaspel.se/491-bradspel/?ordering=desc&order_by=new&page=%s"
DRAGONSLAIRURL = "https://www.dragonslair.se/product/boardgame/sort:recent/price:1:10000"
WORLDOFBOARDGAMESURL = "https://www.worldofboardgames.com/strategispel/nya_produkter%s#kategori"
ALLTPAETTKORTURL = "https://www.alltpaettkort.se/butik/%s?orderby=date"
WEBHALLENURL = "https://www.webhallen.com/se/category/3777-Bradspel?f=stock%5E0&page=1&sort=latest"
RETROSPELBUTIKEN = "http://retrospelbutiken.se/store/category.php?category=190"
PLAYOTEKETURL = "https://www.playoteket.com/strategi?orderby=quantity&orderway=desc"

GameItem = collections.namedtuple('GameItem', 'name, stock, price') # TODO add url

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
        soup = httpbplate.getUrlSoupData(html, "UTF-8")
        gamelist.extend(parseWebhallenGames(soup))
        if debug:
            print(html)


    driver.close()
    return gamelist


def getpagesoup(url):
    try:
        html, charset = httpbplate.createHttpRequest(url)
        pagesoup = httpbplate.getUrlSoupData(html, charset)
    except:
        logger.warn('Failed to get first page from %s' % url)
        raise
    return pagesoup

# Alphaspel
def parseAlphaGames(soup):
    gamelist = []
    contenttable = soup.find("div", {"id": "main"})
    games = contenttable.find_all("div", {"class": "product"})
    for game in games:
        name = game.find("div", {"class": "product-name"}).text.strip()
        price = game.find("div", {"class": "price text-success"}).text.replace("\n", "", -1).strip()
        stock = not any(word in game.find("div", {"class": "stock"}).text.strip().lower() for word in ("slut", "kommande"))
        game = GameItem(name=name, stock=stock, price=price)
        gamelist.append(game)
    return gamelist

class AlphaspelScraper():
    def __init__(self):
        self.url = ALPHAURL
        self.failed = False
        self.nrerrors = 0
        self.nrparsed = 0
        self.firstpageurl = self.url % 1
        try:
            self.firstpage = getpagesoup(url)
        except:
            self.failed = True
        self.setpgmaxnr()
        self.startpagenr = 1
        self.gamelist = []

        # todo map,filter where functions for extractions of elements are fed to a generic class

    def getGameElements(self,soup):
        '''Get a list of soup elements (one for each game)'''
        try:
            contenttable = soup.find("div", {"id": "main"})
            games = contenttable.find_all("div", {"class": "product"})
        except:
            logger.warn('Failed to get game element list for %s' % self.url)
        return games

    def parsePage(self,soup):
        for game in getGameElements(soup):
            try:
                name = game.find("div", {"class": "product-name"}).text.strip()
                price = game.find("div", {"class": "price text-success"}).text.replace("\n", "", -1).strip()
                stock = not any(word in game.find("div", {"class": "stock"}).text.strip().lower() for word in ("slut", "kommande"))
                game = GameItem(name=name, stock=stock, price=price)
                self.gamelist.append(game)
                self.nrparsed +=1
            except:
                logger.warn("Error in parsing game element %s" % (game))
                self.nrerrors +=1


    def setpgmax(self):
        pages = self.firstpage.find('ul', {'class': 'pagination pagination-sm pull-right'}).find_all('a')
        #pgnrs = pages.find_all("a")
        self.pgmax = max([ int(pgnr.text) for pgnr in pgnrs if pgnr.text.isdigit()])

    def getPages(self):
        for pagenr in range(self.startpagenr,self.pgmaxnr):
            self.parsePage(self.url % pagenr)


def alphaGamelist():
    gamelist = []
    # nr of pages
    html, charset = httpbplate.createHttpRequest(ALPHAURL % 1)
    pagesoup = httpbplate.getUrlSoupData(html, charset)
    pages = pagesoup.find("ul", {"class": "pagination pagination-sm pull-right"})
    pgnrs = pages.find_all("a")
    pgmax = max([ int(pgnr.text) for pgnr in pgnrs if pgnr.text.isdigit()])
    for i in range(1,pgmax): # TODO iterate over paginated pages of new games change to pgmax
        html, charset = httpbplate.createHttpRequest(ALPHAURL % i)
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseAlphaGames(soup))

    if debug:
        logger.debug("Alphaspel gamelist:")
        for g in gamelist:
            logger.debug(g)

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
        price = game.find("span", {"class": "price"}).text.strip() or None 
        game = GameItem(name=name, stock=stock, price=price)
        gamelist.append(game)
    return gamelist

def dragonslairGamelist():
    gamelist = []
    html, charset = httpbplate.createHttpRequest(DRAGONSLAIRURL) 
    soup = httpbplate.getUrlSoupData(html, charset)
    gamelist.extend(parseDragonslairGames(soup))

    ##pagination
    pages = soup.find("ul", {"class": "pagination"})
    pgmax = int(pages.find_all('a')[-2].text)

    for i in range(2,pgmax): # iterate over paginated pages of new games
        html, charset = httpbplate.createHttpRequest(DRAGONSLAIRURL + "/%d" % i )
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseDragonslairGames(soup))

    if debug:
        logger.debug("Dragons lair gamelist:")
        for g in gamelist:
            logger.debug(g)

    return gamelist
# End Dragons lair

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
    html, charset = httpbplate.createHttpRequest(WORLDOFBOARDGAMESURL % '')
    soup = httpbplate.getUrlSoupData(html, charset)
    gamelist.extend(parseWordlofboardgamesGames(soup))
    pgmax = int(soup.find('div', {'style': 'float: left; width: 34%; text-align: center;'}).text.strip().split()[-1])
    for count in range(0,pgmax,40):
        html, charset = httpbplate.createHttpRequest(WORLDOFBOARDGAMESURL % ('/' + str(count)))
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseWordlofboardgamesGames(soup))

    logger.debug("WorldOfBoardGames gamelist:")
    if debug:
        for g in gamelist:
            logger.debug(g)

    return gamelist
# End Wordlofboardgames

# Alltpaettkort
def parseAlltpaettkortGames(soup):
    gamelist = []
    #contenttable = soup.find("ul", {"class": "products"})
    #print(contenttable)
    games = soup.find_all("li", {"class": lambda L: L and L.find('post') > -1 })
    logger.debug("Allt På Ett Kort gamelist:")
    for game in games:
        if debug:
            print(game.prettify())
        try:
            name = game.find("h2").text
            price = game.find("span", {"class": "price"}).text.replace("kr", "" ).replace(",", "").strip()
            stock = game.find("a", {"class": "button add_to_cart_button product_type_simple"}) is not None
            game = GameItem(name=name, stock=stock, price=price)
            gamelist.append(game)
            logger.debug(game)
        except:
            logger.debug(sys.exc_info())
    return gamelist

def alltpaettkortGamelist():
    gamelist = []
    html, charset = httpbplate.createHttpRequest(ALLTPAETTKORTURL % '')
    soup = httpbplate.getUrlSoupData(html, charset)
    pgmax = int(soup.find('nav', {'class': 'woocommerce-pagination'}).find_all('a')[-2].text)
    gamelist.extend(parseAlltpaettkortGames(soup))
    for count in range(2, pgmax):
        html, charset = httpbplate.createHttpRequest(ALLTPAETTKORTURL % ('page/' + str(count) + '/') )
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseAlltpaettkortGames(soup))
    return gamelist
# End Allt på ett kort

# Retrospelbutiken
def parseRetrospelButiken(soup):
    gamelist = []
    # find all <td> tags that contain string "brädspel"
    try:
        bgtds = [ td for td in soup.find_all("td") if td and hasattr(td, "text") and "brädspel" in td.text.lower() ]
    except:
        logger.error("Fail getting games for retrospelbutiken '%s': entry:'%s'" % (str(sys.exc_info()), str(bgtds.prettify())))
    logger.debug("Retrospelsbutiken game parsing")
    logger.debug(bgtds)
    for bgtd in bgtds:
        try:
            trparent = bgtd.find_parent("tr")
            prevtr = trparent.find_previous("tr")
            prevtr2 = prevtr.find_previous("tr")
            psibs = bgtd.find_previous_siblings("td")
            #nsibs =  bgtds[10].find_next_siblings("td")
            name = prevtr2.find_all("td")[len(psibs)].text
            price = bgtd.find("b").text
            stock = "i lager" in  bgtd.text.lower()
            game = GameItem(name=name, stock=stock, price=price)
            #logger.debug("retrospelbutiken game %s" % game)
            gamelist.append(game)
        except Exception as exc:
            #logger.error("Fail parse for retrospelbutiken '%s': entry:'%s'" % (str(sys.exc_info()), str(bgtd.prettify())))
            logger.debug("Fail parse for retrospelbutiken '%s'\n" % str(exc))
    return gamelist

def retrospelbutikenGamelist():
    logger.debug("getting games for retrospelbutiken")
    gamelist = []
    html, charset = httpbplate.createHttpRequest(RETROSPELBUTIKEN)
    soup = httpbplate.getUrlSoupData(html, charset)
    
    #pgmax
    sides = soup.find(string="Nästa Sida >")
    pgmax = int(sides.previous_element.find_previous('a').text.strip())

    gamelist.extend(parseAlltpaettkortGames(soup))
    for count in range(2, pgmax):
        html, charset = httpbplate.createHttpRequest(RETROSPELBUTIKEN + '&' + 'page=' + str(count) + '&sort=0')
        logger.debug("Getting page %s, with charset %s" % (count, charset))
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseRetrospelButiken(soup))
    return gamelist
# End Retrospelbutiken

# Playoteket
def parsePlayoteket(soup):
    gamelist = []
    games = soup.find_all("div", {"class": "product-container"})
    logger.debug("Playoteket game parsing")
    for game in games:
        try:
            name = game.find("h3", {"class": "thename"}).string
            price = game.find("span", {"class": "amount"}).string.strip()
            stock = True
            game = GameItem(name=name, stock=stock, price=price)
            gamelist.append(game)
        except:
            logger.error("Failed parsing for playoteket: %s", sys.exc_info())
        if debug:
            logger.debug(game.prettify)
    return gamelist

def playoteketGamelist():
    gamelist = []
    html, charset = httpbplate.createHttpRequest(PLAYOTEKETURL)
    soup = httpbplate.getUrlSoupData(html, charset)

    gamelist.extend(parsePlayoteket(soup))

    pages = soup.find("ul", {"class": "pagination"})
    pagecount = pages.find_all("span")[-1].string
    for count in range(2, int(pagecount)):
        html, charset = httpbplate.createHttpRequest(PLAYOTEKETURL + '&p=' + str(count))
        soup = httpbplate.getUrlSoupData(html, charset)
        gamelist.extend(parseAlltpaettkortGames(soup))
    return gamelist
# End Playoteket


def matchGamesWithWishes():

    allgames = GameProduct.objects.filter(stock=True)

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
            if (matchRatio > 75 and len(game.name.split(" ")) > 1) or (matchRatio > 81 and len(game.name.split(" ")) == 1) :
                if not wishmatch:
                    print('\nGame: %s' % (wish.name))
                    wishmatch = True
                print('\t%s:\n\tStore: %s\n\tStock: %s\n\tPrice: %s' % (game.name, game.shop.name, game.stock, game.price))
                print('Match ratio: %s; %s ---> %s' % (matchRatio, wishname, gamename))


def genWishlist():
    wishes = []
    for want,wantname in WISHDICT.items():
        wishurl = WISHURL + want

        xmlresp, charset = httpbplate.createHttpRequest(wishurl)
        xmlresp = xmlresp.decode(charset or "UTF-8")
        tempfilename = tempfile.mktemp()
        with open(tempfilename, "w") as fhw:
            fhw.write(xmlresp)
            fhw.close()
        doc = xml.dom.minidom.parse(tempfilename)
            
        for node in doc.getElementsByTagName("item"):
            name = node.getElementsByTagName("name")
            priority = node.getElementsByTagName("status")[0].attributes["wishlistpriority"].value
            wishname = name[0].firstChild.data
            wishes.append(wishname)
            wishes.append(wishname)
            w, created = Wishlist.objects.update_or_create(name=wishname, priority=priority)
            try:
                w.save()
            except django.db.utils.IntegrityError:
                logger.warn('Failed to save entry: name:%s : prio:%s' % (wishname, priority))
    logger.debug("Wishlist: %s" % wishes)

    return wishes


def save_gameProducts(stores):
    for store,gamelist in stores.items():
        shop, created = Shop.objects.update_or_create(name=store, scrapetime=int(time.time()))
        if not created:
            shop.save()
        # else: Shop.save(update_fields=['updated'])
        for game in gamelist:
            logger.debug("saving game: ", game)
            print("!!!!!!! saving game: ", game)
            game_name = game.name.replace("\n", "", -1)
            game_name = game_name.strip()
            game_name = " ".join(game_name.split())
            g, created = GameProduct.objects.update_or_create(name=game_name, shop=shop, defaults={"stock": game.stock, "price": game.price})
            g.save()

def getStoreData():
    # Stores todo ( playoteket, 4-games.se, midgård games, storochliten, http://www.unispel.com, firstplayer.nu, http://www.gamesmania.se/, www.spelochsant.se )
    stores = {}
    #stores["Alphaspel"] = alphaGamelist()
    #stores["DragonsLair"] = dragonslairGamelist()
    #stores["Worldofboardgames"] = wordlofboardgamesGamelist()
    #stores["AlltPaEttkortGames"] = alltpaettkortGamelist()
    #stores["RetroSpelbutiken"] = retrospelbutikenGamelist()
    #stores["Playoteket"] = playoteketGamelist()
    #stores["Webhallen"] = webhallenGamelist()
    return stores

def main():
    stores = getStoreData()
    save_gameProducts(stores)
    #wishlist = genWishlist() # make a collector function

    matchGamesWithWishes()

if __name__ == "__main__":
    #application = get_wsgi_application()
    main()

