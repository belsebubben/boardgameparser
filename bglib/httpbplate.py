#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import sys
import os
import glob
VENVPATH="~/fillinpathhere"
sys.path.append(VENVPATH)
from bs4 import BeautifulSoup
import sqlite3
from http import cookiejar
from urllib import parse
import urllib.request
import gzip
import json
import time
from random import randint

UA="Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0"
SESSCOOKIEPATH=""

DEBUG = False

def guessCharset(s, encodings=('utf-8', "iso-8859-1", "windows-1251", "windows-1252", "ascii", "latin1", "utf-16", "utf-32")):
    for encoding in encodings:
        try:
            s.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            pass
    return 'utf-8'

def createHttpRequest(url, cookiejar=None):
        '''
        '''
        urlparts = parse.urlparse(url)
        headers = { 'User-Agent' : UA, 'Referer' : url, 'Cache-Control':  "max-age=0", 
                "Accept-Language": "sv-SE,en;q=0.7,en-US;q=0.3a", "Accept-Encoding":"gzip, deflate",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Pragma": "no-cache"}
        req = urllib.request.Request(url, None, headers)
        if cookiejar:
            cookiejar.add_cookie_header(req)
        if DEBUG: print(req.__dict__) 
        with urllib.request.urlopen(req) as response:
            resp = response.read()
            if response.getheader("Content-Encoding") == "gzip":
                resp = gzip.decompress(resp)
            try:
                charset = response.getheader("Content-Type").split("charset=")[1]
            except:
                charset = guessCharset(resp)

            if DEBUG: print("Response:", response.getheaders()) #DEBUG
            if DEBUG: print("Charset: ", charset) #DEBUG

        return (resp, charset)

def getUrlSoupData(resp, charset):
        '''
        >>> getUrlSoupData(pycurl.Curl(), BytesIO)
        BeautifulSoup()
        '''
        #charset = resp.getheader("Content-Type").split("charset=")[1]

        html = resp
        #print(html) # DEBUG
        return BeautifulSoup(html.decode(charset or "ISO-8859-1" ), "lxml")

## Cookie stuff
class BrowserCookieError(Exception):
        pass

def create_cookie(host, path, secure, expires, name, value):
    """Shortcut function to create a cookie"""
    return cookiejar.Cookie(0, name, value, None, False, host, host.startswith('.'), host.startswith('.'), path, True, secure, expires, False, None, None, {})

class cookiegetter():
    def session_cookie_file(self):
        if sys.platform.startswith("linux"):
            session_cookie_files = glob.glob(os.path.expanduser("~/.mozilla/firefox/*.default*/sessionstore-backups/recovery.js"))
        if session_cookie_files:
            self.sessioncookiefile = session_cookie_files[0]
        else:
            raise browsercookieerror('failed to find firefox session cookies')


    def cookie_file(self):
        if sys.platform.startswith('linux'):
            cookie_files = glob.glob(os.path.expanduser('~/.mozilla/firefox/*.default*/cookies.sqlite'))
        if cookie_files:
            return cookie_files[0]
        else:
            raise browsercookieerror('failed to find firefox cookie')

    def session_cookies_domain(self):
        self.session_cookie_file()
        js = json.loads(open(self.sessioncookiefile, "r").read())
        expires = str(int(time.time()) + 3600 * 24 * 7)
        for window in js.get('windows', []):
            for cookie in window.get('cookies', []):
                if self.domain in cookie["host"]:
                    c = create_cookie(cookie.get('host', ''), cookie.get('path', ''), False, expires, cookie.get('name', ''), cookie.get('value', ''))
                    self.cj.set_cookie(c)

    def cookies_for_domain(self):
        #.mozilla/firefox/xla159eb.default/sessionstore-backups/recovery.js
        con = sqlite3.connect(self.cookie_file())
        cur = con.cursor()
        cur.execute('select host, path, isSecure, expiry, name, value from moz_cookies WHERE baseDomain like "%s"' % self.domain)
        self.cj = cookiejar.CookieJar()
        for item in cur.fetchall():
            c = create_cookie(*item)
            self.cj.set_cookie(c)
            con.close()

        self.session_cookies_domain()


        return self.cj

    def __init__(self, domain):
        self.domain = domain
        self.cookie_file()
        self.cookies_for_domain()
