from bglib.scrapers import *

def name(td):
    trparent = td.find_parent("tr")
    prevtr = trparent.find_previous("tr")
    prevtr2 = prevtr.find_previous("tr")
    psibs = td.find_previous_siblings("td")
    return prevtr2.find_all("td")[len(psibs)].text

class RetroSpelButiken(GenericScraper):
    def __init__(self):

        self.startpagenr = 2
        self.url = 'http://retrospelbutiken.se/store/category.php?category=190&page=%d&sort=0'
        self.firstpageurl = 'http://retrospelbutiken.se/store/category.php?category=190'
        self.gamesoup = {'name': {'funcs': (name,\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (lambda x: x.find("b").text,)},\
                'stock':{'funcs': (lambda x: "i lager" in  x.text.lower(),)}}

        self.gamelistsoup = {'funcs':(lambda x: [td for td in x.find_all("td") if td and hasattr(td, "text") and "brädspel" in td.text.lower()],)}
        self.pagemaxnr = {'funcs':(lambda x: x.find(string="Nästa Sida >"), lambda x: int(x.previous_element.find_previous('a').text.strip()))}

        self.parsetype = 'soup'
        super().__init__()
