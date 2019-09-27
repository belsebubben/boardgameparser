from bglib.scrapers import *

class GamesMania(GenericScraper):
    def __init__(self):

        self.startpagenr = 2
        self.url = 'https://www.gamesmania.se/product-category/alla-sallskapsspel/page/%d/'
        self.firstpageurl = 'https://www.gamesmania.se/product-category/alla-sallskapsspel/'

        self.gamesoup = {'name': {'funcs': (lambda x: x.find('p', {'class': 'name product-title'}).text,\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (lambda x: x.find("span", {"class": "woocommerce-Price-amount amount"}).text.replace("kr", "" ).replace(",", "").strip(),)},\
                'stock':{'funcs': (lambda x: 'out-of-stock' not in x.attrs['class'],)}}

        self.gamelistsoup = {'funcs':(lambda x: x.find_all('div', {"class": lambda L: L and L.find('purchasable product-type-simple') > -1 }),)}

        self.pagemaxnr = {'funcs':(lambda x: int(x.find('nav', {'class': 'woocommerce-pagination'}).find_all('a')[-2].text),)}
        self.parsetype = 'soup'
        super().__init__()
