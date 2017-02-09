import sys
sys.path.append("../")

import urllib2
import urllib
import psconstants
import xml.etree.ElementTree as etree

    
        
def checkActivationCode(centreCode, activationKey):
    request = urllib2.Request(psconstants.CHECK_ACTIVATION_CODE_URL)
    data = urllib.urlencode({'centreCode' : centreCode, 'activationKey': activationKey})
    try:
        xml =  urllib2.urlopen(request, data).read()      
    except:
        #offline
        raise Exception('Activation Service Offline')
    if '<CheckActivationKeyResult>true</CheckActivationKeyResult>' in xml:
        return centreCode
    else:
        return False
    
def checkPetals(centreCode):
    request = urllib2.Request(psconstants.CHECK_PETALS_URL)
    data = urllib.urlencode({'centreCode' : centreCode})
    try:
        xml =  urllib2.urlopen(request, data).read()      
    except:
        raise Exception('Petals Service Offline')

    tree = etree.fromstring(xml)
    resultElement = tree.find('*//{' + psconstants.CENTRES_SERVICES_NAMESPACE + '}GetPetalsResult')

    if not resultElement:
        raise Exception('Petals Service Error: no element ' + psconstants.CENTRES_SERVICES_NAMESPACE + 'GetPetalsResult')
    childs = resultElement.getchildren()
    if not childs:
        raise Exception('Petals Service Error: no children in GetPetalsResult')
    centrePetals = childs[0]
    if not centrePetals or centrePetals.tag != 'CentrePetals':
        raise Exception('Petals Service Error: no CentrePetals child in GetPetalsResult')

    petals = []
    for petal in centrePetals.findall('Petal'):
        newPetal = dict()
        newPetal['name'] = petal.get('CodeName')
        newPetal['description'] = petal.get('Description')
        startDate = petal.find('StartDate')        
        if startDate is not None:
            newPetal['startDate'] = petalDateToISO(startDate.text)
        endDate = petal.find('EndDate')
        if endDate is not None:
            newPetal['endDate'] = petalDateToISO(endDate.text)
        petals.append(newPetal)
    
    return petals
            
def petalDateToISO(datestring):
    try:
        day = datestring[:2]
        month = datestring[2:4]
        year = datestring[4:]
        return "%s-%s-%s" % (day, month, year)
    except:
        return datestring
   


if __name__ == '__main__':
    print checkActivationCode('IT113', '846438fd6d124142a2dc2ff4b0195822')

