#!/home/carl/.pyvenv3/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from bs4 import BeautifulSoup
import sys

html = open("tmp/playoteket").read()
soup = BeautifulSoup(html, "lxml")
#sou
#soup
#soup.find_all("tr")
#soup.find("center")
#center = soup.find("center")
#center.find("tr")
#soup
#soup.find("center")
#c = soup.find("center")
#c
#c.find("tr")
#c.find_all("tr")
#c.find_all("tr")[4:]
#c.find_all("tr")[:3]
#c.find_all("table")
#ctables = c.find_all("table")
#ctables
#for f in ctables:
# c
#for f in ctables:
# print(c)
# print("__" * 40)
#for f in ctables:
# print("__")
#for f in ctables:
# print("__")
# 
#for f in ctables:
# print("_" * 100)
# print(c)
# print("_" * 100)
#soup.find_all("td", lambda L: L and "Brädspel" in L.text })
#soup.find_all("td")
#for ff in soup.find_all("td"):
# if "brädspel" in ff.text.lower()	[B
#for ff in soup.find_all("td"):
# if "brädspel" in ff.text.lower():
#  print(ff)
#for ff in soup.find_all("td"):
# if "brädspel" in ff.text.lower():
#  print(ff)
#  print(ff.find_parent("tr"))
#


#tds = soup.find_all(lambda x: x is not None and x.name == "td" and x.has_attr("next_element") and "brädspel" in x.next_element.lower())
#tds = soup.find_all("td", {lambda x: x and "brädspel" in x.text.lower()})

#print(tds)

#for td in soup.find_all("td"):
#    if "brädspel" in td.text.lower():
#for bgtd in bgtds[10]:
    #print(bgtd.find_next_siblings("td"))
    #print(bgtd.find_parent("tr"))
#    print(bgtds[10].__dict__)
#print(bgtds[10].__dict__)
#print("bgtddict: ", bgtds[10].__dict__)
#print("trparent:", bgtds[10].find_parent("tr"))
#psibs = bgtds[10].find_previous_siblings("td")
#nsibs =  bgtds[10].find_next_siblings("td")
#trparent = bgtds[10].find_parent("tr")
#print(len(trparent.find_all("td")))
#print(len(psibs), len(nsibs))
#print("thistd:", bgtds[10])
#prevtr = trparent.find_previous("tr")
#prevtr2 = prevtr.find_previous("tr")
#print("thistdtest:", trparent.find_all("td")[len(psibs)])
#print("prevtr2tds:", prevtr2.find_all("td")[len(psibs)])

games = soup.find_all("div", {"class": "product-container"})
pages = soup.find("ul", {"class": "pagination"})


for game in games:
    print("game;\n", game.prettify(), "\n\n")
    try:
        print("name;", game.find("h3", {"class": "thename"}).string)
        print("price;", game.find("span", {"class": "amount"}).string.strip())
    except:
        pass

print(pages.find_all("span")[-1].string)

#for bgtd in bgtds:
#    try:
#        trparent = bgtd.find_parent("tr")
#        prevtr = trparent.find_previous("tr")
#        prevtr2 = prevtr.find_previous("tr")
#        psibs = bgtd.find_previous_siblings("td")
#        #nsibs =  bgtds[10].find_next_siblings("td")
#        print()
#        name = prevtr2.find_all("td")[len(psibs)].text
#        stock = "i lager" in  bgtd.text.lower()
#        price = bgtd.find("b").text
#        print("Name {}; stock {}; price {}".format(name, stock, price))
#    except:
#        print(sys.exc_info())



