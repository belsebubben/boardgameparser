from bglib.scrapers import *

def findprice(x):
    try:
        price = x.find("div", {"class": "xlarge"}).next_element.next_element
    except:
        price = "Unknown"
    return price

class WorldOfBoardGames(GenericScraper):

    def pageRanger(self):
        return [x for x in range(0,self.prodcount,self.pagestepper)][1:]

    def urlmaker(self):
        return [self.url % pagenr for pagenr in self.pageRanger()]

    def parsefirstpage(self):
        scrapelogger.debug('Parsing first page url: "%s"' % self.firstpageurl)
        try:
            self.firstpage = getpagesoup(self.firstpageurl)
            self.prodcount = int(self.firstpage.find("div", text=re.compile("\d+-\d+ av \d+")).text.strip().split()[-1])
            self.parsePage(self.firstpage, self.firstpageurl)
        except Exception as err:
            scrapelogger.warning('Error retreiving first page %s' % err)
            self.failed +=1

    def __init__(self):
        self.pagestepper = 40
        self.startpagenr = 1
        self.url = 'https://www.worldofboardgames.com/sallskapsspel/%s#kategori'
        self.firstpageurl = 'https://www.worldofboardgames.com/sallskapsspel'
        self.gamesoup = {'name': {'funcs': (lambda x: x.findChild("a")["title"],\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (findprice,)},\
                'stock':{'funcs': (lambda x: x.find("a", {"class": "button green buttonshadow saveScrollPostion"}) is not None ,)}}

        self.gamelistsoup = {'funcs':(lambda x: x.find_all("div", {"class": "product"}),)}
        self.pagemaxnr = {'funcs':(lambda x: int(x.find('div', {'style': 'float: left; width: 34%; text-align: center;'}).text.strip().split()[-1]),)}

        self.parsetype = 'soup'
        super().__init__()
