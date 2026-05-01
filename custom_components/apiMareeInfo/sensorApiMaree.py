import datetime
import logging
from collections import defaultdict


class manageSensorState:
    def __init__(self):
        self._myPort = None
        self._LOGGER = None
        self.version = None

    def init(self, _myPort, _LOGGER=None, version=None):
        self._myPort = _myPort
        if _LOGGER is None:
            _LOGGER = logging.getLogger(__name__)
        self._LOGGER = _LOGGER
        self.version = version

    def getnextmaree(self, indice=1, maintenant=None):
        i = 1
        if maintenant is None:
            maintenant = datetime.datetime.now()

        sorted_marees = sorted(
            self._myPort.getinfo().values(), key=lambda x: x["dateComplete"]
        )

        for maree in sorted_marees:
            if maintenant < maree["dateComplete"]:
                if indice == i:
                    return maree
                i += 1
        return None

    def getstatus(self):
        status_counts = {}
        status_counts["version"] = self.version

        if self._myPort.getError():
            status_counts["message"] = self._myPort.getErrorMessage()
            return "unavailable", status_counts

        status_counts["nomPort"] = self._myPort.getnomduport()
        status_counts["idPort"] = self._myPort.getid()
        status_counts["Copyright"] = self._myPort.getcopyright()
        status_counts["dateCourante"] = self._myPort.getdatecourante()

        for info in self._myPort.getinfo().values():
            jour = info["jour"]
            nieme = info["nieme"]
            status_counts[f"horaire_{jour}_{nieme}"] = info["horaire"]
            status_counts[f"coeff_{jour}_{nieme}"] = info.get("coeff", "")
            status_counts[f"etat_{jour}_{nieme}"] = info["etat"]
            status_counts[f"hauteur_{jour}_{nieme}"] = info["hauteur"]
            status_counts[f"nb_maree_{jour}"] = (
                status_counts.get(f"nb_maree_{jour}", 0) + 1
            )

        for i in range(1, 3):
            pMaree = self.getnextmaree(i)
            if pMaree:
                status_counts[f"next_maree_{i}"] = pMaree["horaire"]
                status_counts[f"next_coeff_{i}"] = pMaree.get("coeff", "")
                status_counts[f"next_etat_{i}"] = pMaree["etat"]

        status_counts["timeLastCall"] = datetime.datetime.now()

        maxTime = datetime.datetime.now() + datetime.timedelta(
            hours=self._myPort.getmaxhours()
        )
        dicoPrevis = [
            previs
            for maDate, previs in self._myPort.getprevis().items()
            if datetime.datetime.now() <= maDate.replace(tzinfo=None) <= maxTime
        ]
        status_counts["prevision"] = dicoPrevis

        next_maree = self.getnextmaree(1)
        if next_maree:
            status_counts["message"] = (
                f"{next_maree['horaire']} ({next_maree['etat']}/{next_maree.get('coeff', '')})"
            )
            state = next_maree["horaire"]
        else:
            state = "unavailable"

        status_counts["last_update"] = datetime.datetime.now()
        status_counts["last_http_update"] = self._myPort.gethttptimerequest()

        return state, status_counts

    def getStateNextMaree(self, pmbm=""):
        status_counts = {}
        status_counts["version"] = self.version
        status_counts["last_update"] = datetime.datetime.now()
        status_counts["last_http_update"] = self._myPort.gethttptimerequest()

        next_maree = self.getnextmaree(1)
        if next_maree and next_maree["etat"] == pmbm:
            maree = next_maree
        else:
            maree = self.getnextmaree(2)

        if maree and maree["etat"] == pmbm:
            state = maree["horaire"]
            status_counts["coeff"] = maree.get("coeff", "")
        else:
            state = "unavailable"

        return state, status_counts

    def getstatusProchainePluie(self):
        status_counts = {}
        status_counts["version"] = self.version

        dateNextPluie, precipitation = self._myPort.getNextPluie()
        if dateNextPluie:
            dateNextPluieCh = dateNextPluie.strftime("%d/%m %H:%M")
            state = dateNextPluie
        else:
            dateNextPluieCh = ""
            state = "unavailable"

        status_counts["prochainePluie"] = dateNextPluieCh
        status_counts["precipitation"] = precipitation
        status_counts["message"] = f"{dateNextPluieCh} - {precipitation} mm"
        status_counts["attribution"] = "Data provided by Météo-France"
        status_counts["last_update"] = datetime.datetime.now()
        status_counts["last_http_update"] = self._myPort.gethttptimerequest()
        
        # Fallback for 1_hour_forecast to prevent JS errors
        _, forecast, _ = self._myPort.get_1h_forecast()
        status_counts["1_hour_forecast"] = forecast

        return state, status_counts

    def getstatusTemperatureEau(self):
        status_counts = {}
        status_counts["version"] = self.version

        dateTemperatureEau, teau = self._myPort.getTemperatureEau()
        if dateTemperatureEau:
            state = teau
        else:
            state = "unavailable"

        status_counts["dateTemperatureEau"] = (
            dateTemperatureEau.strftime("%d/%m %H:%M") if dateTemperatureEau else ""
        )
        status_counts["teau"] = teau
        status_counts["last_update"] = datetime.datetime.now()
        status_counts["last_http_update"] = self._myPort.gethttptimerequest()

        return state, status_counts

    def getstatusMeteoFrance(self):
        status_counts = {}
        status_counts["version"] = self.version

        forecast_time_ref, forecast, source = self._myPort.get_1h_forecast()
        
        # L'état est la prévision immédiate (0 min)
        state = forecast.get("0 min", "Temps sec")

        status_counts["forecast_time_ref"] = forecast_time_ref.isoformat()
        status_counts["1_hour_forecast"] = forecast
        status_counts["data_source"] = source
        status_counts["attribution"] = "Data provided by Météo-France"
        status_counts["last_update"] = datetime.datetime.now()
        status_counts["last_http_update"] = self._myPort.gethttptimerequest()

        return state, status_counts

    def getstatusRainChance(self):
        status_counts = {}
        status_counts["version"] = self.version
        status_counts["attribution"] = "Data provided by Météo-France"
        state = self._myPort.get_rain_chance()
        status_counts["last_update"] = datetime.datetime.now()
        return state, status_counts

    def getstatusCloudCover(self):
        status_counts = {}
        status_counts["version"] = self.version
        status_counts["attribution"] = "Data provided by Météo-France"
        state = self._myPort.get_cloud_cover()
        status_counts["last_update"] = datetime.datetime.now()
        return state, status_counts

    def getstatusWeatherAlert(self):
        status_counts = {}
        status_counts["version"] = self.version
        status_counts["attribution"] = "Data provided by Météo-France"
        state = self._myPort.get_weather_alert()
        status_counts["last_update"] = datetime.datetime.now()
        return state, status_counts
