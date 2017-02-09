from databasecreator import DatabaseCreator
import sqlite3 as sqlite
import iterdump
import time
import Pyro.core
import psconstants as psc
from psconstants import abspath
import os

import sys
sys.path.append('./utils')

import threading
import logutils


class QueryManager(Pyro.core.SynchronizedObjBase):
    
    def __init__(self, dbname=abspath('data/prosafedata.sqlite'), encryptionKey='', 
                 useAPSW=True, activeClientKeysCallback=None, centreCode=None):
                     
        Pyro.core.SynchronizedObjBase.__init__(self)
        self.dbname = dbname
        self.dbtype = 'sqlite'
        self.fileConnectionLock = False
        self.encryptionKey = encryptionKey
        self.useAPSW = useAPSW
        self.centreCode = centreCode
        self.localIds = dict()
        self.createOrUpdateDb()
        #self.openConnection()
        self.lockDict = dict()
        self.activeClientKeysCallback = activeClientKeysCallback
        
    def __del__(self):
        self.closeConnection()

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

    def openConnection(self):
        try:
            if self.useAPSW:
                import apsw
                from obfuscatedvfs import ObfuscatedVFS
                obfuvfs = ObfuscatedVFS(key=self.encryptionKey)
                self.fileConnection = apsw.Connection(self.dbname,vfs=obfuvfs.vfsname)
                self.memoryConnection = apsw.Connection(':memory:')
                self.dbCached = False
                self.lockQueryIfNotCached = False
                self.executeQuery('PRAGMA journal_mode = TRUNCATE',toFile=True)
                #self.executeQuery('PRAGMA cache_size = 10000',toFile=True)
                
                #dumping all data to memory. This is a startup bottleneck
                self.lockQueryIfNotCached = True
                self.cachingThread = threading.Thread(target=self.cacheDb)
                self.cachingThread.start()
                
            #THIS WILL NOT WORK
            else:
                self.connection = sqlite.connect(self.dbname)
                
        except:
            print 'Cannot connect'
            raise

    def cacheDb(self):
        print "CACHING DB..."
        cur = self.memoryConnection.cursor()
        dump = iterdump._iterdump(self.fileConnection)
        for du in dump:
            cur.execute(du)
        cur.close()
        self.dbCached = True
        print "DB CACHED!"
    
    def closeConnection(self):
        self.memoryConnection.close()
        self.fileConnection.close()
 
    def createOrUpdateDb(self):

        path = os.path.dirname(self.dbname)
        if not os.path.isdir(path):
            os.mkdir(path)

        templateString = """
            CREATE TABLE "admission" ("admissionKey" VARCHAR(100) PRIMARY KEY  NOT NULL, "localId" int(11) NOT NULL, "patientKey" VARCHAR(100), "centreCode" VARCHAR(10), "inputUserKey" varchar(100), "inputDate" DATETIME, "previousAdmissionKey" VARCHAR(100));
            CREATE TABLE "admissionDeleted" ("admissionKey" VARCHAR(100) PRIMARY KEY  NOT NULL, "idReason" int(11) NOT NULL, "deleteUserKey" varchar(100), "centreCode" VARCHAR(10), "deleteDate" DATETIME);
            CREATE TABLE "attributeData" ("crfName" VARCHAR(100) NOT NULL, "className" VARCHAR(100) NOT NULL, "attributeName" VARCHAR(100) NOT NULL, "objectCode" int(11) NOT NULL, "value" varchar(300), "multiInstanceNumber" int(11), "inputUserKey" varchar(100), "centreCode" VARCHAR(10), "localId" int(11) NOT NULL, "inputDate" DATETIME);
            CREATE TABLE "crfStatus" ("admissionKey" VARCHAR(100) NOT NULL, "crfName" VARCHAR(100) NOT NULL, "statusValue" VARCHAR(2) NOT NULL, "crfVersion" VARCHAR(20) NOT NULL, "centreCode" VARCHAR(10), "localId" int(11) NOT NULL, "inputDate" DATETIME);
            CREATE TABLE "objectData" ("objectCode" int(11) PRIMARY KEY NOT NULL, "idActionReason" int(11) NOT NULL, "externalKey" VARCHAR(100) NOT NULL, "crfName" VARCHAR(100) NOT NULL, "className" VARCHAR(100) NOT NULL, "inputUserKey" varchar(100), "inputDate" DATETIME, "multiInstanceNumber" int(11), "centreCode" VARCHAR(10), "crfVersion" VARCHAR(20) NOT NULL);
            CREATE TABLE "patient" ("patientKey" VARCHAR(100) PRIMARY KEY NOT NULL, "localId" int(11) NOT NULL, "centreCode" VARCHAR(10), "inputUserKey" varchar(100), "inputDate" DATETIME);
        """

        updateStrings = []
        updateStrings.append('DROP VIEW "currentObjectData";')
        updateStrings.append('DROP VIEW "currentAttributeData";')
        updateStrings.append('DROP VIEW "activeAdmissions";')
        updateStrings.append('DROP VIEW "browserAttributeData";')
        updateStrings.append('DROP VIEW "currentCrfStatus";')

        updateStrings.append("""
            ALTER TABLE "objectData" ADD COLUMN "timeStamp" int(11);""")

        updateStrings.append("""
            CREATE INDEX objectIndex ON objectData (crfName, className, externalKey, multiInstanceNumber, timeStamp);""")

        updateStrings.append("""
            CREATE INDEX attributeIndex ON attributeData (crfName, className, attributeName, multiInstanceNumber, objectCode);""")
        updateStrings.append("""
            CREATE INDEX crfStatusLocalIdIndex ON crfStatus (localId);""")
        updateStrings.append("""
            CREATE INDEX objectDataLocalIdIndex ON objectData (objectCode);""")
        updateStrings.append("""
            CREATE INDEX attributeDataLocalIdIndex ON attributeData (localId);""")
        updateStrings.append("""
            CREATE INDEX attributeDataObjectCodeIndex ON attributeData (objectCode);""") 

        updateStrings.append("""
            CREATE VIEW "activeAdmissions" AS SELECT admission.admissionKey admissionKey, patientKey, statusValue, max(crfStatus.localId) FROM admission JOIN crfStatus ON crfStatus.admissionKey = admission.admissionKey WHERE admission.admissionKey NOT IN (SELECT admissionKey FROM admissionDeleted) AND crfStatus.crfName == "%s" GROUP BY admission.admissionKey;""" % psc.coreCrfName)

        updateStrings.append("""
            CREATE VIEW "currentCrfStatus" AS SELECT *, max(localId) FROM crfStatus GROUP BY crfName, admissionKey;""")
        updateStrings.append("""
            CREATE TABLE "obsoleteObjectCodes" ("objectCode" int(11) NOT NULL, "centreCode" VARCHAR(10));""")
        updateStrings.append("""
            CREATE INDEX obsoleteObjectCodeIndex ON obsoleteObjectCodes (objectCode);""")    

        #update missing centreCodes in all tables
        if self.centreCode not in [None, '', 'None']:
            updateStrings.append("UPDATE admission set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
            updateStrings.append("UPDATE admissionDeleted set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
            updateStrings.append("UPDATE attributeData set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
            updateStrings.append("UPDATE crfStatus set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
            updateStrings.append("UPDATE objectData set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
            updateStrings.append("UPDATE patient set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
            updateStrings.append("UPDATE obsoleteObjectCodes set centreCode='%s' WHERE centreCode <> '%s' " % (self.centreCode, self.centreCode))
                
        dbCreator = DatabaseCreator(self.dbname, templateString, updateStrings, useAPSW=self.useAPSW, encryptionKey=self.encryptionKey)
        dbCreator.run()
        self.openConnection()
        maxLocalIdQuery = "select MAX(localId) from attributeData"
        resultLocalId = self.sendQuery(maxLocalIdQuery)[0]['MAX(localId)']
        
        #TODO MERGE: keep this, but remove in the future
        if psc.appName == 'prosafe':
            updateQuery = "select objectData.externalKey, attributeData.value, attributeData.localId, attributeData.attributeName, attributeData.objectCode, attributeData.multiInstanceNumber, attributeData.inputUserKey, attributeData.inputDate, attributeData.centreCode from objectData inner join attributeData on objectData.objectCode = attributeData.objectCode where objectData.className = 'ehrId' and objectData.externalKey in (select admission.patientKey from admission inner join crfStatus on admission.admissionKey = crfStatus.admissionKey where crfStatus.crfVersion  = '1.4.0' or crfStatus.crfVersion  = '2.3.0')"
            updateDict = {}
            updateList = []
            alreadyProcessedPatients = []
            result = self.sendQuery(updateQuery)
            for patient in result:
                if patient['externalKey'] in alreadyProcessedPatients:
                    continue
                reducedlist = [el for el in result if el['externalKey'] == patient['externalKey']]
                savedLocalId = 0
                for record in reducedlist:
                    sortedlist = sorted(reducedlist, key=lambda k: k['localId'])
                    if len(sortedlist) > 1:
                        if sortedlist[-1]['value'] == '' and sortedlist[-2]['value'] != '':
                            #updateDict[sortedlist[-1]['localId']] = sortedlist[-2]['value']                   
                            updateList.append(sortedlist[-2])
                alreadyProcessedPatients.append(patient['externalKey'])
            
            for element in updateList:
                #SOSTITUISCI INSERT CON UPDATE
                resultLocalId += 1
                #self.mainLogic.queryManager.sendQuery('UPDATE attributeData SET value = \'%s\' where localId = %d' % (updateDict[element], element))
                try:
                    print 'INSERT INTO attributeData (crfName, className, attributeName, objectCode, value, multiInstanceNumber, inputUserKey, centreCode, localId, inputDate) values (\'%s\', \'%s\', \'%s\', %d, \'%s\', %d, \'%s\', \'%s\', %d, \'%s\')' % (psc.coreCrfName, 'ehrId', element['attributeName'], element['objectCode'], element['value'], element['multiInstanceNumber'], element['inputUserKey'], element['centreCode'], resultLocalId, element['inputDate'])
                    self.sendQuery('INSERT INTO attributeData (crfName, className, attributeName, objectCode, value, multiInstanceNumber, inputUserKey, centreCode, localId, inputDate) values (\'%s\', \'%s\', \'%s\', %d, \'%s\', %d, \'%s\', \'%s\', %d, \'%s\')' % (psc.coreCrfName, 'ehrId', element['attributeName'], element['objectCode'], element['value'], element['multiInstanceNumber'], element['inputUserKey'], element['centreCode'], resultLocalId, element['inputDate']))
                except BaseException, e:
                    print 'ERROR IN FIXING MY BUG', e

            missingObsoletesQuery = "SELECT objectCode, centreCode FROM objectData WHERE objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) AND objectCode NOT IN (SELECT objectCode FROM objectData WHERE objectCode in (SELECT max(objectCode) FROM objectData WHERE objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber, timeStamp))"
            results = self.sendQuery(missingObsoletesQuery)
            queryList = []
            for record in results:
                print 'MISSING OBSOLETES', record
                query = "INSERT INTO obsoleteObjectCodes (objectCode, centreCode) VALUES (?, ?)"
                bindings = (record['objectCode'], record['centreCode'])
                queryList.append({'query':query,'bindings':bindings,'toFile':True})
            if queryList:
                self.sendQueriesInTransaction(queryList)

            self.sendQuery('UPDATE objectData SET timeStamp = %d WHERE timeStamp IS NULL' % (1, ))

    def sendQueriesInTransaction(self, queryList):
        self.sendQuery("BEGIN TRANSACTION",toFile=True)
        results = [None] * len(queryList)
        try:
            for i, queryDict in enumerate(queryList):
                results[i] = self.sendQuery(**queryDict)
        except BaseException, e:
            print e
        self.sendQuery("END TRANSACTION",toFile=True)
        return results
  
    #@logutils.timeit
    def sendQuery(self, query="", bindings=None, bufferIndeces=[], bindingList=None, toFile=False):
        if bindings:
            bindings = list(bindings)
            for index in bufferIndeces:
                bindings[index] = buffer(bindings[index])

        if bindingList:
            result = self.executeQuery(query,bindingList=bindingList, toFile=toFile)
        else:
            result = self.executeQuery(query,bindings=bindings, toFile=toFile)

        return result
    
    #@logutils.timeitWithArgs
    def executeQuery(self, query, bindings=None, bindingList=None, toFile=False):
        if self.lockQueryIfNotCached:
            while not self.dbCached:
                time.sleep(0.1)
                    
        memoryResult = self.executeQueryOnConnection(query, self.memoryConnection, bindings=bindings, bindingList=bindingList )
        if toFile:
            #while self.fileConnectionLock:
            #    time.sleep(0.1)
            fileResult = self.executeQueryOnConnection(query, self.fileConnection, bindings=bindings, bindingList=bindingList )
            #self.fileResult = threading.Thread(target = self.executeQueryOnConnectionWithFileLock, args =(query, self.fileConnection), kwargs={'bindings':bindings, 'bindingList':bindingList} )
            #self.fileResult.start()
        
        return memoryResult;
        
    def executeQueryOnConnectionWithFileLock(self, query, connection, bindings=None, bindingList=None):
        self.fileConnectionLock = True
        self.executeQueryOnConnection(query, connection, bindings=bindings, bindingList=bindingList)
        self.fileConnectionLock = False
        
    def executeQueryOnConnection(self, query, connection, bindings=None, bindingList=None):
        def rowtrace(cursor, row):
            """Called with each row of results before they are handed off.  You can return None to
            cause the row to be skipped or a different set of values to return"""
            out = dict()
            description = cursor.getdescription()
            colnames = [item[0] for item in description]
            for i, item in enumerate(colnames):
                out[item] = row[i]
            
            return out

        cursor = connection.cursor()
        cursor.setrowtrace(rowtrace)
        
        result = []
        try:
            if bindings:
                rows = cursor.execute(query,bindings)
            elif bindingList:
                rows = cursor.executemany(query,bindingList)
            else:
                rows = cursor.execute(query)
            
            result = list(rows) 
            if not self.useAPSW:
                connection.commit()
        except:
            raise
        cursor.close()
        return result
   
    #@logutils.timeit
    def getCurrentLocalIdInDb(self, table):
        if table == 'objectData':
            query = "SELECT MAX(objectCode) AS currentid FROM %s" % table
        else:
            query = "SELECT MAX(localId) AS currentid FROM %s" % table
        result = self.sendQuery(query)
        currentid = result[0]['currentid']
        try:
            currentid = int(currentid)
        except:
            currentid = 0
        return currentid
 
    def getNewLocalId(self, table):
        if table in self.localIds:
            self.localIds[table] += 1
            return self.localIds[table]
        self.localIds[table] = self.getCurrentLocalIdInDb(table) + 1
        return self.localIds[table]
 
    def reserveLocalIds(self, table, numberOfIds):
        newid = self.getNewLocalId(table)
        self.localIds[table] = newid + numberOfIds - 1
        return newid

 
if __name__ == '__main__':
    pass 
   
