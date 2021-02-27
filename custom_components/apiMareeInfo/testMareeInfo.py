"""import apiMareeInfo, sensorApiMaree

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

"""


import json

with open('../../Tests/json/SJM.json') as f:
  data = json.load(f)
import apiMareeInfo, sensorApiMaree

_myMaree = apiMareeInfo.apiMareeInfo()
url = "http://webservices.meteoconsult.fr/meteoconsultmarine/androidtab/115/fr/v20/previsionsSpot.php?lat=46.7711&lon=-2.05306"

_myMaree.setPort( "46.7711", "-2.05306")
_myMaree.getInformationPort()

print(_myMaree.getInfo())
print(_myMaree.getNomDuPort())
print(_myMaree.getDateCourante())

_sAM = sensorApiMaree.manageSensorState()
_sAM.init(_myMaree )
state, attributes = _sAM.getStatus()
#print(state, attributes)
sensorApiMaree.logSensorState( attributes )

#print(data)
#print(data["contenu"]["marees"])
#for maree in data["contenu"]["marees"]:
#    print(maree)
#maree = data["contenu"]["marees"][0]
#for ele in maree["etales"]:
#    print(ele["datetime"])
#    print(ele["hauteur"])
#    print(ele["type_etale"])
#    print(ele.get("coef",""))
#print(maree.keys())