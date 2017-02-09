USER_ADMIN = 4
USER_MANAGER = 3
USER_EDITOR = 2
USER_VIEWER = 1
USER_NO_AUTH = -1

userTypeList = {"DataViewer":'1', "DataEditor":'2', "DataManager":'3', "Administrator":'4'}
userTypeListRev = {'1': "DataViewer", '2' : "DataEditor", '3':"DataManager", '4' : "Administrator"} 

def dateToPretty(date):
    if not date:
        return ""
    splitdate = date.split('-')
    splitdate.reverse()
    return '/'.join(splitdate)

def prettyToDate(date):
    if not date:
        return ""
    splitdate = date.split('/')
    splitdate.reverse()
    return '-'.join(splitdate)

try:
    import esky
    import sys
    eskyApp = esky.Esky(sys.executable)            
    imagesPath = eskyApp.get_abspath("images")
    isFrozen = True
except:
    imagesPath = "images"
    isFrozen = False

import os
splashFile = os.path.join(imagesPath,"logologin.png")

try:
    from appconfig import *
except BaseException, e:
    print e

CRF_SYNCH_TIME_INTERVAL = 15*60
ACTIVE_CRFS_TIME_INTERVAL = 15*60
DB_SYNCH_TIME_INTERVAL = 15*60
CONNECTION_CHECK_TIME_INTERVAL = 5*60
SOFTWARE_UPDATE_TIME_INTERVAL = 15*60
EVALUATION_TIME_INTERVAL = 15*60
READMISSION_TIME_INTERVAL = 5
BACKUP_TIME_INTERVAL = 60*60
SERVER_MESSAGES_TIME_INTERVAL = 60*60
SCRIPTS_CHECK_TIME_INTERVAL = 5*60

from psversion import PROSAFE_VERSION

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
        elif portname == 'port':
            PYRO_PORT = int(portnumber)
except:
    pass

def compareVersions(ver1, ver2):
    if ver1 == ver2:
        return 0 
    if len(ver1.split('.')) < 4:
        ver1 += '.0'
    if len(ver2.split('.')) < 4:
        ver2 += '.0'
    ver1 = [int(el) for el in ver1.split('.')]
    ver2 = [int(el) for el in ver2.split('.')]
    if ver1[0] > ver2[0] or (ver1[0] == ver2[0] and ver1[1] > ver2[1]) or (ver1[0] == ver2[0] and ver1[1] == ver2[1] and ver1[2] > ver2[2])  or (ver1[0] == ver2[0] and ver1[1] == ver2[1] and ver1[2] == ver2[2] and ver1[3] > ver2[3]):
        return 1
    return -1

