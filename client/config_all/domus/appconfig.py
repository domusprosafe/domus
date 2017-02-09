from psconstants import dateToPretty, prettyToDate
import os

appName = 'domus'
toolBarApplications = ['export']

coreCrfName = 'domus'
try:
    import esky
    import sys
    eskyApp = esky.Esky(sys.executable)            
    imagesPath = eskyApp.get_abspath("images")
    configMasterPath = eskyApp.get_abspath("config_master")
    isFrozen = True
except:
    imagesPath = "images"
    configMasterPath = "config_master"
    isFrozen = False

splashFile = os.path.join(configMasterPath,"logosinpe.png")

firstNameAttr =     'domus.name.firstName'
lastNameAttr =      'domus.name.lastName'
sexAttr =           'domus.sex.sex'
birthDateAttr =     'domus.birthDate.birthDate'
admissionDateAttr = 'domus.admissionDate.admissionDate'
ageAttr =           'domus.age.age'

gridColumnAttributes = ('domus.admissionDate.admissionDate','domus.name.lastName','domus.name.firstName','domus.birthDate.birthDate')

gridColumnLabels = ('Admission date', 'Last Name', 'First Name', 'Date of birth')

def rowTextToData(rowText):
    out = rowText.copy()
    out['admissionKey'] = rowText.get('admissionKey',None)
    out['admissionDate'] = prettyToDate(rowText.get('domus.admissionDate.admissionDate',None))
    out['birth'] = prettyToDate(rowText.get('domus.birthDate.birthDate',None))
    return out

def rowDataToText(rowData):
    out = rowData.copy()
    out['domus.admissionDate.admissionDate'] = dateToPretty(rowData.get('domus.admissionDate.admissionDate',None))
    out['domus.birthDate.birthDate'] = dateToPretty(rowData.get('domus.birthDate.birthDate',None))
    return out

dischargeLetterNotesPageName = '@@@61007@@@'

gridDataAttributes = ['domus.admissionDate.admissionDate','domus.name.lastName','domus.name.firstName','domus.birthDate.birthDate','domus.sex.sex']

patientGridDataAttributes = ['domus.name.lastName','domus.name.firstName','domus.birthDate.birthDate','domus.sex.sex']



attrDataTypes = { firstNameAttr:    'string', 
                  lastNameAttr:     'string', 
                  sexAttr:          'codingset', 
                  birthDateAttr:    'datetime', 
                  admissionDateAttr:'datetime' } 

attrNameDict = { firstNameAttr:    'firstName', 
                 lastNameAttr:     'lastName', 
                 sexAttr:          'sex',
                 birthDateAttr:    'birthDate', 
                 admissionDateAttr:'admissionDate' }

classNameList = ['name', 
                 'sex',
                 'birthDate', 
                 'admissionDate']

attrExternalKeys = { firstNameAttr:    'patient', 
                     lastNameAttr:     'patient', 
                     sexAttr:          'patient', 
                     birthDateAttr:    'patient', 
                     admissionDateAttr:'admission' } 

attrCodingSets = { firstNameAttr:    None, 
                   lastNameAttr:     None, 
                   sexAttr:          'domus.sexCodification', 
                   birthDateAttr:    None, 
                   admissionDateAttr:None }

basedataAttributeDict = { 'firstName':    firstNameAttr, 
                          'lastName':     lastNameAttr, 
                          'sex':          sexAttr, 
                          'birthDate':    birthDateAttr, 
                          'admissionDate':admissionDateAttr }

sexCodingSetValues = { 'domus.sexCodification.male':  'Maschio', 
                       'domus.sexCodification.female':'Femmina' }

gridColumnList = ['admissionKey',
                  'admissionDate',
                  'lastName',
                  'firstName',
                  'birthDate',
                  'statusValue']

gridColumnDict = {'admissionKey': 'Admission code',
                  'admissionDate':'Admission date',
                  'lastName':     'Last Name',
                  'firstName':    'First Name',
                  'birthDate':    'Date of birth',
                  'statusValue':  'Status' }

gridColumnTypes = {'admissionDate':'datetime',
                   'lastName':     'string',
                   'firstName':    'string',
                   'birthDate':    'datetime' }

filterList = ['admissionDate',
              'firstName',
              'lastName',
              'birthDate' ]

filterDict = {'admissionDate':'Admission date',
              'lastName':     'Last Name',
              'firstName':    'First Name',
              'birthDate':    'Date of birth' }

age = "|%s|[0], |%s|[0]" % (admissionDateAttr, birthDateAttr)

DB_SYNCH_URL_HSTORE = 'custom_webservice.url'
DB_MERGE_URL = 'custom_webservice.url'
CONNECTION_CHECK_URL = 'custom_webservice.url'
DIFFPATCH_URL = 'custom_webservice.url'
ESKY_FILES_DOWNLOAD_URL = 'custom_webservice.url'

CHECK_ACTIVATION_CODE_URL = 'custom_webservice.url'
CHECK_PETALS_URL = 'custom_webservice.url'
SERVER_QUERY_URL = 'custom_webservice.url'
SECONDARY_PASSWORD_URL = 'custom_webservice.url'


PYRO_PORT = 7866
PYRO_NS_PORT = 9190
PYRO_NS_BC_PORT = 9190

