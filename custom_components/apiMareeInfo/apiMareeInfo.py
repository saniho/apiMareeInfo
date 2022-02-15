import logging
import datetime
import json
import requests
_LOGGER = logging.getLogger(__name__)


class ListePorts:
    def __init__(self):
        # fonction init aucune action à réaliser
        pass

    def getjson(self, url):
        response = None
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
        pass

    def getlisteport(self, nomport):
        url = "http://webservices.meteoconsult.fr/meteoconsultmarine/android/100/fr/v20/recherche.php?rech=%s&type=48" %(nomport)
        print(url)
        retour = self.getjson(url)
        print(retour)
        for x in retour["contenu"]:
            print(x["id"], x["nom"], x[ "lat"], x["lon"])
        return retour


class ApiMareeInfo:
    def __init__(self):
        self._donnees = {}
        self._nomDuPort = None
        self._dateCourante = None
        self._lat = None
        self._lng = None
        pass

    def getjson(self, url):
        response = None
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

    def setport(self, lat, lng):
        self._lat = lat
        self._lng = lng
        self._url = \
            "http://webservices.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v20/previsionsSpot.php?lat=%s&lon=%s"%(lat, lng)
        """ autre url possible
        self._url = \
        #    "http://webservices.meteoconsult.fr/meteoconsultmarine/android/100/fr/v20/previsionsSpot.php?lat=%s&lon=%s" % (
        #    lat, lng)
        #print(self._url)
        """

    def getinformationport(self, jsondata = None, outfile=None):
        if (jsondata == None):
            jsondata = self.getjson(self._url)

        if outfile != None:
            with open(outfile, 'w') as outfilev:
                json.dump(jsondata, outfilev)
        self._nomDuPort = jsondata["contenu"]["marees"][0]['lieu']
        self._dateCourante = jsondata["contenu"]["marees"][0]['datetime']

        a = {}
        myMarees = {}
        j = 0
        for maree in jsondata["contenu"]["marees"][:6]:
            i = 0
            for ele in maree["etales"]:
                dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                detailMaree = {"coeff": ele.get("coef", ""), "hauteur": ele["hauteur"],
                    "horaire": dateComplete.strftime( "%H:%M"),
                    "etat" : ele["type_etale"], "nieme": i, "jour": j, "date": ele["datetime"],
                    "dateComplete" : dateComplete.replace(tzinfo=None)}
                clef = "horaire_%s_%s"%(j,i)
                myMarees[clef] = detailMaree
                #print(clef, detailMaree)
                i += 1
            j += 1
        self._donnees = myMarees

        dicoPrevis = {}
        for ele in jsondata["contenu"]["previs"]["detail"]:
            dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
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

    def getnomduport(self):
        return self._nomDuPort.split("©")[0].strip()

    def getcopyright(self):
        return "©SHOM"

    def getnomcompletduport(self):
        return self._nomDuPort

    def getdatecourante(self):
        return self._dateCourante

    def getinfo(self):
        return self._donnees

    def getprevis(self):
        return self._donneesPrevis

    def getNextPluie(self):
        dateCourante = datetime.datetime.now()
        for x in self._donneesPrevis.keys():
            if self._donneesPrevis[x]["dateComplete"] > dateCourante:
                if self._donneesPrevis[x]["precipitation"] != 0:
                    return self._donneesPrevis[x]["dateComplete"]
        return ""
