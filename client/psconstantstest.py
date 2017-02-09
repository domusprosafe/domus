
USER_ADMIN = 4
USER_MANAGER = 3
USER_EDITOR = 2
USER_VIEWER = 1
USER_NO_AUTH = -1

#attribute constants
#!! needed attributes

#firstnameAttr = '1.firstName.firstName'
#lastnameAttr = '1.lastName.lastName'
#sexAttr = '1.gender.value'
#dobdateAttr = '1.birthDate.birthDate'
#admdateAttr = '1.icuAdmDate.icuAdmDate'
#disdateAttr = '1.icuDisDate.value'
#disdateHAttr = '1.hospDisDate.value'
#meddecordAttr = '1.ehrId.value'
#
#baseAttrList = []
##baseAttrListNames = [_("First name"),  _('Last name'),  _('Sex'),  _('Admission date'),  _('Discharge date'),  _('Date of birth')]
#
#for var in [firstnameAttr,  lastnameAttr, sexAttr,  admdateAttr,  disdateAttr, dobdateAttr]:
#    pieces = var.split('.')
#    baseAttrList.append ('%s.%s' % (pieces[1],  pieces[2]))
#
##useful functions
#age = "|%s|[0], |%s|[0]" % (admdateAttr, dobdateAttr )

userTypeList = {"DataViewer":'1', "DataEditor":'2', "DataManager":'3', "Administrator":'4'}
userTypeListRev = {'1': "DataViewer", '2' : "DataEditor", '3':"DataManager", '4' : "Administrator"} 

firstnameAttr = 'core.firstName.firstName'
lastnameAttr = 'core.lastName.lastName'
sexAttr = 'core.gender.value'
dobdateAttr = 'core.birthDate.birthDate'
admdateAttr = 'core.icuAdmDate.icuAdmDate'
disdateAttr = 'core.icuDisDate.value'
disdateHAttr = 'core.hospDisDate.value'
meddecordAttr = 'core.ehrId.value'

attrDataTypes = {firstnameAttr:'string', lastnameAttr:'string', sexAttr:'codingset', dobdateAttr:'datetime', admdateAttr:'datetime', disdateAttr:'datetime', disdateHAttr:'datetime', meddecordAttr:'string'}
attrCodingSets = {firstnameAttr:None, lastnameAttr:None, sexAttr:'core.sexCodification', dobdateAttr:None, admdateAttr:None, disdateAttr:None, disdateHAttr:None, meddecordAttr:None}

basedataAttributeDict = {'firstname':firstnameAttr, 'lastname':lastnameAttr, 'birth':dobdateAttr, 'admissionDate':admdateAttr}

baseAttrList = []

for var in [firstnameAttr,  lastnameAttr, sexAttr, admdateAttr, disdateAttr, dobdateAttr]:
    pieces = var.split('.')
    baseAttrList.append ('%s.%s' % (pieces[1],  pieces[2]))

sexCodingSetValues = {'core.sexCodification.Male':'@@@5@@@', 'core.sexCodification.Female':'@@@6@@@'}

#useful functions
age = "|%s|[0], |%s|[0]" % (admdateAttr, dobdateAttr)


#http urls
#these are the various url used by master and clients
DB_SYNCH_URL = 'http://epidev3/prosafeserver/synch'
DB_MERGE_URL = 'http://epidev3/prosafeserver/merge'
CONNECTION_CHECK_URL = 'http://epidev3/prosafeserver/test'
DIFFPATCH_URL = "http://epidev3/prosafeserver/getPatches"
ESKY_FILES_DOWNLOAD_URL = "http://epidev3/prosafedownloads/"

CHECK_ACTIVATION_CODE_URL = 'http://epidev3/prosafeserver/checkActivationCode'
CHECK_PETALS_URL = 'http://epidev3/prosafeserver/checkPetals'
SERVER_QUERY_URL = "http://epidev3/prosafeserver/serverQuery"
SECONDARY_PASSWORD_URL = "http://epidev3/prosafeserver/secondaryPassword"

#DB_SYNCH_URL = 'http://localhost:8080/synch'
#DB_MERGE_URL = 'http://localhost:8080/merge'
#CONNECTION_CHECK_URL = 'http://localhost:8080/test'
#DIFFPATCH_URL = "http://localhost:8080/getPatches"
#ESKY_FILES_DOWNLOAD_URL = "http://localhost:8080/prosafedownloads/"
#
#CHECK_ACTIVATION_CODE_URL = 'http://localhost:8080/checkActivationCode'
#CHECK_PETALS_URL = 'http://localhost:8080/checkPetals'
#SERVER_QUERY_URL = "http://localhost:8080/serverQuery"
#SECONDARY_PASSWORD_URL = "http://localhost:8080/secondaryPassword"


#CHECK_ACTIVATION_CODE_URL = 'http://localhost:8080/checkActivationCode'
#CHECK_PETALS_URL = 'http://localhost:8080/checkPetalsTest'

CRF_SYNCH_TIME_INTERVAL = 15*60
ACTIVE_CRFS_TIME_INTERVAL = 15*60
DB_SYNCH_TIME_INTERVAL = 1*60
CONNECTION_CHECK_TIME_INTERVAL = 5*60
SOFTWARE_UPDATE_TIME_INTERVAL = 15*60
EVALUATION_TIME_INTERVAL = 15*60

import os
from psversion import PROSAFE_VERSION

try:
    import esky
    import sys
    eskyApp = esky.Esky(sys.executable)            
    imagesPath = eskyApp.get_abspath("images")
    isFrozen = True
        
except:
    imagesPath = "images"
    isFrozen = False

def abspath(path='./', verpath=False):
    if not isFrozen:
        returnpath = os.path.join(os.getcwd(),path)
    else:
        if not verpath:
            wrapperpath = os.path.join(eskyApp.get_abspath(''), '../')
            returnpath = os.path.join(wrapperpath,path)
        else:
            returnpath = os.path.join(eskyApp.get_abspath(''),path)
    returnpath = os.path.abspath(returnpath) 
    return returnpath

PYRO_PORT = 7766
PYRO_NS_PORT = 9090
PYRO_NS_BC_PORT = 9090
try:
    portFile = open(abspath('port.txt'))
    portlines = portFile.readlines()
    portFile.close()
    for portline in portlines:
        splitline = portline.split()
        if len(splitline) != 2:
            continue
        portname, portnumber = splitline
        print "%s: %s" % (portname, portnumber)
        if portname == 'ns_port':
            PYRO_NS_PORT = int(portnumber)
            PYRO_NS_BC_PORT = int(portnumber)
except:
    pass

def compareVersions(ver1, ver2):
    if ver1 == ver2:
        return 0 
    ver1 = [int(el) for el in ver1.split('.')]
    ver2 = [int(el) for el in ver2.split('.')]
    if ver1[0] > ver2[0] or (ver1[0] == ver2[0] and ver1[1] > ver2[1]) or (ver1[0] == ver2[0] and ver1[1] == ver2[1] and ver1[2] > ver2[2]):
        return 1
    return -1

