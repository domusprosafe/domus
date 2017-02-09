from datasession import DataSession, DataObjects, DataAttributes

from copy import copy, deepcopy
import datetime
import operator

import psconstants as psc

class MigrationDataSession(DataSession):
    
    def __init__(self, mainLogic):

        DataSession.__init__(self, mainLogic)

        self.objects = DataObjects()
        self.objectsAttributes = DataAttributes()

        self.crfProperties = {'enabled':dict()}
        self.classProperties = {'visibility':dict(), 'enabled':dict()}
        #self.attributeProperties = {'visibility':dict(), 'enabled':dict()}
    
        self.mainLogic = mainLogic
        
        self.admissionStatus = dict()
        self.patientKey = None
        self.admissionKey = None

        self.classNamesToInstanceNumbers = dict()
        self.classNamesToTimeStamps = dict()
        self.objectCodesToClasses = dict()

        self.objectDataLocalId = self.mainLogic.getObjectDataCurrentLocalIdInDb()
        self.attributeDataLocalId = self.mainLogic.getAttributeDataCurrentLocalIdInDb()

        self.objectCodesToContainers = dict()

        self.ignoreStatusForUpdate = False
        self.modified = False

    #def __del__(self):
    #    print 'deleting datasession'

    def updateLocalIds(self):
        self.objectDataLocalId = self.mainLogic.getObjectDataCurrentLocalIdInDb()
        self.attributeDataLocalId = self.mainLogic.getAttributeDataCurrentLocalIdInDb()

    def getNewObjectDataLocalId(self):
        self.objectDataLocalId += 1
        return self.objectDataLocalId

    def getNewAttributeDataLocalId(self):
        self.attributeDataLocalId += 1
        return self.attributeDataLocalId

    def remapObjectCodes(self,objectCodeDict):
        pass
    #    self.objects.remapObjectCodes(objectCodeDict)
    #    self.objectsAttributes.remapObjectCodes(objectCodeDict)
    #    #TODO: update self.objectCodesToClasses
    #    #TODO: issue with classes multi instance: solution use dictionary from object codes to containers to efficiently remap

    def remapAttributeLocalIds(self,localIdsDict):
        pass
    #    self.objectsAttributes.remapLocalIds(localIdsDict)

    def getCrfProperty(self,crfName,propertyName):
        try:
            return self.classProperties[propertyName][crfName]
        except:
            return None
    
    def setCrfProperty(self,crfName,propertyName,propertyValue):
        if not propertyName in self.classProperties:
            return
        self.classProperties[propertyName][crfName] = propertyValue

    def getClassProperty(self,crfName,className,propertyName):
        try:
            return self.classProperties[propertyName][(crfName,className)]
        except:
            return None
    
    def setClassProperty(self,crfName,className,propertyName,propertyValue):
        if not propertyName in self.classProperties:
            return
        self.classProperties[propertyName][(crfName,className)] = propertyValue

    #def getAttributeProperty(self,crfName,className,attributeName,propertyName):
    #    try:
    #        return self.attributeProperties[propertyName][(crfName,className,attributeName)]
    #    except:
    #        return None
    #
    #def setAttributeProperty(self,crfName,className,attributeName,propertyName,propertyValue):
    #    if not propertyName in self.attributeProperties:
    #        return
    #    self.attributeProperties[propertyName][(crfName,className,attributeName)] = propertyValue

    def getClassInfoForObjectCode(self,objectCode):
        if objectCode not in self.objectCodesToClasses:
            return None
        return self.objectCodesToClasses[objectCode]

    def getExternalKeys(self):
        return {'patient': self.patientKey, 'admission': self.admissionKey}
 
    def getExternalKey(self,key):
        return self.getExternalKeys()[key]
 
    def getInstanceNumbersForClass(self,crfName,className,timeStamp=None):
        if timeStamp == None:
            timeStamp = self.getTimeStampForClass(crfName,className)
        if not self.classNamesToInstanceNumbers.has_key((crfName,className,timeStamp)):
            return []
        classInstanceNumbers = self.classNamesToInstanceNumbers[(crfName,className,timeStamp)][:]
        if self.mainLogic.crfData.getPropertyForClass(crfName,className,'dynamic') == '1':
            if 1 in classInstanceNumbers:
                classInstanceNumbers.remove(1)
        return classInstanceNumbers

    def registerNewTimeStampForClass(self,crfName,className):
        timeStamp = 1
        if (crfName,className) in self.classNamesToTimeStamps:
            timeStamp = max(self.classNamesToTimeStamps[(crfName,className)])+1 
        self.registerTimeStampForClass(crfName,className,timeStamp)
        return timeStamp

    def registerTimeStampForClass(self,crfName,className,timeStamp):
        if (crfName,className) not in self.classNamesToTimeStamps:
            self.classNamesToTimeStamps[(crfName,className)] = []
        if timeStamp not in self.classNamesToTimeStamps[(crfName,className)]:
            self.classNamesToTimeStamps[(crfName,className)].append(timeStamp)

    def unregisterTimeStampForClass(self,crfName,className,timeStamp):
        if (crfName,className) not in self.classNamesToTimeStamps:
            return
        if timeStamp in self.classNamesToTimeStamps[(crfName,className)]:
            self.classNamesToTimeStamps[(crfName,className)].remove(timeStamp)

    def registerInstanceNumberForClass(self,crfName,className,classInstanceNumber,timeStamp=None):
        if timeStamp == None:
            timeStamp = self.getTimeStampForClass(crfName,className)
        if self.classNamesToInstanceNumbers.has_key((crfName,className,timeStamp)):
            if classInstanceNumber in self.classNamesToInstanceNumbers[(crfName,className,timeStamp)]:
                return
            else:
                self.classNamesToInstanceNumbers[(crfName,className,timeStamp)].append(classInstanceNumber)
        else:
            self.classNamesToInstanceNumbers[(crfName,className,timeStamp)] = [classInstanceNumber]
 
    def unregisterInstanceNumberForClass(self,crfName,className,classInstanceNumber,timeStamp=None):
        if timeStamp == None:
            timeStamp = self.getTimeStampForClass(crfName,className)
        if self.classNamesToInstanceNumbers.has_key((crfName,className,timeStamp)):
            if classInstanceNumber in self.classNamesToInstanceNumbers[(crfName,className,timeStamp)]:
                self.classNamesToInstanceNumbers[(crfName,className,timeStamp)].remove(classInstanceNumber)
 
    def registerSingleInstanceNumberForClass(self,crfName,className,timeStamp=None):
        if timeStamp == None:
            timeStamp = self.getTimeStampForClass(crfName,className)
        classInstanceNumbers = [1]
        self.classNamesToInstanceNumbers[(crfName,className,timeStamp)] = classInstanceNumbers
        return classInstanceNumbers

    def registerNewInstanceNumberForClass(self,crfName,className,timeStamp=None):
        if timeStamp == None:
            timeStamp = self.getTimeStampForClass(crfName,className)
        classInstanceNumber = 2
        if self.classNamesToInstanceNumbers.has_key((crfName,className,timeStamp)):
            currentInstanceNumbers = self.classNamesToInstanceNumbers[(crfName,className,timeStamp)]
            while classInstanceNumber in currentInstanceNumbers:
                classInstanceNumber += 1
        else:
            self.classNamesToInstanceNumbers[(crfName,className,timeStamp)] = []
        self.classNamesToInstanceNumbers[(crfName,className,timeStamp)].append(classInstanceNumber)
        return classInstanceNumber
  
    def getObjectData(self,crfName,className,classInstanceNumber,timeStamp):
        return self.objects.get(crfName,className,classInstanceNumber,timeStamp)
 
    def removeObjectAndAttributes(self,crfName,className,classInstanceNumber,timeStamp=None):
        if not timeStamp:
            timeStamp = self.getTimeStampForClass(crfName,className)
        objectCode = self.getObjectCode(crfName,className,classInstanceNumber,timeStamp)
        if objectCode == None:
            return
        self.objects.remove(crfName,className,classInstanceNumber,timeStamp)
        attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
        for attributeName in attributeNames:
            multiInstance = self.isMultiInstance(crfName,className,attributeName) 
            multiInstanceNumber = 1
            attributeValue = self.objectsAttributes.getValue(objectCode,attributeName,multiInstanceNumber)
            while attributeValue is not None:
                self.objectsAttributes.remove(objectCode,attributeName,multiInstanceNumber)
                multiInstanceNumber += 1
                attributeValue = self.objectsAttributes.getValue(objectCode,attributeName,multiInstanceNumber)
        self.objectCodesToClasses.pop(objectCode)

    def removeInvalidErrorObjects(self):
        crfNames = self.mainLogic.crfData.getCrfNames()
        crfName = psc.coreCrfName
        for className, attributeName, crfAttributeName, containerClassName, containerAttributeName in [['errorDetail','errorId','errorCrf','errorList','errorList'],['warningDetail','warningId','warningCrf','warningList','warningList']]:
            classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
            for classInstanceNumber in classInstanceNumbers:
                errorIdValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
                errorCrfNameValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,crfAttributeName)
                removeError = False
                if not errorIdValues or not errorCrfNameValues:
                    self.removeObjectInContainer(crfName,className,classInstanceNumber,crfName,containerClassName,containerAttributeName)
                    continue
                errorId = errorIdValues[0]
                errorCrfName = errorCrfNameValues[0]
                if errorCrfName not in crfNames:
                    self.removeObjectInContainer(crfName,className,classInstanceNumber,crfName,containerClassName,containerAttributeName)
                    continue
                if errorId not in self.mainLogic.crfData.getErrorIdsForCrf(errorCrfName):
                    self.removeObjectInContainer(crfName,className,classInstanceNumber,crfName,containerClassName,containerAttributeName)
                    continue
                errorInfo = self.mainLogic.crfData.getErrorInfoForId(errorCrfName,errorId)
                if className == 'errorDetail' and errorInfo.get('warning','0') == '1':
                    self.removeObjectInContainer(crfName,className,classInstanceNumber,crfName,containerClassName,containerAttributeName)
                    continue
                if className == 'warningDetail' and errorInfo.get('warning','0') == '0':
                    self.removeObjectInContainer(crfName,className,classInstanceNumber,crfName,containerClassName,containerAttributeName)
                    continue                  

    def cleanUpDirtyObjectContainers(self):
        for crfName in self.mainLogic.crfData.getCrfNames():
            classNames = self.mainLogic.crfData.getClassNamesForCrf(crfName)
            for className in classNames:
                attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
                for attributeName in attributeNames:
                    dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
                    if dataType != 'object':
                        continue
                    classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
                    for classInstanceNumber in classInstanceNumbers:
                        objectCodes = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
                        cleanObjectCodes = []
                        anyDirty = False
                        for objectCode in objectCodes:
                            if objectCode in self.objectCodesToClasses:
                                cleanObjectCodes.append(objectCode)
                            else:
                                anyDirty = True
                        if anyDirty:
                            self.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,cleanObjectCodes,evaluateGlobals=False)
 
    def unregisterOrphanClassInstances(self):
        #DO THIS FOR ALL TIMESTAMPS
        nonOrphanObjectCodes = set()
        for crfName in self.mainLogic.crfData.getCrfNames():
            classNames = self.mainLogic.crfData.getClassNamesForCrf(crfName)
            for className in classNames:
                attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
                for attributeName in attributeNames:
                    dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
                    if not (dataType == 'object' and self.isMultiInstance(crfName,className,attributeName)):
                        continue
                    objectCodes = self.getAttributeValuesForClass(crfName,className,attributeName)
                    nonOrphanObjectCodes.update(set(objectCodes))
        allObjectCodes = set(self.objectCodesToClasses.keys())
        orphanObjectCodes = allObjectCodes - nonOrphanObjectCodes
        for objectCode in orphanObjectCodes:
            classInfo = self.objectCodesToClasses[objectCode]
            if classInfo['classInstanceNumber'] == 1:
                continue
            #print 'ORPHAN ', objectCode
            self.unregisterInstanceNumberForClass(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'])
            self.objectCodesToClasses.pop(self.objects.get(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],classInfo['timeStamp'])['objectCode'])

    def buildObjectCodesToContainers(self):
        #DO THIS FOR ALL TIMESTAMPS
        self.objectCodesToContainers = dict()
        for crfName in self.mainLogic.crfData.getCrfNames():
            classNames = self.mainLogic.crfData.getClassNamesForCrf(crfName)
            for className in classNames:
                attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
                for attributeName in attributeNames:
                    dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
                    if dataType != 'object':
                        continue
                    if self.isMultiInstance(crfName,className,attributeName):
                        objectCodes = self.getAttributeValuesForClass(crfName,className,attributeName)
                        for objectCode in objectCodes:
                            if not objectCode in self.objectCodesToContainers:
                                self.objectCodesToContainers[objectCode] = []
                            self.objectCodesToContainers[objectCode].append(self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName))

    def getAllObjectCodes(self):
        return self.objectCodesToClasses.keys()

    def getObjectCode(self,crfName,className,classInstanceNumber,timeStamp=None):
        if not timeStamp:
            timeStamp = self.getTimeStampForClass(crfName,className)
        objectData = self.getObjectData(crfName,className,classInstanceNumber,timeStamp)
        if objectData is not None:
            return objectData['objectCode']
        return None

    def getObjectExternalKey(self,crfName,className,classInstanceNumber,timeStamp=None):
        if not timeStamp:
            timeStamp = self.getTimeStampForClass(crfName,className)
        objectData = self.getObjectData(crfName,className,classInstanceNumber,timeStamp)
        if objectData is not None:
            return objectData['externalKey']
        return None

    def isMultiInstance(self,crfName,className,attributeName):
        multiInstance = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'multiInstance')
        if multiInstance == '1':
            return True
        return False
 
    def getAttributeValuesForClassInDict(self,crfName,className,attributeName,timeStamp=None):
        classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className,timeStamp)
        output = dict()
        for classInstanceNumber in classInstanceNumbers:
            attributeValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName,timeStamp)
            if not attributeValues:
                continue
            output[classInstanceNumber] = attributeValues
        return output
   
    def getAttributeValuesForClass(self,crfName,className,attributeName,timeStamp=None):
        classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className,timeStamp)
        output = []
        for classInstanceNumber in classInstanceNumbers:
            attributeValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName,timeStamp)
            if not attributeValues:
                continue
            output.extend(attributeValues)
        return output

    def getAllAttributeValuesForClassInDict(self,crfName,className,attributeName,timeDict=False):
        timeStamps = self.getAllTimeStampsForClass(crfName,className)
        output = []
        if timeDict:
            output = dict()
        for timeStamp in timeStamps:
            if timeDict:
                output[timeStamp] = self.getAttributeValuesForClassInDict(crfName,className,attributeName,timeStamp)
            else:
                output.append(self.getAttributeValuesForClassInDict(crfName,className,attributeName,timeStamp))
        return output

    def getAllAttributeValuesForClass(self,crfName,className,attributeName,timeDict=False):
        timeStamps = self.getAllTimeStampsForClass(crfName,className)
        output = []
        if timeDict:
            output = dict()
        for timeStamp in timeStamps:
            if timeDict:
                output[timeStamp] = self.getAttributeValuesForClass(crfName,className,attributeName,timeStamp)
            else:
                output.append(self.getAttributeValuesForClass(crfName,className,attributeName,timeStamp))
        return output

    def getAttributeValuesForObject(self,crfName,className,classInstanceNumber,attributeName,timeStamp=None):
        objectCode = self.getObjectCode(crfName,className,classInstanceNumber,timeStamp)
        if objectCode == None:
            return []
        multiInstance = self.isMultiInstance(crfName,className,attributeName) 
        attributeValues = []
        if multiInstance:
            multiInstanceNumber = 1
            attributeValue = self.objectsAttributes.getValue(objectCode,attributeName,multiInstanceNumber)
            while attributeValue is not None:
                attributeValues.append(attributeValue)
                multiInstanceNumber += 1
                attributeValue = self.objectsAttributes.getValue(objectCode,attributeName,multiInstanceNumber)
        else:
            multiInstanceNumber = 1
            attributeValue = self.objectsAttributes.getValue(objectCode,attributeName,multiInstanceNumber)
            if attributeValue is not None:
                attributeValues.append(attributeValue)
        return attributeValues

    def getInstanceNumbersForClassAndAttributeValue(self,crfName,className,attributeName,attributeValue,timeStamp=None):
        isMultiInstance = self.isMultiInstance(crfName,className,attributeName)
        classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className,timeStamp)
        returnedClassInstanceNumbers = []
        for classInstanceNumber in classInstanceNumbers:
            currentAttributeValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName,timeStamp)
            if not currentAttributeValues:
                if attributeValue:
                    continue
                else:
                    returnedClassInstanceNumbers.append(classInstanceNumber)
                    continue
            if isMultiInstance:
                if attributeValue == currentAttributeValues:
                    returnedClassInstanceNumbers.append(classInstanceNumber)
            else:
                if attributeValue == currentAttributeValues[0]:
                    returnedClassInstanceNumbers.append(classInstanceNumber)
        return returnedClassInstanceNumbers

    def getTimeStampForClass(self,crfName,className):
        timeStamp = 1
        timeStampAttributeFullName = self.mainLogic.crfData.getPropertyForClass(crfName,className,'timeStamp')
        if timeStampAttributeFullName:
            timeStampCrfName, timeStampClassName, timeStampAttributeName = self.mainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
            timeStampList = self.getAttributeValuesForClass(timeStampCrfName,timeStampClassName,timeStampAttributeName)
            if timeStampList:
                timeStamp = timeStampList[0]
        return timeStamp

    def getAllTimeStampsForClass(self,crfName,className,sorted=False):
        if (crfName,className) not in self.classNamesToTimeStamps:
            if self.mainLogic.crfData.getPropertyForClass(crfName,className,'timeStamp'):
                return []
            return [1]
        timeStamps = self.classNamesToTimeStamps[(crfName,className)]

        #if not sorted or len(timeStamps) < 2:
        if len(timeStamps) < 2:
            return timeStamps

        timeStampAttributeFullName = self.mainLogic.crfData.getPropertyForClass(crfName,className,'timeStamp')
        if not timeStampAttributeFullName:
            return [1]
        timeStampCrfName, timeStampClassName, timeStampAttributeName = self.mainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
        sortByAttributeFullName = self.mainLogic.crfData.getPropertyForAttribute(timeStampCrfName,timeStampClassName,timeStampAttributeName,'sortBy')

        if not sortByAttributeFullName:
            timeStamps.sort()
            return timeStamps

        sortByCrfName, sortByClassName, sortByAttributeName = self.mainLogic.crfData.splitAttributeName(sortByAttributeFullName)

        if not sorted:
            return self.classNamesToTimeStamps[(sortByCrfName,sortByClassName)]

        timeStampToSortByValuesDict = dict()
        if sortByCrfName == crfName and sortByClassName == className:
            for timeStamp in timeStamps:
                timeStampToSortByValuesDict[timeStamp] = self.getAttributeValuesForClass(sortByCrfName,sortByClassName,sortByAttributeName,timeStamp)
        else:
            timeStampToSortByValuesDict = self.getAllAttributeValuesForClass(sortByCrfName,sortByClassName,sortByAttributeName,timeDict=True)
        sortByToTimeStampPairs = [(v,k) for k,v in timeStampToSortByValuesDict.iteritems()]
        sortByToTimeStampPairs.sort()
        sortedTimeStamps = [el[1] for el in sortByToTimeStampPairs]

        return sortedTimeStamps


    def setAttributeValue(self,crfName,className,classInstanceNumber,attributeName,attributeValue,inputDate):
        multiInstance = self.isMultiInstance(crfName,className,attributeName)

        objectCode = self.getObjectCode(crfName,className,classInstanceNumber)

        timeStamp = self.getTimeStampForClass(crfName,className)

        if multiInstance and not type(attributeValue) is list:
            print 'Error: trying to set non-list ', type(attributeValue), ' to multi instance attribute ', '.'.join((crfName,className,attributeName))

        previousAttributeValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)

        otherAttributeValues = dict()
        #print self.mainLogic.crfData.getAttributeNamesForClass(crfName,className), crfName,className
        for otherAttributeName in self.mainLogic.crfData.getAttributeNamesForClass(crfName,className):
            if otherAttributeName == attributeName:
                continue
            otherAttributeValues[otherAttributeName] = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,otherAttributeName)
        self.removeObjectAndAttributes(crfName,className,classInstanceNumber)
        self.registerInstanceNumberForClass(crfName,className,classInstanceNumber)
        ########################################
        #self.registerTimeStampForClass(crfName,className,timeStamp)
        ########################################
        newObjectCode = self.insertObject(crfName,className,classInstanceNumber,inputDate,timeStamp)
        for otherAttributeName in otherAttributeValues:
            multiInstanceNumber = 1
            for entry in otherAttributeValues[otherAttributeName]:
                self.insertAttribute(crfName,className,otherAttributeName,newObjectCode,entry,multiInstanceNumber,inputDate)
                multiInstanceNumber += 1
        multiInstanceNumber = 1
        if multiInstance:
            if attributeValue:
                for entry in attributeValue:
                    self.insertAttribute(crfName,className,attributeName,newObjectCode,entry,multiInstanceNumber,inputDate)
                    multiInstanceNumber += 1
        else:
            self.insertAttribute(crfName,className,attributeName,newObjectCode,attributeValue,multiInstanceNumber,inputDate)

        containersToNewObjectCodes = dict()
        if objectCode in self.objectCodesToContainers.keys():
            containerAttributeFullNames = self.objectCodesToContainers[objectCode]
            for containerAttributeFullName in containerAttributeFullNames:
                containerCrfName, containerClassName, containerAttributeName = self.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
                containedObjectCodes = self.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
                if not objectCode in containedObjectCodes:
                    continue
                containedObjectCodes[containedObjectCodes.index(objectCode)] = newObjectCode
                containersToNewObjectCodes[containerAttributeFullName] = containedObjectCodes
            self.objectCodesToContainers[newObjectCode] = self.objectCodesToContainers[objectCode]
            self.objectCodesToContainers.pop(objectCode)

        dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')

        # BUG FIX
        if previousAttributeValues == [[]]:
            previousAttributeValues = []

        if dataType == 'object':
            if not attributeValue:
                droppedAttributeValues = set(previousAttributeValues)
                newAttributeValues = set()                
            else:
                try:
                    droppedAttributeValues = set(previousAttributeValues) - set(attributeValue)
                except:
                    raise
                newAttributeValues = set(attributeValue) - set(previousAttributeValues)

            for droppedObjectCode in droppedAttributeValues:
                if droppedObjectCode in self.objectCodesToContainers:
                    containerAttributeFullName = self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName)
                    if containerAttributeFullName in self.objectCodesToContainers[droppedObjectCode]:
                        self.objectCodesToContainers[droppedObjectCode].remove(containerAttributeFullName)

            for newObjectCode in newAttributeValues:
                if not newObjectCode in self.objectCodesToContainers:
                    self.objectCodesToContainers[newObjectCode] = []
                containerAttributeFullName = self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName)
                if not containerAttributeFullName in self.objectCodesToContainers[newObjectCode]:
                    self.objectCodesToContainers[newObjectCode].append(containerAttributeFullName)

        for containerAttributeFullName in containersToNewObjectCodes:
            containerCrfName, containerClassName, containerAttributeName = self.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
            containedObjectCodes = containersToNewObjectCodes[containerAttributeFullName]
            self.updateDataNoNotify(containerCrfName,containerClassName,1,containerAttributeName,containedObjectCodes,evaluateGlobals=False)

    def copySession(self):
        return (deepcopy(self.objects), deepcopy(self.objectsAttributes))
        
    def setSession(self, copy):
        self.objects, self.objectsAttributes = copy[0], copy[1]

    def setAdmissionStatus(self, status, crfName=None):
        if type(status) != str:
            status = str(status)
        if crfName == None:
            for crfName in self.admissionStatus:
                self.admissionStatus[crfName] = status 
            self.mainLogic.notificationCenter.postNotification("BasedataHasBeenUpdated",self)
            return
        self.admissionStatus[crfName] = status 
        self.mainLogic.notificationCenter.postNotification("BasedataHasBeenUpdated",self)

    def getAdmissionStatus(self, crfName=None):
        #if crfName == None:
        #    if not self.admissionStatus:
        #        return None
        #    return min(self.admissionStatus.values())
        if crfName == None:
            crfName = psc.coreCrfName
        try:
            admissionStatus = self.admissionStatus[crfName]
        except:
            admissionStatus = None
        return admissionStatus
 
    def setPatientKey(self, patientKey):
        self.patientKey = patientKey 
 
    def setAdmissionKey(self, admissionKey):
        self.admissionKey = admissionKey 
 
    def setObjects(self, objects):
        crfNames = self.mainLogic.crfData.getCrfNames()
        for data in objects:
            if data['crfName'] not in crfNames:
                continue
            #existingObject = self.objects.get(data['crfName'],data['className'],data['multiInstanceNumber'],data['timeStamp'])
            #if existingObject:
            #    self.objectCodesToClasses.pop(existingObject['objectCode'])
            #    self.unregisterInstanceNumberForClass(existingObject['crfName'],existingObject['className'],existingObject['multiInstanceNumber'])
            self.objectCodesToClasses[data['objectCode']] = {'crfName':data['crfName'], 'className':data['className'], 'classInstanceNumber':data['multiInstanceNumber'], 'timeStamp':data['timeStamp']}
            self.registerTimeStampForClass(data['crfName'],data['className'],data['timeStamp'])
            self.registerInstanceNumberForClass(data['crfName'],data['className'],data['multiInstanceNumber'],data['timeStamp'])
        self.objects.fromList(objects)
        self.objects.resetModified()

    def getObjects(self):
        return self.objects.toList()
 
    def getModifiedObjects(self):
        return self.objects.toListIfModified()
 
    #def getModifiedObjectsFromLastSave(self):
    #    modifiedObjects = self.objects.toListIfModified()
    #    for modifiedObject in modifiedObjects:
 
    def resetModifiedObjects(self):
        return self.objects.resetModified()
       
    def getObjects(self):
        return self.objects.toList()
 
    def castValueForObjectAttribute(self, crfName, className, attributeName, attributeValue, raiseException = False):
        dataTypeName = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
        if attributeValue in ['']:
            attributeValue = None
        elif dataTypeName == 'string':
            pass 
        elif dataTypeName in ['int', 'object', 'timestamp']:
            if dataTypeName == 'object':
                try:
                    splitObjectCode = attributeValue.split('-')
                    if len(splitObjectCode) == 3:
                        attributeValue = int(splitObjectCode[2])
                except:
                    pass
            try:
                attributeValue = int(attributeValue)
            except:
                try:
                    attributeValue = int(float(attributeValue))
                except:
                    if raiseException:
                        raise
                    else:
                        attributeValue = None
        elif dataTypeName == 'float':
            if type(attributeValue) in [str,unicode]:
                attributeValue = attributeValue.replace(',','.')
            try:
                attributeValue = float(attributeValue)
            except:
                if raiseException:
                    raise
                else:
                    attributeValue = None
        elif dataTypeName == 'boolean':
            try:
                attributeValue = bool(int(attributeValue))
            except:
                if raiseException:
                    raise
                else:
                    attributeValue = None
        elif dataTypeName == 'datetime':
            #TODO: check validity?
            pass
        #elif dataTypeName == 'object':
        #    #TODO: check validity?
        #    pass
        elif dataTypeName == 'error':
            #TODO: check validity?
            pass
        elif dataTypeName == 'codingset':
            pass
            #TODO: check validity?
        return attributeValue
      
    def castObjectsAttributesValues(self, objectsAttributes):
        actualAttributes = []
        for el in objectsAttributes:
            castValue = self.castValueForObjectAttribute(el['crfName'],el['className'],el['attributeName'],el['value'])
            el['value'] = castValue
            if castValue == None:
                continue
            actualAttributes.append(el)
        return actualAttributes

    def setObjectsAttributes(self, attributes):
        crfNames = self.mainLogic.crfData.getCrfNames()
        attributes = [el for el in attributes if el['crfName'] in crfNames]
        attributes = self.castObjectsAttributesValues(attributes)
        self.objectsAttributes.fromList(attributes)
        self.objectsAttributes.resetModified()
        
    def getObjectsAttributes(self):
        return self.objectsAttributes.toList()
 
    def getModifiedObjectsAttributes(self):
        return self.objectsAttributes.toListIfModified()
 
    def resetModifiedObjectsAttributes(self):
        return self.objectsAttributes.resetModified()
 
    def getAllObjectsAttributes(self):
        return self.objectsAttributes
        
    def getAllObjects(self):
        return self.objects

    def postUpdateDataNotification(self):
        self.mainLogic.notificationCenter.postNotification("DataHasBeenUpdated",self)

    def updateDataNoNotify(self, crfName, className, classInstanceNumber, attributeName, attributeValue, evaluateGlobals=True):
        dataUpdated = self.updateData(crfName,className,classInstanceNumber,attributeName,attributeValue,evaluateGlobals,False)
        return dataUpdated

    def updateData(self, crfName, className, classInstanceNumber, attributeName, attributeValue, evaluateGlobals=True, notifyUpdateData=True):

        if self.mainLogic.userType == psc.USER_VIEWER:
            if notifyUpdateData:
                self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
            return False

        currentAttributeValues = self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)

        if self.isMultiInstance(crfName,className,attributeName):
            if currentAttributeValues == attributeValue:
                if notifyUpdateData:
                    self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
                return False
        else:
            if currentAttributeValues and attributeValue == currentAttributeValues[0]:
                if notifyUpdateData:
                    self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
                return False
            elif not currentAttributeValues and attributeValue == None:
                if notifyUpdateData:
                    self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
                return False

        if self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName) in psc.basedataAttributeDict.values():
            if self.isMultiInstance(crfName,className,attributeName):
                if attributeValue == []:
                    if notifyUpdateData:
                        self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
                    return False
            else:
                if attributeValue == None:
                    if notifyUpdateData:
                        self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
                    return False

        if self.getAdmissionStatus(crfName) in ['4','5'] and not self.ignoreStatusForUpdate:
            self.mainLogic.notificationCenter.postNotification("DataModifiedForbidden",self)
            if notifyUpdateData:
                self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
            return False

        self.mainLogic.beginCriticalSection()

        inputDate = self.mainLogic.getDateTime()

        newValues = []
        if self.isMultiInstance(crfName,className,attributeName):
            if currentAttributeValues:
                if attributeValue:
                    for entry in attributeValue:
                        if entry not in currentAttributeValues:
                            newValues.append(entry) 
            else:
                newValues = attributeValue
            self.setAttributeValue(crfName,className,classInstanceNumber,attributeName,attributeValue,inputDate)
        else:
            self.setAttributeValue(crfName,className,classInstanceNumber,attributeName,attributeValue,inputDate)
            newValues.append(attributeValue)

        userInfo = {'crfName':crfName, 'className':className, 'classInstanceNumber':classInstanceNumber, 'attributeName':attributeName}
        self.mainLogic.notificationCenter.postNotification("AttributeHasBeenSet",self,userInfo)

        #TODO: should be handled by observers
        self.evaluateExcludes(crfName,className,classInstanceNumber,attributeName,newValues)
        if evaluateGlobals:
            self.evaluateGlobals()

        self.modified = True

        if notifyUpdateData:
            self.mainLogic.notificationCenter.postNotification("DataHasBeenUpdated",self)
            if className in ['errorDetail','warningDetail']:
                self.mainLogic.notificationCenter.postNotification("ErrorsHaveBeenUpdated",self)
        
        if self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName) in psc.basedataAttributeDict.values():
            self.mainLogic.notificationCenter.postNotification("BasedataHasBeenUpdated",self)

        if self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType') == 'timestamp':
            if notifyUpdateData:
                self.mainLogic.notificationCenter.postNotification("TimeStampHasBeenUpdated",self)
            timeStampClassNames = self.mainLogic.crfData.getClassesByPropertyWithValue(crfName,'timeStamp',self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName))
            if timeStampClassNames:
                for timeStampClassName in timeStampClassNames:
                    self.mainLogic.evaluator.flagClassAsDirty(crfName,timeStampClassName)
            self.evaluateGlobals()
 
        self.mainLogic.endCriticalSection()

        return True

    def evaluateCalculatedSinglePass(self):
        allCrfNames = self.mainLogic.crfData.getCrfNames()
        for aCrfName in allCrfNames:
            self.evaluateCalculated(aCrfName,evaluateProperties=False,evaluateGlobals=False)
 
    #def evaluateGlobals(self, updateStatus=True, evaluateProperties=True):
    def evaluateGlobals(self, updateStatus=False, evaluateProperties=True):
        allCrfNames = self.mainLogic.crfData.getCrfNames()
        anyCrfEnabledUpdated = False
        for aCrfName in allCrfNames:
            crfEnabledUpdated, anyUpdated = self.evaluateCalculated(aCrfName,evaluateProperties)
            if crfEnabledUpdated:
                anyCrfEnabledUpdated = True
            self.evaluateErrors(aCrfName)
        if anyCrfEnabledUpdated and updateStatus:
            self.mainLogic.updateStatus()
            self.mainLogic.notificationCenter.postNotification("CrfEnabledHasBeenUpdated",self)

    def addNewObjectToContainer(self, crfName, className, containerCrfName, containerClassName, containerAttributeName, evaluateGlobals=False, notifyUpdateData=False):

        if self.getAdmissionStatus(crfName) in ['4','5'] and not self.ignoreStatusForUpdate:
            self.mainLogic.notificationCenter.postNotification("DataModifiedForbidden",self)
            if notifyUpdateData:
                self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
            return

        self.mainLogic.beginCriticalSection()
        classInstanceNumber = self.registerNewInstanceNumberForClass(crfName,className)
        inputDate = self.mainLogic.getDateTime()

        timeStamp = self.getTimeStampForClass(crfName,className)
        objectCode = self.insertObject(crfName,className,classInstanceNumber,inputDate,timeStamp)

        containerClassInstanceNumbers = self.getInstanceNumbersForClass(containerCrfName,containerClassName)

        if len(containerClassInstanceNumbers) > 1:
            print "Error: container class %s should not have more than one instance", containerClassName
            self.mainLogic.endCriticalSection()
            return
        if not containerClassInstanceNumbers:
            containerClassInstanceNumbers = self.registerSingleInstanceNumberForClass(containerCrfName,containerClassName)
        containerClassInstanceNumber = containerClassInstanceNumbers[0]

        #TODO: check that container attribute is of type object
        attributeValues = self.getAttributeValuesForObject(containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName)
        attributeValues.append(objectCode)
        self.updateData(containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName,attributeValues,evaluateGlobals=evaluateGlobals,notifyUpdateData=notifyUpdateData)

        if not objectCode in self.objectCodesToContainers:
            self.objectCodesToContainers[objectCode] = []
        containerAttributeFullName = self.mainLogic.crfData.joinAttributeName(containerCrfName,containerClassName,containerAttributeName)
        if not containerAttributeFullName in self.objectCodesToContainers[objectCode]:
            self.objectCodesToContainers[objectCode].append(containerAttributeFullName)
        
        self.mainLogic.endCriticalSection()

        return classInstanceNumber

    def removeObjectCodeInContainer(self, objectCode, containerCrfName, containerClassName, containerAttributeName, evaluateGlobals=False, notifyUpdateData=False):
        classInfo = self.objectCodesToClasses[objectCode]
        self.removeObjectInContainer(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],containerCrfName,containerClassName,containerAttributeName,evaluateGlobals=evaluateGlobals,notifyUpdateData=notifyUpdateData)

    def removeObjectInContainer(self, crfName, className, classInstanceNumber, containerCrfName, containerClassName, containerAttributeName, evaluateGlobals=False, notifyUpdateData=False):

        if self.getAdmissionStatus(crfName) in ['4','5'] and not self.ignoreStatusForUpdate:
            self.mainLogic.notificationCenter.postNotification("DataModifiedForbidden",self)
            if notifyUpdateData:
                self.mainLogic.notificationCenter.postNotification("DataCannotBeUpdated",self)
            return

        self.mainLogic.beginCriticalSection()

        containerClassInstanceNumbers = self.getInstanceNumbersForClass(containerCrfName,containerClassName)

        if len(containerClassInstanceNumbers) > 1:
            print "Error: container class %s should not have more than one instance", containerClassName
            self.mainLogic.endCriticalSection()
            return
        if not containerClassInstanceNumbers:
            containerClassInstanceNumbers = self.registerSingleInstanceNumberForClass(containerCrfName,containerClassName)
        containerClassInstanceNumber = containerClassInstanceNumbers[0]

        attributeValues = self.getAttributeValuesForObject(containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName)
        objectCode = self.getObjectCode(crfName,className,classInstanceNumber)

        if objectCode in self.objectCodesToContainers:
            containerAttributeFullName = self.mainLogic.crfData.joinAttributeName(containerCrfName,containerClassName,containerAttributeName)
            if containerAttributeFullName in self.objectCodesToContainers[objectCode]:
                self.objectCodesToContainers[objectCode].remove(containerAttributeFullName)

        if objectCode in attributeValues:
            attributeValues.remove(objectCode)

        self.removeObjectAndAttributes(crfName,className,classInstanceNumber)
        self.unregisterInstanceNumberForClass(crfName,className,classInstanceNumber)
        #self.objectCodesToClasses.pop(objectCode)

        self.updateData(containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName,attributeValues,evaluateGlobals=evaluateGlobals,notifyUpdateData=notifyUpdateData)
        self.mainLogic.endCriticalSection()

    def getCodingSetNameForAttribute(self, crfName, className, attributeName, classInstanceNumber = 1):
        codingSetName = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'codingSet')

        if codingSetName:
            return codingSetName

        codingSetFormula = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'codingSetFormula')

        if codingSetFormula:
            if classInstanceNumber == 1:
                codingSetName = self.mainLogic.evaluator.eval(codingSetFormula)
            else:
                codingSetName = self.mainLogic.evaluator.eval(codingSetFormula,crfName,className,classInstanceNumber,attributeName)
            print 'CODINGSETNAME FROM FORMULA:', codingSetName

        return codingSetName

    def evaluateExcludes(self,crfName,className,classInstanceNumber,attributeName,newValues):
        #TODO: evaluateExcludes only for changes
        if self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType') != 'codingset':
            return
        self.mainLogic.beginCriticalSection()
        excludeInAttributes = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'excludeInAttributes')
        if excludeInAttributes:
            excludeInAttributes = excludeInAttributes.split(';')
        for newValue in newValues:
            value = newValue
            if value == None:
                continue
            try:
                valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(value)
            except:
                continue
            excludesProperty = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'excludes')
            if excludesProperty == None:
                continue
            for excludedValue in excludesProperty.split(';'):
                if not excludedValue:
                    continue
                try:
                    excludedCrfName, excludedCodingSetName, excludedCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(excludedValue)
                except:
                    print "Cannot split codingSetValueName:", excludedValue
                    continue

                excludedAttributeName = None
                if excludedCodingSetName == valueCodingSetName:
                    excludedCrfName = crfName
                    excludedClassName = className
                    excludedClassInstanceNumber = classInstanceNumber
                    excludedAttributeName = attributeName
                else:
                    if not excludeInAttributes:
                        continue
                    for excludeInAttribute in excludeInAttributes:
                        if not excludeInAttribute:
                            continue
                        try:
                            excludeInCrfName, excludeInClassName, excludeInAttributeName = self.mainLogic.crfData.splitAttributeName(excludeInAttribute)
                        except:
                            print "ERROR while splitting attribute name %s for excludeInAttribute" % excludeInAttribute
                        excludeInCodingSetFullName = self.mainLogic.crfData.getPropertyForAttribute(excludeInCrfName,excludeInClassName,excludeInAttributeName,'codingSet')
                        try:
                            if excludeInCodingSetFullName == self.mainLogic.crfData.joinCodingSetName(excludedCrfName,excludedCodingSetName):
                                excludeInCrfName, excludeInCodingSetName = self.mainLogic.crfData.splitCodingSetName(excludeInCodingSetFullName)
                                excludedCrfName = excludeInCrfName
                                excludedClassName = excludeInClassName
                                #TODO: limitation here. No idea on how to lift it. Ok for now.
                                #probably best way is specify self, all or first at the XML level.
                                excludedClassInstanceNumber = 1
                                excludedAttributeName = excludeInAttributeName
                                break
                        except BaseException, e:
                            print "Error:",e

                if not excludedAttributeName:
                    print 'WARNING: uncaught exclusion: %s excludes %s' % (value,excludedValue)
                    continue

                attributeValues = self.getAttributeValuesForObject(excludedCrfName,excludedClassName,excludedClassInstanceNumber,excludedAttributeName)

                if not attributeValues:
                    continue

                multiInstance = self.isMultiInstance(excludedCrfName,excludedClassName,excludedAttributeName)

                if multiInstance:
                    anyExcluded = False
                    newAttributeValues = []
                    for attributeValue in attributeValues:
                        if attributeValue != excludedValue:
                            newAttributeValues.append(attributeValue)
                        else:
                            anyExcluded = True

                    if anyExcluded:
                        self.updateDataNoNotify(excludedCrfName,excludedClassName,excludedClassInstanceNumber,excludedAttributeName,newAttributeValues,evaluateGlobals=False)
                else:
                    attributeValue = attributeValues[0]
                    if attributeValue == excludedValue:
                        attributeValue = None
                        self.updateDataNoNotify(excludedCrfName,excludedClassName,excludedClassInstanceNumber,excludedAttributeName,attributeValue,evaluateGlobals=False)
        self.mainLogic.endCriticalSection()

    def insertObject(self, crfName, className, classInstanceNumber, inputDate, timeStamp):

        #localId = self.getNewObjectDataLocalId()
        localId = self.mainLogic.getNewLocalId('objectData')
        dataStorage = self.mainLogic.crfData.getPropertyForClass(crfName,className,'dataStorage')
        if not dataStorage:
            dataStorage = 'admission'
 
        newRow = dict()
        newRow['crfName'] = crfName 
        newRow['className'] = className
        newRow['multiInstanceNumber'] = classInstanceNumber
        newRow['externalKey'] = self.getExternalKey(dataStorage)
        #newRow['objectCode'] = str(self.mainLogic.centrecode) + '-' + str(localId) 
        newRow['objectCode'] = localId 
        newRow['centreCode'] = self.mainLogic.centrecode 
        #newRow['localId'] = localId 
        newRow['inputDate'] =  inputDate
        newRow['inputUserKey'] = self.mainLogic.inputUserKey
        #da rivedere (deve venire dai controlli)
        newRow['idActionReason'] = 1
        newRow['crfVersion'] = self.mainLogic.crfData.getPropertyForCrf(crfName,'version')
        newRow['timeStamp'] = timeStamp

        if self.objects.get(crfName,className,classInstanceNumber,timeStamp):
            try:
                self.objectCodesToClasses.pop(self.objects.get(crfName,className,classInstanceNumber,timeStamp)['objectCode'])
            except:
                print 'Object code %d not found in objectCodesToClasses' % self.objects.get(crfName,className,classInstanceNumber,timeStamp)['objectCode']

        self.objectCodesToClasses[newRow['objectCode']] = {'crfName':crfName, 'className':className, 'classInstanceNumber':classInstanceNumber, 'timeStamp':timeStamp}
        self.objects.set(newRow)

        self.registerTimeStampForClass(crfName,className,timeStamp)

        return newRow['objectCode']

    def insertAttribute(self, crfName, className, attributeName, objectCode, value, multiInstanceNumber, inputDate):

        #localId = self.getNewAttributeDataLocalId()
        localId = self.mainLogic.getNewLocalId('attributeData')

        if self.objectsAttributes.has(objectCode,attributeName,multiInstanceNumber):
            self.objectsAttributes.setValue(objectCode,attributeName,multiInstanceNumber,value,localId,inputDate)
            return

        newRow = dict()
        newRow['crfName'] = crfName
        newRow['className'] = className
        newRow['attributeName'] = attributeName
        newRow['multiInstanceNumber'] = multiInstanceNumber
        newRow['objectCode'] = objectCode 
        newRow['centreCode'] = self.mainLogic.centrecode 
        newRow['value'] = value 
        newRow['inputUserKey'] = self.mainLogic.inputUserKey
        newRow['localId'] = localId
        newRow['inputDate'] = inputDate

        self.objectsAttributes.set(newRow) 

    def getCompletedClassNames(self,crfName):
        completedClassNames = []
        for className in self.mainLogic.crfData.getClassNamesForCrf(crfName):
            
            classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
            attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
            foundNone = False
            for classInstanceNumber in classInstanceNumbers:
                for attributeName in attributeNames:
                    #if not self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName) and not self.getAttributeProperty(crfName,className,attributeName,'visibility') == False and not self.getAttributeProperty(crfName,className,attributeName,'enabled') == False:
                    if not self.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName) and not self.mainLogic.crfData.getPropertyForAttribute(crfName, className, attributeName, 'excludeFromStatus'):
                        foundNone = True
                        break
                    
                if foundNone:
                    break
            if classInstanceNumbers and not foundNone:
                completedClassNames.append(className)
        return completedClassNames

    def getRegisteredClassNames(self,crfName):
        registeredClassNames = set([])
        for className in self.mainLogic.crfData.getClassNamesForCrf(crfName):
            classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
            if self.mainLogic.crfData.getPropertyForClass(crfName,className,'dynamic') == '1' and (not classInstanceNumbers or classInstanceNumbers == [1]):
                continue
            registeredClassNames.add(className)
        return registeredClassNames
           
    def evaluateCalculated(self,crfName,evaluateProperties=True,evaluateGlobals=True):
        if not self.mainLogic.crfData.getClassNamesForCrf(crfName):
            return False
        self.mainLogic.beginCriticalSection()
        crfEnabledUpdated = False
        if evaluateProperties:
            crfEnabledUpdated = self.evaluateCrfProperties(crfName)
        anyUpdated = False
        for className in self.mainLogic.crfData.getClassNamesForCrf(crfName):
            if evaluateProperties:
                self.evaluateClassProperties(crfName,className)
            for attributeName in self.mainLogic.crfData.getAttributeNamesForClass(crfName,className):
                #self.evaluateAttributeProperties(crfName,className,attributeName)
                computedFormula = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'computedFormula')
                if not computedFormula:
                    continue
                inputDate = self.mainLogic.getDateTime()
                classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
                if not classInstanceNumbers and self.mainLogic.crfData.getPropertyForClass(crfName,className,'dynamic') != '1':
                    classInstanceNumbers = self.registerSingleInstanceNumberForClass(crfName,className)
                for classInstanceNumber in classInstanceNumbers:
                    if classInstanceNumber == 1:
                        value = self.mainLogic.evaluator.eval(computedFormula)
                    else:
                        if self.getObjectCode(crfName,className,classInstanceNumber) == None:
                            continue
                        value = self.mainLogic.evaluator.eval(computedFormula,crfName,className,classInstanceNumber,attributeName)
                    updated = self.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,value,evaluateGlobals=evaluateGlobals)
                    if updated:
                        anyUpdated = True
            #self.evaluateClassProperties(crfName,className)
        self.mainLogic.endCriticalSection()
        return crfEnabledUpdated, anyUpdated

    def evaluateCrfProperties(self,crfName):
        anyUpdated = False
        evaluator = self.mainLogic.evaluator
        enabledResult = True
        enabledExpression = self.mainLogic.crfData.getPropertyForCrf(crfName,'enabled')
        if enabledExpression:
            enabledResult = bool(evaluator.eval(enabledExpression))
        anyChange = False
        if self.getCrfProperty(crfName,'enabled') != enabledResult:
            anyChange = True

        if not anyChange:
            return anyUpdated

        self.setCrfProperty(crfName,'enabled',enabledResult)
        anyUpdated = True

        return anyUpdated

    def evaluateClassProperties(self,crfName,className):
        anyUpdated = False
        evaluator = self.mainLogic.evaluator
        crfEnabled = self.getCrfProperty(crfName,'enabled')
        visibilityResult = True
        enabledResult = True
        keepValueIfDisabled = None
        if True:
        #if crfEnabled:
            visibilityExpression = self.mainLogic.crfData.getPropertyForClass(crfName,className,'visible')
            if visibilityExpression:
                visibilityResult = bool(evaluator.eval(visibilityExpression))
            enabledExpression = self.mainLogic.crfData.getPropertyForClass(crfName,className,'enabled')
            if enabledExpression:
                enabledResult = bool(evaluator.eval(enabledExpression))
                keepValueIfDisabled = self.mainLogic.crfData.getPropertyForClass(crfName,className,'keepValueIfDisabled')
        #else:
        #    visibilityResult = False
        #    enabledResult = False

        anyChange = False
        if self.getClassProperty(crfName,className,'visibility') != visibilityResult:
            anyChange = True
        if self.getClassProperty(crfName,className,'enabled') != enabledResult:
            anyChange = True

        if not anyChange:
            return anyUpdated

        self.mainLogic.beginCriticalSection()

        classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
        
        self.setClassProperty(crfName,className,'visibility',visibilityResult)
        self.setClassProperty(crfName,className,'enabled',enabledResult)

        if anyChange and (visibilityResult == False or (enabledResult == False and not keepValueIfDisabled)):
        #if anyChange and visibilityResult == False:
            for attributeName in self.mainLogic.crfData.getAttributeNamesForClass(crfName,className):
                #TODO: this is for not touching computed values when they have no visibility
                #computedFormula = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'computedFormula')
                #if computedFormula:
                #    continue
                multiInstance = self.isMultiInstance(crfName,className,attributeName)
                if multiInstance:
                    for classInstanceNumber in classInstanceNumbers:
                        updated = self.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,[])
                        if updated:
                            anyUpdated = True
                else:
                    for classInstanceNumber in classInstanceNumbers:
                        updated = self.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,None)
                        if updated:
                            anyUpdated = True

        self.mainLogic.endCriticalSection()

        return anyUpdated
 
    #def evaluateAttributeProperties(self,crfName,className,attributeName):
    #    anyUpdated = False
    #    evaluator = self.mainLogic.evaluator
    #    visibilityResult = True
    #    enabledResult = True
    #    visibilityExpression = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'visible')
    #    if visibilityExpression:
    #        visibilityResult = bool(evaluator.eval(visibilityExpression))
    #    enabledExpression = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'enabled')
    #    if enabledExpression:
    #        enabledResult = bool(evaluator.eval(enabledExpression))
    #    anyChange = False
    #    if self.getAttributeProperty(crfName,className,attributeName,'visibility') != visibilityResult:
    #        anyChange = True
    #    if self.getAttributeProperty(crfName,className,attributeName,'enabled') != enabledResult:
    #        anyChange = True

    #    if not anyChange:
    #        return anyUpdated

    #    classInstanceNumbers = self.getInstanceNumbersForClass(crfName,className)
 
    #    self.setAttributeProperty(crfName,className,attributeName,'visibility',visibilityResult)
    #    self.setAttributeProperty(crfName,className,attributeName,'enabled',enabledResult)

    #    if anyChange and visibilityResult == False:
    #        multiInstance = self.isMultiInstance(crfName,className,attributeName)
    #        if multiInstance:
    #            for classInstanceNumber in classInstanceNumbers:
    #                updated = self.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,[])
    #                if updated:
    #                    anyUpdated = True
    #        else:
    #            for classInstanceNumber in classInstanceNumbers:
    #                updated = self.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,None)
    #                if updated:
    #                    anyUpdated = True
 
    #    return anyUpdated
   
    def evaluateErrors(self,crfName):

        self.mainLogic.beginCriticalSection()

        previousIgnoreStatusFlag = self.ignoreStatusForUpdate
        if crfName != psc.coreCrfName:
            self.ignoreStatusForUpdate = True

        evaluator = self.mainLogic.evaluator

        anyErrorsAdded = False
        anyErrorsRemoved = False

        for errorId in self.mainLogic.crfData.getErrorIdsForCrf(crfName).keys():
        
            errorInfo = self.mainLogic.crfData.getErrorInfoForId(crfName,errorId)
            errorCrfName = psc.coreCrfName

            if crfName == errorCrfName and 'originCrfName' in errorInfo:
                continue

            warning = "0"
            if 'warning' in errorInfo:
                warning = errorInfo['warning']
            errorResult = bool(evaluator.eval(errorInfo['expression']))

            if self.getCrfProperty(crfName,'enabled') == False:
                errorResult = False

            if not self.mainLogic.crfData.getErrorInfoForId(errorCrfName,errorId):
                self.mainLogic.crfData.addErrorToCrf(errorCrfName,errorId,errorInfo,crfName)

            containerClassName = 'errorList'
            containerAttributeName = 'errorList'
            className = 'errorDetail'
            attributeName = 'errorId'
            crfAttributeName = 'errorCrf'
            crfLabelAttributeName = 'errorCrfLabel'
            crfLabel = self.mainLogic.translateString(self.mainLogic.crfData.getPropertyForCrf(crfName,'label'))

            if warning == "1":
                containerClassName = 'warningList'
                containerAttributeName = 'warningList'
                className = 'warningDetail'
                attributeName = 'warningId'
                crfAttributeName = 'warningCrf'
                crfLabelAttributeName = 'warningCrfLabel'

            containerClassInstanceNumbers = self.getInstanceNumbersForClass(errorCrfName,containerClassName)
            if len(containerClassInstanceNumbers) > 1:
                print "Error: container class %s should not have more than one instance" % containerClassName
                continue
            if not containerClassInstanceNumbers:
                containerClassInstanceNumbers = self.registerSingleInstanceNumberForClass(errorCrfName,containerClassName)
            containerClassInstanceNumber = containerClassInstanceNumbers[0]

            if errorResult:
                maxOccurrences = 1
                attributeValues = self.getAttributeValuesForClass(errorCrfName,className,attributeName)
                if attributeValues:
                    numberOfOccurrences = len([el for el in attributeValues if el == errorId])
                    if numberOfOccurrences >= maxOccurrences:
                        continue

                classInstanceNumber = self.addNewObjectToContainer(errorCrfName,className,errorCrfName,containerClassName,containerAttributeName)
                self.updateDataNoNotify(errorCrfName,className,classInstanceNumber,attributeName,errorId)
                self.updateDataNoNotify(errorCrfName,className,classInstanceNumber,crfLabelAttributeName,crfLabel)
                self.updateDataNoNotify(errorCrfName,className,classInstanceNumber,crfAttributeName,crfName)

                anyErrorsAdded = True
            else:

                #classInstanceNumbers = self.getInstanceNumbersForClass(className)
                #classInstanceNumbersToUnregister = []
                #for classInstanceNumber in classInstanceNumbers:
                #    attributeValues = self.getAttributeValuesForObject(className,classInstanceNumber,attributeName)
                #    for value in attributeValues:
                #        if int(value) == int(errorId):
                #            classInstanceNumbersToUnregister.append(classInstanceNumber)
                
                classInstanceNumbersToUnregister = self.getInstanceNumbersForClassAndAttributeValue(errorCrfName,className,attributeName,errorId)

                for classInstanceNumber in classInstanceNumbersToUnregister:

                    self.removeObjectInContainer(errorCrfName,className,classInstanceNumber,errorCrfName,containerClassName,containerAttributeName,evaluateGlobals=False)
                    anyErrorsRemoved = True

        if crfName != psc.coreCrfName:
            self.ignoreStatusForUpdate = previousIgnoreStatusFlag

        self.mainLogic.endCriticalSection()

        if anyErrorsAdded or anyErrorsRemoved:
            self.mainLogic.notificationCenter.postNotification("ErrorsHaveChanged",self)

