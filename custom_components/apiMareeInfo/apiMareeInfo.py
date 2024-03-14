import logging
import datetime
import json
try:
    import requests
except:
    pass

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
        url = "http://webservices.meteoconsult.fr/meteoconsultmarine/android/100/fr/v20/recherche.php?rech=%s&type=48" % (
            nomport)
        url = "https://ws.meteoconsult.fr/meteoconsultmarine/android/100/fr/v30/recherche.php?rech=%s&type=48" % (
            nomport)
        _url = \
            "http://ws.meteoconsult.fr/meteoconsultmarine/android/100/fr/v30/recherche.php?rech=%s&type=48" % (
                nomport)

        print(url)
        retour = self.getjson(url)
        print(retour)
        for x in retour["contenu"]:
            print(x["id"], x["nom"], x["lat"], x["lon"])
        return retour


class MeteoMarine:
    def __init__(self, lat, lng):

        self._url = \
            "http://webservices.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v20/previsionsSpot.php?lat=%s&lon=%s" % (
                lat, lng)
        self._url = \
            "http://ws.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v30/previsionsSpot.php?lat=%s&lon=%s" % (
                lat, lng)
        """ autre url possible
        self._url = \
        #    "http://webservices.meteoconsult.fr/meteoconsultmarine/android/100/fr/v20/previsionsSpot.php?lat=%s&lon=%s" % (
        #    lat, lng)
        #print(self._url)
        """
        pass

    def getdata(self):
        response = None
        try:
            import json
            session = requests.Session()
            response = session.post(self._url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as error:
            response = {"error": "UNKERROR_001"}
            return response
        except requests.exceptions.HTTPError as error:
            return response.json()
        pass


class stormIO:
    def __init__(self, lat, lng, storm_key):
        import requests
        self._lat = lat
        self._lng = lng
        self._storm_key = storm_key

    def getdata(self):
        import datetime
        now = datetime.datetime.now()
        nowJ2 = now + datetime.timedelta(days=2)
        self._deb = now.strftime("%Y-%m-%d %H:%M:%S+00:00")
        self._fin = nowJ2.strftime("%Y-%m-%d %H:%M:%S+00:00")
        # self._deb = "2022-12-14 03:40:44+00:00"
        # self._fin = "2022-12-20 16:40:44+00:00"
        response = requests.get(
            'https://api.stormglass.io/v2/tide/extremes/point',
            params={
                'lat': self._lat,
                'lng': self._lng,
                'start': self._deb, 'end': self._fin,  # Convert to UTC timestam
            },
            headers={
                'Authorization': self._storm_key
            }
        )
        # Do something with response data.
        json_data = response.json()
        return json_data


class ApiMareeInfo:
    def __init__(self):
        self._donnees = {}
        self._nomDuPort = None
        self._dateCourante = None
        self._maxhours = None
        self._lat = None
        self._lng = None
        self._message = ""
        self._error = False
        self._errorMessage = ""
        pass

    def getjson(self, origine, info=None):
        if origine == "MeteoMarine":
            mm = MeteoMarine(self._lat, self._lng)
            return mm.getdata()
        elif origine == "stormio":
            mm = stormIO(self._lat, self._lng, info["stormkey"])
            return mm.getdata()

    def setport(self, lat, lng):
        self._lat = lat
        self._lng = lng

    def setmaxhours(self, maxhours):
        self._maxhours = maxhours

    def getinformationport(self, jsondata=None, outfile=None, origine="MeteoMarine", info=None):
        if (jsondata is None):
            jsondata = self.getjson(origine, info)

        if outfile is not None:
            with open(outfile, 'w') as outfilev:
                json.dump(jsondata, outfilev)
        if origine == "MeteoMarine":
            self._nomDuPort = jsondata["contenu"]["marees"][0]['lieu']
            self._dateCourante = jsondata["contenu"]["marees"][0]['datetime']
        elif origine == "stormio":
            if "station" in jsondata["meta"]:
                self._nomDuPort = jsondata["meta"]["station"]['name']
                self._errorMessage = ""
                self._error = False
            else:
                self._nomDuPort = ""
                self._errorMessage = jsondata["errors"]["key"]
                self._error = True
            self._dateCourante = datetime.datetime.now()
        else:
            raise RuntimeError("Data Origin unknow")
        self._httptimerequest = datetime.datetime.now()

        a = {}
        myMarees = {}
        dicoPrevis = {}
        if (origine == "MeteoMarine") and (not self._error):
            j = 0
            for maree in jsondata["contenu"]["marees"][:6]:
                i = 0
                for ele in maree["etales"]:
                    dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                    detailMaree = {"coeff": ele.get("coef", ""), "hauteur": ele["hauteur"],
                                   "horaire": dateComplete.strftime("%H:%M"),
                                   "etat": ele["type_etale"], "nieme": i, "jour": j, "date": ele["datetime"],
                                   "dateComplete": dateComplete.replace(tzinfo=None)}
                    clef = "horaire_%s_%s" % (j, i)
                    myMarees[clef] = detailMaree
                    # print(clef, detailMaree)
                    i += 1
                j += 1
            self._donnees = myMarees

            for ele in jsondata["contenu"]["previs"]["detail"]:
                dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                detailPrevis = {"forcevnds": ele.get("forcevnds", ""), "rafvnds": ele.get("rafvnds", ""),
                                "dirvdegres": ele.get("dirvdegres", ""),
                                "dateComplete": dateComplete.replace(tzinfo=None),
                                "nuagecouverture": ele.get("nuagecouverture", ""),
                                "precipitation": ele.get("precipitation", ""),
                                "teau": ele.get("teau", ""),
                                "t": ele.get("t", ""),
                                "risqueorage": ele.get("risqueorage", ""),
                                "dirhouledegres": ele.get("dirhouledegres", ""),
                                "hauteurhoule": ele.get("hauteurhoule", ""),
                                "periodehoule": ele.get("periodehoule", ""),
                                "hauteurmerv": ele.get("hauteurmerv", ""),
                                "periodemerv": ele.get("periodemerv", ""),
                                "hauteurvague": ele.get("hauteurvague", "")

                                }
                clef = dateComplete
                dicoPrevis[clef] = detailPrevis
        elif (origine == "stormio") and (not self._error):
            j = 0
            dateCompletePrevious = self._dateCourante
            for maree in jsondata["data"][:6]:
                i = 0
                dateComplete = datetime.datetime.fromisoformat(maree["time"])
                detailMaree = {"coeff": maree.get("coef", ""), "hauteur": maree.get("height", ""),
                               "horaire": dateComplete.strftime("%H:%M"),
                               "etat": maree["type"], "nieme": i, "jour": j, "date": maree["time"],
                               "dateComplete": dateComplete.replace(tzinfo=None)}
                clef = "horaire_%s_%s" % (j, i)
                myMarees[clef] = detailMaree
                # print(clef, detailMaree)
                i += 1
                if (dateComplete != dateCompletePrevious):
                    j += 1
                dateCompletePrevious = dateComplete
            self._donnees = myMarees

            # for ele in jsondata["contenu"]["previs"]["detail"]:
            #     dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
            #     detailPrevis = {"forcevnds": ele.get("forcevnds", ""), "rafvnds": ele.get("rafvnds", ""),
            #                     "dirvdegres": ele.get("dirvdegres", ""),
            #                     "dateComplete": dateComplete.replace(tzinfo=None),
            #                     "nuagecouverture": ele.get("nuagecouverture", ""),
            #                     "precipitation": ele.get("precipitation", ""),
            #                     "teau": ele.get("teau", ""),
            #                     "t": ele.get("t", ""),
            #                     "risqueorage": ele.get("risqueorage", ""),
            #                     "dirhouledegres": ele.get("dirhouledegres", ""),
            #                     "hauteurhoule": ele.get("hauteurhoule", ""),
            #                     "periodehoule": ele.get("periodehoule", ""),
            #                     "hauteurmerv": ele.get("hauteurmerv", ""),
            #                     "periodemerv": ele.get("periodemerv", ""),
            #                     "hauteurvague": ele.get("hauteurvague", "")
            #
            #                     }
            #     clef = dateComplete
            #     dicoPrevis[clef] = detailPrevis
        self._donneesPrevis = dicoPrevis

    def getnomduport(self):
        return self._nomDuPort.split("©")[0].strip()

    def getcopyright(self):
        return "©SHOM"

    def getnomcompletduport(self):
        return self._nomDuPort

    def getdatecourante(self):
        return self._dateCourante
    def getmaxhours(self):
        return self._maxhours

    def gethttptimerequest(self):
        return self._httptimerequest

    def getinfo(self):
        return self._donnees

    def getprevis(self):
        return self._donneesPrevis

    def getError(self):
        return self._error

    def getErrorMessage(self):
        return self._errorMessage

    def getNextPluie(self):
        dateCourante = datetime.datetime.now()
        for x in self._donneesPrevis.keys():
            if self._donneesPrevis[x]["dateComplete"] > dateCourante:
                if self._donneesPrevis[x]["precipitation"] != 0:
                    return self._donneesPrevis[x]["dateComplete"], self._donneesPrevis[x]["precipitation"]
        return None, 0
