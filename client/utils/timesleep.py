import time

Alive = True

def TimeSleep(seconds, timeunit=0.5):
    for i in range(int(seconds/float(timeunit))):
        if not Alive:
            return False
        time.sleep(timeunit)
    return True

MasterAlive = True

def MasterTimeSleep(seconds, timeunit=0.5):
    for i in range(int(seconds/float(timeunit))):
        if not MasterAlive:
            return False
        time.sleep(timeunit)
    return True

