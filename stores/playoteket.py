from bglib.scrapers import *

class Playoteket(GenericScraper):
    def __init__(self):

        self.startpagenr = 2
        self.url = 'https://www.playoteket.com/strategi?orderby=quantity&orderway=desc&p=%d'
        self.firstpageurl = 'https://www.playoteket.com/strategi?orderby=quantity&orderway=desc'
        self.gamesoup = {'name': {'funcs': (lambda x: x.find("h3", {"class": "thename"}).string,\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (lambda x: x.find("span", {"class": "amount"}).string.strip(),)},\
                'stock':{'funcs': (lambda x: True,)}}

        self.gamelistsoup = {'funcs':(lambda x: x.find_all("div", {"class": "product-container"}),)}
        self.pagemaxnr = {'funcs':( lambda x: x.find("ul", {"class": "pagination"}),\
                lambda x: int(x.find_all("span")[-1].string),)}

        self.parsetype = 'soup'
        super().__init__()
