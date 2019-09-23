import sys
import os
sys.path.insert(0, os.path.dirname(os.path.join(os.path.dirname(__file__), 'stores')))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
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

# Selenium
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# local imports
from bglib.lib import *
from bglib import httpbplate

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

def getpagesoup(url):
    try:
        html, charset = httpbplate.createHttpRequest(url)
        pagesoup = httpbplate.getUrlSoupData(html, charset)
    except:
        logger.warning('Failed to get page from %s' % url)
        raise
    return pagesoup

class GenericScraper():
    def __init__(self):
        self.games = []
        self.failed = False
        self.nrerrors = 0
        self.nrparsed = 0
        self.parsefirstpage()
        self.setpgmaxnr()
        self.parsePages()

    def parsefirstpage(self):
        logger.debug('Parsing first page')
        try:
            self.firstpage = getpagesoup(self.firstpageurl)
            self.parsePage(self.firstpage, self.firstpageurl)
        except Exception as err:
            logger.warning('Error retreiving first page %s' % err)
            self.failed = True

    def getGameElements(self,soup):
        '''Get a list of soup elements (one for each game)'''
        games = soup
        try:
            for f in self.gamelistsoup['funcs']:
                games = f(games)
                logger.debug(games)
        except Exception as err:
            logger.warning('Failed to get game element list for %s: Error: "%s" ' % (self.url, err))
        return games

    def parsePage(self,soup,url):
        elemnr = -1
        for game in self.getGameElements(soup):
            elemnr += 1
            data = {}
            try:
                for dtype in ('name', 'stock', 'price'):
                    logger.debug('Deriving: "%s"' % (dtype))
                    gametypesoup = game

                    for f in self.gamesoup[dtype]['funcs']:
                        gametypesoup =  f(gametypesoup)
                        logger.debug('Derived "%s"' % (gametypesoup))

                    data[dtype] = gametypesoup

            except Exception as err:
                logger.warning('Error in parsing type:"%s" Error:"%s";\n Game element nr %d: >>> %s <<<; Error: "%s"; Url:"%s"\n' % (dtype, err, elemnr, game, err, url))
                self.nrerrors +=1
                continue

            game = GameItem(**data)
            print(game)
            self.games.append(game)
            self.nrparsed +=1

    def setpgmaxnr(self):
        for f in self.pagemaxnr['funcs']:

            self.firstpage = f(self.firstpage)
        self.pgmaxnr = self.firstpage
        assert(type(self.pgmaxnr) == int)

    def parsePages(self):
        for pagenr in range(self.startpagenr,self.pgmaxnr):
            url = self.url % pagenr # "http://example.com&page=%d"
            soup = getpagesoup(url)
            self.parsePage(soup, url)
