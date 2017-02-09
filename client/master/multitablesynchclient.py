from synchtablesqlite import SynchTableSqlite
import urllib
import urllib2
import zlib
import datetime
import shutil
import os
import datetime
import sqlite3


MAX_MESSAGE_LENGTH = 1048576

def pickleAndCompress(data):
    rData = repr(data)
    cmpData = zlib.compress(rData)
    return cmpData

def decompressAndUnpickle(data):
    dcmpData = zlib.decompress(data)
    unpData = eval(dcmpData)
    return unpData
    

class MultiTableSynchClient:
    def __init__(self, synchUrl, mergeUrl, localdb, token, tableData, centreCode, encryptionKey='', useAPSW=False):
        
        self.synchUrl = synchUrl
        self.mergeUrl = mergeUrl
        self.localdb = localdb
        self.token = token
        self.tableData =  tableData
        self.centreCode = centreCode
        self.encryptionKey = encryptionKey
        self.useAPSW = useAPSW
        
    def removeFlatTableFromStore(self, localdbCopy):
        conn = sqlite3.connect(localdbCopy)
        conn.execute("DELETE from %s" % 'flat')
        conn.execute("VACUUM")
        conn.close()
    
    def removeHStoreTableAfterSynch(self):
        conn = sqlite3.connect(self.localdb)
        conn.execute("DELETE from hstore")
        conn.execute("VACUUM")
        conn.close()    
    
    def run(self):
        #make a copy of db
        
        localdbCopy = self.localdb + ".tmp.sqlite"
        shutil.copyfile(self.localdb, localdbCopy);
        self.removeFlatTableFromStore(localdbCopy)
        block_size = MAX_MESSAGE_LENGTH
        reader = open(localdbCopy,"rb")
        while(True):
    
            req = urllib2.Request(self.synchUrl) 
            data = reader.read(block_size)

            if not data:
                urldata = urllib.urlencode([('centreCode', self.centreCode), 
                                        ('token', self.token),
                                        ('message', data),
                                        ('partialMessageId', self.token),
                                        ('endMessage', '1')])
                                        
                try:
                    remoteMsg = urllib2.urlopen(req, urldata, 600).read()            
                    print remoteMsg
                except Exception, e:
                    raise Exception('Synchronization server error:' + str(e))
                
                break
            
                       
            urldata = urllib.urlencode([('centreCode', self.centreCode),
                                        ('token', self.token),
                                        ('message', data),
                                        ('partialMessageId', self.token)])

            
            try:
                remoteMsg = urllib2.urlopen(req, urldata, 600).read()            
                print remoteMsg
            except Exception, e:
                raise Exception('Synchronization server error:' + str(e))
                
            
            
        
        reader.close()
        
        if os.path.exists(localdbCopy):
            os.remove(localdbCopy)
        self.removeHStoreTableAfterSynch()
        #os.remove(localdbCopy)
        print "sync ended, file sent"
 
if __name__ == '__main__':
    
    
    import sys
    sys.path.append("../")
    import psconstants
    tableData = {  'patient' : {'hashFields' : ['patientKey'] }, 
                   'objectData' : { 'hashFields' : ['objectCode', 'externalKey']},
                   'attributeData' : { 'hashFields' : ['localId'] },
                   'admission' : { 'hashFields' : ['admissionKey'] },
                   'admissionDeleted' : { 'hashFields' : ['admissionKey'] },
                   'crfStatus' : { 'hashFields' : ['admissionKey', 'localId', 'crfName', 'statusValue', 'crfVersion'] }
                            
                } 
    worker = MultiTableSynchClient(psconstants.DB_SYNCH_URL, 
                                   psconstants.DB_MERGE_URL, 
                                   "../data/prosafedata.sqlite", 
                                   "atoken",
                                   tableData,
                                   "IT999",
                                   encryptionKey='custom_encryption_key', useAPSW=True)
    worker.run()
    

