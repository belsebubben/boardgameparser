from bglib.scrapers import *

class DragonsLair(GenericScraper):
    def __init__(self):

        self.startpagenr = 1
        self.url = 'https://www.dragonslair.se/product/boardgame/sort:recent/price:1:10000/%d'
        self.firstpageurl = 'https://www.dragonslair.se/product/boardgame/sort:recent/price:1:10000/1'
        self.gamesoup = {'name': {'funcs': (lambda x: x.find("a", {"class": "label"}).text.strip(),\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)) )},\
                'price': {'funcs': (lambda x: x.find("span", {"class": "price"}).text.strip() or None,)},\
                'stock':{'funcs': (lambda x: x.find("div", {"class": "controls"}).text.strip(),\
                lambda x: "I lager: Ja" in x)}}

        self.gamelistsoup = {'funcs':(lambda x: x.find("div", {"id": "product-list"}),\
                lambda x: x.find_all("div", {"class": "container"}))}

        self.pagemaxnr = {'funcs':(lambda x: x.find("ul", {"class": "pagination"}),\
                lambda x: int(x.find_all('a')[-2].text))}

        self.parsetype = 'soup'
        super().__init__()
