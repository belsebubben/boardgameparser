from bglib.scrapers import *

class AlltPaEttkort(GenericScraper):
    def __init__(self):

        self.startpagenr = 2
        self.url = 'https://www.alltpaettkort.se/butik/page/%d/?orderby=date'
        self.firstpageurl = 'https://www.alltpaettkort.se/butik/?orderby=date'
        self.gamesoup = {'name': {'funcs': (lambda x: x.find("h2").text,\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (lambda x: x.find("span", {"class": "price"}).text.replace("kr", "" ).replace(",", "").strip(),)},\
                'stock':{'funcs': (lambda x: x.find("a", {"class": "button add_to_cart_button product_type_simple"}) is not None,)}}

        self.gamelistsoup = {'funcs':(lambda x: x.find_all("li", {"class": lambda L: L and L.find('product type-product') > -1 }),)}
        self.pagemaxnr = {'funcs':(lambda x: int(x.find('nav', {'class': 'woocommerce-pagination'}).find_all('a')[-2].text),)}

        self.parsetype = 'soup'
        super().__init__()
