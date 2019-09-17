#!/usr/bin/python3

from bs4 import BeautifulSoup
import sys
import httpbplate

html, charset = httpbplate.createHttpRequest(URL)

soup = httpbplate.getUrlSoupData(html, charset)

soup.find('nav', {'class': 'woocommerce-pagination'})
