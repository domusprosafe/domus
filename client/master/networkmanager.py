import sys
sys.path.append("../")
import os
from urllib2 import urlopen, URLError, HTTPError
import Pyro.core
import cookielib
import urllib
import urllib2
import time
import threading
import multiparthandler
import activationcode
import psconstants
import os
from psversion import PROSAFE_VERSION
from timesleep import MasterTimeSleep
from psconstants import abspath
from psconstants import compareVersions
import shutil

def QueryServer(centreCode, key, value='', flag=False, forced=False):
    url = psconstants.SERVER_QUERY_URL
    try:
        req = urllib2.Request(url)
        data = urllib.urlencode({'centreCode':centreCode, 'key':key, 'value':value, 'flag':flag, 'version':PROSAFE_VERSION, 'forced':forced})
        #print url, data
        f = urllib2.urlopen(url,data)
        result = f.read()
        if result == 'OK':
            return True
    except:
        pass
    return False

class NetworkManager(Pyro.core.ObjBase):
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.connectionSetUp = self.isInternetAvailable()
        self.checkingSoftwareUpdate = False
        self.releaseServerBasedThreads = False
        
    def isInternetAvailable(self):
        try:
            #should we use something different?
            response=urllib2.urlopen('http://74.125.228.100',timeout=1)
            return True
        except urllib2.URLError as e:
            pass
        return False

    def couldConnect(self):
        return self.connectionSetUp

    def tryConnection(self, proxyAddress, username, password):
        connectionSetUp = False
        if proxyAddress:
            if username and password:
                connectionSetUp = self.setUpConnection(proxyAddress,username,password)
            else:
                connectionSetUp = self.setUpConnection(proxyAddress)
    
        if not connectionSetUp:
            connectionSetUp = self.setUpConnection()

        if not connectionSetUp:
            connectionSetUp = self.setUpConnection(noProxy=True)
    
        self.connectionSetUp = connectionSetUp
        print 'can connect to server?', connectionSetUp
        self.releaseServerBasedThreads = connectionSetUp
        return connectionSetUp

    def setUpConnection(self, proxyAddress=None, username=None, password=None, noProxy=False):
   
        opener = None
      
        if proxyAddress:
            if username and password:
                proxyHandler = urllib2.ProxyHandler({'http': 'http://' + username + ':' + password + '@' + proxyAddress, 'https': 'http://' + username + ':' + password + '@' + proxyAddress})
                authHandler = urllib2.HTTPBasicAuthHandler()
                opener = urllib2.build_opener(proxyHandler, authHandler, urllib2.HTTPHandler, urllib2.HTTPSHandler, multiparthandler.MultipartPostHandler)
      
            else:
                proxyHandler = urllib2.ProxyHandler({'http': 'http://' + proxyAddress, 'https': 'http://' + proxyAddress})
                authHandler = urllib2.HTTPBasicAuthHandler()
                opener = urllib2.build_opener(proxyHandler, authHandler, urllib2.HTTPHandler, urllib2.HTTPSHandler, multiparthandler.MultipartPostHandler)
        elif noProxy == False:
            cookies = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),multiparthandler.MultipartPostHandler) 
        else:
            proxy_handler = urllib2.ProxyHandler({})
            opener = urllib2.build_opener(proxy_handler)

        urllib2.install_opener(opener)

        url = psconstants.CONNECTION_CHECK_URL
        try:
            output = opener.open(url)
            result = output.read()
      
            if 'Hello world :)' in result:
                return True
            else:
                cookies = cookielib.CookieJar()
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),multiparthandler.MultipartPostHandler)
                urllib2.install_opener(opener)
                #output = opener.open(url, params)            
                output = opener.open(url)            
                result = output.read()
                if 'Hello world :)' in result:
                    return True
                else:
                    return False
            return False

        except BaseException, e:
            try:
                cookies = cookielib.CookieJar()
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),multiparthandler.MultipartPostHandler)
                urllib2.install_opener(opener)
                #output = opener.open(url, params)            
                output = opener.open(url) 
                result = output.read()
                if 'Hello world :)' in result:
                    return True
                else:
                    return False
            except BaseException, e:
                return False

        return False

    def verifyActivationCode(self, centreCode, activationKey):
        try:
            return activationcode.checkActivationCode(centreCode,activationKey)
        except:
            return False

    def sendSecondaryPasswordToServer(self, centreCode, secondaryPassword):
        url = psconstants.SECONDARY_PASSWORD_URL
        try:
            req = urllib2.Request(url)
            data = urllib.urlencode({'centreCode':centreCode, 'secondaryPassword':secondaryPassword})
            f = urllib2.urlopen(url,data)
            result = f.read()
            if result == 'OK':
                return True
        except:
            pass
        return False

    #TODO: Remove.
    def getVersion(self):
        if PROSAFE_VERSION in ['1.1.7', '1.1.8', '1.1.9', '1.1.10', '1.1.11']:
            return '1.1.6'
        return PROSAFE_VERSION

    def getMasterVersion(self):
        return PROSAFE_VERSION

    def getActivePetals(self, centreCode):
        try:
            return activationcode.checkPetals(centreCode)
        except:
            return False
            
    def fetchMessagesFromServer(self, centreCode):
        url = psconstants.FETCH_MESSAGES_URL
        try:
            req = urllib2.Request(url)
            data = urllib.urlencode({'centreCode':centreCode})
            f = urllib2.urlopen(url,data)
            result = f.read()
            messages = []
            exec("messages = %s" % result)
            return messages
        except BaseException, e:
            print e
            pass
        return []
        
    def serverBasedThreadsHaveBeenReleased(self):
        counter = 0
        while not self.releaseServerBasedThreads:
            time.sleep(1)
            counter += 1
            if counter >= 30:
                return False
        return True
                
        
    def fetchScriptsFromServer(self, centreCode, scriptDirectory):
        url = psconstants.FETCH_SCRIPTS_URL
        url2 = psconstants.FETCH_SCRIPTS_FILENAMES_URL
        print 'trying to get scripts from server'
        newScripts = []
        if not self.serverBasedThreadsHaveBeenReleased():
            return []
        try:
            data = urllib.urlencode({'centreCode':centreCode})
            f = urllib2.urlopen(url2,data)
            result = f.read()
            scripts = eval(result)
            scripts.sort()
            for fileName in scripts:
                if os.path.exists(os.path.join(scriptDirectory, fileName)):
                    continue
                #checking same scripts of different version
                if '_v' in fileName:
                    baseFileName, version = fileName.split('_v')
                    removeThoseScripts = [scriptName for scriptName in os.listdir(scriptDirectory) if baseFileName in scriptName and scriptName != fileName and ('_v' not in scriptName or scriptName.split('_v')[1] < version)]
                    for script in removeThoseScripts:
                        os.remove(os.path.join(scriptDirectory, script))
                
                self.downloadFileFromServer(url, scriptDirectory, fileName)
                newScripts.append(fileName)
            print 'scripts correctly updated'
        except BaseException, e:
            print 'error occurred while updating scripts:', e
        
        return newScripts
        
    def downloadFileFromServer(self, url, scriptDirectory, fileName):
        try:
            f = urlopen(url+fileName)
            print "downloading " + url
            # Open our local file for writing
            with open(os.path.join(scriptDirectory, fileName), "wb") as local_file:
                local_file.write(f.read())
        #handle errors
        except HTTPError, e:
            print "HTTP Error:", e.code, url
        except URLError, e:
            print "URL Error:", e.reason, url
        
        

    def checkSoftwareUpdate(self, centreCode, stopServicesCallback):

        if self.checkingSoftwareUpdate:
            return False

        self.checkingSoftwareUpdate = True

        try:
            import esky
            from versionfinder import ProsafeVersionFinder
        except:
            print 'WARNING: No Esky module found'
            self.checkingSoftwareUpdate = False
            return False
            
        updated = False 
        
        if QueryServer(centreCode, 'UpdateSW','Allow', True):
            try:
                if getattr(sys,"frozen",False):       
                    updateStopped = False        
                    
                    lockfile = os.path.join(os.getcwd(),'download.lock')
                    try:
                        os.unlink(lockfile)
                    except:
                        pass
                    import psconstants as psc
                    #if psc.appName == 'prosafe':
                    #    vfinder = ProsafeVersionFinder(psconstants.ESKY_FILES_DOWNLOAD_URL + centreCode, lockfile)
                    #else:
                    #    vfinder = ProsafeVersionFinder(psconstants.ESKY_FILES_DOWNLOAD_URL, lockfile)
                    vfinder = ProsafeVersionFinder(psconstants.ESKY_FILES_DOWNLOAD_URL + centreCode, lockfile)
                    eskyApp = esky.Esky(sys.executable, vfinder)            
                    #self.progressDlg.Show()
                    #self.progressDlg.SetFocus()            
                    tr = EskyDownloader(eskyApp)
                    print "starting Esky downloader"
                    tr.start()
                    keepGoing = True
                    while tr.is_alive() and keepGoing:
                        if not MasterTimeSleep(1):
                            keepGoing = False
                    #    (keepGoing, skip) = self.progressDlg.UpdatePulse()
                        if not keepGoing:
                            updateStopped = True

                    #TODO: what is this lockfile here for?
                    if updateStopped:
                        l = open(lockfile, "wb")
                        l.close()
 
                    #self.progressDlg.Destroy()
                    if tr.downloaded == True:
                        print "cleanup"
                        eskyApp.cleanup()
                        updated = True
 
                        #stop Pyro services and threads                    
                        stopServicesCallback()
                        
                        #notify server of update done ... if we restart this
                        #is the last place where we can do it
                        QueryServer(centreCode, 'UpdateSW','Done', True)
                      
                        #TODO: "prosafe.exe" is not crossplatform
                        #TODO: avoid doing this in network manager
                        #command = abspath("prosafe.exe") 
                        #os.execl(command, ' ')
                        import wx
                        wx.CallAfter(sys.exit,0)
                    
            except BaseException, e:
                print e

            self.checkingSoftwareUpdate = False
            QueryServer(centreCode, 'UpdateSW','Done', True)

        else:
            print 'Update denied'
            

        return updated
 
class EskyDownloader(threading.Thread):

    def __init__(self, eskyApp):
        threading.Thread.__init__(self)
        self.eskyApp = eskyApp
        self.downloaded = False      
        
    def run(self):
        currentVersion = self.eskyApp.active_version
        print "currentVersion", currentVersion
        try:
            updateVersion = self.eskyApp.find_update()
            print "updateVersion", updateVersion
            #if updateVersion is not None and updateVersion > currentVersion :
            if updateVersion is not None and compareVersions(updateVersion,currentVersion) > 0:
                packageName = self.eskyApp.fetch_version(updateVersion)
                               
                if not self.eskyApp.version_finder.stopped:
                    self.eskyApp.install_version(updateVersion)
                    self.downloaded = True

        except Exception, e:
            print str(e)
            pass 
