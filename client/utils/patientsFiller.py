# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.append('./gui')
sys.path.append('./locale')
sys.path.append('./utils')
sys.path.append('./dlls')
sys.path.append('./master')
import warnings
warnings.simplefilter("ignore",DeprecationWarning)

from mainlogic import MainLogic
from psversion import PROSAFE_VERSION
from maincontroller import MainController

import random
import time
import datetime
import string

def randomString(length=8, chars=string.letters + string.digits):
    return ''.join([random.choice(chars) for i in range(length)])


def strTimeProp(start, end, format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))
    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDateISO(start, end, prop):
    return strTimeProp(start, end, '%Y-%m-%d', prop)
    #return strTimeProp(start, end, '%d-%m-%Y', prop)


class PatientFiller(object):
    def __init__(self):
        self.mainLogic = MainLogic(testing=True,localhost=True,nosynch=True)
        self.mainController = MainController(self.mainLogic)
        self.mainLogic.loadAppdata()
        self.mainLogic.loadConfig()
        
    def doLogin(self, user, password):
        print "Logging in..."
        return self.mainLogic.doLogin(user, password)
        
    def createRandomAdmission(self):
        print "Creating random admission"
        basedata = dict()
        basedata['firstName'] = randomString()
        basedata['lastName'] = randomString()
        #basedata['birthDate'] = randomDateISO("01-01-1920", "31-12-2009", random.random())
        basedata['birthDate'] = randomDateISO("1920-01-01", "2009-12-31", random.random())
        basedata['sex'] = None
        #basedata['admissionDate'] = randomDateISO("01-01-2010", "31-12-2010", random.random())
        basedata['admissionDate'] = randomDateISO("2010-01-01", "2010-12-31", random.random())
        basedata['admissionKey'] = -1
        
        self.mainLogic.createAdmission(newPatient = True, admissionDate = basedata['admissionDate'])
        self.mainLogic.saveBasedata(basedata)
        
        
if __name__ == '__main__':
    filler = PatientFiller()
    filler.doLogin('a','o')
    for i in range(100):
        filler.createRandomAdmission()
        
    sys.exit(1)

