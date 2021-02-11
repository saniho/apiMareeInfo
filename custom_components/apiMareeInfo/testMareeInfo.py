import apiMareeInfo, sensorApiMaree

_myMaree = apiMareeInfo.apiMareeInfo()
_myMaree.getInformationPort("124")

_sAM = sensorApiMaree.manageSensorState()
_sAM.init(_myMaree )
state, attributes = _sAM.getStatus()
print(state, attributes)
sensorApiMaree.logSensorState( attributes )
print(_myMaree.getInfo())
print(_myMaree.getNomDuPort())
print(_myMaree.getDateCourante())