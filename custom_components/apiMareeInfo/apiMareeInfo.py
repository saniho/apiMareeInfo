import logging
import datetime
import json
import aiohttp

_LOGGER = logging.getLogger(__name__)


class ListePorts:
    def __init__(self):
        # fonction init aucune action à réaliser
        pass

    async def getjson(self, url, session: aiohttp.ClientSession):
        response = None
        try:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as error:
            _LOGGER.error("Error getting json: %s", error)
            response = {"error": "UNKERROR_001"}
            return response

    async def getlisteport(self, nomport, session: aiohttp.ClientSession):
        url = (
            "https://ws.meteoconsult.fr/meteoconsultmarine/android/100/fr/v30/recherche.php?rech=%s&type=48"
            % (nomport)
        )

        retour = await self.getjson(url, session)
        return retour


class MeteoMarine:
    def __init__(self, lat, lng):
        self._url = (
            "https://ws.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v30/previsionsSpot.php?lat=%s&lon=%s"
            % (lat, lng)
        )
        pass

    async def getdata(self, session: aiohttp.ClientSession):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
        try:
            async with session.get(self._url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as error:
            _LOGGER.error("Error getting data from MeteoMarine: %s", error)
            return {"error": "UNKERROR_001"}


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

    async def getjson(self, origine, info=None, session=None):
        if origine == "MeteoMarine":
            mm = MeteoMarine(self._lat, self._lng)
            return await mm.getdata(session)

    def setport(self, lat, lng):
        self._lat = lat
        self._lng = lng

    def setmaxhours(self, maxhours):
        self._maxhours = maxhours

    async def getinformationport(
        self,
        jsondata=None,
        origine="MeteoMarine",
        info=None,
        session=None,
    ):
        if jsondata is None:
            jsondata = await self.getjson(origine, info, session)

        if origine == "MeteoMarine":
            if (
                not jsondata
                or "contenu" not in jsondata
                or len(jsondata["contenu"]["marees"]) == 0
            ):
                self._error = True
                self._errorMessage = "No tide data available from MeteoMarine"
            else:
                self._nomDuPort = jsondata["contenu"]["marees"][0]["lieu"]
                self._dateCourante = jsondata["contenu"]["marees"][0]["datetime"]
                self._error = False
        else:
            raise RuntimeError("Data Origin unknown")
        self._httptimerequest = datetime.datetime.now()

        myMarees = {}
        dicoPrevis = {}
        if (origine == "MeteoMarine") and (not self._error):
            j = 0
            for maree in jsondata["contenu"]["marees"][:6]:
                i = 0
                for ele in maree["etales"]:
                    dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                    detailMaree = {
                        "coeff": ele.get("coef", ""),
                        "hauteur": ele["hauteur"],
                        "horaire": dateComplete.strftime("%H:%M"),
                        "etat": ele["type_etale"],
                        "nieme": i,
                        "jour": j,
                        "date": ele["datetime"],
                        "dateComplete": dateComplete.replace(tzinfo=None),
                    }
                    clef = "horaire_%s_%s" % (j, i)
                    myMarees[clef] = detailMaree
                    i += 1
                j += 1
            self._donnees = myMarees

            for ele in jsondata["contenu"]["previs"]["detail"]:
                dateComplete = datetime.datetime.fromisoformat(ele["datetime"])
                detailPrevis = {
                    "forcevnds": ele.get("forcevnds", ""),
                    "rafvnds": ele.get("rafvnds", ""),
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
                    "hauteurvague": ele.get("hauteurvague", ""),
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

    def getmaxhours(self):
        return self._maxhours

    def getlat(self):
        return self._lat

    def getlng(self):
        return self._lng

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
                    return self._donneesPrevis[x]["dateComplete"], self._donneesPrevis[
                        x
                    ]["precipitation"]
        return None, 0

    def getTemperatureEau(self):
        dateCourante = datetime.datetime.now()
        for x in self._donneesPrevis.keys():
            if self._donneesPrevis[x]["dateComplete"] > dateCourante:
                return self._donneesPrevis[x]["dateComplete"], self._donneesPrevis[x][
                    "teau"
                ]
        return None, 0
