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
#LOGFORMAT = "%(asctime)s %(levelname)s: line:%(lineno)d  func:%(funcName)s;  %(message)s"
#bgparselogger = logging.StreamHandler(stream=sys.stderr)
scrapelogger = logging.getLogger('root.scraper')
#logger.addHandler(bgparselogger)
#if debug:
#    logger.setLevel(logging.DEBUG)
#else:
#    logger.setLevel(logging.INFO)
#logformatter = logging.Formatter(LOGFORMAT)
#bgparselogger.setFormatter(logformatter)

def getpagesoup(url):
    scrapelogger.debug('get page soup from "%s"' % url)
    try:
        html, charset = httpbplate.createHttpRequest(url)
        pagesoup = httpbplate.getUrlSoupData(html, charset)
    except:
        scrapelogger.warning('Failed to get page from %s' % url)
        raise
    return pagesoup

class GenericScraper():
    def __init__(self):
        self.games = []
        self.failed = False
        self.nrerrors = 0
        self.nrparsed = 0
        self.pgstep = 1
        self.parsefirstpage()
        self.setpgmaxnr()
        self.parsePages()

    def parsefirstpage(self):
        scrapelogger.debug('Parsing first page url: "%s"' % self.firstpageurl)
        try:
            self.firstpage = getpagesoup(self.firstpageurl)
            self.parsePage(self.firstpage, self.firstpageurl)
        except Exception as err:
            scrapelogger.warning('Error retreiving first page %s' % err)
            self.failed = True

    def getGameElements(self,soup,url):
        '''Get a list of soup elements (one for each game)'''
        games = soup
        try:
            for f in self.gamelistsoup['funcs']:
                games = f(games)
                scrapelogger.debug(games)
        except Exception as err:
            scrapelogger.warning('Failed to get game element list for %s: Error: "%s" ' % (url, err))
        return games

    def parsePage(self,soup,url):
        elemnr = -1
        for game in self.getGameElements(soup, url):
            elemnr += 1
            data = {}
            try:
                for dtype in ('name', 'stock', 'price'):
                    scrapelogger.debug('Deriving: "%s"' % (dtype))
                    gametypesoup = game

                    for f in self.gamesoup[dtype]['funcs']:
                        gametypesoup =  f(gametypesoup)
                        scrapelogger.debug('Derived "%s"' % (gametypesoup))

                    data[dtype] = gametypesoup

            except Exception as err:
                scrapelogger.warning('Error in parsing inside type:"%s" Error:"%s;";\n\
                        Game element nr %d: >>> %s <<<; Error: "%s"; Url:"%s"\n' % (dtype, err, elemnr, game, err, url))
                self.nrerrors +=1
                continue

            game = GameItem(**data)
            scrapelogger.info(game)
            self.games.append(game)
            self.nrparsed +=1

    def setpgmaxnr(self):
        if not self.pagemaxnr: # Set this to False in parser to skip
            return
        for f in self.pagemaxnr['funcs']:
            self.firstpage = f(self.firstpage)
        self.pgmaxnr = self.firstpage
        assert(type(self.pgmaxnr) == int)

    def pageRanger(self):
        return [x for x in range(self.startpagenr,self.pgmaxnr,self.pgstep)]

    def urlmaker(self):
        return [self.url % pagenr for pagenr in self.pageRanger()] # "http://example.com&page=%d"

    def parsePages(self):
        for url in self.urlmaker():
            scrapelogger.debug("Starting parse of page with url '%s'" % url)
            soup = getpagesoup(url)
            self.parsePage(soup, url)
