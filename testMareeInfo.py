import apiMareeInfo
maree = apiMareeInfo.apiMareeInfo()
maree.getInformationPort("124")
print(maree.getInfo())
print(maree.getNomDuPort())
print(maree.getDateCourante())