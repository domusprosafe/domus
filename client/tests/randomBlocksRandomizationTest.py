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

import psconstants as psc
import copy
import psevaluator
import random

#exec("globals()['helperMainLogic'] = None")

class myMainLogic(object):
    def __init__(self):
        self.jsonStore = jsonStore()
    
class jsonStore(object):
    def __init__(self):
        pass
    
    def load_values(self):
        pass
        
class randomBlocksRandomizationTestCase(unittest.TestCase):
    
    indexAttributeName = 'indexAttributeName'
    indexInBlockAttributeName = 'indexInBlockAttributeName'
    randomizationResultAttributeName = 'randomizationResultAttributeName'
    randomizationResultStudy = 'randomizationResultStudy'
    randomizationResultControl = 'randomizationResultControl'
    firstBlockType = 'A'
    secondBlockType = 'B'
    resultIndex = None
    resultIndexInBlock = None
    myMainLogic = None
    
    listOfBlockIndexes = {}
    listOfRandomizationValues = {}
    
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        
        self.listOfBlockIndexes = {'P0': 4, 'P1': 3}
        self.listOfBlockOfFourIndexesNewBlock = {'P0': 4, 'P1': 3, 'P2': 2, 'P3':1}
        self.listOfBlockOfSixIndexesNewBlock = {'P0': 6, 'P1': 5, 'P2': 4, 'P3':3, 'P4':2, 'P5':1}
        self.listOfBlockOfSixIndexesUncompleteBlock = {'P0': 4, 'P1': 3, 'P2': 2, 'P3':1, 'P4':6, 'P5':5, 'P6': 4, 'P7':3, 'P8': 2}
        self.listOfBlockOfFourIndexesUncompleteBlock = {'P0': 6, 'P1': 5, 'P2': 4, 'P3':3, 'P4':2, 'P5':1, 'P6': 4, 'P7':3, 'P8': 2}
        self.listOfBlockOfIndexesMixedBlockType = {'P0': 4, 'P1': 3, 'P2': 4, 'P3':2, 'P4':3}
        self.listOfRandomizationValues = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultStudy}
        self.listOfRandomizationValuesRandom = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultControl}
        self.listOfRandomizationValuesFromBlockOfFourToNewBlock = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultStudy, 'P2': self.randomizationResultControl, 'P3':self.randomizationResultControl}
        self.listOfRandomizationValuesFromBlockOfSixToNewBlock = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultStudy, 'P2': self.randomizationResultControl, 'P3':self.randomizationResultControl, 'P4':self.randomizationResultStudy, 'P5':self.randomizationResultControl}
        self.listOfRandomizationValuesUncompleteBlockOfSix = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultStudy, 'P2': self.randomizationResultControl, 'P3':self.randomizationResultControl, 'P4': self.randomizationResultStudy, 'P5': self.randomizationResultControl, 'P6': self.randomizationResultControl, 'P7':self.randomizationResultControl, 'P8':self.randomizationResultStudy}
        self.listOfRandomizationValuesUncompleteBlockOfFour = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultStudy, 'P2': self.randomizationResultControl, 'P3':self.randomizationResultControl, 'P4': self.randomizationResultStudy, 'P5': self.randomizationResultControl, 'P6': self.randomizationResultControl, 'P7':self.randomizationResultControl, 'P8':self.randomizationResultStudy}
        self.listOfRandomizationValuesMixedBlockType = {'P0': self.randomizationResultStudy, 'P1': self.randomizationResultStudy, 'P2': self.randomizationResultControl, 'P3':self.randomizationResultControl, 'P4': self.randomizationResultStudy}
     
    def setUp(self):
        #exec("globals()['helperMainLogic'] = self.myMainLogic")
        self.myMainLogic = myMainLogic()
        psevaluator.helperMainLogic = self.myMainLogic
        psevaluator.updateDataNoNotify = self.updateDataNoNotify
        self.resultIndex = None
        self.resultIndexInBlock = None
        
    #randomizationIndexes = helperMainLogic.jsonStore.load_values(None, indexAttributeName)
    #stringIndexInBlock = helperMainLogic.jsonStore.load_value(idOfMax, indexInBlockAttributeName)
    #def randomBlocksRandomization(indexAttributeName, indexInBlockAttributeName, randomizationResultAttributeName, randomizationResultStudy, randomizationResultControl)
    
    def updateDataNoNotify(self, attributeName, value):
        if self.indexAttributeName == attributeName:
            self.resultIndex = value
        elif self.indexInBlockAttributeName == attributeName:
            self.resultIndexInBlock = value
        else:
            assert(False)
            
    
    def testFirstPatientEver(self):
        self.myMainLogic.jsonStore.load_values = lambda id, name:{}
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        self.assertEqual(self.resultIndex, self.firstBlockType + str(0))
        assert (self.resultIndexInBlock == 4 or self.resultIndexInBlock == 6)
    
    def testThirdPatientIndexes(self):
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockIndexes[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValues[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        
        self.assertEqual(self.resultIndex, 'A2')
        self.assertEqual(self.resultIndexInBlock, 2)
        assert(not returnValue)
        
    def testNewBlockWithPreviousBlockOfFourCompleted(self):
        """Test: Patient is correcly inserted in the second block as first patient of the new block. Testing from block of size four"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'A2', 'P3':'A3'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfFourIndexesNewBlock[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesFromBlockOfFourToNewBlock[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        self.assertEqual(self.resultIndex, self.firstBlockType + '4')
        assert (self.resultIndexInBlock == 4 or self.resultIndexInBlock == 6)
        
    def testNewBlockWithPreviousBlockOfSixCompleted(self):
        """Test: Patient is correcly inserted in the second block as first patient of the new block. Testing from block of size six"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'A2', 'P3':'A3', 'P4':'A4', 'P5':'A5'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfSixIndexesNewBlock[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesFromBlockOfSixToNewBlock[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        self.assertEqual(self.resultIndex, self.firstBlockType + '6')
        assert (self.resultIndexInBlock == 4 or self.resultIndexInBlock == 6)
        
    def testBlockOfSixWithPreviousBlockCompleted(self):
        """Test: Patient is correcly inserted in the second block (already started). Testing block of size six """
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'A2', 'P3':'A3', 'P4':'A4', 'P5':'A5', 'P6':'A6', 'P7':'A7', 'P8':'A8'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfSixIndexesUncompleteBlock[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesUncompleteBlockOfSix[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        self.assertEqual(self.resultIndex, self.firstBlockType + '9')
        assert(self.resultIndexInBlock == 1)
        
    def testBlockOfFourWithPreviousBlockCompleted(self):
        """Test: Patient is correcly inserted in the second block (already started). Testing block of size four"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'A2', 'P3':'A3', 'P4':'A4', 'P5':'A5', 'P6':'A6', 'P7':'A7', 'P8':'A8'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfFourIndexesUncompleteBlock[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesUncompleteBlockOfFour[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        self.assertEqual(self.resultIndex, self.firstBlockType + '9')
        assert(self.resultIndexInBlock == 1)
        
    def testSelectionIsReallyRandomThirdPatient(self):
        """ Test: Is third value in a row really random when needed? (one hundred proofs). Case: Third patient in an already balanced block"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockIndexes[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesRandom[id]
        valueList = []
        for x in range(1000):
            returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
            valueList.append(returnValue)
        print valueList.count(False)
        print valueList.count(True)
        assert (valueList and len(list(set(valueList))) > 1)
        
    def testBlockOfSixIsCompletedCorrectly(self):
        """Test: Does the last value of a block correctly complete the block itself?"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'A2', 'P3':'A3', 'P4':'A4', 'P5':'A5', 'P6':'A6', 'P7':'A7', 'P8':'A8'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfSixIndexesUncompleteBlock[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesUncompleteBlockOfSix[id]
        previousValue = None
        isAlwaysTheSameResult = True
        for x in range(1000):
            returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
            if previousValue is None:
                previousValue = returnValue
            elif previousValue != returnValue:
                isAlwaysTheSameResult = False
                break
        assert(isAlwaysTheSameResult)
        
    def testBlockOfFourIsCompletedCorrectly(self):
        """Test: Does the last value of a block correctly complete the block itself?"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'A2', 'P3':'A3', 'P4':'A4', 'P5':'A5', 'P6':'A6', 'P7':'A7', 'P8':'A8'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfFourIndexesUncompleteBlock[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesUncompleteBlockOfFour[id]
        previousValue = None
        isAlwaysTheSameResult = True
        for x in range(1000):
            returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
            if previousValue is None:
                previousValue = returnValue
            elif previousValue != returnValue:
                isAlwaysTheSameResult = False
                break
        assert(isAlwaysTheSameResult)
        
    def testFirstBlockTypePatientAddedInItsBlockType(self):
        """Test: Assuming we have mixed blockType, Is the new index considering it block type? Case: firstBlockType"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'B0', 'P3':'A2', 'P4':'B1', 'P5':'B2'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfIndexesMixedBlockType[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesMixedBlockType[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        assert (self.resultIndex == self.firstBlockType + '3')
        
    def testFirstBlockTypePatientAddedInItsBlockType(self):
        """Test: Assuming we have mixed blockType, Is the new index considering it block type? Case: secondBlockType"""
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': 'A0', 'P1': 'A1', 'P2':'B0', 'P3':'A2', 'P4':'B1'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockOfIndexesMixedBlockType[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValuesMixedBlockType[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.secondBlockType)
        assert (self.resultIndex == self.secondBlockType + '2')
    
    def testPatientIfFirstIndexIsZero(self):
        self.myMainLogic.jsonStore.load_values = lambda id, name:{'P0': '0'}
        self.myMainLogic.jsonStore.load_value = lambda id, name: self.listOfBlockIndexes[id] if name == 'crfs.' + self.indexInBlockAttributeName else self.listOfRandomizationValues[id]
        returnValue = psevaluator.randomBlocksRandomization(self.indexAttributeName, self.indexInBlockAttributeName, self.randomizationResultAttributeName, self.randomizationResultStudy, self.randomizationResultControl, self.firstBlockType)
        self.assertEqual(self.resultIndex, 'A0')
        #assert(not returnValue)
    
    def tearDown(self):
        pass

if __name__ == '__main__':

    unittest.main()
