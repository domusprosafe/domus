from xlrd import open_workbook
from xlutils.copy import copy
import xlwt
import math
import re

def emptyIfZero(value):
    if value == 0:
        return ''
    return value


class DescriptiveTableCreator(object):
    def __init__(self, excelmodel, targetpath, data, metadata):
        self.excelmodel = excelmodel
        self.targetpath = targetpath
        self.data = data        
        self.metadata = metadata
        self.keysToNotRound = []
        self.keysToNotEvaluate = []
    def mergeDicts(self, dictList, basekeyName):
        out = dict()
        for di in dictList:
            
            for bkey in di:
                key = bkey.split(":")[1]
                nkey = basekeyName + ":" + key
                if nkey in out:
                    out[nkey] += di[bkey]
                else:
                    out[nkey] = di[bkey]
        
        return out
    
    
    def computeSortedItems(self, inDict, basekeyName='', excludedInSort=[]):
        
        if basekeyName != '' and not basekeyName.endswith(':'):
            basekeyName += ':'
                
        occurredItems = []
        keys = inDict.keys()
        for key in keys:
            if (key.find("__") == -1 and key not in excludedInSort) or key in [basekeyName+'__none__',basekeyName+'__any__', basekeyName+'__missing__', basekeyName+'__none_or_missing__']:
                if key.find("__") == -1:
                    occurredItems.append((inDict[key],key))
                    #print "calculate perc", key
                    try:
                        inDict[key+".__frac__"] = float(inDict[key])/float(inDict[basekeyName+"__len__"] - inDict[basekeyName+"__none_or_missing__"])

                        inDict[key+".__perc__"] = inDict[key+".__frac__"] * 100
                
                    except Exception, e:
                        print "perc error", key, str(e)
        
        #sorting occurences
        occurredItems.sort()
        occurredItems.reverse()
                
        counter = 0
        for x in range(len(occurredItems)):
            
            valueNamePieces = occurredItems[x][1].split(':')
            valueName = valueNamePieces[1]
            if valueName in excludedInSort:
                continue
            inDict[basekeyName+"__sorted__[%d]" % counter] = "'%s'" % valueName
            if valueName in self.metadata:
                try:
                    translated = self.metadata[valueName]['translatedValue']
                    #print "trans", translated
                except:
                    translated = ''
                inDict[basekeyName+"__sorted__[%d].__translated__" % counter] = "\"%s\"" % translated
            
            
            inDict[basekeyName+"__sorted__[%d].__num__" % counter] = occurredItems[x][0]
            try:
                inDict[basekeyName+"__sorted__[%d].__frac__" % counter] = float(occurredItems[x][0]) / (inDict[basekeyName+'__len__'] - inDict[basekeyName+'__none_or_missing__'])
                inDict[basekeyName+"__sorted__[%d].__perc__" % counter] = inDict[basekeyName+"__sorted__[%d].__frac__" % counter] * 100
            except:
                pass
                
            counter += 1
        
        return inDict
    
    def computeOccurrencesForKey(self, key, basekeyName='', excludedInSort=[], restrictedTo=[]):
        
        if basekeyName != '':
            basekeyName += ':'
            excludedInSort = [basekeyName +x for x in excludedInSort]

        out = dict()        
        out[basekeyName+'__none__'] = 0
        out[basekeyName+'__missing__'] = 0
        out[basekeyName+'__len__'] = len(self.data)
        out[basekeyName+'__any__'] = 0
        
        items = []
        for x in self.data:
            try:    
                items.append(x[key])
            except Exception, e:
                #print e
                pass

        if len(restrictedTo):
            items = [x for x in items if x is not None]
            items = [x for x in items if(list(set(x) & set(restrictedTo))) ]
        
        out[basekeyName+'__missing__'] =  out[basekeyName+'__len__'] - len(items)
       
        for item in items:
            if item is None or not len(item):
                out[basekeyName+'__none__'] +=1
            else:
                out[basekeyName+'__any__'] +=1
                noRepetitionsItem = list(set(item))
#                for value in item:
                for value in noRepetitionsItem:
                    if basekeyName+value not in out:
                        out[basekeyName+value] = 0
                    out[basekeyName+value] += 1

        out[basekeyName+'__none_or_missing__'] = out[basekeyName+'__none__'] + out[basekeyName+'__missing__']

        out[basekeyName+'__none__.__frac__'] = float(out[basekeyName+'__none__']) / out[basekeyName+'__len__']
        out[basekeyName+'__none__.__perc__'] = out[basekeyName+'__none__.__frac__']   * 100 


        out[basekeyName+'__any__.__frac__'] = float(out[basekeyName+'__any__']) / out[basekeyName+'__len__']
        out[basekeyName+'__any__.__perc__'] = out[basekeyName+'__any__.__frac__']   * 100 

        out[basekeyName+'__missing__.__frac__'] = float(out[basekeyName+'__missing__']) / out[basekeyName+'__len__']
        out[basekeyName+'__missing__.__perc__'] = out[basekeyName+'__missing__.__frac__']   * 100 

        out[basekeyName+'__none_or_missing__.__frac__'] = float(out[basekeyName+'__none_or_missing__']) / out[basekeyName+'__len__']
        out[basekeyName+'__none_or_missing__.__perc__'] = out[basekeyName+'__none_or_missing__.__frac__']   * 100 

        out = self.computeSortedItems(out, basekeyName=basekeyName, excludedInSort=excludedInSort)

        return out
        
        
    def countValuesForKeys(self, basekeyName, keys = [], values=[]):
        out = dict()

        count = 0

        for x in self.data:
            found = True        
            for key in keys:
                try:
                    v = x[key]
                    #print v, key
                    if type(v) == type(list()):
                        if v[0] not in values:
                            found = False
                            continue
                    else:
                        if v not in values:
                            found = False
                            continue
                except:
                    #print "xxx", key
                    found = False
            if found:
               count += 1    
                    
        out[basekeyName] = count
        return out


    def computeMathStatsForKey(self, key, basekeyName='', lambdas = {}, excludedInPerc = []):
        
        #print "computeMathStat", key        
        out = dict()
        if basekeyName != '':
            basekeyName += ':'

        items = []
        noneCount = 0
        missingCount = 0
        for x in self.data:
            try:            
                value = x[key]
                if value is None:
                    noneCount += 1                
                else:
                    item = value[0]
                    items.append(item)
        
            except:
                missingCount += 1
        


        out[basekeyName+'__missing__'] = missingCount 
        out[basekeyName+'__none__'] = noneCount
        out[basekeyName+'__items__'] = []

        temp = []        
        for item in items:
            try:
                v = float(item)                
                temp.append(v)
                out[basekeyName+'__items__'].append(v)
                for lam in lambdas:
                    if basekeyName+lam not in out:
                        out[basekeyName+lam] = 0
                    if lambdas[lam](v):
                        out[basekeyName+lam] += 1
                
            except:
                out[basekeyName+'__missing__'] += 1

        out[basekeyName+'__none_or_missing__'] = out[basekeyName+'__missing__'] + out[basekeyName+'__none__']
        out[basekeyName+'__any__'] = len(self.data) - out[basekeyName+'__none_or_missing__']

        #getting number of records to exclude in percentages
        excludedCount = 0
        for key in excludedInPerc:
            try:
                keyCount = out[basekeyName+lam]
                excludedCount += keyCount    
            except:
                pass

        for lam in lambdas:
            out[basekeyName+lam+".__frac__"] = float(out[basekeyName+lam]) / (len(self.data) - out[basekeyName+'__none_or_missing__'] - excludedCount)
            out[basekeyName+lam+".__perc__"] = out[basekeyName+lam+".__frac__"] * 100
        
        if len(temp):
            out[basekeyName+'min'] = min(temp)
            out[basekeyName+'max']= max(temp)
            out[basekeyName+'average'] = sum(temp) / len(temp)
            try:
                out[basekeyName+'median'] = self.median(temp)
            except:
                pass
            try:
                out[basekeyName+'std'] = self.std(temp)
            except:
                pass
            out[basekeyName+'sum'] = sum(temp)

        else:
            out[basekeyName+'sum'] = 0
            
        return out
            
    #median function
    def median(self, vector):
        a = sorted(vector)
        l = len(a)
        if l % 2 == 0:
            position1 = int(l/2)-1
            position2 = int(l/2)
            out = (a[position1] + a[position2]) /2
        else:
            position = int(l/2)
            out = a[position]
        return out
        
    #standard deviation function
    def std(self, vector):
        l = len(vector)
        mean = sum(vector) / l
        tmp = 0
        for item in vector:
            tmp += math.pow(item-mean,2)
        out = math.sqrt(tmp/l)
        return out
        

    def computeStats(self):
        out = dict()

        #number of patients
        out['numPatients'] = len(self.data)


        proceduresKeys = []
        for key in self.metadata.keys():
            if key.startswith('core.exportProcedures.'):
                proceduresKeys.append(key)

        noProceduresStats = self.countValuesForKeys('noProcedures', proceduresKeys, ['core.yesNoCodification.no']);
        out.update(noProceduresStats)

        # Calculating missing procedures
        noProceduresStats = dict()
        count = 0
        for x in self.data :
            found = False
            for key in proceduresKeys:
                try:
                    v = x[key]
                    found = True
                    break
                except:
                    continue
            if not found:
               count += 1
        
        noProceduresStats['missingProcedures'] = count
        #noProceduresStats = self.countValuesForKeys('missingProcedures', proceduresKeys, [None]);
        out.update(noProceduresStats)

        procedureStats = {}
        proceduresCounts = dict()
        for procedureKey in proceduresKeys:
            procedureStat = self.computeOccurrencesForKey(procedureKey,procedureKey, restrictedTo=['core.yesNoCodification.yes'])
            out.update(procedureStat)
            proceduresCounts[procedureKey] = procedureStat
           
        #determining top procedures
        proceduresToSort = []
        for procedureKey in proceduresKeys:
            try:
                countKey = procedureKey + ':core.yesNoCodification.yes'
                value = proceduresCounts[procedureKey][countKey]
                percKey = procedureKey + ':__any__.__perc__'
                perc = proceduresCounts[procedureKey][percKey]

                procedureItem = (value, procedureKey, perc)
                proceduresToSort.append(procedureItem)
            except:
                pass
                #print "noKey:" , procedureKey
    
        proceduresToSort.sort()
        proceduresToSort.reverse()

        #grouping procedures by occurence
        proceduresToSortByOccurrence = dict()

        for g in proceduresToSort:
            occurrences = g[0]
            if occurrences not in proceduresToSortByOccurrence:
                proceduresToSortByOccurrence[occurrences] = []
            proceduresToSortByOccurrence[occurrences].append(g)

        occurrencesKeys = proceduresToSortByOccurrence.keys()
        occurrencesKeys.sort()
        occurrencesKeys.reverse()

        groupedProceduresToSort = []
        for occurrencesKey in occurrencesKeys:
            occ = occurrencesKey
            procList = proceduresToSortByOccurrence[occurrencesKey]
            procNames = []
            for proc in procList:
                procNames.append(proc[1])
            procPerc = procList[0][2]
            groupedProcedure = (occ, procNames, procPerc)
            groupedProceduresToSort.append(groupedProcedure)

        """        
        print "####"        
        print groupedProceduresToSort
        print "####"        
        print
        """    
        
        """
        print "*******"        
        for o in proceduresToSortByOccurrence:
            print o, proceduresToSortByOccurrence[o]
        """

        """
        for i,p in enumerate(proceduresToSort[:10]):
            keyName = p[1]
            procedureStats['topProcedures[' + str(i) + ']'] = keyName
            procedureStats['topProcedures[' + str(i) + '].__num__'] = p[0]
            procedureStats['topProcedures[' + str(i) + '].__perc__'] = p[2]
            procedureStats['topProcedures[' + str(i) + '].__translated__'] = self.metadata[keyName]['translatedValue']
        """
        for i,p in enumerate(groupedProceduresToSort[:10]):
            keyName = "\n".join(p[1])
            translations = ",".join([self.metadata[xx]['translatedValue'] for xx in p[1]])
            procedureStats['topProcedures[' + str(i) + ']'] = keyName
            procedureStats['topProcedures[' + str(i) + '].__num__'] = p[0]
            procedureStats['topProcedures[' + str(i) + '].__perc__'] = p[2]
            procedureStats['topProcedures[' + str(i) + '].__translated__'] = translations
        """
        print "---------"
        print procedureStats
        """

        out.update(procedureStats)
        
        #gender statistics
        stats = self.computeOccurrencesForKey('core.genderClear.value','gender', restrictedTo=['core.sexCodification.Male','core.sexCodification.Female'])
        out.update(stats)

        #age statistics for pediatric/non pediatric
        ageLambdas = dict()
        ageLambdas['pediatric'] = lambda x: x < 17;
        ageLambdas['adult'] = lambda x: x >= 17
        ageStats = self.computeMathStatsForKey('core.exportAge.years','patientPediatric', ageLambdas)
        out.update(ageStats)

        out['numPatientsPediatric'] = out['patientPediatric:pediatric']
        out['numPatientsAdult'] = out['patientPediatric:adult']


        #age statistics
        ageLambdas = dict()
        ageLambdas['less2'] = lambda x: x < 2;
        ageLambdas['2to4'] = lambda x: x >= 2 and x <= 4
        ageLambdas['5to10'] = lambda x: x >= 5 and x <= 10
        ageLambdas['11to16'] = lambda x: x >= 11 and x <= 16
        ageLambdas['17to45'] = lambda x: x >= 17 and x <= 45
        ageLambdas['46to65'] = lambda x: x >= 46 and x <= 65
        ageLambdas['66to75'] = lambda x: x >= 66 and x <= 75
        ageLambdas['more75'] = lambda x: x > 75
        ageStats = self.computeMathStatsForKey('core.exportAge.years','age', ageLambdas)
        out.update(ageStats)

        
        #admSource (same hospital/other ospital)        
        ostats = self.computeOccurrencesForKey('core.admSource.value','admSource',restrictedTo=['core.sourceTypeCodification.otherHospital','core.sourceTypeCodification.sameHospital'])
        out.update(ostats)        

        #admWard
        ostats = self.computeOccurrencesForKey('core.admWard.value','admWard')
        out.update(ostats)

        #comorbities TODO:FIXME
        ostats = self.computeOccurrencesForKey('core.comorbidities.value','comorbidities', excludedInSort=['core.comorbiditiesCodification.none'])
        out.update(ostats)       


        #trauma
        ostats = self.computeOccurrencesForKey('core.typeTrauma.value','typeTrauma')
        out.update(ostats)
        
        #Surgical status at admission (N,%)
        ostats = self.computeOccurrencesForKey('core.typeStatus.value','typeStatus', restrictedTo=      ['core.statusCodification.electSurgicalPed','core.statusCodification.electSurgical','core.statusCodification.emergSurgical','core.statusCodification.nonSurgical'])
        out.update(ostats)
        
        #Top 5 surgical interventions at admisison (N,%)
        #Non-surgical interventions at admission (N,%)
        #Non-surgical interventions at admission (N,%)
        ostats = self.computeOccurrencesForKey('core.typeNonSurgical.value','typeNonSurgical', restrictedTo=['core.nonSurgProcCodification.electNonSurgProc','core.nonSurgProcCodification.electNonSurgProcPed','core.nonSurgProcCodification.emergNonSurgProc','core.nonSurgProcCodification.noNonSurgProc','core.surgIntervCodification.none'])
        out.update(ostats)

        #surgery
        surgStayStats = self.computeOccurrencesForKey('core.exportSurgeryDetails.surgDuringStay','surgDuringStay', excludedInSort=['core.surgIntervCodification.missing', 'core.surgIntervCodification.none'])
        out.update(surgStayStats)
        
        surgAdmStats = self.computeOccurrencesForKey('core.exportSurgeryDetails.surgOnAdm','surgOnAdm', excludedInSort=['core.surgIntervCodification.missing', 'core.surgIntervCodification.none'])
        out.update(surgAdmStats)
        
        surgAllStats = self.mergeDicts([surgStayStats, surgAdmStats], 'surgAll')
        
        #surgAllStats = surgStayStats
        #surgAllStats.update(surgAdmStats)
        
        surgAllSortedStats = self.computeSortedItems(surgAllStats, 'surgAll', excludedInSort=['core.surgIntervCodification.none','core.surgIntervCodification.missing'])
        out.update(surgAllSortedStats)
        
        #Reason for admission (N,%)
        ostats = self.computeOccurrencesForKey('core.admReas.value','admReas')
        out.update(ostats)

        #Failures at admission (N,%)
        #Failures at admission (N,%)(alone or in combination)
        ostats = self.computeOccurrencesForKey('core.exportFailures.admFailures', 'admFailures')
        out.update(ostats)

        #Top 5 conditions on admission (N,%)
        ostats = self.computeOccurrencesForKey('core.clinicalCondAdm.value', 'clinicalCondAdm')
        out.update(ostats)

        #infected/not infected
        ostats = self.computeOccurrencesForKey('core.exportCondAdm.infections','infectionsYesNo')
        out.update(ostats)


        #infected/not infected during the stay
        ostats = self.computeOccurrencesForKey('core.exportCondDuringStay.infectionsStay','infectionsStayYesNo', restrictedTo=['core.yesNoCodification.no','core.yesNoCodification.yes'])
        out.update(ostats)


        #Top 5 infections at admission (N,%)
        ostats = self.computeOccurrencesForKey('core.infections.value','infections')
        out.update(ostats)

        ###########second column in excel file
        #Top 5 trauma (N,%)
        ostats = self.computeOccurrencesForKey('core.traumaCondAdm.value','traumaCondAdm')
        out.update(ostats)

        #Failures during the stay (N,%)
        #Failures during the stay (N,%)(alone or in combination)
        ostats = self.computeOccurrencesForKey('core.exportFailures.stayFailures','stayFailures')
        out.update(ostats)

        #Top 5 complications during the stay (N,%)
        ostats = self.computeOccurrencesForKey('core.icuDiseases.value','icuDiseases', excludedInSort=['core.complCodification.noCompl'])
        out.update(ostats)

        #Top 5 infections during the stay (N,%)

        ostats = self.computeOccurrencesForKey('core.icuInfections.value','icuInfections')
        out.update(ostats)

        #Incidence rates        
#        ostats = self.computeMathStatsForKey('core.vapExposure.value','vapExposure')
        ostats = self.computeMathStatsForKey('core.vapExposure.value','vapExposure')
        out.update(ostats)
     
        ostats = self.computeMathStatsForKey('core.catheterExposure.value','catheterExposure')
        out.update(ostats)
        
        ostats = self.computeOccurrencesForKey('core.vap.value','vap')
        out.update(ostats)


        #Maximum severity of infection (N,%)
        ostats = self.computeOccurrencesForKey('core.icuSevInfections.value','icuSevInfections', restrictedTo=['core.severInfectCodification.noSirs','core.severInfectCodification.sevSepsis','core.severInfectCodification.sepShock'])
        out.update(ostats)
        
        #GCS (worst within first 24 hrs)
        stats = self.computeMathStatsForKey('core.exportGcs.gcs24','gcs24')
        out.update(stats)

        #icu stay days
        stats = self.computeMathStatsForKey('core.exportAdditionalPatientData.icuStayDays','icuStayDays')
        out.update(stats)        
        
        stats = self.computeMathStatsForKey('core.exportAdditionalPatientData.icuAfter','icuAfter')
        out.update(stats)
        
        
        stats = self.computeMathStatsForKey('core.sofaTotal.value','sofa')
        out.update(stats)
        
        stats = self.computeMathStatsForKey('core.sapsTotal.value','saps')
        out.update(stats)
        
        stats = self.computeMathStatsForKey('core.pimTotal.value','pim')
        out.update(stats)
        
        stats = self.computeMathStatsForKey('core.pelodScoreTotal.value','pelod')
        out.update(stats)
        

        
        ostats = self.computeOccurrencesForKey('core.exportSurgeryDetails.nonSurgDuringStay','nonSurgDuringStay', excludedInSort=['core.nonSurgIntervCodification.none','core.nonSurgIntervCodification.missing'])
        out.update(ostats)
        
        ostats = self.computeOccurrencesForKey('core.exportSurgeryDetails.nonSurgOnAdm','nonSurgOnAdm', excludedInSort=['core.nonSurgIntervCodification.none','core.nonSurgIntervCodification.missing','core.surgIntervCodification.none','core.surgIntervCodification.missing'])
        out.update(ostats)
        
        ostats = self.computeOccurrencesForKey('core.icuOutcome.value','icuOutcome')
        out.update(ostats)
   
        ostats = self.computeOccurrencesForKey('core.exportHospOutcome.value','hospOutcome', restrictedTo=['core.hospOutCodification.alive', 'core.hospOutCodification.hospDead'])
        out.update(ostats)
        
        ostats = self.computeOccurrencesForKey('core.icuFailures.value','icuFailures')
        out.update(ostats)

        #calculating exposures ratios
        try:
            #out['vapRatio'] = str(out['vap:core.yesNoCodification.yes']) + '/' + str(int(out['vapExposure:sum']))
            out['vapRatio'] = float(out['vap:core.yesNoCodification.yes'])  / float(out['vapExposure:sum']) * 1000

        except:
            out['vapRatio'] = '-'

        self.keysToNotRound.append('vapRatio');
        #self.keysToNotEvaluate.append('vapRatio');


        try:
            #out['catheterRatio'] = str(out['icuInfections:core.infectCodification.cathetBact']) +  ' / ' + str(int(out['catheterExposure:sum']))
            out['catheterRatio'] = float(out['icuInfections:core.infectCodification.cathetBact'])  /  float(out['catheterExposure:sum']) * 1000
        except:
            out['catheterRatio'] = '-'

        self.keysToNotRound.append('catheterRatio');
#        self.keysToNotEvaluate.append('catheterRatio');
               
        """
        print "*" * 30
        keys= sorted(out.keys())
        for key in keys:
            pass
            try :
                v=out[key].encode('ascii','ignore')
            except:
                v = out[key]
            print key, v
        print "*" * 30
        """
        return out
        
    def run(self):
        
        rawstr = r"""##[\w|\:|\[|\].]*\##"""
        self.varre = re.compile(rawstr, re.IGNORECASE)
        
        stats = self.computeStats()
        
        source =  open_workbook(self.excelmodel,formatting_info = True)
        destination = copy(source)
        
        srcsheet = source.sheets()[0]
        datasheet = destination.get_sheet(0)
        for i in range(srcsheet.nrows ):

            row = datasheet.row(i) 
            
            for j in range(srcsheet.ncols):
                cellvalue = str(srcsheet.cell_value(i,j).encode('ascii','ignore'))
                evaluateCell =True
                
                if cellvalue.find("##") > -1:
                    expression = cellvalue
                    vars = self.varre.finditer(cellvalue)
                    for var in vars:
                        var = str(var.group())
                        #print "var:", var
                        key = var.replace("##","")
                        if key in self.keysToNotEvaluate:
                            evaluateCell = False
                        #print "key:", key
                        try:
                            value = stats[key]
                            if key not in self.keysToNotRound:
                                try:
                                    value = round(value, 1)
                                except:
                                    pass
                            #print "val", value
                        except:
                            if "__sorted__" in key and not ("__num__" in key or "__perc__" in key):
                                value = ''
                            else:
                                value = 0                        
                            #print "no key " + key
                        
                        try:
                            value = value.encode('ascii','ignore')
                        except:
                            pass
                        expression = expression.replace(var, str(value))
                    

                    oldCell = row._Row__cells[j];
                   
                    if not evaluateCell:
                        datasheet.write(i,j,str(expression))
                    else:
                        try:
                            datasheet.write(i,j,eval(expression))
                        except Exception,e:
                            #print "expression error in excel output:",expression
                            datasheet.write(i,j,str(expression))

                    #preserving old format
                    newCell = row._Row__cells[j];
                    newCell.xf_idx = oldCell.xf_idx
                    
        destination.save(self.targetpath)
        
        return True
