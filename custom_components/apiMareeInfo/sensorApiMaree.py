import datetime
import logging
from collections import defaultdict

try:
    from .const import (
        __VERSION__,
        __name__,
    )

except ImportError:
    from const import (
        __VERSION__,
        __name__,
    )


class manageSensorState:
    def __init__(self):
        self._myPort = None
        self._LOGGER = None
        self.version = None
        pass

    def init(self, _myPort, _LOGGER=None, version=None):
        self._myPort = _myPort
        if (_LOGGER == None):
            _LOGGER = logging.getLogger(__name__)
        self._LOGGER = _LOGGER
        self.version = version

    def getnextmaree(self, indice=1, maintenant=None):
        i = 1
        if (maintenant == None):
            maintenant = datetime.datetime.now()
        prochainemaree = None
        for x in self._myPort.getinfo().keys():
            if (prochainemaree is None) and (maintenant < self._myPort.getinfo()[x]["dateComplete"]):
                if indice == i:
                    prochainemaree = self._myPort.getinfo()[x]
                else:
                    i += 1
        return prochainemaree

    def getstatus(self):
        state = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version

        self._LOGGER.info("tente un update  infoPort? ... %s" % (self._myPort))
        status_counts["version"] = __VERSION__
        for n in range(2):
            status_counts["horaire_%s_3" % n] = ""
            status_counts["coeff_%s_3" % n] = ""
            status_counts["etat_%s_3" % n] = ""
            status_counts["hauteur_%s_3" % n] = ""

        # probleme mauvaise variable
        status_counts["nomPort"] = self._myPort.getnomduport()
        status_counts["Copyright"] = self._myPort.getcopyright()
        status_counts["dateCourante"] = self._myPort.getdatecourante()
        nieme_horaire = 0
        for horaireMaree in self._myPort.getinfo().keys():
            info = self._myPort.getinfo()[horaireMaree]
            nieme = info["nieme"]
            jour = info["jour"]
            status_counts["horaire_%s_%s" % (jour, nieme)] = "%s" % (info['horaire'])
            status_counts["coeff_%s_%s" % (jour, nieme)] = "%s" % (info['coeff'])
            status_counts["etat_%s_%s" % (jour, nieme)] = "%s" % (info['etat'])
            status_counts["hauteur_%s_%s" % (jour, nieme)] = "%s" % (info['hauteur'])
        # pour avoir les 2 prochaines marées
        for x in range(2):
            i = x + 1
            status_counts["next_maree_%s" % i] = "%s" % self.getnextmaree(i)["horaire"]
            status_counts["next_coeff_%s" % i] = "%s" % self.getnextmaree(i)["coeff"]
            status_counts["next_etat_%s" % i] = "%s" % self.getnextmaree(i)["etat"]
        status_counts["timeLastCall"] = datetime.datetime.now()

        dicoPrevis = []
        for maDate in self._myPort.getprevis().keys():
            if (maDate.replace(tzinfo=None) >= datetime.datetime.now()):
                dico = {}
                dico["datetime"] = maDate
                for clefPrevis in self._myPort.getprevis()[maDate].keys():
                    dico[clefPrevis] = self._myPort.getprevis()[maDate][clefPrevis]
                dicoPrevis.append(dico)
        status_counts["prevision"] = dicoPrevis
        self._attributes = status_counts
        self._state = self.getnextmaree()["horaire"]
        return self._state, self._attributes


def logSensorState(status_counts):
    for x in status_counts.keys():
        print(" %s : %s" % (x, status_counts[x]))
