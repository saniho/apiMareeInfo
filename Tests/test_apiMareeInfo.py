
import datetime

from custom_components.apiMareeInfo import apiMareeInfo, sensorApiMaree


def loadHtmlFile( filename ):
    dateHtml = open(filename).read()
    return dateHtml

def test_lectureFichier():
    dataHtml = loadHtmlFile("Tests/htmlpage/port.html")
    assert len(dataHtml) == 37142

def test_getinformation_port():
    dataHtml = loadHtmlFile("Tests/htmlpage/port.html")
    _myMaree = apiMareeInfo.apiMareeInfo()
    _myMaree.getInformationPort("124", dataHtml)

    _sAM = sensorApiMaree.manageSensorState()
    _sAM.init(_myMaree)
    assert _myMaree.getNomDuPort() == "Saint-Gilles-Croix-de-Vie"
    maintenant = datetime.datetime.strptime( "2021-02-11 22:14", "%Y-%m-%d %H:%M")
    assert _sAM.getNextMaree(1, maintenant)['horaire'] == "22:54"
    assert _sAM.getNextMaree(1, maintenant)['coeff'] == "88"
    assert _sAM.getNextMaree(1, maintenant)['hauteur'] == "0,86m"
    assert _sAM.getNextMaree(1, maintenant)['etat'] == "BM"
    assert _sAM.getNextMaree(1, maintenant)['dateComplete'] == datetime.datetime(2021, 2, 11, 22, 54)
