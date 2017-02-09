import sys
sys.path.append('./utils')

import Pyro.core
import Pyro.naming
import time
from threading import Thread
import os
import shutil
import datetime

from querymanager import QueryManager
from psjsonstore import JSONStore
from appdatamanager import AppdataManager
from filemanager import FileManager
from filemanager import createZip
from filemanager import md5_for_file
from bulletinmanager import BulletinManager
from diffpatchclient import DiffPatchClientManager
from networkmanager import NetworkManager
from networkmanager import QueryServer
from synchservice import synchService
from jsonsynchservice import jsonSynchService
import psconstants
from psconstants import abspath
from timesleep import MasterTimeSleep
from xml.etree import ElementTree as etree
from pslogging import PsLogger


class ProsafeMaster(object):

    def __init__(self, dataPath=abspath('data'), flags=dict()):

        self.dataPath = dataPath
        self.isEvaluatingAdmissions = False
        self.scriptPath = abspath('scriptlist')
        self.scriptList = []
        self.updatingScripts = False
        if not os.path.exists(self.scriptPath):
            os.mkdir(scriptPath)
        self.scriptList = [el for el in os.listdir(self.scriptPath) if el.split('.')[1] != 'pyc']
        sys.path.append('./scriptlist')
        
        if not os.path.isdir(self.dataPath):
            os.mkdir(self.dataPath)

        self.dlettersPath = os.path.join(self.dataPath,'dletters')
        if not os.path.isdir(self.dlettersPath):
            os.mkdir(self.dlettersPath)

        self.dataBackupPath = abspath('backup')
        if not os.path.isdir(self.dataBackupPath):
            os.mkdir(self.dataBackupPath)
 
        self.dataBackupZipPath = abspath('backupzip')
        if not os.path.isdir(self.dataBackupZipPath):
            os.mkdir(self.dataBackupZipPath)
        
        self.localhost = flags.get('localhost',False)
        self.nosynch = flags.get('nosynch',False)

        self.publicEncryptionKey = 'custom_encryption_key'
        self.useAPSW = True
        self.crfFileDict = None
        self.serverMessages = {}
        self.serverThread = None
        self.serverStarted = False
        self.serverAlive = False
        self.serverStopped = False
        self.serverThread = Thread(target=self.startServer)
        self.serverThread.daemon = True
        self.serverThread.start()
        while not self.serverStarted:
            if not MasterTimeSleep(1):
                break
       
        self.isConnected = False
        checkingThread = Thread(target = self.startConnectionLoop, kwargs = {'timeInterval':psconstants.CONNECTION_CHECK_TIME_INTERVAL})
        checkingThread.daemon = True
        checkingThread.start()

        evaluationThread = Thread(target = self.startEvaluationLoop, kwargs = {'timeInterval':psconstants.EVALUATION_TIME_INTERVAL})
        evaluationThread.daemon = True
        #evaluationThread.start()
        self.evaluationThread = evaluationThread

        backupThread = Thread(target = self.startBackupLoop, kwargs = {'timeInterval':psconstants.BACKUP_TIME_INTERVAL})
        backupThread.daemon = True
        backupThread.start()

        self.readmissionMainLogic = None
        self.readmissionAttributesQueue = []

        readmissionThread = Thread(target = self.startReadmissionLoop, kwargs = {'timeInterval':psconstants.READMISSION_TIME_INTERVAL})
        readmissionThread.daemon = True
        #readmissionThread.start()
        self.readmissionThread = readmissionThread
        
        
        if not self.nosynch:
            if 'scripts' in psconstants.toolBarApplications:
                fetchScriptsFromServerThread = Thread(target = self.startFetchScriptsFromServerLoop, kwargs = {'timeInterval':psconstants.SCRIPTS_CHECK_TIME_INTERVAL})
                fetchScriptsFromServerThread.daemon = True
                fetchScriptsFromServerThread.start()
            
            activeCrfsThread = Thread(target = self.startActiveCrfsLoop, kwargs = {'timeInterval':psconstants.ACTIVE_CRFS_TIME_INTERVAL})
            activeCrfsThread.daemon = True
            activeCrfsThread.start()

            updateThread = Thread(target = self.startSoftwareUpdateLoop, kwargs = {'timeInterval':psconstants.SOFTWARE_UPDATE_TIME_INTERVAL})
            updateThread.daemon = True
            updateThread.start()
            
            if 'notification' in psconstants.toolBarApplications:
                fetchMessagesThread = Thread(target = self.startFetchMessagesLoop, kwargs = {'timeInterval':psconstants.SERVER_MESSAGES_TIME_INTERVAL})
                fetchMessagesThread.daemon = True
                fetchMessagesThread.start()

            #self.diffPatchManager = DiffPatchClientManager(self.centreCode,self.crfUpdatedCallback)
            #self.diffPatchManager.startLoop(abspath('config_master',True),psconstants.DIFFPATCH_URL,psconstants.CRF_SYNCH_TIME_INTERVAL)
            #while not self.diffPatchManager.firstRun:
            #    if not MasterTimeSleep(1):
            #        break
                
            centreCode = self.appdataManager.getAppdataValue('centre','centreCode')
            #TODO JSON: synch service with jsonstore
            localdb = os.path.join(self.dataPath,'prosafestore.sqlite')
            #localdb = abspath(self.queryManager.dbname)
            
            self.databaseSynchService = jsonSynchService(localdb, encryptionKey=self.publicEncryptionKey, useAPSW=self.useAPSW);
            self.startSynchServiceLoop(timeInterval = psconstants.DB_SYNCH_TIME_INTERVAL)
    
    def createBackupZipFile(self, backupPath=None):
        print 'Performing backup'
        bkpfiles = os.listdir(self.dataBackupPath)
        for file in bkpfiles:
            try:
                os.remove(os.path.join(self.dataBackupPath,file))
            except BaseException, e:
                PsLogger().warning(['ProsafeMasterTag','ExceptionTag'], str(e))
                print e, file
        self.appdataManager.copyToPath(self.dataBackupPath)
        #self.queryManager.copyToPath(self.dataBackupPath)
        self.jsonStore.copyToPath(self.dataBackupPath)
        dletterFiles = os.listdir(self.dlettersPath)
        for file in dletterFiles:
            shutil.copy(os.path.join(self.dlettersPath,file),self.dataBackupPath)
        tmpBackupFileName = os.path.join(self.dataBackupZipPath,'databkp_tmp.zip')
        tmp2BackupFileName = os.path.join(self.dataBackupZipPath,'databkp_tmp2.zip')
        backupFileName = os.path.join(self.dataBackupZipPath,'databkp.zip')
        setPassword = None
        if backupPath:
            setPassword = self.publicEncryptionKey
        createZip(self.dataBackupPath,tmpBackupFileName,setPassword)
        removeTmp2 = False
        if os.path.isfile(backupFileName):
            if os.path.exists(tmp2BackupFileName):
                os.remove(tmp2BackupFileName)
            os.rename(backupFileName,tmp2BackupFileName)
            removeTmp2 = True
        os.rename(tmpBackupFileName,backupFileName)
        if removeTmp2:
            os.remove(tmp2BackupFileName)
        historyFileName = "databkp-%s.zip" % datetime.date.today().isoformat()
        historyFiles = [el for el in os.listdir(self.dataBackupZipPath) if el.startswith('databkp-')]
        if historyFileName in historyFiles and os.path.exists(os.path.join(self.dataBackupZipPath,historyFileName)):
            os.remove(os.path.join(self.dataBackupZipPath,historyFileName))
        elif len(historyFiles) > 10:
            mtimesToNames = dict(zip([os.path.getmtime(os.path.join(self.dataBackupZipPath,el)) for el in historyFiles],historyFiles))
            minMTime = min(mtimesToNames.keys())
            historyFileName = mtimesToNames[minMTime]
            os.remove(os.path.join(self.dataBackupZipPath,mtimesToNames[minMTime]))
        if not backupPath:
            shutil.copyfile(os.path.join(self.dataBackupZipPath,'databkp.zip'),os.path.join(self.dataBackupZipPath,historyFileName))
        else:
            f = open(backupFileName, 'rb')
            file = f.read()
            f.close()
            #encrypt file
            from blowfish import Blowfish
            fileCipher = Blowfish(self.publicEncryptionKey)
            fileCipher.initCTR()
            file = fileCipher.encryptCTR(file)
            f = open(backupFileName, 'wb')
            f.write(file)
            f.close()
            shutil.copyfile(backupFileName,backupPath)
        self.postNotificationOnBulletin('BackupAvailable')

    def startBackupLoop(self, timeInterval):
        PsLogger().info('ProsafeMasterTag', "startBackupLoop")
        try:
            self.createBackupZipFile()
        except:
            pass
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            try:
                self.createBackupZipFile()
            except:
                pass
        PsLogger().info('ProsafeMasterTag', "endBackupLoop")
 
    def startConnectionLoop(self, timeInterval):
        PsLogger().info('ProsafeMasterTag', "startConnectionLoop")
        self.checkConnection()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.checkConnection()
        PsLogger().info('ProsafeMasterTag', "endConnectionLoop")
 
    def startSoftwareUpdateLoop(self, timeInterval):
        #sleeping on first cycle to let checkConnection act before checkSoftwareUpdate
        PsLogger().info('ProsafeMasterTag', "startSoftwareUpdateLoop")
        self.initializationTimeSleepLoop()
        self.checkSoftwareUpdate()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.checkSoftwareUpdate()
        PsLogger().info('ProsafeMasterTag', "endSoftwareUpdateLoop")
 
    def startActiveCrfsLoop(self, timeInterval):
        PsLogger().info('ProsafeMasterTag', "startActiveCrfsLoop")
        self.initializationTimeSleepLoop()
        MasterTimeSleep(60)
        self.updateActiveCrfs()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.updateActiveCrfs()
        PsLogger().info('ProsafeMasterTag', "endActiveCrfsLoop")
            
    def startSynchServiceLoop(self, timeInterval, forced=False):
        PsLogger().info('ProsafeMasterTag', "startSynchServiceLoop")
        print "started synchservice loop"
        self.synchronizing = True
        synchServiceThread = Thread(target = self.synchServiceLoop, kwargs = {'timeInterval':timeInterval, 'forced':forced})
        synchServiceThread.daemon = True
        synchServiceThread.start()
        PsLogger().info('ProsafeMasterTag', "endSynchServiceLoop")
        
    def synchServiceLoop(self, timeInterval, forced=False):
        
        while self.databaseSynchService.loopActive:
            if self.jsonStoreMigrationIsNeeded() or self.needsRestore():
                print 'SYNCH BLOCKED'
            elif QueryServer(self.centreCode,'SynchDB','Allow',True,forced):
                self.synchronizing = True
                try:
                    print "Trying db synchronization"
                    centreCode = self.appdataManager.getAppdataValue('centre','centreCode')
                    self.databaseSynchService.synchronize(centreCode=centreCode)
                    QueryServer(self.centreCode,'SynchDB','Done',True)
                    self.synchronizing = False
                    if forced:
                        break
                except Exception, e:
                    PsLogger().warning(['ProsafeMasterTag','ExceptionTag'], str(e))
                    print "DB Synchronization failed. " + str(e)
            if not MasterTimeSleep(timeInterval):
                break
        

    def checkConnection(self):
        proxyAddress = self.appdataManager.getAppdataValue('network/proxy','address')
        username = self.appdataManager.getAppdataValue('network/proxy','username')
        password = self.appdataManager.getAppdataValue('network/proxy','password')
        self.isConnected = self.networkManager.tryConnection(proxyAddress,username,password) 

    def jsonStoreMigrationIsNeeded(self):
        dbFileName = os.path.join(self.dataPath,'prosafedata.sqlite')
        if self.jsonStore.search_ids({'migration':'complete'}) or not os.path.isfile(dbFileName):
            self.bulletinManager.setMigrationFlag(False)
            return False
        self.bulletinManager.setMigrationFlag(True)
        return True
        
    def needsRestore(self):
        return self.jsonStore.needsRestore()
            
    def migrateToStore(self, updateProgressStatus):
        if not self.jsonStoreMigrationIsNeeded():            
            return True
        import datetime
        migrationTime = datetime.datetime.now()
        from migrationmainlogic import MigrationMainLogic
        from notificationcenter import NotificationCenter
        from mainlogic import _
        migrationMainLogic = MigrationMainLogic({'testing':False,'localhost':True,'nosynch':True,'asclient':True,'nolanguage':True,'staticclientkey':'Migration','notificationcenter':NotificationCenter()})
        migrationMainLogic.loadAppdata()
        migrationMainLogic.loadConfig(crfFileDict=self.crfFileDict)
        migrationMainLogic.inputUserKey = 'PROSAFE'
        migrationMainLogic.username = 'PROSAFE'
        migrationMainLogic.userType = psconstants.USER_ADMIN
        dbFileName = os.path.join(self.dataPath,'prosafedata.sqlite')
        updateProgressStatus.Step(stepValue=50, message=_("Loading original database"))
        migrationMainLogic.queryManager = QueryManager(dbFileName,self.publicEncryptionKey, useAPSW=self.useAPSW, activeClientKeysCallback=self.bulletinManager.getActiveClientKeys, centreCode=self.centreCode)
        migrationMainLogic.queryManager.sendQuery("SELECT MAX(localId) FROM admission")
        admissionStartingId = migrationMainLogic.queryManager.sendQuery("SELECT MAX(localId) as localId FROM admission")[0]['localId']
        patientStartingId = migrationMainLogic.queryManager.sendQuery("SELECT MAX(localId) as localId FROM patient")[0]['localId']
        self.jsonStore.setStartingUUID('admission',admissionStartingId)
        self.jsonStore.setStartingUUID('patient',patientStartingId)
        
        updateProgressStatus.Step(stepValue=50, message=_("Getting admissions"))
        migrationMainLogic.gridData = migrationMainLogic.getAllActiveAdmissionsData()
        #print 'migrationMainLogic.gridData', migrationMainLogic.gridData
        for row in migrationMainLogic.gridData:
            admissionKey = row['admissionKey']
            if updateProgressStatus.imStopping:
                return False
            updateProgressStatus.Step(stepValue=1, message=_("MIGRATING") + " %s" % admissionKey)
            loaded = migrationMainLogic.loadAdmission(admissionKey)
            if not loaded:
                print 'not loaded'
                continue
            if row['readmissionKey']:
                migrationMainLogic.dataSession.readmissionKey = row['readmissionKey']
            migrationMainLogic.saveData()
            migrationMainLogic.exitAdmission()

        self.jsonStore.create({'migration':'complete'})
        
        migrationEndedTime = datetime.datetime.now()
        f = open('timinglog.txt', 'wb')
        f.write('MIGRATION TIME: %s\n' % str((migrationEndedTime - migrationTime).seconds))
        f.close()
        print 'MIGRATION TIME: %s\n' % str((migrationEndedTime - migrationTime).seconds)
        self.bulletinManager.migrationFlag = False
        return True

    def startEvaluationLoop(self, timeInterval):
        from mainlogic import MainLogic
        from notificationcenter import NotificationCenter
        self.evaluationMainLogic = MainLogic({'testing':False,'localhost':True,'nosynch':True,'asclient':True,'nolanguage':True,'staticclientkey':'Evaluation','notificationcenter':NotificationCenter()})
        self.evaluationMainLogic.loadAppdata()
        self.evaluationMainLogic.loadConfig(crfFileDict=self.crfFileDict)
        self.evaluationMainLogic.inputUserKey = 'PROSAFE'
        self.evaluationMainLogic.username = 'PROSAFE'
        self.evaluationMainLogic.userType = psconstants.USER_ADMIN

        self.performEvaluation()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.performEvaluation()

    def performEvaluation(self): 
        #print 'EVALUATING'
        self.evaluationMainLogic.gridData = self.evaluationMainLogic.getAllActiveAdmissionsData()
        admissionsToUpdate = self.evaluationMainLogic.checkCrfVersionOfAdmissions()
        self.isEvaluatingAdmissions = True
        for i, admissionKey in enumerate(admissionsToUpdate):
            if not MasterTimeSleep(1):
                break
            self.evaluationMainLogic.openSaveAndCloseAdmission(admissionKey)
        self.isEvaluatingAdmissions = False

    def setupReadmissionMainLogic(self):
        from mainlogic import MainLogic
        from notificationcenter import NotificationCenter
        import notificationcenter
        self.readmissionMainLogic = MainLogic({'testing':False,'localhost':True,'nosynch':True,'asclient':True,'nolanguage':True,'staticclientkey':'Readmission','notificationcenter':NotificationCenter()})
        #self.readmissionMainLogic = MainLogic({'testing':False,'localhost':True,'nosynch':True,'asclient':True,'nolanguage':True,'staticclientkey':'Readmission'})
        self.readmissionMainLogic.loadAppdata()
        self.readmissionMainLogic.loadConfig(crfFileDict=self.crfFileDict)
        self.readmissionMainLogic.inputUserKey = 'PROSAFE'
        self.readmissionMainLogic.username = 'PROSAFE'
        self.readmissionMainLogic.userType = psconstants.USER_ADMIN
        notificationcenter.notificationCenter.addObserver(self,self.requestUpdateReadmissionAttributes,'ShouldUpdateReadmissionAttributes')
 
    def requestUpdateReadmissionAttributes(self, notifyingObject, userInfo=None):
        print 'READMISSION QUEUE PRE', userInfo, self.readmissionAttributesQueue
        for admissionKey in userInfo['admissionKeys']:
            self.readmissionAttributesQueue.append({'admissionKey':admissionKey, 'attributes':userInfo['attributes']})
        print 'READMISSION QUEUE', userInfo, self.readmissionAttributesQueue

    def startReadmissionLoop(self, timeInterval):
        self.setupReadmissionMainLogic()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.performReadmission()

    def performReadmission(self): 
        #print 'READMISSION LOOP'
        readmissionAttributesQueue = self.readmissionAttributesQueue[:]
        for item in readmissionAttributesQueue:
            admissionKey = item['admissionKey']
            attributes = item['attributes']
            print 'OPENING ADMISSION', admissionKey
            loaded = self.readmissionMainLogic.loadAdmission(admissionKey)
            if not loaded:
                continue
            #TODO: update admission with data
            dataUpdate = dict()
            for row in attributes:
                attributeFullName = "%s.%s.%s" % (row['crfName'],row['className'],row['attributeName'])
                multiInstanceNumber = row['multiInstanceNumber']
                if attributeFullName not in dataUpdate:
                    dataUpdate[attributeFullName] = []
                dataUpdate[attributeFullName].insert(multiInstanceNumber-1,row['value'])
            for attributeFullName in dataUpdate:
                crfName, className, attributeName = attributeFullName.split('.')
                attributeValue = dataUpdate[attributeFullName]
                if not self.readmissionMainLogic.dataSession.isMultiInstance(crfName,className,attributeName):
                    attributeValue = attributeValue[0]
                #TODO: extend to multi instance classes?
                self.readmissionMainLogic.dataSession.updateDataNoNotify(crfName,className,1,attributeName,attributeValue)
            self.readmissionMainLogic.saveData()
            self.readmissionMainLogic.exitAdmission()
            try:
                self.readmissionAttributesQueue.remove(item)
            except:
                pass
        #print 'END READMISSION LOOP'

    def checkSoftwareUpdate(self):
        updated = self.networkManager.checkSoftwareUpdate(self.centreCode, self.stopServices)
        if updated:
            self.postNotificationOnBulletin('SoftwareUpdated')
            
    
    def startFetchMessagesLoop(self, timeInterval):
        #sleeping on first cycle to let checkConnection act before checkSoftwareUpdate
        PsLogger().info('ProsafeMasterTag', "startFetchMessagesLoop")
        self.initializationTimeSleepLoop(30)
        self.fetchMessagesFromServer()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.fetchMessagesFromServer()
        PsLogger().info('ProsafeMasterTag', "endFetchMessagesLoop")
    
    def initializationTimeSleepLoop(self, numberOfTries=15):
        PsLogger().info('ProsafeMasterTag', "IntializationTimeSleepLoop")
        timeSleepCounter = 1
        while not self.isConnected:
            MasterTimeSleep(1)
            timeSleepCounter += 1
            if timeSleepCounter == numberOfTries:
                break
        PsLogger().info('ProsafeMasterTag', "endInitializationTimeSleepLoop")
                
    def startFetchScriptsFromServerLoop(self, timeInterval):
        PsLogger().info('ProsafeMasterTag', "startFetchScriptsFromServerLoop")
        self.initializationTimeSleepLoop()
        MasterTimeSleep(60)
        self.fetchScriptsFromServer()
        while True:
            if not MasterTimeSleep(timeInterval):
                break
            self.fetchScriptsFromServer()
        PsLogger().info('ProsafeMasterTag', "endFetchScriptsFromServerLoop")
            
    def fetchScriptsFromServer(self): 
        print 'fetching scripts'
        self.updatingScripts = True
        scriptListNew = self.networkManager.fetchScriptsFromServer(self.centreCode, self.scriptPath)
        self.encryptScripts(scriptListNew)
        self.scriptList.extend(scriptListNew)            
        self.updatingScripts = False
        print 'fetched any script'
        
    def encryptScripts(self, scriptListNew):
        #def publicEncryptDecryptString(self, inputValue, operation):
        for file in scriptListNew:
            try:
                currentFileName = os.path.join(self.scriptPath, file)
                if not os.path.exists(currentFileName):
                    continue
                f = open(currentFileName, 'rb')
                fileContent = f.read()
                f.close()
                encryptedFileContent = self.appdataManager.publicEncryptDecryptString(fileContent, 'encrypt')
                f = open(currentFileName, 'wb')
                f.write(encryptedFileContent)
                f.close()
            except BaseException, e:
                PsLogger().warning(['ProsafeMasterTag','ExceptionTag'], str(e))
                print 'encryptScripts', e
                pass
        
    
    def fetchMessagesFromServer(self):
        self.serverMessages = self.networkManager.fetchMessagesFromServer(self.centreCode)
        self.bulletinManager.setServerMessages(self.serverMessages)
            
    def askPermissionToShutDown(self):
        activeClientKeys = self.bulletinManager.getActiveClientKeys()
        activeClientSet = set(activeClientKeys)
        respondingClientSet = set()
        #TODO: implement timeout
        counter = 0
        while activeClientSet - respondingClientSet and counter < 180:
            self.postNotificationOnBulletin('MasterIsShuttingDown')
            time.sleep(1)
            for entry in self.bulletinManager.bulletin:
                if self.bulletinManager.bulletin[entry]['name'] == 'OKToShutDownMaster':
                    respondingClientSet.add(entry[0])
            activeClientKeys = self.bulletinManager.getActiveClientKeys()
            activeClientSet.union(activeClientKeys)
            counter += 1
        counter = 0
        while self.readmissionAttributesQueue and counter < 180:
            time.sleep(1)
            counter += 1
 
    def stopServices(self, askPermission=True):

        self.postNotificationOnBulletin('MasterClientShouldQuit')
        if askPermission:
            self.askPermissionToShutDown()

        print "Stopping services"
        try:
            self.nameServerStarter.shutdown()
        except BaseException, e:
            PsLogger().warning(['ProsafeMasterTag','ExceptionTag'], str(e))
            print e

        import timesleep
        timesleep.MasterAlive = False
        self.serverAlive = False
        #time.sleep(2)
        print "Services stopped"

    def startServer(self):
        Pyro.config.PYRO_MULTITHREADED = 0
        Pyro.config.PYRO_PORT = psconstants.PYRO_PORT
        Pyro.config.PYRO_NS_PORT = psconstants.PYRO_NS_PORT
        Pyro.config.PYRO_NS_BC_PORT = psconstants.PYRO_NS_BC_PORT

        if self.localhost:
            Pyro.config.PYRO_HOST = 'localhost'
            Pyro.config.PYRO_PUBLISHHOST = 'localhost'
            Pyro.config.PYRO_NS_HOSTNAME = 'localhost'
            Pyro.config.PYRO_NS_BC_ADDR = 'localhost'
 
        print "Launching Pyro Name Server"
        nameServerStarter = None
        try:
            ns = Pyro.naming.NameServerLocator().getNS()
        except:
            nameServerStarter = Pyro.naming.NameServerStarter()
            nameServerThread = Thread(target = nameServerStarter.start, kwargs={'allowmultiple':1})
            nameServerThread.daemon = True
            nameServerThread.start()
            nameServerStarter.waitUntilStarted(None)
            self.nameServerStarter = nameServerStarter
    
        print "Launching Pyro Server"
        Pyro.core.initServer()
        daemon = Pyro.core.Daemon()
        ns = Pyro.naming.NameServerLocator().getNS()
        daemon.useNameServer(ns)
        if nameServerStarter:
            nameServerStarter.daemon = daemon

        dbFileName = os.path.join(self.dataPath,'prosafedata.sqlite')
        storeFileName = os.path.join(self.dataPath,'prosafestore.sqlite')
        appdataFileName = os.path.join(self.dataPath,'appdata.xml')

        self.fileManager = FileManager(self.dataPath)
        self.bulletinManager = BulletinManager()
        self.networkManager = NetworkManager()
        self.appdataManager = AppdataManager(appdataFileName,self.publicEncryptionKey)
        
        self.appdataManager.loadAppdata()
        self.centreCode = self.appdataManager.getAppdataValue('centre','centreCode')       
        print "*" * 10
        print self.centreCode
        print "*" * 10

        self.jsonStore = JSONStore(storeFileName, self.publicEncryptionKey, activeClientKeysCallback=self.bulletinManager.getActiveClientKeys, centreCode=self.centreCode)
        for serviceName in ["querymanager", "appdatamanager", "filemanager", "bulletinmanager", "networkmanager", "jsonstore"]:
            try:
                #pass
                ns.unregister(serviceName)
            except:
                pass
        
        #uri = daemon.connect(self.queryManager,"querymanager")
        #try:
        #    uri = daemon.connect(self.jsonStore,"jsonstore")
        #except BaseException, e:
        #    print 'daemon connection error:', e
        uri = daemon.connect(self.jsonStore,"jsonstore")
        uri = daemon.connect(self.appdataManager,"appdatamanager")
        uri = daemon.connect(self.fileManager,"filemanager")
        uri = daemon.connect(self.bulletinManager,"bulletinmanager")
        uri = daemon.connect(self.networkManager,"networkmanager")

        print "The daemon runs on port:",daemon.port
        print "The object's uri is:",uri
    
        self.serverStarted = True
        self.serverAlive = True
        self.serverStopped = False
        daemon.requestLoop(condition = self.shouldServerBeAlive)
        self.serverStopped = True

    def shouldServerBeAlive(self):
        return self.serverAlive

    def postNotificationOnBulletin(self, name, userInfo=None):
        message = {'name':name, 'userInfo':userInfo}
        self.bulletinManager.post('MASTER',message)

    def updateActiveCrfs(self):
        print 'updateActiveCrfs'
        activePetals = self.networkManager.getActivePetals(self.centreCode)
        if activePetals == False:
            return

        crfsEl = etree.Element('crfs')

        crfEl = etree.SubElement(crfsEl,'crf')
        crfEl.set('name',psconstants.coreCrfName)

        for petal in activePetals:
            crfEl = etree.SubElement(crfsEl,'crf')
            crfEl.set('name',petal['name'])
            if not petal.get('startDate'):
                crfEl.set('minValidDate','2010-01-01')
            else:
                startDate = datetime.datetime.strptime(petal['startDate'], "%d-%m-%Y").isoformat()[:10]
                crfEl.set('minValidDate',startDate)
                print 'petal', petal['name'], 'should start in date ', startDate
               
            if petal.get('endDate'):
                endDate = datetime.datetime.strptime(petal['endDate'], "%d-%m-%Y").isoformat()[:10]
                crfEl.set('maxValidDate',endDate)
                print 'petal', petal['name'], 'should stop in date ', endDate

        if self.appdataManager:
            self.appdataManager.setAppdataElement('centre',crfsEl)

    def crfUpdatedCallback(self, result):
        self.updateActiveCrfs()
        userInfo = {'filenames': result}
        self.postNotificationOnBulletin('CRFUpdated',userInfo)


if __name__=='__main__':

    localhost = False
    if '--localhost' in sys.argv and not getattr(sys,"frozen",None):
        print 'Starting ProsafeMaster in localhost mode'
        localhost = True

    nosynch = False
    if '--nosynch' in sys.argv:
        print 'Starting ProsafeMaster with synchronization switched off'
        nosynch = True

    noEsky = False
    try:
        import esky
    except:
        noEsky = True

    if getattr(sys,"frozen",False) and not noEsky:
        eskyApp = esky.Esky(sys.executable, psconstants.ESKY_FILES_DOWNLOAD_URL)
        #change to real path of python program
        target = esky.join_app_version(eskyApp.name,eskyApp.version,eskyApp.platform)
        target = os.path.join(eskyApp.appdir,target)
        os.chdir(target)

    master = ProsafeMaster(abspath('data'),flags={'localhost':localhost,'nosynch':nosynch})

    try:
        while True:
            if not MasterTimeSleep(1):
                break
    except KeyboardInterrupt:
        pass

    #TODO: post on bulletin, wait for client approval (bulletin knows who is around) or force quitting anyway
    print
    print "Shutting down Prosafe master"
    master.postNotificationOnBulletin('MasterIsShuttingDown')
    MasterTimeSleep(1)

