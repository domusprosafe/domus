import sys
sys.path.append('../')

from multitablesynchclient import MultiTableSynchClient
import time
import psconstants
import datetime


class synchService(object):
    def __init__(self, localdb, encryptionKey='', useAPSW=False):
        
        self.localdb = localdb
        self.encryptionKey = encryptionKey
        self.useAPSW = useAPSW
        self.tableData = {  'patient' : {'hashFields' : ['patientKey'] }, 
                            'objectData' : { 'hashFields' : ['objectCode', 'externalKey']},
                            'attributeData' : { 'hashFields' : ['localId'] },
                            'admission' : { 'hashFields' : ['admissionKey'] },
                            'admissionDeleted' : { 'hashFields' : ['admissionKey'] },
                            'crfStatus' : { 'hashFields' : ['admissionKey', 'localId', 'crfName', 'statusValue', 'crfVersion'] },
                            'obsoleteObjectCodes' : { 'hashFields' : ['objectCode']},
                            
                         } 
        self.loopActive = True
        self.firstRun = False
        
        
    def terminateLoop(self):
        self.loopActive = False        
    
    def synchronize(self, centreCode): 
        if  centreCode:
            #adding centrecode to token
            token = "token" + centreCode.replace("-",'')
            #adding timestamp to token
            token = token + "_" + str(datetime.datetime.now()).replace(':','').replace(' ','').replace('-','').replace('.','')
            
            client =  MultiTableSynchClient(synchUrl = psconstants.DB_SYNCH_URL,
                                    mergeUrl = psconstants.DB_MERGE_URL,
                                    localdb = self.localdb,
                                    token = token,
                                    tableData = self.tableData,
                                    centreCode = centreCode,
                                    encryptionKey = self.encryptionKey,
                                    useAPSW = self.useAPSW)
            client.run()
         


    
