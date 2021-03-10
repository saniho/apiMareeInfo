def testPort():
  import json

  with open('../../Tests/json/SJM.json') as f:
    data = json.load(f)
  import ApiMareeInfo, sensorApiMaree

  _myMaree = ApiMareeInfo.ApiMareeInfo()
  lat, lng = "46.7711", "-2.05306"
  lat, lng = "46.4967", "-1.79667"
  _myMaree.setport(lat, lng)
  # _myMaree.getInformationPort( outfile = "file.json" )
  _myMaree.getinformationport()
  print(_myMaree.getinfo())
  print(_myMaree.getnomduport())
  print(_myMaree.getdatecourante())
  _sAM = sensorApiMaree.manageSensorState()
  _sAM.init(_myMaree )
  state, attributes = _sAM.getstatus()
  sensorApiMaree.logSensorState( attributes )

def testListePorts():
  import ApiMareeInfo

  _myPort = ApiMareeInfo.ListePorts()
  a = _myPort.getlisteport("olonne")
  print(a)

testPort()
testListePorts()