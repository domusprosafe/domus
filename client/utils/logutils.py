import datetime
import os
import inspect
import sys

#this is a global counter useful to write sane logs
logging_call_id = 0

def getNewCallId():
    global logging_call_id;
    logging_call_id+=1
    return logging_call_id


def timeit(func):
    def wrapper(*args, **kwargs):
        try:
            newId = getNewCallId()
            frm = inspect.stack()[1]
            mod = inspect.getmodule(frm[0])
            startTime = datetime.datetime.now()
            print str(newId) + "#: Calling " + mod.__name__ + "." + func.__name__  +" ("+ mod.__file__ + ")"
            print
            out = func(*args, **kwargs)
            timeElapsed = datetime.datetime.now() - startTime
            print str(newId) + "#: Done " + mod.__name__ + "." + func.__name__  +" ("+ mod.__file__ + ") in " + str(timeElapsed)
            print
            return out
        except BaseException, e:
            raise e
    return wrapper
    
def timeitWithArgs(func):
    def wrapper(*args, **kwargs):
        try:
            newId = getNewCallId()
            frm = inspect.stack()[1]
            mod = inspect.getmodule(frm[0])
            startTime = datetime.datetime.now()
            print str(newId) + "#: Calling " + mod.__name__ + "." + func.__name__  +" ("+ mod.__file__ + ")"
            print "args", args
            print "kwargs", kwargs
            print
            out = func(*args, **kwargs)
            timeElapsed = datetime.datetime.now() - startTime
            print str(newId) + "#: Done " + mod.__name__ + "." + func.__name__  +" ("+ mod.__file__ + ") in " + str(timeElapsed)
            print
            return out
        except BaseException, e:
            raise e
    return wrapper


def muteit(func):
    def wrapper(*args, **kwargs):
        tmp = sys.stdout
        sys.stdout = None
        try:
            out = func(*args, **kwargs)
        except BaseException, e:
            raise e
        finally:
            sys.stdout = tmp
        return out
    return wrapper

