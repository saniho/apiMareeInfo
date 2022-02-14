def testPort():
  import json

  with open('../../Tests/json/SJM_20220214.json') as f:
    dataJson = json.load(f)
  import apiMareeInfo, sensorApiMaree

  _myMaree = apiMareeInfo.ApiMareeInfo()
  lat, lng = "46.7711", "-2.05306"
  lat, lng = "46.4967", "-1.79667"
  _myMaree.setport(lat, lng)
  #_myMaree.getinformationport( outfile = "file_20220214.json" )
  _myMaree.getinformationport( dataJson)
  print(_myMaree.getinfo())
  print(_myMaree.getnomduport())
  print(_myMaree.getdatecourante())
  print(_myMaree.getNextPluie())
  _sAM = sensorApiMaree.manageSensorState()
  _sAM.init(_myMaree )
  state, attributes = _sAM.getstatus()
  sensorApiMaree.logSensorState( attributes )

def testListePorts():
  import apiMareeInfo

  _myPort = apiMareeInfo.ListePorts()
  a = _myPort.getlisteport("olonne")
  print(a)

testPort()
#testListePorts()