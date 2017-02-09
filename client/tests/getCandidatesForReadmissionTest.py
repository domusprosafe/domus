import unittest

import sys
sys.path.append('..')
sys.path.append('../gui')
sys.path.append('../locale')
sys.path.append('../utils')
sys.path.append('../dlls')
sys.path.append('../master')
sys.path.append('../master/jsonstore')
sys.path.append('../config_master')

import mainlogic
import psconstants as psc
import copy

class GetCandidatesForReadmissionTestCase(unittest.TestCase):
    
    basedata = {}
    candidate = {}
    icuDeadPatient = {}
    hospDeadPatient = {}
    myMainLogic = None
    
    def __init__(self, methodName='runTest'):
        
        unittest.TestCase.__init__(self, methodName)
    
        self.basedata['lastName'] = "Lastname"
        self.basedata['firstName'] = "Firstname"
        self.basedata['birthDate'] = "1940-10-10"
        self.basedata['admissionDate'] = "2012-02-12"
        self.basedata['sex'] = "F"
        
        self.candidate[psc.lastNameAttr] = "Lastname"
        self.candidate[psc.firstNameAttr] = "Firstname"
        self.candidate[psc.birthDateAttr] = "1940-10-10"
        self.candidate[psc.sexAttr] = "F"
        self.candidate['core.icuOutcome.value'] = 'core.icuOutCodification.alive' # 'core.icuOutCodification.dead'
        self.candidate['core.icuAdmDate.icuAdmDate'] = "2011-15-03"
        self.candidate['core.icuDisDate.value'] = "2011-15-09"
        self.candidate['core.hospOutcome.value'] = 'core.hospOutCodification.hospAlive' # 'core.hospOutCodification.hospDead'
        self.candidate['core.hospAdmDate.value'] = "2011-15-03"
        self.candidate['core.hospDisDate.value'] = "2011-15-09"
        self.candidate['core.hospOutcomeIT.value'] = 'core.hospOutCodificationIT.hospAlive' # 'core.hospOutCodificationIT.hospDead'
        
        self.icuDeadPatient = copy.deepcopy(self.candidate)
        self.icuDeadPatient['core.icuOutcome.value'] = 'core.icuOutCodification.dead'
        
        self.hospDeadPatient = copy.deepcopy(self.candidate)
        self.hospDeadPatient['core.hospOutcome.value'] = 'core.hospOutCodification.hospDead'
        
        self.hospITDeadPatient = copy.deepcopy(self.candidate)
        self.hospITDeadPatient['core.hospOutcomeIT.value'] = 'core.hospOutCodificationIT.hospDead'
        
        self.stillInICUPatient = copy.deepcopy(self.candidate)
        self.stillInICUPatient['core.icuOutcome.value'] = None
        self.stillInICUPatient['core.icuDisDate.value'] = None
        self.stillInICUPatient['core.hospOutcome.value'] = None
        self.stillInICUPatient['core.hospDisDate.value'] = None
        self.stillInICUPatient['core.hospOutcomeIT.value'] = None
        
        self.admittedPreviousThanDismissionPatient = copy.deepcopy(self.candidate)
        self.admittedPreviousThanDismissionPatient['core.icuDisDate.value']  = '2012-02-13'
        
        self.admittedPreviousThanAdmissionPatient = copy.deepcopy(self.candidate)
        self.admittedPreviousThanAdmissionPatient['core.icuAdmDate.icuAdmDate']  = '2012-02-13'
        
        self.admittedPreviousThanHospAdmissionPatient = copy.deepcopy(self.candidate)
        self.admittedPreviousThanHospAdmissionPatient['core.hospAdmDate.value'] = '2012-02-13'
        
        self.withoutHospAdmDatePatient = copy.deepcopy(self.candidate)
        self.withoutHospAdmDatePatient['core.hospAdmDate.value'] = None
        
        self.withoutICUAdmDatePatient = copy.deepcopy(self.candidate)
        self.withoutICUAdmDatePatient['core.icuAdmDate.icuAdmDate'] = None
        
        self.differentSexPatient = copy.deepcopy(self.candidate)
        self.differentSexPatient[psc.sexAttr] = "M"
        
        self.withoutSexPatient = copy.deepcopy(self.candidate)
        self.withoutSexPatient[psc.sexAttr] = None
        
        self.strangeCaseNamePatient = copy.deepcopy(self.candidate)
        self.strangeCaseNamePatient[psc.lastNameAttr] = "LaStNaMe"
        self.strangeCaseNamePatient[psc.firstNameAttr] = "fIrStNaMe"
        
        self.differentFirstNamePatient = copy.deepcopy(self.candidate)
        self.differentFirstNamePatient[psc.firstNameAttr] = "Pluto"
        
        self.differentLastNamePatient = copy.deepcopy(self.candidate)
        self.differentLastNamePatient[psc.lastNameAttr] = "Pippo"
        
        self.differentBirthDatePatient = copy.deepcopy(self.candidate)
        self.differentBirthDatePatient[psc.birthDateAttr] = "1940-10-11"
        
    def setUp(self):
        reload(mainlogic)
        self.myMainLogic = mainlogic.MainLogic({'testing':False,'localhost':True,'nosynch':True,'createmasterfile':False})
        
    def testNoCandidatesOnEmptyList(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(candidates, [])
        
    def testCandidateFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.candidate]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 1)
    
    def testIcuDeadCandidateNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.icuDeadPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
        
    def testHospDeadCandidateNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.hospDeadPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
    
    def testHospITDeadCandidateNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.hospITDeadPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
        
    def testStillInICUCandidateNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.stillInICUPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
        
    def testCandidatesWithIncompatibleDatesNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.admittedPreviousThanDismissionPatient, self.admittedPreviousThanAdmissionPatient, self.admittedPreviousThanHospAdmissionPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
    
    def testCandidateWithoutHospAdmDateFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.withoutHospAdmDatePatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 1)
    
    def testCandidateWithoutICUAdmDateFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.withoutICUAdmDatePatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 1)
    
    def testCandidateWithDifferentSexNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.differentSexPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
    
    def testCandidateWithoutSexFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.withoutSexPatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 1)
    
    def testCandidateWithStrangeCaseNameFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.strangeCaseNamePatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 1)
    
    def testCandidatesWithDifferentNamesNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.differentFirstNamePatient, self.differentLastNamePatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
    
    def testCandidateWithDifferentBirthDateNotFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[self.differentBirthDatePatient]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 0)
    
    def testRightCandidatesFound(self) :
        self.myMainLogic.getAllActiveAdmissionsData = lambda:[
            self.differentBirthDatePatient, self.differentFirstNamePatient,
            self.differentLastNamePatient, self.strangeCaseNamePatient,
            self.withoutSexPatient, self.differentSexPatient,
            self.withoutICUAdmDatePatient, self.withoutHospAdmDatePatient,
            self.admittedPreviousThanDismissionPatient,
            self.admittedPreviousThanAdmissionPatient,
            self.admittedPreviousThanHospAdmissionPatient,
            self.stillInICUPatient, self.hospITDeadPatient,
            self.hospDeadPatient, self.icuDeadPatient, self.candidate
        ]
        
        candidates, ignored = self.myMainLogic.getCandidatesForReadmission(self.basedata)
        self.assertEqual(len(candidates), 5)
        assert(self.candidate in candidates)
        assert(self.withoutICUAdmDatePatient in candidates)
        assert(self.withoutHospAdmDatePatient in candidates)
        assert(self.withoutSexPatient in candidates)
        assert(self.strangeCaseNamePatient in candidates)
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
