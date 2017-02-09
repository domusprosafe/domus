import sys
sys.path.append("./master")
sys.path.append("./utils")

import os

import base64
import datetime
import sqlite3

from querymanager import QueryManager
from psversion import PROSAFE_VERSION
import ConfigParser


class DBMigrator(object):
    def __init__(self, dataPath):
        self.dataPath = dataPath
        self.publicEncryptionKey = 'custom_encryption_key'
        self.dbFileName = os.path.join(self.dataPath,'prosafedata.sqlite')
        self.centreCode = None
        self.queryManagerNewDB = None
        self.queryManagerOldDB = None
    
    
    def hasEncryptedDB(self):
        if not os.path.isfile(self.dbFileName):
            return None
 
        try:
            connection = sqlite3.connect(self.dbFileName)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM admission")
            cursor.close()
            connection.close()
            return False
        except:
            return True
            
        
    def migrate(self):
        if not os.path.isfile(self.dbFileName):
            return True
    
        encrypted = self.hasEncryptedDB()
        if encrypted:
            return True
        
        #move old db
        oldDBFilename = self.dbFileName + ".old.sqlite"
        os.rename(self.dbFileName, oldDBFilename)
        self.queryManagerOldDB = QueryManager(oldDBFilename,self.publicEncryptionKey, useAPSW=False)
        
            
        #create new db
        self.queryManagerNewDB = QueryManager(self.dbFileName,self.publicEncryptionKey, useAPSW=True)
        #self.queryManagerNewDB.executeQuery("INTO         
        
        centreCodeResults = self.queryManagerOldDB.sendQuery("SELECT * FROM admission")
        #if we have no admissions we cannot get centre code. Data upgrade is useless (NO ADMISSIONS)
        if not len(centreCodeResults):
            return
        
        self.centreCode = centreCodeResults[0]['centreCode']        
        patientClassNames = ['firstName', 'lastName', 'gender', 'birthDate', 'placeOfBirth', 'nhsNumber', 'blood', 'address', 'ehrId']
        
        self.queryManagerNewDB.sendQuery('BEGIN TRANSACTION')
        
        #ADMISSION TABLE
        print "Updating admission table"
        admissionItems = self.queryManagerOldDB.sendQuery("SELECT * FROM admission")
        newAdmissionItems = []
        
        for admissionItem in admissionItems:
            newAdmissionItem = admissionItem
            newAdmissionItem['admissionKey'] = 'A-'+ newAdmissionItem['admissionKey']
            newAdmissionItem['patientKey'] = 'P-'+ newAdmissionItem['patientKey']
            if newAdmissionItem['previousAdmissionKey'] != '':
                newAdmissionItem['previousAdmissionKey'] = 'A-'+ newAdmissionItem['previousAdmissionKey']
            newAdmissionItems.append(newAdmissionItem)
            
        queryAdmission = "INSERT INTO admission(localId, admissionKey, patientKey, centreCode, inputUserKey, inputDate, previousAdmissionKey) VALUES(:localId, :admissionKey, :patientKey, :centreCode, :inputUserKey, :inputDate, :previousAdmissionKey)"
        self.queryManagerNewDB.sendQuery(queryAdmission, bindingList=newAdmissionItems)
            
        #ADMISSION DELETED TABLE
        print "Updating admissionDeleted table"
        admissionDeletedItems = self.queryManagerOldDB.sendQuery("SELECT * FROM admissionDeleted")
        newAdmissionDeletedItems = []
        
        if len (admissionDeletedItems):
            for admissionDeletedItem in admissionDeletedItems:
                newAdmissionDeletedItem = admissionDeletedItem
                newAdmissionDeletedItem['admissionKey'] = 'A-' + newAdmissionDeletedItem['admissionKey']
                newAdmissionDeletedItem['centreCode'] = self.centreCode
                newAdmissionDeletedItems.append(newAdmissionDeletedItem)
                
            
            queryAdmissionDeleted = "INSERT INTO admissionDeleted (admissionKey, idReason, deleteUserKey, centreCode, deleteDate) VALUES (:admissionKey, :idReason, :deleteUserKey, :centreCode, :deleteDate)" 
            self.queryManagerNewDB.sendQuery(queryAdmissionDeleted, bindingList=newAdmissionDeletedItems)
            
        #attributeData TABLE
        print "Updating attributeData table"
        attributeDataItems = self.queryManagerOldDB.sendQuery("SELECT * FROM attributeData ORDER BY inputDate")
        newAttributeDataItems = []
        
        localId = 1
        
        for attributeDataItem in attributeDataItems:
            newAttributeDataItem = attributeDataItem
            newAttributeDataItem['centreCode'] = self.centreCode 
            newAttributeDataItem['value'] = str(newAttributeDataItem['value'])
            
            if newAttributeDataItem['className'] in patientClassNames:
                newAttributeDataItem['value'] = base64.b64encode(newAttributeDataItem['value'])
            else:
                newAttributeDataItem['value'] = base64.b64encode(newAttributeDataItem['value'])
            
            newAttributeDataItem['objectCode'] = newAttributeDataItem['objectCode'].split('-')[-1]    
            newAttributeDataItem['localId'] = localId
            localId += 1
            newAttributeDataItems.append(newAttributeDataItem)
            
            
        queryAttributeData = "INSERT INTO attributeData(objectCode, crfName, className, attributeName, value, multiInstanceNumber, inputUserKey, localId, centreCode, inputDate) VALUES (:objectCode, :crfName, :className, :attributeName, :value, :multiInstanceNumber, :inputUserKey, :localId, :centreCode, :inputDate)"
        self.queryManagerNewDB.sendQuery(queryAttributeData, bindingList=newAttributeDataItems)
        
        
        print "Updating crfStatus table"
        crfStatusItems = self.queryManagerOldDB.sendQuery("SELECT * FROM crfStatus")
        newCrfStatusItems = []
        
        for crfStatusItem in crfStatusItems:
            newCrfStatusItem = crfStatusItem
            newCrfStatusItem['centreCode'] = self.centreCode
            newCrfStatusItem['admissionKey'] = 'A-' + newCrfStatusItem['admissionKey']
            newCrfStatusItem['localId'] = 1
            newCrfStatusItem['inputDate'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            newCrfStatusItems.append(newCrfStatusItem)
            
        queryCrfStatus = "INSERT INTO crfStatus (admissionKey, crfName, statusValue, crfVersion, centreCode, localId, inputDate) VALUES (:admissionKey, :crfName, :statusValue, :crfVersion, :centreCode, :localId, :inputDate)"
        self.queryManagerNewDB.sendQuery(queryCrfStatus, bindingList=newCrfStatusItems)
        
        #objectData TABLE
        print "Updating objectData table"
        objectDataItems = self.queryManagerOldDB.sendQuery("SELECT * FROM objectData")
        newObjectDataItems = []
        
        
        for objectDataItem in objectDataItems:
            newObjectDataItem = objectDataItem
            newObjectDataItem['objectCode'] = newObjectDataItem['localId']
            newObjectDataItem['centreCode'] = self.centreCode
            if newObjectDataItem['className'] in patientClassNames:
                newObjectDataItem['externalKey'] = "P-" + newObjectDataItem['externalKey']
            else:
                newObjectDataItem['externalKey'] = "A-" + newObjectDataItem['externalKey']
            newObjectDataItems.append(newObjectDataItem)
            
        queryObjectData = "INSERT INTO objectData(objectCode, multiInstanceNumber, idActionReason, externalKey, crfName, className, inputUserKey, inputDate, centreCode, crfVersion) VALUES (:objectCode, :multiInstanceNumber, :idActionReason, :externalKey, :crfName, :className, :inputUserKey, :inputDate, :centreCode, :crfVersion)"
        self.queryManagerNewDB.sendQuery(queryObjectData, bindingList=newObjectDataItems)
        
        #patient TABLE
        print "Updating patient table"
        patientItems = self.queryManagerOldDB.sendQuery("SELECT * FROM patient")
        newPatientItems = []
        
        for patientItem in patientItems:
            newPatientItem = patientItem
            newPatientItem['patientKey'] = 'P-'+ newPatientItem['patientKey']
            newPatientItems.append(newPatientItem)
            
        queryPatient = "INSERT INTO patient(localId, patientKey, centreCode, inputUserKey, inputDate) VALUES(:localId, :patientKey, :centreCode, :inputUserKey, :inputDate)"
        self.queryManagerNewDB.sendQuery(queryPatient, bindingList=newPatientItems)
        
        self.queryManagerNewDB.sendQuery('COMMIT TRANSACTION')
        
        
        
if __name__ == '__main__':

    datapath = 'data'
    if len(sys.argv) > 1:
        datapath = sys.argv[1]
    
    migrator = DBMigrator(os.path.join(datapath))     
    migrator.migrate()   
          
    
