import logging
from datetime import timedelta, datetime

from bs4 import BeautifulSoup
from urllib.request import urlopen
_LOGGER = logging.getLogger(__name__)
import time

class apiMareeInfo:
    def __init__(self):
        pass
    def getinformationPort(self, soup):
        import json
        script = soup.findAll('script')[7].string
        #print(script)
        jsonch = script[script.find('{'):script.rfind('}')+1]
        jsonch = jsonch.replace("null",'"None"').replace("true",'"True"')
        jsonch = jsonch.replace("false",'"False"').replace("'",'"')
        #print(jsonch)
        jsonData = json.loads(jsonch)
        #print(jsonData)
        self._nomDuPort = jsonData["PortNom"]
        self._dateCourante = str(jsonData["aujourdhui"])

    def getinformationJour(self, soup, idsoup, idJour):
        pagehtml = soup.find(id=idsoup).prettify()
        col = 0
        for ligne in pagehtml.split("</td>")[1:-1]:
            col += 1
            x = ligne.replace("\n", "").split("</td>")
            chaine = x[0]
            for carReplacement in ["<td>", "<br/>", "</b>", "<b>"]:
                chaine = chaine.replace(carReplacement, "")
            for x in range(5):
                chaine = chaine.replace("  ", " ")
            tab = chaine.strip().split(" ")
            if (col == 1):
                tabHauteurs = tab
            else:
                tabCoeffs = tab
            # print(x)

        chaine = pagehtml.split("</td>")[0]
        chaine = chaine.split("<td>")[1]
        for carReplacement in ["<td>", "<br/>", "</b>", "<b>", "\n"]:
            chaine = chaine.replace(carReplacement, " ")
        for x in range(5):
            chaine = chaine.replace("  ", " ")
        chaine = chaine.replace("h",":") # pour remplacer le h
        tab = chaine.strip().split(" ")
        tabHoraires = tab

        import copy
        bassemer = copy.copy(tabHauteurs)
        bassemer.sort()
        bassemer = bassemer[:2]
        myTab = {}
        nieme = 0
        if (len(tabCoeffs) == 1):
            # une seule marée Haute ou basse
            i = 0
            for x in tabHoraires:
                nieme += 1
                indice = "horaire_%s_%s" %(idJour, nieme)
                myTab[indice] = {"coeff": tabCoeffs[0], "hauteur": tabHauteurs[i], "horaire": x, "nieme":nieme, "jour" : idJour}
                i += 1
            pass
        else:
            i = 0
            for x in tabHoraires[:2]:
                nieme += 1
                indice = "horaire_%s_%s" %(idJour, nieme)
                myTab[indice] = {"coeff": tabCoeffs[0], "hauteur": tabHauteurs[i], "horaire": x, "nieme":nieme, "jour" : idJour}
                i += 1
            for x in tabHoraires[2:]:
                nieme += 1
                indice = "horaire_%s_%s" %(idJour, nieme)
                myTab[indice] = {"coeff": tabCoeffs[1], "hauteur": tabHauteurs[i], "horaire": x, "nieme":nieme, "jour" : idJour}
                i += 1

        for x in myTab:
            if (myTab[x]['hauteur'] in bassemer):
                myTab[x]['etat'] = "BM"
            else:
                myTab[x]['etat'] = "HM"
        return myTab

    def getInformationPort(self, idPort):
        urlpagemaree = "https://maree.info/%s" %(idPort)
        _LOGGER.warning("tente un update  ? ... %s" % (urlpagemaree))
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        import urllib.request
        req = urllib.request.Request(
            urlpagemaree,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
            })
        page = urllib.request.urlopen(req, context=ctx)
        soup = BeautifulSoup(page, 'html.parser')
        myTab = {}
        myTab.update(self.getinformationJour( soup, "MareeJours_0", "0"))
        myTab.update(self.getinformationJour( soup, "MareeJours_1", "1"))

        self.getinformationPort(soup)
        for horaireMaree in myTab.keys():
            info = myTab[horaireMaree]
            nieme = info["nieme"]
            date = datetime.strptime(self.getDateCourante() +" " + info["horaire"],"%Y%m%d %H:%M")
            date = date + timedelta(int(info["jour"]))
            info["dateComplete"] = date
        self._donnees = myTab

    def getInfo(self):
        return self._donnees

    def getNomDuPort(self):
        return self._nomDuPort

    def getDateCourante(self):
        return self._dateCourante

