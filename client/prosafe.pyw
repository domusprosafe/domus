# -*- coding: utf-8 -*-

import sys
import os
import threading

sys.path.append('./gui')
sys.path.append('./locale')
sys.path.append('./utils')
sys.path.append('./dlls')
sys.path.append('./master')
sys.path.append('./master/jsonstore')
sys.path.append('./config_master')
import warnings
warnings.simplefilter("ignore",DeprecationWarning)

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import wx
import time
import datetime
import gzip
import xml
import random
import string
import urllib2
import sqlite3 as sqlite
import blowfish
from wx.lib.embeddedimage import PyEmbeddedImage
import psconstants as psc
from login import LoginDialog
from login import ActivationDialog
from mainlogic import MainLogic
from psbrowser import PSBrowser
from pseditor import PSEditor
from psuserprefs import PSUserPrefs
from psusermanager import PSUserManager
from pspwdchanger import PSPwdChanger
from psfieldscustomizer import PSFieldsCustomizer

from psadmissiondialog import PSAdmissionDialog
from psproxydialog import PSProxyDialog
from psexporter import PSExporter

from psconstants import abspath
from psversion import PROSAFE_VERSION
import wx.lib.hyperlink
from pslogging import PsLogger
from maincontroller import MainController

from networkmanager import NetworkManager
from appdatamanager import AppdataManager
from pslogging import PsLogger

class PSApp(wx.App):
    
    def __init__(self, redirect=False, flags=dict(), filename=None, useBestVisual=False, clearSigInt=True):
        self.flags = flags
        wx.App.__init__(self, redirect, filename, useBestVisual, clearSigInt)
        
    def OnInit(self):
        import datetime
        startingTime = datetime.datetime.now()
        self.imageFile = psc.splashFile
        bmp = wx.Image(self.imageFile,wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        splash = wx.SplashScreen(bmp, wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_NO_TIMEOUT, 6000, None, -1, wx.DefaultPosition, wx.DefaultSize, wx.SIMPLE_BORDER)
        splash.Raise()

        wx.Log.EnableLogging(False)
        #self.name = _("PROSAFE")
        self.name = "PROSAFE"
        self.instance = wx.SingleInstanceChecker("%s-%s" % (self.name,wx.GetUserId()))
        if self.instance.IsAnotherRunning() and not os.path.isfile(abspath('multimaster.txt')):
            splash.Destroy()
            #wx.MessageBox(_("Another instance of PROSAFE is currently running"), _("ERROR"))
            wx.MessageBox("Another instance of PROSAFE is currently running.\n\nPROSAFE e' gia' in esecuzione su questo computer.", "ERROR")
            sys.exit(0)
            return False

        try:
            if os.path.isfile(abspath('test.txt')):
                os.remove(abspath('test.txt'))
            f = open(abspath('test.txt'),'wb')
            f.write('Write test')
            f.close()
            if os.path.isfile(abspath('test.txt')):
                os.remove(abspath('test.txt'))
        except BaseException, e:
            PsLogger().warning(['MainModuleTag','ExceptionTag'], str(e))
            print e
            splash.Destroy()
            wx.MessageBox("The software cannot work correctly becuase the PROSAFE folder is not writable by the current user. Please contact your system administrator for changing the folder write permissions.\n\nIl programma non puo' funzionare correttamente in quanto non e' possibile scrivere nella cartella di installazione di PROSAFE. Contattare l'amministratore di sistema per modificare i permessi di scrittura della cartella.", "ERROR")
            sys.exit(0)
            return False
 
        dataPath = abspath('data')
        self.mainLogic = MainLogic(flags=self.flags)
        from mainlogic import _
        
        #TODO: TRANSLATE
        if self.mainLogic.isMaster == False and self.mainLogic.connectedToMaster == False:
            splash.Destroy()
            wx.MessageBox(_("This computer is configured as a PROSAFE Client, but no PROSAFE Master can be found on the network"), _("ERROR"))
            sys.exit(0)
            return False

        if self.mainLogic.connectingToOtherMasterAsMaster == True:
            splash.Destroy()
            wx.MessageBox(_("This computer is configured as a PROSAFE Master, but another PROSAFE Master was found on the network.\nPlease contact your IT department for setting up a multi-Master configuration."), _("ERROR"))
            sys.exit(0)
            return False
        migrationCompleted = None
        self.mainController = MainController(self.mainLogic)
        needsRestore = False
        if self.mainLogic.isMaster:
            needsRestore = self.mainLogic.master.needsRestore()
            if self.mainLogic.master.jsonStoreMigrationIsNeeded():
                splash.Hide()
                dlg = wx.MessageDialog(None, _("ENGLISH:\n\nProsafe needs to migrate its database. This operation is mandatory and cannot be avoided. Please wait the end of the migration or cancel it to migrate later (in this case Prosafe will close itself). Please call for assistance if any error occurs.\n\nITALIANO:\n\nProsafe necessita di migrare il suo database. Questa operazione � obbligatoria e non pu� essere evitata. Si prega di attendere il termine della migrazione o di annullarla per migrare in seguito (in tal caso Prosafe si chiuder�). Si prega di richiedere assistenza qualora ci fossero problemi."), _("Warning"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
                dlg.Center()
                result = dlg.ShowModal()
                if result != wx.ID_OK:
                    sys.exit(0)
                    return False
                migrationCompleted = self.mainController.showJsonMigrationProgressBar(self.mainLogic.master.migrateToStore)
            else:
                migrationCompleted = True
            
        if not migrationCompleted:
            storePath = abspath('data',True)
            if self.mainLogic.isMaster:
                try:
                    self.mainLogic.master.jsonStore.entryManager.pool.dispose()
                    os.remove(os.path.join(self.mainLogic.dataPath,'prosafestore.sqlite'))
                except BaseException, e:
                    PsLogger().warning(['MainModuleTag','ExceptionTag'], str(e))
                    print "can't delete prosafestore:", e
                sys.exit(0)
        local = False
        if not self.mainLogic.masterFileExists():
            local = True
        self.mainLogic.loadAppdata(local)
        self.mainLogic.loadConfig(local)
        if needsRestore:
            splash.Hide()
            self.restoreIndexes()
        else:
            print 'does not need restore'
            
        splash.Destroy()

        if not self.mainLogic.masterFileExists():
            if self.mainLogic.checkActivation():
                self.mainLogic.deactivate()
                self.mainLogic.loadAppdata(local)
            #self.connectAndActivate()

        if not self.mainLogic.checkActivation():
            self.connectAndActivate()
        
        #if self.mainLogic.testing and not self.mainLogic.checkActivation():
        #    self.connectAndActivate()

        if local:
            #TODO: TRANSLATE
            busyInfo = wx.BusyInfo(_("Initializing PROSAFE"),None)
            self.mainLogic.loadAppdata()
            self.mainLogic.loadConfig()
            self.mainLogic.createMasterFile()
            self.mainLogic.attemptBecomeMaster()
            del busyInfo

        if self.mainLogic.isMaster:
            self.mainLogic.master.crfFileDict = self.mainLogic.crfFileDict
            self.mainLogic.master.readmissionThread.start()
            self.mainLogic.master.evaluationThread.start()

        self.mainController.showLogin()
        showLoginTime = datetime.datetime.now()
        PsLogger().warning('MainModuleTag', 'BEFORE LOGIN: %s\n' % str((showLoginTime - startingTime).seconds))
        #self.mainController.doLogin('admin','adminadmin')
        return True

    def restoreIndexes(self):
        admissions = []
        patients = []
        storeRows = self.mainLogic.master.jsonStore.getStore()
        self.mainLogic.inputUserKey = 'PROSAFE'
        print 'needs restore'
        self.mainLogic.initializeEncryption()
        counter = 0
    
        maximum = len(storeRows)
        from mainlogic import _
        dlg = wx.ProgressDialog(_("Restoring prosafe indexes"),
                               "",
                               maximum = maximum,
                               parent=None,
                               style = wx.PD_CAN_ABORT
                                | wx.PD_APP_MODAL
                                | wx.PD_ELAPSED_TIME
                                #| wx.PD_ESTIMATED_TIME
                                | wx.PD_REMAINING_TIME
                                )

        keepGoing = True
        count = 0

        while keepGoing and count < maximum:
            row = storeRows[count]
            id, dump = row
            try:
                loadedAdmission = self.mainLogic.loadAdmission(admissionKey=None, acquireLock=True, dump=dump)
            except BaseException, e:
                PsLogger().warning(['MainModuleTag','ExceptionTag'], str(e))
                print 'error while loading json id ', id
                continue
            if not loadedAdmission:
                count += 1
                continue
            try:
                self.mainLogic.saveData(False, True, True, False, dataId=id)                    
            except BaseException, e:
                PsLogger().warning(['MainModuleTag','ExceptionTag'], str(e))
                print e
                self.mainLogic.master.jsonStore.emptyFlat()
                sys.exit(0)
            if self.mainLogic.dataSession.admissionKey not in admissions:
                admissions.append(self.mainLogic.dataSession.admissionKey)
            if self.mainLogic.dataSession.patientKey not in patients:
                patients.append(self.mainLogic.dataSession.patientKey)
            self.mainLogic.exitAdmission()
            (keepGoing, skip) = dlg.Update(count, _("Restoring admission... "))
            count += 1
            if not keepGoing and skip:
                self.mainLogic.master.jsonStore.emptyFlat()
                sys.exit(0)
        dlg.Destroy()
            
        admissionsNextId = 1
        patientsNextId = 1
        if admissions:
            admissionsNextId = max([int(el.split('-')[-1]) for el in admissions])
            patientsNextId = max([int(el.split('-')[-1]) for el in patients])
            self.mainLogic.master.jsonStore.create({'migration':'complete'})
            print 'setting admissionsNextId', admissionsNextId
            print 'setting patientsNextId', patientsNextId
        self.mainLogic.master.jsonStore.setStartingUUID('admission',admissionsNextId)
        self.mainLogic.master.jsonStore.setStartingUUID('patient',patientsNextId)
        
    def connectAndActivate(self):
        print 'connectAndActivate'

        from mainlogic import _
        try:
            networkManager = self.mainLogic.networkManager
            if not networkManager:
                raise
            self.mainLogic.loadAppdata()
            self.mainLogic.master.checkConnection()
        except BaseException, e:
            PsLogger().warning(['MainModuleTag','ExceptionTag'], str(e))
            print e
            networkManager = NetworkManager()
            
            address = ''
            username = ''
            password = ''
            try:
                address = self.mainLogic.appdataManager.getAppdataValue('network/proxy','address')
                username = self.mainLogic.appdataManager.getAppdataValue('network/proxy','username')
                password = self.mainLogic.appdataManager.getAppdataValue('network/proxy','password')
            except BaseException, e:
                PsLogger().warning(['MainModuleTag','ExceptionTag'], str(e))
                print e
            
            networkManager.tryConnection(address,username,password)
            self.mainLogic.networkManager = networkManager
        
        connectionSetUp = networkManager.couldConnect()
        
        #if not self.mainLogic.checkActivation():

        address = ''
        username = ''
        password = ''

        if not self.mainLogic.testing:
            if not connectionSetUp:
                dlg = wx.MessageDialog(None, 
                    _("A connection could not be established. Please check that a network connection is available, and eventually enter proxy settings in the next dialog."),
                    _("Connection Error"), wx.OK | wx.ICON_ERROR)
                dlg.Center()
                dlg.ShowModal()
                dlg.Destroy()
                proxyDlg = PSProxyDialog(None,-1,activation=True)
                proxyDlg.Center()
 
                while not connectionSetUp:
                    proxyDlg.ShowModal()
                    if proxyDlg.exitFlag:
                        self.mainController.doQuit()
                    address = proxyDlg.address.GetValue()
                    address = address.replace('http://','')
                    username = proxyDlg.username.GetValue()
                    password = proxyDlg.password.GetValue()
                    connectionSetUp = networkManager.tryConnection(address,username,password)

        self.mainController.showActivation()
        if address:
            self.mainLogic.saveProxySettings(address,username,password)

        if not connectionSetUp:
            dlg = wx.MessageDialog(None, 
                _("A connection could not be established. Please check that a network connection is available, and that eventual proxy settings has been propery configured by the PROSAFE Administrator. PROSAFE will still be usable in local mode, but no software or data syncrhonization will be available."),
                _("Connection Error"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
        
        return True

 
    #def connect(self):
    #    # 1. get connection data in appdata
    #    # 2. test connections
    #    # 3. eventually acknowledge user of connection problem
    #    from mainlogic import _
    #    #proxyAddress = 'srvisalecco.osp-lecco.it:8080'
    #    #username = 'm.tavola'
    #    #passwords = ['mplep01684','01684mplep']
    #    progressDlg = wx.ProgressDialog(_("Connection"),_("Establishing network connection."),maximum = 10,parent=None,style = wx.PD_SMOOTH|wx.PD_APP_MODAL)
    #    progressDlg.Pulse()
   
    #    progressDlg.Destroy()

 

if __name__ == '__main__':

    #noEsky = False
    #try:
    #    import esky
    #except:
    #    noEsky = True

    #if getattr(sys,"frozen",False) and not noEsky:

    #    eskyApp = esky.Esky(sys.executable,"http://manda.marionegri.it:8080/prosafedownloads/")
    #    #change to real path of python program
    #    target = esky.join_app_version(eskyApp.name,eskyApp.version,eskyApp.platform)
    #    target = os.path.join(eskyApp.appdir,target)
    #    os.chdir(target)

    if '--app' in sys.argv:
        appName = sys.argv[sys.argv.index('--app')+1]
        print 'Configuring PROSAFE app %s' % appName
        config_all_path = abspath('config_all',True)
        config_app_path = os.path.join(config_all_path,appName)
        config_master_path = abspath('config_master',True)
        if not os.path.isdir(config_master_path):
            os.mkdir(config_master_path)
        if os.path.isdir(config_app_path):
            fileNames = os.listdir(config_master_path)
            for fileName in fileNames:
                filePath = os.path.join(config_master_path,fileName)
                if not os.path.isfile(filePath):
                    continue
                os.remove(filePath)
            fileNames = os.listdir(config_app_path)
            for fileName in fileNames:
                filePath = os.path.join(config_app_path,fileName)
                import shutil
                shutil.copy(filePath,config_master_path)
        print 'Done'
        sys.exit(0)

    testing = False
    if '--testing' in sys.argv and not getattr(sys,"frozen",None):
        print 'Starting PROSAFE in testing mode'
        testing = True

    localhost = False
    if '--localhost' in sys.argv and not getattr(sys,"frozen",None):
        print 'Starting PROSAFEMaster in localhost mode'
        localhost = True
    

    createmasterfile = False
    if '--createmasterfile' in sys.argv and not getattr(sys,"frozen",None):
        print 'Creating master file'
        createmasterfile = True
    

    nosynch = False
    if '--nosynch' in sys.argv:
        print 'Starting PROSAFEMaster with synchronization switched off'
        nosynch = True

    app = PSApp(redirect=False,flags={'testing':testing,'localhost':localhost,'nosynch':nosynch,'createmasterfile':createmasterfile})
    #from mainlogic import _
    #inspection tool (debug)
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()

