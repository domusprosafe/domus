import psconstants as psc
import sys
from xml.etree import ElementTree as etree
import datetime
import re
import csv 
import wx
from rdflib.plugins import memory
import rdflib.plugins.memory
import rdflib.plugins.serializers.turtle

from rdflib import *
from rdflib.plugins import *
from rdflib.plugins.parsers import notation3
from rdflib.plugins.parsers import *
from dataconfiguration import DataConfiguration
from rdfextras import *
from rdfextras.sparql import *
import rdfextras.sparql.query
import rdfextras.sparql.processor
from datasession import DataSession
from psevaluator import PSEvaluator
import psevaluator

import notificationcenter

from blowfish import Blowfish

import random
import string
import os
import zipfile

import Pyro.core
import Pyro.errors
import time
from threading import Thread

import base64

import shutil

from filemanager import md5_for_file

from psversion import PROSAFE_VERSION
import ConfigParser
from pslogging import PsLogger
from dbmigrator import DBMigrator 

import timesleep
from timesleep import TimeSleep
import socket

from psconstants import abspath

from appdatamanager import AppdataManager

from psdescriptivetable import DescriptiveTableCreator
from psrdfmanager import PSRDFManager
sys.path.append('./utils')
import logutils

import pprint

class WrapperCallable(object):

    def __init__(self, proxy, name):
        self.proxy = proxy
        self.name = name

    def __call__(self, *args, **kwargs):
        try:
            return getattr(self.proxy.pyroProxy,self.name)(*args,**kwargs)
        except Pyro.errors.ConnectionClosedError:
            print 'lost!'
            notificationcenter.notificationCenter.postNotification("PyroProxyShouldReconnect",self)
            print 'reconnect'
            if not self.proxy.reconnected:
                return None
            return getattr(self.proxy.pyroProxy,self.name)(*args,**kwargs)


class PyroProxyWrapper(object):

    def __init__(self, uri):

        self.uri = None
        self.pyroProxy = None
        self.getProxyForURI(uri)
        notificationcenter.notificationCenter.addObserver(self,self.reconnect,"PyroProxyShouldReconnect")

    def getProxyForURI(self, uri):
        self.uri = uri
        self.reconnected = False
        self.pyroProxy = Pyro.core.getProxyForURI(uri)

    def reconnect(self, notifyingObject, userData=None):
        print 'trying to reconnect'
        counter = 0
        while counter < 180:
            if not TimeSleep(1):
                break
            try:
                self.getProxyForURI(self.uri)
                self.reconnectd = True
                return True
            except:
                counter += 1
                continue
        self.reconnected = False
        return False

    def __getattr__(self, name):
        return WrapperCallable(self,name)


class BulletinClient(object):

    def __init__(self, mainLogic):
        self.mainLogic = mainLogic
        self.processedMessages = []
        self.cleanupInterval = 10
        self.lastCleanupTime = None
        self.bulletinManager = None
        self.clientKey = None
        self.pollingThread = None

    def setBulletinManager(self, bulletinManager, staticClientKey=None):
        self.bulletinManager = bulletinManager
        if staticClientKey != None:
            self.clientKey = staticClientKey
            self.bulletinManager.registerStaticClientKey(self.clientKey)
        else:
            self.clientKey = self.bulletinManager.getNewClientKey()

    def getClientKeyForEntry(self, entry):
        return entry[0]

    def getMessageTimeForEntry(self, entry):
        return entry[1]
        
    def getBulletinManagerServerMessages(self):
        return self.bulletinManager.getServerMessages()
        
    def setBulletinManagerServerMessages(self, messages):
        self.bulletinManager.setServerMessages(messages)
        
    def removeBulletinManagerServerMessage(self, title, text, priority, type=None, repeatable=None, notificationTime=None, admissionReference=None, notificationExpireDate=None):
        if notificationTime:
            self.mainLogic.beginCriticalSection()
            notifications = self.mainLogic.getNotificationsFromStore()
            
            for notificationId in notifications.keys():
                notification = eval(notifications[notificationId][0]['value'])
                if notification['admissionReference'] == admissionReference and notification['title'] == title and notification['text'] == text:
                    self.mainLogic.bulletinManager.removeServerMessage(title, text, priority, type, repeatable, notificationTime, admissionReference, notificationExpireDate)
                    self.mainLogic.moveNotificationFromStoreToHStore(notificationId)
            self.mainLogic.endCriticalSection()
        
    def addBulletinManagerServerMessage(self, title, text, priority, type=None, repeatable=None, notificationTime=None, admissionReference=None, notificationExpireDate=None):
        if type == 'global' and notificationTime != datetime.datetime.now():
            #should add only if not present in stored notification
            self.mainLogic.beginCriticalSection()
            self.mainLogic.jsonStore.create({'notification': True, 'value':repr({'title':title, 'text':text, 'priority':priority, 'shown':False, 'type':'global', 'repeatable':repeatable, 'notificationTime':notificationTime, 'admissionReference':admissionReference, 'notificationExpireDate':notificationExpireDate})})
            self.mainLogic.endCriticalSection()
        else:
            self.bulletinManager.addServerMessage(title, text, priority, type, repeatable, notificationTime, admissionReference, notificationExpireDate)
            
    def cleanup(self, cleanupTime):
        self.processedMessages = [entry for entry in self.processedMessages if (cleanupTime - self.getMessageTimeForEntry(entry)).seconds < self.bulletinManager.getCleanupInterval()]
        self.lastCleanupTime = cleanupTime

    def pollBulletin(self, pollingInterval):
        self.pollingActive = True
        while True and self.pollingActive:
            bulletin = self.bulletinManager.poll(self.clientKey,PROSAFE_VERSION)
            if bulletin == None:
                if self.bulletinManager.getMigrationFlag():
                    self.mainLogic.masterIsMigrating = True
                else:
                    self.mainLogic.masterIsMigrating = False
                self.mainLogic.notificationCenter.postNotification('SoftwareUpdated',self)
                break
            for entry in bulletin:
                if entry in self.processedMessages:
                    continue
                try:
                    if self.getClientKeyForEntry(entry) != self.clientKey:
                        self.mainLogic.notificationCenter.postNotification(bulletin[entry]['name'],self,bulletin[entry].get('userInfo',None))
                    self.processedMessages.append(entry)
                except:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], 'Could not forward notification from bulletin ' + entry + ' ' + bulletin[entry])
                    print 'Could not forward notification from bulletin ' + entry + ' ' + bulletin[entry]
                    pass
            currentTime = datetime.datetime.now()
            if not self.lastCleanupTime or (currentTime-self.lastCleanupTime).seconds > self.bulletinManager.getCleanupInterval():
                self.cleanup(currentTime)
            if not TimeSleep(pollingInterval):
                break

    def startPollingLoop(self, pollingInterval = 1.0):
        if self.pollingThread:
            return
        self.pollingThread = Thread(target=self.pollBulletin,args=(pollingInterval,))
        self.pollingThread.daemon = True
        self.pollingThread.start()

    def terminatePollingLoop(self):
        self.pollingActive = False

    def postOnBulletin(self, message):
        result = self.bulletinManager.post(self.clientKey,message)
        return result

    def postNotificationOnBulletin(self, name, userInfo=None):
        message = {'name':name, 'userInfo':userInfo}
        return self.postOnBulletin(message)


class FileClient(object):

    def __init__(self):
        pass

    def setFileManager(self, fileManager):
        self.fileManager = fileManager

    def getFileNamesInPath(self, path, extension=None, relativeTo=None):
        return self.fileManager.getFileNamesInPath(path,extension,relativeTo)

    def getFileNamesInPathWithMD5(self, path, extension=None, relativeTo=None):
        return self.fileManager.getFileNamesInPathWithMD5(path,extension,relativeTo)

    def getFileContents(self, path, filename, relativeTo=None):
        """filepath = os.path.join(path, filename)
        if not os.path.exists(filepath):
            return None"""
        return self.fileManager.getFileContents(path,filename,relativeTo)

    def putFileContents(self, path, filename, contents, relativeTo=None):
        return self.fileManager.putFileContents(path,filename,contents,relativeTo)

    def getFile(self, path, filename, targetPath, targetFileName, relativeTo=None):
        contents = self.getFileContents(path,filename,relativeTo)
        if contents == None:
            return
        filepath = os.path.join(targetPath,targetFileName)
        f = open(filepath,'wb')
        f.write(contents)
        f.close()

    def putFile(self, path, filename, targetPath, targetFileName, relativeTo=None):
        filepath = os.path.join(path,filename)
        #if not os.path.exists(filepath):
        #    return None
        f = open(filepath,'rb')
        contents = f.read()
        f.close()
        self.putFileContents(targetPath,targetFileName,contents,relativeTo)

    def zipFile(self, path, filename, relativeTo=None):
        self.fileManager.zipFile(path,filename,relativeTo)


class MainLogic(object):

    def __init__(self, flags):
        self.macAddresses = self.getMacAddresses(sixHexadecimalsMac=True)
        self.macAddress = None
        self.currentNewUUID = None
        self.shouldAnonymizeData = False
        if self.macAddresses:
            self.macAddress = self.macAddresses[0]
        else:
            self.macAddress = '00:00:00:00:00'
        self.quickCompilationMode = ''
        self.ipAddresses = socket.gethostbyname_ex(socket.gethostname())[2]
        self.masterIPAddresses = []

        self.jsonStore = None
        self.changedAttributes = {}
        self.confirmResult = {}
        self.translationMode = False
        
        self.dataPath = abspath('data')
        
        self.flags = flags

        self.testing = flags.get('testing',False)
        self.localhost = flags.get('localhost',False)
        self.nosynch = flags.get('nosynch',False)
        self.asclient = flags.get('asclient',False)
        self.nolanguage = flags.get('nolanguage',False)
        self.staticClientKey = flags.get('staticclientkey',None)
        self.notificationCenter = flags.get('notificationcenter',None)

        self.publicEncryptionKey = 'custom_encryption_key'
        self.masterFileEncryptionKey = 'custom_encryption_key'
        self.masterFileName = abspath('master.cfg')

        ###
        #self.migrateIfNeeded()
        ###
        self.logsPath = abspath('logs')
        if not os.path.exists(self.logsPath):
            os.mkdir(self.logsPath)
            
        self.scriptPath = abspath('scriptlist')
        if not os.path.exists(self.scriptPath):
            os.mkdir(self.scriptPath)
        self.scriptList = self.getUpdatedScriptList()
        sys.path.append('./scriptlist')
        self.configDirectory = abspath('config')
        if not os.path.exists(self.configDirectory):
            os.mkdir(self.configDirectory)

        self.dischargeLettersDirectory = abspath('dletters')
        if not os.path.exists(self.dischargeLettersDirectory):
            os.mkdir(self.dischargeLettersDirectory)
            
        self.xlsModelsDirectory = abspath('xlsmodels')
        if not os.path.exists(self.xlsModelsDirectory):
            os.mkdir(self.xlsModelsDirectory)
            
        self.givitiMapperDirectory = abspath('GivitiMapper')
        if not os.path.exists(self.givitiMapperDirectory):
            os.mkdir(self.givitiMapperDirectory)
        
        self.dischargeLetterFolder = ''
        self.dischargeLetterModelFolder = ''
        self.dischargeLetterMasterModelFolder = ''

        self.dataBackupDirectory = abspath('databkp')
        if not os.path.exists(self.dataBackupDirectory):
            os.mkdir(self.dataBackupDirectory)

        self.currentUpdateDirectory = abspath('currentupdate')
        if not os.path.exists(self.currentUpdateDirectory):
            os.mkdir(self.currentUpdateDirectory)
        self.removeOlderUpdates()
        if flags.get('createmasterfile',False):
            self.createMasterFile()
        if self.notificationCenter == None:
            self.notificationCenter = notificationcenter.notificationCenter

        self.fileClient = FileClient()
        self.bulletinClient = BulletinClient(self)
        self.masterIsMigrating = False
        self.isMaster = False
        self.connectedToMaster = False
        self.retrievingSoftwareUpdate = False

        self.connectingToMasterAsMaster = False
        self.connectingToOtherMasterAsMaster = False
        
        try:
            self.connectToMasterAndStartServices()
            self.connectedToMaster = True
        except BaseException, e:
            self.connectedToMaster = False
            print e
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass

        if not self.nolanguage:
            global _
            _ = lambda translationString: self.translateString(translationString)
 
        if self.connectingToOtherMasterAsMaster:
            print 'connecting to other master as master'
            return
        
        self.connectingToMasterAsMaster = True
        if not self.connectedToMaster:
            self.attemptBecomeMaster()

        self.dataSession = None

        self.username = None
        self.userType = psc.USER_NO_AUTH;
        #self.passwordExpiryDate = loginResult['passwordExpiryDate']
        
        self.langStrings = dict()
        
        self.gridData = []
        self.filters = []
        self.quickFilters = dict()
        self.initializeQuickFilters()
        self.initializeFilters()
        #TODO: REMOVE
        #self.currentYearFilterActive = True        

        self.encryptionKey = None
        self.userLanguage = None
        self.typedEvaluator = True

        self.criticalSectionCount = 0
        self.unsavedStatus = False
        self.objectCodesOnLoad = set()

        self.languages = dict()
        self.crfData = DataConfiguration()    
        self.interfacesXML = dict()
        self.pagesXML = dict()
        self.pageHierarchy = dict()
        self.pageHierarchyExpanded = dict()
        self.quickCompilationPages = dict()
        self.crfFileDict = dict()
        self.customizationDict = dict()
        self.indexedKeys = set()
        self.storedCrfVersions = dict()
        self.crfPetalStatus = dict()
        self.serverMessages = None
        self.clientMessages = None
        self.evaluator = PSEvaluator(self)
        self.evaluator.typedEvaluator = self.typedEvaluator
            
    def disposeJsonStore(self):
        print 'disposing official db connection, setting master as if its migrating'
        self.bulletinManager.setMigrationFlag(True)
        self.jsonStore.dispose()
        
    def connectJsonStore(self):
        print 'reconnecting to official db connection, unsetting master as if its migrating'
        self.bulletinManager.setMigrationFlag(False)
        self.jsonStore.connect()
        
    def getUpdatedScriptList(self):
        return os.listdir(self.scriptPath)
        
    #NOTIFICATION MANAGEMENT
    
    def getNotificationsFromStore(self):
        self.beginCriticalSection()
        notificationIds = self.jsonStore.search_ids({'notification': True})
        positions = []
        positions.append('value')
        values = self.jsonStore.load_value_list(notificationIds,positions)
        self.endCriticalSection()
        return values 
    
    def updateServerMessages(self):
        #adding stored messages
        storedMessages = self.getNotificationsFromStore()
        for notificationId in storedMessages:
            value = storedMessages[notificationId]
            if value:
                value = value[0]
                value = eval(value['value'])
                if 'notificationExpireDate' in value and value['notificationExpireDate'] is not None and value['notificationExpireDate'] < datetime.datetime.now():
                    self.bulletinManager.removeServerMessage(value['title'], value['text'], value['priority'], value['type'], value['repeatable'], value['notificationTime'], value['admissionReference'], value['notificationExpireDate'])
                    self.moveNotificationFromStoreToHStore(notificationId)
                elif value['notificationTime'] and value['notificationTime'] <= datetime.datetime.now():
                    self.bulletinManager.addServerMessage(value['title'], value['text'], value['priority'], value['type'], value['repeatable'], value['notificationTime'], value['admissionReference'])
        self.serverMessages = self.bulletinClient.getBulletinManagerServerMessages()
           
    def moveNotificationFromStoreToHStore(self, notificationId):
        self.jsonStore.delete(notificationId)
           
    def getServerMessages(self, updateMessageList=False, includeClientMessages=False, localFetch=False):
        if updateMessageList:
            self.updateServerMessages()
        result = self.serverMessages
        
        if includeClientMessages and self.clientMessages:
            if result:
                result.extend(self.clientMessages)
            else:
                result = self.clientMessages
        if localFetch:
            result = self.clientMessages
        return result
        
    def addClientMessage(self, title, text, priority, type, repeatable, notificationTime=None):
        title = _(title)
        text = _(text)
        if not self.clientMessages:
            self.clientMessages = []
        if not [el for el in self.clientMessages if el['title'] == title and el ['text'] == text]:
            clientMessage = {'title':title, 'text':text, 'priority':priority, 'shown':False, 'type':type, 'repeatable':repeatable}
            self.clientMessages.append(clientMessage)
        if type == 'istant':
            self.bulletinClient.postNotificationOnBulletin('ServerMessagesAvailable')
            
    def removeClientMessage(self, clientMessage):
        self.clientMessages = filter(lambda message: message != clientMessage, self.clientMessages)
        
    #END NOTIFICATION MANAGEMENT

    def translateClassForGcpViewerData(self):
        for className in self.dataSession.gcp.keys():
            for timeStamp in self.dataSession.gcp[className]:
                for element in self.dataSession.gcp[className][timeStamp]:
                    userKey = element['userKey']
                    label=self.crfData.getPropertyForAttribute(element['crfName'], className, element['attributeName'], 'label')
                    if label:
                        if label.replace('@','') in self.languages[self.userLanguage]['translations'] or label in self.languages[self.userLanguage]['translations']:
                            element['classNameTranslation'] = self.languages[self.userLanguage]['translations'][label.replace('@','')]
                        else:
                            element['classNameTranslation'] = label
                    else:
                        element['classNameTranslation'] = '.'.join((element['crfName'], className, element['attributeName']))
                    
                    idName = self.crfData.getPropertyForClass(element['crfName'], className, 'idName')
                    if idName:
                        values = self.dataSession.getAttributeValuesForObject(element['crfName'],className,element['classInstanceNumber'],idName)
                        if values:
                            element['groupLabel'] = values[0]
                        
        return self.dataSession.gcp
        
    def setGcpChangedAttributes(self, crfName, className, classInstanceNumber, timeStamp, attributeName, attributeValue, previousAttributeValue):
        if timeStamp == None:
            timeStamp = 1
        if className in self.changedAttributes.keys():
            if self.crfData.getPropertyForAttribute(crfName, className, attributeName, 'multiInstance'):
                #updating gcp info for multiInstance classes changed inside same session
                for changedAttributeDict in self.changedAttributes[className][timeStamp]:
                    changedAttributeDict['attributeValue'] = attributeValue
                    changedAttributeDict['datetime'] = datetime.datetime.now().isoformat()
                return
        changedAttributeDict = {}
        if previousAttributeValue:
            if type(attributeValue) == list:
                if previousAttributeValue:
                    if not [el for el in previousAttributeValue if el not in attributeValue]:
                        return
            else:
                if attributeValue in previousAttributeValue:
                    return
        else:
            changedAttributeDict['firstSave'] = '1'
        changedAttributeDict['crfName'] = crfName
        changedAttributeDict['className'] = className
        changedAttributeDict['classInstanceNumber'] = classInstanceNumber
        #changedAttributeDict['timeStamp'] = timeStamp
        changedAttributeDict['attributeName'] = attributeName
        changedAttributeDict['attributeValue'] = attributeValue
        changedAttributeDict['previousAttributeValue'] = previousAttributeValue
        changedAttributeDict['datetime'] = datetime.datetime.now().isoformat()
        classLabel = self.crfData.getPropertyForAttribute(crfName, className, attributeName, 'label')
        idName = self.crfData.getPropertyForClass(crfName, className, 'idName')
        if not classLabel:
            classLabel = '.'.join((crfName, className, attributeName))
        changedAttributeDict['classNameTranslation'] = classLabel
        if classLabel.replace('@','') in self.languages[self.userLanguage]['translations']:
            changedAttributeDict['classNameTranslation'] = self.languages[self.userLanguage]['translations'][classLabel.replace('@','')]
        idName = self.crfData.getPropertyForClass(crfName, className, 'idName')
        if idName:
            values = self.dataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,idName)
            if values:
                changedAttributeDict['groupLabel'] = values[0]
            
        #self.changedAttributes.append(changedAttributeDict)
        if className not in self.changedAttributes:
            self.changedAttributes[className] = {}
        if timeStamp not in self.changedAttributes[className]:
            self.changedAttributes[className][timeStamp] = []
        lowestTimeStamp = changedAttributeDict['datetime']
        for element in self.changedAttributes[className][timeStamp]:
            if element['datetime'] < lowestTimeStamp:
                lowestTimeStamp = element['datetime']
                
        #for element in self.changedAttributes[className][timeStamp]:
        #    if element['datetime'] == lowestTimeStamp:
        #        if [el for el in element['previousAttributeValue'] if (type(el) is bool and el == attributeValue) or (type(el) is not bool and el in attributeValue)]:
        #            return                
        if not self.changedAttributes[className][timeStamp]:
            self.changedAttributes[className][timeStamp].append(changedAttributeDict)
        else:
            for element in self.changedAttributes[className][timeStamp]:
                if 'firstSave' in element.keys():
                    break
                if element['classInstanceNumber'] == changedAttributeDict['classInstanceNumber'] and element['attributeName'] == changedAttributeDict['attributeName']:                    
                    if changedAttributeDict['attributeValue'] not in element['previousAttributeValue']:
                        element['attributeValue'] = changedAttributeDict['attributeValue']
                    else:
                        del self.changedAttributes[className][timeStamp]
                        if not self.changedAttributes[className]:
                            del self.changedAttributes[className]
                        break
                else:
                    if changedAttributeDict not in self.changedAttributes[className][timeStamp]:
                        self.changedAttributes[className][timeStamp].append(changedAttributeDict)
        
    def getGcpChangedAttributes(self, removeFirstSave=False):
        if removeFirstSave:
            #removing first save gcps 
            from copy import copy, deepcopy
            changedAttributesDue = deepcopy(self.changedAttributes)
            firstSaveElement = []
            for className in changedAttributesDue:
                for timeStamp in changedAttributesDue[className]:
                    for element in changedAttributesDue[className][timeStamp]:
                        if 'firstSave' in element:
                            self.changedAttributes[className][timeStamp].remove(element)
                        if not self.changedAttributes[className][timeStamp]:
                            del self.changedAttributes[className][timeStamp]
                        if not self.changedAttributes[className]:
                            self.changedAttributes[className] = {}
                        if not self.changedAttributes[className]:
                            del self.changedAttributes[className]
                        if not self.changedAttributes:
                            return {}
        return self.changedAttributes
        
    def resetChangedAttributes(self, confirmResult):
        self.confirmResult = confirmResult
        self.changedAttributes = {}


    def beginCriticalSection(self):
        self.criticalSectionCount += 1

    def endCriticalSection(self):
        self.criticalSectionCount -= 1

    def inCriticalSection(self):
        return bool(self.criticalSectionCount)

    def getCentreCode(self):
        return self.centrecode

    def isUpdatingScripts(self):
        if self.isMaster:
            return self.master.updatingScripts
        return False
        
    def shutDownMaster(self,askPermission):
        if self.isMaster:
            self.master.stopServices(askPermission)
            
    def forceMasterSynchronization(self):
        self.master.startSynchServiceLoop(psc.DB_SYNCH_TIME_INTERVAL,forced=True)
            
    def getMasterDataPackage(self, path):
        try:
            #force sync before everything starts
            #if self.master.synchronizing == False:
            self.master.createBackupZipFile(backupPath=path)
            #here we shall remove master.cfg and prompt for closure
            if self.masterFileName:
                os.remove(self.masterFileName)
            return True
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            print e
            return False
        
        
    def importDataFromPackage(self, backupPath):        
        if not os.path.exists(backupPath):
            print 'missing package'                
            return _("No prosafe master data package was specified.")
        if self.isMaster:
            if self.master.jsonStore.getStore():
                print 'not empty store'
                return False
        if os.path.exists(self.dataPath):
            fileList = os.listdir(self.dataPath)
            if 'prosafestore.sqlite' in fileList or 'appdata.xml' in fileList:
                print 'Prosafe data folder is not an empty folder, master data still inside?'
                return _("Prosafe data folder is not an empty folder, master data still inside?")
            if not os.path.exists(os.path.join(self.dataPath,'dletters')):
                os.mkdir('data/dletters')
        else:
            print 'creating data directory to put inside it the masterdatafile'
            os.mkdir('data')
            os.mkdir('data/dletters')
        if not self.restoreBackupZipFile(backupPath):
            print 'somehow failed import'
            return False
        
        return True
        
    def restoreBackupZipFile(self, backupPath='./masterdata.pmd'):
        try:
            
            if os.path.isfile(backupPath):
                #extractZip(os.path.join(self.dataPath,'masterdata.zip'))
                path = os.path.join(self.dataPath,'masterdata.pmd')
                shutil.copyfile(os.path.join(backupPath),path)
                import zipfile
                f=open(path,'rb')
                file = f.read()
                f.close()
                
                from blowfish import Blowfish
                fileCipher = Blowfish(self.publicEncryptionKey)
                fileCipher.initCTR()
                file = fileCipher.decryptCTR(file)
                
                f = open(path, 'wb')
                f.write(file)
                f.close()
                zipPath = path.replace('pmd', 'zip')
                shutil.copyfile(path,zipPath)
                f=open(zipPath,'rb')
                file = f.read()
                f.close()
                backupZip = zipfile.ZipFile(zipPath,'r', zipfile.ZIP_DEFLATED)
                for member in backupZip.namelist():
                    filename = os.path.basename(member)
                    # skip directories
                    if not filename:
                        continue

                    file, fileExt = filename.split('.')
                    if fileExt in ['xml', 'sqlite']:
                        myDir = self.dataPath
                    else:
                        myDir = os.path.join(self.dataPath,'dletters')
                    # copy file (taken from zipfile's extract)
                    source = backupZip.open(member)
                    target = open(os.path.join(myDir, filename), "wb")
                    shutil.copyfileobj(source, target)
                    source.close()
                    target.close()
                backupZip.close()
                f.close()
                os.remove(path)
                #try:
                #    os.remove(os.path.join(zipPath))
                #    os.remove(backupPath)
                #except:
                #    pass
        except BaseException, e:
            print e
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            return False
        return True

    def shutDownThreads(self):
        timesleep.Alive = False

    def masterFileExists(self):
        return os.path.isfile(self.masterFileName)

    def verifyMasterKey(self):
        if not os.path.isfile(self.masterFileName):
            return None
        masterKeyVerified = False
        masterFileCipher = Blowfish(self.masterFileEncryptionKey)
        masterFileCipher.initCTR()
        config = ConfigParser.ConfigParser()
        config.read(self.masterFileName)
        try:
            masterKey = masterFileCipher.decryptCTR(base64.b64decode(config.get('Prosafe','masterkey')))
            print 'MASTER KEY', masterKey
            if sys.platform == 'win32':
                macSeparator = '-'
            else:
                macSeparator = '\:'
            if len(masterKey.split(macSeparator)) == 5:
                self.macAddresses = self.getMacAddresses(sixHexadecimalsMac=False)
            try:
                dataPath = config.get('Prosafe','datapath')
                dataPath = dataPath.strip()
                if dataPath and os.path.isdir(dataPath):
                    self.dataPath = dataPath
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            self.masterIPAddresses = config.get('Prosafe','ipaddr').split(' ')
            if masterKey in self.macAddresses:
                masterKeyVerified = True
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
        if self.asclient:
            return False
        return masterKeyVerified

    def migrateIfNeeded(self):
        print 'EVALUATION IF MIGRATION NEEDS FIXING'
        datapath = abspath('data')
        try:
            migrator = DBMigrator(datapath)    
        except:
            return

        try:
            appdataManager = AppdataManager(os.path.join(datapath,'appdata.xml'),self.publicEncryptionKey)
            loadedUnencoded = appdataManager.loadAppdata(base64encoded=False)

            if not loadedUnencoded:
                print 'NO NEED OF MIGRATING'
                return

            dbEncrypted = migrator.hasEncryptedDB()
 
            import shutil
            shutil.copyfile(os.path.join(datapath,'appdata.xml'),os.path.join(datapath,'appdata_noenc.xml'))

            appdataManager.writeAppdata(True)

            if dbEncrypted:
                print 'FIXING MIGRATION'
                #os.rename(os.path.join(datapath,'prosafedata.sqlite'),os.path.join(datapath,'prosafedata.sqlite.broken'))
                #shutil.copyfile(os.path.join(datapath,'prosafedata.sqlite.old.sqlite'),os.path.join(datapath,'prosafedata.sqlite'))
                os.rename(os.path.join(datapath,'prosafedata.sqlite'),os.path.join(datapath,'prosafedata.sqlite.broken'))
                shutil.copyfile(os.path.join(datapath,'prosafedata.sqlite.old.sqlite'),os.path.join(datapath,'prosafedata.sqlite'))
                os.rename(os.path.join(datapath,'prosafedata.sqlite.old.sqlite'),os.path.join(datapath,'prosafedata.sqlite.old2.sqlite'))
            else:
                print 'MIGRATING FROM 1.0'

            migrator = DBMigrator(datapath)     
            migrator.migrate()

            self.createMasterFile()
            
        except BaseException, e:
            print e
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
 
    def attemptBecomeMaster(self, force=False):
        self.isMaster = self.verifyMasterKey()
        
        if not self.isMaster:
            return

        from prosafemaster import ProsafeMaster
        self.master = ProsafeMaster(self.dataPath,flags=self.flags)
        self.connectToMasterAndStartServices()
        self.createMasterFile()
        
    def connectToMasterAndStartServices(self):
        #if not self.isMaster:
        Pyro.config.PYRO_PORT = psc.PYRO_PORT
        Pyro.config.PYRO_NS_PORT = psc.PYRO_NS_PORT
        Pyro.config.PYRO_NS_BC_PORT = psc.PYRO_NS_BC_PORT
       
        self.isMaster = self.verifyMasterKey()
        #if self.localhost and not self.isMaster:
        #    raise BaseException
        if self.localhost or self.connectingToMasterAsMaster:
            Pyro.config.PYRO_HOST = 'localhost'
            Pyro.config.PYRO_PUBLISHHOST = 'localhost'
            Pyro.config.PYRO_NS_HOSTNAME = 'localhost'
            self.networkManager = PyroProxyWrapper("PYRONAME://networkmanager")
        else: 
            done = False
            ipAddressIndex = 0
            while not done:
                try:
                    self.networkManager = PyroProxyWrapper("PYRONAME://networkmanager")
                    done = True
                except BaseException, e:
                    if ipAddressIndex < len(self.masterIPAddresses):
                        Pyro.config.PYRO_NS_HOSTNAME = self.masterIPAddresses[ipAddressIndex]
                        #os.environ['PYRO_NS_HOSTNAME'] = self.masterIPAddresses[ipAddressIndex]
                        print 'Using NS hostname', Pyro.config.PYRO_NS_HOSTNAME
                        ipAddressIndex += 1
                    else:
                        Pyro.config.PYRO_NS_HOSTNAME = None
                        raise
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
        try:
            resultForAttempt = self.networkManager.getMasterVersion()
            
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass
        if not self.connectingToMasterAsMaster and self.isMaster:
            self.networkManager = None
            self.connectingToOtherMasterAsMaster = True
            raise BaseException
        self.fileManager = PyroProxyWrapper("PYRONAME://filemanager")
        self.fileClient.setFileManager(self.fileManager)
        
        if getattr(sys,"frozen",False):
            if not self.isMaster:
                if self.networkManager.getMasterVersion() != PROSAFE_VERSION:
                    self.checkAndRetrieveCurrentUpdate()
                    self.performUpdate()
        self.jsonStore = PyroProxyWrapper("PYRONAME://jsonstore")
        self.appdataManager = PyroProxyWrapper("PYRONAME://appdatamanager")
        self.bulletinManager = PyroProxyWrapper("PYRONAME://bulletinmanager")
        if not self.isMaster and not self.staticClientKey:
            self.fileClient.getFile('./','master.cfg',abspath(),'master.cfg')

        if self.isMaster:
            self.staticClientKey = 'Master'
        self.bulletinClient.setBulletinManager(self.bulletinManager,self.staticClientKey)
        self.notificationCenter.addObserver(self,self.retrieveUpdatedCrfs,'CRFUpdated')
        self.notificationCenter.addObserver(self,self.retrieveUpdatedSoftware,'SoftwareUpdated')
        if not self.staticClientKey:
            self.notificationCenter.addObserver(self,self.retrieveDataBackup,'BackupAvailable')
        self.bulletinClient.startPollingLoop()
        self.checkAndRetrieveCrfs()
        

    def getMacAddresses(self, sixHexadecimalsMac=True):
        grepstr = ''
        if sys.platform == 'win32':
            lines = os.popen("ipconfig /all")
            grepstr = r'..-..-..-..-..'
            if sixHexadecimalsMac:
                grepstr = r'..-..-..-..-..-..'
        else:
            lines = os.popen("/sbin/ifconfig")
            grepstr = r'..\:..\:..\:..\:..'
            if sixHexadecimalsMac:
                grepstr = r'..\:..\:..\:..\:..\:..'
        compiledre = re.compile(grepstr)

        macAddresses = []
        for line in lines:
            searchLine = line.upper()
            result = compiledre.findall(searchLine)
            if result:
                macAddresses.extend(result)

        return macAddresses

    def createMasterFile(self):
        masterFileCipher = Blowfish(self.masterFileEncryptionKey)
        masterFileCipher.initCTR()
        config = ConfigParser.ConfigParser()
        config.add_section('Prosafe')
        config.set('Prosafe','masterkey',base64.b64encode(masterFileCipher.encryptCTR(self.macAddress)))
        config.set('Prosafe','datapath',self.dataPath)
        #config.set('Prosafe','lastcwd',abspath())
        config.set('Prosafe','version',PROSAFE_VERSION)
        config.set('Prosafe','ipaddr',' '.join(self.ipAddresses))
        with open(self.masterFileName,'wb') as configfile:
            config.write(configfile)

    #def crfUpdatedCallback(self, result):
    #    userInfo = {'filenames': result}
    #    self.notificationCenter.postNotification('CRFUpdated',self,userInfo)
    #    self.bulletinClient.postNotificationOnBulletin('CRFUpdated',userInfo)

    
    def getMappingFileFromMaster(self):
        filenamesWithMD5 = self.fileClient.getFileNamesInPathWithMD5('GivitiMapper_master',None,relativeTo='version')
        for filename in filenamesWithMD5:
            self.fileClient.getFile('GivitiMapper_master',filename,abspath('GivitiMapper'),filename,relativeTo='version')
            try:
                self.fileClient.putFile('GivitiMapper_master',filename,'GivitiMapper',filename)
            except:
                pass
               
    
    def retrieveUpdatedCrfs(self,notifyingObject,userInfo=None):
        filenames = userInfo['filenames']
        for filename in filenames:
            self.fileClient.getFile('config_master',filename,abspath('config'),filename,relativeTo='version')
        self.crfData.initialize()

    def checkAndRetrieveCrfs(self):
        filenamesWithMD5 = self.fileClient.getFileNamesInPathWithMD5('config_master','.xml',relativeTo='version')
        currentFileNames = os.listdir(abspath('config'))
        for currentFileName in currentFileNames:
            if currentFileName not in filenamesWithMD5:
                os.remove(os.path.join(abspath('config'),currentFileName))
        for filename in filenamesWithMD5:
            filepath = os.path.join(abspath('config'),filename)
            if os.path.isfile(filepath) and filenamesWithMD5[filename] == md5_for_file(filepath):
                continue
            self.fileClient.getFile('config_master',filename,abspath('config'),filename,relativeTo='version')

    def retrieveDataBackup(self,notifyingObject,userInfo=None):
        backupThread = Thread(target=self.getDataBackup)
        backupThread.daemon = True
        backupThread.start()
    
    def getDataBackup(self):
        bkpFileName = 'databkp.zip'
        localBkpFileName = 'databkp.zip'
        self.fileClient.getFile('backupzip',bkpFileName,self.dataBackupDirectory,localBkpFileName)

    def retrieveUpdatedSoftware(self,notifyingObject,userInfo=None):
        if getattr(sys,"frozen",False):
            if not self.isMaster:
                self.checkAndRetrieveCurrentUpdate()
                self.performUpdate()
    
    def checkAndRetrieveCurrentUpdate(self):
        filenamesWithMD5 = self.fileClient.getFileNamesInPathWithMD5('currentupdate')
        for filename in filenamesWithMD5:
            filepath = os.path.join(abspath('currentupdate'),filename)
            if os.path.isfile(filepath) and filenamesWithMD5[filename] == md5_for_file(filepath):
                continue
            self.fileClient.getFile('currentupdate',filename,abspath('currentupdate'),filename)

    def performUpdate(self):
        import esky
        import esky.finder
        vfinder = esky.finder.LocalVersionFinder(abspath('currentupdate'))
        eskyApp = esky.Esky(sys.executable,vfinder)
        newVersion = eskyApp.find_update()
        if newVersion == None:
            return
        try:
            eskyApp.auto_update()
        except Exception, e:
            print "ERROR UPDATING APP:", e
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
        eskyApp.cleanup()
        command = os.path.join(eskyApp.appdir, "prosafe.exe") 
        os.execl(command, ' ')
        
    def removeOlderUpdates(self):
        packageName = 'Prosafe-%s.win32' % PROSAFE_VERSION
        for file in os.listdir(self.currentUpdateDirectory):
            if file < packageName:
                os.remove(os.path.join(self.currentUpdateDirectory, file))            

    def loadConfig(self, local=False, crfFileDict=None):
        self.initializeEncryption()
       
        #if not self.hasUsers():
        #    self.createFirstUser()
        
        if crfFileDict != None:
            self.crfFileDict = crfFileDict
        else:
            self.buildCrfFileDict()
        self.crfData = DataConfiguration()       
        if not local:
            self.crfData.readCrfConfiguration(os.path.join(self.configDirectory,'basedata_config.xml'))
        else:
            self.crfData.readCrfConfiguration(abspath('config_master/basedata_config.xml',True))
        today = datetime.date.today().isoformat()
        crfVersionForFormats = self.getCrfValidVersion(psc.coreCrfName, today)
        self.loadTranslations(self.userLanguage,os.path.join(self.configDirectory,'%s_languages_%s.xml' % (psc.coreCrfName, crfVersionForFormats)))
        self.readCustomizableCodingSets()
        #self.loadAppLanguages()
        #self.loadAppTranslations('Italiano')
        try:
            self.loadUsers()
        except BaseException, e:
            print e
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass
            
    def readCustomizableCodingSets(self):
        
        if 'personalizations' not in psc.toolBarApplications:
            return
        crfData = DataConfiguration()
        
        #TODO: read crfnames
        # crfNames = ['core', 'infection', 'cch']
        crfNames = ['core']
        if not self.userLanguage:
            return
        #crfData.readCrfConfiguration(abspath('config_master/core_config_4.3.0.xml',True))
        for crfName in crfNames:
            today = datetime.date.today().isoformat()
            crfVersionForCustomization = self.getCrfValidVersion(crfName, today)
            crfData.readCrfConfiguration(os.path.join(self.configDirectory,self.crfFileDict[crfName][crfVersionForCustomization]['filenames']['crf']))
            self.customizationDict[crfName] = {} 
            for codingSetName in crfData.getCodingSetsForCrf(crfName):
                if 'customizable' in crfData.getPropertiesForCodingSet(crfName,codingSetName):
                    customizableGroup = ''
                    if 'customizableGroup' in crfData.getPropertiesForCodingSet(crfName,codingSetName):
                        textId = crfData.getPropertyForCodingSet(crfName,codingSetName, 'customizableGroup').replace('@', '')
                        if textId in self.languages[self.userLanguage]['translations']:
                            customizableGroup = self.languages[self.userLanguage]['translations'][textId]
                        elif textId in self.languages['English']['translations']:
                            customizableGroup = self.languages['English']['translations'][textId]
                        else:
                            customizableGroup = textId
                    label = ''
                    if customizableGroup not in self.customizationDict[crfName].keys():
                        self.customizationDict[crfName][customizableGroup] = []
                    if crfData.getPropertyForCodingSet(crfName,codingSetName, 'label'):
                        textId = crfData.getPropertyForCodingSet(crfName,codingSetName, 'label').replace('@', '')
                        label = textId
                        if textId in self.languages[self.userLanguage]['translations']:
                            label = self.languages[self.userLanguage]['translations'][textId]
                        elif textId in self.languages['English']['translations']:
                            label = self.languages['English']['translations'][textId]
                        else:
                            label = textId
                            
                    self.customizationDict[crfName][customizableGroup].append({codingSetName : label})
        #print 'CUSTOMIZATION FILE DICT', self.customizationDict
                
    def setEncryptionKey(self, encryptionKey):
        if not encryptionKey:
            return
        self.encryptionKey = encryptionKey
        self.initializeEncryption()

    def initializeEncryption(self):
        if not self.encryptionKey:
            return
        self.cipher = Blowfish(self.encryptionKey)
 
    def buildCrfFileDict(self):
        xmlFileList = os.listdir(self.configDirectory)
        xmlFileList = [filename for filename in xmlFileList if filename[-4:] == '.xml']
        self.crfFileDict = dict()
        self.forceGcp = False
        for filename in xmlFileList:
            f = open(os.path.join(self.configDirectory,filename),"r")
            xmlLine = None
            while not xmlLine or not xmlLine.strip() or xmlLine.strip().startswith('<!--') or xmlLine.strip().startswith('<?xml'):
                xmlLine = f.readline()
            xmlLine = xmlLine.strip()[:-1] + '/>'
            #f = open(os.path.join(self.configDirectory,filename),"r")
            #xmlString = f.read()
            #f.close()
            #from psxml2xml import psXMLToXML
            #xmlString = psXMLToXML(xmlString)
            #f = open('foo.xml','w')
            #f.write(xmlString)
            #f.close()
            #xmlDocument = etree.fromstring(xmlString)
            xmlDocument = etree.fromstring(xmlLine)
            #for event, elem in etree.iterparse(os.path.join(self.configDirectory,filename)):
            elem = xmlDocument
            
            if elem.tag == 'crf':
                tag = elem.tag
                crfName = elem.get('name')
                version = elem.get('version')
                basedata = elem.get('basedata')
                enablesGcp = elem.get('enablesGcp')
                if basedata == '1':
                    continue
                minValidDate = elem.get('minValidDate')
                maxValidDate = elem.get('maxValidDate')
                today = datetime.date.today().isoformat()
                    
                if enablesGcp and (today >= minValidDate and today <= maxValidDate):
                    try:
                        currentCrfNames = self.getAppdataCrfNamesForDate(self.getDate())
                        if elem.get('name') in currentCrfNames:
                            self.setGcpSetting(True)
                            self.forceGcp = True
                    except:
                        pass
                
                if not (crfName and version and tag):
                    continue
                if crfName not in self.crfFileDict:
                    self.crfFileDict[crfName] = dict()
                if version not in self.crfFileDict[crfName]:
                    self.crfFileDict[crfName][version] = dict()
                    self.crfFileDict[crfName][version]['filenames'] = dict()
                self.crfFileDict[crfName][version]['filenames'][tag] = filename
                self.crfFileDict[crfName][version]['minValidDate'] = minValidDate
                self.crfFileDict[crfName][version]['maxValidDate'] = maxValidDate
            elif elem.tag in ['interfaces','pages','languages']:
                tag = elem.tag
                crfName = elem.get('crf')
                version = elem.get('version')
                basedata = elem.get('basedata')
                if basedata == '1':
                    continue
                if not (crfName and version and tag):
                    continue
                if crfName not in self.crfFileDict:
                    self.crfFileDict[crfName] = dict()
                if version not in self.crfFileDict[crfName]:
                    self.crfFileDict[crfName][version] = dict()
                    self.crfFileDict[crfName][version]['filenames'] = dict()
                self.crfFileDict[crfName][version]['filenames'][tag] = filename
            if elem.tag == 'pages':
                f = open(os.path.join(self.configDirectory,filename),"r")
                xmlString = f.read()
                f.close()
                from psxml2xml import psXMLToXML
                xmlString = psXMLToXML(xmlString)
                xmlDocument = etree.fromstring(xmlString)
                crfName = xmlDocument.get('crf')
                version = xmlDocument.get('version')
                for childElem in xmlDocument:
                    if childElem.tag != 'page':
                        continue
                    quickcompilation = childElem.get('quickcompilation')
                    if quickcompilation == '1':
                        quickcompilationdescription = childElem.get('quickcompilationdescription')
                        quickcompilationcondition = childElem.get('quickcompilationcondition')
                        if crfName not in self.quickCompilationPages:
                            self.quickCompilationPages[crfName] = dict()
                        if not quickcompilationdescription:
                           quickcompilationdescription = ''
                        if not quickcompilationcondition:
                            quickcompilationcondition = ''
                        if version not in self.quickCompilationPages[crfName]:
                            self.quickCompilationPages[crfName][version] = []
                        self.quickCompilationPages[crfName][version].append({'pageName': childElem.get('name'), 'pageDescription' : quickcompilationdescription, 'pageConditionClass' : quickcompilationcondition})

        crfNames = self.crfFileDict.keys()
        for crfName in crfNames:
            versions = self.crfFileDict[crfName].keys()
            for version in versions:
                if 'minValidDate' not in self.crfFileDict[crfName][version]:
                    self.crfFileDict[crfName].pop(version)
            if not self.crfFileDict[crfName]:
                self.crfFileDict.pop(crfName)
                
    def areDatesSorted(self, firstDate, secondDate, includeEqual=False):
        if includeEqual:
            return datetime.datetime.strptime(firstDate,'%Y-%m-%d') <= datetime.datetime.strptime(secondDate,'%Y-%m-%d')
        return datetime.datetime.strptime(firstDate,'%Y-%m-%d') < datetime.datetime.strptime(secondDate,'%Y-%m-%d')

    def maxVersion(self, versions):
        splitVersions = [el.split('.') for el in versions]
        paddedVersions = ['%010d.%010d.%010d' % (int(el[0]),int(el[1]),int(el[2])) for el in splitVersions]
        maxVersion = max(paddedVersions)
        splitMaxVersion = maxVersion.split('.')
        return '%d.%d.%d' % (int(splitMaxVersion[0]),int(splitMaxVersion[1]),int(splitMaxVersion[2]))

    def getCrfValidVersion(self,crfName,admissionDate):

        if crfName not in self.crfFileDict:
            return None 
        validVersions = []
        for version in self.crfFileDict[crfName]:
            minValidDate = self.crfFileDict[crfName][version]['minValidDate']
            maxValidDate = self.crfFileDict[crfName][version]['maxValidDate']
            if not (minValidDate and maxValidDate):
                validVersions.append(version)
            elif not maxValidDate and self.areDatesSorted(minValidDate,admissionDate,True):
                validVersions.append(version)
            elif self.areDatesSorted(minValidDate,admissionDate,True) and self.areDatesSorted(admissionDate,maxValidDate,True):
                validVersions.append(version)
        if not validVersions:
            return None
        return self.maxVersion(validVersions)
        #validVersions.sort()
        #return validVersions[-1]

    def loadPersonalizations(self, personalizations, crfName):
        if crfName == psc.coreCrfName and personalizations:
            for customization in [el for el in personalizations.getchildren()]:
                if customization.tag == 'codingSetValue':
                    self.crfData.addPersonalizedCodingSetValue(customization)
                elif customization.tag == 'attribute':
                    self.crfData.addPersonalizedAttribute(customization)
        self.crfData.mergePersonalizations(personalizations)
        
    def saveCustomization(self, customizations, proceduresCustomization, removingList, removalOptions):
        from xml.etree import cElementTree as etree
        personalizationElementList = []
        if customizations or proceduresCustomization:
            personalizationElement = '<codingSetValue value="%s" name="%s"/>'
            for crfName in customizations.keys():
                if customizations[crfName]:
                    for page in customizations[crfName].keys():
                        for codingSetName in customizations[crfName][page]:
                            for codingSetValue in customizations[crfName][page][codingSetName]:
                                codingSetValueName = codingSetValue['name']
                                codingSetValueLabel = codingSetValue['label']
                                fullCodingSetValueName = '%s.%s.%s' % (crfName, codingSetName, codingSetValueName)
                                personalizationElementList.append(personalizationElement % (codingSetValueLabel, fullCodingSetValueName))
            
            personalizationElement = '<codingSetValue active="1" value="%s" name="core.procTreatCodification.%s" dynattribute="core.procedureDetailCustom.procedureId" dynclass="core.procedureDetailCustom" />'
            for crfName in proceduresCustomization.keys():
                for page in proceduresCustomization[crfName]:
                    for procedure in proceduresCustomization[crfName][page]:
                        print personalizationElement % (procedure['label'], procedure['name'])
                        personalizationElementList.append(personalizationElement % (procedure['label'], procedure['name']))
        if removalOptions:
            coreRemovalOptions = removalOptions['core']['prelieve']
            print 'coreRemovalOptions to be saved in appdata:', coreRemovalOptions
            if coreRemovalOptions['organs'] == True:
                personalizationElement = '<attribute label="@@@300033@@@" multiInstance="1" description="" dataType="codingset" codingSet="core.organRemovalCodification" name="core.organRemovalCustom.value" export="@@@300000@@@" exportWeight="140"/>'
                personalizationElementList.append(personalizationElement)
            if coreRemovalOptions['fabric'] == True:
                personalizationElement = '<attribute label="@@@300050@@@" multiInstance="1" description="" dataType="codingset" codingSet="core.fabricRemovalCodification" name="core.fabricRemovalCustom.value" export="@@@300000@@@" exportWeight="1300"/>'
                personalizationElementList.append(personalizationElement)
        if personalizationElementList:
            self.setAppdataPersonalizations(personalizationElementList)
            personalizations = self.getAppdataPersonalizations()
            crfNames = self.getAppdataCrfNamesForDate(self.getDate())
            if personalizations:
                for crfName in crfNames:
                    self.loadPersonalizations(personalizations, crfName)
        
    def loadCrfs(self,admissionDate):
        newid = 1000

        crfNames = self.getAppdataCrfNamesForDate(admissionDate)
            
        personalizations = self.getAppdataPersonalizations()
        #print [el.get('value') for el in personalizations]

        for crfName in crfNames:

            validVersion = self.getCrfValidVersion(crfName,admissionDate)

            if not validVersion:
                continue

            currentCrfVersion = self.crfData.getPropertyForCrf(crfName,'version')
            isBasedata = self.crfData.getPropertyForCrf(crfName,'basedata')

            if currentCrfVersion == validVersion and isBasedata != '1':
                continue

            self.crfData.readCrfConfiguration(os.path.join(self.configDirectory,self.crfFileDict[crfName][validVersion]['filenames']['crf']))
            if personalizations:
                self.loadPersonalizations(personalizations, crfName)
                #if crfName == psc.coreCrfName:
                #    #self.crfData.addPersonalizationClassToCrf(psc.coreCrfName)
                #    for customization in [el for el in personalizations.getchildren()]:
                #        if customization.tag == 'codingSetValue':
                #            self.crfData.addPersonalizedCodingSetValue(customization)
                #        elif customization.tag == 'attribute':
                #            self.crfData.addPersonalizedAttribute(customization)
                #self.crfData.mergePersonalizations(personalizations)
            
            f = open(os.path.join(self.configDirectory,self.crfFileDict[crfName][validVersion]['filenames']['interfaces']), "r")
            xml = f.read()
            f.close()
            from psxml2xml import psXMLToXML
            xml = psXMLToXML(xml)
            self.interfacesXML[crfName] = etree.fromstring(xml)

            self.pagesXML[crfName] =  dict()
            self.pageHierarchy[crfName] = dict()
            self.pageHierarchyExpanded[crfName] = dict()

            f = open(os.path.join(self.configDirectory,self.crfFileDict[crfName][validVersion]['filenames']['pages']), "r")
            xml = f.read()
            f.close()
            xml = psXMLToXML(xml)
            treeXML = etree.fromstring(xml)
            
            for page in treeXML:
                pageid = newid
                if page.tag == 'page':
                    name = str(page.get('name'))
                    dynamic = page.get('dynamic')
                    visibility = page.get('visible')
                    parentname = str(page.get('parentname'))
                    onenter = page.get('onenter')
                    onleave = page.get('onleave')
                    unexpandable = page.get('unexpandable')
                    collapsed = page.get('collapsed')
                    quickcompilation = page.get('quickcompilation')
                    quickcompilationdescription = page.get('quickcompilation')
                    quickcompilationcondition = page.get('quickcompilationcondition')
                    if quickcompilation != '1' and dynamic != '1':
                        if parentname not in self.pageHierarchy[crfName]:
                            self.pageHierarchy[crfName][parentname] = []
                        self.pageHierarchy[crfName][parentname].append(name)
                    self.pagesXML[crfName][name] = dict()
                    self.pagesXML[crfName][name]['xml'] = page
                    self.pagesXML[crfName][name]['name'] = name
                    self.pagesXML[crfName][name]['dynamic'] = dynamic
                    self.pagesXML[crfName][name]['parentname'] = parentname
                    self.pagesXML[crfName][name]['pageid'] = pageid
                    self.pagesXML[crfName][name]['visible'] = visibility
                    self.pagesXML[crfName][name]['onenter'] = onenter
                    self.pagesXML[crfName][name]['onleave'] = onleave
                    self.pagesXML[crfName][name]['unexpandable'] = unexpandable
                    self.pagesXML[crfName][name]['collapsed'] = collapsed
                    self.pagesXML[crfName][name]['quickcompilation'] = quickcompilation
                    self.pagesXML[crfName][name]['quickcompilationdescription'] = quickcompilationdescription
                    self.pagesXML[crfName][name]['quickcompilationcondition'] = quickcompilationcondition
                elif page.tag == 'dynpage':
                    attribute = page.get('attribute')
                    name = attribute
                    parentname = str(page.get('parentname'))
                    visibility = page.get('visible')
                    appendtoname = page.get('appendtoname')
                    appendtonamedefault = page.get('appendtonamedefault')
                    currentonly = page.get('currentonly')
                    unexpandable = page.get('unexpandable')
                    collapsed = page.get('collapsed')
                    self.pagesXML[crfName][name] = dict()
                    self.pagesXML[crfName][name]['xml'] = page
                    self.pagesXML[crfName][name]['name'] = name
                    self.pagesXML[crfName][name]['dynpage'] = True
                    self.pagesXML[crfName][name]['parentname'] = parentname
                    self.pagesXML[crfName][name]['pageid'] = pageid
                    self.pagesXML[crfName][name]['attribute'] = attribute
                    self.pagesXML[crfName][name]['appendtoname'] = appendtoname
                    self.pagesXML[crfName][name]['appendtonamedefault'] = appendtonamedefault
                    self.pagesXML[crfName][name]['currentonly'] = currentonly
                    self.pagesXML[crfName][name]['visible'] = visibility
                    self.pagesXML[crfName][name]['unexpandable'] = unexpandable
                    self.pagesXML[crfName][name]['collapsed'] = collapsed

                    if parentname not in self.pageHierarchy[crfName]:
                        self.pageHierarchy[crfName][parentname] = []
                    self.pageHierarchy[crfName][parentname].append(name)

                newid +=1

            languageFilePath = os.path.join(self.configDirectory,self.crfFileDict[crfName][validVersion]['filenames']['languages'])
            f = open(languageFilePath, "r")
            xmlString = f.read()
            f.close()
            xmlString = psXMLToXML(xmlString)
            xmlDocument = etree.fromstring(xmlString)
            if xmlDocument.tag == 'languages':
                for el in xmlDocument:
                    if el.tag == 'language' and el.get('name') and el.get('name') not in self.languages:
                        self.languages[el.get('name')] = dict()
                        self.languages[el.get('name')]['translations'] = dict()
                        self.languages[el.get('name')]['formats'] = dict()
            self.loadTranslations('English',languageFilePath)
            self.loadTranslations(self.userLanguage,languageFilePath)

        self.buildIndexedKeys()

    def buildIndexedKeys(self):
        self.indexedKeys = set()
        crfNames = self.crfData.getCrfNames()
        indexedClasses = []

        for crfName in crfNames:
            indexedClassNames = self.crfData.getClassesByPropertyWithValue(crfName,"indexed","1")
            if not indexedClassNames:
                continue
            indexedClasses.extend([(crfName,className) for className in indexedClassNames])

        for crfName, className in indexedClasses:
            attributeNames = self.crfData.getAttributeNamesForClass(crfName,className)
            for attributeName in attributeNames:
                self.indexedKeys.add('crfs.%s.%s.%s' % (crfName,className,attributeName))

        for attributeFullName in psc.gridDataAttributes:
            self.indexedKeys.add('crfs.%s' % attributeFullName)

    def getLanguageNames(self):
        languageNames = self.languages.keys()
        languageNames.sort()
        return languageNames
 
    def loadAppLanguages(self):
        f = open(os.path.join(self.configDirectory,'gui_languages.xml'),"r")
        xmlString = f.read()
        f.close()
        from psxml2xml import psXMLToXML
        xmlString = psXMLToXML(xmlString)
        xmlDocument = etree.fromstring(xmlString)
        if xmlDocument.tag == 'languages':
            for el in xmlDocument:
                if el.tag == 'language' and el.get('name') and el.get('name') not in self.languages:
                    self.languages[el.get('name')] = dict()
                    self.languages[el.get('name')]['translations'] = dict()
                    self.languages[el.get('name')]['formats'] = dict()
        f = open(os.path.join(self.configDirectory,'basedata_languages.xml'),"r")
        xmlString = f.read()
        f.close()
        from psxml2xml import psXMLToXML
        xmlString = psXMLToXML(xmlString)
        xmlDocument = etree.fromstring(xmlString)
        if xmlDocument.tag == 'languages':
            for el in xmlDocument:
                if el.tag == 'language' and el.get('name') and el.get('name') not in self.languages:
                    self.languages[el.get('name')] = dict()
                    self.languages[el.get('name')]['translations'] = dict()
                    self.languages[el.get('name')]['formats'] = dict()
            
    def loadAppTranslations(self,language):
        self.loadTranslations(language,os.path.join(self.configDirectory,'gui_languages.xml'))
        self.loadTranslations(language,os.path.join(self.configDirectory,'basedata_languages.xml'))

    def loadTranslations(self,language,languageFilePath):
        if not self.appdataManager.isAppdataLoaded():
            return
        if not self.languages:
            self.loadAppLanguages()
        f = open(languageFilePath,"r")
        xmlString = f.read()
        f.close()
        from psxml2xml import psXMLToXML
        xmlString = psXMLToXML(xmlString)
        xmlDocument = etree.fromstring(xmlString)
        if xmlDocument.tag == 'languages':
            crfName = xmlDocument.get('crf')
            for languageEl in xmlDocument:
                if languageEl.tag != 'language':
                    continue
                if languageEl.get('name') != language:
                    continue
                for translationsEl in languageEl:
                    if translationsEl.tag == 'translations':
                        for translationEl in translationsEl:
                            if translationEl.tag != 'translation':
                                continue
                            self.languages[language]['translations'][translationEl.get('textId')] = translationEl.get('text')
                            if translationEl.get('text') == None:
                                self.languages[language]['translations'][translationEl.get('textId')] = ""
                    elif translationsEl.tag == 'formats':
                        for translationEl in translationsEl:
                            if translationEl.tag != 'format':
                                continue
                            itemName = translationEl.get('item')
                            itemType = 'item'
                            if not itemName:
                                itemName = translationEl.get('class')
                                itemType = 'class'
                            if not itemName:
                                itemName = translationEl.get('attribute')
                                itemType = 'attribute'
                            itemFullName = '%s.%s' % (crfName,itemName)
                            self.languages[language]['formats'][itemFullName] = {'label':translationEl.get('label'), 'expression':translationEl.get('expression'), 'type':itemType, 'description':translationEl.get('description'), 'baseformat':translationEl.get('baseformat')}

    def getFormatDict(self, crfName, itemName):
        itemFullName = '%s.%s' % (crfName,itemName)
        if itemFullName in self.languages[self.userLanguage]['formats']:
            return self.languages[self.userLanguage]['formats'][itemFullName]
        elif itemFullName in self.languages['English']['formats']:
            return self.languages['English']['formats'][itemFullName]
        return None

    def getFormatExpression(self, crfName, itemName):
        itemFormatDict = self.getFormatDict(crfName,itemName)
        if itemFormatDict:
            return itemFormatDict['expression']
        return None

    def getFormatLabel(self, crfName, itemName):
        itemFormatDict = self.getFormatDict(crfName,itemName)
        if itemFormatDict:
            return itemFormatDict['label']
        return None
        
    def isFormatForClass(self, crfName, itemName):
        itemFormatDict = self.getFormatDict(crfName,itemName)
        if itemFormatDict:
            return itemFormatDict['type'] == 'class'
            #return itemFormatDict['isClass']
        return None

    def getAllFormats(self):
        formats = self.languages['English']['formats']
        formats.update(self.languages[self.userLanguage]['formats'])
        return formats
        
    def getFormatsAndDescription(self):
        import os
        import datetime
        today = datetime.date.today().isoformat()
        crfVersionForFormats = self.getCrfValidVersion(psc.coreCrfName, today)
        self.loadTranslations(self.userLanguage,os.path.join(self.configDirectory,'%s_languages_%s.xml' % (psc.coreCrfName, crfVersionForFormats)))
        formats = self.getAllFormats()
        formatsAndDescriptionDict = dict()
        for itemFullName in formats:
            if formats[itemFullName]['baseformat']:
                formatsAndDescriptionDict[formats[itemFullName]['label']] = formats[itemFullName]['description']
        return formatsAndDescriptionDict

    def translateString(self, text):
        if not text.startswith('@@@'):
            try:
                if self.languages[self.userLanguage]['translations'][text]:
                    text = self.languages[self.userLanguage]['translations'][text]
            except BaseException, e:
                pass
        else:
            r = re.compile('@@@[0-9]+@@@')
            replacements = r.findall(text)
            for rep in replacements:
                textId = rep.replace('@@@', '')
                try:
                    text = text.replace(rep,self.languages[self.userLanguage]['translations'][textId])
                    if not text and self.centrecode in ['IT999', 'IT998']:
                        text = textId
                except BaseException, e:
                    if self.centrecode in ['IT999', 'IT998']:
                        text = textId
                    else:
                        try:
                            text = text.replace(rep,self.languages['English']['translations'][textId])
                        except BaseException, er:
                            text = 'TextId: ' + textId + '(no string available)'
            while text.find('""') != -1:
                text = text.replace('""','"')
            if self.translationMode:
                text = '%s - %s' % (textId, text)
        return text

    def getDateTime(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    def getDate(self):
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def loadAppdata(self, local=False):

        if local:
            appdataFileName = os.path.join(self.dataPath,'appdata.xml') 
            self.appdataManager = AppdataManager(appdataFileName,self.publicEncryptionKey)

        try:
            if not self.appdataManager.loadAppdata():
                self.centrecode = None
                self.encryptionKey = None
                return False
        except BaseException, e:
            print e
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            return False

        self.centrecode = self.appdataManager.getAppdataValue('centre','centreCode')
        encryptionKey = self.appdataManager.getAppdataValue('centre','privateKey')
        self.setEncryptionKey(encryptionKey)
        self.gcpActive = self.getGcpSetting()
        self.translationMode = self.getTranslationModeSetting()
        self.userLanguage = self.appdataManager.getAppdataValue('centre','userLanguage')
        return True

    def resetPrivateKey(self):
        backupPrivateKey = self.appdataManager.getAppdataValue('centre','backupPrivateKey')
        if not backupPrivateKey:
            return False
        self.appdataManager.setAppdataValue('centre','privateKey',backupPrivateKey)
        self.setEncryptionKey(backupPrivateKey)
        return True

    def setNewPrivateKey(self,privateKey):
        if not self.appdataManager.getAppdataValue('centre','backupPrivateKey'):
            currentPrivateKey = self.appdataManager.getAppdataValue('centre','privateKey')
            self.appdataManager.createAppdataElement('centre','backupPrivateKey',write=False)
            self.appdataManager.setAppdataValue('centre','backupPrivateKey',currentPrivateKey)
        self.appdataManager.setAppdataValue('centre','privateKey',privateKey)
        self.setEncryptionKey(privateKey)
        
    def setGcpSetting(self, gcpValue):
        try:
            if not self.appdataManager.getAppdataValue('centre','gcpSetting'):
                self.appdataManager.createAppdataElement('centre','gcpSetting',write=False)            
            self.appdataManager.setAppdataValue('centre','gcpSetting',str(gcpValue))
        except BaseException, e:
            print str(e)
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
        self.gcpActive = gcpValue
        
    def getGcpSetting(self):
        if 'gcp' not in psc.toolBarApplications:
            return False
        if not self.appdataManager.getAppdataValue('centre','gcpSetting'):
            self.appdataManager.createAppdataElement('centre','gcpSetting',write=False)            
            self.appdataManager.setAppdataValue('centre','gcpSetting','False')
        gcpSetting = self.appdataManager.getAppdataValue('centre','gcpSetting')        
        result = False
        if gcpSetting == 'True':
            result = True
        return result
        
    def setTranslationModeSetting(self, translationModeValue):
        try:
            if not self.appdataManager.getAppdataValue('centre','translationMode'):
                self.appdataManager.createAppdataElement('centre','translationMode',write=False)            
            self.appdataManager.setAppdataValue('centre','translationMode',str(translationModeValue))
        except BaseException, e:
            print str(e)
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
        self.translationMode = translationModeValue
        
    def getTranslationModeSetting(self):
        if not self.appdataManager.getAppdataValue('centre','translationMode'):
            self.appdataManager.createAppdataElement('centre','translationMode',write=False)            
            self.appdataManager.setAppdataValue('centre','translationMode','False')
        translationMode = self.appdataManager.getAppdataValue('centre','translationMode')        
        result = False
        if translationMode == 'True':
            result = True
        return result
        

    def checkActivation(self):
        try:
            self.centrecode = self.appdataManager.getAppdataValue('centre','centreCode')
            self.encryptionKey = self.appdataManager.getAppdataValue('centre','privateKey')
        except:
            return False
        if self.centrecode in [None, '', 'None'] or not self.encryptionKey:
            return False
        if self.encryptionKey:
            self.setEncryptionKey(self.encryptionKey)
        return True

    def reactivate(self,centreCode):
        self.appdataManager.setAppdataValue('centre','centreCode',centreCode)

    def deactivate(self):
        self.encryptionKey = None
        self.centrecode = None
        self.appdataManager.setAppdataValue('centre','centreCode','')

    def generatePrivateKey(self):
        return ''.join([random.choice(string.ascii_letters+string.digits) for i in range(32)])

    def saveProxySettings(self, address, username='', password=''):
        self.appdataManager.createAppdataElement('','network',write=False)
        self.appdataManager.createAppdataElement('network','proxy',write=False)
        self.appdataManager.setAppdataValue('network/proxy','address',address,write=False)
        self.appdataManager.setAppdataValue('network/proxy','username',username,write=False)
        self.appdataManager.setAppdataValue('network/proxy','password',password,write=True)

    def createAppdata(self, centrecode):

        self.centrecode = centrecode
        #TODO: clientkey here is hardcoded for a single installation per center.
        #For more than one client per center must check last client key and generate one accordingly
        #TODO: this should be generated on the fly for the first client, and copied from the first client for the other clients
        self.setEncryptionKey(self.generatePrivateKey())

        self.appdataManager.createAppdata(self.dataPath)

        currentDate = self.getDate()

        self.appdataManager.setAppdataValue('centre','centreCode',self.centrecode,write=False)
        # TODO: create a set of country-countrycode in a outer file
        countryCode = centrecode[:2]
        countryCodes = {'IT':'Italiano', 'EN':'English', 'HU':'Magyar', 'PO':'Polski'}
        
        self.userLanguage = 'English'
        if countryCode in countryCodes:
            self.userLanguage = countryCodes[countryCode]
        self.appdataManager.setAppdataValue('centre','privateKey',self.encryptionKey,write=False)
        self.appdataManager.setAppdataValue('centre','userLanguage', self.userLanguage, write=False)
        
        crfsEl = etree.Element('crfs')
        crfEl = etree.SubElement(crfsEl,'crf')
        crfEl.set('name',psc.coreCrfName)
        if self.testing:
            if 'petals' in psc.toolBarApplications:
                for petalName in ['infection', 'cch', 'crimyne2', 'start', 'compact2', 'tiss28', 'neuro', 'test']:
                    crfEl = etree.SubElement(crfsEl,'crf')
                    crfEl.set('name', petalName)
                    crfEl.set('minValidDate','2010-01-01')
            else:
                pass

        self.appdataManager.setAppdataElement('centre',crfsEl,write=False)

        usersEl = etree.Element('users')
        
        adminEl = self.createNewUserElement('Admin','Admin','admin','admin', self.userLanguage,'4','1')
        usersEl.append(adminEl)
        self.appdataManager.setAppdataElement('centre',usersEl)
        
        #self.setAppdataPersonalizations(['<attribute description="X" dataType="float" name="value" name="core.firstName.firstName"/>','<codingSetValue description="X" positionWeight="0" value="Ciccio" name="core.sexCodification.ciccio"/>'])
        if self.testing:
            userEl = self.createNewUserElement('A','A','a','o', self.userLanguage,'3','1')
            userEl.set('firstPasswordChanged','1')
            usersEl.append(userEl)
            #self.appdataManager.setAppdataElement('centre',usersEl)
            #self.setAppdataPersonalizations(['<codingSetValue description="X" positionWeight="0" value="sala uno" name="core.operatingTheaterCustomCodification.uno"/>','<codingSetValue description="X" positionWeight="0" value="sala due" name="core.operatingTheaterCustomCodification.due"/>'])

    def getAppdataCrfNames(self):
        crfsEl = self.appdataManager.getAppdataElement('centre/crfs')
        crfNames = [el.get('name') for el in crfsEl if el.get('name') not in (None,"")]
        crfNames = list(set(crfNames))
        return crfNames

    def getAppdataPersonalizations(self):
        personalizationsEl = self.appdataManager.getAppdataElement('centre/personalizations')
        return personalizationsEl

    def setAppdataPersonalizations(self,personalizations):
        personalizationsEl = etree.Element('personalizations')
        for personalization in personalizations:
            print 'PERSONALIZATION TO BE SET:', personalization
            personalizationsEl.append(etree.fromstring(personalization))
        personalizationsEl = self.appdataManager.setAppdataElement('centre',personalizationsEl)
        

    def getAppdataCrfNamesForDate(self,admissionDate):
        crfsEl = self.appdataManager.getAppdataElement('centre/crfs')
        crfNames = []
        for el in crfsEl:
            if el.get('name') in (None,""):
                continue
            name = el.get('name')
            if name == psc.coreCrfName:
                crfNames.append(name)
                continue
            minValidDate = el.get('minValidDate')
            maxValidDate = el.get('maxValidDate')
            if not minValidDate:
                continue
            if not admissionDate:
                print 'ERROR: in getAppdataCrfNamesForDate: admissionDate not available'
                continue
            if self.areDatesSorted(minValidDate,admissionDate,True) and not maxValidDate:
                crfNames.append(name)
            elif self.areDatesSorted(minValidDate,admissionDate,True) and self.areDatesSorted(admissionDate,maxValidDate,False):
                crfNames.append(name)
        return crfNames

    def hasUsers(self):
        usersEl = self.appdataManager.getAppdataElement('centre/users')
        if usersEl == None or len(usersEl.getchildren()) == 0:
            return False
        return True

    def loadUsers(self):
        usersEl = self.appdataManager.getAppdataElement('centre/users')
        if usersEl == None:
            return None
        users = [{'userKey':el.get('userKey'),'name':el.get('name'),'surname':el.get('surname')} for el in usersEl]
        return users
  
    def generateRandomPasswordWithSeed(self):
        import datetime
        utcnow = datetime.datetime.utcnow()
        h = utcnow.hour * utcnow.month * utcnow.year
        n = 1067347
        seed = h * n
        import random
        random.seed(seed)
        password = random.randint(1, 1000000)
        return str(password)
  
    def doLogin(self, username, password):
        self.shouldAnonymizeData = False
        if username == 'ASSISTENZA' and password == self.generateRandomPasswordWithSeed():
            self.shouldAnonymizeData = True
            userDict = {'userKey':'ASSISTENZA','name':'giviti','surname':'giviti','username':'ASSISTENZA','password':'danidani','flgEnabled':1,'firstPasswordChanged':1,'userType':4,'passwordExpiryDate':None,'inputDate':None,'defaultLanguage':'Italiano'}
        else:
            el = self.appdataManager.getAppdataElementWithAttributes('centre/users/user',('username','password'),(username,password))

            if el == None:
                el = self.appdataManager.getAppdataElementWithAttributes('centre/users/user',('username','secondaryPassword'),(username,password))
                if el != None:
                    el.attrib.pop('secondaryPassword')
                    el.set('firstPasswordChanged','0')
                    self.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,el)

            if el == None or el.get('enabled') == '0':
                return {'userType': psc.USER_NO_AUTH} 

            userDict = {'userKey':el.get('userKey'),'name':el.get('name'),'surname':el.get('surname'),'username':el.get('username'),'password':el.get('password'),'flgEnabled':int(el.get('enabled')),'firstPasswordChanged':int(el.get('firstPasswordChanged')),'userType':int(el.get('userType')),'passwordExpiryDate':el.get('passwordExpiryDate'),'inputDate':el.get('inputDate'),'defaultLanguage':el.get('defaultLanguage')}
        self.inputUserKey = userDict['userKey']
        return userDict
        
    def setUser(self, loginResult):
        self.username = loginResult['username']
        self.userType = loginResult['userType']
        self.passwordExpiryDate = loginResult['passwordExpiryDate']
        self.userLanguage = loginResult['defaultLanguage']
        if not self.userLanguage:
            self.userLanguage = 'English'
        self.loadAppTranslations(self.userLanguage)
        if self.userLanguage != 'English':
            self.loadAppTranslations('English')
    
    def doLogout(self):
        if self.dischargeLetterModelFolder:
            self.closeLetterModelFolder()
        self.dischargeLetterModelFolder = ''
        self.dischargeLetterMasterModelFolder = ''
        self.cleanDischargeLetterDirectory()
        self.initializeQuickFilters()
        self.initializeFilters()
   
    def doControlPwd(self, username, password):
        """controlla se la password inserita per il cambio password e' corretta """
        el = self.appdataManager.getAppdataElementWithAttributes('centre/users/user',('username','password'),(username,password))
        if el == None:
            return False
        return True

    def createAdminSecondaryPassword(self):
        secondaryPassword = ''.join([random.choice(string.ascii_letters+string.digits) for i in range(12)])
        username = 'admin'
        userEl = self.appdataManager.getAppdataElementWithAttribute('centre/users/user','username',username)
        if userEl == None:
            print 'ERROR: could not find any user with username %s' % username
            return False
        userEl.set('secondaryPassword',secondaryPassword)
        self.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,userEl)
        return secondaryPassword

    def deleteAdminSecondaryPassword(self):
        secondaryPassword = ''.join([random.choice(string.ascii_letters+string.digits) for i in range(12)])
        username = 'admin'
        userEl = self.appdataManager.getAppdataElementWithAttribute('centre/users/user','username',username)
        if userEl == None:
            print 'ERROR: could not find any user with username %s' % username
            return False
        userEl.set('secondaryPassword',secondaryPassword)
        self.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,userEl)
        return secondaryPassword

    def doSavePassword(self, username, password, name='', surname='', firstPasswordChanged='1'):
        """saves the new password for this user"""
        if password in (None,""):
            print 'ERROR: empty password'
            return False
        userEl = self.appdataManager.getAppdataElementWithAttribute('centre/users/user','username',username)
        if userEl == None:
            print 'ERROR: could not find any user with username %s' % username
            return False
        userEl.set('password',password)
        if name:
            userEl.set('name',name)
        if surname:
            userEl.set('surname',surname)
        userEl.set('firstPasswordChanged', firstPasswordChanged)
        self.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,userEl)
        return True

    def doSaveUserLang(self, username, language):
        """saves the new language settings for this user"""
        if language == None:
            return False
        if self.userLanguage != language:
            self.userLanguage = language
            self.loadAppTranslations(self.userLanguage)
            self.crfData.initialize()
        userEl = self.appdataManager.getAppdataElementWithAttribute('centre/users/user','username',username)
        if userEl == None:
            print 'ERROR: could not find any user with username %s' % username
            return False
        userEl.set('defaultLanguage',language)
        self.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,userEl)
        return True

    def getUsers(self):
        usersEl = self.appdataManager.getAppdataElement('centre/users')
        users = [{'userKey':el.get('userKey'),'name':el.get('name'),'surname':el.get('surname'),'username':el.get('username'),'flgEnabled':int(el.get('enabled')),'userType':int(el.get('userType')),'language':el.get('defaultLanguage')} for el in usersEl]
        return users
        
    def getGcpUserDataFromUserKey(self, userKey):
        users = self.getUsers()
        userData = psc.gcpUserData
        user = [el for el in users if el['userKey'] == userKey]
        if not user:
            return userKey
        user = user[0]
        return  '%s (%s)' % (user['username'], ' '.join([user[userDataName] for userDataName in userData if userDataName != 'username']))
            
    
    def updateUserByAdmin(self, userKey, name, surname, flgEnabled, userType, language, password):
        userEl = self.appdataManager.getAppdataElementWithAttribute('centre/users/user','userKey',userKey)
        if userEl == None:
            print "ERROR: no user with userKey %s" % userKey
            return False
        userEl.set('userType',str(userType))
        if name:
            userEl.set('name',name)
        if surname:
            userEl.set('surname',surname)
        userEl.set('enabled',str(flgEnabled))
        userEl.set('defaultLanguage',language)
        if self.username == userEl.get('username') and self.userLanguage != language:
            self.crfData.initialize()
            self.userLanguage = language
        if password not in (None,""):
            userEl.set('password',password)
            if self.username == userEl.get('username'):
                userEl.set('firstPasswordChanged','1')
            else:
                userEl.set('firstPasswordChanged','0')
        self.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','userKey',userKey,userEl)
        return True
 
    def createNewUserElement(self, surname, name, username, password, language, userType, enabled):
        currentDate = self.getDate()
        el = etree.Element('user')
        el.set('name',name)
        el.set('surname',surname)
        el.set('username',username)
        el.set('defaultLanguage',language)
        el.set('userType',str(userType))
        el.set('enabled',str(enabled))
        el.set('password',password)
        el.set('inputDate',currentDate)
        userEls = self.appdataManager.getAppdataElements('centre/users/user')
        if not userEls:
            localId = 1
        else:
            localId = 1 + max([int(userEl.get('localId')) for userEl in userEls if userEl != None and userEl.get('localId') != None and userEl.get('localId').isdigit() == True])
        el.set('localId','%d' % localId)
        el.set('userKey','%s-%d' % (self.centrecode,localId))
        el.set('passwordExpiryDate','1970-01-01')
        #TODO: not used
        el.set('lastAccessDate',currentDate)
        el.set('firstPasswordChanged','0')
        return el
    
    def saveNewUser(self, surname, name, username, lang, userType, enabled, password):
        userEl = self.createNewUserElement(surname,name,username,password,lang,userType,enabled)
        self.appdataManager.appendAppdataElement('centre/users',userEl)
        return True
    
    def userExists(self, username):
        el = self.appdataManager.getAppdataElementWithAttribute('centre/users/user','username',username)
        if el == None:
            return False
        return True
    
    def saveClientConfig(self):
        pass
   
    def createAdmission(self, prevAdmission='', newPatient=False, admissionDate=None, basedata=None, acquireLock=True):

        newid = self.currentNewUUID
        if not newid:
            newid = self.jsonStore.getNewUUID('admission')
        admissionKey = "A-%s-%s" % (self.centrecode, newid)
        readmissionKey = prevAdmission

        if acquireLock:
            result = self.jsonStore.acquireLock(admissionKey,self.bulletinClient.clientKey)
            if result == False:
                return False

        self.beginCriticalSection()

        self.loadCrfs(admissionDate)

        self.evaluator.cleanCache()
        self.dataSession = DataSession(self)
        if newPatient:
            newid = self.jsonStore.getNewUUID('patient')
            self.dataSession.setPatientKey("P-%s-%s" % (self.centrecode, newid))
        else:
            self.dataSession.setPatientKey(basedata['patientKey'])
        self.dataSession.setAdmissionKey(admissionKey)
        
        previousAdmission = self.jsonStore.search({'admissionKey':prevAdmission, 'activeAdmission' : True})
        if previousAdmission:
            previousAdmission = previousAdmission[0]
        if 'readmissionKey' in previousAdmission and previousAdmission['readmissionKey']:
            prevAdmission = previousAdmission['readmissionKey']
        self.dataSession.setReadmissionKey(prevAdmission)
        result = self.jsonStore.acquireLock(admissionKey,self.bulletinClient.clientKey)

        ###############################################################################################################
        #TODO JSON: if we save basedata, we don't need to build the empty JSON at all! Just set the info on datasession
        ###############################################################################################################
        self.changedAttributes = {}
        self.confirmResult = {}
        self.saveBasedata(basedata)
        self.endCriticalSection()

        self.notificationCenter.postNotification('AdmissionsHaveBeenUpdated',self)
        self.bulletinClient.postNotificationOnBulletin('AdmissionsHaveBeenUpdated')
        if prevAdmission:
            #we should set stuff like comorbidities, inherited only the first time
            inheritedClassNamesForICUReadmissions = psc.inheritedClassNamesForICUReadmissions
            from psevaluator import years
            age = years(admissionDate, basedata['birthDate'])
            if age < 16:
                inheritedClassNamesForICUReadmissions = [el for el in inheritedClassNamesForICUReadmissions if el not in psc.pediatricExceptions]
            admissionData = self.jsonStore.search({'admissionKey':prevAdmission, 'activeAdmission' : True})
            admissionData = admissionData[0]
            admissionData = self.dataSession.decryptJSON(admissionData)
            for inheritedClassName in inheritedClassNamesForICUReadmissions:
                crfName, className, attributeName = inheritedClassName.split('.')
                classValue = self.dataSession.getValuesFromJSON(admissionData, crfName, className, attributeName)
                if type(classValue) is list and not self.crfData.getPropertyForAttribute(crfName, className, attributeName, 'multiInstance'):
                    if classValue:
                        classValue = classValue[0]
                if classValue:
                    self.dataSession.updateData(crfName,className,1,attributeName,classValue)
        elif not newPatient:
            from psevaluator import years
            age = years(admissionDate, basedata['birthDate'])
            inheritedClassNamesForHospitalReadmissions = psc.inheritedClassNamesForHospitalReadmissions            
            if age < 16:
                inheritedClassNamesForHospitalReadmissions = [el for el in inheritedClassNamesForHospitalReadmissions if el not in psc.pediatricExceptions]
            admissionData = self.jsonStore.search({'patientKey' : self.dataSession.patientKey, 'activeAdmission' : True})
            selectedAdmissionData = None
            for hospitalAdmission in admissionData:
                if hospitalAdmission['admissionKey'] == admissionKey:
                    continue
                selectedAdmissionData = hospitalAdmission
                break
            admissionData = selectedAdmissionData
            admissionData = self.dataSession.decryptJSON(admissionData)
            for inheritedClassName in inheritedClassNamesForHospitalReadmissions:
                crfName, className, attributeName = inheritedClassName.split('.')
                classValue = self.dataSession.getValuesFromJSON(admissionData, crfName, className, attributeName)
                if type(classValue) is list and not self.crfData.getPropertyForAttribute(crfName, className, attributeName, 'multiInstance'):
                    classValue = classValue[0]
                if classValue:
                    self.dataSession.updateData(crfName,className,1,attributeName,classValue)
        self.loadAdmission(admissionKey)
       
        self.dataSession.modified = False
        if prevAdmission:
            self.dataSession.modified = True
        self.dischargeLetterFolder = ''
        self.dischargeLetterModelFolder = ''

        return True
        
    def checkFaultTolleranceForReadmissionsNames(self, patientLastName, patientFirstName, candidateLastName, candidateFirstName):
        #TODO: improve method efficiency
        if patientLastName.lower() == candidateLastName.lower() and patientFirstName.lower() == candidateFirstName.lower():
            return True
        return False
        
    def getCandidatesForReadmission(self, basedata, sexMatching = True, tolerance = True):
        candidates = []
        if 'readmission' not in psc.toolBarApplications:
            return candidates
        #if tolerance:
        candidatesHaveBeenRemoved = False
        if type(basedata['lastName']) is int:
            basedata['lastName'] = str(basedata['lastName'])
        if type(basedata['lastName']) is int:
            basedata['firstName'] = str(basedata['firstName'])
        candidatesList = self.getAllActiveAdmissionsData()
        for candidate in candidatesList:
            if type(candidate[psc.lastNameAttr]) is int:
                candidate[psc.lastNameAttr] = str(candidate[psc.lastNameAttr])
            if type(candidate[psc.firstNameAttr]) is int:
                candidate[psc.firstNameAttr] = str(candidate[psc.firstNameAttr])
            
        candidates = [xx for xx in candidatesList if self.checkFaultTolleranceForReadmissionsNames(xx[psc.lastNameAttr].strip(), xx[psc.firstNameAttr].strip(), basedata['lastName'].strip(), basedata['firstName'].strip()) and xx[psc.birthDateAttr] == basedata['birthDate']]
        removingCandidatesList = []
        if candidates:
            for candidate in candidates:
                if not candidate['core.icuOutcome.value'] and not candidate['core.icuDisDate.value'] and not candidate['core.hospOutcome.value'] and not candidate['core.hospDisDate.value'] and not candidate['core.hospOutcomeIT.value']:
                    #excludes candidates still in ICU
                    candidatesHaveBeenRemoved = True
                    removingCandidatesList.append(candidate)
                    continue
                #skipping dead candidates
                if candidate['core.icuOutcome.value'] and candidate['core.icuOutcome.value'] == 'core.icuOutCodification.dead':
                    candidatesHaveBeenRemoved = True
                    removingCandidatesList.append(candidate)
                    continue
                if candidate['core.hospOutcomeIT.value'] and candidate['core.hospOutcomeIT.value'] == 'core.hospOutCodificationIT.hospDead':
                    candidatesHaveBeenRemoved = True
                    removingCandidatesList.append(candidate)
                    continue
                if candidate['core.hospOutcome.value'] and candidate['core.hospOutcome.value'] == 'core.hospOutCodification.hospDead':
                    candidatesHaveBeenRemoved = True
                    removingCandidatesList.append(candidate)
                    continue
                admissionDate = basedata['admissionDate']
                #CHECKING DATES
                if admissionDate < candidate['core.icuDisDate.value'] or admissionDate < candidate['core.hospAdmDate.value'] or admissionDate < candidate['core.icuAdmDate.icuAdmDate']:
                    candidatesHaveBeenRemoved = True
                    removingCandidatesList.append(candidate)
                    continue
            #removing selected candidates
            for element in removingCandidatesList:
                candidates.remove(element)
                
            if sexMatching:
                #candidates = [xx for xx in candidates if xx[psc.sexAttr] == basedata['sex']]
                if not basedata['sex']:
                    return None
                else:
                    #candidates = [xx for xx in candidates if xx[psc.sexAttr]]
                    for candidate in candidates:
                        if candidate[psc.sexAttr] != basedata['sex'] and not candidate[psc.sexAttr] == None:
                            candidates.remove(candidate)
                            candidatesHaveBeenRemoved = True
        return candidates, candidatesHaveBeenRemoved
       
    def closeAdmission(self, crfs=None):
        self.beginCriticalSection()
        for crfName in crfs:
            self.dataSession.setAdmissionStatus('5',crfName)
        self.saveData(False,True,True,False)

        self.notificationCenter.postNotification("BasedataHasBeenUpdated",self)
        self.notificationCenter.postNotification("StatusHasBeenUpdated",self)
        self.endCriticalSection()
        return True
        
        
    ######## Deleted patient ###########
    def getAllAdmissionsDataDeleted(self):
        self.beginCriticalSection()

        unAdmissondata = self.jsonStore.search_ids({'activeAdmission':False})

        positions = []
       
        positions.append('crfs.core.lastName.lastName')
        positions.append('crfs.core.firstName.firstName')
        positions.append('crfs.core.icuAdmDate.icuAdmDate')
        positions.append('crfs.core.birthDate.birthDate')
        positions.append('patientKey')
        positions.append('admissionKey')
        
        values = self.jsonStore.load_value_list(unAdmissondata,positions)
        self.endCriticalSection()
        return values 
    
    def RestoreDeleteAdmission(self):
        # if self.isParentReadmission():
            # return False

        self.beginCriticalSection()

        self.dataSession.activeAdmission = True
        self.saveData(True,False,True,False)

        self.endCriticalSection()

        return True    
        
    def reopenAdmission(self, crfs=None):
        self.beginCriticalSection()
        for crfName in crfs:
            self.dataSession.setAdmissionStatus('2',crfName)
            self.dataSession.evaluateGlobals(updateStatus=False)
            if self.evalErrors(crfName) or self.evalUnacceptedWarnings(crfName):
                self.dataSession.setAdmissionStatus('1')
        self.saveData(False,True,False,False)

        self.notificationCenter.postNotification("BasedataHasBeenUpdated",self)
        self.notificationCenter.postNotification("StatusHasBeenUpdated",self)
        self.evaluator.cleanCache()
        self.endCriticalSection()
        return True

    def deleteAdmission(self):
        if self.isParentReadmission():
            return False

        self.beginCriticalSection()

        self.dataSession.activeAdmission = False
        self.saveData(False,False,False,False)

        self.endCriticalSection()

        return True    
        
    def isFilled(self, externalKey, attributeId, patient=False):
        pass    
   
    def saveBasedata(self, basedata):

        #TODO JSON: change this, just create the JSON and save it (it's important to save to notify other users about the patient).

        #TODO MERGE remove if, adopt else and integrate readmission code.
        if psc.appName == 'prosafe':
            firstname = psc.firstNameAttr.split('.')
            lastname = psc.lastNameAttr.split('.')
            dob = psc.birthDateAttr.split('.')
            admissiondate = psc.admissionDateAttr.split('.')
            sex = psc.sexAttr.split('.')

            #FIXME: really ugly
            names = {'firstname':'firstName','lastname':'lastName','dob':'birthDate','admissiondate':'admissionDate','sex':'sex'}
            for key in names:
                exec("self.dataSession.updateData(%s[0],%s[1],%d,%s[2],basedata['%s'])" % (key,key,1,key,names[key]))

            if psc.appName == 'prosafe':
                if 'prevAdmissionKey' in basedata and basedata['prevAdmissionKey']:
                    activeAdmissionsData = self.getAllActiveAdmissionsData()
                    parentAdmissionData = [el for el in activeAdmissionsData if el['admissionKey'] == basedata['prevAdmissionKey']][0]
                    fullAttributeNamesForReadmissionList = ['core.hospDisDate.value', 'core.hospOutcome.value', 'core.hospOutcomeIT.value', 'core.hospOutcomeLatest.value', 'core.hospOutTransf.value', 'core.hospAdmDate.value']
                    for fullAttributeName in fullAttributeNamesForReadmissionList:
                        if fullAttributeName not in parentAdmissionData:
                            continue
                        crfName, className, attributeName = self.crfData.splitAttributeName(fullAttributeName)
                        # Limitation to single instance classes
                        self.dataSession.updateData(crfName,className,1,attributeName,parentAdmissionData[fullAttributeName])

            self.updateStatus(computeOnly=True)
            self.changedAttributes = {}
            self.confirmResult = {}
            self.saveData(evaluateErrors=False,notify=False,updateStatus=False,firstSave=True)

        else:
            for key in psc.basedataAttributeDict:
                attributeName = psc.basedataAttributeDict[key]
                crfName, className, attributeName = attributeName.split('.')
                self.dataSession.updateData(crfName,className,1,attributeName,basedata[key])
                
            self.updateStatus(computeOnly=True)
            self.saveData(False,False,False)

    def getCurrentBasedata(self):
        if not self.dataSession:
            return None
        basedata = {}
        for key in psc.basedataAttributeDict:
            crfName, className, attributeName = self.crfData.splitAttributeName(psc.basedataAttributeDict[key])
            values = self.dataSession.getAttributeValuesForClass(crfName,className,attributeName)
            if not values:
                value = ""
            else:
                value = values[0]
            basedata[key] = value
        return basedata

    def loadAdmission(self, admissionKey, acquireLock=True, dump=None):

        
        print 'LOADING ADMISSION', admissionKey
        self.beginCriticalSection()
        self.evaluator.cleanCache()

        self.unsavedStatus = False
        if not dump:
            admissionData = self.jsonStore.search({'admissionKey':admissionKey})
        else:
            import base64
            import gzip
            from json import loads
            admissionData = loads(gzip.zlib.decompress(base64.b64decode(dump)))
            
            if '_type' in admissionData.keys() and admissionData['_type'] == 'UUIDS':
                return False
            if 'admissionKey' in admissionData.keys():
                admissionKey = admissionData['admissionKey']
            else:
                return False
            admissionData = [admissionData]
        if acquireLock:
            result = self.jsonStore.acquireLock(admissionKey,self.bulletinClient.clientKey)

            if result == False:
                return False
        self.dataSession = DataSession(self)
        self.dataSession.setAdmissionKey(admissionKey)
        
        if not admissionData:
            raise BaseException("Error: no admission data in store")

        admissionData = admissionData[0]

        admissionData = self.dataSession.decryptJSON(admissionData)
        crfStatusDict = eval(admissionData['crfStatusDict'])
        if self.dataSession.readmissionKey:
            return False
        for crfName in crfStatusDict.keys():
            self.dataSession.setAdmissionStatus(crfStatusDict[crfName], crfName)
        #pprint.pprint(admissionData,sys.stdout,2,2)

        flgStatusFive = admissionData['crfs'][psc.coreCrfName]['crfStatus'] == '5'

        self.storedCrfVersions = eval(admissionData['crfVersionDict'])
        if flgStatusFive:
            self.reopenAdmission(self.crfData.getCrfNames())
        
        self.dataSession.setPatientKey(admissionData['patientKey'])

        admissionDateAttrCrfName, admissionDateAttrClassName, admissionDateAttrAttributeName = psc.admissionDateAttr.split('.')
        #admissionDateAttr
        admissionDate = self.dataSession.getValueFromJSON(admissionData, admissionDateAttrCrfName, admissionDateAttrClassName, admissionDateAttrAttributeName)
        self.dataSession.ignoreStatusForUpdate = True
        
        self.loadCrfs(admissionDate)

        #TODO: PERSONALIZATIONS SHOULD BE STORED AT THE ROOT OF ADMISSIONS IN JSONDB, RATHER THAN IN A CLASS
        storedPersonalizations = self.dataSession.getAttributeValuesForClass(psc.coreCrfName,'personalizations','personalizations')
        self.crfData.mergePersonalizations(storedPersonalizations)

        self.dataSession.loadFromJSON(admissionData)

        #self.objectCodesOnLoad = set(self.dataSession.getAllObjectCodes())

        #TODO: remove once all admissions have been resaved
        #self.dataSession.unregisterOrphanClassInstances()
        #self.dataSession.cleanUpDirtyObjectContainers()
        #TODO: end remove
        self.dataSession.buildObjectCodesToContainers()

        self.dataSession.removeInvalidErrorObjects()

        self.dataSession.evaluateCalculatedSinglePass()
        #self.dataSession.evaluateGlobals(updateStatus=False)
        self.dataSession.evaluateGlobals(updateStatus=True)
        
        if flgStatusFive:
            #set back admission to status 5
            self.closeAdmission(self.crfData.getCrfNames())
            
        # This is to avoid prompting for save without modifications.
        #self.dataSession.resetModifiedObjects()
        #self.dataSession.resetModifiedObjectsAttributes()
        self.dataSession.modified = False

        self.dataSession.ignoreStatusForUpdate = False

        self.dischargeLetterFolder = ''
        self.dischargeLetterModelFolder = ''


        currentAttributePersonalizations = self.crfData.getAttributePersonalizations()
        currentCodingSetValuePersonalizations = self.crfData.getCodingSetValuePersonalizations()
        #self.dataSession.updateDataNoNotify(psc.coreCrfName,'personalizations',1,'attributes',currentAttributePersonalizations,evaluateGlobals=False)
        #self.dataSession.updateDataNoNotify(psc.coreCrfName,'personalizations',1,'codingSetValues',currentCodingSetValuePersonalizations,evaluateGlobals=False)
        print 'patientKey', self.dataSession.patientKey
        print 'admissionKey', self.dataSession.admissionKey
        print 'readmissionKey', self.dataSession.readmissionKey

        self.endCriticalSection()
        return True

    def exitAdmission(self, releaseLock=True):
        if self.dischargeLetterFolder:
            self.closeLetterFolder()
        self.dischargeLetterFolder = ''
        self.dischargeLetterModelFolder = ''
        self.dischargeLetterMasterModelFolder = ''
        self.cleanDischargeLetterDirectory()

        self.crfData.removePersonalizations()
        readmissionData = None
        #shall we look for readmission cases only with modified dataSession?

        if self.dataSession.modified and 'readmission' in psc.toolBarApplications:
            admissionKeySet = []
            self.dataSession.getAttributeValuesForClass('core', 'age', 'value')
            age = self.dataSession.getAttributeValuesForClass('core', 'age', 'value')
            if age and type(age) == list:
                age = age[0]
            #updating data only for readmitted patients and their previous/next admissions
            if self.dataSession.readmissionKey:
                #encrypted_data = readmissionDataSession.makeJSON(encrypted=True)
                #data = readmissionDataSession.makeJSON()
                admissionKeySet.append(self.dataSession.readmissionKey)
                data_ids = self.jsonStore.search_ids({'readmissionKey': self.dataSession.readmissionKey, 'activeAdmission' : True})            
            else:
                data_ids = self.jsonStore.search_ids({'readmissionKey':self.dataSession.admissionKey, 'activeAdmission' : True})
            for id in data_ids:
                admissionKeyForKeySet = self.jsonStore.load_values(id, 'admissionKey')
                if admissionKeyForKeySet[0] not in [self.dataSession.admissionKey, self.dataSession.readmissionKey]:
                    admissionKeySet.append(admissionKeyForKeySet[0])
            linkedClassNamesForICUReadmissions = psc.linkedClassNamesForICUReadmissions
            if age < 16:
                linkedClassNamesForICUReadmissions = [el for el in psc.linkedClassNamesForICUReadmissions if el not in psc.pediatricExceptions]                
            self.updatedRelatedAdmissionsFromKeySet(admissionKeySet, linkedClassNamesForICUReadmissions)   
            admissionKeySet = []
            #updating data only for admissions with same patient key
            data_ids = self.jsonStore.search_ids({'patientKey':self.dataSession.patientKey, 'activeAdmission' : True})
            for id in data_ids:
                admissionKeyForKeySet = self.jsonStore.load_values(id, 'admissionKey')
                if admissionKeyForKeySet[0] not in [self.dataSession.admissionKey, self.dataSession.readmissionKey]:
                    admissionKeySet.append(admissionKeyForKeySet[0])
            inheritedClassNamesForHospitalReadmissions = psc.inheritedClassNamesForHospitalReadmissions
            if age < 16:
                inheritedClassNamesForHospitalReadmissions = [el for el in psc.inheritedClassNamesForHospitalReadmissions if el not in psc.pediatricExceptions]
            self.updatedRelatedAdmissionsFromKeySet(admissionKeySet, inheritedClassNamesForHospitalReadmissions)   
        
        admissionKey = self.dataSession.admissionKey
        self.jsonStore.releaseLock(admissionKey,self.bulletinClient.clientKey)
        self.dataSession = None
        self.objectCodesOnLoad = set()
        self.confirmResult = {}
        self.changedAttributes = {}
        self.evaluator.cleanCache()
        
    def updatedRelatedAdmissionsFromKeySet(self, admissionKeySet, classNamesToUpdate):
        #should we optimize retrieving current admission data only once?
        #FIX ME: temporary skipping metadata
        for admissionKey in admissionKeySet:
            print 'Updating admissionKey no. %s due to readmission link' % admissionKey
            readmissionData = self.jsonStore.search({'admissionKey': admissionKey, 'activeAdmission' : True})
            readmissionData = readmissionData[0]
            
            #linkedClassNamesForICUReadmissions = psc.linkedClassNamesForICUReadmissions
            #should acquire lock even on parent admission
            result = self.jsonStore.acquireLock(admissionKey,self.bulletinClient.clientKey)
            #readmissionDataSession.loadFromJSON(readmissionData)
            defaultKeyListForMetadata = [u'userKey', u'crfVersion', u'inputDate']
            defaultKeyListForMetadata.sort()
            for linkedClassName in classNamesToUpdate:
                crfName, className, attributeName = linkedClassName.split('.')
                classValue = self.dataSession.getAttributeValuesForClass(crfName, className, attributeName)
                dataStorage = self.crfData.getPropertyForClass(crfName,className,'dataStorage')
                #adding new record
                if className not in readmissionData['crfs'][crfName] or not readmissionData['crfs'][crfName][className]['#1'][0] or attributeName not in readmissionData['crfs'][crfName][className]['#1'][0]:
                    if className not in readmissionData['crfs'][crfName] or not readmissionData['crfs'][crfName][className]['#1'][0]:
                        readmissionData['crfs'][crfName][className] = dict()
                        readmissionData['crfs'][crfName][className]['#1'] = []
                    valueList = []
                    for value in classValue:
                        someValue = value
                        if dataStorage == 'patient':
                            someValue = self.encryptDecryptValue(value, 'encrypt', dataStorage)
                        print 'encrypting inherited value', value, someValue
                        valueList.append(someValue)
                    valueDict = dict()
                    metaData = self.dataSession.getMetaJSON(crfName)
                    if dataStorage == 'patient':
                        metaData["encryption"] = self.encryptDecryptValue(self.encryptionKey,'encrypt',dataStorage)
                    valueDict[attributeName] = [valueList, metaData]
                    if not readmissionData['crfs'][crfName][className]['#1']:
                        readmissionData['crfs'][crfName][className]['#1'].append(valueDict)
                        readmissionData['crfs'][crfName][className]['#1'].append(metaData)
                    else:
                        for dictionary in readmissionData['crfs'][crfName][className]['#1']:
                            dictKeys = dictionary.keys()
                            dictKeys.sort()
                            if dictKeys == defaultKeyListForMetadata:
                                dictionary = metaData
                            else:
                                dictionary.update(valueDict)
                    continue
                    
                    
                #updating existing record
                position = -1
                for element in readmissionData['crfs'][crfName][className]['#1']:
                    position += 1
                    sortedAttributeNameKeys = element.keys()
                    sortedAttributeNameKeys.sort()
                    if sortedAttributeNameKeys == defaultKeyListForMetadata:
                        #FIX ME: temporary skipping metadata
                        continue
                    attributeElementPosition = 0
                    if attributeName not in readmissionData['crfs'][crfName][className]['#1'][position]:
                        continue
                    for attributeElement in readmissionData['crfs'][crfName][className]['#1'][position][attributeName]:
                        if type(attributeElement) == list:
                            readmissionData['crfs'][crfName][className]['#1'][position][attributeName][attributeElementPosition] = []
                            for value in classValue:
                                someValue = value
                                if dataStorage == 'patient':
                                    someValue = self.encryptDecryptValue(value, 'encrypt', dataStorage)
                                readmissionData['crfs'][crfName][className]['#1'][position][attributeName][attributeElementPosition].append(someValue)

            decryptedReadmissionData = self.dataSession.decryptJSON(readmissionData)
            self.jsonStore.update(readmissionData,entry_id=readmissionData['__id__'],indexed_entry=decryptedReadmissionData,indexed_keys=self.indexedKeys)
            self.jsonStore.releaseLock(admissionKey,self.bulletinClient.clientKey)
            
            #now we shall do something with readmissionData
        

    def getPatientKey(self, admissionKey):
        ids = self.jsonStore.search_ids({'admissionKey': admissionKey})
        if not ids:
            return None
        id_ = ids[0]
        return self.jsonStore.load_value(id_,'patientKey')

    def valueForEncryption(self,value):
        if value == None:
            return ''
        if value == True:
            return 1
        if value == False:
            return 0
        return value

    def encryptDecryptValue(self, inputValue, operation, internalKeyTable):
        self.cipher.initCTR()

        if operation == 'encrypt':
            value = self.valueForEncryption(inputValue)
            if type(value) == unicode:
                strvalue = value.encode('utf-8')
            else:
                strvalue = str(value)
            outputValue = strvalue
            if internalKeyTable == 'patient':
                strvalue = self.cipher.encryptCTR(strvalue)
            outputValue = base64.b64encode(strvalue)
        else:
            strvalue = str(inputValue)
            strvalue = base64.b64decode(inputValue)
            if internalKeyTable == 'patient':
                strvalue = self.cipher.decryptCTR(strvalue)
            try:
                value = strvalue.decode('utf-8')
            except:
                value = _("ENCRYPTED")
            outputValue = value
        return outputValue

    def encryptDecryptObjectsAttributes(self, objectsAttributes, operation='encrypt', discrepancies=None):
        if discrepancies is not None:
            discrepancies['objects'] = {}
            discrepancies['objectsAttributes'] = {}
        outputObjectsAttributes = []
        for objectAttribute in objectsAttributes:
            dataStorage = self.crfData.getPropertyForClass(objectAttribute['crfName'],objectAttribute['className'],'dataStorage')
            if not dataStorage:
                dataStorage = 'admission'
            classInfo = self.dataSession.getClassInfoForObjectCode(objectAttribute['objectCode'])
            if classInfo:
                for timeStamp in self.dataSession.getAllTimeStampsForClass(classInfo['crfName'],classInfo['className']):
                    if not self.dataSession.getObjectCode(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],timeStamp):
                        print 'PROBLEM DETECTED: attribute objectCode does not correspond to an actual objectCode. Ignoring attribute ',classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],timeStamp, objectAttribute['objectCode']
                        continue
                    externalKey = self.dataSession.getObjectExternalKey(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],timeStamp)
                    if not externalKey:
                        print 'NULL EXTERNAL KEY FOUND, FIXING'
                        if dataStorage == 'admission':
                            externalKey = self.dataSession.admissionKey
                        else:
                            externalKey = self.dataSession.patientKey
                        if discrepancies is not None:
                            discrepancies['objects'][objectAttribute['objectCode']] = {'externalKey':externalKey}
                    if dataStorage == 'patient' and externalKey[0] != 'P':
                        print 'DISCREPANCY P DETECTED for class %s, FIXING' % classInfo['className']
                        dataStorage = 'admission'
                        externalKey = self.dataSession.patientKey
                        if discrepancies is not None:
                            discrepancies['objects'][objectAttribute['objectCode']] = {'externalKey':externalKey}
                            discrepancies['objectsAttributes'][objectAttribute['localId']] = {'dataStorage':'patient', 'value':None}
                    elif dataStorage == 'admission' and externalKey[0] != 'A':
                        print 'DISCREPANCY A DETECTED for class %s, FIXING' % classInfo['className']
                        dataStorage = 'patient'
                        externalKey = self.dataSession.admissionKey
                        if discrepancies is not None:
                            discrepancies['objects'][objectAttribute['objectCode']] = {'externalKey':externalKey}
                            discrepancies['objectsAttributes'][objectAttribute['localId']] = {'dataStorage':'admission', 'value':None}
            self.cipher.initCTR()
            if operation == 'encrypt':
                value = self.valueForEncryption(objectAttribute['value'])
                if type(value) == unicode:
                    strvalue = value.encode('utf-8')
                else:
                    strvalue = str(value)
                objectAttributeValue = strvalue
                if dataStorage == 'patient':
                    strvalue = self.cipher.encryptCTR(strvalue)
                objectAttributeValue = base64.b64encode(strvalue)
            else:
                #strvalue = str(objectAttribute['value'])
                strvalue = base64.b64decode(objectAttribute['value'])
                if dataStorage == 'patient':
                    strvalue = self.cipher.decryptCTR(strvalue)
                try:
                    value = strvalue.decode('utf-8')
                except:
                    value = _("ENCRYPTED")
                objectAttributeValue = value
            outputObjectAttribute = dict()
            for key in objectAttribute:
                if key == 'value':
                    continue
                outputObjectAttribute[key] = objectAttribute[key]
            outputObjectAttribute['value'] = objectAttributeValue
            if discrepancies is not None and objectAttribute['localId'] in discrepancies['objectsAttributes']:
                discrepancies['objectsAttributes'][objectAttribute['localId']]['value'] = objectAttributeValue
            outputObjectsAttributes.append(outputObjectAttribute)
        return outputObjectsAttributes
 
    def encryptObjectsAttributes(self,objectsAttributes):
        return self.encryptDecryptObjectsAttributes(objectsAttributes,'encrypt')

    def decryptObjectsAttributes(self,objectsAttributes,discrepancies=None):
        return self.encryptDecryptObjectsAttributes(objectsAttributes,'decrypt',discrepancies)
        
    def saveData(self, evaluateErrors=True, notify=True, updateStatus=True, firstSave=False, dataId=None):
        self.beginCriticalSection()
        #gcp are active and data have not been confirmed. Saving denied.
        if self.getGcpChangedAttributes(True):
            print 'save data denied'
            return
        if evaluateErrors:
            anyErrors = self.evalErrors()
            anyUnacceptedWarnings = self.evalUnacceptedWarnings()
            if notify:
                userInfo = {'errors': anyErrors, 'warnings': anyUnacceptedWarnings}
                self.notificationCenter.postNotification("ErrorsAndWarningsHaveBeenFound",self,userInfo)

        if updateStatus:
            self.updateStatus()
        
        data = self.dataSession.makeJSON()
        encrypted_data = self.dataSession.makeJSON(encrypted=True)
        if not dataId:
            data_ids = self.jsonStore.search_ids({'admissionKey': self.dataSession.admissionKey})
        else:
            data_ids = [dataId]
        if data_ids:
            self.jsonStore.update(encrypted_data,entry_id=data_ids[0],indexed_entry=data,indexed_keys=self.indexedKeys)
        else:
            self.jsonStore.create(encrypted_data,indexed_entry=data,indexed_keys=self.indexedKeys)
        self.confirmResult = {}
        self.dataSession.resetModifiedObjects()
        self.dataSession.resetModifiedObjectsAttributes()
        self.endCriticalSection()

        if notify:
            self.notificationCenter.postNotification("DataHaveBeenSaved",self)

    ###################################################################
    #TODO JSON#########################################################
    ###################################################################
    def getReadmissionAdmissionKeys(self):
        return []
        currentPatientKey = self.dataSession.patientKey
        currentAdmissionKey = self.dataSession.admissionKey
        query = "SELECT admissionKey from admissionDeleted"
        deletedAdmission = self.queryManager.sendQuery(query)
        deletedAdmissionKeys = [el['admissionKey'] for el in deletedAdmission]
        query = "SELECT admissionKey, previousAdmissionKey from admission where patientKey = '%s'" % currentPatientKey
        samePatientAdmission = self.queryManager.sendQuery(query)
        readmissionAdmissionKeys = []
        self.checkParentAdmission(samePatientAdmission, currentAdmissionKey, readmissionAdmissionKeys, deletedAdmissionKeys)
        self.checkChildrenAdmission(samePatientAdmission, currentAdmissionKey, readmissionAdmissionKeys, deletedAdmissionKeys)
        print 'READMISSION KEYS:', currentAdmissionKey, readmissionAdmissionKeys
        return readmissionAdmissionKeys
        
    ###################################################################
    #TODO JSON#########################################################
    ###################################################################
    def isParentReadmission(self):
        return False
        currentPatientKey = self.dataSession.patientKey
        currentAdmissionKey = self.dataSession.admissionKey
        query = "SELECT admissionKey from admissionDeleted"
        deletedAdmission = self.queryManager.sendQuery(query)
        deletedAdmissionKeys = [el['admissionKey'] for el in deletedAdmission]
        query = "SELECT admissionKey, previousAdmissionKey from admission where patientKey = '%s'" % currentPatientKey
        samePatientAdmission = self.queryManager.sendQuery(query)
        isParentReadmissionList = []
        if self.checkChildrenAdmission(samePatientAdmission, currentAdmissionKey, isParentReadmissionList, deletedAdmissionKeys):
            return True
        return False
        
    def checkParentAdmission(self, patientAdmissions, currentAdmissionKey, savedAdmissionKeyList, deletedAdmissionKeys):
        for admission in patientAdmissions:
            if admission['admissionKey'] not in deletedAdmissionKeys:
                if admission['admissionKey'] == currentAdmissionKey:
                    if admission['previousAdmissionKey']:
                        #case 1
                        if admission['previousAdmissionKey'] not in savedAdmissionKeyList:
                            savedAdmissionKeyList.append(admission['previousAdmissionKey'])
                        savedAdmissionKeyList = self.checkParentAdmission(patientAdmissions, admission['previousAdmissionKey'], savedAdmissionKeyList, deletedAdmissionKeys)
                    else:
                        return savedAdmissionKeyList

    def checkChildrenAdmission(self, patientAdmissions, currentAdmissionKey, savedAdmissionKeyList, deletedAdmissionKeys):
        for admission in patientAdmissions:
            if admission['admissionKey'] not in deletedAdmissionKeys:
                if admission['previousAdmissionKey'] == currentAdmissionKey:
                    #case 1
                    if admission['admissionKey'] not in savedAdmissionKeyList:
                        savedAdmissionKeyList.append(admission['admissionKey'])
                    savedAdmissionKeyList = self.checkChildrenAdmission(patientAdmissions, admission['admissionKey'], savedAdmissionKeyList, deletedAdmissionKeys)
                    return savedAdmissionKeyList
        return savedAdmissionKeyList
        
    def computeStatus(self,crfName):

        if self.dataSession.getCrfProperty(crfName,'enabled') == False:
            newStatus = '0'
            self.crfStatusunder3((crfName, set(), newStatus))
            return newStatus

        newStatus = '1'
        if not self.evalErrors(crfName) and not self.evalUnacceptedWarnings(crfName):

            try:
                currentClassNames = self.dataSession.getCompletedClassNames(crfName)
                currentClassNames = set(currentClassNames)
                registeredClassNames = self.dataSession.getRegisteredClassNames(crfName)
                registeredClassNames = set(registeredClassNames)
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                self.crfStatusunder3((crfName, set(), newStatus))
                return newStatus
            
            newStatus = '2'

            if newStatus == '2':
                try:
                    status3ClassNames = self.crfData.getClassesByPropertyWithValue(crfName,'requiredForStatus','3')
                    status3ClassNames = [className for className in status3ClassNames if (crfName,className) in self.dataSession.classProperties['visibility'] and self.dataSession.classProperties['visibility'][(crfName,className)] == True]
                    status3ClassNames = [className for className in status3ClassNames if (crfName,className) in self.dataSession.classProperties['enabled'] and self.dataSession.classProperties['enabled'][(crfName,className)] == True]
                    status3ClassNames = set(status3ClassNames).intersection(registeredClassNames)
                    if status3ClassNames.issubset(currentClassNames):
                        newStatus = '3'
                    else:
                        PsLogger().info(['RequiredForStatusTag'], "Required for status 3 in " + crfName + ": " + str(status3ClassNames - currentClassNames))
                    #print 'STATUS 3:', crfName, status3ClassNames - currentClassNames
                    self.crfStatusunder3((crfName, status3ClassNames - currentClassNames, newStatus))
                    self.crfStatusunder3((crfName, status3ClassNames - currentClassNames, newStatus))
                except BaseException, e:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                    return newStatus
            
            if newStatus == '3':
                try:
                    status4ClassNames = self.crfData.getClassesByPropertyWithValue(crfName,'requiredForStatus','4')
                    status4ClassNames = [className for className in status4ClassNames if (crfName,className) in self.dataSession.classProperties['visibility'] and self.dataSession.classProperties['visibility'][(crfName,className)] == True]
                    status4ClassNames = [className for className in status4ClassNames if (crfName,className) in self.dataSession.classProperties['enabled'] and self.dataSession.classProperties['enabled'][(crfName,className)] == True]
                    status4ClassNames = set(status4ClassNames).intersection(registeredClassNames)
                    if status4ClassNames and status4ClassNames.issubset(currentClassNames):
                        newStatus = '4'
                    else:
                        PsLogger().info(['RequiredForStatusTag'], "Required for status 4 in " + crfName + ": " + str(status4ClassNames - currentClassNames))
                    #print 'STATUS 4:', crfName, status4ClassNames - currentClassNames
                    self.crfStatusunder3((crfName, status4ClassNames - currentClassNames, newStatus))
                    self.crfStatusunder3((crfName, status4ClassNames - currentClassNames, newStatus))
                except BaseException, e:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                    return newStatus
        else:
            self.crfStatusunder3((crfName, set(), newStatus))

        return newStatus
        
    def crfStatusunder3(self,varCrfStaus = None): 
        if varCrfStaus != None:
            self.crfPetalStatus[varCrfStaus[0]]=varCrfStaus[2]
        # else:
            # self.crfPetalStatus = {}
            
    def StatusPetal(self):
        return self.crfPetalStatus

    def updateStatus(self, computeOnly=False):

        if self.dataSession.getAdmissionStatus() == '5':
            return

        self.dataSession.evaluateGlobals(updateStatus=False)

        self.beginCriticalSection()
        #self.queryManager.sendQuery('BEGIN TRANSACTION',toFile=True)

        for crfName in self.crfData.getCrfNames():

            #if crfName == psc.coreCrfName and self.dataSession.getAdmissionStatus() == '4' and not self.dataSession.ignoreStatusForUpdate:
            #    continue

            storedCrfVersion = None
            if not computeOnly:
                if self.storedCrfVersions:
                    storedCrfVersion = self.storedCrfVersions.get(crfName)
                #query = "SELECT crfVersion FROM currentCrfStatus WHERE admissionKey = '%s' AND crfName = '%s'" % (self.dataSession.admissionKey,crfName)
                #result = self.queryManager.sendQuery(query)
 
            try:
                crfVersion = self.crfData.getPropertyForCrf(crfName,'version')
                currentStatus = self.dataSession.getAdmissionStatus(crfName)
                newStatus = self.computeStatus(crfName)
            except BaseException, e:
                print e
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                continue

            #if crfName == psc.coreCrfName and self.dataSession.getAdmissionStatus() == '4' and not self.dataSession.ignoreStatusForUpdate and result and crfVersion == storedCrfVersion and not self.unsavedStatus:
            if crfName == psc.coreCrfName and self.dataSession.getAdmissionStatus() == '4' and not self.dataSession.ignoreStatusForUpdate and crfVersion == storedCrfVersion and not self.unsavedStatus:
                continue

            if not computeOnly and newStatus == currentStatus and storedCrfVersion and crfVersion == storedCrfVersion:
                if self.unsavedStatus == False:
                    continue

            if not computeOnly:
                #####################################################
                #TODO JSON: should we save here?
                #####################################################
                #localId = self.getNewLocalId('crfStatus')
                #query = "INSERT INTO crfStatus (admissionKey, crfName, statusValue, crfVersion, centreCode, localId, inputDate) VALUES (?, ?, ?, ?, ?, ?, ?)"
                #bindings = (self.dataSession.admissionKey,crfName,newStatus,crfVersion,self.centrecode,localId,self.getDateTime())
                ##result = self.queryManager.sendQuery(query,bindings,toFile=True)
                #queryList.append({'query':query,'bindings':bindings,'toFile':True})
                self.unsavedStatus = False
            else:
                self.unsavedStatus = True
 
            self.dataSession.setAdmissionStatus(newStatus,crfName)
            if newStatus != currentStatus:
                self.notificationCenter.postNotification("BasedataHasBeenUpdated",self)
        #self.queryManager.sendQuery('COMMIT TRANSACTION',toFile=True)
        #self.queryManager.sendQueriesInTransaction(queryList)
        self.endCriticalSection()
        
        self.notificationCenter.postNotification("StatusHasBeenUpdated",self)
 
    def checkCrfVersionOfAdmissions(self, activeAdmissionsData=None):
        if activeAdmissionsData == None:
            activeAdmissionsData = self.getAllActiveAdmissionsData()

        if not activeAdmissionsData:
            return []

        crfVersionDicts = self.jsonStore.load_values(None,'crfVersionDict')
        admissionKeys = self.jsonStore.load_values(None,'admissionKey')
        admissionKeysToIds = dict(zip(admissionKeys.values(),admissionKeys.keys()))

        admissionsToOpen = set()

        for admissionData in activeAdmissionsData: 
            admissionKey = admissionData['admissionKey']
            admissionDate = admissionData[psc.admissionDateAttr]

            if not admissionDate:
                print 'ERROR in checkCrfVersionOfAdmissions: admissionDate not available for admissionKey %s' % admissionKey
            try:
                id_ = admissionKeysToIds[admissionKey]
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print 'Cannot find data for admission', e
                continue
            crfVersionDict = eval(crfVersionDicts[id_])

            crfNames = self.getAppdataCrfNamesForDate(admissionDate)

            for crfName in crfNames:
                if crfName not in crfVersionDict:
                    continue
                currentCrfVersion = crfVersionDict[crfName]
                updatedCrfVersion = self.getCrfValidVersion(crfName,admissionDate)
                if updatedCrfVersion == None:
                    continue
                splitCurrentCrfVersion = currentCrfVersion.split('.')
                splitUpdatedCrfVersion = updatedCrfVersion.split('.')
                if not (len(splitCurrentCrfVersion) > 1 and len(splitUpdatedCrfVersion) > 1):
                    continue
                if splitCurrentCrfVersion[0] != splitUpdatedCrfVersion[0] or splitCurrentCrfVersion[1] != splitUpdatedCrfVersion[1]:
                    admissionsToOpen.add(admissionKey)
                    break

        return list(admissionsToOpen)

    def openSaveAndCloseAdmission(self, admissionKey):
        self.beginCriticalSection()
        print 'OPENING ADMISSION', admissionKey
        loaded = self.loadAdmission(admissionKey)
        if not loaded:
            self.endCriticalSection()
            return False
        self.saveData()
        self.exitAdmission()
        self.endCriticalSection()
        return True
    
    def getNextLocalId(self, table='admission'):
        self.currentNewUUID = self.jsonStore.getNewUUID(table)
        return self.currentNewUUID
        
    def getAllActiveAdmissionsData(self):
        self.beginCriticalSection()
        admissionIds = self.jsonStore.search_ids({'activeAdmission':True})
        attributeFullNames = psc.gridDataAttributes

        positions = ['crfs.'+el for el in attributeFullNames]
        positions.append('crfStatusDict')
        positions.append('patientKey')
        positions.append('admissionKey')

        attributesToInternalKeys = dict.fromkeys(attributeFullNames,'admission')
        for patientAttribute in psc.patientGridDataAttributes:
            attributesToInternalKeys[patientAttribute] = 'patient'
            
        tokenSize = 250
        tokenCounter = 0
        endFlag = True
        valueList = {}
        
        while endFlag:
            if tokenCounter + tokenSize <= len(admissionIds):
                valueList.update(self.jsonStore.load_value_list(admissionIds[tokenCounter:tokenCounter+tokenSize],positions))
            else:
                valueList.update(self.jsonStore.load_value_list(admissionIds[tokenCounter:len(admissionIds)],positions))
                endFlag = False
            tokenCounter += tokenSize
        
        prefixLength = len('crfs.')
        data = []
        for id_ in valueList:
            row = {}.fromkeys(attributeFullNames)
            crfStatusDict = None

            for el in valueList[id_]:
                position = el.keys()[0]
                value = el[position]
                if position == 'patientKey':
                    row['patientKey'] = value
                elif position == 'admissionKey':
                    row['admissionKey'] = value
                elif position == 'crfStatusDict':
                    crfStatusDict = eval(value)
                else:
                    fullName = position[prefixLength:]
                    #TODO: decrypt
                    #row[fullName] = self.encryptDecryptValue(value,'decrypt',attributesToInternalKeys[fullName])
                    row[fullName] = value
            
            row['statusValue'] = crfStatusDict[psc.coreCrfName]
            petalStatusDict = dict()
            row['petalsComplete'] = True
            for petalName in crfStatusDict:
                if petalName == psc.coreCrfName:
                    continue
                row[petalName] = crfStatusDict[petalName]
                petalStatusDict[petalName] = crfStatusDict[petalName]
                if petalStatusDict[petalName] != '0':
                    if petalStatusDict[petalName] != '3':
                        row['petalsComplete'] = False                        
            row.update(petalStatusDict)
            data.append(row)
        self.endCriticalSection()

        return data
        
        
    def getExportDictionaries(self, admissionKeysSet = None):
        admissionIds = self.jsonStore.search_ids({'activeAdmission':True})
        positions = []
        positions.append('crfStatusDict')
        positions.append('crfVersionDict')
        positions.append('patientKey')
        positions.append('admissionKey')

        tokenSize = 500
        tokenCounter = 0
        endFlag = True
        valueList = {}
        while endFlag:
            if tokenCounter + tokenSize <= len(admissionIds):
                valueList.update(self.jsonStore.load_value_list(admissionIds[tokenCounter:tokenCounter+tokenSize],positions))
            else:
                valueList.update(self.jsonStore.load_value_list(admissionIds[tokenCounter:len(admissionIds)],positions))
                endFlag = False
            tokenCounter += tokenSize
        
        #PRIMA QUERY EFFETTIVAMENTE MODIFICATA CON SUCCESSIVO RIADATTAMENTO ALLA STRUTTURA
        #query = "SELECT crfName, crfVersion, statusValue, admissionKey FROM currentCrfStatus"
        #crfrdict = self.queryManager.sendQuery(query)
        crfrdict = []
        existingCrfNames = self.jsonStore.load_values(None,'crfVersionDict').values()
        if existingCrfNames:
            existingCrfNames = set(reduce(lambda a, b: a + b,[eval(el).keys() for el in existingCrfNames]))
        rdict = []
        for value in valueList.values():
            currentAdmissionKey = ''
            for valueDict in value:
                if 'crfVersionDict' in valueDict:
                    crfVersionDict = eval(valueDict['crfVersionDict'])
                elif 'crfStatusDict' in valueDict:
                    crfStatusDict = eval(valueDict['crfStatusDict'])
                elif 'admissionKey' in valueDict:
                    currentAdmissionKey = valueDict['admissionKey']
                elif 'patientKey' in valueDict:
                    currentPatientKey = valueDict['patientKey']
            if currentAdmissionKey not in admissionKeysSet:
                continue
            for existingCrfName in existingCrfNames:
                crfrDictTmp = {}
                crfrDictTmp['crfName'] = existingCrfName
                if existingCrfName == psc.coreCrfName:
                    rdicttmp = dict()
                    rdicttmp['patientKey'] = currentPatientKey
                    rdicttmp['admissionKey'] = currentAdmissionKey
                    rdicttmp['statusValue'] = crfStatusDict[existingCrfName]
                    rdict.append(rdicttmp)
                if existingCrfName in crfVersionDict:
                    crfrDictTmp['crfVersion'] = crfVersionDict[existingCrfName]
                    crfrDictTmp['statusValue'] = crfStatusDict[existingCrfName]
                    crfrDictTmp['admissionKey'] = currentAdmissionKey
                    crfrdict.append(crfrDictTmp)
        return [rdict, crfrdict]
        
        
    def getAttrDict(self, admissionIds, admissionKeySet, progressBar=None):
        #attrDictValueList = self.jsonStore.search({'activeAdmission':True})
        
        attrrdict = []
        fakeLocalIdCounter = 1
        fakeObjectCodeCounter = 1
        admissionIdsCounter = 1
        defaultKeyListForMetadata = [u'userKey', u'crfVersion', u'inputDate']
        patientDefaultKeyListForMetadata = [u'userKey', u'crfVersion', u'inputDate', 'encryption']
        defaultKeyListForMetadata.sort()
        patientDefaultKeyListForMetadata.sort()
        decryptDataSession = DataSession(self)
        for admissionId in admissionIds:
            admissionIdsCounter += 1
            if progressBar and admissionIdsCounter % 10 == 0:
                progressBar.Step(stepValue=1, message=_('Extracting patient data'))
            admission = self.jsonStore.search({'__id__':admissionId, 'activeAdmission':True})
            if admission:
                admission = admission[0]
                if admission['admissionKey'] not in admissionKeySet:
                    continue
            decryptedAdmission = decryptDataSession.decryptJSON(admission)
            admissionValues = decryptedAdmission['crfs']
            for crfName in admissionValues.keys():
                
                for className in admissionValues[crfName]:
                    
                    #temporary skipping metadata informations
                    if className in ['crfStatus', 'crfVersion']:
                        continue
                    fakeObjectCodeCounter += 1
                    #temporary forced reference to timestamp 1
                    patientClass = False
                    
                    timeStamps = admissionValues[crfName][className].keys()
                    timeStamps.sort()

                    for timeStamp in timeStamps:
                        for childElement in admissionValues[crfName][className][timeStamp]:
                            sortedAttributeNameKeys = childElement.keys()
                            sortedAttributeNameKeys.sort()
                            if sortedAttributeNameKeys == patientDefaultKeyListForMetadata:
                                patientClass = True
                                break

                        for attributeNameList in admissionValues[crfName][className][timeStamp]:
                            
                            #element is composed by attribute and its metadata
                            sortedAttributeNameKeys = attributeNameList.keys()
                            sortedAttributeNameKeys.sort()
                            if sortedAttributeNameKeys == defaultKeyListForMetadata:
                                #temporary skip metadata
                                continue
                            elif sortedAttributeNameKeys == patientDefaultKeyListForMetadata:
                                continue
                            multiInstanceNumber = 1
                            for element in attributeNameList:
                                if type(attributeNameList[element]) == type(dict()):
                                    #temporary skip metadata
                                    continue
                                else:
                                    for attributeValues in attributeNameList[element]:
                                        #element[attributeName] is composed by attributeValues and metadata
                                        attributeValueTmp = None
                                        if type(attributeValues) == type(dict()):
                                            #temporary skip attributeValues metadata
                                            continue
                                        else:
                                            for attributeValue in attributeValues:
                                                if type(attributeValue) == type(dict()):
                                                    #should be a container
                                                    for containedClassName in attributeValue.keys():
                                                        multiInstanceNumber = 1
                                                        for containedAttributeDict in attributeValue[containedClassName]:
                                                            sortedContainedAttributeNameKeys = containedAttributeDict.keys()
                                                            sortedContainedAttributeNameKeys.sort()
                                                            if sortedContainedAttributeNameKeys == defaultKeyListForMetadata:
                                                                #temporary skip metadata
                                                                continue
                                                            for containedAttributeName in containedAttributeDict.keys():
                                                                for containedAttributeValues in containedAttributeDict[containedAttributeName]:
                                                                    if type(containedAttributeValues) == type(dict()):
                                                                        #temporary skip attributeValues metadata
                                                                        continue
                                                                    else:
                                                                        for containedAttributeValue in containedAttributeValues:
                                                                            attrrdictTmpDict = {}
                                                                            attrrdictTmpDict['crfName'] = crfName
                                                                            attrrdictTmpDict['className'] = containedClassName
                                                                            #simulating objectCode presence
                                                                            attrrdictTmpDict['objectCode'] = fakeObjectCodeCounter
                                                                            attrrdictTmpDict['attributeName'] = containedAttributeName
                                                                            attrrdictTmpDict['multiInstanceNumber'] = multiInstanceNumber
                                                                            multiInstanceNumber += 1
                                                                            #simulating localId presence
                                                                            attrrdictTmpDict['localId'] = fakeLocalIdCounter
                                                                            fakeLocalIdCounter += 1
                                                                            attrrdictTmpDict['externalKey'] = decryptedAdmission['admissionKey']
                                                                            attrrdictTmpDict['value'] = containedAttributeValue
                                                                            attrrdictTmpDict['dataStorage'] = 'admission'
                                                                            attrrdictTmpDict['timeStamp'] = timeStamp
                                                                            if patientClass:
                                                                                attrrdictTmpDict['dataStorage'] = 'patient'
                                                                            attrrdict.append(attrrdictTmpDict)
                                                
                                                else:
                                                    #non-container classes
                                                    attrrdictTmpDict = {}
                                                    attrrdictTmpDict['crfName'] = crfName
                                                    attrrdictTmpDict['className'] = className
                                                    #simulating objectCode presence
                                                    attrrdictTmpDict['objectCode'] = fakeObjectCodeCounter
                                                    attrrdictTmpDict['attributeName'] = element
                                                    attrrdictTmpDict['multiInstanceNumber'] = multiInstanceNumber
                                                    multiInstanceNumber += 1
                                                    #simulating localId presence
                                                    attrrdictTmpDict['localId'] = fakeLocalIdCounter
                                                    fakeLocalIdCounter += 1
                                                    attrrdictTmpDict['externalKey'] = admission['admissionKey']
                                                    attrrdictTmpDict['value'] = attributeValue
                                                    attrrdictTmpDict['dataStorage'] = 'admission'
                                                    attrrdictTmpDict['timeStamp'] = timeStamp
                                                    if patientClass:
                                                        attrrdictTmpDict['dataStorage'] = 'patient'
                                                    attrrdict.append(attrrdictTmpDict)
        return attrrdict

    def getAllActiveAdmissionsDataTable(self, admissionKeysSet=None, chooseGroupsCallback=None, GroupCrfCallback=None, translate=True, progressBar=None):
        from mainlogic import _
        progressBar.max = 1000
        progressBar.StartProgressBar(title=_("Export data"))
        progressBar.Step(stepValue=50, message=_('Loading patients'))
        self.beginCriticalSection()
        rdict, crfrdict = self.getExportDictionaries(admissionKeysSet=admissionKeysSet)
        exportGroups = set()
        exportGroupsToTitles = dict()
        allAttributesToGroups = dict()
        allAttributesToWeights = dict()
        allAttributesToTitles = dict()
        dicCrfgroupexport = dict()

        admissionKeysToCrfs = dict()
        crfDataDict = dict()
        self.GroupCrfCallback=GroupCrfCallback
        for record in crfrdict:
            
            if record['admissionKey'] not in admissionKeysSet:
                continue
            if record['admissionKey'] not in admissionKeysToCrfs:
                admissionKeysToCrfs[record['admissionKey']] = dict()
            admissionKeysToCrfs[record['admissionKey']][record['crfName']] = record['crfVersion']
            if record['crfName'] not in crfDataDict:
                crfDataDict[record['crfName']] = dict()
            if record['crfVersion'] not in crfDataDict[record['crfName']]:
                crfData = DataConfiguration()
                try:
                    crfData.readCrfConfiguration(os.path.join(self.configDirectory,self.crfFileDict[record['crfName']][record['crfVersion']]['filenames']['crf']))
                except BaseException, e:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                    pass
                try:
                    languageFilePath = os.path.join(self.configDirectory,self.crfFileDict[record['crfName']][record['crfVersion']]['filenames']['languages'])
                except KeyError, e:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                    continue
                f = open(languageFilePath, "r")
                xmlString = f.read()
                f.close()
                xmlDocument = etree.fromstring(xmlString)
                if xmlDocument.tag == 'languages':
                    for el in xmlDocument:
                        if el.tag == 'language' and el.get('name') and el.get('name') not in self.languages:
                            self.languages[el.get('name')] = dict()
                            self.languages[el.get('name')]['translations'] = dict()
                            self.languages[el.get('name')]['formats'] = dict()
                self.loadTranslations('English',languageFilePath)
                self.loadTranslations(self.userLanguage,languageFilePath)

                attributesToGroups = dict()
                for className in crfData.getClassNamesForCrf(record['crfName']):
                    for attributeName in crfData.getAttributeNamesForClass(record['crfName'],className):
                        exportGroup = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'export')
                        exportWeight = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'exportWeight')
                        if exportWeight != None:
                            exportWeight = int(exportWeight)
                        if exportGroup:
                            #print exportGroup
                            exportGroups.add(exportGroup)
                            if record['crfName'] not in  dicCrfgroupexport.keys():
                                dicCrfgroupexport[record['crfName']] = [self.translateString(exportGroup)]
                            else:
                                if self.translateString(exportGroup) not in dicCrfgroupexport[record['crfName']]:
                                    dicCrfgroupexport[record['crfName']].append(self.translateString(exportGroup))
                            exportGroupsToTitles[exportGroup] = self.translateString(exportGroup)
                            attributeFullName = crfData.joinAttributeName(record['crfName'],className,attributeName)
                            attributesToGroups[attributeFullName] = exportGroup
                            allAttributesToGroups[attributeFullName] = exportGroup
                            allAttributesToWeights[attributeFullName] = exportWeight
                            classLabel = crfData.getPropertyForClass(record['crfName'],className,'label')
                            if classLabel:
                                classLabel = self.translateString(classLabel)
                            attributeLabel = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'label')
                            if attributeLabel:
                                attributeLabel = self.translateString(attributeLabel)
                            if classLabel and attributeLabel:
                                if classLabel != attributeLabel:
                                    title = classLabel + u" - " + attributeLabel
                                else:
                                    title = attributeLabel
                            elif attributeLabel:
                                title = attributeLabel
                            else:
                                title = className + "."  + attributeName
                            allAttributesToTitles[attributeFullName] = title

                crfDataDict[record['crfName']][record['crfVersion']] = {'crfData':crfData, 'attributesToGroups':attributesToGroups}
        
        progressBar.Step(stepValue=50, message=_('Patients loaded'))
        
        if dicCrfgroupexport=={}:
            chosenGroups = exportGroupsToTitles.keys()
        else:
            print 'error dicCrfgroupexport:',dicCrfgroupexport
            try:
                self.GroupCrfCallback(dicCrfgroupexport)
            except:
                pass
            # if not test:
                # return None
            chosenGroups = chooseGroupsCallback(exportGroupsToTitles)
        if dicCrfgroupexport and not chosenGroups:
            progressBar.Stop(message=_("Export aborted"))
            return None
        #chosenGroups = chooseGroupsCallback(exportGroupsToTitles)
        # if not chosenGroups:
            # return None
        progressBar.Step(stepValue=50, message=_('Patients filtered'))
        decoratedAttributeFullNames = [(allAttributesToGroups[el],allAttributesToWeights[el],el) for el in allAttributesToGroups if allAttributesToGroups[el] in chosenGroups]
        #TODO: translate before sorting? If not, make sure @@@ are sorted correctly
        decoratedAttributeFullNames.sort()

        columnNames = [el[2] for el in decoratedAttributeFullNames]
        translatedColumnNames = [allAttributesToTitles[el[2]].replace("\r\n", " ").replace("\r", " ").replace("\n", " ") for el in decoratedAttributeFullNames]
        columnNamesToTranslatedColumnNames = dict(zip(columnNames,translatedColumnNames))
        columnNamesToIndices = dict.fromkeys(columnNames,range(len(columnNames)))

        classNames = [el.split('.')[1] for el in columnNames]

        progressBar.Step(stepValue=50, message=_('Loading data'))
        #progressBar.Step(stepValue=50, message=_('Data loaded!'))
        
        admissionIds = self.jsonStore.search_ids({'activeAdmission':True})
        tokenSize = 500
        tokenCounter = 0
        endFlag = True
        #valueList = {}
        data = []
        while endFlag:
            progressBar.Step(stepValue=50, message=_('Extracting patient data'))
            attributeData = dict()
            if tokenCounter + tokenSize <= len(admissionIds):
                attrrdict = self.getAttrDict(admissionIds[tokenCounter:tokenCounter+tokenSize], admissionKeysSet, progressBar)
            else:
                attrrdict = self.getAttrDict(admissionIds[tokenCounter:len(admissionIds)], admissionKeysSet, progressBar)
                #valueList.update(self.jsonStore.load_value_list(admissionIds[tokenCounter:len(admissionIds)],positions))
                endFlag = False
            tokenCounter += tokenSize
            progressBar.Step(stepValue=50, message=_('Extracting patient data'))
            counter = 0 
            maxcounter = len(attrrdict) / 600.0
            if maxcounter == 0 :
                maxcounter = 1
            for record in attrrdict:
                counter += 1
                if counter % maxcounter == 0:
                    progressBar.Step(stepValue=1, message=_('Extracting patient data'))
                if record['externalKey'] not in attributeData:
                    attributeData[record['externalKey']] = dict()
                attributeFullName = self.crfData.joinAttributeName(record['crfName'],record['className'],record['attributeName'])
                multiInstanceNumber = record['multiInstanceNumber']
                if attributeFullName not in attributeData[record['externalKey']]:
                    attributeData[record['externalKey']][attributeFullName] = {}
                timeStamp = record['timeStamp']
                if timeStamp not in attributeData[record['externalKey']][attributeFullName]:
                    attributeData[record['externalKey']][attributeFullName][timeStamp] = {}
                if multiInstanceNumber in attributeData[record['externalKey']][attributeFullName][timeStamp]:
                    attributeDataItem = attributeData[record['externalKey']][attributeFullName][timeStamp][multiInstanceNumber]
                    if record['objectCode'] > attributeDataItem['objectCode'] or (record['objectCode'] == attributeDataItem['objectCode'] and record['localId'] > attributeDataItem['localId']):
                        attributeData[record['externalKey']][attributeFullName][timeStamp][multiInstanceNumber] = {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value'], 'dataStorage':record['dataStorage']}
                else:
                    attributeData[record['externalKey']][attributeFullName][timeStamp][multiInstanceNumber] = {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value'], 'dataStorage':record['dataStorage']}
            progressBar.Step(stepValue=50, message=_('Extracting patient data'))

            columnNamesToTimeStamps = {}
            for record in rdict:
                for columnName in columnNames:
                    externalKey = record['patientKey']
                    attributeFullName = columnName
                    if record['admissionKey'] in attributeData and columnName in attributeData[record['admissionKey']]:
                        externalKey = record['admissionKey']
                        internalKeyTable = 'admission'
                    if externalKey not in attributeData or attributeFullName not in attributeData[externalKey]:
                        continue
                    for timeStamp in attributeData[externalKey][attributeFullName]:
                        if timeStamp == '#1':
                            continue
                        if columnName not in columnNamesToTimeStamps:
                            columnNamesToTimeStamps[columnName] = []
                        if timeStamp not in columnNamesToTimeStamps[columnName]:
                            columnNamesToTimeStamps[columnName].append(timeStamp)

            for record in rdict:
                admissionKey = record['admissionKey']
                if admissionKey not in admissionKeysSet:
                    continue
                patientKey = record['patientKey']
                row = []
                for columnName in columnNames:
                    attributeFullName = columnName
                    externalKey = record['patientKey']
                    internalKeyTable = 'patient'
                    if record['admissionKey'] in attributeData and attributeFullName in attributeData[record['admissionKey']]:
                        externalKey = record['admissionKey']
                        internalKeyTable = 'admission'

                    actualTimeStamps = columnNamesToTimeStamps.get(columnName,['#1'])

                    if externalKey not in attributeData or attributeFullName not in attributeData[externalKey]:
                        row += [''] * len(actualTimeStamps)
                        continue

                    for timeStamp in actualTimeStamps:

                        if timeStamp not in attributeData[externalKey][attributeFullName]:
                            row.append('')
                            continue

                        multiInstanceNumbers = attributeData[externalKey][attributeFullName][timeStamp].keys()
                        multiInstanceNumbers.sort()
                        values = []
                        
                        for multiInstanceNumber in multiInstanceNumbers:
                            try:
                                if attributeData[externalKey][attributeFullName][timeStamp][multiInstanceNumber]['dataStorage'] == 'patient':
                                    value = self.encryptDecryptValue(attributeData[externalKey][attributeFullName][timeStamp][multiInstanceNumber]['value'],'decrypt','patient')                        
                                else:
                                    value = attributeData[externalKey][attributeFullName][timeStamp][multiInstanceNumber]['value']
                            except BaseException, e:
                                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                                value = attributeData[externalKey][attributeFullName][timeStamp][multiInstanceNumber]['value']
                                #if internalKeyTable == 'patient':
                                #    value = 'ENCRYPTED'
                            
                            values.append(value)

                        crfName = attributeFullName.split('.')[0]
                        crfVersion = admissionKeysToCrfs[record['admissionKey']][crfName]
                        if translate:
                            decodedValues = psevaluator.decode(values,mainLogic=self,crfData=crfDataDict[crfName][crfVersion]['crfData'])
                            row.append(' '.join(';'.join(decodedValues).splitlines()).expandtabs(2))
                        else:
                            decodedValues = values
                            row.append(values)
                
                statusValue = record['statusValue']
                if [el for el in row if el != '']:
                    row = [admissionKey] + row
                    data.append(row)

        self.endCriticalSection()

        data.sort(key=lambda x: x[0])

        finalColumnNames = []
        for columnName in columnNames:
            if columnName in columnNamesToTimeStamps:
                for timeStamp in columnNamesToTimeStamps[columnName]:
                    finalColumnNames.append(columnNamesToTranslatedColumnNames[columnName] + timeStamp)
            else:
                finalColumnNames.append(columnNamesToTranslatedColumnNames[columnName])

        data.insert(0, ['AdmissionKey'] + finalColumnNames)
        progressBar.Stop(message = _('FINISHED!'))
        return data
        
    def getAllActiveAdmissionsRawDataTable(self, admissionKeysSet=None, chooseGroupsCallback=None, GroupCrfCallback=None,progressBar=None):
        
        outMetaData = dict()
        self.beginCriticalSection()
        progressBar.max = 75000
        progressBar.StartProgressBar(title=_("Get overview table"))
        progressBar.Step(stepValue=500, message=_('mapping admissions'))
        rdict, crfrdict = self.getExportDictionaries(admissionKeysSet=admissionKeysSet)

        exportGroups = set()
        exportGroupsToTitles = dict()
        allAttributesToGroups = dict()
        allAttributesToTitles = dict()
        dicCrfgroupexport = dict()
        
        admissionKeysToCrfs = dict()
        crfDataDict = dict()
        for record in crfrdict:
            if record['admissionKey'] not in admissionKeysSet:
                continue
            if record['admissionKey'] not in admissionKeysToCrfs:
                admissionKeysToCrfs[record['admissionKey']] = dict()
            admissionKeysToCrfs[record['admissionKey']][record['crfName']] = record['crfVersion']
            
            if record['crfName'] not in crfDataDict:
                
                crfDataDict[record['crfName']] = dict()
            if record['crfVersion'] not in crfDataDict[record['crfName']]:
                crfData = DataConfiguration()
                crfData.readCrfConfiguration(os.path.join(self.configDirectory,self.crfFileDict[record['crfName']][record['crfVersion']]['filenames']['crf']))
                
                languageFilePath = os.path.join(self.configDirectory,self.crfFileDict[record['crfName']][record['crfVersion']]['filenames']['languages'])
                f = open(languageFilePath, "r")
                xmlString = f.read()
                f.close()
                xmlDocument = etree.fromstring(xmlString)
                if xmlDocument.tag == 'languages':
                    for el in xmlDocument:
                        if el.tag == 'language' and el.get('name') and el.get('name') not in self.languages:
                            self.languages[el.get('name')] = dict()
                            self.languages[el.get('name')]['translations'] = dict()
                            self.languages[el.get('name')]['formats'] = dict()
                self.loadTranslations('English',languageFilePath)
                self.loadTranslations(self.userLanguage,languageFilePath)
                
                
                
                attributesToGroups = dict()
                for className in crfData.getClassNamesForCrf(record['crfName']):
                    for attributeName in crfData.getAttributeNamesForClass(record['crfName'],className):
                        exportGroup = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'export')
                        if exportGroup:
                            exportGroups.add(exportGroup)
                            #print 'Name of CRF:',record['crfName']
                            
                            exportGroupsToTitles[exportGroup] = self.translateString(exportGroup)
                            # if record['crfName'] not in  dicCrfgroupexport.keys():
                                # dicCrfgroupexport[record['crfName']] = [exportGroup]
                            # else:
                                # dicCrfgroupexport[record['crfName']].append(exportGroup)
                            attributeFullName = crfData.joinAttributeName(record['crfName'],className,attributeName)
                            if attributeFullName not in outMetaData:
                                outMetaData[attributeFullName] = dict()
                                dataType = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'dataType')
                                outMetaData[attributeFullName]['dataType'] = dataType
                                
                                if dataType.lower() == 'codingset':
                                    classLabel = crfData.getPropertyForClass(record['crfName'],className,'label')
###--cut here
                                    if classLabel:
                                        classLabel = self.translateString(classLabel)
                                    attributeLabel = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'label')
                                    if attributeLabel:
                                        attributeLabel = self.translateString(attributeLabel)
                                    outMetaData[attributeFullName]['translatedValue'] = attributeLabel
###--cut here
                                    codingSetName = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'codingSet')
                                    codingSetName = codingSetName.split('.')[1]
                                    codingSetValuesNames = crfData.getCodingSetValueNamesForCodingSet(record['crfName'], codingSetName)
                                    if codingSetValuesNames:
                                        for codingSetValueName in codingSetValuesNames:
                                            valueFullName = '.'.join([record['crfName'],codingSetName , codingSetValueName])
                                            if valueFullName not in outMetaData:
                                                outMetaData[valueFullName] = dict()
                                                value = crfData.getPropertyForCodingSetValue(record['crfName'],codingSetName,codingSetValueName,'value')
                                                outMetaData[valueFullName]['value'] = value
                                                outMetaData[valueFullName]['translatedValue'] = self.translateString(value)
                            
                            attributesToGroups[attributeFullName] = exportGroup
                            allAttributesToGroups[attributeFullName] = exportGroup
                            title = className + "."  + attributeName
                            allAttributesToTitles[attributeFullName] = title

                crfDataDict[record['crfName']][record['crfVersion']] = {'crfData':crfData, 'attributesToGroups':attributesToGroups}
        # if dicCrfgroupexport=={}:
            
            # chosenGroups = chooseGroupsCallback(exportGroupsToTitles)
        # else:
            # GroupCrfCallback(dicCrfgroupexport)
        chosenGroups = chooseGroupsCallback(exportGroupsToTitles)
        if not chosenGroups:
            return None

        decoratedAttributeFullNames = [(allAttributesToGroups[el],el) for el in allAttributesToGroups if allAttributesToGroups[el] in chosenGroups]
        #TODO: translate before sorting? If not, make sure @@@ are sorted correctly
        #decoratedAttributeFullNames.sort()
        columnNames = [el[1] for el in decoratedAttributeFullNames]
        
        columnNamesToIndices = dict.fromkeys(columnNames,range(len(columnNames)))

        classNames = [el.split('.')[1] for el in columnNames]
        admissionIds = self.jsonStore.search_ids({'activeAdmission':True})
        attrrdict = self.getAttrDict(admissionIds, admissionKeysSet)
        #query = "SELECT externalKey, objectData.objectCode objectCode, attributeData.localId localId, objectData.crfName crfName, objectData.className className, attributeName, value, attributeData.multiInstanceNumber multiInstanceNumber FROM objectData JOIN attributeData ON objectData.objectCode = attributeData.objectCode WHERE objectData.objectCode IN (SELECT max(objectCode) FROM objectData WHERE objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber) AND objectData.className IN (%s);" % ','.join(["'%s'" % el for el in classNames])
        #attrrdict = self.queryManager.sendQuery(query)

        crfStatusDict = dict()
        for record in crfrdict:
            if record['admissionKey'] not in crfStatusDict:
                crfStatusDict[record['admissionKey']] = dict()
            crfStatusDict[record['admissionKey']][record['crfName']] = record['statusValue']

        attributeData = dict()

        
        outData = []
                
        for record in attrrdict:
            if record['externalKey'] not in attributeData:
                attributeData[record['externalKey']] = dict()
            attributeFullName = self.crfData.joinAttributeName(record['crfName'],record['className'],record['attributeName'])
            multiInstanceNumber = record['multiInstanceNumber']
            if attributeFullName not in attributeData[record['externalKey']]:
                attributeData[record['externalKey']][attributeFullName] = {}
            if multiInstanceNumber in attributeData[record['externalKey']][attributeFullName]:
                attributeDataItem = attributeData[record['externalKey']][attributeFullName][multiInstanceNumber]
                if record['objectCode'] > attributeDataItem['objectCode'] or (record['objectCode'] == attributeDataItem['objectCode'] and record['localId'] > attributeDataItem['localId']):
                    attributeData[record['externalKey']][attributeFullName][multiInstanceNumber] = {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value']}
            else:
                attributeData[record['externalKey']][attributeFullName][multiInstanceNumber] = {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value']}

        for externalKey in attributeData:
            for attributeFullName in attributeData[externalKey]:
                multiInstanceNumbers = attributeData[externalKey][attributeFullName].keys()
                objectCodes = [attributeData[externalKey][attributeFullName][el]['objectCode'] for el in multiInstanceNumbers]
                maxObjectCode = max(objectCodes)
                for multiInstanceNumber in multiInstanceNumbers:
                    if attributeData[externalKey][attributeFullName][multiInstanceNumber]['objectCode'] != maxObjectCode:
                        attributeData[externalKey][attributeFullName].pop(multiInstanceNumber)

        for record in rdict:
            
            admissionKey = record['admissionKey']
            if admissionKey not in admissionKeysSet:
                continue
            dataItem = dict()
            dataItem['admissionKey'] = admissionKey
            
            patientKey = record['patientKey']
            dataItem['patientKey'] = patientKey
        
            for columnName in columnNames:
                attributeFullName = columnName
                externalKey = record['patientKey']
                internalKeyTable = 'patient'
                if record['admissionKey'] in attributeData and columnName in attributeData[record['admissionKey']]:
                    externalKey = record['admissionKey']
                    internalKeyTable = 'admission'
                if externalKey not in attributeData or attributeFullName not in attributeData[externalKey]:
                    dataItem[columnName] = None
                    continue
                multiInstanceNumbers = attributeData[externalKey][attributeFullName].keys()
                multiInstanceNumbers.sort()
                values = []
                for multiInstanceNumber in multiInstanceNumbers:
                    try:
                        value = self.encryptDecryptValue(attributeData[externalKey][attributeFullName][multiInstanceNumber]['value'],'decrypt',internalKeyTable)
                        #value = attributeData[externalKey][attributeFullName][multiInstanceNumber]['value']
                    except:
                        value = attributeData[externalKey][attributeFullName][multiInstanceNumber]['value']
                        #if internalKeyTable == 'patient':
                            #value = 'ENCRYPTED'
                    values.append(value)
                    
                                    
                crfName = attributeFullName.split('.')[0]
                crfVersion = admissionKeysToCrfs[record['admissionKey']][crfName]
                
                dataItem[columnName] = values
                
            statusValue = record['statusValue']
        
            outData.append(dataItem)
        self.endCriticalSection()
        return outData, outMetaData
        


    def initializeQuickFilters(self):
        self.quickFilters = dict()
        self.quickFilters['FirstName'] = '' 
        self.quickFilters['LastName'] = '' 
        self.quickFilters['EhrId'] = '' 
        self.quickFilters['AdmissionMinDate'] = '' 
        self.quickFilters['AdmissionMaxDate'] = '' 
        self.quickFilters['AdmissionHours'] = '' 
        self.quickFilters['AdmissionYear'] = '' 
        self.quickFilters['CoreStatus'] = '' 
        self.quickFilters['Petal'] = '' 
        self.quickFilters['PetalStatus'] = '' 

    def initializeFilters(self):
        self.filters = []

    def setQuickFilters(self,quickFilters):
        self.quickFilters = quickFilters
 
    def refreshGridData(self):
        gridData = self.getAllActiveAdmissionsData()
        self.gridData = self.filterAdmissionsData(gridData)
    
    def refreshGridDataFromDataSession(self):
        if not self.dataSession:
            return

        attributeFullNames = psc.gridDataAttributes

        row = dict()
        for attributeFullName in attributeFullNames:
            try: 
                crfName, className, attributeName = self.crfData.splitAttributeName(attributeFullName)
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                pass
                continue
            attributeValues = self.dataSession.getAttributeValuesForClass(crfName,className,attributeName)
            if not attributeValues:
                row[attributeFullName] = ''
            else:
                row[attributeFullName] = attributeValues[0]
        row['admissionKey'] = self.dataSession.admissionKey
        row['patientKey'] = self.dataSession.patientKey
        row['statusValue'] = self.dataSession.getAdmissionStatus()
        petalNames = self.crfData.getCrfNames()
        petalStatusDict = dict()
        for petalName in petalNames:
            if petalName == psc.coreCrfName:
                continue
            petalStatusDict[petalName] = self.dataSession.getAdmissionStatus(petalName)
            if petalStatusDict[petalName] != '0':
                row['petalsComplete'] = True
                if petalStatusDict[petalName] != '3':
                    row['petalsComplete'] = False
        row.update(petalStatusDict)
        gridData = [row] 
        filteredGridData = self.filterAdmissionsData(gridData)
        index = 0
        for gridRow in self.gridData:
            if gridRow['admissionKey'] == row['admissionKey']:
                break
            index += 1
        if filteredGridData:
            self.gridData[index] = filteredGridData[0]
        else:
            self.gridData.pop(index)

    def filterAdmissionsData(self, gridData):
       
        attributeFullNames = psc.gridDataAttributes
        activeQuickFilters = dict()
        for key in self.quickFilters:
            if self.quickFilters[key] != '':
                activeQuickFilters[key] = self.quickFilters[key]
        
        if self.filters or activeQuickFilters or self.quickCompilationMode:
            filteredGridData = []
            for row in gridData:
                includeRow = True
                #quick compilation intervention
                if self.quickCompilationMode != '':
                    for crfName in self.quickCompilationPages:
                        for version in self.quickCompilationPages[crfName]:
                            for quickPage in self.quickCompilationPages[crfName][version]:
                                if quickPage['pageName'] == self.quickCompilationMode:
                                    attributeNameForFilter = quickPage['pageConditionClass']
                                    break
                    if attributeNameForFilter in row:
                        if row[attributeNameForFilter] == '0' or row[attributeNameForFilter] == False:
                            includeRow = False
                
                for filter in self.filters:
                    attribute = filter['attribute']
                    #if psc.appName == 'prosafe':
                    #    if attribute not in attributeFullNames or attribute not in row:
                    #        continue
                    #    #value = row[attributeNameDict[attribute]]
                    #    value = row[attribute]
                    #else:
                    #    if attribute not in psc.attrNameDict or psc.attrNameDict[attribute] not in row:
                    #        continue
                    #    value = row[psc.attrNameDict[attribute]]

                    if attribute not in attributeFullNames or attribute not in row:
                        continue
                    value = row[attribute]

                    for condition in filter['conditions']:
                        try:
                            result = condition(value)
                        except BaseException, e:
                            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                            pass
                            #raise
                            result = False
                            pass
                        if not result:
                            includeRow = False
                            break
                    if not includeRow:
                        break
                if includeRow: 
                    if 'FirstName' in activeQuickFilters:
                        firstName = activeQuickFilters['FirstName']
                        if row[psc.firstNameAttr].lower() != firstName.lower() and row[psc.firstNameAttr].find(firstName) == -1:
                            includeRow = False
                    if 'LastName' in activeQuickFilters:
                        lastName = activeQuickFilters['LastName']
                        if row[psc.lastNameAttr].lower() != lastName.lower() and row[psc.lastNameAttr].find(lastName) == -1:
                            includeRow = False
                    if psc.appName == 'prosafe':
                        if 'EhrId' in activeQuickFilters:
                            ehrId = activeQuickFilters['EhrId']
                            if row['core.ehrId.value'] != ehrId:
                                includeRow = False
                        if 'AdmissionHours' in activeQuickFilters:
                            admHours = activeQuickFilters['AdmissionHours']
                            if row['core.exportIcuStayHours.value'] == None or int(row['core.exportIcuStayHours.value']) > int(admHours):
                                includeRow = False
                    if 'AdmissionMinDate' in activeQuickFilters:
                        minDate = activeQuickFilters['AdmissionMinDate']
                        if row[psc.admissionDateAttr] < minDate:
                            includeRow = False
                    if 'AdmissionMaxDate' in activeQuickFilters:
                        maxDate = activeQuickFilters['AdmissionMaxDate']
                        if row[psc.admissionDateAttr] > maxDate:
                            includeRow = False
                    if 'AdmissionYear' in activeQuickFilters:
                        currentYear = activeQuickFilters['AdmissionYear']
                        if not (row[psc.admissionDateAttr] >= '%s-01-01' % currentYear and row[psc.admissionDateAttr] <= '%s-12-31' % currentYear):
                            includeRow = False
                    if 'CoreStatus' in activeQuickFilters:
                        currentStatus = activeQuickFilters['CoreStatus']
                        if currentStatus.isdigit():
                            if row['statusValue'] != currentStatus:
                                includeRow = False
                        else:
                            if row['statusValue'] not in '0' and not (int(row['statusValue']) < int(currentStatus[-1])):
                                includeRow = False
                    if includeRow and 'Petal' in activeQuickFilters:
                        currentPetal = activeQuickFilters['Petal']
                        if currentPetal not in row or row[currentPetal] == '0':
                            includeRow = False
                        if includeRow and currentPetal and 'PetalStatus' in activeQuickFilters:
                            currentPetalStatus = activeQuickFilters['PetalStatus']
                            if currentPetalStatus.isdigit():
                                if row[currentPetal] != currentPetalStatus:
                                    includeRow = False
                            else:
                                if row[currentPetal] != '0' and not (int(row[currentPetal]) < int(currentPetalStatus[-1])):
                                    includeRow = False
                    elif includeRow and 'PetalStatus' in activeQuickFilters:
                        currentPetalStatus = activeQuickFilters['PetalStatus']
                        for currentPetal in self.getAppdataCrfNames():
                            if currentPetal == psc.coreCrfName:
                                continue
                            if currentPetalStatus.isdigit():
                                if row[currentPetal] != '0' and row[currentPetal] != currentPetalStatus:
                                    includeRow = False
                            else:
                                if row[currentPetal] != '0' and not (int(row[currentPetal]) < int(currentPetalStatus[-1])):
                                    includeRow = False
 
                if includeRow:
                    filteredGridData.append(row)

            gridData = filteredGridData

        decoratedGridData = [(el[psc.admissionDateAttr],el) for el in gridData]
        decoratedGridData.sort(reverse=True)

        sortedGridData = [el[1] for el in decoratedGridData]
        return sortedGridData

    def getGridNum(self):
        #query = "SELECT COUNT(*) AS counter FROM activeAdmissions"
        #result = self.queryManager.sendQuery(query)
        #return int(result[0]['counter'])                     
        return self.jsonStore.search({'activeAdmission':True},count=True)
    
    def getStats(self):
        """funzione utilizzata per la visualizzazione delle statistiche"""
        totAdm = self.getGridNum()
        visAdm = len(self.gridData)
        
        #statistiche sugli stati: da implementare con query
        #s0Adm = 0
        s1Adm = len([xx for xx in self.gridData if xx['statusValue'] == '1'])
        s2Adm = len([xx for xx in self.gridData if xx['statusValue'] == '2'])
        s3Adm = len([xx for xx in self.gridData if xx['statusValue'] == '3'])
        s4Adm = len([xx for xx in self.gridData if xx['statusValue'] == '4'])
        s5Adm = len([xx for xx in self.gridData if xx['statusValue'] == '5'])
        
        #dizionario di output
        out = {'total':totAdm, 'visualized':visAdm, 
                   #'status0':s0Adm,
                   'status1':s1Adm,'status2':s2Adm,'status3':s3Adm,
                   'status4':s4Adm,'status5':s5Adm }
        return out
    
    def getGridData(self):
        return self.gridData
    
    def getRowLabels(self):
        return range(1, len(self.gridData)+1)
    
    def getFilterFields(self):
        """ritorna i campi sui quali applicabile il filtro"""
        fields = []
        for crf in self.crfs:
            for attr in self.crfData.attributes[crf].keys():
                fields.append(attr)
        return fields

    def exportCurrentAdmissionsList(self, path):
        self.beginCriticalSection()
        gridData = self.getAllActiveAdmissionsData()
        filteredGridData = self.filterAdmissionsData(gridData)
        if not filteredGridData:
            return None
        import unicodedata
        #encodedData = [[unicodedata.normalize('NFKD',unicode(el)).encode('ascii','ignore') for el in row] for row in filteredGridData]
        headers = psc.printColumAttributes
        from mainlogic import _
        columns = [_(el) for el in psc.printColumnLabels]
        rows = []
        for admission in filteredGridData:
            for key in admission.keys():
                admission[key] = unicodedata.normalize('NFKD',unicode(admission[key])).encode('ascii','ignore')
            #rows.append(';'.join([str(psevaluator.decodevalue(admission[el],mainLogic=self)).replace('None', '') for el in headers if el in admission]))
            valcolumn = [str(psevaluator.decodevalue(admission[el],mainLogic=self)).replace('None', '') for el in headers if el in admission]
            for k in range(len(valcolumn)):
                if ';' in valcolumn[k]:
                    valcolumn[k]='"%s"'%valcolumn[k]
            rows.append(';'.join(valcolumn))
            # rows.append(';'.join([str(psevaluator.decodevalue(admission[el],mainLogic=self)).replace('None', '') for el in headers if el in admission]))
            
            
            
        f = open(path,'wb')
        f.write(';'.join(columns))
        for row in rows:
            f.write('\n' + row)
        f.close()
        self.endCriticalSection()
        
        return True

     
    def exportData(self, path, chooseGroupsCallback=None,GroupCrfCallback=None,stepCallback=None):

        self.beginCriticalSection()
        applyFiltersForExport = True
        filteredAdmissionKeys = None
        if applyFiltersForExport:
            gridData = self.getAllActiveAdmissionsData()
            filteredGridData = self.filterAdmissionsData(gridData)
            filteredAdmissionKeys = set([el['admissionKey'] for el in filteredGridData])
            
        data = self.getAllActiveAdmissionsDataTable(admissionKeysSet=filteredAdmissionKeys,chooseGroupsCallback=chooseGroupsCallback,GroupCrfCallback=GroupCrfCallback,progressBar=stepCallback)
        if not data:
            return None
        import unicodedata
        encodedData = [[unicodedata.normalize('NFKD',unicode(el)).encode('ascii','ignore') for el in row] for row in data]
        f = open(path,'wb')
        dataWriter = csv.writer(f,delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        dataWriter.writerows(encodedData)
        f.close()
        self.endCriticalSection()
        return True
   
    def exportDataOverview(self, path, chooseGroupsCallback, GroupCrfCallback, stepCallback=None):
        try:
            self.beginCriticalSection()
            gridData = self.getAllActiveAdmissionsData()
            filteredGridData = self.filterAdmissionsData(gridData)
            filteredAdmissionKeys = set([el['admissionKey'] for el in filteredGridData])
            if not filteredAdmissionKeys:
                return None
            self.getMappingFileFromMaster()
            data,metadata = self.getAllActiveAdmissionsRawDataTable(admissionKeysSet=filteredAdmissionKeys,chooseGroupsCallback=chooseGroupsCallback, GroupCrfCallback=GroupCrfCallback, progressBar=stepCallback)
            data = self.mapData(chooseGroupsCallback=chooseGroupsCallback, progressBar=stepCallback)

            if not data:
                return None
            #writing to excel file
            modelName = self.getExcelExportOverviewModel()
            modelFileName = os.path.join('xlsmodels',modelName)
            descriptiveTableCreator = DescriptiveTableCreator(modelFileName, path,data,metadata)
            descriptiveTableCreator.run()
            """
            f = open(path,'wb')
            dataWriter = csv.writer(f,delimiter=';')
            dataWriter.writerows(encodedData)
            f.close()
            """
            self.endCriticalSection()
            return True
        except Exception, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            raise
            print "exportDataOverview failed", str(e)
            return False
    
    def mapData(self, chooseGroupsCallback, progressBar=None):
    
        from mainlogic import _

        try:
            self.beginCriticalSection()
            applyFiltersForExport = True
            filteredAdmissionKeys = None
            if applyFiltersForExport:
                
                gridData = self.getAllActiveAdmissionsData()
                progressBar.Step(stepValue=2000, message=_('getting admissions from datatable'))
                filteredGridData = self.filterAdmissionsData(gridData)
                filteredAdmissionKeys = set([el['admissionKey'] for el in filteredGridData])
            
            progressBar.stepMultiplicator = 10000.0 / len(filteredAdmissionKeys)
            
            #ciclo for su filtered admission key, suddivise in sottogruppi in modo da non sforare con la memoria (circa 1mb per paziente [??])
            
            filteredAdmissionKeys = list(filteredAdmissionKeys)
            #a
            #usableRam = freeRamInMegaBytes / 100 * 75
            usableRam = 250
            #b
            totalPatients = len(filteredAdmissionKeys)
            #c
            firstCounter = 0
            #d
            lastCounter = 0
            cumulativeOverviewTableList = []
            patientsCounter = 1
            while firstCounter != totalPatients:
                if lastCounter + usableRam  < totalPatients:
                    lastCounter += usableRam
                    reducedList = filteredAdmissionKeys[firstCounter:lastCounter]
                    firstCounter = lastCounter
                else:
                    reducedList = filteredAdmissionKeys[firstCounter:totalPatients]
                    firstCounter = totalPatients
                overviewTableList = self.getOverviewTableListToken(reducedList, chooseGroupsCallback, progressBar, patientsCounter)
                cumulativeOverviewTableList.extend(overviewTableList)
            
            self.endCriticalSection()
            progressBar.Stop(message = _('FINISHED!'))
            return cumulativeOverviewTableList
        except Exception, e:
            #raise
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            print "exportDataOverview failed", str(e)    
            progressBar.Stop(message = _('overview table error'))
            return False
            
    def getOverviewTableListToken(self, reducedList, chooseGroupsCallback, progressBar, patientsCounter):
        
        #TODO: big refactoring needed!    
        progressBar.ruleMultiplicator = 1000 / progressBar.stepMultiplicator * len(reducedList)
    
        originalCrfVersionKey = 'http://giviti.marionegri.it/knowledgebase/prosafe-core#core__originalCrfVersion__value'
        mappingData = self.getMappedAdmissionsDataTable(admissionKeysSet=reducedList,chooseGroupsCallback=chooseGroupsCallback,progressBar=progressBar)
        from mainlogic import _
        progressBar.Step(stepValue=50, message=_('Admissions have been mapped.'))
        rdfExport = PSRDFManager()                
        rdfImport = PSRDFManager()
        sys.path.append('GivitiMapper')
        from GivitiMapper import GivitiMapper
        progressBar.Step(stepValue=50, message=_('Loading mapper rules'))
        mapper = GivitiMapper("prosafe-core4", "prosafe-core3")
        mapperForCore5 = GivitiMapper("prosafe-core5", "prosafe-core3")
        import rdflib
        nonMappedResultingGraph = rdflib.Graph()
        resultingGraph = rdflib.Graph()
        resultingGraphForCore5 = rdflib.Graph()
        print 'mapping data token'
        for admissionKey in mappingData:
            progressBar.Step(message = _('loading patient number') + ' %d' % patientsCounter, relativeStep=True)
            patientsCounter += 1
            patientGraph = rdfExport.admissionToRDF(mappingData, admissionKey, toFile=False)
            if int(mappingData[admissionKey][originalCrfVersionKey]) == 4:
                resultingGraph += patientGraph
            elif int(mappingData[admissionKey][originalCrfVersionKey]) == 5:
                resultingGraphForCore5 += patientGraph
            else:
                nonMappedResultingGraph += patientGraph
                #resultingGraph = mapper.doMapping(patientGraph)                    
        newResultingGraph = mapper.doMapping(resultingGraph, progressBar) + mapperForCore5.doMapping(resultingGraphForCore5, progressBar) + nonMappedResultingGraph
        
        progressBar.Step(stepValue=50, message = _('preparing admissions for overview table'))
        patientsMappingCollection = rdfImport.RDFToAdmission(newResultingGraph)
        print 'RdfToAdmission for token'
        overviewTableList = self.fromIntermediateStructureToOverviewTable(patientsMappingCollection,progressBar)
        print 'end mapping data token'
        return overviewTableList        

    def fromIntermediateStructureToOverviewTable(self, patientsMappingCollection,progressBar=None):
        overviewTableList = []
        counter = 1
        for admissionKey, intermediatePatientList in patientsMappingCollection.iteritems():
            progressBar.message = _('elaborating patient no.') + ' %d' % counter
            counter += 1
            progressBar.Step(relativeStep=True)
            patientOverviewDict = dict()
            for intermediateValue in intermediatePatientList:
                attributeFullName = '%s.%s.%s' % (intermediateValue['crfName'], intermediateValue['className'], intermediateValue['attributeName'])
                attributeValue = intermediateValue['value']
                if attributeFullName not in patientOverviewDict:
                    patientOverviewDict[attributeFullName] = []
                patientOverviewDict[attributeFullName].append(attributeValue)
            overviewTableList.append(patientOverviewDict)
        return overviewTableList
    
            
    def rebuildMappingDictFromRdfFile(self, path):
        from psconstants import appName
        import rdflib
        from rdflib import Namespace
        g = rdflib.Graph()
        
        #g.namespace_manager.bind("ns2", "http://xmlns.com/foaf/0.1/prosafe.core4")
        #g.namespace_manager.bind("ns3", "http://xmlns.com/foaf/0.1/prosafe.core4")
        data = g.parse(file=open(path, 'rb'), format="n3")
        attrrdict = {}
        for subj, pred, obj in data:
            try:
                rdfAdmissionKey = g.resource(subj).qname()
                admissionKey = rdfAdmissionKey.split(':')[1]
                rdfAdmissionKeyName = g.resource(pred).qname()
                admissionKeyName = rdfAdmissionKeyName.split(':')[1]
                if type(obj) == rdflib.term.Literal:
                    admissionValue = obj.format()
                else:
                    rdfAdmissionValue = g.resource(obj).qname()
                    admissionValue = rdfAdmissionValue.split(':')[1]
            except BaseException, e:
                print e
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print 'wrong parameters', subj, pred, obj
            admissionDict = {}
            
    def reverseMappedAdmissionsDataTable(self, path):
        from psconstants import appName
        import rdflib
        from rdflib import Namespace
        g = rdflib.Graph()
        data = g.parse(file=open(path, 'rb'), format="n3")
        #admission = Namespace("http://xmlns.com/foaf/0.1/")
        #admissionKeyName = Namespace("http://xmlns.com/foaf/0.1/")
        #admissionValue = Namespace("http://xmlns.com/foaf/0.1/")
        
        attrrdict = []
        for subj, pred, obj in data:
            progressiveObjectCode = 1
            if type(subj) == rdflib.term.BNode:
                print 'wow'
                continue
            rdfAdmissionKey = g.resource(subj).qname()
            admissionKey = rdfAdmissionKey.split(':')[1]
            rdfAdmissionKeyName = g.resource(pred).qname()
            admissionKeyName = rdfAdmissionKeyName.split(':')[1]
            if type(obj) == rdflib.term.Literal:
                admissionValue = obj.format()
            elif type(obj) == rdflib.term.BNode:
                for subj2, pred2, obj2 in g.triples((obj, None, None)):
                    predValue2 = g.resource(pred2).qname().split(':')[1]
                    admissionKeyName = predValue2
                    if type(obj2) == rdflib.term.Literal:
                        objValue2 = obj.format()
                    else:
                        objValue2 = g.resource(obj2).qname().split(':')[1]
                    try:
                        crfName, className, attributeName = admissionKeyName.replace('__', '.').split('.')
                    except BaseException, e:
                        PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                        print e, admissionKeyName
                        
                        
                    admissionDict['externalKey'] = admissionKey
                    admissionDict['crfName'] = crfName
                    admissionDict['className'] = className
                    admissionDict['attributeName'] = attributeName
                    admissionDict['value'] = objValue2
                    admissionDict['objectCode'] = progressiveObjectCode 
                    attrrdict.append(admissionDict)
                    
                progressiveObjectCode += 1
                continue
            else:
                rdfAdmissionValue = g.resource(obj).qname()
                admissionValue = rdfAdmissionValue.split(':')[1]

            admissionDict = {}
            try:
                crfName, className, attributeName = admissionKeyName.replace('__', '.').split('.')
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print e
            admissionDict['externalKey'] = admissionKey
            admissionDict['crfName'] = crfName
            admissionDict['className'] = className
            admissionDict['attributeName'] = attributeName
            if '#' in admissionValue:
                admissionValue = admissionValue.split('#')[1]
            admissionDict['value'] = admissionValue.replace('__', '.')
            
            attrrdict.append(admissionDict)
        
        return attrrdict
                
    
    
    def getRawDataFromAttributeDict(self, admissionKeysSet, attrrdict, rdict, crfrdict, progressBar):
        mappedAdmissions = {}
        from psconstants import appName
        import base64
        import psevaluator
        print 'CYCLING FOR ADMISSIONS'
        mappingCrfData = DataConfiguration()
        patientCrfVersion = ''
        oldPatientCrfVersion = ''
        for patientAdmission in rdict:
        
            admissionKey = patientAdmission['admissionKey']
            if admissionKey not in admissionKeysSet:
                continue
            progressBar.Step(stepValue=1, message=_('Getting raw data') + ' %s' % admissionKey, relativeStep=True)
            patientKey = patientAdmission['patientKey']
            crfs = [el for el in crfrdict if el['admissionKey'] == admissionKey]
            patientCrfVersion = [el['crfVersion'] for el in crfs if el['crfName'] == 'core'][0]
            
            if patientCrfVersion != oldPatientCrfVersion:
                oldPatientCrfVersion = patientCrfVersion
                try:
                    mappingCrfData = DataConfiguration()
                    mappingCrfData.readCrfConfiguration(os.path.join(self.configDirectory,self.crfFileDict['core'][patientCrfVersion]['filenames']['crf']))
                except BaseException, e:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                    print e
                    pass
                
            processedMultiInstance = []
            processedDynamic = []
            mappedAdmissions[admissionKey] = {}
            myList = [el for el in attrrdict if el['externalKey'] in [patientKey, admissionKey] and el['externalKey'] in admissionKeysSet]
            
            for attribute in myList:
                if attribute['externalKey'] in [patientKey, admissionKey]:
                    crfName = attribute['crfName']
                    crfVersion = patientCrfVersion.split('.')[0]
                    originalCrfVersion = crfVersion
                    className = attribute['className']
                    errorClasses = ['warningList', 'errorList']
                    noteClasses = ['comorbNote','admCondNote','complNote','intervNote','intervNonSurgNote','treatNote']
                    dynamicClassesList = ['procedureList', 'surgicalList', 'nonSurgicalList']
                    dischargeLetterClasses = ['anamnesi', 'anamnesiRemota', 'anamnesiFarm', 'anamnesiFarmly', 'anamnesiPhy', 'allergie', 'antibiotici', 'decorsoClinico', 'situazione', 'terapia', 'problemi']
                    if className in errorClasses or className in noteClasses or className in dynamicClassesList  or className in dischargeLetterClasses :
                        continue
                    
                    attributeName = attribute['attributeName']
                    if '%s.%s' % (crfName, className) in processedMultiInstance:
                        continue
                    attributeValue = attribute['value']
                    dataType = mappingCrfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
                    isMultiInstance = mappingCrfData.getPropertyForAttribute(crfName,className,attributeName,'multiInstance')
                    key = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, crfName, crfVersion, crfName, className, attributeName)
                    dataStorage = mappingCrfData.getPropertyForClass(crfName,className,'dataStorage')
                    dynamic = mappingCrfData.getPropertyForClass(crfName,className,'dynamic')
                    
                    if dataStorage != 'admission':
                        continue
                    if dynamic:
                        values = {}
                        sameDynClassAttrrdict = [el for el in myList if el['className'] == attribute['className']]
                        if '%s.%s' % (crfName, className) in processedDynamic:
                            continue
                        for sameDynClassAttribute in sameDynClassAttrrdict:
                            dataType = mappingCrfData.getPropertyForAttribute(crfName,className,sameDynClassAttribute['attributeName'],'dataType')
                            if sameDynClassAttribute['externalKey'] != admissionKey:
                                continue
                            if sameDynClassAttribute['objectCode'] not in values.keys():
                                values[sameDynClassAttribute['objectCode']] = {}
                            if dataType == 'codingset':
                                decodedAttributeValue = sameDynClassAttribute['value']
                                value = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s' % (appName, crfName, crfVersion, decodedAttributeValue.replace('.', '__'))
                            else:
                                value = sameDynClassAttribute['value']                                
                            tempKey = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, crfName, crfVersion, crfName, className, sameDynClassAttribute['attributeName'])
                            values[sameDynClassAttribute['objectCode']][tempKey] = value
                        processedDynamic.append('%s.%s' % (crfName, className))
                        newKey = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, crfName, crfVersion, crfName, className, sameDynClassAttribute['attributeName'])
                        mappedAdmissions[admissionKey][newKey] = values
                    elif isMultiInstance:
                        values = []
                        sameClassAttrrdict = [el for el in myList if el['className'] == attribute['className']]
                        for sameClassAttribute in sameClassAttrrdict:
                            if sameClassAttribute['externalKey'] != admissionKey:
                                continue
                            if dataType == 'codingset':
                                decodedAttributeValue = sameClassAttribute['value']
                                value = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s' % (appName, crfName, crfVersion, decodedAttributeValue.replace('.', '__'))                                
                            else:
                                value = sameDynClassAttribute['value']
                            newAttributeKey = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, crfName, crfVersion, crfName, className, sameClassAttribute['attributeName'])
                            if newAttributeKey not in mappedAdmissions[admissionKey]:
                                mappedAdmissions[admissionKey][newAttributeKey] = []
                            mappedAdmissions[admissionKey][newAttributeKey].append(value)
                        
                        processedMultiInstance.append('%s.%s' % (crfName, className))
                    else:
                        if dataType == 'codingset':
                            value = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s' % (appName, crfName, crfVersion, attributeValue.replace('.', '__'))                            
                        else:
                            value = attributeValue
                        mappedAdmissions[admissionKey][key] = value
            
            #adding patient key
            patientKeyForMappedDict = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, 'core', '', 'core', 'patientKey', 'value')
            patientKeyValueForMappedDict = '%s-%s%s#%s' % (appName, 'core', '', patientKey)
            mappedAdmissions[admissionKey][patientKeyForMappedDict] = patientKeyValueForMappedDict
            #adding admission key
            admissionKeyForMappedDict = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, 'core', '', 'core', 'admissionKey', 'value')
            admissionKeyValueForMappedDict = '%s-%s%s#%s' % (appName, 'core', '', admissionKey)
            mappedAdmissions[admissionKey][admissionKeyForMappedDict] = admissionKeyValueForMappedDict
            #adding crf version 
            crfVersionForMappedDict = 'http://giviti.marionegri.it/knowledgebase/%s-%s%s#%s__%s__%s' % (appName, 'core', '', 'core', 'originalCrfVersion', 'value')
            crfVersionValueForMappedDict = originalCrfVersion
            mappedAdmissions[admissionKey][crfVersionForMappedDict] = crfVersionValueForMappedDict
        print 'END CYCLING FOR ADMISSIONS'
        return mappedAdmissions
    
    def getMappedAdmissionsDataTable(self, admissionKeysSet=None, chooseGroupsCallback=None, translate=True, progressBar=None):
        self.beginCriticalSection()
        #query = "SELECT * FROM activeAdmissions"
        #rdict = self.queryManager.sendQuery(query)
        #print 'INSIDE MAPPING'
        #query = "SELECT crfName, crfVersion, statusValue, admissionKey FROM currentCrfStatus"
        #crfrdict = self.queryManager.sendQuery(query)
        rdict, crfrdict = self.getExportDictionaries(admissionKeysSet=admissionKeysSet)

        progressBar.Step(stepValue=1000, message=_('ready for cycling on admissions'))
        
        exportGroups = set()
        exportGroupsToTitles = dict()
        allAttributesToGroups = dict()
        allAttributesToWeights = dict()
        allAttributesToTitles = dict()

        admissionKeysToCrfs = dict()
        crfDataDict = dict()

        for record in crfrdict:
            progressBar.Step(stepValue=1, message=_('mapping admission') + ' %s' % record['admissionKey'], relativeStep=True)
            if record['crfName'] != 'core':
                continue
            if record['admissionKey'] not in admissionKeysSet:
                continue
            if record['admissionKey'] not in admissionKeysToCrfs:
                admissionKeysToCrfs[record['admissionKey']] = dict()
            admissionKeysToCrfs[record['admissionKey']][record['crfName']] = record['crfVersion']
            if record['crfName'] not in crfDataDict:
                crfDataDict[record['crfName']] = dict()
            if record['crfVersion'] not in crfDataDict[record['crfName']]:
                crfData = DataConfiguration()
                try:
                    crfData.readCrfConfiguration(os.path.join(self.configDirectory,self.crfFileDict[record['crfName']][record['crfVersion']]['filenames']['crf']))
                except BaseException, e:
                    PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                    print 'getMappedAdmissionsDataTable readCrfConfiguration error:', e
                languageFilePath = os.path.join(self.configDirectory,self.crfFileDict[record['crfName']][record['crfVersion']]['filenames']['languages'])
                f = open(languageFilePath, "r")
                xmlString = f.read()
                f.close()
                xmlDocument = etree.fromstring(xmlString)
                if xmlDocument.tag == 'languages':
                    for el in xmlDocument:
                        if el.tag == 'language' and el.get('name') and el.get('name') not in self.languages:
                            self.languages[el.get('name')] = dict()
                            self.languages[el.get('name')]['translations'] = dict()
                            self.languages[el.get('name')]['formats'] = dict()
                self.loadTranslations('English',languageFilePath)
                self.loadTranslations(self.userLanguage,languageFilePath)

                attributesToGroups = dict()
                for className in crfData.getClassNamesForCrf(record['crfName']):
                    for attributeName in crfData.getAttributeNamesForClass(record['crfName'],className):
                        
                        exportGroup = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'export')
                        exportWeight = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'exportWeight')
                        attributeFullName = crfData.joinAttributeName(record['crfName'],className,attributeName)
                        if not exportGroup:
                            exportGroup = '@@@1@@@'
                        if exportWeight != None:
                            exportWeight = int(exportWeight)
                        if exportGroup:
                            exportGroups.add(exportGroup)
                            exportGroupsToTitles[exportGroup] = self.translateString(exportGroup)
                            attributesToGroups[attributeFullName] = exportGroup
                            allAttributesToGroups[attributeFullName] = exportGroup
                            allAttributesToWeights[attributeFullName] = exportWeight
                        classLabel = crfData.getPropertyForClass(record['crfName'],className,'label')
                        if classLabel:
                            classLabel = self.translateString(classLabel)
                        attributeLabel = crfData.getPropertyForAttribute(record['crfName'],className,attributeName,'label')
                        if attributeLabel:
                            attributeLabel = self.translateString(attributeLabel)
                        if classLabel and attributeLabel:
                            if classLabel != attributeLabel:
                                title = classLabel + u" - " + attributeLabel
                            else:
                                title = attributeLabel
                        elif attributeLabel:
                            title = attributeLabel
                        else:
                            title = className + "."  + attributeName
                        allAttributesToTitles[attributeFullName] = title

                crfDataDict[record['crfName']][record['crfVersion']] = {'crfData':crfData, 'attributesToGroups':attributesToGroups}
        print 'CREATED CRFDATADICT'
        chosenGroups = chooseGroupsCallback(exportGroupsToTitles)
        if not chosenGroups:
            return None
        decoratedAttributeFullNames = [(allAttributesToGroups[el],allAttributesToWeights[el],el) for el in allAttributesToGroups if allAttributesToGroups[el] in chosenGroups]
        #TODO: translate before sorting? If not, make sure @@@ are sorted correctly
        decoratedAttributeFullNames.sort()
        
        columnNames = [el[2] for el in decoratedAttributeFullNames]
        #translatedColumnNames = [allAttributesToTitles[el[2]] for el in decoratedAttributeFullNames]
        #columnNamesToIndices = dict.fromkeys(columnNames,range(len(columnNames)))
        
        classNames = [el.split('.')[1] for el in columnNames]
        
        externalKeysForQuery = ",".join(["'%s'" % el for el in admissionKeysSet])
        classesForQuery = ','.join(["'%s'" % el for el in classNames])
        
        
        #query = "SELECT externalKey, objectData.objectCode objectCode, attributeData.localId localId, objectData.crfVersion crfVersion, objectData.crfName crfName, objectData.className className, attributeName, value, attributeData.multiInstanceNumber multiInstanceNumber FROM objectData JOIN attributeData ON objectData.objectCode = attributeData.objectCode WHERE objectData.objectCode IN (SELECT max(objectCode) FROM objectData WHERE objectData.crfName = 'core' and objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber) AND objectData.className IN (%s) and externalKey in (%s);" % (classesForQuery, externalKeysForQuery)
        #attrrdict = self.queryManager.sendQuery(query)
        admissionIds = self.jsonStore.search_ids({'activeAdmission':True})
        attrrdict = self.getAttrDict(admissionIds, admissionKeysSet, progressBar)
        
        print 'GETTING RAW DATA'
        result = self.getRawDataFromAttributeDict(admissionKeysSet, attrrdict, rdict, crfrdict, progressBar)
        
        self.endCriticalSection()
        return result
    
    
    def getTotalNumberOfErrors(self):
        numberOfErrors = 0
        for crfName in self.crfData.getCrfNames():
            numberOfErrors += self.evalErrors(crfName)
        return numberOfErrors

    def getTotalNumberOfUnacceptedWarnings(self):
        numberOfUnacceptedWarnings = 0
        for crfName in self.crfData.getCrfNames():
            numberOfUnacceptedWarnings += self.evalUnacceptedWarnings(crfName)
        return numberOfUnacceptedWarnings

    def evalErrors(self,crfName=None):
        if crfName == None:
            crfName = psc.coreCrfName
        errorList = self.dataSession.getAttributeValuesForClass(psc.coreCrfName,'errorList','errorList')
        if errorList == None:
            return 0
        crfErrorCount = 0
        for objectCode in errorList:
            classInfo = self.dataSession.getClassInfoForObjectCode(objectCode)
            if not classInfo:
                continue
            errorId = self.dataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],'errorId')
            errorCrf = self.dataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],'errorCrf')
            if crfName != psc.coreCrfName and crfName in errorCrf:
                crfErrorCount += 1
            elif crfName == psc.coreCrfName and (errorCrf == None or crfName in errorCrf):
                crfErrorCount += 1
        return crfErrorCount

    def evalUnacceptedWarnings(self,crfName=None):
        if crfName == None:
            crfName = psc.coreCrfName
        warningList = self.dataSession.getAttributeValuesForClass(psc.coreCrfName,'warningList','warningList')
        if warningList == None:
            return 0
        crfWarningCount = 0
        for objectCode in warningList:
            classInfo = self.dataSession.getClassInfoForObjectCode(objectCode)
            if not classInfo:
                continue
            warningId = self.dataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],'warningId')
            accepted = self.dataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],'accepted')
            warningCrf = self.dataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],'warningCrf')
            if accepted and accepted[0] == True:
                continue
            if crfName != psc.coreCrfName and crfName in warningCrf:
                crfWarningCount += 1
            elif crfName == psc.coreCrfName and (warningCrf == None or crfName in warningCrf):
                crfWarningCount += 1
        return crfWarningCount

    def getDischargeLetterFileName(self):
        return "%s.xml" % self.dataSession.admissionKey

    def getDischargeLetterBackupFileName(self):
        return os.path.splitext(self.getDischargeLetterFileName())[0] + '_bkp.xml'

    def getDischargeLetterFilePath(self):
        return os.path.join(self.dischargeLettersDirectory,self.getDischargeLetterFileName())

    def getDischargeLetterBackupFilePath(self):
        return os.path.join(self.dischargeLettersDirectory,self.getDischargeLetterBackupFileName())

    def getDischargeLetterModelFilePath(self):
        modelFileName = self.getDischargeLetterModelFileName()
        return os.path.join(self.dischargeLettersDirectory,modelFileName)

    def getDischargeLetterModelBackupFilePath(self):
        modelFileName = self.getDischargeLetterModelBackupFileName()
        return os.path.join(self.dischargeLettersDirectory,modelFileName)

    def getDischargeLetterMasterModelFileName(self):
        try:
            modelFileName = 'model_%s.xml' % self.centrecode[:2]
        except:
            modelFileName = 'model.xml'
        if modelFileName not in self.fileClient.getFileNamesInPath('dletters_master',relativeTo='version'):
            modelFileName = 'model_EN.xml'
        return modelFileName
 
    def getDischargeLetterModelFileName(self):
        return 'model.xml'

    def getDischargeLetterModelBackupFileName(self):
        return os.path.splitext(self.getDischargeLetterModelFileName())[0] + '_bkp.xml'

    def backupDischargeLetterModel(self):
        try:
            shutil.copyfile(self.getDischargeLetterModelFilePath(),self.getDischargeLetterModelBackupFilePath())
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass
            
    def backupDischargeLetter(self):
        try:
            shutil.copyfile(self.getDischargeLetterFilePath(),self.getDischargeLetterBackupFilePath())
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass

    def restoreDischargeLetterModelBackup(self):
        try:
            shutil.copyfile(self.getDischargeLetterModelBackupFilePath(),self.getDischargeLetterModelFilePath())
            os.remove(self.getDischargeLetterModelBackupFilePath())
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass

    def restoreDischargeLetterBackup(self):
        try:
            shutil.copyfile(self.getDischargeLetterBackupFilePath(),self.getDischargeLetterFilePath())
            os.remove(self.getDischargeLetterBackupFilePath())
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            pass

    def getDischargeLetterModelFromMaster(self):
        #TODO: handle errors
        modelFileName = self.getDischargeLetterModelFileName()
        if modelFileName not in self.fileClient.getFileNamesInPath('dletters',relativeTo='data'):
            self.fileClient.getFile('dletters_master',self.getDischargeLetterMasterModelFileName(),self.dischargeLettersDirectory,modelFileName,relativeTo='version')
            self.beginCriticalSection()
            self.fileClient.putFile(self.dischargeLettersDirectory,modelFileName,'dletters',modelFileName,relativeTo='data')
            self.endCriticalSection()
        else:
            self.fileClient.getFile('dletters',modelFileName,self.dischargeLettersDirectory,modelFileName,relativeTo='data')

    def getDischargeLetterModelBackupFromMaster(self):
        #TODO: handle errors
        modelFileName = self.getDischargeLetterModelFileName()
        self.fileClient.getFile('dletters_master',self.getDischargeLetterMasterModelFileName(),self.dischargeLettersDirectory,modelFileName,relativeTo='version')
 
    def getDischargeLetterFromMaster(self, forceGetModel=False):
        #TODO: handle errors
        dischargeLetterFileName = self.getDischargeLetterFileName()
        modelFileName = self.getDischargeLetterModelFileName()
        if forceGetModel or dischargeLetterFileName not in self.fileClient.getFileNamesInPath('dletters',relativeTo='data'):
            if modelFileName not in self.fileClient.getFileNamesInPath('dletters',relativeTo='data'):
                self.fileClient.getFile('dletters_master',self.getDischargeLetterMasterModelFileName(),self.dischargeLettersDirectory,modelFileName,relativeTo='version')
                self.beginCriticalSection()
                self.fileClient.putFile(self.dischargeLettersDirectory,modelFileName,'dletters',modelFileName,relativeTo='data')
                self.endCriticalSection()
            self.fileClient.getFile('dletters',modelFileName,self.dischargeLettersDirectory,dischargeLetterFileName,relativeTo='data')
        else:
            self.fileClient.getFile('dletters',dischargeLetterFileName,self.dischargeLettersDirectory,dischargeLetterFileName,relativeTo='data')

    def putDischargeLetterToMaster(self):
        #TODO: handle errors
        dischargeLetterFileName = self.getDischargeLetterFileName()
        self.beginCriticalSection()
        self.fileClient.putFile(self.dischargeLettersDirectory,dischargeLetterFileName,'dletters',dischargeLetterFileName,relativeTo='data')
        self.endCriticalSection()

    def putDischargeLetterModelToMaster(self):
        #TODO: handle errors
        self.beginCriticalSection()
        modelFileName = self.getDischargeLetterModelFileName()
        self.fileClient.putFile(self.dischargeLettersDirectory,modelFileName,'dletters',modelFileName,relativeTo='data')
        self.endCriticalSection()

    def getExcelExportOverviewModel(self):
        
        try:
            modelFileName = "descriptivetable_model_%s.xls" % self.centrecode[:2]
            self.getExcelExportOverviewModelFromMaster(modelFileName)
        except:
            modelFileName = "descriptivetable_model_EN.xls"
            self.getExcelExportOverviewModelFromMaster(modelFileName)        
        return modelFileName

    def getExcelExportOverviewModelFromMaster(self, modelFileName):
        if not os.listdir(os.path.join(os.getcwd(), 'xlsmodels')):
            #if modelFileName not in self.fileClient.getFileNamesInPath('xlsmodels'):
            self.fileClient.getFile('xlsmodels_master',modelFileName,self.xlsModelsDirectory,modelFileName,relativeTo='version')
            self.beginCriticalSection()
            self.fileClient.putFile(self.xlsModelsDirectory,modelFileName,'xlsmodels',modelFileName)
            self.endCriticalSection()
        else:
            self.fileClient.getFile(self.xlsModelsDirectory, modelFileName, self.xlsModelsDirectory, modelFileName)
        
    def buildFormatsDict(self):
        rawstr = r"""\|[\w.]*\|"""
        expandedre = re.compile(rawstr, re.IGNORECASE)
        formats = self.getAllFormats()
        formatsDict = dict()
        for itemFullName in formats:
            label = formats[itemFullName]['label']
            type = formats[itemFullName]['type']
            expression = formats[itemFullName]['expression']
            description = formats[itemFullName]['description']
            baseformat = formats[itemFullName]['baseformat']
            text = ''
            crfName = itemFullName.split('.')[0]
            if type == 'class':
                className = itemFullName.split('.')[1]
                classInstanceNumbers = self.dataSession.getInstanceNumbersForClass(crfName,className)
                textList = []
                for classInstanceNumber in classInstanceNumbers:
                    attributeVars = expandedre.finditer(expression)
                    for attributeVar in attributeVars:
                        attributeTag = attributeVar.group()
                        attributeName = attributeTag[1:-1]
                        attributeValues = self.dataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
                        attributeText = ', '.join(psevaluator.decode(attributeValues))
                        expression = expression.replace(attributeTag,repr(attributeText))
                    result = None
                    try:
                        exec(expression)
                    except BaseException, e:
                        PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                        result = None
                        print e
                    if result and result.strip():
                        textList.append(result)
                if not textList:
                    textList.append(self.translateString("NA"))
                text = '\n'.join(textList)
            elif type == 'attribute':
                className, attributeName = itemFullName.split('.')[1:]
                classInstanceNumbers = self.dataSession.getInstanceNumbersForClass(crfName,className)
                textList = []
                for classInstanceNumber in classInstanceNumbers:
                    attributeValues = self.dataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
                    attributeText = ', '.join(psevaluator.decode(attributeValues))
                    if attributeText.strip():
                        textList.append(attributeText)
                if not textList:
                    textList.append(self.translateString("NA"))
                text = '\n'.join(textList)
            else:
                itemName = itemFullName.split('.')[1]
                textList = []
                result = self.evaluator.eval(expression,noCache=True)
                if result:
                    textList.append(result)
                else:
                    textList.append(self.translateString("NA"))
                text = '\n'.join(textList)
            formatsDict['$%s$' % label] = text
        print formatsDict
        return formatsDict

    def getDischargeLetter2FileName(self):
        return "%s.zip" % self.dataSession.admissionKey

    def getDischargeLetter2FilePath(self):
        return os.path.join(self.dischargeLettersDirectory,self.getDischargeLetter2FileName())

    def getDischargeLetter2ModelFilePath(self):
        modelFileName = self.getDischargeLetter2ModelFileName()
        return os.path.join(self.dischargeLettersDirectory,modelFileName)

    def getDischargeLetter2MasterModelFilePath(self):
        masterModelFileName = self.getDischargeLetter2MasterModelFileName()
        return os.path.join(self.dischargeLettersDirectory,masterModelFileName)

    def getDischargeLetter2MasterModelFileName(self):
        try:
            #modelFileName = 'model_%s.zip' % self.centrecode[:2]
            #TODO: there is already in mainlogic a reference to countryCodes dict. See that reference for further detail
            countryCodes = {'IT':'Italiano', 'EN':'English', 'HU':'Magyar', 'PO':'Polski'}
            flagRaise = True
            for key, value in countryCodes.iteritems():
                if value == self.userLanguage:
                    modelFileName = 'model_%s.zip' % key
                    flagRaise = False
            if flagRaise:
                raise
        except:
            modelFileName = 'model_EN.zip'
        if modelFileName not in self.fileClient.getFileNamesInPath('dletters_master',relativeTo='version'):
            modelFileName = 'model_EN.zip'
        return modelFileName
 
    def getDischargeLetter2ModelFileName(self):
        return 'model.zip'

    def getDischargeLetter2MasterModelFromMaster(self):
        #TODO: handle errors
        masterModelFileName = self.getDischargeLetter2MasterModelFileName()
        self.fileClient.getFile('dletters_master',masterModelFileName,self.dischargeLettersDirectory,masterModelFileName,relativeTo='version')

    def getDischargeLetter2ModelFromMaster(self):
        #TODO: handle errors
        modelFileName = self.getDischargeLetter2ModelFileName()
        try:
            self.fileClient.getFile('dletters',modelFileName,self.dischargeLettersDirectory,modelFileName,relativeTo='data')
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            return
        if modelFileName not in self.fileClient.getFileNamesInPath('dletters',relativeTo='data'):
            self.fileClient.getFile('dletters_master',self.getDischargeLetter2MasterModelFileName(),self.dischargeLettersDirectory,modelFileName,relativeTo='version')
            self.beginCriticalSection()
            self.fileClient.putFile(self.dischargeLettersDirectory,modelFileName,'dletters',modelFileName,relativeTo='data')
            self.endCriticalSection()
        else:
            self.fileClient.getFile('dletters',modelFileName,self.dischargeLettersDirectory,modelFileName,relativeTo='data')

    def getDischargeLetter2FromMaster(self, forceGetModel=False):
        #TODO: handle errors
        dischargeLetterFileName = self.getDischargeLetter2FileName()
        modelFileName = self.getDischargeLetter2ModelFileName()
        if dischargeLetterFileName not in self.fileClient.getFileNamesInPath('dletters',relativeTo='data'):
            return
        self.fileClient.getFile('dletters',dischargeLetterFileName,self.dischargeLettersDirectory,dischargeLetterFileName,relativeTo='data')

    def putDischargeLetter2ToMaster(self):
        #TODO: handle errors
        dischargeLetterFileName = self.getDischargeLetter2FileName()
        self.beginCriticalSection()
        self.fileClient.putFile(self.dischargeLettersDirectory,dischargeLetterFileName,'dletters',dischargeLetterFileName,relativeTo='data')
        self.endCriticalSection()

    def putDischargeLetter2ModelToMaster(self):
        #TODO: handle errors
        self.beginCriticalSection()
        modelFileName = self.getDischargeLetter2ModelFileName()
        self.fileClient.putFile(self.dischargeLettersDirectory,modelFileName,'dletters',modelFileName,relativeTo='data')
        self.endCriticalSection()

    def compressDischargeLetter2Folder(self, folderName):
        self.compressLetterFolder(folderName,self.getDischargeLetter2FileName())
        
    def compressDischargeLetter2ModelFolder(self, folderName):
        self.compressLetterFolder(folderName,self.getDischargeLetter2ModelFileName(),checkFileSize=True)
 
    def uncompressDischargeLetter2Folder(self):
        return self.uncompressLetterFolder(self.getDischargeLetter2FileName())
   
    def uncompressDischargeLetter2ModelFolder(self):
        return self.uncompressLetterFolder(self.getDischargeLetter2ModelFileName())

    def uncompressDischargeLetter2MasterModelFolder(self):
        return self.uncompressLetterFolder(self.getDischargeLetter2MasterModelFileName())

    def compressLetterFolder(self, folderName, zipFileName, checkFileSize=False):
        try:
            from mainlogic import _
            folderFileNames = os.listdir(os.path.join(self.dischargeLettersDirectory,folderName))
            if checkFileSize:
                try:
                    atLeastOneLetterTooBig = False
                    for fileName in folderFileNames:
                        size = os.path.getsize(os.path.join(os.path.join(self.dischargeLettersDirectory,folderName), fileName))
                        if size > 7340032:
                            #should spread notification
                            self.addClientMessage('Advice', 'Discharge letter model is too heavy', 'medium', 'global', False, datetime.datetime.now())
                            self.notificationCenter.postNotification("ServerMessagesAvailable",self)
                            atLeastOneLetterTooBig = True
                            break
                    if not atLeastOneLetterTooBig:
                            clientMessage = {'title':'Advice', 'text':'Discharge letter model is too heavy', 'priority': 'medium', 'shown':False, 'type': 'global', 'repeatable':False}
                            self.removeClientMessage(clientMessage)
                            clientMessage = {'title':'Advice', 'text':'Discharge letter model is too heavy', 'priority': 'medium', 'shown':True, 'type': 'global', 'repeatable':False}
                            self.removeClientMessage(clientMessage)
                            self.notificationCenter.postNotification("ServerMessagesAvailable",self)
                except:
                    pass
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            folderFileNames = None
            pass
        
        if folderFileNames:
            zipFile = zipfile.ZipFile(os.path.join(self.dischargeLettersDirectory,zipFileName),mode='w')
            for fileName in folderFileNames:
                zipFile.write(os.path.join(self.dischargeLettersDirectory,folderName,fileName),fileName)
            zipFile.close()
        else:
            self.dischargeLetterModelFolder = '' 
            self.dischargeLetterMasterModelFolder = '' 
            zipFile = zipfile.ZipFile(os.path.join(self.dischargeLettersDirectory,zipFileName),mode='w')
            zipFile.write(self.dischargeLettersDirectory,'')
            zipFile.close()

    def uncompressLetterFolder(self, zipFileName):
        uncompressedFolderRootName = os.path.splitext(zipFileName)[0]
        i = 1
        done = False
        while not done:
            uncompressedFolderName = '%s_%02d' % (uncompressedFolderRootName, i)
            if not os.path.exists(os.path.join(self.dischargeLettersDirectory,uncompressedFolderName)):
                done = True
                break
            i += 1
        if not os.path.exists(os.path.join(self.dischargeLettersDirectory,zipFileName)):
            os.mkdir(os.path.join(self.dischargeLettersDirectory,uncompressedFolderName))
            return uncompressedFolderName
        try:
            zipFile = zipfile.ZipFile(os.path.join(self.dischargeLettersDirectory,zipFileName))
            zipFile.extractall(os.path.join(self.dischargeLettersDirectory,uncompressedFolderName))
            zipFile.close()
            return uncompressedFolderName
        except BaseException, e:
            PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
            print e
            return None

    def getLetterFolderPath(self, folderName):
        return os.path.join(self.dischargeLettersDirectory,folderName)

    def copyLetterMasterModel(self, masterModelFileName, modelFileName):

        self.openLetterMasterModelFolder(show=False)
        self.openLetterModelFolder(show=False)

        masterModelPath = os.path.join(self.getLetterFolderPath(self.dischargeLetterMasterModelFolder),masterModelFileName)
        modelPath = os.path.join(self.getLetterFolderPath(self.dischargeLetterModelFolder),modelFileName)

        shutil.copyfile(masterModelPath,modelPath)

    def composeLetter(self, modelFileName, letterFileName):

        self.openLetterFolder(show=False)
        self.openLetterModelFolder(show=False)

        modelPath = os.path.join(self.getLetterFolderPath(self.dischargeLetterModelFolder),modelFileName)
        letterPath = os.path.join(self.getLetterFolderPath(self.dischargeLetterFolder),letterFileName)

        import doctools
        formatsDict = self.buildFormatsDict()

        modelExtension = os.path.splitext(modelFileName)[1]
        if modelExtension == '.docx':
            try:
                modelDocument = doctools.docx_open(modelPath)
                letterDocument = modelDocument
                for label in formatsDict:
                    print label, formatsDict[label]
                    letterDocument = doctools.docx_replace(letterDocument,label.replace('$','\\$'),formatsDict[label])
                doctools.docx_save(letterDocument,modelPath,letterPath)
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print 'Error reading discharge letter model'

        elif modelExtension == '.odt':
            try:
                modelDocument = doctools.odt_open(modelPath)
                letterDocument = doctools.odt_replace(modelDocument,'\\$.*?\\$',formatsDict)
                doctools.odt_save(letterDocument,modelPath,letterPath)
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print 'Error reading discharge letter model'
            
        elif modelExtension == '.rtf':
            try:
                modelDocument = doctools.rtf_open(modelPath)
                letterDocument = doctools.rtf_replace(modelDocument,'\\$.*?\\$',formatsDict)
                doctools.rtf_save(letterDocument,letterPath)
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print 'Error reading discharge letter model'
           
    def openLetterFolder(self, show=False):

        if not self.dischargeLetterFolder:
            self.getDischargeLetter2FromMaster()
            self.dischargeLetterFolder = self.uncompressDischargeLetter2Folder()

        if show:
            letterPath = self.getLetterFolderPath(self.dischargeLetterFolder)
            self.showFolder(letterPath)

    def openLetterModelFolder(self, show=False):
        if not self.dischargeLetterModelFolder:
            self.getDischargeLetter2ModelFromMaster()
            self.dischargeLetterModelFolder = self.uncompressDischargeLetter2ModelFolder()

        if show:
            letterModelPath = self.getLetterFolderPath(self.dischargeLetterModelFolder)
            self.showFolder(letterModelPath)

    def openLetterMasterModelFolder(self, show=False):
        if not self.dischargeLetterMasterModelFolder:
            self.getDischargeLetter2MasterModelFromMaster()
            self.dischargeLetterMasterModelFolder = self.uncompressDischargeLetter2MasterModelFolder()

        if show:
            letterMasterModelPath = self.getLetterFolderPath(self.dischargeLetterMasterModelFolder)
            self.showFolder(letterMasterModelPath)

    def closeLetterFolder(self):
        if not self.dischargeLetterFolder:
            return
        self.compressDischargeLetter2Folder(self.dischargeLetterFolder)
        self.putDischargeLetter2ToMaster()

    def closeLetterModelFolder(self):
        if not self.dischargeLetterModelFolder:
            return
        self.compressDischargeLetter2ModelFolder(self.dischargeLetterModelFolder)
        self.putDischargeLetter2ModelToMaster()

    def cleanDischargeLetterDirectory(self):
        #TODO: remove zip files as well
        entries = os.listdir(self.dischargeLettersDirectory)
        dirs = [el for el in entries if os.path.isdir(os.path.join(self.dischargeLettersDirectory,el))]
        for dir in dirs:
            try:
                shutil.rmtree(os.path.join(self.dischargeLettersDirectory,dir))
            except BaseException, e:
                PsLogger().warning(['MainLogicTag','ExceptionTag'], str(e))
                print e

    def getLetterModelFileNamesDict(self):
        self.openLetterModelFolder(show=False)
        fileNames = os.listdir(self.getLetterFolderPath(self.dischargeLetterModelFolder))
        fileNamesDict = dict()
        fileNamesDict['docx'] = [el for el in fileNames if os.path.splitext(el)[1] == '.docx']
        fileNamesDict['odt'] = [el for el in fileNames if os.path.splitext(el)[1] == '.odt']
        fileNamesDict['rtf'] = [el for el in fileNames if os.path.splitext(el)[1] == '.rtf']
        return fileNamesDict

    def getLetterMasterModelFileNamesDict(self):
        self.openLetterMasterModelFolder(show=False)
        fileNames = os.listdir(self.getLetterFolderPath(self.dischargeLetterMasterModelFolder))
        fileNamesDict = dict()
        fileNamesDict['docx'] = [el for el in fileNames if os.path.splitext(el)[1] == '.docx']
        fileNamesDict['odt'] = [el for el in fileNames if os.path.splitext(el)[1] == '.odt']
        fileNamesDict['rtf'] = [el for el in fileNames if os.path.splitext(el)[1] == '.rtf']
        return fileNamesDict

    def getLetterMasterModelFileNames(self, format=None):
        if not format:
            return self.getLetterMasterModelFileNamesDict()
        return self.getLetterMasterModelFileNamesDict().get(format,[])

    def getNewLetterModelFileName(self, format, name, userModelName):
        nowdate = psevaluator.nowdateiso()
        nowdatelist = nowdate.split('-')
        nowdatelist.reverse()
        nowdate = '-'.join(nowdatelist)
        self.openLetterModelFolder(show=False)
        letterModelFolderPath = self.getLetterFolderPath(self.dischargeLetterModelFolder)
        letterModelFileName = ''
        done = False
        counter = 1
        while not done:
            if not userModelName:
                letterModelFileName = name + '-' + 'model-%02d.%s' % (counter,format)
            else:
                letterModelFileName = userModelName + '.' + format
            if not os.path.isfile(os.path.join(letterModelFolderPath, letterModelFileName)) and not userModelName:
                done = True
            if userModelName:
                letterModelFileName = letterModelFileName.split('.')[0] + '-' + '%02d.%s' % (counter,format)
                if not os.path.isfile(os.path.join(letterModelFolderPath, letterModelFileName)):
                    done = True
            counter += 1
        return letterModelFileName

    def getLetterModelFileNames(self, format=None):
        if not format:
            return self.getLetterModelFileNamesDict()
        return self.getLetterModelFileNamesDict().get(format,[])

    def getNewLetterFileName(self, format, letterName):
        admissionKey = self.dataSession.admissionKey
        nowdate = psevaluator.nowdateiso()
        nowdatelist = nowdate.split('-')
        nowdatelist.reverse()
        nowdate = '-'.join(nowdatelist)
        self.openLetterFolder(show=False)
        letterFolderPath = self.getLetterFolderPath(self.dischargeLetterFolder)
        letterFileName = ''
        done = False
        counter = 1
        while not done:
            letterFileName = letterName.split('-')[0] + '-' + '%s-%02d.%s' % (admissionKey,counter,format)
            if not os.path.isfile(os.path.join(letterFolderPath,letterFileName)):
                done = True
            counter += 1
        return  letterFileName

    def showFolder(self,path):
        import subprocess
        if sys.platform == 'darwin':
            subprocess.Popen(('open',path))
        elif sys.platform == 'win32':
            os.startfile(path)


    #####################
    #TODO: MOVE TO MASTER
    #####################
    def uploadDB(self):
 
        import urllib2
        import hashlib
       
        def md5_for_file(filename, block_size=1024 * 8):
            f = open(filename, 'rb')
            md5 = hashlib.md5()
            while True:
                data = f.read(block_size)
                if not data:
                    break
                md5.update(data)
            f.close()
            return md5.hexdigest()
   
        proxyAddress = self.getAppdataValue('network/proxy','address')
        username = self.getAppdataValue('network/proxy','username')
        password = self.getAppdataValue('network/proxy','password')
      
        fileMD5 =  md5_for_file(self.queryManager.localdata) 
        params = {'myCode': self.centrecode, 'myPassword':'12345678', 'myFile': open(self.queryManager.localdata,'rb'), 'fileMD5': fileMD5 }
        url = 'http://manda.marionegri.it:8080/prosafedata/upload'
        try:
            output = urllib2.urlopen(url,params)
            result = output.read()
      
            if result == 'OK':
                return True
            else:
                return False

        except BaseException,e:
            return False

        return False

