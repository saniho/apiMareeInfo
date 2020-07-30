

from bs4 import BeautifulSoup
from urllib.request import urlopen

# urlpage = "http://fr.wisuki.com/forecast/1522/saint-jean-de-monts"
# page = urlopen(urlpage)
# soup = BeautifulSoup(page, 'html.parser')
# #print( soup )
# print(soup.find(id='day-9'))
#
#
# urlpagemaree = "http://fr.wisuki.com/tide/1522/saint-jean-de-monts"
# page = urlopen(urlpagemaree)
# soup = BeautifulSoup(page, 'html.parser')
# #print( soup )
# print(soup.find(id='content'))



urlpagemaree = "http://maree.info/124"
import urllib.request
req = urllib.request.Request(
    urlpagemaree,
    data=None,
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    })
page = urllib.request.urlopen(req)
#print( page)
soup = BeautifulSoup(page, 'html.parser')
#pagehtml = soup.find(id='MareeJours_1').prettify()
#f = open("pagehtml_1.html", "w").write( pagehtml )
#pagehtml = open( "pagehtml_1.html", "r").read()  # à finir
# print(element)
col = 0
for ligne in pagehtml.split("</td>")[1:-1]:
    col += 1
    x = ligne.replace("\n","").split("</td>")
    #print("******")
    chaine = x[0]
    for carReplacement in ["<td>","<br/>","</b>", "<b>"]:
        chaine = chaine.replace(carReplacement,"")
    for x in range(5):
        chaine = chaine.replace("  ", " ")
    tab = chaine.strip().split(" ")
    if( col == 1 ):
        tabHauteurs = tab
    else:
        tabCoeffs = tab
    #print(x)

chaine = pagehtml.split("</td>")[0]

chaine = chaine.split("<td>")[1]
for carReplacement in ["<td>", "<br/>", "</b>", "<b>", "\n"]:
    chaine = chaine.replace(carReplacement, " ")
for x in range(5):
    chaine = chaine.replace("  ", " ")
tab = chaine.strip().split(" ")
tabHoraires = tab
#

import copy
bassemer = copy.copy( tabHauteurs )
bassemer.sort()
bassemer = bassemer[:2]
myTab = {}
if (len(tabCoeffs)==1):
    # une seule marée Haute ou basse
    i = 0
    for x in tabHoraires:
        myTab[ x ] = { "coeff" : tabCoeffs[0], "hauteur": tabHauteurs[i]}
        i += 1
    pass
else:
    i = 0
    for x in tabHoraires[:2]:
        myTab[ x ] = { "coeff" : tabCoeffs[0], "hauteur": tabHauteurs[i]}
        i += 1
    for x in tabHoraires[2:]:
        myTab[ x ] = { "coeff" : tabCoeffs[1], "hauteur": tabHauteurs[i]}
        i += 1

for x in myTab:
    if ( myTab[x]['hauteur'] in bassemer):
        myTab[x]['etat'] = "BM"
    else:
        myTab[x]['etat'] = "HM"
print(myTab)

