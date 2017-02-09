

class DataConfiguration(object):

    def __init__(self):
        self.initialize()

        self.indexedClassProperties = ['visible','enabled','requiredForStatus','timeStamp','indexed', 'includeInGCP']
        self.indexedCodingSetValueProperties = ['visible','enabled','excludes','groupName','dynclass','dynattribute','dynmaxoccurrences']

    def initialize(self):
        self.crfs = dict()
        self.errors = dict()
        self.classesByProperty = dict()
        self.codingSetValuesByProperty = dict()
        self.personalizations = dict()

    def splitClassName(self,name):
        splitName = name.split('.')
        if len(splitName) != 2:
            return None
        return splitName

    def splitAttributeName(self,name):
        splitName = name.split('.')
        if len(splitName) != 3:
            return None
        return splitName

    def splitCodingSetName(self,name):
        splitName = name.split('.')
        if len(splitName) != 2:
            return None
        return splitName

    def splitCodingSetValueName(self,name):
        splitName = name.split('.')
        if len(splitName) != 3:
            return None
        return splitName

    def joinClassName(self,crfName,className):
        return '.'.join((crfName,className))

    def joinAttributeName(self,crfName,className,attributeName):
        return '.'.join((crfName,className,attributeName))

    def joinCodingSetName(self,crfName,codingSetName):
        return '.'.join((crfName,codingSetName))

    def joinCodingSetValueName(self,crfName,codingSetName,codingSetValueName):
        return '.'.join((crfName,codingSetName,codingSetValueName))

    def getCrfNames(self):
        return self.crfs.keys()

    def getClassNamesForCrf(self,crfName):
        try:
            return self.crfs[crfName]['classes'].keys()
        except:
            return None

    def getAttributeNamesForClass(self,crfName,className):
        try:
            return self.crfs[crfName]['classes'][className]['attributes'].keys()
        except:
            return None

    def getSortedAttributeNamesForClass(self,crfName,className):
        try:
            attributeNames = self.crfs[crfName]['classes'][className]['attributes'].keys()
            decoratedAttributeNames = [(self.getPropertyForAttribute(crfName,className,attributeName,'positionWeight'),attributeName) for attributeName in attributeNames]
            decoratedAttributeNames.sort()
            return [decoratedAttributeName[1] for decoratedAttributeName in decoratedAttributeNames]
        except:
            return None

    def getPropertiesForCrf(self,crfName):
        try:
            return self.crfs[crfName]['properties'].keys()
        except:
            return None

    def getPropertiesForClass(self,crfName,className):
        try:
            return self.crfs[crfName]['classes'][className]['properties'].keys()
        except:
            return None

    def getPropertiesForAttribute(self,crfName,className,attributeName):
        try:
            return self.crfs[crfName]['classes'][className]['attributes'][attributeName]['properties'].keys()
        except:
            return None

    def getCodingSetsForCrf(self,crfName):
        try:
            return self.crfs[crfName]['codingSets'].keys()
        except:
            return None

    def getCodingSetValueNamesForCodingSet(self,crfName,codingSetName):
        try:
            return self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'].keys()
        except:
            return None

    def getPropertiesForCodingSet(self,crfName,codingSetName):
        try:
            return self.crfs[crfName]['codingSets'][codingSetName]['properties'].keys()
        except:
            return None

    def getPropertiesForCodingSetValue(self,crfName,codingSetName,codingSetValueName):
        try:
            return self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'][codingSetValueName]['properties'].keys()
        except:
            return None

    def getPropertyForCrf(self,crfName,propertyName):
        try:
            return self.crfs[crfName]['properties'][propertyName]
        except:
            return None

    def getPropertyForClass(self,crfName,className,propertyName):
        try:
            return self.crfs[crfName]['classes'][className]['properties'][propertyName]
        except:
            return None

    def getPropertyForAttribute(self,crfName,className,attributeName,propertyName):
        try:
            return self.crfs[crfName]['classes'][className]['attributes'][attributeName]['properties'][propertyName]
        except:
            return None

    def getPropertyForCodingSet(self,crfName,codingSetName,propertyName):
        try:
            return self.crfs[crfName]['codingSets'][codingSetName]['properties'][propertyName]
        except:
            return None

    def getPropertyForCodingSetValue(self,crfName,codingSetName,codingSetValueName,propertyName):
        try:
            return self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'][codingSetValueName]['properties'][propertyName]
        except:
            return None

    def getClassesByProperty(self,crfName,propertyName):
        try:
            return self.classesByProperty[crfName][propertyName]
        except:
            return None

    def getClassesByPropertyWithValue(self,crfName,propertyName,propertyValue):
        try:
            return [className for className in self.classesByProperty[crfName][propertyName] if self.getPropertyForClass(crfName,className,propertyName) == propertyValue]
        except:
            return None

    def getCodingSetValuesByProperty(self,crfName,propertyName):
        try:
            return self.codingSetValuesByProperty[crfName][propertyName]
        except:
            return None

    def getErrorIdsForCrf(self,crfName):
        try:
            return self.crfs[crfName]['errors']
        except:
            return None

    def getErrorInfoForId(self,crfName,errorId):
        try:
            return self.crfs[crfName]['errors'][errorId]
        except:
            return None
 
    def getExpressionNamesForCrf(self,crfName):
        try:
            return self.crfs[crfName]['expressions']
        except:
            return None

    def getExpressionInfoForName(self,crfName,expressionName):
        try:
            return self.crfs[crfName]['expressions'][expressionName]
        except:
            return None
        
    def classesFromXml(self,crfName,classesEl):
        self.crfs[crfName]['classes'] = dict()
        self.classesByProperty[crfName] = dict()
        for classEl in classesEl:
            self.addClass(crfName,classEl)
            #if classEl.tag != 'class':
            #    continue
            #className = classEl.get('name')
            #self.crfs[crfName]['classes'][className] = {'properties':dict(),'attributes':dict()}
            #for key in classEl.keys():
            #    self.crfs[crfName]['classes'][className]['properties'][key] = classEl.get(key)
            #    if key in self.indexedClassProperties:
            #        if key not in self.classesByProperty[crfName]:
            #            self.classesByProperty[crfName][key] = []
            #        self.classesByProperty[crfName][key].append(className)
            #for attributeEl in classEl:
            #    self.addAttribute(crfName,className,attributeEl)
            #    if attributeEl.tag != 'attribute':
            #        continue
            #    attributeName = attributeEl.get('name')
            #    self.crfs[crfName]['classes'][className]['attributes'][attributeName] = {'properties':dict()}
            #    for key in attributeEl.keys():
            #        self.crfs[crfName]['classes'][className]['attributes'][attributeName]['properties'][key] = attributeEl.get(key)

    def addClass(self,crfName,classEl):
        if classEl.tag != 'class':
            return
        className = classEl.get('name')
        self.crfs[crfName]['classes'][className] = {'properties':dict(),'attributes':dict()}
        for key in classEl.keys():
            self.crfs[crfName]['classes'][className]['properties'][key] = classEl.get(key)
            if key in self.indexedClassProperties:
                if key not in self.classesByProperty[crfName]:
                    self.classesByProperty[crfName][key] = []
                self.classesByProperty[crfName][key].append(className)
        for attributeEl in classEl:
            self.addAttribute(crfName,className,attributeEl)
 
    def addAttribute(self,crfName,className,attributeEl):
        if attributeEl.tag != 'attribute':
            return
        attributeName = attributeEl.get('name')
        self.crfs[crfName]['classes'][className]['attributes'][attributeName] = {'properties':dict()}
        for key in attributeEl.keys():
            self.crfs[crfName]['classes'][className]['attributes'][attributeName]['properties'][key] = attributeEl.get(key)

    def codingSetsFromXml(self,crfName,codingSetsEl):
        self.crfs[crfName]['codingSets'] = dict()
        self.codingSetValuesByProperty[crfName] = dict()
        for codingSetEl in codingSetsEl:
            if codingSetEl.tag != 'codingSet':
                continue
            codingSetName = codingSetEl.get('name')
            self.crfs[crfName]['codingSets'][codingSetName] = {'properties':dict(),'codingSetValues':dict()}
            if codingSetEl.get('customizable'):
                self.crfs[crfName]['codingSets'][codingSetName]['properties']['customizable'] = '1'
            if codingSetEl.get('customizableGroup'):
                self.crfs[crfName]['codingSets'][codingSetName]['properties']['customizableGroup'] = codingSetEl.get('customizableGroup')
            if codingSetEl.get('label'):
                self.crfs[crfName]['codingSets'][codingSetName]['properties']['label'] = codingSetEl.get('label')
            for codingSetValueEl in codingSetEl:
                self.addCodingSetValue(crfName,codingSetName,codingSetValueEl)
#                if codingSetValueEl.tag != 'codingSetValue':
#                    continue
#                codingSetValueName = codingSetValueEl.get('name')
#                self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'][codingSetValueName] = {'properties':dict()}
#                for key in codingSetValueEl.keys():
#                    self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'][codingSetValueName]['properties'][key] = codingSetValueEl.get(key)
#                    if key in self.indexedCodingSetValueProperties:
#                        if key not in self.codingSetValuesByProperty[crfName]:
#                            self.codingSetValuesByProperty[crfName][key] = []
#                        self.codingSetValuesByProperty[crfName][key].append(self.joinCodingSetValueName(crfName,codingSetName,codingSetValueName))

    def addCodingSetValue(self,crfName,codingSetName,codingSetValueEl):
        codingSetValueName = codingSetValueEl.get('name')
        self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'][codingSetValueName] = {'properties':dict()}
        for key in codingSetValueEl.keys():
            self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'][codingSetValueName]['properties'][key] = codingSetValueEl.get(key)
            if key in self.indexedCodingSetValueProperties:
                if key not in self.codingSetValuesByProperty[crfName]:
                    self.codingSetValuesByProperty[crfName][key] = []
                self.codingSetValuesByProperty[crfName][key].append(self.joinCodingSetValueName(crfName,codingSetName,codingSetValueName))

    def addErrorToCrf(self,crfName,errorId,error,originCrfName):
        self.crfs[crfName]['errors'][errorId] = error
        self.crfs[crfName]['errors'][errorId]['originCrfName'] = originCrfName

    def errorsFromXml(self,crfName,errorsEl):
        self.crfs[crfName]['errors'] = dict()
        for errorEl in errorsEl:
            if errorEl.tag != 'error':
                continue
            id = errorEl.get('id')
            self.crfs[crfName]['errors'][id] = dict()
            for key in errorEl.keys():
                self.crfs[crfName]['errors'][id][key] = errorEl.get(key)

    def expressionsFromXml(self,crfName,expressionsEl):
        self.crfs[crfName]['expressions'] = dict()
        for expressionEl in expressionsEl:
            if expressionEl.tag != 'expression':
                continue
            name = expressionEl.get('name')
            self.crfs[crfName]['expressions'][name] = dict()
            for key in expressionEl.keys():
                self.crfs[crfName]['expressions'][name][key] = expressionEl.get(key)

    def crfFromXml(self,crfEl):
        crfName = crfEl.get('name')
        self.crfs[crfName] = dict()
        self.crfs[crfName]['properties'] = dict()
        for key in crfEl.keys():
            self.crfs[crfName]['properties'][key] = crfEl.get(key)
        for el in crfEl:
            if el.tag == 'classes':
                self.classesFromXml(crfName,el)
            if el.tag == 'codingSets':
                self.codingSetsFromXml(crfName,el)
            if el.tag == 'errors':
                self.errorsFromXml(crfName,el)
            if el.tag == 'expressions':
                self.expressionsFromXml(crfName,el)

    def readCrfConfiguration(self,path):
        from xml.etree import cElementTree as etree
        f = open(path,"r")
        xmlString = f.read()
        f.close()
        from psxml2xml import psXMLToXML
        xmlString = psXMLToXML(xmlString)
        xmlDocument = etree.fromstring(xmlString)
        if xmlDocument.tag == 'crf':
            self.crfFromXml(xmlDocument)
        else:
            for el in xmlDocument:
                if el.tag == 'crf':
                    self.crfFromXml(el)

    #def mergePersonalizations(self,personalizationString):
    #    personalizationString = """
    #        <personalizations>
    #          <crf name="core">
    #            <classes>
    #              <class name="gender">
    #                <attribute description="Patient gender 2" dataType="codingset" codingSet="core.sexCodification" name="value" label="Ciccio" />
    #              </class>
    #            </classes>
    #            <codingSets>
    #              <codingSet name="sexCodification">
    #                <codingSetValue description="X" positionWeight="0" value="Ciccio" name="ciccio"/>
    #              </codingSet>
    #            </codingSets>
    #          </crf>
    #        </personalizations>
    #    """
    #    from xml.etree import cElementTree as etree
    #    xmlDocument = etree.fromstring(personalizationString)
    #    # For now personalizations can only attach a new attribute to a class or a new codingSetValue to a codingSet
    #    # TODO: how to show a new attribute?
    #    # TODO: the new coding set value could cause issues if it's removed or modified at a later stage. Should we add it as 
    #    if xmlDocument.tag != 'personalizations':
    #        return
    #    for crfEl in xmlDocument:
    #        if crfEl.tag != 'crf':
    #            continue
    #        crfName = crfEl.get("name")
    #        for typeEl in crfEl:
    #            if typeEl.tag == 'classes':
    #                for classEl in typeEl:
    #                    className = classEl.get("name")
    #                    for attributeEl in classEl:
    #                        self.addAttribute(crfName,className,attributeEl)
    #            elif typeEl.tag == 'codingSets':
    #                for codingSetEl in typeEl:
    #                    codingSetName = codingSetEl.get("name")
    #                    for codingSetValueEl in codingSetEl:
    #                        self.addCodingSetValue(crfName,codingSetName,codingSetValueEl)

    def addPersonalizedAttribute(self,attributeEl):
        from xml.etree import cElementTree as etree
        attributeElString = etree.tostring(attributeEl)
        attributeFullName = attributeEl.get("name")
        crfName, className, attributeName = self.splitAttributeName(attributeFullName)
        attributeEl.set("name",attributeName)

        try:
            self.addAttribute(crfName,className,attributeEl)
            if 'attributes' not in self.personalizations.keys():
                self.personalizations['attributes'] = dict()
            self.personalizations['attributes'][attributeFullName] = attributeElString
        except BaseException, e:
            PsLogger().warning(['DataConfigurationTag','ExceptionTag'], str(e))
            print 'error while adding personalized attribute', str(e)
            pass

    def addPersonalizedCodingSetValue(self,codingSetValueEl):
        from xml.etree import cElementTree as etree
        codingSetValueElString = etree.tostring(codingSetValueEl)
        codingSetValueFullName = codingSetValueEl.get("name")
        #print codingSetValueFullName
        crfName, codingSetName, codingSetValueName = self.splitCodingSetValueName(codingSetValueFullName)
        codingSetValueEl.set("name",codingSetValueName)

        try:
            self.addCodingSetValue(crfName,codingSetName,codingSetValueEl)
            if 'codingSetValues' not in self.personalizations.keys():
                self.personalizations['codingSetValues'] = dict()
            self.personalizations['codingSetValues'][codingSetValueFullName] = codingSetValueElString
        except BaseException, e:
            PsLogger().warning(['DataConfigurationTag','ExceptionTag'], str(e))
            print 'error while adding personalized coding set value', str(e)
            pass

    def addPersonalizationClassToCrf(self,crfName):
        personalizationClass = """
            <class dataStorage="admission" name="personalizations">
              <attribute dataType="string" name="attributes" multiInstance="1"/>
              <attribute dataType="string" name="codingSetValues" multiInstance="1"/>
            </class>
        """
        return
        from xml.etree import cElementTree as etree
        classEl = etree.fromstring(personalizationClass)
        self.addClass(crfName, classEl)

    def mergePersonalizations(self,personalizations):
        samplePersonalizationString = """
            <personalizations>
              <attribute description="X" dataType="float" name="value" value="core.firstName.firstName"/>
              <codingSetValue description="X" positionWeight="0" value="Ciccio" name="core.sexCodification.ciccio"/>
            </personalizations>
        """
        self.personalizations = {'attributes':{}, 'codingSetValues':{}}
        from xml.etree import cElementTree as etree
        if type(personalizations) == str:
            personalizationsEl = etree.fromstring(personalizationString)
            for typeEl in personalizationsEl:
                if typeEl.tag == 'attribute':
                    self.addPersonalizedAttribute(typeEl)
                elif typeEl.tag == 'codingSetValue':
                    self.addPersonalizedCodingSetValue(typeEl)
        elif type(personalizations) == list:
            for typeString in personalizations:
                typeEl = etree.fromstring(typeString)
                if typeEl.tag == 'attribute':
                    self.addPersonalizedAttribute(typeEl)
                elif typeEl.tag == 'codingSetValue':
                    self.addPersonalizedCodingSetValue(typeEl)
        elif type(personalizations) == type(etree.Element('')):
            for typeEl in personalizations:
                if typeEl.tag == 'attribute':
                    self.addPersonalizedAttribute(typeEl)
                elif typeEl.tag == 'codingSetValue':
                    self.addPersonalizedCodingSetValue(typeEl)
        #print 'PERSONALIZATIONS', self.personalizations

    def removePersonalizations(self):
        if 'attributes' in self.personalizations:
            for attributeFullName in self.personalizations['attributes']:
                #print 'PERSONALIZATIONS', attributeFullName
                crfName, className, attributeName = self.splitAttributeName(attributeFullName)
                #properties = self.getPropertiesForAttribute(crfName,className,attributeName)
                #for key in properties:
                #    self.attributesByProperty[crfName][key].remove(attributeFullName)
                self.crfs[crfName]['classes'][className]['attributes'].pop(attributeName)

        if 'codingSetValues' in self.personalizations:
            for codingSetValueFullName in self.personalizations['codingSetValues']:
                #print 'PERSONALIZATIONS', codingSetValueFullName
                crfName, codingSetName, codingSetValueName = self.splitCodingSetValueName(codingSetValueFullName)
                properties = self.getPropertiesForCodingSetValue(crfName,codingSetName,codingSetValueName)
                if properties:
                    for key in properties:
                        if key not in self.codingSetValuesByProperty[crfName].keys():
                            continue
                        self.codingSetValuesByProperty[crfName][key].remove(codingSetValueFullName)
                self.crfs[crfName]['codingSets'][codingSetName]['codingSetValues'].pop(codingSetValueName)

    def getAttributePersonalizations(self):
        if 'attributes' in self.personalizations:
            return self.personalizations['attributes'].values()
        return None

    def getCodingSetValuePersonalizations(self):
        if 'codingSetValues' in self.personalizations:
            return self.personalizations['codingSetValues'].values()
        return None

