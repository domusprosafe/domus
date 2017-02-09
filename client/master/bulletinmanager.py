import Pyro.core
import datetime
from psversion import PROSAFE_VERSION

class BulletinManager(Pyro.core.ObjBase):
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.bulletin = dict()
        self.lastCleanupTime = None 
        self.cleanupInterval = 10
        self.clientCounter = 0
        self.staticClientKeys = set()
        self.activeClientKeys = set()
        self.oldActiveClientKeys = set()
        self.migrationFlag = False
        self.serverMessages = None

    def getNewClientKey(self):
        while self.clientCounter in self.staticClientKeys:
            self.clientCounter += 1
        return self.clientCounter

    def registerStaticClientKey(self,clientKey):
        if clientKey in self.activeClientKeys:
            raise BaseException("Cannot register static client key if key is already taken")
        self.staticClientKeys.add(clientKey)

    def getActiveClientKeys(self):
        return list(self.activeClientKeys.union(self.oldActiveClientKeys))

    def getActiveNonStaticClientKeys(self):
        return list(self.activeClientKeys.union(self.oldActiveClientKeys).difference(self.staticClientKeys))

    def getCleanupInterval(self):
        return self.cleanupInterval

    def post(self, clientKey, message):
        currentTime = datetime.datetime.now() 
        self.bulletin[(clientKey,currentTime)] = message
        return True

    def cleanup(self, cleanupTime):
        bulletinKeys = self.bulletin.keys()
        self.oldActiveClientKeys = self.activeClientKeys
        self.activeClientKeys = set()
        for entry in bulletinKeys:
            if (cleanupTime - entry[1]).seconds > self.cleanupInterval:
                self.bulletin.pop(entry)
        self.lastCleanupTime = cleanupTime

    def getMigrationFlag(self):
        return self.migrationFlag
        
    def setMigrationFlag(self, migrationFlag):
        self.migrationFlag = migrationFlag
        
        
    #NOTIFICATION MANAGEMENET
    def getServerMessages(self):
        return self.serverMessages
        
    def addServerMessage(self, title, text, priority, type=None, repeatable=None, notificationTime=None, admissionReference=None, notificationExpireDate=None):
        if not self.serverMessages:
            self.serverMessages = []        
        if not [el for el in self.serverMessages if el['title'] == title and el ['text'] == text and el['admissionReference'] == admissionReference]:
            serverMessage = {'title':title, 'text':text, 'priority':priority, 'shown':False, 'type':'global', 'repeatable':repeatable, 'notificationTime':notificationTime, 'admissionReference':admissionReference, 'notificationExpireDate':notificationExpireDate}
            self.serverMessages.append(serverMessage)    
        
    def removeServerMessage(self, title, text, priority, type=None, repeatable=None, notificationTime=None, admissionReference=None, notificationExpireDate=None):
        if not self.serverMessages:
            return
        shouldBeRemoved = []
        for message in self.serverMessages:
            if message['title'] == title and message['text'] == text and message['admissionReference'] == admissionReference:
                shouldBeRemoved.append(message)
        for message in shouldBeRemoved:
            self.serverMessages.remove(message)
            
        
    def setServerMessages(self, serverMessages):
        self.serverMessages = serverMessages        
    #END NOTIFICATION MANAGEMENET
    
    def poll(self, clientKey, version):
        if self.migrationFlag:
            return None
        if version != PROSAFE_VERSION and not (version == '1.1.6' and PROSAFE_VERSION in ['1.1.7', '1.1.8', '1.1.9', '1.1.10', '1.1.11']):
            return None
        self.activeClientKeys.add(clientKey)
        currentTime = datetime.datetime.now() 
        if not self.lastCleanupTime or (currentTime-self.lastCleanupTime).seconds > self.cleanupInterval:
            self.cleanup(currentTime)
        return self.bulletin
        
