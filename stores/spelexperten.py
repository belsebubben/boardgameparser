from bglib.scrapers import *

def findprice(x):
    try:
        price = x.find("span", {"class": "PT_PrisNormal"}).text
    except:
        price = "Unknown"
    return price

class Spelexperten(GenericScraper):

    def pageRanger(self):
        return [x for x in range(1,self.pgmaxnr,self.pagestepper)][1:]

    def urlmaker(self):
        return [self.url % (pagenr,pagenr+self.pagestepper) for pagenr in self.pageRanger()]

    def parsefirstpage(self):
        scrapelogger.debug('Parsing first page url: "%s"' % self.firstpageurl)
        try:
            self.firstpage = getpagesoup(self.firstpageurl)
            self.parsePage(self.firstpage, self.firstpageurl)
            self.pagestepper = int(self.firstpage.find("input", {"id": "ajax_stop"}).attrs["value"])
            self.pgmaxnr = int(self.firstpage.find("input", {"id": "ajax_max"}).attrs["value"])
        except Exception as err:
            scrapelogger.warning('Error retreiving first page %s' % err)
            self.failed = True


    def __init__(self):

        self.startpagenr = 1
        self.url = "https://www.spelexperten.com/cgi-bin/ibutik/AIR_ibutik.fcgi?funk=steg_tva&Ajax=J&artgrp=2&limit=&Visn=Std&Sort=PublDat&visa=%d-%d"
        self.firstpageurl = "https://www.spelexperten.com/sallskapsspel/"
        self.gamesoup = {'name': {'funcs': (lambda x: x.find("div", {"class": "PT_Beskr"}).text,\
                lambda x: ' '.join(re.split('\s+', x, flags=re.UNICODE)))},\
                'price': {'funcs': (findprice,)},\
                'stock':{'funcs': (lambda x: x.find_all("td", {"class": lambda L: L and L.startswith('Knapp_Kop') }),lambda x: any(["Köp" in h.text for h in x]))}}

        self.gamelistsoup = {'funcs':(lambda x: x.find_all("div", {"class": "PT_Wrapper"}),)}
        self.pagemaxnr = False

        self.parsetype = 'soup'

        super().__init__()

