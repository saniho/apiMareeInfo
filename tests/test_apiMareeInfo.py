import datetime

from custom_components.apiMareeInfo import apiMareeInfo, sensorApiMaree
import json


def test_getinformation_port():
    with open('./json/SJM.json') as f:
        dataJson = json.load(f)
    _myMaree = apiMareeInfo.ApiMareeInfo()
    lat, lng = "1", "1"
    _myMaree.setport(lat, lng)
    _myMaree.getinformationport(dataJson)

    _sam = sensorApiMaree.manageSensorState()
    _sam.init(_myMaree)
    assert _myMaree.getnomduport() == "Saint-Gilles-Croix-de-Vie"
    maintenant = datetime.datetime.strptime("2021-02-19 04:14", "%Y-%m-%d %H:%M")
    assert _sam.getnextmaree(1, maintenant)['horaire'] == "08:59"
    assert _sam.getnextmaree(1, maintenant)['coeff'] == 45
    assert _sam.getnextmaree(1, maintenant)['hauteur'] == 4.15
    assert _sam.getnextmaree(1, maintenant)['etat'] == "PM"
    assert _sam.getnextmaree(1, maintenant)['dateComplete'] == datetime.datetime(2021, 2, 19, 8, 59)
