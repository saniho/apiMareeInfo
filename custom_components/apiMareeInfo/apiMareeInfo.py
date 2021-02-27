import logging
from datetime import datetime
import json
import requests
_LOGGER = logging.getLogger(__name__)

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

        #with open('port.json', 'w') as outfile:
        #    json.dump(jsonData, outfile)
        self._nomDuPort = jsonData["contenu"]["marees"][0]['lieu']
        self._dateCourante = jsonData["contenu"]["marees"][0]['datetime']

        a = {}
        myMarees = {}
        j = 0
        for maree in jsonData["contenu"]["marees"][:6]:
            i = 0
            for ele in maree["etales"]:
                dateComplete = datetime.fromisoformat(ele["datetime"])
                detailMaree = {"coeff": ele.get("coef", ""), "hauteur": ele["hauteur"], \
                    "horaire": dateComplete.strftime( "%H:%M"), \
                    "etat" : ele["type_etale"], "nieme": i, "jour": j, "date": ele["datetime"], \
                    "dateComplete" : dateComplete.replace(tzinfo=None)}
                clef = "horaire_%s_%s"%(j,i)
                myMarees[clef] = detailMaree
                #print(clef, detailMaree)
                i += 1
            j += 1
        self._donnees = myMarees

        dicoPrevis = {}
        for ele in jsonData["contenu"]["previs"]["detail"]:
            dateComplete = datetime.fromisoformat(ele["datetime"])
            detailPrevis = {"forcevnds": ele.get("forcevnds", ""), "rafvnds": ele.get("rafvnds", ""), \
                           "dirvdegres": ele.get("dirvdegres", ""), \
                           "dateComplete": dateComplete.replace(tzinfo=None), \
                           "nuagecouverture": ele.get("nuagecouverture",""),
                           "precipitation": ele.get("precipitation",""),
                           "teau": ele.get("teau",""),
                           "t": ele.get("t",""),
                           "risqueorage": ele.get("risqueorage",""),
                           "dirhouledegres": ele.get("dirhouledegres",""),
                           "hauteurhoule": ele.get("hauteurhoule",""),
                           "periodehoule": ele.get("periodehoule",""),
                           "hauteurmerv": ele.get("hauteurmerv",""),
                           "periodemerv": ele.get("periodemerv",""),
                           "hauteurvague": ele.get("hauteurvague","")

                           }
            clef = dateComplete
            dicoPrevis[clef] = detailPrevis
        self._donneesPrevis = dicoPrevis


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

    def getPrevis(self):
        return self._donneesPrevis
