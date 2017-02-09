
import psconstants as psc
from mainlogic import MainLogic
from datasession import DataSession

class MigrationMainLogic(MainLogic):

    def __init__(self, flags):

        MainLogic.__init__(self, flags)

    def getAllActiveAdmissionsData(self):
        self.beginCriticalSection()
        query = "SELECT * FROM activeAdmissions"
        rdict = self.queryManager.sendQuery(query)

        query = "SELECT crfName, crfVersion, statusValue, admissionKey FROM currentCrfStatus"
        crfrdict = self.queryManager.sendQuery(query)

        query = "SELECT * FROM admission"
        readmissionKeys = self.queryManager.sendQuery(query)
        
        
        
        attributeFullNames = psc.gridDataAttributes
        
        attributesToInternalKeys = dict.fromkeys(attributeFullNames,'admission')
        for patientAttribute in psc.patientGridDataAttributes:
            attributesToInternalKeys[patientAttribute] = 'patient'

        columnNames = attributeFullNames
        classNames = []
        for columnName in columnNames:
            classNames.append(columnName.split('.')[1])

        columnNamesToIndices = dict.fromkeys(columnNames,range(len(columnNames)))
        query = "SELECT externalKey, objectData.objectCode objectCode, attributeData.localId localId, objectData.crfName crfName, objectData.className className, attributeName, value, attributeData.multiInstanceNumber multiInstanceNumber FROM objectData JOIN attributeData ON objectData.objectCode = attributeData.objectCode WHERE objectData.objectCode IN (SELECT max(objectCode) FROM objectData WHERE objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber) AND objectData.className IN (%s);" % ','.join(["'%s'" % el for el in classNames])
        attrrdict = self.queryManager.sendQuery(query)

        crfStatusDict = dict()
        for record in crfrdict:
            if record['admissionKey'] not in crfStatusDict:
                crfStatusDict[record['admissionKey']] = dict()
            crfStatusDict[record['admissionKey']][record['crfName']] = record['statusValue']

        attributeData = dict()

        data = []
        for record in attrrdict:
            if record['externalKey'] not in attributeData:
                attributeData[record['externalKey']] = dict()
            #TODO MERGE: potential problem, the attributeData dictionary used to be like 
            #attributeData[record['externalKey']][self.crfData.joinAttributeName(record['crfName'],record['className'],record['attributeName'])] = record['value']
            # and it now contains a dictionary like {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value']}
            # In any case, in theory no need of storing time stamp as well in dictionary.
            attributeFullName = self.crfData.joinAttributeName(record['crfName'],record['className'],record['attributeName'])
            if attributeFullName in attributeData[record['externalKey']]:
                if record['objectCode'] > attributeData[record['externalKey']][attributeFullName]['objectCode'] or (record['objectCode'] == attributeData[record['externalKey']][attributeFullName]['objectCode'] and record['localId'] > attributeData[record['externalKey']][attributeFullName]['localId']):
                    attributeData[record['externalKey']][attributeFullName] = {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value']}
            else:
                attributeData[record['externalKey']][attributeFullName] = {'objectCode':record['objectCode'], 'localId':record['localId'], 'value':record['value']}

        internalKeyNames = {'admission':'admissionKey', 'patient':'patientKey'}

        for record in rdict:
            row = dict()
            row['admissionKey'] = record['admissionKey']
            row['patientKey'] = record['patientKey']
            for readmissionKeyRow in readmissionKeys:
                if readmissionKeyRow['admissionKey'] == record['admissionKey'] and readmissionKeyRow['patientKey'] == record['patientKey']:
                    row['readmissionKey'] = readmissionKeyRow['previousAdmissionKey']
                    break
            if record['admissionKey'] not in attributeData:
                print 'WARNING: admissionKey %s not found' % record['admissionKey']
                continue
            if record['patientKey'] not in attributeData:
                print 'WARNING: patientKey %s not found' % record['patientKey']
                continue
        #    statusValue = record['statusValue']
        #    gridDataDict = {'admissionKey':admissionKey,'patientKey':patientKey,'statusValue':statusValue}
        #    for attributeName in psc.attrNameDict:
        #        externalKey = psc.attrExternalKeys[attributeName]
        #        if externalKey == 'patient':
        #            key = 'patientKey'
        #        else:
        #            key = 'admissionKey'
        #        try:
        #            var = self.encryptDecryptValue(attributeData[record[key]][attributeName],'decrypt',externalKey)
        #        except:
        #            var = None
        #        gridDataDict[psc.attrNameDict[attributeName]] = var
        #    gridData.append(gridDataDict)

        ##TODO: this is still dependent on the existence of an 'admissionDate'. Generalize
        #if self.filters or self.currentYearFilterActive:
            for attribute in attributesToInternalKeys:
                internalKey = attributesToInternalKeys[attribute]
                try:
                    row[attribute] = self.encryptDecryptValue(attributeData[record[internalKeyNames[internalKey]]][attribute]['value'],'decrypt',internalKey)
                except:
                    row[attribute] = None
            row['statusValue'] = record['statusValue']
            petalStatusDict = dict()
            row['petalsComplete'] = True
            for petalName in crfStatusDict[row['admissionKey']]:
                if petalName == psc.coreCrfName:
                    continue
                petalStatusDict[petalName] = crfStatusDict[row['admissionKey']][petalName]
                if petalStatusDict[petalName] != '0':
                    if petalStatusDict[petalName] != '3':
                        row['petalsComplete'] = False
                        break
            row.update(petalStatusDict)
            data.append(row)

        self.endCriticalSection()

        return data

    def updateStatus(self, computeOnly=False):

        if self.dataSession.getAdmissionStatus() == '5':
            return

        self.dataSession.evaluateGlobals(updateStatus=False)

        self.beginCriticalSection()
        #self.queryManager.sendQuery('BEGIN TRANSACTION',toFile=True)
        queryList = []
        for crfName in self.crfData.getCrfNames():

            #if crfName == psc.coreCrfName and self.dataSession.getAdmissionStatus() == '4' and not self.dataSession.ignoreStatusForUpdate:
            #    continue

            result = None
            if not computeOnly:
                query = "SELECT crfVersion FROM currentCrfStatus WHERE admissionKey = '%s' AND crfName = '%s'" % (self.dataSession.admissionKey,crfName)
                result = self.queryManager.sendQuery(query)
 
            try:
                crfVersion = self.crfData.getPropertyForCrf(crfName,'version')
                currentStatus = self.dataSession.getAdmissionStatus(crfName)
                newStatus = self.computeStatus(crfName)
            except BaseException, e:
                print e
                continue

            if crfName == psc.coreCrfName and self.dataSession.getAdmissionStatus() == '4' and not self.dataSession.ignoreStatusForUpdate and result and crfVersion == result[0]['crfVersion'] and not self.unsavedStatus:
                continue

            if not computeOnly and newStatus == currentStatus and result and crfVersion == result[0]['crfVersion']:
                if self.unsavedStatus == False:
                    continue

            if not computeOnly:
                localId = self.getNewLocalId('crfStatus')
                query = "INSERT INTO crfStatus (admissionKey, crfName, statusValue, crfVersion, centreCode, localId, inputDate) VALUES (?, ?, ?, ?, ?, ?, ?)"
                bindings = (self.dataSession.admissionKey,crfName,newStatus,crfVersion,self.centrecode,localId,self.getDateTime())
                #result = self.queryManager.sendQuery(query,bindings,toFile=True)
                queryList.append({'query':query,'bindings':bindings,'toFile':True})
                self.unsavedStatus = False
            else:
                self.unsavedStatus = True
 
            self.dataSession.setAdmissionStatus(newStatus,crfName)
            if newStatus != currentStatus:
                self.notificationCenter.postNotification("BasedataHasBeenUpdated",self)
        #self.queryManager.sendQuery('COMMIT TRANSACTION',toFile=True)
        self.queryManager.sendQueriesInTransaction(queryList)
        self.endCriticalSection()
        self.notificationCenter.postNotification("StatusHasBeenUpdated",self)

    def getNewLocalId(self, table):
        return self.queryManager.getNewLocalId(table)

    def getObjectDataCurrentLocalIdInDb(self):
        return self.queryManager.getCurrentLocalIdInDb('objectData')

    def getAttributeDataCurrentLocalIdInDb(self):
        return self.queryManager.getCurrentLocalIdInDb('attributeData')

    def loadAdmission(self, admissionkey, acquireLock=True):

        #print 'OPENING ADMISSION', admissionkey
        #if acquireLock:
        #    result = self.queryManager.acquireLock(admissionkey,self.bulletinClient.clientKey)

        #    if result == False:
        #        return False
        self.beginCriticalSection()
        self.evaluator.cleanCache()

        from migrationdatasession import MigrationDataSession

        self.dataSession = MigrationDataSession(self)
        self.dataSession.setAdmissionKey(admissionkey)
        self.unsavedStatus = False

        query = "SELECT statusValue, crfName, crfVersion FROM currentCrfStatus WHERE admissionKey = '%s'" % (self.dataSession.admissionKey)
        result = self.queryManager.sendQuery(query)
        flgStatusFive = False
        for row in result:
            self.dataSession.setAdmissionStatus(row['statusValue'],row['crfName'])
            #crfNamesToVersions[row['crfName']] = row['crfVersion']
            if row['crfName'] == psc.coreCrfName and row['statusValue'] == '5':
                flgStatusFive = True
        flgStatusFive = False        
        if flgStatusFive:
            #re-open admission to allow re-evaluation of the admisssion even if it's in status 5    
            self.reopenAdmission()
                            
        query = "SELECT patientKey FROM admission WHERE admissionKey = '%s'" % self.dataSession.admissionKey
        result = self.queryManager.sendQuery(query)
        record = result[0]
        self.dataSession.setPatientKey(record['patientKey'])

        if len(self.gridData) == 0:
            self.refreshGridData()

        admissionDate = [line[psc.admissionDateAttr] for line in self.gridData if line['admissionKey'] == admissionkey][0]

        self.dataSession.ignoreStatusForUpdate = True
        
        self.loadCrfs(admissionDate)
    
        self.loadObjects()
        self.loadObjectsAttributes()

        # TODO: personalizations
        #storedPersonalizations = self.dataSession.getAttributeValuesForClass(psc.coreCrfName,'personalizations','personalizations')
        #self.crfData.mergePersonalizations(storedPersonalizations)

        self.objectCodesOnLoad = set(self.dataSession.getAllObjectCodes())

        self.dataSession.unregisterOrphanClassInstances()
        self.dataSession.cleanUpDirtyObjectContainers()
        self.dataSession.buildObjectCodesToContainers()

        self.dataSession.removeInvalidErrorObjects()

        self.dataSession.evaluateCalculatedSinglePass()
        self.dataSession.evaluateGlobals(updateStatus=True)
        
        if flgStatusFive:
            self.closeAdmission()
            
        self.dataSession.modified = False
                
        self.dataSession.ignoreStatusForUpdate = False

        self.dischargeLetterFolder = ''
        self.dischargeLetterModelFolder = ''

        #currentAttributePersonalizations = self.crfData.getAttributePersonalizations()
        #currentCodingSetValuePersonalizations = self.crfData.getCodingSetValuePersonalizations()
        #self.dataSession.updateDataNoNotify(psc.coreCrfName,'personalizations',1,'attributes',currentAttributePersonalizations,evaluateGlobals=False)
        #self.dataSession.updateDataNoNotify(psc.coreCrfName,'personalizations',1,'codingSetValues',currentCodingSetValuePersonalizations,evaluateGlobals=False)

        self.endCriticalSection()
        return True
    def loadObjects(self):

        self.beginCriticalSection()
        #query = "SELECT *, max(objectCode) FROM objectData WHERE externalKey = '%s' AND objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber " % self.dataSession.patientKey
        query = "SELECT * FROM objectData WHERE objectCode in (SELECT max(objectCode) FROM objectData WHERE externalKey = '%s' AND objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber, timeStamp);" % self.dataSession.patientKey
        presult = self.queryManager.sendQuery(query)
        
        #query = "SELECT *, max(objectCode) FROM objectData WHERE externalKey = '%s' AND objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber " % self.dataSession.admissionKey
        query = "SELECT * FROM objectData WHERE objectCode in (SELECT max(objectCode) FROM objectData WHERE externalKey = '%s' AND objectCode NOT IN (SELECT objectCode FROM obsoleteObjectCodes) GROUP BY crfName, className, externalKey, multiInstanceNumber, timeStamp);" % self.dataSession.admissionKey
        aresult = self.queryManager.sendQuery(query)

        self.dataSession.setObjects(presult+aresult)

        self.endCriticalSection()
    
    #@logutils.timeit
    def loadObjectsAttributes(self, discrepancies=None):

        self.beginCriticalSection()
        #query = "SELECT *, max(localId) FROM attributeData WHERE objectCode IN "
        query = "SELECT * FROM attributeData WHERE localId IN (SELECT max(localId) FROM attributeData WHERE objectCode IN "

        bindings = []
        for it in self.dataSession.getObjects():
            bindings.append(it['objectCode'])
        query += '(' + ', '.join([str(entry) for entry in bindings]) + ')'
        query += " GROUP BY crfName, className, attributeName, multiInstanceNumber, objectCode);"
        results = self.queryManager.sendQuery(query)

        decryptedResults = self.decryptObjectsAttributes(results,discrepancies)
        self.dataSession.setObjectsAttributes(decryptedResults)
        self.endCriticalSection()

