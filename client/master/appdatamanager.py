import sys
sys.path.append('./utils')
from blowfish import Blowfish
from xml.etree import ElementTree as etree
import Pyro.core
import os
import base64
from psconstants import abspath
import threading
from pslogging import PsLogger

class AppdataManager(Pyro.core.SynchronizedObjBase):
    
    def __init__(self, appdataFileName=abspath('data/appdata.xml'), encryptionKey=''):
        PsLogger().info('AppdataTag', 'AppdataManager initialization')
        global _   
        _ = lambda translationString: self.translateString(translationString)

        Pyro.core.SynchronizedObjBase.__init__(self)
        self.appdataRoot = None
        self.encryptionKey = encryptionKey
        self.publicCipher = Blowfish(self.encryptionKey)
        self.appdataFileName = appdataFileName
        
        self.lock = threading.RLock()

    def publicEncryptDecryptString(self, inputValue, operation):
        PsLogger().info('AppdataTag', "publicEncryptDecryptString")
        self.lock.acquire()
        try:
            PsLogger().info('AppdataLockTag', "lock acquired")
            self.publicCipher.initCTR()

            if operation == 'encrypt':
                inputValue = inputValue.encode('utf-8')
                outputValue = self.publicCipher.encryptCTR(inputValue)            
            else:
                outputValue = self.publicCipher.decryptCTR(inputValue)
                outputValue = outputValue.decode('utf-8')
        except BaseException, e:
            PsLogger().warning(['AppdataTag','ExceptionTag'], str(e))
            outputValue = None
            PsLogger().info('AppdataTag', str(e))
        finally:
            self.lock.release()
            PsLogger().info('AppdataLockTag', "lock released")
        PsLogger().info('AppdataTag', "END publicEncryptDecryptString")
        return outputValue

    def copyToPath(self, path):
        import shutil
        self.lock.acquire()
        try:
            shutil.copy(self.appdataFileName,path)
        except BaseException, e:
            PsLogger().warning(['AppdataTag','ExceptionTag'], str(e))
            print 'Cannot copy %s to %s' % (self.appdataFileName, path), e
        self.lock.release()
 
    def createAppdata(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)
        if os.path.isfile(self.appdataFileName):
            return
        #xmlString = """<?xml version="1.0" encoding="iso-8859-1"?>
        #    <appdata>
        #      <client clientKey=""/>
        #      <centre centreCode="" privateKey="" country="" wardName="" hospitalName="" city="" defaultLanguage="">
        #        <users>
        #          <user localId="" name="" surname="" username="" password="" userType="" enabled="" lastAccessDate="" passwordExpiryDate="" firstPasswordChanged="" defaultLanguage="" inputDate=""/>
        #        </users>
        #        <crfs>
        #          <crf name="" minValidDate="" maxValidDate=""/>
        #        </crfs>
        #      </centre>
        #    </appdata> 
        #""" 
        xmlString = """<?xml version="1.0" encoding="iso-8859-1"?>
            <appdata>
                <client/>
                <centre>
                    <users/>
                    <crfs/>
                </centre>
            </appdata> 
        """ 

        self.appdataRoot = etree.fromstring(xmlString)
        self.writeAppdata()
 
    def getAppdataString(self):
        return etree.tostring(self.appdataRoot)

    def getElementString(self,el):
        return etree.tostring(el)

    def getAppdataValue(self,path,attribute):
        if not self.appdataRoot:
            return None
        el = self.appdataRoot.find(path)
        if el is None:
            #print 'Error: getAppdataValue could not find path %s' % path
            return None
        return el.get(attribute)

    def setAppdataValue(self,path,attribute,value,write=True):
        el = self.appdataRoot.find(path)
        if el is None:
            print 'Error: getAppdataValue could not find path %s' % path
            self.lock.release()
            return
        el.set(attribute,unicode(value))
        if write:
            self.writeAppdata()

    def getAppdataElement(self,path):
        if not self.appdataRoot:
            return None
        el = self.appdataRoot.find(path)
        return el

    def getAppdataElements(self,path):
        if not self.appdataRoot:
            return None
        iter = self.appdataRoot.findall(path)
        return iter

    def getAppdataElementsWithAttribute(self,path,attribute,value):
        if not self.appdataRoot:
            return None
        iter = self.appdataRoot.findall(path)
        elements = [el for el in iter if el.get(attribute) == value]
        return elements

    def getAppdataElementWithAttribute(self,path,attribute,value):
        if not self.appdataRoot:
            return None
        iter = self.appdataRoot.findall(path)
        elements = [el for el in iter if el.get(attribute) == value]
        if not elements:
            return None
        return elements[0]

    def replaceAppdataElementWithAttribute(self,path,attribute,value,element,write=True):
        if not self.appdataRoot:
            return None
        parentPath = '/'.join(path.split('/')[:-1])
        iter = self.appdataRoot.findall(path)
        elements = [el for el in iter if el.get(attribute) == value]
        parentElement = self.getAppdataElement(parentPath)
        for el in elements:
            parentElement.remove(el)
        self.appendAppdataElement(parentPath,element,write)

    def getAppdataElementsWithAttributes(self,path,attributes,values):
        if not self.appdataRoot:
            return None
        iter = self.appdataRoot.findall(path)
        elements = []
        for el in iter:
            skip = False
            for attribute, value in zip(attributes,values):
                if el.get(attribute) != value:
                    skip = True
                    break
            if skip:
                continue
            elements.append(el)
        return elements

    def getAppdataElementWithAttributes(self,path,attributes,values):
        if not self.appdataRoot:
            return None
        iter = self.appdataRoot.findall(path)
        elements = []
        for el in iter:
            skip = False
            for attribute, value in zip(attributes,values):
                if el.get(attribute) != value:
                    skip = True
                    break
            if skip:
                continue
            elements.append(el)
        if not elements:
            return None
        return elements[0]

    def setAppdataElement(self,path,element,write=True):
        if self.appdataRoot == None:
            print 'Error: appdataRoot is None, could not setAppdataElement'
            return
        parent = self.appdataRoot.find(path)
        if parent is None:
            print 'Error: getAppdataValue could not find path %s' % path
            return
        el = parent.find(element.tag)
        if el is not None:
            parent.remove(el)
        parent.append(element)
        if write:
            self.writeAppdata()

    def createAppdataElement(self,path,tag,write=True):
        element = etree.Element(tag)
        self.setAppdataElement(path,element,write)

    def appendAppdataElement(self,path,element,write=True):
        parent = self.appdataRoot.find(path)
        if parent is None:
            print 'Error: getAppdataValue could not find path %s' % path
            return
        parent.append(element)
        if write:
            self.writeAppdata()
            
    def writeAppdata(self,base64encoded=True):
        PsLogger().info('AppdataTag', "writeAppdata")
        self.lock.acquire()
        PsLogger().info('AppdataLockTag', "lock acquired")
        try:
            xmlString = etree.tostring(self.appdataRoot)
            xmlStringEnc = self.publicEncryptDecryptString(xmlString,'encrypt')
            if base64encoded:
                xmlStringEnc = base64.b64encode(xmlStringEnc)
            tmpAppdataFileName = self.appdataFileName + '.tmp'
            tmp2AppdataFileName = self.appdataFileName + '.tmp2'
            f = open(tmpAppdataFileName,"wb")
            f.write(xmlStringEnc)
            f.close() 
            removeTmp2 = False
            if os.path.isfile(self.appdataFileName):
                os.rename(self.appdataFileName,tmp2AppdataFileName)
                removeTmp2 = True
            os.rename(tmpAppdataFileName,self.appdataFileName)
            if removeTmp2:
                os.remove(tmp2AppdataFileName)
        except BaseException, e:
            PsLogger().warning(['AppdataTag','ExceptionTag'], str(e))
        finally:
            self.lock.release()
            PsLogger().info('AppdataLockTag', "lock released")
        PsLogger().info('AppdataTag', "end writeAppdata")

    def backupAppdata(self,backupFileName,base64encoded=True):
        PsLogger().info('AppdataTag', "backupAppdata")
        self.lock.acquire()
        try:
            PsLogger().info('AppdataLockTag', "lock acquired")
            backupFilePath = os.path.join(os.path.dirname(self.appdataFileName),backupFileName)
            xmlString = etree.tostring(self.appdataRoot)
            f = open(backupFilePath,"wb")
            xmlStringEnc = self.publicEncryptDecryptString(xmlString,'encrypt')
            if base64encoded:
                xmlStringEnc = base64.b64encode(xmlStringEnc)
            f.write(xmlStringEnc)
        except BaseException, e:
            PsLogger().warning(['AppdataTag','ExceptionTag'], str(e))
        finally:
            f.close() 
            self.lock.release()
            PsLogger().info('AppdataLockTag', "lock released")
            
        PsLogger().info('AppdataTag', "END backupAppdata")

    def loadAppdata(self,base64encoded=True):
        PsLogger().info('AppdataTag', "loadAppdata")
        self.lock.acquire()
        PsLogger().info('AppdataLockTag', "lock acquired")
        tmp2AppdataFileName = self.appdataFileName + '.tmp2'
        if not os.path.isfile(self.appdataFileName) and os.path.isfile(tmp2AppdataFileName):
            os.rename(tmp2AppdataFileName,self.appdataFileName)
        try:
            f = open(self.appdataFileName, "rb")
        except BaseException, e:
            self.lock.release()
            PsLogger().warning(['AppdataTag','ExceptionTag'], str(e))
            PsLogger().info('AppdataLockTag', "lock released")
            return False

        xmlStringEnc = f.read()
        if base64encoded:
            xmlStringEnc = base64.b64decode(xmlStringEnc)
        xmlString = self.publicEncryptDecryptString(xmlStringEnc,'decrypt')
        f.close()
        if xmlString == None:
            self.lock.release()
            PsLogger().info('AppdataLockTag', "lock released")
            return False
        
        try:
            self.appdataRoot = etree.fromstring(xmlString)
            self.backupAppdata('appdata_bkp.xml')
        except:
            try:
                f = open('appdata_bkp.xml', 'rb')
            except:
                self.lock.release()
                PsLogger().info('AppdataLockTag', "lock released")
                return False
            xmlStringEnc = f.read()
            if base64encoded:
                xmlStringEnc = base64.b64decode(xmlStringEnc)
            xmlString = self.publicEncryptDecryptString(xmlStringEnc,'decrypt')
            f.close()
            if xmlString == None:
                self.lock.release()
                return False
            self.appdataRoot = etree.fromstring(xmlString)

        self.lock.release()
        PsLogger().info('AppdataLockTag', "lock released")
        PsLogger().info('AppdataTag', "END loadAppdata")
        return True

    def isAppdataLoaded(self):
        if not self.appdataRoot:
            return False
        return True


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print 'Usage: python appdatamanager.py appdatafile.xml [--activate CENTRECODE] encoded[0|1] [[outputencodedfile.xml] encoded[0|1]], e.g.\npython appdatamanager.py appdata.xml 0 appdata2.xml\npython appdatamanager.py appdata.xml 1\npython appdatamanager.py --activate IT999 appdata.xml 1 appdata.xml'
        sys.exit(0)

    offset = 0

    centreCode = None
    if '--activate' in sys.argv:
        centreCode = sys.argv[2]
        offset = 2

    dataPath = sys.argv[offset+1]
    key = 'custom_encryption_key'

    encoded = True
    if sys.argv[offset+2] == '0':
        encoded = False
    
    appdataManager = AppdataManager(dataPath,key)
    loaded = appdataManager.loadAppdata(encoded)
    #users = appdataManager.getAppdataElementWithAttribute('centre/users/user','username','admin')
    #users.set('enabled','1')

    print 'appdata loaded: ', loaded
    print etree.tostring(appdataManager.appdataRoot)
    write = False
    if len(sys.argv) > offset + 3:
        appdataManager.appdataFileName = sys.argv[offset+3]
        write = True
    if centreCode:
        appdataManager.setAppdataValue('centre','centreCode',centreCode,write=False)
    writeEncoded = True
    if len(sys.argv) > offset + 4 and sys.argv[4] == '0':
        writeEncoded = False
    if write:
        print 'writing appdata:'
        print etree.tostring(appdataManager.appdataRoot)
        appdataManager.writeAppdata(writeEncoded)

