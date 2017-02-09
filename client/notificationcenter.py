import weakref

class NotificationCenter(object):

    def __init__(self):
        self.notifications = {}
        self.observerKeys = {}

    def addObserver(self, observer, method, notificationName, observedObject=None):
        observedObjectRef = None
        if observedObject:
            try:
                observedObjectRef = weakref.ref(observedObject)
            except BaseException, e:
                print e
                observedObjectRef = observedObject
        if not self.notifications.has_key(notificationName):
            self.notifications[notificationName] = {}
        notificationDict = self.notifications[notificationName] 
        if not notificationDict.has_key(observedObjectRef):
            notificationDict[observedObjectRef] = {}
        notificationDict[observedObjectRef][observer] = method
        if not self.observerKeys.has_key(observer):
            self.observerKeys[observer] = []
        self.observerKeys[observer].append((notificationName,observedObjectRef))

    def removeObserver(self, observer, notificationName=None, observedObject=None):
        observedObjectRef = None
        if observedObject:
            try:
                observedObjectRef = weakref.ref(observedObject)
            except BaseException, e:
                print e
                observedObjectRef = observedObject
        try:
            observerKeys = self.observerKeys.pop(observer)
        except KeyError:
            return
        for observerKey in observerKeys:
            if notificationName and observerKey[0] != notificationName:
                continue
            if observedObject and observerKey[1] != observedObjectRef:
                continue
            try:
                self.notifications[observerKey[0]][observerKey[1]].pop(observer)
            except KeyError:
                return
            if len(self.notifications[observerKey[0]][observerKey[1]]) == 0:
                self.notifications[observerKey[0]].pop(observerKey[1])
                if len(self.notifications[observerKey[0]]) == 0:
                    self.notifications.pop(observerKey[0])

    def postNotification(self, notificationName, notifyingObject, userInfo=None):
        notifyingObjectRef = None
        if notifyingObject:
            try:
                notifyingObjectRef = weakref.ref(notifyingObject)
            except BaseException, e:
                print e
                notifyingObjectRef = notifyingObject
        try:
            notificationDict = self.notifications[notificationName]
        except KeyError:
            return
        for key in (notifyingObjectRef,None):
            try:
                methodsDict = notificationDict[key]
            except KeyError:
                continue
            observers = methodsDict.keys()
            for observer in observers:
                try:
                    if not userInfo:
                        methodsDict[observer](notifyingObjectRef())
                    else:
                        methodsDict[observer](notifyingObjectRef(),userInfo)
                except BaseException, e:
                    print 'EXCEPTION THROWN UPON NOTIFICATION:', e
                    print methodsDict[observer].func_code.co_filename, methodsDict[observer].func_name
                    import sys, traceback
                    print traceback.print_exc(file=sys.stdout)

notificationCenter = NotificationCenter()

#def InstantiateNotificationCenter():
#    global notificationCenter
#    notificationCenter = NotificationCenter()

if __name__ == '__main__':

    class A(object):
        def foo(self,notifyingObject,userInfo=None):
            print "foo"
            if userInfo:
                try:
                    print userInfo['foo']
                except KeyError:
                    pass
    
    class B(object):
        pass

    notificationCenter = NotificationCenter()

    a = A()
    b = B()
    c = B()

    notificationCenter.addObserver(a,a.foo,"notifyFoo",b)
    notificationCenter.addObserver(a,a.foo,"notifyFoo")

    print notificationCenter.notifications
    print notificationCenter.observerKeys

    print "Before post"
    notificationCenter.postNotification("notifyFoo",b)
    notificationCenter.postNotification("notifyFoo",c)
    print "After post"

    userInfo = {"foo":"userInfoo"}

    print "Before post with userInfo"
    notificationCenter.postNotification("notifyFoo",b,userInfo)
    notificationCenter.postNotification("notifyFoo",c,userInfo)
    print "After post with userInfo"


    #notificationCenter.removeObserver(a,"notifyFoo",b)
    #notificationCenter.removeObserver(a,"notifyFoo")
    notificationCenter.removeObserver(a)

    print notificationCenter.notifications
    print notificationCenter.observerKeys

