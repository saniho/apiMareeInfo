async def testPortMeteoMarine():
    import json

    with open('./file_20240314.json') as f:
        dataJson = json.load(f)
    dataJson = None
    from custom_components.apiMareeInfo import apiMareeInfo, sensorApiMaree

    _myMaree = apiMareeInfo.ApiMareeInfo()
    lat, lng = "46.7711", "-2.05306"
    # lat, lng = "46.4967", "-1.79667"
    # lat, lng = "46.009313818464726", "-1.1740585688883056"
    # lat, lng = "45.0015181", "-1.1999562"
    lat, lng = "46.7711", "-2.05306"
    _myMaree.setport(lat, lng)
    # await _myMaree.getinformationport(jsondata =dataJson)
    # await _myMaree.getinformationport(outfile="file_20240314.json")
    #await _myMaree.getinformationport()
    _myMaree.setmaxhours(6)
    # dataJson = None
    await _myMaree.getinformationport(dataJson)
    # print(_myMaree.getinfo())
    # print(_myMaree.getnomduport())
    # print(_myMaree.getdatecourante())
    # print(_myMaree.getNextPluie())
    _sAM = sensorApiMaree.manageSensorState()
    _sAM.init(_myMaree)
    state, attributes = _sAM.getStateNextMaree( "PM")
    state, attributes = _sAM.getStateNextMaree( "BM")
    print(state)
    print(attributes)
    state, attributes = _sAM.getstatus()
    # sensorApiMaree.logSensorState(attributes)
    state, attributes = _sAM.getstatusProchainePluie()
    # sensorApiMaree.logSensorState(attributes)


async def testPortStormGlass():

    import configparser

    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/maree.txt")
    mon_conteneur["MAREE"]["KEY"]
    import json

    with open('./tests/json/stormGlass.io/SJM_20221214.json', 'r') as f:
        dataJson = json.loads(f.read())
    dataJson = None
    from custom_components.apiMareeInfo import apiMareeInfo, sensorApiMaree

    _myMaree = apiMareeInfo.ApiMareeInfo()
    # lat, lng = "46.7711", "-2.05306"
    lat, lng = "46.4967", "-1.79667"
    _myMaree.setport(lat, lng)
    # await _myMaree.getinformationport( jsondata= dataJson, outfile = "file_20220726.json",
    #                             origine="stormio", info={'stormkey':thekey} )
    await _myMaree.getinformationport(jsondata=dataJson, outfile="file_20220726.json",
                                origine="MeteoMarine")

    # await _myMaree.getinformationport( outfile = "file_20220726.json", origine="stormio", info={'stormkey':thekey} )
    # print(_myMaree.getinfo())
    # print(_myMaree.getnomduport())
    # print(_myMaree.getdatecourante())
    # print(_myMaree.getNextPluie())
    _sAM = sensorApiMaree.manageSensorState()
    _sAM.init(_myMaree)
    state, attributes = _sAM.getstatus()
    # sensorApiMaree.logSensorState(attributes)
    state, attributes = _sAM.getstatusProchainePluie()
    # sensorApiMaree.logSensorState(attributes)


async def testListePorts():
    from custom_components.apiMareeInfo import apiMareeInfo

    _myPort = apiMareeInfo.ListePorts()
    a = await _myPort.getlisteport("Saint Gilles Croix")
    # a = await _myPort.getlisteport("Armel")
    print(a)


if __name__ == "__main__":
    import asyncio
    import sys

    # Fix asyncio on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    #asyncio.run(testPortMeteoMarine())
    # asyncio.run(testPortStormGlass())
    asyncio.run(testListePorts())
