import re
import psconstants as psc
import time
import datetime
import math
import random
from pslogging import PsLogger

class PSEvaluator:

    def __init__(self, mainLogic):
        self.mainLogic = mainLogic
        
        rawstr = r"""\|[\w.]*\|"""
        self.expandedre = re.compile(rawstr, re.IGNORECASE)

        rawstr = r"""\$[\w.]*\$"""
        self.nonexpandedre = re.compile(rawstr, re.IGNORECASE)

        rawstr = r"""\|\|[\w.]*\|\|"""
        self.expandeddictre = re.compile(rawstr, re.IGNORECASE)

        rawstr = r"""\@[\w.]*\@"""
        self.expressionre = re.compile(rawstr, re.IGNORECASE)

        self.mainLogic.notificationCenter.addObserver(self,self.onAttributeSet,"AttributeHasBeenSet")
        self.expressionCache = dict()
        self.attributesToExpressions = dict()

    def cleanCache(self):
        self.expressionCache = dict()
        self.attributesToExpressions = dict()

    def flagClassAsDirty(self,crfName,className):
        attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
        for attributeName in attributeNames:
            self.flagAttributeAsDirty(crfName,className,attributeName)

    def flagAttributeAsDirty(self,crfName,className,attributeName):
        try:
            #expressions = self.attributesToExpressions['crfName','className','attributeName']
            expressions = self.attributesToExpressions[crfName,className,attributeName]
        except:
            return
        for expression in expressions:
            try:
                self.expressionCache[expression]['dirtyFlag'] = True
            except:
                pass

    def onAttributeSet(self,notifyingObject,userInfo=None):
        try:
            expressions = self.attributesToExpressions[userInfo['crfName'],userInfo['className'],userInfo['attributeName']]
        except:
            return
        for expression in expressions:
            try:
                self.expressionCache[expression]['dirtyFlag'] = True
            except:
                pass

    def eval(self, expression, lhsCrfName = None, lhsClassName = None, lhsClassInstanceNumber = None, lhsAttributeName = None, noCache = False):
        #caching = False
        #cachedResult = None
        try:
            #1/0
            cachedDict = self.expressionCache[expression]
            if cachedDict['dirtyFlag'] == False and lhsClassInstanceNumber == None and noCache == False and expression[:2] != '$$':
                return cachedDict['result']
                #pass
                #print 'Cached'
                #cachedResult = cachedDict['result']
                #caching = True
        except:
            pass
        workExpression = expression[:]
        if workExpression[:2] == '$$':
            workExpression = workExpression[2:]

        vars = self.expressionre.finditer(workExpression)
        for var in vars:
            placeholder = str(var.group())
            name = placeholder[1:-1]
            pieces = name.split('.')
            if len(pieces) != 2:
                print 'ERROR IN EVALUATION EXPRESSION: %s', workExpression
            crfName = pieces[0]
            exprName = pieces[1]
            exprInfo = self.mainLogic.crfData.getExpressionInfoForName(crfName,exprName)
            mangledName = '%s_%s' % (crfName,exprName)
            functionDef = exprInfo['body'].replace(exprName,mangledName)
            for dependency in exprInfo['dependencies'].split(';'):
                crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(dependency)
                if (crfName,className,attributeName) not in self.attributesToExpressions:
                    self.attributesToExpressions[(crfName,className,attributeName)] = set()
                self.attributesToExpressions[(crfName,className,attributeName)].add(expression)
            workExpression = workExpression.replace(placeholder,mangledName)
            workExpression = '%s\n%s' % (functionDef, workExpression)

        vars = self.nonexpandedre.finditer(workExpression)
        for var in vars:
            placeholder = str(var.group())
            name = placeholder[1:-1]
            pieces = name.split('.')
            if len(pieces) != 3:
                print 'ERROR IN EVALUATING EXPRESSION: %s' % workExpression
            crfName = pieces[0]
            className = pieces[1]
            attributeName = pieces[2]
            if (crfName,className,attributeName) not in self.attributesToExpressions:
                self.attributesToExpressions[(crfName,className,attributeName)] = set()
            self.attributesToExpressions[(crfName,className,attributeName)].add(expression)
            workExpression = workExpression.replace(placeholder, "'%s'" % name)

        vars = self.expandeddictre.finditer(workExpression)
        for var in vars:
            placeholder = str(var.group())
            name = placeholder[2:-2]
            pieces = name.split('.')
            if len(pieces) != 3:
                print 'ERROR IN EVALUATING EXPRESSION: %s' % workExpression
            crfName = pieces[0]
            className = pieces[1]
            attributeName = pieces[2]
            attributeValues = self.mainLogic.dataSession.getAttributeValuesForClassInDict(crfName,className,attributeName)
            if (crfName,className,attributeName) not in self.attributesToExpressions:
                self.attributesToExpressions[(crfName,className,attributeName)] = set()
            self.attributesToExpressions[(crfName,className,attributeName)].add(expression)
            workExpression = workExpression.replace(placeholder, repr(attributeValues))

        vars = self.expandedre.finditer(workExpression)
        for var in vars:
            placeholder = str(var.group())
            name = placeholder[1:-1]
            pieces = name.split('.')
            if len(pieces) != 3:
                print 'ERROR IN EVALUATING EXPRESSION: %s' % workExpression
            crfName = pieces[0]
            className = pieces[1]
            attributeName = pieces[2]
            if crfName == lhsCrfName and className == lhsClassName and lhsClassInstanceNumber != None:
                attributeValues = self.mainLogic.dataSession.getAttributeValuesForObject(crfName,className,lhsClassInstanceNumber,attributeName)
            else:
                attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(crfName,className,attributeName)
            if (crfName,className,attributeName) not in self.attributesToExpressions:
                self.attributesToExpressions[(crfName,className,attributeName)] = set()
            self.attributesToExpressions[(crfName,className,attributeName)].add(expression)
            workExpression = workExpression.replace(placeholder, repr(attributeValues))

        result = None
        try:
            workExpression = workExpression.encode('ascii','xmlcharrefreplace')
            exec("globals()['helperMainLogic'] = self.mainLogic\n"+workExpression)
            #exec(workExpression)
            #self.expressionCache[expression] = {'dirtyFlag':False, 'result':result}
        except BaseException, e:
            pass
            #PsLogger().warning('EvaluatorTag', '#############')
            #PsLogger().warning('EvaluatorTag', expression)
            #PsLogger().warning('EvaluatorTag', '-------------')
            #PsLogger().warning('EvaluatorTag', workExpression)
            #PsLogger().warning('EvaluatorTag', '-------------')
            #PsLogger().warning('EvaluatorTag', str(e))
            #PsLogger().warning('EvaluatorTag', '#############')
            
            #pass
            #print '#####'
            #print expression
            #print workExpression
            #print e
            #print expression[0:80], e

        self.expressionCache[expression] = {'dirtyFlag':False, 'result':result}

        #if caching:
        #    if cachedResult != result:
        #        print 'Cached INCORRECT!'
        #    else:
        #        print 'Cached'
        #else:
        #    print 'Computed'
        #print lhsCrfName, lhsClassName, lhsClassInstanceNumber, lhsAttributeName
        #print 'Computed'
        #print expression
        #print workExpression
        #print result
        return result


#helper functions
   
class psBaseException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return 'psBaseException:' + repr(self.value)
        

def decode(values, mainLogic=None, crfData=None):
    try:
        currentMainLogic = helperMainLogic
    except:
        currentMainLogic = mainLogic
    if crfData != None:
        currentCrfData = crfData
    else:
        currentCrfData = currentMainLogic.crfData
    decodedValues = []
    for value in values:
        if type(value) not in [str,unicode]:
            decodedValues.append(unicode(value))
            continue
        splitDot = value.split('.')
        splitDash = value.split('-')
        if len(splitDot) == 3:
            crfName, codingSetName, codingSetValueName = splitDot
            decodedValue = currentCrfData.getPropertyForCodingSetValue(crfName,codingSetName,codingSetValueName,'value')
            if decodedValue != None:
                decodedValues.append(currentMainLogic.translateString(decodedValue))
            else:
                #decodedValues.append(codingSetValueName)
                personalizations = None
                if currentMainLogic.getAppdataPersonalizations():
                    personalizations = [el.get('value') for el in currentMainLogic.getAppdataPersonalizations().getchildren() if el.get('name') == value]
                if personalizations:
                    decodedValues.append(personalizations[0])
                else:
                    decodedValues.append(value)
                #decodedValues.append(value)
        elif len(splitDash) == 3:
            import datetime
            try:
                testDate = datetime.date(int(splitDash[0]),int(splitDash[1]),int(splitDash[2]))
                decodedValues.append("%s/%s/%s" % (splitDash[2],splitDash[1],splitDash[0]))
            except:
                decodedValues.append(value)
            
            
        else:
            decodedValues.append(value)
    return decodedValues

def shouldHideForAssistance():
    return helperMainLogic.shouldAnonymizeData
    
def decodevalue(value, mainLogic=None, crfData=None):
    return decode([value],mainLogic,crfData)[0]

def all(attributeFullName,timeDict=False):
    helperDataSession = helperMainLogic.dataSession
    crfName, className, attributeName = helperMainLogic.crfData.splitAttributeName(attributeFullName)
    return helperDataSession.getAllAttributeValuesForClass(crfName,className,attributeName,timeDict)

def at(attributeFullName,relativeTimeStamp):

    #if attributeFullName == "adhd.mph.value":
    #    import pdb
    #    pdb.set_trace()
    
    helperDataSession = helperMainLogic.dataSession
    crfName, className, attributeName = helperMainLogic.crfData.splitAttributeName(attributeFullName)
    timeStamp = helperDataSession.getTimeStampForClass(crfName,className)
    
    timeStampAttributeFullName = helperMainLogic.crfData.getPropertyForClass(crfName, className, 'timeStamp')
    timeStampsForTimeStampName = {}
    timeStamps = set()
    if timeStampAttributeFullName == None:
        timeStamps.add(1)
    if timeStampAttributeFullName is not None:
        if timeStampAttributeFullName not in timeStampsForTimeStampName:
            timeStampCrfName, timeStampClassName, timeStampAttributeName = helperMainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
            for timestampedClassName in helperMainLogic.crfData.getClassesByPropertyWithValue(timeStampCrfName, 'timeStamp', timeStampAttributeFullName):
                timeStampsForClass = helperDataSession.getAllTimeStampsForClass(timeStampCrfName,timestampedClassName) #attributeName is not used
                timeStamps.update(timeStampsForClass)
            timeStampsForTimeStampName[timeStampAttributeFullName] = timeStamps
        else:
            timeStamps = timeStampsForTimeStampName[timeStampAttributeFullName]
    
    #TODO: Only for ADHD, merge with main proSAFE branch
    timeStamps = list(timeStamps)
    timeStamps.sort()

    if timeStamp not in timeStamps : 
        return []
    timeStampIndex = timeStamps.index(timeStamp)
    if timeStampIndex + relativeTimeStamp < 0:
        #timeStamp = timeStamps[0]
        return []
    elif timeStampIndex + relativeTimeStamp > len(timeStamps)-1:
        #timeStamp = timeStamps[-1]
        return []
    else:
        timeStamp = timeStamps[timeStampIndex+relativeTimeStamp]
    return helperDataSession.getAttributeValuesForClass(crfName,className,attributeName,timeStamp)

def timestamps(attributeFullName):
    helperDataSession = helperMainLogic.dataSession
    crfName, className, attributeName = helperMainLogic.crfData.splitAttributeName(attributeFullName)
    timeStamps = helperDataSession.getAllTimeStampsForClass(crfName,className,sorted=True)
    return timeStamps

def previous_timestamp(attributeFullName):
    helperDataSession = helperMainLogic.dataSession
    crfName, className, attributeName = helperMainLogic.crfData.splitAttributeName(attributeFullName)
    timeStamp = helperDataSession.getTimeStampForClass(crfName,className)
    timeStamps = timestamps(attributeFullName)
    if timeStamp not in timeStamps:
        return None
    timeStampIndex = timeStamps.index(timeStamp)
    if timeStampIndex == 0:
        return None
    return timeStamps[timeStampIndex-1]

#def notifyDynPageChanged(attributeFullName):
#    userInfo = {'attributeFullName':attributeFullName}
#    helperMainLogic.notificationCenter.postNotification('DynPageHasChanged',None,userInfo)

#def isAdmissionKeyDeleted(admissionKey):
#    query = "SELECT * from admissionDeleted where admissionKey = '%s'" % admissionKey
#    result = helperMainLogic.queryManager.sendQuery(query)
#    if result:
#        return True
#    return False
#

#TODO JSON: replace with jsonStore
def isPatientReadmitted():
    if helperMainLogic.dataSession.readmissionKey:
        return True
    return False
    
def anyValuesInCodingSet(codingSetFullName):
    helperCrfData = helperMainLogic.crfData
    crfName, codingSetName = helperCrfData.splitCodingSetName(codingSetFullName)
    if not helperCrfData.getCodingSetValueNamesForCodingSet(crfName,codingSetName):
        return False
    return True
    
    
#here below the original 
def setNotificationFromCrf(title, text, priority, type='istant', repeatable=False, notificationTime=None, notificationExpireDate=None):
    if type == 'global':
        print 'adding global notification'
        admissionKey = helperMainLogic.dataSession.admissionKey
        #notificationTime = datetime.datetime.now()
        helperMainLogic.bulletinClient.addBulletinManagerServerMessage(title, text, priority, type, repeatable, notificationTime, admissionReference=admissionKey, notificationExpireDate=notificationExpireDate)
    else:
        helperMainLogic.addClientMessage(title, text, priority, type, repeatable, notificationTime)
        
def removeNotificationFromCrf(title, text, priority, type='istant', repeatable=False, notificationTime=None, notificationExpireDate=None):
    if type == 'global':
        admissionKey = helperMainLogic.dataSession.admissionKey
        #notificationTime = datetime.datetime.now()
        helperMainLogic.bulletinClient.removeBulletinManagerServerMessage(title, text, priority, type, repeatable, notificationTime, admissionReference=admissionKey, notificationExpireDate=notificationExpireDate)
    else:
        helperMainLogic.removeClientMessage(title, text, priority, type, repeatable, notificationTime)
        
def encryptionStringForStart():
    myCentreCode = ''
    myCentreCode = str(centreCode())
    CONST_PWD = 'Mt724alT'
    myCentreCode = myCentreCode[2:]
    strIn = "CodiceCentro" + str(myCentreCode)
    strOut = ""
    maxI = len(strIn) +1 
    lenChiave = len(CONST_PWD)
    iChiave = -1    
    for i in range (1, maxI):
        chTmp = strIn[i-1:i]
        codeTmp = ord(chTmp)
        if codeTmp == 9: codeTmp = 31
        iChiave = iChiave + 1
        if iChiave + 1 > lenChiave: iChiave = 0
        if codeTmp >= 31:
            valTmp = codeTmp + ord(CONST_PWD[iChiave:iChiave+1]) + 111
            if valTmp > 254: valTmp = valTmp - 254 + 31
            if valTmp > 254: valTmp = valTmp - 254 + 31
            strOut = chr(valTmp) + strOut
        else:
            strOut = chr(codeTmp) + strOut
    print myCentreCode, strOut
    return strOut    
    
def compareCursors(id, secondCursorList, attributeNameList):
    #TODO: check if needed
    helperDataSession = helperMainLogic.dataSession
    if len(secondCursorList) > 0 and len(attributeNameList) > 0:
        attributeName = attributeNameList[0]
        secondCursor = secondCursorList[0]
    else:
        return False
    
    #firstClassInfo = helperDataSession.getClassInfoForObjectCode(id)
    secondClassInfo = helperDataSession.getClassInfoForObjectCode(secondCursor)
    #firstAttributeValue = helperDataSession.getAttributeValuesForObject(firstClassInfo['crfName'],firstClassInfo['className'],firstClassInfo['classInstanceNumber'],attributeName)
    secondAttributeValue = helperDataSession.getAttributeValuesForObject(helperDataSession.getClassInfoForObjectCode(secondCursor)['crfName'],helperDataSession.getClassInfoForObjectCode(secondCursor)['className'],helperDataSession.getClassInfoForObjectCode(secondCursor)['classInstanceNumber'],attributeName)
    result = False
    if id in secondAttributeValue:
        result = True
    #print 'COMPARE CURSORS RESULT', result, id
    return result
       
def getVisibilityForMicrorganismsClasses(objectCode, attributeValue, pageType=None):
    #TODO: maybe too infection/microrganisms oriented, should we make it overall?
    helperDataSession = helperMainLogic.dataSession
    classInfoForObjectCode = helperDataSession.getClassInfoForObjectCode(objectCode)
    className = classInfoForObjectCode['className']
    classInstanceNumber = classInfoForObjectCode['classInstanceNumber']
    attributeNamesForClass = helperMainLogic.crfData.getAttributeNamesForClass('infection', className)
    selectedClassName = ''
    for attributeName in attributeNamesForClass:
        if pageType:
            if pageType == attributeName:
                attributeValues = helperDataSession.getAttributeValuesForObject('infection',className,classInstanceNumber,attributeName)
                if attributeValue in attributeValues:
                    #found correct attribute
                    return True
        else:
            attributeValues = helperDataSession.getAttributeValuesForObject('infection',className,classInstanceNumber,attributeName)
            if attributeValue in attributeValues:
                #found correct attribute
                return True
    return False
    
def getInstanceNumbersForClassAndAttributeValue(containerAttributeFullName, value):
    if not value:
        return None
    value = value[0]
    helperDataSession = helperMainLogic.dataSession
    crfName, className, attributeName = helperDataSession.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
    classInstanceNumbers = helperDataSession.getInstanceNumbersForClassAndAttributeValue(crfName, className, attributeName, value)
    if len(classInstanceNumbers) > 0:
        return classInstanceNumbers[0]
    return None
    
def getCursorClassInstanceNumberFromObjectCode(objectCode):
    helperDataSession = helperMainLogic.dataSession
    classInfoForObjectCode = helperDataSession.getClassInfoForObjectCode(objectCode)
    return classInfoForObjectCode['classInstanceNumber']
    
def getClassInfoFromObjectCode(objectCode):
    helperDataSession = helperMainLogic.dataSession
    classInfoForObjectCode = helperDataSession.getClassInfoForObjectCode(objectCode)
    return classInfoForObjectCode

def getCursorInfectionIdValue(containerAttributeFullName, objectCode):
    helperDataSession = helperMainLogic.dataSession
    crfName, className, attributeName = helperDataSession.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
    
    classInfoForObjectCode = helperDataSession.getClassInfoForObjectCode(objectCode)
    classInstanceNumber = classInfoForObjectCode['classInstanceNumber']
    attributeValues = helperDataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
    return attributeValues[0]
    
def getObjectCode(crfName,className,classInstanceNumber):
    helperDataSession = helperMainLogic.dataSession
    return helperDataSession.getObjectCode(crfName,className,classInstanceNumber)
    
def updateDataWithFormula(attributeFullName, computedFormula):
    helperDataSession = helperMainLogic.dataSession
    if not helperDataSession:
        return []
    crfName, className, attributeName = helperDataSession.mainLogic.crfData.splitAttributeName(attributeFullName)
    helperEvaluator = helperMainLogic.evaluator
    value = helperEvaluator.eval(computedFormula,crfName,className,attributeName)
    #updated = helperDataSession.updateDataNoNotify(crfName,className,attributeName,value)
    updateData(attributeFullName, value)
    
def updateData(attributeFullName, attributeValue, notifyUpdateData=True):
    helperDataSession = helperMainLogic.dataSession
    if not helperDataSession:
        return []
    crfName, className, attributeName = helperDataSession.mainLogic.crfData.splitAttributeName(attributeFullName)
    helperDataSession.updateData(crfName,className,1,attributeName,attributeValue,notifyUpdateData=notifyUpdateData)
    
def updateDataNoNotify(attributeFullName, attributeValue):
    updateData(attributeFullName,attributeValue,notifyUpdateData=False)

def getCrfStartingDate(crfName):
    #network/proxy
    if helperMainLogic.appdataManager.getAppdataElementsWithAttribute('centre/crfs/crf', 'name', crfName)[0].get('minValidDate'):
        return helperMainLogic.appdataManager.getAppdataElementsWithAttribute('centre/crfs/crf', 'name', crfName)[0].get('minValidDate')
    else:
        return None
    
def updateCursorFromContainerWithValues(containerAttributeFullName, cursorAttributeFullName, attributeName, values, cursorClassInstanceNumber=None):
    helperDataSession = helperMainLogic.dataSession

    if not helperDataSession:
        return []

    containerCrfName, containerClassName, containerAttributeName = helperDataSession.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
    cursorCrfName, cursorClassName, cursorAttributeName = helperDataSession.mainLogic.crfData.splitAttributeName(cursorAttributeFullName)

    objectCodes = helperDataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
    cursorObjectCodes = []
    for objectCode in objectCodes:
        classInfo = helperDataSession.getClassInfoForObjectCode(objectCode)
        #if cursorClassInstanceNumber and int(classInfo['classInstanceNumber']) != int(cursorClassInstanceNumber):
        #    continue
        currentValues = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeName)
        if not (set(values) - set(currentValues)):   
            cursorObjectCodes.append(objectCode)

    helperDataSession.updateDataNoNotify(cursorCrfName,cursorClassName,1,cursorAttributeName,cursorObjectCodes,evaluateGlobals=False)
    #helperMainLogic.notificationCenter.postNotification('PageShouldBeRebuilt',helperMainLogic)
    
    return cursorObjectCodes

def updateContainerWithValues(containerAttributeFullName, attributeFullNamesToValuesDict):
    try:
        helperDataSession = helperMainLogic.dataSession

        if not helperDataSession:
            return []
        
        for attributeFullName in attributeFullNamesToValuesDict:
            values = attributeFullNamesToValuesDict[attributeFullName]

            containerCrfName, containerClassName, containerAttributeName = helperDataSession.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
            crfName, className, attributeName = helperDataSession.mainLogic.crfData.splitAttributeName(attributeFullName)
            objectCodes = helperDataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
            
            for objectCode in objectCodes:
                classInfo = helperDataSession.getClassInfoForObjectCode(objectCode)
                currentValues = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeName)
                if not currentValues:
                    helperDataSession.removeObjectInContainer(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],containerCrfName,containerClassName,containerAttributeName)
                    continue
                for currentValue in currentValues:
                    if crfName == classInfo['crfName'] and className == classInfo['className'] and currentValue not in values:
                        helperDataSession.removeObjectInContainer(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],containerCrfName,containerClassName,containerAttributeName)
            
            tmpInstanceNumbers = helperDataSession.getInstanceNumbersForClass(crfName,className)
            for tmpInstanceNumber in tmpInstanceNumbers:
                tmpObjectCode = helperDataSession.getObjectCode(crfName,className,tmpInstanceNumber)
                if tmpObjectCode not in objectCodes:
                    helperDataSession.removeObjectInContainer(crfName,className,tmpInstanceNumber,containerCrfName,containerClassName,containerAttributeName,evaluateGlobals=False, notifyUpdateData=False, removeMe=True)
                    
                        
            for value in values:
                found = False
                for objectCode in objectCodes:
                    classInfo = helperDataSession.getClassInfoForObjectCode(objectCode)
                    if classInfo:
                        currentValues = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeName)
                        if crfName == classInfo['crfName'] and className == classInfo['className'] and currentValues and value in currentValues:
                            found = True
                            break

                if found:
                    continue

                classInstanceNumber = helperDataSession.addNewObjectToContainer(crfName,className,containerCrfName,containerClassName,containerAttributeName,evaluateGlobals=False)
                helperDataSession.updateDataNoNotify(crfName,className,classInstanceNumber,attributeName,value,evaluateGlobals=False)
      
        
        objectCodes = helperDataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
        return objectCodes
    except BaseException, e:
        print e
        return []
    
def erasePetal(crfName):
    helperDataSession = helperMainLogic.dataSession    
    classesForPetalName = helperDataSession.mainLogic.crfData.getClassNamesForCrf(crfName)    
    for className in classesForPetalName:    
        
        attributesForClassName = helperDataSession.mainLogic.crfData.getAttributeNamesForClass(crfName, className)
        for attributeName in attributesForClassName:       
            attributeFullName = '%s.%s.%s' %(crfName, className, attributeName)
            try:
                updateDataNoNotify(attributeFullName, None)
            except BaseException, e:
                try:
                    updateDataNoNotify(attributeFullName, [])
                except BaseException, e:
                    print '#####################################'
                    print 'attributeFullName', attributeFullName
                    print '#####################################'
    
def updateContainerWithValuesDouble(containerAttributeFullName, attributeNames, codingSetToClassesCodingSetName, infectionIdsToMicroIds, mainContainerCrfName='infection', mainContainerClassName='procedureDetailInfectAdm', mainContainerAttributeName='infectionId' ):
    
    helperDataSession = helperMainLogic.dataSession
    if not helperDataSession:
        return []
    containerCrfName, containerClassName, containerAttributeName = helperDataSession.mainLogic.crfData.splitAttributeName(containerAttributeFullName)
    
    objectCodes = helperDataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
    
    for objectCode in objectCodes:
        classInfo = helperDataSession.getClassInfoForObjectCode(objectCode)
        currentValues0 = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeNames[0])
        currentValues1 = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeNames[1])
        found = False
        if currentValues0 and currentValues0[0] in infectionIdsToMicroIds:
            if currentValues1 and currentValues1[0] in infectionIdsToMicroIds[currentValues0[0]]:
                found = True
        if not found:
            helperDataSession.removeObjectInContainer(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],containerCrfName,containerClassName,containerAttributeName)
    
    for infectionId in infectionIdsToMicroIds:
        microIds = infectionIdsToMicroIds[infectionId]
        for microId in microIds:
            crfName, codingSetName, codingSetValueName = helperDataSession.mainLogic.crfData.splitCodingSetValueName(microId)
    
            microDetailClassNames = helperDataSession.mainLogic.crfData.getPropertyForCodingSetValue(crfName,codingSetToClassesCodingSetName,codingSetValueName,'value')
            if not microDetailClassNames:
                continue
            microDetailClassNames = microDetailClassNames.split(',')
            
            for microDetailClassName in microDetailClassNames:
    
                crfName, microClassName = helperDataSession.mainLogic.crfData.splitClassName(microDetailClassName)
                objectCodes = helperDataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
                #currentInstanceNumber = helperDataSession.getInstanceNumbersForClassAndAttributeValue(mainContainerCrfName, mainContainerClassName, mainContainerAttributeName, infectionId)[0]
                #currentInstanceNumber = helperDataSession.getInstanceNumbersForClassAndAttributeValue('infection', 'procedureDetailInfectAdm', 'infectionId', infectionId)
                found = False
                for objectCode in objectCodes:
                    classInfo = helperDataSession.getClassInfoForObjectCode(objectCode)
                    if crfName == classInfo['crfName'] and microClassName == classInfo['className']:
                        currentValues0 = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeNames[0])
                        if currentValues0 and infectionId in currentValues0:
                            currentValues1 = helperDataSession.getAttributeValuesForObject(classInfo['crfName'],classInfo['className'],classInfo['classInstanceNumber'],attributeNames[1])
                            if currentValues1 and microId in currentValues1:
                                found = True
                                break
                
                if found:
                    continue
    
                classInstanceNumber = helperDataSession.addNewObjectToContainer(crfName,microClassName,containerCrfName,containerClassName,containerAttributeName,evaluateGlobals=False)
                helperDataSession.updateDataNoNotify(crfName,microClassName,classInstanceNumber,attributeNames[0],infectionId,evaluateGlobals=False)
                helperDataSession.updateDataNoNotify(crfName,microClassName,classInstanceNumber,attributeNames[1],microId,evaluateGlobals=False)
    objectCodes = helperDataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)

    helperMainLogic.notificationCenter.postNotification('PageShouldBeRebuilt',helperMainLogic)
       
    return objectCodes

#def fillContainerWithObjectsOfClass(containerAttributeFullName, classFullName, numberOfObjects, retainOriginal = True):
#    containerCrfName, containerClassName, containerAttributeName = helperMainLogic.crfData.splitAttributeName(containerAttributeFullName)
#    crfName, className = helperMainLogic.crfData.splitAttributeName(classFullName)

def countries(countryCodesString):
    countryCodes = countryCodesString.split()
    if centreCodeMatches(countryCodes):
        return True
    return False
    
def notCountries(countryCodesString):
    countryCodes = countryCodesString.split()
    if centreCodeMatches(countryCodes):
        return False
    return True

def centreCode():
    return helperMainLogic.getCentreCode()

def centreCodeMatches(centreCodeSubstrings):
    for centreCodeSubstring in centreCodeSubstrings:
        if helperMainLogic.centrecode.startswith(centreCodeSubstring):
            return True
    return False

def maximum(valuelist):
    if valuelist:
        return max(valuelist)
    raise psBaseException('cannot return maximum value if list is None. Please check the formula')
    
def minimum(valuelist):
    if valuelist:
        return min(valuelist)
    raise psBaseException('cannot return minimum value if list is None. Please check the formula')

def booleanValue(list):
    if list:
        if list[0] == True or list[0] == False:
            return list[0]
    return None

def anyinlist(values,collection):
    return not set(values).isdisjoint(collection)
 
def value(collection):
    """if the input value is a colletion, returns its first existing value"""
    if isinstance(collection, list):        
        if len(collection) > 0:
            return collection[0]
        else:
            return None
    else:
        return collection

        
def cleanOldAttribute(fullAttributeName, attributeValue, newFullAttributeName, newAttributeValue, yesNoFullAttributeName, yesNoFullAttributeValue):   
    if not attributeValue:
        return 
    helperDataSession = helperMainLogic.dataSession
    updateDataNoNotify(newFullAttributeName, newAttributeValue)
    updateDataNoNotify(yesNoFullAttributeName, yesNoFullAttributeValue)
    updateDataNoNotify(fullAttributeName, None)        
        
        
        
def valuetodatetime(dateiso,timeiso):
    if not dateiso or not timeiso:
        return None
    dateisovalue = value(dateiso)
    timeisovalue = value(timeiso)
    if not dateisovalue or not timeisovalue:
        return None
    try:
        date = datetime.datetime.strptime(dateisovalue+' '+timeisovalue, "%Y-%m-%d %H:%M")
    except:
        return None
    return date
    
def valuestrdatetime(dateiso,timeiso=None):
    if not dateiso:
        return None
    dateisovalue = value(dateiso)
    # timeisovalue = value(timeiso)
    if not dateisovalue:
        return None
    try:
        date = datetime.datetime.strptime(dateisovalue, "%Y-%m-%d %H:%M")
    except:
        return None
    return date
def valuetodate(dateiso):
    if not dateiso:
        return None
    dateisovalue = value(dateiso)
    if not dateisovalue:
        return None
    try:
        date = datetime.datetime.strptime(dateisovalue, "%Y-%m-%d")
    except:
        return None
    return date

def nowdateiso():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def years(earlydateiso, laterdateiso=None):
    """differenza in anni tra 2 date in formato iso"""

    if isEncryptedValue(earlydateiso) or isEncryptedValue(laterdateiso):
        return None
    ed = valuetodate(earlydateiso)
    ld = datetime.datetime.now()
    if laterdateiso:
        ld = valuetodate(laterdateiso)

    if not ed or not ld:
        return None

    #switch dates if needed
    if ld < ed:
        ld, ed = ed, ld            
    
    res = ld.year - ed.year
    if res > 0:
        if ld.month < ed.month:
            res -= 1
        elif ld.month == ed.month:
            if ld.day < ed.day:
                res -= 1
    return res

 
def months(earlydateiso, laterdateiso=None):
    """differenza in mesi tra 2 date in formato iso"""
    ed = valuetodate(earlydateiso)
    ld = datetime.datetime.now()
    if laterdateiso:
        ld = valuetodate(laterdateiso)

    deltamonths = 0
    #switch dates if needed
    if ld < ed:
        ld, ed = ed, ld 
    
    res = ld.year - ed.year
    if res > 0:
        if ld.month < ed.month:
            res -= 1
        elif ld.month >= ed.month:
            if ld.day < ed.day:
                deltamonths = 1
    
    if ld.month < ed.month:
        diffmonths = ld.month + (12 - ed.month)
    else:
        diffmonths = ld.month - ed.month
    
    months = res * 12
    out = max(0, months + diffmonths - deltamonths)
    return out
    
def evalsaps2(age, HR, BP, temperature, ventilation, PaO2FiO2, urine, serum, WBC, potassium, \
              sodium, hco3, bilirubin, gcs, admissionType, pathologies, returnTuple = False  ):
    """saps2 evaluation""" 
    
    HR = value(HR)
    BP = value(BP)
    temperature = value(temperature)
    ventilation = value(ventilation)
    PaO2FiO2 = value(PaO2FiO2)
    urine = value(urine)
    serum = value(serum)
    WBC = value(WBC)
    potassium = value(potassium)
    sodium = value(sodium)
    hco3 = value(hco3)
    bilirubin = value(bilirubin)
    gcs = value(gcs)
    admissionType = value(admissionType)
    pathologies = pathologies
    
    
    todayISO = nowdateiso()
    patientYears = age
    if patientYears < 40:
        yearsComponent = 0
    elif patientYears >= 40 and patientYears < 60:
        yearsComponent = 7
    elif patientYears >= 60 and patientYears < 70:
        yearsComponent = 12
    elif patientYears >= 70 and patientYears < 75:
        yearsComponent = 15
    elif patientYears >= 75 and patientYears < 80:
        yearsComponent = 16
    elif patientYears >= 80:
        yearsComponent = 18
    else:
        raise Exception("birthdate is not valid for SAPSII calculation")
    if HR == 'core.sapsHRCodification.sapsHRMin40':
        HRComponent = 11
    elif HR == 'core.sapsHRCodification.sapsHRMin70':
        HRComponent = 2
    elif HR == 'core.sapsHRCodification.sapsHRMin120':
        HRComponent = 0
    elif HR == 'core.sapsHRCodification.sapsHRMin160':
        HRComponent = 4
    elif HR == 'core.sapsHRCodification.sapsHRMore160':
        HRComponent = 7
    else:
        raise Exception("HR is not valid for SAPSII calculation")
    #TODO: nel db etichetta sbagliata per bp=1167 da cambiare in 70-99 (e non 70-90)
    if BP == 'core.sapsSystBlPrCodification.sapsBPMin70':
        BPComponent = 13
    elif BP == 'core.sapsSystBlPrCodification.sapsBPMin90':
        BPComponent = 5
    elif BP == 'core.sapsSystBlPrCodification.sapsBPMin200':
        BPComponent = 0
    elif BP == 'core.sapsSystBlPrCodification.sapsBPMore200':
        BPComponent = 2
    else:
        raise Exception("BP is not valid for SAPSII calculation")
    if temperature == 'core.sapsTempCodification.sapsTempMin39':
        temperatureComponent = 0
    elif temperature == 'core.sapsTempCodification.sapsTempMore39':
        temperatureComponent = 3
    else:
        raise Exception("temperature is not valid for SAPSII calculation")
    #TODO: ventilation is self-calculated (see pelod ventilation)
    if ventilation == 'core.yesNoCodification.no':
        PaO2FiO2Component = 0 
    elif PaO2FiO2 == 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min400' or PaO2FiO2 == 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2More400' or PaO2FiO2 == 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min300':
        PaO2FiO2Component = 6
    elif PaO2FiO2 == 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min200':
        PaO2FiO2Component = 9
    elif PaO2FiO2 == 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min100':
        PaO2FiO2Component = 11
    else:
        raise Exception("PaO2FiO2 is not valid for SAPSII calculation")
    
    if urine == 'core.sapsSofaUrOutCodification.sapsSofaUOMin02' or  urine == 'core.sapsSofaUrOutCodification.sapsSofaUOMin040':
        urineComponent = 11
    elif urine == 'core.sapsSofaUrOutCodification.sapsSofaUOMin099':
        urineComponent = 4
    elif urine == 'core.sapsSofaUrOutCodification.sapsSofaUOMore1':
        urineComponent = 0
    else:
        raise Exception("urine value is not valid for SAPSII calculation")
    if serum == 'core.sapsSerumCodification.sapsSerumMin60':
        serumComponent = 0
    elif serum == 'core.sapsSerumCodification.sapsSerumMin180':
        serumComponent = 6
    elif serum == 'core.sapsSerumCodification.sapsSerumMore180':
        serumComponent = 10
    else:
        raise Exception("serum urea / B.U.N. value is not valid for SAPSII calculation")
    if WBC == 'core.sapsWbcCodification.sapsWbcMin1':
        WBCComponent = 12
    elif WBC == 'core.sapsWbcCodification.sapsWbcMin20':
        WBCComponent = 0
    elif WBC == 'core.sapsWbcCodification.sapsWbcMore20':
        WBCComponent = 3
    else:
        raise Exception("WBC value is not valid for SAPSII calculation")
    if potassium == 'core.sapsPotCodification.sapsPotMin3':
        potassiumComponent = 3
    elif potassium == 'core.sapsPotCodification.sapsPotMin5':
        potassiumComponent = 0
    elif potassium == 'core.sapsPotCodification.sapsPotMore5':
        potassiumComponent = 3
    else:
        raise Exception("potassium value is not valid for SAPSII calculation")
    if sodium == 'core.sapsSodCodification.sapsSodMin125':
        sodiumComponent = 5
    elif sodium == 'core.sapsSodCodification.sapsSodMin145':
        sodiumComponent = 0
    elif sodium == 'core.sapsSodCodification.sapsSodMore145':
        sodiumComponent = 1
    else:
        raise Exception("sodium value is not valid for SAPSII calculation")     
    if hco3 == 'core.sapsHco3Codification.sapsHco3Min15':
        hco3Component = 6
    elif hco3 == 'core.sapsHco3Codification.sapsHco3Min20':
        hco3Component = 3
    elif hco3 == 'core.sapsHco3Codification.sapsHco3More20':
        hco3Component = 0
    else:
        raise Exception("HCO3 value is not valid for SAPSII calculation")
    if bilirubin in ['core.sapsSofaBilirCodification.sapsSofaBilirMin1dot2', 'core.sapsSofaBilirCodification.sapsSofaBilirMin2', 'core.sapsSofaBilirCodification.sapsSofaBilirMin4']:
        bilirubinComponent =  0
    elif bilirubin == 'core.sapsSofaBilirCodification.sapsSofaBilirMin6':
        bilirubinComponent =  4
    elif bilirubin == 'core.sapsSofaBilirCodification.sapsSofaBilirMin12' or bilirubin == 'core.sapsSofaBilirCodification.sapsSofaBilirMore12' :
        bilirubinComponent = 9
    else:
        raise Exception("bilirubin value is not valid for SAPSII calculation")

    gcs = int(gcs)
    if gcs == 14 or gcs == 15:
        gcsComponent = 0
    elif gcs >= 11 and gcs <=13:
        gcsComponent = 5
    elif gcs == 9 or gcs == 10:
        gcsComponent = 7
    elif gcs >= 6 and gcs <=8:
        gcsComponent = 13
    elif gcs < 6:
        gcsComponent = 26
    else:
        raise Exception("gcs value is not valid for SAPSII calculation")
 
    if admissionType == 'core.statusCodification.nonSurgical':
        admissionTypeComponent = 6
    elif admissionType == 'core.statusCodification.emergSurgical':
        admissionTypeComponent = 8
    elif admissionType == 'core.statusCodification.electSurgical':
        admissionTypeComponent = 0
    else:
        raise Exception("admissionType value is not valid for SAPSII calculation")

    #pathologies is a list
    if 'core.comorbiditiesCodification.aids' in pathologies:
        pathologiesComponent = 17
    else:
        if 'core.comorbiditiesCodification.malignHaemDis' in pathologies:
            pathologiesComponent = 10
        else:
            if 'core.comorbiditiesCodification.metCancer' in pathologies:
                pathologiesComponent = 9
            else:
                pathologiesComponent = 0 
    if returnTuple:
        return (yearsComponent, HRComponent, BPComponent, temperatureComponent, PaO2FiO2Component, urineComponent, serumComponent, WBCComponent, \
    potassiumComponent, sodiumComponent, hco3Component, bilirubinComponent, gcsComponent, admissionTypeComponent, pathologiesComponent)
    else:
        return yearsComponent+ HRComponent+ BPComponent+ temperatureComponent+ PaO2FiO2Component+ urineComponent+ serumComponent+ WBCComponent+ \
    potassiumComponent+ sodiumComponent+ hco3Component+ bilirubinComponent+ gcsComponent+ admissionTypeComponent+ pathologiesComponent

def evalsofa(map, vasopress, pao, creat, bil, piastr, gcs, ventilation, diur):
    map = value(map)
    vasopress = value(vasopress)
    pao = value(pao)
    creat = value(creat)
    bil = value(bil)
    piastr = value(piastr)
    gcs = value(gcs)
    ventilation = value(ventilation)
    diur = value(diur)
    
    vasopressVals = ['core.sofaVasCodification.sofaDopaMin5','core.sofaVasCodification.sofaDopaMore5','core.sofaVasCodification.sofaDopaMore5EpiMore01']
    paoVals = ['core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min400', 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2More400', 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min300', 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min200', 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min100']
    creatVals = ['core.sofaCreatCodification.sofaCreatMin1dot2', 'core.sofaCreatCodification.sofaCreatMin2', 'core.sofaCreatCodification.sofaCreatMin6', 'core.sofaCreatCodification.sofaCreatMin12', 'core.sofaCreatCodification.sofaCreatMore12']
    diurVals = ['core.sapsSofaUrOutCodification.sapsSofaUOMore1', 'core.sapsSofaUrOutCodification.sapsSofaUOMin099', 'core.sapsSofaUrOutCodification.sapsSofaUOMin040','core.sapsSofaUrOutCodification.sapsSofaUOMin02']
    bilVals = ['core.sapsSofaBilirCodification.sapsSofaBilirMin1dot2','core.sapsSofaBilirCodification.sapsSofaBilirMin2','core.sapsSofaBilirCodification.sapsSofaBilirMin4','core.sapsSofaBilirCodification.sapsSofaBilirMin6','core.sapsSofaBilirCodification.sapsSofaBilirMin12','core.sapsSofaBilirCodification.sapsSofaBilirMore12']
    piastrVals = ['core.sofaPlatCodification.sofaPlatMore150','core.sofaPlatCodification.sofaPlatMin150','core.sofaPlatCodification.sofaPlatMin100','core.sofaPlatCodification.sofaPlatMin50','core.sofaPlatCodification.sofaPlatMin20']
    
    try:
        gcs = int(gcs)
        vasopress = str(vasopress)
        pao = str(pao)
        creat = str(creat)
        bil = str(bil)
        piastr = str(piastr)
        ipotensScore = 0
        paoValue = 0
        if map == 'core.sofaMAPCodification.sofaMAPLess70':
            ipotensScore = 1
        if vasopress in vasopressVals:
            vasoPressIndex = vasopressVals.index(vasopress)
            ipotensScore = vasoPressIndex+2
    
        if ventilation == 'core.yesNoCodification.no':
            if pao in ['core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min200', 'core.sapsSofaPao2Fio2Codification.sapsSofaPaO2Min100']:
                paoValue = 2
            else:
                paoValue = paoVals.index(pao)
        else:
            paoValue = paoVals.index(pao)
        
        if gcs==15:
            gcsScore=0
        elif gcs==13 or gcs==14:
            gcsScore=1
        elif gcs==10 or gcs==11 or gcs==12:
            gcsScore=2
        elif gcs==6 or gcs==7 or gcs==8 or gcs==9:
            gcsScore=3
        elif gcs<6:
            gcsScore=4
        else:
            gcsScore = None
        
        bilirubineValue = bilVals.index(bil)
        if bilirubineValue > 2:
            bilirubineValue = bilirubineValue - 1
        
        valorePiastrine = 0
        if piastr in ['core.sofaPlatCodification.sofaPlatMore150','core.sofaPlatCodification.sofaPlatMin150','core.sofaPlatCodification.sofaPlatMin100']:
            valorePiastrine = piastrVals.index(piastr)
        elif piastr in ['core.sofaPlatCodification.sofaPlatMin50']:
            valorePiastrine = 3
        elif piastr in ['core.sofaPlatCodification.sofaPlatMin20']:
            valorePiastrine = 4

        diuresisValue = diurVals.index(diur)
        if diuresisValue > 1:
            diuresisValue = diuresisValue + 1
        else:
            diuresisValue = 0
        
        sofa = ipotensScore + paoValue + max([creatVals.index(creat), diuresisValue]) + bilirubineValue + valorePiastrine + int(gcsScore)
        return sofa
    except BaseException, e:
        print e
        return None
def evalPIM2(electiveAdmission, isAdmittedPostProcedure, cardiacBypass, highRisk, lowRisk, \
                    pupils, VAM, BP, BE, FiO2, PaO2, BPValue, BEValue, FiO2Value, PaO2Value, highRiskReadonly, lowRiskReadonly, pimBPReadonly, pimVAMReadonly):
    
    
    if not pupils:
        return None
        
    VAMValue = 0
    if pimVAMReadonly:
        VAMValue = 1
    elif value(VAM) == 'core.yesNoCodification.yes':
        VAMValue = 1
    else:
        if not VAM:
            return None
    
    electiveAdmissionValue = 0
    if value(electiveAdmission) == 'core.yesNoCodification.yes':
        electiveAdmissionValue = 1
    
    isAdmittedPostProcedureValue = 0
    if value(isAdmittedPostProcedure) == 'core.yesNoCodificationPost.yes':
        isAdmittedPostProcedureValue = 1
    
    cardiacBypassValue = 0
    if value(cardiacBypass) == 'core.yesNoCodificationBypass.yes' and value(isAdmittedPostProcedure) == 'core.yesNoCodificationPost.yes':
        cardiacBypassValue = 1
    
    highRiskValue = 1
    if highRisk:
        if value(highRisk) == 'core.pimHighRiskCodification.none':
            highRiskValue = 0
    else:
        if not highRiskReadonly:
            return None
    
    lowRiskValue = 1
    if lowRisk:
        if value(lowRisk) == 'core.pimLowRiskCodification.none' or highRiskValue == 1:
            lowRiskValue = 0
    else:
        if not lowRiskReadonly:
            return None
    
    pupilsValue = 0
    if value(pupils) == 'core.pimPupilsCodification.fixed':
        pupilsValue = 1
        
    FiO2CombValue = 0
    if value(FiO2) == 'core.pimValueOrUnknownCodification.unknown':
        FiO2CombValue = 0
    elif value(FiO2) == 'core.pimValueOrUnknownCodification.value':
        if value(FiO2Value):
            FiO2CombValue = float(value(FiO2Value))
        else:
            return None
    else:
        return None
            
    PaO2CombValue = 0
    if value(PaO2) == 'core.pimValueOrUnknownCodification.unknown':
        PaO2CombValue = 100
    elif value(PaO2) == 'core.pimValueOrUnknownCodification.value':
        if value(PaO2Value):
            PaO2CombValue = float(value(PaO2Value))
        else:
            return None
    else:
        return None
        
    BECombValue = 0
    if value(BE) == 'core.pimValueOrUnknownCodification.unknown':
        BECombValue = 0
    elif value(BE) == 'core.pimValueOrUnknownCodification.value':
        #if value(BEValue):
        if value(BEValue) is not None:
            BECombValue = float(value(BEValue))
        else:
            return None
    else:
        return None

    BPCombValue = 0
    if not pimBPReadonly:
        if value(BP) == 'core.pimBPCodification.shock':
            BPCombValue = 30
        elif value(BP) == 'core.pimBPCodification.cardiacArrest':
            BPCombValue = 0
        elif value(BP) == 'core.pimBPCodification.unknown':
            BPCombValue = 120
        elif value(BP) == 'core.pimBPCodification.value':
            if value(BPValue):
                BPCombValue = float(value(BPValue))
            else:
                return None
        else:
            return None
    
    total = None
    predictedDeathRate = None
    #if BPCombValue and pupilsValue and FiO2CombValue and PaO2CombValue and BECombValue and VAMValue and electiveAdmissionValue and isAdmittedPostProcedureValue and cardiacBypassValue and highRiskValue and lowRiskValue:
    total = (0.01395 * abs(BPCombValue - 120) + (3.0791 * pupilsValue) + (0.2888 * (100 * (float(FiO2CombValue) / float(PaO2CombValue))) + (0.104 * abs(BECombValue)) + (1.3352 * VAMValue) - (0.9282 * electiveAdmissionValue) - (1.0244 * isAdmittedPostProcedureValue) + (0.7507 * cardiacBypassValue) + (1.6829 * highRiskValue) - (1.577 * lowRiskValue) - 4.8841))
    predictedDeathRate = (math.exp(total) / (1 + math.exp(total)) * 100)
    return '%.2f' % (total)

def saps2pdr(saps2):
    """saps2 predicted death rate"""
    #todo: add class and attribute to db
    saps2 = value(saps2)
    saps2 = float(saps2)
    logit = -7.7631 + 0.0737 * (saps2) + 0.9971 * math.log((saps2)+1)
    pdr = math.exp(logit) / (1 + math.exp(logit))
    return pdr
    

#pelod helpers
def pelodCardioVascular(HR, SBP, returnTuple=False):
    """pelod cardiovascular score"""
    HR = HR
    SBP = SBP
    #HR component
    if HR == 'core.pelodHRCodification.min195Below12' or HR == 'core.pelodHRCodification.min150Above12':
        hrComponent = 0
    elif HR == 'core.pelodHRCodification.more195Below12' or HR == 'core.pelodHRCodification.more150Above12':
        hrComponent = 10
    else:
        raise Exception("HR is not valid for PELOD calculation")   
    #sbp component 
    if SBP == 'core.pelodSBPCodification.more65Below1M' or SBP == 'core.pelodSBPCodification.more75Above1M' or SBP == 'core.pelodSBPCodification.more85Above1' or SBP == 'core.pelodSBPCodification.more95Above12':
        sbpComponent = 0
    elif SBP == 'core.pelodSBPCodification.min65Below1M' or SBP == 'core.pelodSBPCodification.min75Above1M' or SBP == 'core.pelodSBPCodification.min85Above1' or SBP == 'core.pelodSBPCodification.min95Above12':
        sbpComponent = 10
    elif SBP == 'core.pelodSBPCodification.min35Below1M' or SBP == 'core.pelodSBPCodification.min35Above1M' or SBP == 'core.pelodSBPCodification.min45Above1' or SBP == 'core.pelodSBPCodification.min55Above12':
        sbpComponent = 20     
    else:
        raise Exception("SBP is not valid for PELOD calculation") 
    #return single value (sum of components) or tuple
    if returnTuple:
        return (hrComponent, sbpComponent)
    else:
        return  hrComponent + sbpComponent
    
 
    #line for db
    #result = pelodCardioVascular( |1.pelodHR.value|[0], |1.pelodBP.value|[0])

def pelodPulmonary(PaO2FiO2, PaCO2, ventilation, returnTuple=False):
    """pelod pulmonary score"""
    PaO2FiO2 = PaO2FiO2
    PaCO2 = PaCO2
    ventilation = ventilation
     
    if PaO2FiO2=='core.pelodPao2Fio2Codification.pao2More70':
        PaO2FiO2Component = 0
    elif PaO2FiO2=='core.pelodPao2Fio2Codification.pao2Min70':
        PaO2FiO2Component = 10
    else:
        raise Exception("PaO2FiO2 is not valid for PELOD calculation")
        
    if PaCO2=='core.pelodPaCo2Codification.paco2Min90':
        PaCO2Component = 0
    elif PaCO2=='core.pelodPaCo2Codification.paco2More90':
        PaCO2Component = 10
    else:
        raise Exception("PaCO2 is not valid for PELOD calculation")
    
    print ventilation
    if ventilation == 'core.yesNoCodification.no':
        ventilationComponent = 0
    elif ventilation == 'core.yesNoCodification.yes':
        ventilationComponent = 1
    else:
        raise Exception("ventilation is not valid for PELOD calculation")
   
    if returnTuple:
        return (PaO2FiO2Component, PaCO2Component, ventilationComponent)
    else:
        return PaO2FiO2Component + PaCO2Component + ventilationComponent


def pelodHepatic(sgot, prothrombinTimeOrINR, returnTuple=False ):
    """pelod Hepatic score"""
    sgot = sgot
    prothrombinTimeOrINR = prothrombinTimeOrINR
    
    if sgot=='core.pelodSgotCodification.min950':
        sgotComponent = 0
    elif sgot=='core.pelodSgotCodification.more950':
        sgotComponent = 1
    else:
        raise Exception("sgot is not valid for PELOD calculation") 
    
    if prothrombinTimeOrINR=='core.pelodINRCodification.lowINR':
        prothrombinTimeOrINRComponent = 0
    elif prothrombinTimeOrINR=='core.pelodINRCodification.highINR':
        prothrombinTimeOrINRComponent = 1
    else:
        raise Exception("prothrombin Time / INR is not valid for PELOD calculation") 
    
    #return single value (sum of components) or tuple
    if returnTuple:
        return (sgotComponent, prothrombinTimeOrINRComponent)
    else:
        return  sgotComponent + prothrombinTimeOrINRComponent

def pelodNeurologic(glasgow, pupillary, returnTuple=False):
    """pelod Neurologic score"""
    glasgow = glasgow
    pupillary = pupillary
     
    #glasgow component
    intGlasgow = int(glasgow)
    if intGlasgow >= 12 and intGlasgow <= 15:
        glasgowComponent = 0
    elif intGlasgow >= 7 and intGlasgow <= 11:
        glasgowComponent = 1
    elif intGlasgow >= 4 and intGlasgow <= 6:
        glasgowComponent = 10
    elif intGlasgow == 3:
        glasgowComponent = 20
    else:
        raise Exception("glasgow is not valid for PELOD calculation")
        
    #pupillary component
    if pupillary == 'core.pelodPupilCodification.bothReact':
        pupillaryComponent = 0
    elif pupillary == 'core.pelodPupilCodification.bothFixed':
        pupillaryComponent = 10
    else:
        raise Exception("pupillary reaction is not valid for PELOD calculation")
    #return single value (sum of components) or tuple
    if returnTuple:
        return (pupillaryComponent, glasgowComponent)
    else:
        return  pupillaryComponent + glasgowComponent

def pelodHematologic(WBC, platetes, returnTuple=False):
    """pelod Hematologic score"""
    WBC = WBC
    platetes = platetes
    
    if WBC == 'core.pelodWbcCodification.wbcMore4':
        WBCComponent = 0
    elif WBC == 'core.pelodWbcCodification.wbcMin4':
        WBCComponent = 1
    elif WBC == 'core.pelodWbcCodification.wbcMin1':
        WBCComponent = 10
    else:
        raise Exception("WBC is not valid for PELOD calculation")
    
    if platetes == 'core.pelodPlateletsCodification.platMore35':
        platetesComponent = 0
    elif platetes == 'core.pelodPlateletsCodification.platMin35':
        platetesComponent = 1 
    else:
        raise Exception("platetes is not valid for PELOD calculation") 
    
    if returnTuple:
        return (WBCComponent, platetesComponent)
    else:
        return  WBCComponent + platetesComponent

def pelodRenal(creatinine):
    creatinine = creatinine
    if creatinine == 'core.pelodCreatinineCodification.creatMin140' or creatinine == 'core.pelodCreatinineCodification.creatMin55' or creatinine == 'core.pelodCreatinineCodification.creatMin100'  or creatinine == 'core.pelodCreatinineCodification.creatMin140Above12':
        creatinineComponent = 0
    elif creatinine == 'core.pelodCreatinineCodification.creatMore140' or creatinine == 'core.pelodCreatinineCodification.creatMore55' or creatinine == 'core.pelodCreatinineCodification.creatMore100' or creatinine == 'core.pelodCreatinineCodification.creatMore140Above12' :
        creatinineComponent = 10
    else:
        raise Exception("creatinine is not valid for PELOD calculation")
    
    return creatinineComponent

def pelodScore(pelodPulmonary,pelodCardiovascular,pelodHepatic,pelodNeurologic, pelodHematologic,pelodRenal ):
    pelodPulmonary = pelodPulmonary
    pelodCardiovascular = pelodCardiovascular
    pelodHepatic = pelodHepatic
    pelodNeurologic = pelodNeurologic
    pelodHematologic = pelodHematologic
    pelodRenal = pelodRenal
    """pelod total score"""
    return int(pelodPulmonary)+int(pelodCardiovascular)+int(pelodHepatic)+int(pelodNeurologic)+int(pelodHematologic)+int(pelodRenal)
    
    #riga per db
    #result = pelodScore(|1.pelodPulScore.value|[0],|1.pelodCardScore.value|[0],|1.pelodHepScore.value|[0],|1.pelodNeuroScore.value|[0], |1.pelodHemaScore.value|[0],|1.pelodRenalScore.value|[0])

def pelodPDR(pelodScore):
    pelodScore = value(pelodScore)
    """PELOD predicted death rate"""
    pelodScore = float(pelodScore)
    logit =  -7.64 + 0.30*(pelodScore)
    pdr =  1 / (1 + math.exp(-logit))
    return pdr
    
def days(earlydateiso, laterdateiso):
    """differenza in giorni  tra 2 date in formato iso. Il risultato e' valido solo per valori inferiori and un mese"""
    ed = valuetodate(earlydateiso)
    ld = datetime.datetime.now()
    if laterdateiso:
        ld = valuetodate(laterdateiso)
    deltamonths = 0
    #switch dates if needed
    if ld < ed:
        ld, ed = ed, ld            
    return (ld - ed).days
    #res = ld.year - ed.year
    #if res > 0:
    #    if ld.month < ed.month:
    #        res -= 1
    #    elif ld.month == ed.month:
    #        if ld.day < ed.day:
    #            deltamonths = 1
    #months = res * 12
    #months =  months + max(0, ld.month - ed.month) - deltamonths
    #out = max(0, ld.day - ed.day) + months * 30
    #return out

def weeks(earlydateiso, laterdateiso):
    return days(earlydateiso,laterdateiso) / 7
 
def isEncryptedValue(value):
    from mainlogic import _
    if value == _("ENCRYPTED"):
        return True
    return False
    
def getCentreCode():
    return str(helperMainLogic.getCentreCode())
        
def validHour(hourstring):
    hourstring = value(hourstring)
    pieces = hourstring.split(':')
    if len(pieces) != 2:
        return False
    else:
        try:
            hours = int (pieces[0])
            mins = int (pieces[1])
        except:
            return False
        if hours > 23 or hours < 0:
            return False
        if mins > 59 or mins < 0:
            return False
        return True

def validNumber(astring):
    astring = value(astring)
    try:
        f = float(astring)
        return True
    except:
        return False

def forceSave():
    helperMainLogic.notificationCenter.postNotification('NeedSaveWithBusyInfo',helperMainLogic)
    
def shouldCompileGcpLog():
    if helperMainLogic.getGcpChangedAttributes(removeFirstSave=True):
        return True
    return False
    
        
def randomBlocksRandomization(indexAttributeName, indexInBlockAttributeName, randomizationResultAttributeName, randomizationResultStudy, randomizationResultControl, blockType="", allowedBlocksSizes = [4, 6]):

    randomizationResult = None

    randomizationIndexes = helperMainLogic.jsonStore.load_values(None, 'crfs.' + indexAttributeName)
    randomizationIndexesByIndex = dict((x, y) for x, y in randomizationIndexes.iteritems() if blockType in y)
    randomizationIndexesByIndex = dict((int(y.replace(blockType, '')), x) for x, y in randomizationIndexesByIndex.iteritems())
    maxIndex = -1
    idOfMax = None
    for id, index in randomizationIndexes.iteritems():
        try:
            if not blockType or index[0] != blockType:
                continue
            if blockType:
                if int(index[1:]) > maxIndex:
                    maxIndex = int(index[1:])
                    idOfMax = id
            else:
                if int(index) > maxIndex:
                    maxIndex = int(index)
                    idOfMax = id
        except:
            print "ERROR: Trying to convert string '" + index + "' to integer when recovering informations for the randomization of a patient"
            pass
    
    newIndex = maxIndex + 1  
    
    indexInBlock = None
    if idOfMax != None :
        try:
            stringIndexInBlock = helperMainLogic.jsonStore.load_value(idOfMax, 'crfs.' + indexInBlockAttributeName)
            indexInBlock = int(stringIndexInBlock)
        except:
            print "ERROR: Trying to convert string '" + str(stringIndexInBlock) + "' to integer when recovering informations for the randomization of a patient"
            pass
    if indexInBlock <= 1 or indexInBlock == None or idOfMax == None :
        newIndexInBlock = random.choice(allowedBlocksSizes)
        randomizationResult = random.choice([True, False])
    else:
        newIndexInBlock = indexInBlock - 1
        currentIndex = maxIndex
        studyCount = 0
        controlCount = 0
        lastIndexInBlock = 0
        endOfBlock = False
        while currentIndex >= 0 and not endOfBlock:
            
            try:
                currentId = randomizationIndexesByIndex[currentIndex]
            except KeyError:
                currentIndex -= 1
                continue
            
            try:
                stringCurrentIndexInBlock = helperMainLogic.jsonStore.load_value(currentId, 'crfs.' + indexInBlockAttributeName)
                currentIndexInBlock = int(stringCurrentIndexInBlock)
            except:
                print "ERROR: Trying to convert string '" + str(stringIndexInBlock) + "' to integer when recovering informations for the randomization of a patient"
                continue

            if currentIndexInBlock <= 0 :
                endOfBlock = True
                continue
            else:
                currentValue = helperMainLogic.jsonStore.load_value(currentId, 'crfs.' + randomizationResultAttributeName)
                if currentValue == randomizationResultStudy :
                    studyCount += 1
                elif currentValue == randomizationResultControl :
                    controlCount += 1
                else: 
                    print "ERROR: patient with jsonID " + str(currentId) + " has an incorrect randomization value (" + str(currentValue) + ") in FLAT table"
            
            lastIndexInBlock = currentIndexInBlock  
            currentIndex -= 1
        
        if lastIndexInBlock not in allowedBlocksSizes :
            print "ERROR: found a randomization block with size (" + str(lastIndexInBlock) + ") not compatible with allowed sizes (" + str(allowedBlocksSizes) + ")"
               
        if controlCount >= lastIndexInBlock / 2 :
            randomizationResult = True
        elif studyCount >= lastIndexInBlock / 2 :
            randomizationResult = False
        else:
            randomizationResult = random.choice([True, False])
    
    updateDataNoNotify(indexAttributeName, blockType + str(newIndex))
    updateDataNoNotify(indexInBlockAttributeName, newIndexInBlock)
        
    return randomizationResult


def confirmBox(confirmtext):
    import wx
    dlg = wx.MessageDialog(None, confirmtext, '', wx.YES_NO | wx.ICON_QUESTION)
    dlg.Center()
    result = dlg.ShowModal()
    if result == wx.ID_YES:
        return True
    else:
        return False
    
try:
    from helpers import *
except BaseException, e:
    print "HELPER IMPORT EXCEPTION", e


if __name__ == '__main__':
    print months ('2009-01-10', '2009-10-10')
    print months ('2011-03-11', '2010-01-12')
    print days ('2011-02-28', '2011-03-01')
    print valuetodatetime('2011-02-28','10:10')
    print valuetodatetime('2011-03-04','10:10')
    print (valuetodatetime('2011-04-01','10:10') - valuetodatetime('2011-02-28','10:10')).days

