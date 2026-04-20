import logging
import datetime
import json
import aiohttp

_LOGGER = logging.getLogger(__name__)


class ListePorts:
    def __init__(self):
        pass

    async def getjson(self, url, session=None, params=None):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "fr,en-US;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        }
        
        async def _fetch(s):
            try:
                async with s.get(url, params=params, headers=headers, timeout=30, ssl=False) as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
            except aiohttp.ClientError as error:
                _LOGGER.error("Error getting json from %s: %s", url, error)
                return {"error": "UNKERROR_001"}

        if session:
            return await _fetch(session)
        else:
            async with aiohttp.ClientSession() as local_session:
                return await _fetch(local_session)

    async def getlisteport(self, nomport, session=None):
        url = "https://ws.meteoconsult.fr/meteoconsultmarine/android/100/fr/v30/recherche.php"
        params = {"rech": nomport, "type": "48"}
        retour = await self.getjson(url, session, params=params)
        return retour


class MeteoMarine:
    def __init__(self, lat, lng):
        self._url = (
            "https://ws.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v30/previsionsSpot.php?lat=%s&lon=%s"
            % (lat, lng)
        )

    async def getdata(self, session=None):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "fr,en-US;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        }

        async def _fetch(s):
            try:
                async with s.get(self._url, headers=headers, timeout=30, ssl=False) as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
            except aiohttp.ClientError as error:
                _LOGGER.error("Error getting data from MeteoMarine (%s): %s", self._url, error)
                return {"error": "UNKERROR_001"}

        if session:
            return await _fetch(session)
        else:
            async with aiohttp.ClientSession() as local_session:
                return await _fetch(local_session)


class stormIO:
    def __init__(self, lat, lng, storm_key):
        self._lat = lat
        self._lng = lng
        self._storm_key = storm_key

    async def getdata(self, session=None):
        import datetime
        now = datetime.datetime.now()
        nowJ2 = now + datetime.timedelta(days=2)
        self._deb = now.strftime("%Y-%m-%d %H:%M:%S+00:00")
        self._fin = nowJ2.strftime("%Y-%m-%d %H:%M:%S+00:00")
        
        params={
                'lat': self._lat,
                'lng': self._lng,
                'start': self._deb, 'end': self._fin,
            }
        headers={
                'Authorization': self._storm_key
            }
        url = 'https://api.stormglass.io/v2/tide/extremes/point'

        async def _fetch(s):
            try:
                async with s.get(url, params=params, headers=headers, timeout=600) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as error:
                _LOGGER.error("Error getting data from StormIO: %s", error)
                return {"errors": {"key": f"Communication error: {error}"}}

        if session:
            return await _fetch(session)
        else:
            async with aiohttp.ClientSession() as local_session:
                return await _fetch(local_session)


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
        self._httptimerequest = datetime.datetime.now()
        pass

    async def getjson(self, origine, info=None, session=None):
        if origine == "MeteoMarine":
            mm = MeteoMarine(self._lat, self._lng)
            return await mm.getdata(session)
        elif origine == "stormio":
            mm = stormIO(self._lat, self._lng, info["stormkey"])
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
                _LOGGER.warning("MeteoMarine data error for lat=%s, lng=%s. Response: %s", self._lat, self._lng, str(jsondata)[:200])
            else:
                self._nomDuPort = jsondata["contenu"]["marees"][0]["lieu"]
                self._dateCourante = jsondata["contenu"]["marees"][0]["datetime"]
                self._error = False
        elif origine == "stormio":
            if not jsondata or "errors" in jsondata:
                self._nomDuPort = ""
                self._errorMessage = jsondata.get("errors", {}).get("key", "Unknown error from StormIO")
                self._error = True
            elif "station" in jsondata.get("meta", {}):
                self._nomDuPort = jsondata["meta"]["station"]['name']
                self._errorMessage = ""
                self._error = False
            self._dateCourante = datetime.datetime.now()
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
        elif (origine == "stormio") and (not self._error):
            j = 0
            dateCompletePrevious = self._dateCourante
            for maree in jsondata["data"][:6]:
                i = 0
                dateComplete = datetime.datetime.fromisoformat(maree["time"])
                detailMaree = {
                    "coeff": maree.get("coef", ""),
                    "hauteur": maree.get("height", ""),
                    "horaire": dateComplete.strftime("%H:%M"),
                    "etat": maree["type"],
                    "nieme": i,
                    "jour": j,
                    "date": maree["time"],
                    "dateComplete": dateComplete.replace(tzinfo=None),
                }
                clef = "horaire_%s_%s" % (j, i)
                myMarees[clef] = detailMaree
                i += 1
                if (dateComplete.date() != dateCompletePrevious.date()):
                    j += 1
                dateCompletePrevious = dateComplete
            self._donnees = myMarees

        self._donneesPrevis = dicoPrevis

    def getnomduport(self):
        if self._nomDuPort:
            return self._nomDuPort.split("©")[0].strip()
        return "Unknown"

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
