import logging
from datetime import timedelta, datetime

import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
_LOGGER = logging.getLogger(__name__)
import time

class apiMareeInfo:
    def __init__(self):
        self._donnees = {}
        pass

    def getJson(self, url):
        try:
            import json
            session = requests.Session()
            response = session.post(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as error:
            response = {"error": "UNKERROR_001"}
            return response
        except requests.exceptions.HTTPError as error:
            return response.json()

    def setPort(self, lat, lng):
        self._lat = lat
        self._lng = lng
        self._url = \
            "http://webservices.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v20/previsionsSpot.php?lat=%s&lon=%s"%(lat, lng)

    def getInformationPort(self, jsonData = None):
        if (jsonData == None):
            jsonData = self.getJson(self._url)
        #print(jsonData)
        self._nomDuPort = jsonData["contenu"]["marees"][0]['lieu']
        self._dateCourante = jsonData["contenu"]["marees"][0]['datetime']

        a = {}
        myTab = {}
        j = 0
        for maree in jsonData["contenu"]["marees"][:4]:
            i = 0
            for ele in maree["etales"]:
                dateComplete = datetime.fromisoformat(ele["datetime"])
                detailMaree = {"coeff": ele.get("coef", ""), "hauteur": ele["hauteur"], \
                    "horaire": dateComplete.strftime( "%H:%M"), \
                    "etat" : ele["type_etale"], "nieme": i, "jour": j, "date": ele["datetime"], \
                    "dateComplete" : dateComplete.replace(tzinfo=None)}
                clef = "horaire_%s_%s"%(j,i)
                a[clef] = detailMaree
                #print(clef, detailMaree)
                i += 1
            j += 1
        myTab.update(a)
        self._donnees = myTab


    def getNomDuPort(self):
        return self._nomDuPort.split("©")[0].strip()

    def getCopyright(self):
        return "©SHOM"

    def getNomCompletDuPort(self):
        return self._nomDuPort

    def getDateCourante(self):
        return self._dateCourante

    def getInfo(self):
        return self._donnees
