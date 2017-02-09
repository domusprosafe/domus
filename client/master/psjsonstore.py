from store import EntryManager, ConflictError, InvalidError
from psconstants import abspath
import os
import Pyro.core


class JSONStore(Pyro.core.SynchronizedObjBase):
    
    def __init__(self, dbname=abspath('data/prosafestore.sqlite'), encryptionKey='', activeClientKeysCallback=None, centreCode=None, admissionStartingId=1, patientStartingId=1):
        
        Pyro.core.SynchronizedObjBase.__init__(self)
        self.dbname = dbname
        self.dbtype = 'sqlite'
        self.fileConnectionLock = False
        self.encryptionKey = encryptionKey
        self.centreCode = centreCode
        self.lockDict = dict()
        self.activeClientKeysCallback = activeClientKeysCallback
        self.entryManager = EntryManager(dbname)
        self.needsRestoreFlag = False
        self.uuids = self.entryManager.search({'_type': 'UUIDS'})
        if not self.uuids:
            self.needsRestoreFlag = self.entryManager.needsRestore()
            self.uuids = self.entryManager.create({'_type': 'UUIDS', 'admission': admissionStartingId, 'patient': patientStartingId})
        else:
            self.uuids = self.uuids[0]

    def __del__(self):
        pass
        
    def dispose(self):
        print 'disposing db connection'
        self.entryManager.dispose()
    
    def connect(self):
        self.entryManager.connect()

    def setStartingUUID(self, name, uuid):
        self.uuids[name] = uuid + 1
        self.entryManager.update(self.uuids)
        
    def getNewUUID(self, name):
        uuid = self.uuids[name]
        self.uuids[name] = uuid + 1
        self.entryManager.update(self.uuids)
        return uuid

    def copyToPath(self, path):
        import shutil
        shutil.copy(self.dbname,path)

    def acquireLock(self, key, clientKey):
        if key in self.lockDict and self.lockDict[key] in self.activeClientKeysCallback():
            return False
        self.lockDict[key] = clientKey
        return True

    def releaseLock(self, key, clientKey):
        if key in self.lockDict:
            self.lockDict.pop(key)

    def search_ids(self, *args, **kwargs):
        return self.entryManager.search_ids(*args,**kwargs)

    def update(self, *args, **kwargs):
        return self.entryManager.update(*args,**kwargs)

    def create(self, *args, **kwargs):
        return self.entryManager.create(*args,**kwargs)

    def search(self, *args, **kwargs):
        return self.entryManager.search(*args,**kwargs)

    def load_value_list(self, *args, **kwargs):
        return self.entryManager.load_value_list(*args,**kwargs)

    def load_values(self, *args, **kwargs):
        return self.entryManager.load_values(*args,**kwargs)

    def load_value(self, *args, **kwargs):
        return self.entryManager.load_value(*args,**kwargs)
        
    def delete(self, *args, **kwargs):
        return self.entryManager.delete(*args,**kwargs)
        
    def needsRestore(self):
        return self.needsRestoreFlag
        
    def getStore(self, *args, **kwargs):
        return self.entryManager.getStore(*args, **kwargs)
        
    def emptyFlat(self, *args, **kwargs):
        return self.entryManager.emptyFlat(*args, **kwargs)


if __name__ == '__main__':
    pass 
   
