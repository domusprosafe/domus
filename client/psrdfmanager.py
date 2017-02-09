import rdflib
from rdflib import Namespace, BNode
import datetime


class PSRDFManager(object):
    
    def __init__(self,namespacesSource='namespaces.txt', rdfOutputFile='', multipleFile = False):
        self.multipleFile = multipleFile
        
        if not self.multipleFile:
            self.rdfOutputFile = rdfOutputFile + datetime.datetime.now().isoformat().replace(':','') + '.rdf'
        else:
            self.rdfOutputFile = rdfOutputFile + '%s' + datetime.datetime.now().isoformat().replace(':','') + '.rdf'
        self.namespacesSource = namespacesSource
        self.readNamespaces()
    
    def readNamespaces(self):
        #should we read namespaces from external source?
        return 
        
    def admissionToRDF(self, admissionData, admissionKey,toFile=False):
        PROSAFE = Namespace("http://giviti.marionegri.it/knowledgebase/prosafe-core#")
        CRF4 = Namespace("http://giviti.marionegri.it/knowledgebase/prosafe-core4#")
        CRF3 = Namespace("http://giviti.marionegri.it/knowledgebase/prosafe-core3#")
        CRF2 = Namespace("http://giviti.marionegri.it/knowledgebase/prosafe-core2#")
        CRF1 = Namespace("http://giviti.marionegri.it/knowledgebase/prosafe-core1#")
        mappingGraph = rdflib.Graph()
        mappingGraph.namespace_manager.bind("prosafe-core4", CRF4)
        mappingGraph.namespace_manager.bind("prosafe-core3", CRF3)
        mappingGraph.namespace_manager.bind("prosafe-core2", CRF2)
        mappingGraph.namespace_manager.bind("prosafe-core1", CRF1)
        mappingGraph.namespace_manager.bind("prosafe-core", PROSAFE)
        mappingGraph.commit()
        for key, value in admissionData[admissionKey].iteritems():
            if type(value) == type([]):
                for element in value:
                    element = str(element)
                    if len(element.split('#')[-1].replace('__', '.').split('.')) == 3:
                        rdfValue = rdflib.term.URIRef(element)
                    else:
                        rdfValue = rdflib.term.Literal(element)
                    mappingGraph.add((PROSAFE[admissionKey], rdflib.term.URIRef(key), rdfValue))
                continue
            
            if type(value) == type({}):
                #TODO (FIXME): ugly, took for granted that dynamic classes have their ids in the list below
                knownIds = ['surgicalId', 'nonSurgicalId', 'procedureId']
                for object in value:
                    #object now is an object of a prosafe container
                    listId = ''
                    for element in value[object].keys():
                       listIdList = [el for el in knownIds if el in element]
                       if listIdList:
                            listId = element
                            break
                    
                    BNODE = rdflib.term.BNode()
                    mappingGraph.add((PROSAFE[admissionKey], rdflib.term.URIRef(listId), BNODE))
                    for element in value[object].keys():
                        if (type(value[object][element]) == str or type(value[object][element]) == unicode) and len(str(value[object][element]).split('#')[-1].replace('__', '.').split('.')) == 3:
                            rdfValue = rdflib.term.URIRef(value[object][element])
                        else:
                            rdfValue = rdflib.term.Literal(value[object][element])                        
                        mappingGraph.add((BNODE, rdflib.term.URIRef(element), rdfValue))
                continue
            value = str(value)
            if len(value.split('#')[-1].replace('__', '.').split('.')) == 3:
                rdfValue = rdflib.term.URIRef(value)
            else:
                try:
                    rdfValue = rdflib.term.Literal(value.replace("\n", ""))
                except BaseException, e:
                    print e
                    continue
            
            mappingGraph.add((PROSAFE[admissionKey], rdflib.term.URIRef(key), rdfValue))
        mappingGraph.commit()
        serializedGraph = mappingGraph.serialize(format='turtle')
        if self.multipleFile:
            self.rdfOutputFile = self.rdfOutputFile % admissionKey
        if toFile:
            f = open(self.rdfOutputFile,'a')
            f.write(str(serializedGraph))
            f.close()
        return mappingGraph

    def RDFToAdmission(self, RDF, fromFile=False):
        from psconstants import appName
        emptyGraph = rdflib.Graph()
        data = RDF
        if fromFile:
            data = emptyGraph.parse(file=open(RDF, 'rb'), format="n3")
        
        attrrdict = {}
        progressiveObjectCode = 1
        for subj, pred, obj in data:
            if str(pred) == '':
                continue
            if type(subj) == rdflib.term.BNode:
                continue
            rdfAdmissionKey = emptyGraph.resource(subj).qname()
            admissionKey = rdfAdmissionKey.split(':')[1]
            rdfAdmissionKeyName = emptyGraph.resource(pred).qname()
            admissionKeyName = rdfAdmissionKeyName.split(':')[1]
            if type(obj) == rdflib.term.Literal:
                admissionValue = "" + obj                
            elif type(obj) == rdflib.term.BNode:
                for subj2, pred2, obj2 in emptyGraph.triples((obj, None, None)):
                    predValue2 = emptyGraph.resource(pred2).qname().split(':')[1]
                    admissionKeyName = predValue2
                    if type(obj2) == rdflib.term.Literal:
                        #objValue2 = obj2.format()
                        objValue2 = "" + obj2
                    else:
                        objValue2 = emptyGraph.resource(obj2).qname().split(':')[1]
                    try:
                        crfName, className, attributeName = admissionKeyName.replace('__', '.').split('.')
                    except BaseException, e:
                        print e, admissionKeyName
                        
                        
                    admissionDict['externalKey'] = admissionKey
                    admissionDict['crfName'] = crfName
                    admissionDict['className'] = className
                    admissionDict['attributeName'] = attributeName
                    admissionDict['value'] = objValue2
                    admissionDict['objectCode'] = progressiveObjectCode
                    if admissionKey not in attrrdict:
                        attrrdict[admissionKey] = []
                    attrrdict[admissionKey].append(admissionDict)
                    
                progressiveObjectCode += 1
                    
                continue
            else:
                rdfAdmissionValue = emptyGraph.resource(obj).qname()
                admissionValue = rdfAdmissionValue.split(':')[1]

            admissionDict = {}
            try:
                crfName, className, attributeName = admissionKeyName.replace('__', '.').split('.')
            except BaseException, e:
                print e
            admissionDict['externalKey'] = admissionKey
            admissionDict['crfName'] = crfName
            admissionDict['className'] = className
            admissionDict['attributeName'] = attributeName
            if '#' in admissionValue:
                admissionValue = admissionValue.split('#')[1]
            admissionDict['value'] = admissionValue.replace('__', '.')
            
            if admissionKey not in attrrdict:
                attrrdict[admissionKey] = []
            attrrdict[admissionKey].append(admissionDict)
        
        return attrrdict
        