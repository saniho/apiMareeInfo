def testPort():
  import json

  with open('../../Tests/json/SJM.json') as f:
    data = json.load(f)
  import apiMareeInfo, sensorApiMaree

  _myMaree = apiMareeInfo.apiMareeInfo()
  lat, lng = "46.7711", "-2.05306"
  lat, lng = "46.4967", "-1.79667"
  _myMaree.setPort( lat, lng)
  _myMaree.getInformationPort()
  print(_myMaree.getInfo())
  print(_myMaree.getNomDuPort())
  print(_myMaree.getDateCourante())
  _sAM = sensorApiMaree.manageSensorState()
  _sAM.init(_myMaree )
  state, attributes = _sAM.getStatus()
  sensorApiMaree.logSensorState( attributes )

def testListePorts():
  import apiMareeInfo

  _myPort = apiMareeInfo.listePorts()
  a = _myPort.getListePort( "sables")
  print(a)

testPort()
#testListePorts()