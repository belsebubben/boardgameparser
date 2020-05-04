#!/home/carl/.bgparser/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# pip install python-Levenshtein
# fuzzywuzzy

# Selenium firefox geckodriver
# https://github.com/mozilla/geckodriver/releases

# wget "https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && tar -C /opt -xzf /tmp/geckodriver.tar.gz && chmod 755 /opt/geckodriver && ln -fs /opt/geckodriver /usr/bin/geckodriver && ln -fs /opt/geckodriver /usr/local/bin/geckodriver

DESCRIPTION ="""Simple parser and matcher for boardgamegeek with items in swedish stores"""

import sys
import os
import argparse

# sys.path.append("/home/carl/.local_python3/lib/python3.4/site-packages/")
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
# django settings
import django

sys.path.append("/home/carl/Code/boardgameparser")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bgindex.settings")
from django.core.wsgi import get_wsgi_application

django.setup()
# end django settings
from bgs.models import *

# Selenium
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# local imports
from bglib.lib import *
from bglib.httpbplate import *
import stores

# debugging
debug = False

# logging
import logging
import traceback

LOGFORMAT = "%(asctime)s %(levelname)s: %(pathname)s line:%(lineno)d func:%(funcName)s; %(message)s exception:%(exc_info)s"
logger = logging.getLogger("root")
bgparselogger = logging.StreamHandler(stream=sys.stderr)
logformatter = logging.Formatter(LOGFORMAT)
bgparselogger.setFormatter(logformatter)
if debug:
    # bgparselogger.setLevel(logging.DEBUG)
    logging.root.setLevel(logging.DEBUG)
else:
    # bgparselogger.setLevel(logging.INFO)
    logging.root.setLevel(logging.INFO)
logger.addHandler(bgparselogger)
logger.debug("Debugging enabled!")


filterlistfile = "filterlist"
WISHDICT = {
    "1": "Must have",
    "2": "Love to have",
    "3": "Like to have",
    "4": "Thinking about it",
}
WISHURL = "https://www.boardgamegeek.com/xmlapi/collection/carl77?wishlist=1&%20wishlistpriority="

WEBHALLENURL = (
    "https://www.webhallen.com/se/category/3777-Bradspel?f=stock%5E0&page=1&sort=latest"
)

# Database stuff
# game, wishlist, shop

# end Database stuff

def parse_args():
    global debug
    parser = argparse.ArgumentParser(
        epilog=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        help="Enable debug",
        default=False,
    )
    parser.add_argument(
        "-w",
        "--wishlist",
        dest="wishlist",
        action="store_true",
        default=False,
        help="Fetch wishlist from boardgamegeek (wishlist account)",
    )
    parser.add_argument(
        "-c",
        "--compare",
        dest="compare",
        action="store_true",
        default=False,
        help="Compare wishlist and store items",
    )
    parser.add_argument(
        "-l", "--list", dest="liststores", action="store_true", help="List stores", default=False
    )
    parser.add_argument(
        "-p",
        "--parsestore",
        dest="parsestore",
        help="Parse store <storename>",
        default=False,
    )
    parser.add_argument(
        "-P",
        "--parseallstores",
        dest="parseallstore",
        action="store_true",
        help="Parse all stores",
        default=False,
    )

    args = parser.parse_args()
    if args.debug:
        debug = args.debug
        print("Debugging enabled")
    return args, parser


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
        logger.debug("html: '%s'" % str(html))

    driver.close()
    return gamelist


def soupExtractor(soup, extractions):
    pass


def matchGamesWithWishes():

    # todo show unmatched wishes
    # todo show lowest price

    # allgames = GameProduct.objects.filter(stock=True)
    allgames = GameProduct.objects.filter()

    with open(filterlistfile) as flfile:
        filterwords = [l.strip() for l in flfile.readlines()]

    for wish in Wishlist.objects.all():
        wishname = wish.name.lower()
        wishmatch = False
        for game in allgames:
            gamename = game.name.lower()

            # handle colons ':' (usually implies expansion or other item)
            if (":" in gamename and not ":" in wishname) or (
                ":" in wishname and not ":" in gamename
            ):
                continue

            # handle expansions explicitly
            if ("exp" in gamename.lower() and not "exp" in wishname.lower()) or (
                "exp" in wishname.lower() and not "exp" in gamename
            ):
                continue

            # handle filterwords - if we explicitly have these in our wish then dont filter them out
            for word in filterwords:
                gamename = gamename.replace(word, "")
                # print('replaced %s !!!!!!!!!!!!!!!!!!!' % word, gamename)

            # matchRatio = fuzz.WRatio(game.name, wish.name)
            # matchRatio = fuzz.partial_ratio(game.name, wish.name)
            # matchRatio = fuzz.token_sort_ratio(game.name, wish.name)
            matchRatio = fuzz.ratio(gamename, wishname)

            logger.debug("Matching: %s with %s" % (wish.name, game.name))
            # todo . examine different ratios depending on nr of words in product
            if (matchRatio > 72 and len(game.name.split(" ")) > 1) or (
                matchRatio > 81 and len(game.name.split(" ")) == 1
            ):
                if not wishmatch:
                    print("\nGame: %s" % (wish.name))
                    wishmatch = True
                print(
                    "\t%s:\n\tStore: %s\n\tStock: %s\n\tPrice: %s"
                    % (game.name, game.shop.name, game.stock, game.price)
                )
                print("Match ratio: %s; %s ---> %s" % (matchRatio, wishname, gamename))


def genWishlist():
    # todo make it wait for the request to generate
    wishes = []
    for want, wantname in WISHDICT.items():
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
            priority = (
                node.getElementsByTagName("status")[0]
                .attributes["wishlistpriority"]
                .value
            )
            wishname = name[0].firstChild.data
            wishes.append(wishname)
            w, created = Wishlist.objects.update_or_create(
                defaults={"name": wishname, "priority": priority, "imageurl": imageurl},
                name=wishname,
            )
            try:
                w.save()
            except django.db.utils.IntegrityError:
                logger.warning(
                    "Failed to save entry: name:%s : prio:%s" % (wishname, priority)
                )
    logger.debug("Wishlist: %s" % wishes)

    return wishes


def save_gameProducts(storename=False):
    global stores
    allstores = stores.__all__
    if storename: # only parse this _one_
        allstores = [stores.__all__[stores.__all__.index(storename)]]

    for storename in allstores:
        logger.info("Starting parsing of '%s'" % storename)
        shop, created = Shop.objects.update_or_create(
            defaults={"name": storename, "scrapetime": int(time.time())}, name=storename
        )
        logger.info("Object '%s'" % str(shop.__dict__))

        try:
            storeobj = getattr(stores, storename)()
        except:
            logger.warning("Store %s failed to initialize" % storename)
            raise
        if not created:
            shop.save()
        # else: Shop.save(update_fields=['updated'])
        for game in storeobj.games:
            logger.debug("Saving game: '%s' " % str(game))
            game_name = game.name.replace("\n", "", -1)
            game_name = game_name.strip()
            game_name = " ".join(game_name.split())
            try:
                g, created = GameProduct.objects.update_or_create(
                    name=game_name,
                    shop=shop,
                    defaults={
                        "stock": game.stock,
                        "price": game.price,
                        "name": game_name,
                    },
                )
                g.save()
            except Exception as err:
                logger.warning("Failed to save product '%s'; '%s'", (str(game), err))


def getStoreData():
    # Stores todo ( spelexperten, midgård games, storochliten, http://www.unispel.com,  www.spelochsant.se )
    # A = AlphaSpel()
    # D = DragonsLair()
    # W = WorldOfBoardGames()
    # A = AlltPaEttkort()
    # R = RetroSpelButiken()
    # P = Playoteket()
    # four = FourGames()
    # F = FirstPlayer()
    # G = GamesMania()
    return stores.__all__


def main():
    args, parser = parse_args()
    if args.compare:
        matchGamesWithWishes()
        sys.exit(0)
    if args.wishlist:
        genWishlist()  # make a collector function
        sys.exit(0)
    if args.liststores:
        print(getStoreData())
        sys.exit(0)
    if args.parsestore:
        stores = getStoreData()
        print("Parsing store %s" % (args.parsestore))
        save_gameProducts(args.parsestore)
        sys.exit(0)


if __name__ == "__main__":
    # application = get_wsgi_application()
    main()
