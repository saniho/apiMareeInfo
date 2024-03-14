def testPortMeteoMarine():
    import json

    with open('./tests/json/meteomarine/SJM_20220214.json') as f:
        dataJson = json.load(f)
    dataJson = None
    from custom_components.apiMareeInfo import apiMareeInfo, sensorApiMaree

    _myMaree = apiMareeInfo.ApiMareeInfo()
    lat, lng = "46.7711", "-2.05306"
    #lat, lng = "46.4967", "-1.79667"
    #lat, lng = "46.009313818464726", "-1.1740585688883056"
    #lat, lng = "45.0015181", "-1.1999562"
    lat, lng = "47.19382", "-2.16449"
    _myMaree.setport(lat, lng)
    _myMaree.getinformationport(outfile="file_20220726.json")
    _myMaree.setmaxhours(6)
    dataJson = None
    _myMaree.getinformationport(dataJson)
    # print(_myMaree.getinfo())
    # print(_myMaree.getnomduport())
    # print(_myMaree.getdatecourante())
    # print(_myMaree.getNextPluie())
    _sAM = sensorApiMaree.manageSensorState()
    _sAM.init(_myMaree)
    state, attributes = _sAM.getstatus()
    sensorApiMaree.logSensorState(attributes)
    state, attributes = _sAM.getstatusProchainePluie()
    sensorApiMaree.logSensorState(attributes)


def testPortStormGlass():

    import configparser

    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/maree.txt")
    thekey = token = mon_conteneur["MAREE"]["KEY"]
    import json

    with open('./tests/json/stormGlass.io/SJM_20221214.json', 'r') as f:
        dataJson = json.loads(f.read())
    dataJson = None
    from custom_components.apiMareeInfo import apiMareeInfo, sensorApiMaree

    _myMaree = apiMareeInfo.ApiMareeInfo()
    # lat, lng = "46.7711", "-2.05306"
    lat, lng = "46.4967", "-1.79667"
    _myMaree.setport(lat, lng)
    # _myMaree.getinformationport( jsondata= dataJson, outfile = "file_20220726.json",
    #                             origine="stormio", info={'stormkey':thekey} )
    _myMaree.getinformationport(jsondata=dataJson, outfile="file_20220726.json",
                                origine="MeteoMarine")

    # _myMaree.getinformationport( outfile = "file_20220726.json", origine="stormio", info={'stormkey':thekey} )
    # print(_myMaree.getinfo())
    # print(_myMaree.getnomduport())
    # print(_myMaree.getdatecourante())
    # print(_myMaree.getNextPluie())
    _sAM = sensorApiMaree.manageSensorState()
    _sAM.init(_myMaree)
    state, attributes = _sAM.getstatus()
    sensorApiMaree.logSensorState(attributes)
    state, attributes = _sAM.getstatusProchainePluie()
    sensorApiMaree.logSensorState(attributes)


def testListePorts():
    from custom_components.apiMareeInfo import apiMareeInfo

    _myPort = apiMareeInfo.ListePorts()
    # a = _myPort.getlisteport("olonne")
    a = _myPort.getlisteport("Brévin")
    print(a)


testPortMeteoMarine()
# testPortStormGlass()
#testListePorts()
