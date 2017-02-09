from login import LoginDialog
from login import ActivationDialog
from psbrowser import PSBrowser
from pseditor import PSEditor
from psuserprefs import PSUserPrefs
from psusermanager import PSUserManager
from pspwdchanger import PSPwdChanger
from psgcpconfig import PSGcpConfig
from psfieldscustomizer import PSFieldsCustomizer
from psadmissiondialog import PSAdmissionDialog
from psexportgroupchooser import PSExportGroupChooser
from psexporter import PSExporter
import psconstants as psc
from psversion import PROSAFE_VERSION
from psdischargeletter import PSDischargeLetter
from psdischargeletter2 import PSDischargeLetterDialog
from psdischargeletter2 import PSDischargeLetterModelDialog
from psadmissionsupdate import PSAdmissionsUpdate
from pspopupmenu import transientPopup
from pscustomizer import PSFieldCustomizer
from psimportdatabrowser import ImportDataBrowserDialog
from psnotification import PSNotification
from psnotificationviewer import PSNotificationViewer 
from psscriptviewer import ProsafeScriptViewer
from pslogging import PsLogger
import datetime
import os
import wx
import sys
from threading import Thread
import time
from timesleep import TimeSleep
from psquickcompilationpages import PSQuickCompilationPagesChooser

from psmessagedialog import PSMessageDialog
from psprogressbar import PSProgressBar
from psrestordeleted import PSRestorableDeleted


class ShutDownConsentFrame(wx.Frame):

    def __init__(self,*args,**kwargs):

        if 'callback' not in kwargs:
            raise Exception('Error: No callback provided!')

        self.callback = kwargs.pop('callback')

        wx.Frame.__init__(self,*args,**kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        from mainlogic import _
        label = wx.StaticText(self,-1,_("PROSAFE needs to restart."))
        sizer.Add(label,0,wx.ALIGN_CENTRE|wx.ALL,10)
        #label = wx.StaticText(self,-1,_("Please complete current operations and press the OK button within the next minute."))
        label = wx.StaticText(self,-1,_("Press the OK button and complete current operations within the next minute."))
        sizer.Add(label,0,wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT|wx.BOTTOM,10)

        okButton = wx.Button(self,wx.ID_OK)
        okButton.Bind(wx.EVT_BUTTON,self.onOK)
        sizer.Add(okButton,0,wx.ALIGN_CENTRE|wx.ALL,10)

        self.Fit()

    def onOK(self,event):
        self.callback()
        self.Destroy()
    

class MainController(object):

    def __init__(self, mainLogic):
        self.mainLogic = mainLogic
        self.loginErrors = 0
        self.root = None
        self.login = None
        self.mainLogic.notificationCenter.addObserver(self,self.onMasterMustShutdown,"MasterMustShutDown")
        self.mainLogic.notificationCenter.addObserver(self,self.onMasterShutdown,"MasterIsShuttingDown")
        self.mainLogic.notificationCenter.addObserver(self,self.clientQuit,"ClientShouldQuit")
        self.mainLogic.notificationCenter.addObserver(self,self.masterClientQuit,"MasterClientShouldQuit")
        self.mainLogic.notificationCenter.addObserver(self,self.doSaveAdmission,"NeedSaveWithBusyInfo")
        
        if 'notification' in psc.toolBarApplications:
            self.mainLogic.notificationCenter.addObserver(self,self.fetchServerMessages,'ServerMessagesAvailable')
        self.mustShutDownRequestReceived = False
        self.shutDownRequestReceived = False
        self.shouldStopThreads = False
        self.shouldAskPermissionIfMaster = True
        self.sortColumn = 1
        self.sortAscending = 0
        self.lastAdmissionKey = ""  
        self.tbList = []        
      
      
    def setBaloonTip(self, target, isLoggingIn, text, title="GiViTI Alert", priority='high', admissionIds=None):
        if not isLoggingIn or not text or not title:
            return
        tb = PSNotification(target, text, title, priority, admissionIds, self.showEditor, self.showNotificationCallback)
        self.tbList.append(tb)
        tb.Play()
        return
        
    def waitUntilCriticalSection(self, callback):
        time.sleep(10)
        while self.mainLogic.inCriticalSection():
            time.sleep(0.1)
        wx.CallAfter(callback)

    def consentToShutDownMaster(self):
        print 'OKToShutDownMaster'
        self.mainLogic.bulletinClient.postNotificationOnBulletin("OKToShutDownMaster")        
        if self.shouldStopThreads:
            print 'Stopping threads'
            self.mainLogic.shutDownThreads()
            time.sleep(1.0)

    def onMasterMustShutdown(self, notifyingObject, userInfo=None):
        if self.mustShutDownRequestReceived or self.mainLogic.isMaster:
            return
        self.mustShutDownRequestReceived = True
        wx.CallAfter(self.doQuit)

    def onMasterShutdown(self, notifyingObject, userInfo=None):
        if self.shutDownRequestReceived:
            return
        if self.mainLogic.isMaster and not self.shouldAskPermissionIfMaster:
            self.shutDownRequestReceived = True
            self.mainLogic.bulletinClient.postNotificationOnBulletin("OKToShutDownMaster")
            return
        self.shutDownRequestReceived = True
        wx.CallAfter(self.masterShutdownCallback)

    def consentToShutDownCallback(self):
        waitThread = Thread(target=self.waitUntilCriticalSection,args=(self.consentToShutDownMaster,))
        waitThread.start()

    def masterShutdownCallback(self):
        from mainlogic import _
        wx.MessageBox(_("PROSAFE needs to restart.\n\nComplete current operations within the next 10 seconds after pressing the button."),_("WARNING"))
        self.consentToShutDownCallback()

        
    def showJsonMigrationProgressBar(self, migrateToStoreCallback):
        from mainlogic import _
        from psprogressbar import PSProgressBar
        print 'progressing'
        jsonstoreProgressBar = PSProgressBar(None, max=100)
        jsonstoreProgressBar.max = 1000
        jsonstoreProgressBar.StartProgressBar(title=_("MIGRATING"))
        print 'starting'
        #jsonstoreProgressBar.Step(stepValue=50, message=_('Loading patients'))
        'migrating'
        result = migrateToStoreCallback(jsonstoreProgressBar)
        'after migration'
        if result:
            jsonstoreProgressBar.Stop(message = _('FINISHED!'))
            return True
        else:
            jsonstoreProgressBar.Stop(message = _('ABORTED!'))
            return False
            
        
    def showActivation(self):
        
        if not self.mainLogic.checkActivation() or not self.mainLogic.masterFileExists():
            if self.mainLogic.testing:
                if not self.mainLogic.masterFileExists():
                    self.mainLogic.createMasterFile()
                #self.mainLogic.isMaster = None
                self.mainLogic.attemptBecomeMaster()
                if not self.mainLogic.loadAppdata():
                    self.mainLogic.createAppdata('IT999')
                    self.mainLogic.loadAppdata()
                elif not self.mainLogic.checkActivation():
                    self.mainLogic.reactivate('IT999')
                self.mainLogic.loadConfig()
                return
            activationDialog = ActivationDialog(None,self.doVerifyActivationCode, self.showImportMasterDataDialog)
            activationDialog.Center()
            activationDialog.ShowModal()
            if not activationDialog.centrecode:
                self.doQuit() 
            else:
                from mainlogic import _
                busyInfo = wx.BusyInfo(_("Initializing PROSAFE"),None)
                self.mainLogic.createMasterFile()
                self.mainLogic.attemptBecomeMaster()
                if not self.mainLogic.loadAppdata():
                    self.mainLogic.createAppdata(activationDialog.centrecode)
                    self.mainLogic.loadAppdata()
                else:
                    self.mainLogic.reactivate(activationDialog.centrecode)
                    self.mainLogic.loadAppdata()
                self.mainLogic.loadConfig()
                del busyInfo

    def doVerifyActivationCode(self, centreCode, activationKey):
        return self.mainLogic.networkManager.verifyActivationCode(centreCode,activationKey)
        
    def showImportMasterDataDialog(self):
        ImportDataBrowser = ImportDataBrowserDialog(None, self.importDataFromPackageCallback)
        ImportDataBrowser.Center()
        ImportDataBrowser.ShowModal()
        return ImportDataBrowser.getImportStatus()
        
    def importDataFromPackageCallback(self, packagePath):
        result = self.mainLogic.importDataFromPackage(packagePath)        
        from mainlogic import _
        message = _("data restore failed - is this the original masterdata.zip?")
        if type(result) == str:
            message = result
        icon = wx.ICON_ERROR
        if result == True:
            message = _("data restored succesfully!")
            icon = wx.ICON_INFORMATION
        dlg = wx.MessageDialog(None, message, _("Data restore"), wx.OK | icon)
        dlg.Center()
        dlg.ShowModal()
        return result
        
    def showLogin(self):
        if self.root:
            self.root.Destroy()
            self.root = None
        if self.login:
            self.login.Destroy()
        self.mainLogic.loadAppTranslations(self.mainLogic.userLanguage)
        from mainlogic import _
        if self.mainLogic.masterIsMigrating and self.mainLogic.isMaster == False:
            dlg = wx.MessageDialog(None, _("Prosafe MASTER is now busy. Please try again later"), _("Warning"), wx.OK | wx.ICON_WARNING)
            dlg.Center()
            dlg.ShowModal()
            sys.exit(0)
        self.login = LoginDialog(None,self.doLogin,self.doQuit,self.doRequestNewPassword, self.mainLogic.isMaster, self.mainLogic.getCentreCode)
        self.login.Center()
        self.login.Show()
        self.login.Raise()
        self.login.SetFocus()

    def setFrameAsRoot(self,frame):
        if self.root == None or self.root == frame or self.root.IsMaximized():
            frame.Maximize()
        else:
            frame.SetSize(self.root.GetSize())   
            frame.SetPosition(self.root.GetPosition())   
        self.root = frame
        
    def quickCompilationSelectionCallback(self,returnPage=False):
        if returnPage:
            return self.mainLogic.quickCompilationMode
        chosenPage = ''
        if self.mainLogic.quickCompilationMode:
            chosenPage = self.mainLogic.quickCompilationMode
        chosePage = PSQuickCompilationPagesChooser(self.browser, self.quickCompilationPagesCallback, self.mainLogic.userLanguage, self.mainLogic.quickCompilationMode)
        chosePage.Center()
        result = chosePage.ShowModal()
        if result == wx.ID_OK:
            wx.BeginBusyCursor()
            chosenPage = chosePage.getChosenPage()
        else:
            wx.BeginBusyCursor()
        if self.mainLogic.quickCompilationMode != chosenPage:
            self.mainLogic.quickCompilationMode = chosenPage
            self.mainLogic.refreshGridData()
            self.browser.populateList() 
            self.browser.Update()
            self.changeToolbarToolIcon()
        wx.EndBusyCursor()
        return chosenPage
        
    def changeToolbarToolIcon(self):
        imageName = 'quick.png'
        if self.mainLogic.quickCompilationMode != '':            
            imageName = 'quickActive.png'            
        bmp = wx.Image(os.path.join(psc.imagesPath, imageName),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.browser.tool_quick.SetNormalBitmap(bmp)
        self.browser.toolbar.Realize()
            
    def changeNotificationToolbarToolIcon(self):
        messages = self.getServerMessages(True, True, False)
        imageName = 'notification.png'
        if messages:
            imageName = 'newnotification.png'
        bmp = wx.Image(os.path.join(psc.imagesPath, imageName),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        if messages:
            self.drawNumber = len(messages)
            bmp = self.drawNotificationNumberOnIcon(len(messages), bmp)
        self.browser.tool_notification.SetNormalBitmap(bmp)
        self.browser.toolbar.Realize()
        
    def drawNotificationNumberOnIcon(self, number, originalbmp):
        image = originalbmp.ConvertToImage()
        image.ConvertAlphaToMask()
        originalbmp = image.ConvertToBitmap()
        dc = wx.MemoryDC()
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetTextForeground(wx.RED)
        dc.SelectObject(originalbmp)
        #dc.SetPen(wx.BLACK_PEN)
        font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        dc.SetFont(font)
        dc.DrawText(str(number), 24, 24)
        dc.SelectObject(wx.NullBitmap)
        return originalbmp

    def showBrowser(self, firstLogin=False, isLoggingIn=False):
    
        from mainlogic import _
        clientMasterString = "Client"
        if self.mainLogic.isMaster:
            clientMasterString = "Master"
        isOnline = self.mainLogic.networkManager.couldConnect()
        onlineOfflineString = "Offline"
        if isOnline:
            onlineOfflineString = "Online"

        self.browser = PSBrowser(None,-1,"PROSAFE %s (%s) - %s" % (clientMasterString, onlineOfflineString, _("Browser")),self.mainLogic.userType,self.mainLogic.getCentreCode(),self.filtersCallback,self.quickFiltersCallback,self.petalsCallback,self.exportDataCallback,self.exportDataOverviewCallback,self.uploadDBCallback,self.gridDataCallback,self.admissionsToEvaluateCallback,self.statsCallback,self.openAdmissionCallback,self.newAdmissionCallback,self.quickCompilationCallback,self.quickCompilationPagesCallback,self.showUserPrefs,self.showUserManager,self.proxyCallback,self.testConnectionCallback,self.privateKeyCallback,self.setPrivateKeyCallback,self.dischargeLetterModelCallback,self.doClose,self.doLogout,self.showHelp,self.showAbout,self.quickCompilationSelectionCallback,self.printCallback,self.showConfigurationCallback,self.showCustomizationEditor,self.onExportMappingCallback,self.moveMasterConfigurationCallback,self.showNotificationCallback,firstLogin=firstLogin,shouldAnonymizeData=self.mainLogic.shouldAnonymizeData)

        self.setFrameAsRoot(self.browser)
        
        self.browser.Freeze()
        self.mainLogic.notificationCenter.addObserver(self,self.onAdmissionsUpdated,"AdmissionsHaveBeenUpdated")
        self.onAdmissionsUpdated(self)
        self.browser.sortList(self.sortColumn,self.sortAscending)
        self.browser.selectItem(self.lastAdmissionKey)
        self.browser.Thaw()
        self.browser.Show()
        
        if not isOnline and isLoggingIn:
            warningText = _("Warning! PROSAFE is currently Offline.\nAs such, PROSAFE cannot update or transmit data to the GiViTI Coordinating Centre.")
            if self.mainLogic.userType == psc.USER_ADMIN:
                warningText += '\n\n' + _("Verify that the Internet connection settings in the Administration, Proxy settings menu are correct.\nPlease contact the Coordinating Centre +390354535313 for further support.")
            else:
                warningText += '\n\n' + _("Contact your PROSAFE Administrator to check that the Internet connection settings in the Administration, Proxy settings menu are correct.\nPlease contact the Coordinating Centre +390354535313 for further support.")
            dlg = wx.MessageDialog(None, warningText, _("Offline Warning"), wx.OK | wx.ICON_WARNING)
            dlg.Center()
            dlg.ShowModal()
        if 'notification' in psc.toolBarApplications:
            messages = self.getServerMessages(updateMessageList=True)
            if messages or messages == []:
                self.mainLogic.notificationCenter.postNotification("ServerMessagesAvailable",self)
                self.changeNotificationToolbarToolIcon()
                
    def quickCompilationPagesCallback(self,crfName=None,crfVersions=None,admissionDate=None):
        if admissionDate == None:
            return self.mainLogic.quickCompilationPages
        validVersion = self.mainLogic.getCrfValidVersion(crfName,admissionDate)
        if validVersion not in crfVersions:
            return False
        return True

    def printCallback(self):
        from mainlogic import _
        
        if not self.mainLogic.gridData:
            dlg = wx.MessageDialog(None, _("No patient selected."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        userPath = os.path.expanduser('~')
        if userPath == '~' or not os.path.exists(userPath):
            userPath = os.cwd()
        dlg = wx.FileDialog(None, _("Save location"), userPath, "", "*.csv", wx.SAVE)
        path = ''
        wx.BeginBusyCursor()
        if dlg.ShowModal() != wx.ID_OK:
            wx.EndBusyCursor()
            return
        path = dlg.GetPath()
        if not path:
            wx.EndBusyCursor()
            return
        wx.EndBusyCursor()

        wx.BeginBusyCursor()
        result = self.mainLogic.exportCurrentAdmissionsList(path)
        wx.EndBusyCursor()
        if result == True:
            dlg = wx.MessageDialog(None, _("Data has been successfully exported."), _("Success"), wx.OK)
            dlg.Center()
            dlg.ShowModal()
        elif result == False:
            dlg = wx.MessageDialog(None, _("Data export failed."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
        
    def exportDataCallback(self):
        from mainlogic import _
        #self.nonSupportedFeautureDialog(_("ANALYZER_FOR_NOT_SUPPORTED_FEAUTURE"))
        #return
        dlg = wx.MessageDialog(None, _("WARNING_EXPORT"), _("Warning"), wx.YES_NO | wx.ICON_WARNING)
        dlg.Center()
        result = dlg.ShowModal()
        if result != wx.ID_YES:
            return
        if not self.mainLogic.gridData:
            dlg = wx.MessageDialog(None, _("No patient selected."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        userPath = os.path.expanduser('~')
        if userPath == '~' or not os.path.exists(userPath):
            userPath = os.cwd()
        dlg = wx.FileDialog(None, _("Save location"), userPath, "", "*.csv", wx.SAVE)
        path = ''
        wx.BeginBusyCursor()
        if dlg.ShowModal() != wx.ID_OK:
            wx.EndBusyCursor()
            return
        path = dlg.GetPath()
        if not path:
            wx.EndBusyCursor()
            return
        wx.EndBusyCursor()
        admissionsToUpdate = self.mainLogic.checkCrfVersionOfAdmissions()
        if admissionsToUpdate:
            dlg = wx.MessageDialog(None, _("Cannot export data while admissions are being updated."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        #wx.BeginBusyCursor()
        from psprogressbar import PSProgressBar
        overviewProgressBar = PSProgressBar(self.root, max=100)
        result = self.mainLogic.exportData(path,self.chooseGroupsCallback,self.GroupCrfCallback,overviewProgressBar)
        #wx.EndBusyCursor()
        #if result == True:
        #    dlg = wx.MessageDialog(None, _("Data has been successfully exported."), _("Success"), wx.OK)
        #    dlg.Center()
        #    dlg.ShowModal()
        #elif result == False:
        #    dlg = wx.MessageDialog(None, _("Data export failed."), _("ERROR"), wx.OK | wx.ICON_ERROR)
        #    dlg.Center()
        #    dlg.ShowModal()
            
    def exportDataOverviewCallback(self):
        from mainlogic import _
        self.nonSupportedFeautureDialog(_("ANALYZER_FOR_NOT_SUPPORTED_FEAUTURE"))
        return
        dlg = wx.MessageDialog(None, _("WARNING_EXPORT"), _("Warning"), wx.YES_NO | wx.ICON_WARNING)
        dlg.Center()
        result = dlg.ShowModal()
        if result != wx.ID_YES:
            return
        if not self.mainLogic.gridData:
            dlg = wx.MessageDialog(None, _("No patient selected."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        #opening dialog for determinig destination filename
        admissionsToUpdate = self.mainLogic.checkCrfVersionOfAdmissions()
        
        if admissionsToUpdate:
            dlg = wx.MessageDialog(None, _("Cannot export data while admissions are being updated."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        #else:
        #    dlg = wx.MessageDialog(None, _("Overview table advice"), _("Get overview table"), wx.OK | wx.ICON_EXCLAMATION)
        #    dlg.Center()
        #    dlg.ShowModal()
        
        userPath = os.path.expanduser('~')
        if userPath == '~' or not os.path.exists(userPath):
            userPath = os.cwd()
        dlg = wx.FileDialog(None, _("Save location"), userPath, "", "*.xls", wx.SAVE)
        path = ''
        if dlg.ShowModal() != wx.ID_OK:
            return
        path = dlg.GetPath()
        if not path:
            return
        
        #adding datetime to filename
        basename = path.split('.xls')[0]
        now = datetime.datetime.now()
        timestamp = now.strftime("__%d_%m_%y__%H_%M")
        path = basename + timestamp + ".xls"

        from psprogressbar import PSProgressBar
        overviewProgressBar = PSProgressBar(self.root, max=100)
        
        #result = self.mainLogic.exportData(path,self.chooseGroupsCallback)
        #busyInfo = wx.BusyInfo(_("Generating overview table"),self.root)
        
        
        result = self.mainLogic.exportDataOverview(path,self.chooseGroupsOverviewCallback,self.dic_tmp_crf, overviewProgressBar)
        
            
            
        #del busyInfo

        #if result == True:
        #    dlg = wx.MessageDialog(None, _("Data has been successfully exported."), _("Success"), wx.OK)
        #    dlg.Center()
        #    dlg.ShowModal()
        #elif result == False:
        #    dlg = wx.MessageDialog(None, _("Data export failed."), _("ERROR"), wx.OK | wx.ICON_ERROR)
        #    dlg.Center()
        #    dlg.ShowModal()
            
    def onExportMappingCallback(self):
        from mainlogic import _
        if not self.mainLogic.gridData:
            dlg = wx.MessageDialog(None, _("No patient selected."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        #opening dialog for determinig destination filename
        admissionsToUpdate = self.mainLogic.checkCrfVersionOfAdmissions()
        
        if admissionsToUpdate:
            dlg = wx.MessageDialog(None, _("Cannot export data while admissions are being updated."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        
        path = 'file.txt'
        #adding datetime to filename
        basename = path.split('.txt')[0]
        now = datetime.datetime.now()
        timestamp = now.strftime("__%d_%m_%y__%H_%M")
        path = basename + timestamp + ".txt"

        #result = self.mainLogic.exportData(path,self.chooseGroupsCallback)
        busyInfo = wx.BusyInfo(_("Generating overview table"),self.root)
        previousFilterAdmissionYear = self.mainLogic.quickFilters['AdmissionYear']
        #self.mainLogic.quickFilters['AdmissionYear'] = '2011'
        result = self.mainLogic.mapData(self.chooseGroupsOverviewCallback)
        self.mainLogic.quickFilters['AdmissionYear'] = previousFilterAdmissionYear
        del busyInfo

        if result == True:
            dlg = wx.MessageDialog(None, _("Data has been successfully exported."), _("Success"), wx.OK)
            dlg.Center()
            dlg.ShowModal()
        elif result == False:
            dlg = wx.MessageDialog(None, _("Data export failed."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
        
    def dic_tmp_crf(self, dictemp):
        return dictemp
        
        
    def chooseGroupsOverviewCallback(self,groupsToTitles):
        return groupsToTitles.keys()
        
        
    def GroupCrfCallback(self, var):
        self.crfGroupList = var
       
    
    def chooseGroupsCallback(self,groupsToTitles):
        chosenGroups = []
        groupChooser = PSExportGroupChooser(self.browser,groupsToTitles, self.crfGroupList)
        groupChooser.Center()
        result = groupChooser.ShowModal()
        if result == wx.ID_OK:
            chosenGroups = groupChooser.getChosenGroups()
        return chosenGroups

    def petalsCallback(self):
        petalNames = self.mainLogic.getAppdataCrfNames()
        petalNames.remove(psc.coreCrfName)
        petalNames.sort()
        return petalNames

    def admissionsToEvaluateCallback(self,gridData):
        return self.mainLogic.checkCrfVersionOfAdmissions(gridData)

    #def updateAdmissionsCallback(self, admissionsToUpdate, progressCallback):
    #    updateThread = Thread(target=self.doUpdateAdmissions,args=(admissionsToUpdate,progressCallback))
    #    updateThread.start()

    #def stopUpdateAdmissionsCallback(self):
    #    self.updateAdmissionsThreadShouldStop = True

    #def doUpdateAdmissions(self, admissionsToUpdate, progressCallback):
    #    self.updateAdmissionsThreadShouldStop = False
    #    for i, admissionKey in enumerate(admissionsToUpdate):
    #        if self.updateAdmissionsThreadShouldStop:
    #            break
    #        self.mainLogic.openSaveAndCloseAdmission(admissionKey)
    #        progressCallback(i,len(admissionsToUpdate))
    #    wx.CallAfter(self.browser.refreshList)

    def resetDischargeLetterModelCallback(self):
        self.mainLogic.backupDischargeLetterModel()
        self.mainLogic.getDischargeLetterModelBackupFromMaster()

    def resetDischargeLetterCallback(self):
        self.mainLogic.backupDischargeLetter()
        self.mainLogic.getDischargeLetterFromMaster(forceGetModel=True)

    def undoResetDischargeLetterModelCallback(self):
        self.mainLogic.restoreDischargeLetterModelBackup()

    def undoResetDischargeLetterCallback(self):
        self.mainLogic.restoreDischargeLetterBackup()

    def oldDischargeLetterModelCallback(self):
        self.dischargeLetterModelCallback(oldSystem=True)

    def oldDischargeLetterCallback(self):
        self.dischargeLetterCallback(oldSystem=True)

    def dischargeLetterModelCallback(self, oldSystem=False):

        if not oldSystem:
            self.dischargeLetter2ModelCallback()
            return

        cursor = wx.BusyCursor()
        filename = self.mainLogic.getDischargeLetterModelFilePath()
        self.mainLogic.getDischargeLetterModelFromMaster()

        self.mainLogic.loadCrfs(self.mainLogic.getDate())

        from mainlogic import _
        dischargeLetter = PSDischargeLetter(self.root,title=_("Discharge letter model"),filename=filename,mainLogic=self.mainLogic,editModel=True,resetCallback=self.resetDischargeLetterModelCallback,undoResetCallback=self.undoResetDischargeLetterModelCallback,style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        size = self.root.GetSize()
        dischargeLetter.SetSize((min(size[0]-100,800),size[1]-100))
        dischargeLetter.Center()
        dischargeLetter.MakeModal()
        dischargeLetter.Show()
        dischargeLetter.Bind(wx.EVT_CLOSE,self.onDischargeLetterModelClose)
        del cursor

    def dischargeLetterCallback(self, oldSystem=False):

        if not oldSystem:
            self.dischargeLetter2Callback()
            return

        cursor = wx.BusyCursor()
        filename = self.mainLogic.getDischargeLetterFilePath()
        self.mainLogic.getDischargeLetterFromMaster()

        from mainlogic import _
        dischargeLetter = PSDischargeLetter(self.root,title=_("Discharge letter"),filename=filename,mainLogic=self.mainLogic,resetCallback=self.resetDischargeLetterCallback,undoResetCallback=self.undoResetDischargeLetterCallback,style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        size = self.root.GetSize()
        dischargeLetter.SetSize((min(size[0]-100,800),size[1]-100))
        dischargeLetter.Center()
        dischargeLetter.MakeModal()
        dischargeLetter.Show()
        dischargeLetter.Bind(wx.EVT_CLOSE,self.onDischargeLetterClose)
        del cursor

    def onDischargeLetterModelClose(self, event):
        event.GetEventObject().MakeModal(False)
        self.mainLogic.putDischargeLetterModelToMaster()
        event.Skip()

    def onDischargeLetterClose(self, event):
        event.GetEventObject().MakeModal(False)
        self.mainLogic.putDischargeLetterToMaster()
        event.Skip()

    def dischargeLetter2ModelCallback(self):
        letterModelDialog = PSDischargeLetterModelDialog(self.root,self.getLetterModelCallback,self.copyLetterMasterModelCallback,self.getLetterMasterModelFileNamesCallback,self.getNewLetterModelFileNameCallback,self.oldDischargeLetterModelCallback,self.closeLetterModelCallback, self.getFormatsAndDescriptionCallback)
        letterModelDialog.Center()
        letterModelDialog.MakeModal()
        letterModelDialog.Show()
        letterModelDialog.Bind(wx.EVT_CLOSE,self.onDischargeLetter2Close)

    def dischargeLetter2Callback(self):
        try:
            result = self.mainLogic.getLetterModelFileNames(format=None)
        except:
            result = None
        if result:
            flg = False
            for key in result.keys():
                if result[key]:
                    flg = True
            if not flg:
                result = None
        if not result:
            from mainlogic import _
            dlg = wx.MessageDialog(None, 
                    _("No model was found. Please contact your PROSAFE administrator."),
                    _("Warning"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.Center()
            dlg.ShowModal()
            return
        majorNumber = self.mainLogic.crfData.getPropertyForCrf('core','version').split('.')[0]
        if int(majorNumber) < 3:
            result = None
            from mainlogic import _
            dlg = wx.MessageDialog(None, 
                    _("Remember you cannot use the new PROSAFE discharge letter with patient admitted before 2011-09-07"),
                    _("Warning"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.Center()
            dlg.ShowModal()
        letterDialog = PSDischargeLetterDialog(self.root,self.getLetterCallback,self.composeLetterCallback,self.getLetterModelFileNamesCallback,self.getNewLetterFileNameCallback,self.oldDischargeLetterCallback,self.closeLetterCallback, self.showNotesForDischargeLetterCallback, newSystemEnabled = result)
        letterDialog.Center()
        letterDialog.MakeModal()
        letterDialog.Show()
        letterDialog.Bind(wx.EVT_CLOSE,self.onDischargeLetter2Close)

    def showNotesForDischargeLetterCallback(self):
        self.editor.rightPanel.guiGenerator.showPage(psc.coreCrfName,psc.dischargeLetterNotesPageName)
        self.mainLogic.notificationCenter.postNotification("PageHasChanged",self)
        
    def onDischargeLetter2ModelClose(self, event):
        event.GetEventObject().MakeModal(False)
        event.Skip()

    def onDischargeLetter2Close(self, event):
        event.GetEventObject().MakeModal(False)
        event.Skip()

    def getLetterModelCallback(self):
        cursor = wx.BusyCursor()
        self.mainLogic.openLetterModelFolder(show=True)
        del cursor

    def getLetterCallback(self):
        cursor = wx.BusyCursor()
        self.mainLogic.openLetterFolder(show=True)
        del cursor

    def getLetterMasterModelFileNamesCallback(self, format=None):
        return self.mainLogic.getLetterMasterModelFileNames(format=None)

    def getNewLetterModelFileNameCallback(self, format, modelName, userModelName):
        return self.mainLogic.getNewLetterModelFileName(format, modelName, userModelName)

    def getLetterModelFileNamesCallback(self, format=None):
        return self.mainLogic.getLetterModelFileNames(format=None)

    def getNewLetterFileNameCallback(self, format, letterName):
        return self.mainLogic.getNewLetterFileName(format, letterName)

    def copyLetterMasterModelCallback(self, masterModelFileName, modelFileName):
        cursor = wx.BusyCursor()
        self.mainLogic.copyLetterMasterModel(masterModelFileName,modelFileName)
        del cursor
        
    def getFormatsAndDescriptionCallback(self):
        return self.mainLogic.getFormatsAndDescription()

    def composeLetterCallback(self, modelFileName, letterFileName):
        cursor = wx.BusyCursor()
        self.mainLogic.composeLetter(modelFileName,letterFileName)
        self.mainLogic.openLetterFolder(show=True)
        del cursor

    def closeLetterCallback(self):
        cursor = wx.BusyCursor()
        self.mainLogic.closeLetterFolder()
        del cursor

    def closeLetterModelCallback(self):
        cursor = wx.BusyCursor()
        self.mainLogic.closeLetterModelFolder()
        del cursor

    def destroyBrowser(self):
        if self.root == self.browser:
            self.root = None
        self.sortColumn, self.sortAscending = self.browser.getSortStatus()
        self.browser.Destroy()
        self.mainLogic.notificationCenter.removeObserver(self,"AdmissionsHaveBeenUpdated")

    def quickFiltersCallback(self, quickFilters=None):
        if quickFilters == None:
            return self.mainLogic.quickFilters
        self.mainLogic.setQuickFilters(quickFilters)
        self.mainLogic.notificationCenter.postNotification("AdmissionsHaveBeenUpdated",self)

    def filtersCallback(self, filters=None):
        if filters == None:
            return self.mainLogic.filters
        self.mainLogic.filters = filters
        self.mainLogic.notificationCenter.postNotification("AdmissionsHaveBeenUpdated",self)

    def gridDataCallback(self):
        return self.mainLogic.getGridData()
 
    def statsCallback(self):
        return self.mainLogic.getStats()

    def openAdmissionCallback(self, admissionData):
        print 'admissionData for openAdmissionCallback:', admissionData
        self.showEditor(admissionData)
 
    def newAdmissionCallback(self):
        self.showEditorNew()
 
    def showPageCallback(self):
        pass

    def quickCompilationCallback(self, data, crfName, pageName):
        from psdialogpanel import PSDialogPanel
        from mainlogic import _
        import psevaluator 
        firstdatakrey = data['admissionKey']
        shouldOpenNextAdmission = True
        gridData = self.mainLogic.getGridData()
        while shouldOpenNextAdmission:
            result = self.mainLogic.loadAdmission(data['admissionKey'])
            #TODO: make this project-independent
            title = unicode(data['core.lastName.lastName']) + ' ' + unicode(data['core.firstName.firstName']) + _("  Admitted: ") + psevaluator.decodevalue(data['core.icuAdmDate.icuAdmDate'])
            self.quickCompilationFrame = wx.Dialog(self.browser,-1,title)
            dialogPanel = PSDialogPanel(self.quickCompilationFrame,self.mainLogic,self.showPageCallback, data)
            dialogPanel.showPage(crfName,pageName)
            dialogPanel.Layout()
            self.quickCompilationFrame.SetSize((dialogPanel.GetSizer().GetMinSize()[0]+250,self.browser.GetSize()[1]-250))
            self.quickCompilationFrame.Center()
            result = self.quickCompilationFrame.ShowModal()
            
            shouldOpenNextAdmission = dialogPanel.shouldOpenNextAdmission
            if shouldOpenNextAdmission:
                self.mainLogic.saveData()
                # gridData = self.mainLogic.getGridData()
                for elt in range(len(gridData)):
                    k=elt+1
                    if data['admissionKey'] == gridData[elt]['admissionKey']:
                        if k <= max(range(len(gridData))):
                            data = gridData[k]
                        else:
                            data=gridData[0]
                        break
                if firstdatakrey == data['admissionKey']:
                    shouldOpenNextAdmission = False
                else:
                    self.mainLogic.exitAdmission()
        wx.BeginBusyCursor()
        if result == wx.ID_OK:
            self.mainLogic.saveData()
        
        self.lastAdmissionKey = self.mainLogic.dataSession.admissionKey
        
        if dialogPanel.shouldOpenAdmission == True:
            self.showEditor(None)
        else:
            self.mainLogic.refreshGridData()
            self.mainLogic.exitAdmission()
        self.browser.populateList()
        self.browser.Update()            
        
        wx.EndBusyCursor()

    def onAdmissionsUpdated(self, notifyingObject, userInfo=None):
        self.mainLogic.refreshGridData()
        self.browser.populateList() 
        self.browser.Update()
        
    def destroyBaloons(self):
        for tb in self.tbList:
            try:
                tb.GetToasterBoxWindow().NotifyTimer(None)
                tb.Destroy()
            except BaseException, e:
                print 'baloon error', e
                PsLogger().warning(['MainControllerTag','ExceptionTag'], str(e))
                pass
        self.tbList = []
 
    def showEditor(self, data):
        self.destroyBaloons()
        from mainlogic import _

        if data:
            busyInfo = wx.BusyInfo(_("Loading admission"),self.root)
            result = self.mainLogic.loadAdmission(data['admissionKey'])
            del busyInfo

            if result == False:
                dlg = wx.MessageDialog(None, 
                    _("This admission is already open on another ProSafe client."),
                    _("Load Admission Error"), wx.OK | wx.ICON_ERROR)
                dlg.Center()
                dlg.ShowModal()
                return
        
        self.editor = PSEditor(None, -1, _("Editor"), self.mainLogic, self.mainLogic.userType, self.doSaveAdmission, self.doCloseAdmission, self.doDeleteAdmission, self.doReopenAdmission, self.basedataCallback, self.statusCallback, self.updateStatusCallback, self.errorsCallback, self.showUserPrefs, self.dischargeLetterCallback, self.doCloseEditor, self.showHelp, self.showAbout, self.showGcpViewer)
        self.editor.Freeze()
        self.setFrameAsRoot(self.editor)
        self.editor.showInfoInConsolePanel()
        self.editor.showCoreSummaryPage()
        self.editor.refreshMenu()
        self.editor.Thaw()
        self.editor.Show()
        self.editor.ensureLeftPanelVisibility()
        self.destroyBrowser() 
        #self.root = self.editor

        
    def confirmEditedDataForGcp(self):
        changedAttributes = self.mainLogic.getGcpChangedAttributes(removeFirstSave=True)
        if not changedAttributes or not self.mainLogic.gcpActive:
            return
        from psgcpdialog import PSGcpDialog
        size = self.root.GetSize()
        size.width = size.width * 7 / 10
        size.height = size.height * 7 / 10
        userKey = self.mainLogic.getGcpUserDataFromUserKey(self.mainLogic.inputUserKey)
        gcpDialog = PSGcpDialog(self.root,self.confirmGcp,changedAttributes,inputUserKey=userKey,size=size)
        gcpDialog.Center() 
        gcpDialog.Show()
        
    def showGcpViewer(self):
        gcpEdits = self.mainLogic.translateClassForGcpViewerData()
        from psgcpdialog import PSGcpDialog
        size = self.root.GetSize()
        size.width = size.width * 7 / 10
        size.height = size.height * 7 / 10
        userKey = self.mainLogic.getGcpUserDataFromUserKey(self.mainLogic.inputUserKey)
        gcpDialog = PSGcpDialog(self.root,self.confirmGcp,gcpEdits,isReadOnly=True,inputUserKey=userKey,size=size)
        
        gcpDialog.Center() 
        gcpDialog.Show()
        
    def confirmGcp(self, confirmResult):
        self.mainLogic.resetChangedAttributes(confirmResult)
        self.mainLogic.saveData()
        from mainlogic import _
        wx.MessageBox(_("Data saved."), _("Data saved."))
        #shall save confirm result
        
    def doRequestNewPassword(self):
        secondaryPassword = self.mainLogic.createAdminSecondaryPassword()
        result = self.mainLogic.networkManager.sendSecondaryPasswordToServer(self.mainLogic.centrecode,secondaryPassword)
        return result

    def doSaveAdmission(self,notifyingObject=None):
        if self.mainLogic.gcpActive:
            self.confirmEditedDataForGcp()
        from mainlogic import _
        busyInfo = wx.BusyInfo(_("Saving data"),self.root)
        if notifyingObject:
            self.mainLogic.saveData(False, False, False, False)
        else:
            self.mainLogic.saveData()
        del busyInfo
        if 'notification' in psc.toolBarApplications:
            self.fetchServerMessages(notifyingObject=None, localFetch=True)

    def doCloseAdmission(self, crfs):
        self.mainLogic.closeAdmission(crfs)
        
    def doDeleteAdmission(self):
        from mainlogic import _
        if not self.mainLogic.deleteAdmission():
            dlg = wx.MessageDialog(None,
                                _("Cannot delete parent readmission, please delete before children readmission"),
                                _("Readmission deletion error"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()

    def doReopenAdmission(self, crfs):
        self.mainLogic.reopenAdmission(crfs)

    def basedataCallback(self):
        return self.mainLogic.getCurrentBasedata()

    def statusCallback(self, crfName=None):
        return self.mainLogic.dataSession.getAdmissionStatus(crfName)

    def updateStatusCallback(self):
        return self.mainLogic.updateStatus(computeOnly=True)

    def errorsCallback(self):
        numberOfErrors = self.mainLogic.getTotalNumberOfErrors()
        numberOfUnacceptedWarnings = self.mainLogic.getTotalNumberOfUnacceptedWarnings()
        #TODO: for clarity, report number of errors in core and number of errors
        return {'errors':numberOfErrors, 'warnings':numberOfUnacceptedWarnings}

    def editorToBrowser(self):
        from mainlogic import _
        self.destroyBaloons()
        busyInfo = wx.BusyInfo(_("Closing admission"),self.root)
        self.mainLogic.notificationCenter.addObserver(self,self.onAdmissionsUpdated,"AdmissionsHaveBeenUpdated")
        self.showBrowser()
        del busyInfo

        #if self.editor.IsMaximized():
        #    self.browser.Maximize()
        #else:
        #    self.browser.SetSize(self.editor.GetSize())
        #    self.browser.SetPosition(self.editor.GetPosition())

        #self.onAdmissionsUpdated(self)

        self.editor.Destroy()
        self.browser.listView.selectItem(self.lastAdmissionKey)
        if self.mainLogic.quickCompilationMode:
            self.changeToolbarToolIcon()
        
        #self.mainLogic.notificationCenter.postNotification("AdmissionsHaveBeenUpdated",self)
               
    def showEditorNew(self):
        from mainlogic import _
        adialog = PSAdmissionDialog(self.browser,self.mainLogic)
        adialog.Center()
        result = adialog.ShowModal()
        basedata = adialog.GetData()
        insertAdmission = True
        if result == wx.ID_OK:
            #basedata = self.mainLogic.checkReadmission(basedata)
            #avoiding readmission check for non-prosafe crfs. Should use readmission as tool!
            readmission = False
            patient = True
            if psc.appName == 'prosafe':
                candidates, candidatesHaveBeenRemoved = self.mainLogic.getCandidatesForReadmission(basedata)
                #TODO: cycle for each candidate in candidates or take only first result? 
                if candidates and 'readmission' in psc.toolBarApplications:
                    for candidate in candidates:
                        dlg = wx.MessageDialog(None,
                                        _("Is this patient the same") % (candidate['core.lastName.lastName'], candidate['core.firstName.firstName'], candidate['admissionKey']),
                                        _("Confirm"), wx.YES_NO | wx.ICON_QUESTION)
                        dlg.Center()
                        resultSamePatient = dlg.ShowModal()
                        if resultSamePatient == wx.ID_YES:
                            chosenCandidate = candidate
                            break
                    if resultSamePatient == wx.ID_YES:
                        patient = False
                        basedata['patientKey'] = chosenCandidate['patientKey']
                        #patient recognized as same. Readmission? 
                        if not chosenCandidate['core.hospDisDate.value']:
                            dlg = wx.MessageDialog(None, 
                                                    _("Readmission question"),
                                                    _("Confirm"), wx.YES_NO | wx.ICON_QUESTION)
                            dlg.Center()
                            readmissiondlg = dlg.ShowModal()
                            if readmissiondlg == wx.ID_YES:
                                if chosenCandidate['core.icuDisDate.value']:
                                    readmission = True
                                    basedata['prevAdmissionKey'] = chosenCandidate['admissionKey']
                                else:
                                    insertAdmission = False
                                    dlg = wx.MessageDialog(None, 
                                    _("Admission error: this patient is still present in ICU. Please fill ICU discharge date before adding a new admission for this patient."),
                                    _("Admission Error"), wx.OK | wx.ICON_ERROR)
                                    dlg.Center()
                                    dlg.ShowModal()
                            elif readmissiondlg == wx.ID_NO:
                                dlg = wx.MessageDialog(None, _("Please, do not forget to fill in the hospital discharge data in the previous record of this patient"), 
                                _("Info"), wx.OK | wx.ICON_EXCLAMATION)
                                dlg.Center()
                                dlg.ShowModal()
                            else:
                                insertAdmission = False
                elif candidatesHaveBeenRemoved:
                    dlg = wx.MessageDialog(None, 
                                            _("CANDIDATES_REMOVED_QUESTION"),
                                            _("Confirm"), wx.YES_NO | wx.ICON_QUESTION)
                    dlg.Center()
                    candidatesRemovedDialog = dlg.ShowModal()
                    if candidatesRemovedDialog != wx.ID_YES:
                        insertAdmission = False
            
            if insertAdmission:
                busyInfo = wx.BusyInfo(_("Creating new admission"),self.root)
                if readmission and basedata:
                    self.mainLogic.createAdmission(prevAdmission = basedata['prevAdmissionKey'], newPatient = patient, admissionDate = basedata['admissionDate'], basedata = basedata)
                else:
                    self.mainLogic.createAdmission(newPatient = patient, admissionDate = basedata['admissionDate'], basedata = basedata)
                del busyInfo
                self.destroyBaloons()
                self.editor = PSEditor(None, -1, _("Editor"), self.mainLogic, self.mainLogic.userType, self.doSaveAdmission, self.doCloseAdmission, self.doDeleteAdmission, self.doReopenAdmission, self.basedataCallback, self.statusCallback, self.updateStatusCallback, self.errorsCallback, self.showUserPrefs, self.dischargeLetterCallback, self.doCloseEditor, self.showHelp, self.showAbout, self.showGcpViewer)
                self.editor.Freeze()
                self.setFrameAsRoot(self.editor)
                self.editor.Show()
                self.editor.showInfoInConsolePanel()
                self.editor.showCoreSummaryPage()
                self.destroyBrowser() 
                self.editor.Thaw()
        
    def showUserPrefs(self):
        updialog = PSUserPrefs(self.root,self.mainLogic)
        updialog.Center()
        updialog.ShowModal()
        

    def showNotificationCallback(self):
        messageList = self.getServerMessages(True, True, False)
        if messageList:
            print 'messageList', messageList
            frame = PSNotificationViewer(messageList, self.showEditor)
            frame.MakeModal()
            frame.Show()

    def moveMasterConfigurationCallback(self):
        from mainlogic import _
        if not self.mainLogic.isMaster:
            dlg = wx.MessageDialog(None, 
                _("This operation can be completed only using the Prosafe master."),
                _("Move master error"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
            return
        
        dlg = wx.MessageDialog(None, 
                _("This operation will deactivate and close your master. Continue?"),
                _("Move master error"), wx.YES_NO | wx.ICON_WARNING)
        dlg.Center()
        if dlg.ShowModal() == wx.ID_NO:
            return
            
        
        userPath = os.path.expanduser('~')
        if userPath == '~' or not os.path.exists(userPath):
            userPath = os.cwd()
        dlg = wx.FileDialog(None, _("Save location"), userPath, "masterdata", "*.pmd", wx.SAVE)
        path = ''
        wx.BeginBusyCursor()
        if dlg.ShowModal() != wx.ID_OK:
            wx.EndBusyCursor()
            return
        path = dlg.GetPath()
        if not path:
            wx.EndBusyCursor()
            return
        wx.EndBusyCursor()
        
        

        keepGoing = True
        stopped = False
        count = 0
        self.mainLogic.forceMasterSynchronization()
        dlg = wx.ProgressDialog(_("Synchronizing"),_("Prosafe is synchronizing data, please wait."),maximum = 100,parent=None,style = wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        while keepGoing:
            wx.MilliSleep(100)
            (keepGoing, skip) = dlg.Pulse(_("Prosafe is synchronizing data, please wait."))
            if not self.mainLogic.master.synchronizing:
                keepGoing = False
            if not keepGoing and self.mainLogic.master.synchronizing:
                stopped = True
            
        dlg.Destroy()
        if stopped:
            print 'synchronization has been stopped'
            return
        self.mainLogic.getMasterDataPackage(path)
        self.consentToShutDownMaster()
        self.doQuit(False)
            
    def showConfigurationCallback(self, event):
        win = transientPopup(self.root, self.showUserPrefs, self.dischargeLetterModelCallback, self.showUserManager, self.showCustomizationEditor,self.showRestorableDeleted, self.moveMasterConfigurationCallback, self.gcpSettingsCallback)
        pos = event.GetEventObject().GetScreenPositionTuple()
        win.SetPosition((pos[0], pos[1]))
        win.ShowModal()
        
    
    def restoredeleted(self, var):
        self.showEditor(var)
        self.mainLogic.RestoreDeleteAdmission()
    
    def showRestorableDeleted(self):
        from mainlogic import _
        unAdmissionData=self.mainLogic.getAllAdmissionsDataDeleted()
        if unAdmissionData !=[]:
            dialog = PSRestorableDeleted(unAdmissionData, self.restoredeleted) 
            dialog.SetSize((800,600))
            dialog.Centre()
            dialog.Show()
        else:
            
            dial = wx.MessageDialog(None, _('No hospitalization unactivated'),_("Info"), wx.OK)
            dial.Centre()
            dial.ShowModal()
        
    def showCustomizationEditor(self):
        personalizations = {}
        proceduresPersonalizations = {}
        removalOptions = {}
        removalOptions = {}
        removalOptions['prelieve'] = {}
        removalOptions['prelieve']['organs'] = False
        removalOptions['prelieve']['fabric'] = False
        self.mainLogic.loadCrfs(self.mainLogic.getDate())
        self.mainLogic.readCustomizableCodingSets()
        if self.mainLogic.getAppdataPersonalizations():
            for customization in [el for el in self.mainLogic.getAppdataPersonalizations().getchildren()]:
                if customization.tag == 'codingSetValue':
                    codingSetValueFullName = customization.get("name")
                    crfName, codingSetName, codingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(codingSetValueFullName)
                    if customization.get("active"):
                        #TODO: must be fixed
                        if 'Trattamenti' not in proceduresPersonalizations.keys():
                            proceduresPersonalizations['Trattamenti'] =  []
                        proceduresPersonalizations['Trattamenti'].append({'name': codingSetValueName, 'label':customization.get('value'), 'value':'True'})
                    else:
                        if codingSetName not in personalizations.keys():
                            personalizations[codingSetName] = []
                        personalizations[codingSetName].append({'name': codingSetValueName, 'label':customization.get('value')})
                elif customization.tag == 'attribute':
                    if customization.get('name') == 'core.organRemovalCustom.value':
                        removalOptions['prelieve']['organs'] = True
                    if customization.get('name') == 'core.fabricRemovalCustom.value':
                        removalOptions['prelieve']['fabric'] = True    
                    
        print 'removal option to be shown in customization editor', removalOptions
        dialog = PSFieldCustomizer(self.root,callback=self.saveCustomizationCallback,customizableFields=self.mainLogic.customizationDict, customizedFields=personalizations,proceduresPersonalizations=proceduresPersonalizations, removalOptions=removalOptions) 
        dialog.SetSize((800,600))
        dialog.Centre()
        dialog.Show()
        

    def saveCustomizationCallback(self, customizations, proceduresCustomization, removingList, removalOptions):
        #TODO: move to mainlogic
        self.mainLogic.saveCustomization(customizations, proceduresCustomization, removingList, removalOptions)
        
    def showUserManager(self):
        languages = self.mainLogic.getLanguageNames()
        userManager = PSUserManager(self.root,languages,self.usersCallback,self.createUserCallback,self.updateUserCallback,self.showHelp,self.showAbout)
        #self.setFrameAsRoot(userManager)
        size = self.root.GetSize()
        size.width = size.width * 3 / 4
        size.height = size.height * 3 / 4
        userManager.SetSize(size)   
        userManager.Center() 
        userManager.Show()
        #self.root = userManager

    def createUserCallback(self, surname, name, username, lang, userType, flgEnabled, npassword):
        if self.mainLogic.userExists(username):
            return 'duplicate'
        result = self.mainLogic.saveNewUser(surname,name,username,lang,userType,flgEnabled,npassword)
        return result

    def updateUserCallback(self, userKey, name, surname, flgEnabled, userType, language, npassword):
        result = self.mainLogic.updateUserByAdmin(userKey,name,surname,flgEnabled,userType,language,npassword)
        return result

    def privateKeyCallback(self):
        return self.mainLogic.appdataManager.getAppdataValue('centre','privateKey')

    def setPrivateKeyCallback(self, privateKey):
        if privateKey == None:
            self.mainLogic.resetPrivateKey()
        else:
            self.mainLogic.setNewPrivateKey(privateKey)
        self.mainLogic.notificationCenter.postNotification("AdmissionsHaveBeenUpdated",self)

    def usersCallback(self):
        userList = self.mainLogic.getUsers()
        users = {}
        for user in userList:
            users[user['username']] = user
        return users

    def testConnectionCallback(self, address=None, username=None, password=None):
        connectionSetUp = self.mainLogic.networkManager.tryConnection(address,username,password)
        return connectionSetUp

    def proxyCallback(self, address=None, username=None, password=None):

        if address == None:
            address = self.mainLogic.appdataManager.getAppdataValue('network/proxy','address')
            username = self.mainLogic.appdataManager.getAppdataValue('network/proxy','username')
            password = self.mainLogic.appdataManager.getAppdataValue('network/proxy','password')
            return address, username, password

        address = address.replace('http://','')
        if username == None:
            username = ''
        if password == None:
            password = ''
        self.mainLogic.saveProxySettings(address,username,password)
 
    def gcpSettingsCallback(self):
        updialog = PSGcpConfig(self.root,self.mainLogic)
        updialog.Center()
        updialog.ShowModal()
        
    def showFieldsCustomizer(self):
        updialog = PSFieldsCustomizer(self.root,self.mainLogic)
        updialog.Center()
        updialog.ShowModal()
        
    def showExport(self):
        updialog = PSExporter(self.root,self.mainLogic)
        updialog.Center()
        updialog.ShowModal()
        
    def showOverviewProgressBar(self):
        max = 100
        overviewProgressBar = PSProgressBar(self.root, max)
        overviewProgressBar.Show()
        
    def doLogin(self, username, password, fixerUser):
        loginResult = self.mainLogic.doLogin(username,password)
        from mainlogic import _
        firstLogin = False
        
        if loginResult['userType'] != psc.USER_NO_AUTH and not self.mainLogic.shouldAnonymizeData:
            firstPasswordChanged = loginResult['firstPasswordChanged']
            expiryDate = loginResult['passwordExpiryDate']
            passwordChangeNeeded = False
            if not firstPasswordChanged:
                passwordChangeNeeded = True
            if not expiryDate:
                el = self.mainLogic.appdataManager.getAppdataElementWithAttributes('centre/users/user',('username','password'),(username,loginResult['password']))
                days = 90
                nextExpiryDate = (datetime.datetime.now() + datetime.timedelta(days)).strftime("%Y-%m-%d")
                el.set('passwordExpiryDate',nextExpiryDate)
                loginResult['passwordExpiryDate'] = nextExpiryDate
                self.mainLogic.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,el)
                self.mainLogic.appdataManager.writeAppdata()
            else:
                if datetime.datetime.strptime(expiryDate, "%Y-%m-%d") < datetime.datetime.now():
                    passwordChangeNeeded = True
            if passwordChangeNeeded:
                firstLogin = True
                changeName = False
                if not firstPasswordChanged and loginResult['userType'] == psc.USER_ADMIN:
                    changeName = True
                else:
                    firstLogin = False
                passwordChangeDialog = PSPwdChanger(self.login,loginResult,self.changePasswordCallback,changeName)
                passwordChangeDialog.Center()
                ret = passwordChangeDialog.ShowModal()
                if not ret:
                    self.doLogoutNoConfirm()
                    return
                el = self.mainLogic.appdataManager.getAppdataElementWithAttributes('centre/users/user',('username','password'),(username,loginResult['password']))
                el.set('firstPasswordChanged','1')
                loginResult['firstPasswordChanged'] = '1'
                days = 90
                nextExpiryDate = (datetime.datetime.now() + datetime.timedelta(days)).strftime("%Y-%m-%d")
                el.set('passwordExpiryDate',nextExpiryDate)
                loginResult['passwordExpiryDate'] = nextExpiryDate
                self.mainLogic.appdataManager.replaceAppdataElementWithAttribute('centre/users/user','username',username,el)
                self.mainLogic.appdataManager.writeAppdata()
        if ((username in ['admin', 'ASSISTENZA']) and fixerUser) and loginResult['userType'] != psc.USER_NO_AUTH:
            self.mainLogic.setUser(loginResult)
            isEvaluatingAdmissions = False
            if self.mainLogic.isMaster:
                isEvaluatingAdmissions = self.mainLogic.master.isEvaluatingAdmissions
            if isEvaluatingAdmissions:
                dlg = wx.MessageDialog(self.login, 
                    _("Do you wish to login as fixer while evaluating admissions?"),
                    "Login Error", wx.YES_NO | wx.ICON_EXCLAMATION)
                dlg.Center()
                result = dlg.ShowModal()
                if result != wx.ID_YES:
                    return
            if self.mainLogic.isUpdatingScripts():
                dlg = wx.MessageDialog(self.login, 
                    _("Cannot use fixer scripts while updating prosafe scripts"),
                    "Login Error", wx.OK | wx.ICON_EXCLAMATION)
                dlg.Center()
                dlg.ShowModal()
                return
            scriptViewer = ProsafeScriptViewer(self.mainLogic.getUpdatedScriptList,self.doLogoutNoConfirm, self.mainLogic.appdataManager.publicEncryptDecryptString, self.mainLogic.disposeJsonStore, self.mainLogic.connectJsonStore)
            scriptViewer.Show()
            self.login.Destroy() 
            return
        if loginResult['userType'] != psc.USER_NO_AUTH or self.mainLogic.shouldAnonymizeData:
            if self.login:
                self.login.Destroy() 
            self.mainLogic.setUser(loginResult)
            self.loginErrors = 0

            from mainlogic import _
            busyInfo = wx.BusyInfo(_("Logging in"),self.root)
            self.showBrowser(firstLogin=firstLogin,isLoggingIn=True)
            del busyInfo
            
        else:
            self.loginErrors += 1
            if self.loginErrors == 1:
                wx.MessageBox(_("Login error!"),parent=self.login)
            else:
                dlg = wx.MessageDialog(self.login, 
                    _("LOGIN_ERROR_TEXT"),
                    "Login Error", wx.OK | wx.ICON_ERROR)
                dlg.Center()
                dlg.ShowModal()

    def changePasswordCallback(self, username, newPassword, name='', surname=''):
        saveOk = self.mainLogic.doSavePassword(username,newPassword,name,surname)
        return saveOk
 
    def doLogout(self):
        from mainlogic import _
        #dlg = wx.MessageDialog(None, 
        #     _("Do you really want to logout?"),
        #     _("Confirm logout"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        #dlg.Center()
        #result = dlg.ShowModal()
                
        #if result == wx.ID_OK:
        if True:
            self.destroyBaloons()
            self.mainLogic.doLogout()
            self.mainLogic.username = None
            self.mainLogic.userType = psc.USER_NO_AUTH
            self.sortColumn = 1
            self.sortAscending = 0
            self.lastAdmissionKey = ""
            self.showLogin()
 
    def doLogoutNoConfirm(self):
        self.mainLogic.doLogout()
        #for c in self.root.GetChildren():
        #    c.Show(False)
        #    c.Destroy()
        self.mainLogic.username = None
        self.mainLogic.userType = psc.USER_NO_AUTH
        self.showLogin()
    
    def clientQuit(self,notifyingObject):
        self.doQuit(False)
 
    def masterClientQuit(self,notifyingObject):
        if self.mainLogic.isMaster:
            #self.mainLogic.shutDownThreads()
            #time.sleep(1.0)
            self.shouldStopThreads = True
            #self.doQuit(False)
 
    def doQuit(self, checkConnectedClients=True):
        from mainlogic import _
        #TODO: TRANSLATE
        if self.mainLogic.isMaster and checkConnectedClients and self.mainLogic.master.bulletinManager.getActiveNonStaticClientKeys():
            dlg = wx.MessageDialog(None,
                _("There are clients currently connected to this PROSAFE Master. Continue?"),
                _("Confirm quit"), wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                return
            self.mainLogic.bulletinClient.postNotificationOnBulletin("MasterMustShutDown")
            counter = 0
            while self.mainLogic.master.bulletinManager.getActiveNonStaticClientKeys() and counter < 4:
                time.sleep(1.0)
                counter += 1

        cursor = wx.BusyCursor()
        #busyInfo = wx.BusyInfo(_("PROSAFE shutting down"),self.root)
        #self.minLogic.shutDownThreads()
        #time.sleep(1.0)
        self.shouldStopThreads = True
        self.shouldAskPermissionIfMaster = False
        if self.mainLogic.isMaster:
            if not self.mainLogic.master.serverStopped:
                self.mainLogic.shutDownMaster(False)
            while not self.mainLogic.master.serverStopped:
                time.sleep(0.25)
        sys.exit(0)
        
    def getServerMessages(self,updateMessageList=False,includeClientMessages=False,localFetch=False):
        return self.mainLogic.getServerMessages(updateMessageList,includeClientMessages,localFetch)
        
    def removeClientMessage(self, clientMessage):
        self.mainLogic.removeClientMessage(clientMessage)
        
    def fetchServerMessages(self, notifyingObject, localFetch=False):
        #TODO! should be moved to mainLogic?
        messages = self.getServerMessages(updateMessageList=False,includeClientMessages=True,localFetch=localFetch)
        if self.root and messages:
            for message in messages:
                if 'admissionReference' in message.keys() and message['admissionReference'] is not None:
                    continue
                if 'shown' in message.keys() and message['shown'] == True:
                    continue
                title = message['title']
                text = message['text']
                if 'title' not in message.keys() or 'text' not in message.keys():
                    continue
                priority = 'low'
                if 'priority' in message.keys():
                    priority = message['priority']                
                self.setBaloonTip(self.root, True, text=text, title=title, priority=priority)
                if 'type' in message.keys() and message['type'] == 'istant':
                    self.removeClientMessage(message)
                if 'repeatable' in message.keys() and message['repeatable'] == False:
                    message['shown'] = True
                
            cumulativeMessages = {}
            priorityOrder = {'high':3, 'medium':2, 'low':1}
            for message in messages:
                if 'admissionReference' not in message.keys() or message['admissionReference'] is None:
                    continue
                if message['title'] not in cumulativeMessages.keys():
                    cumulativeMessages[message['title']] = {}
                    cumulativeMessages[message['title']]['values'] = {}
                #cumulativeMessages[message['title']]['text'] = message['text']
                #cumulativeMessages[message['title']] = message['priority']
                if message['priority'] not in cumulativeMessages[message['title']]['values']:
                    cumulativeMessages[message['title']]['values'][message['priority']] = {}
                    
                if message['text'] not in cumulativeMessages[message['title']]['values'][message['priority']]:
                    cumulativeMessages[message['title']]['values'][message['priority']][message['text']] = []
                cumulativeMessages[message['title']]['values'][message['priority']][message['text']].append(message['admissionReference'])
               
            for cumulativeTitle in cumulativeMessages.keys():
                title = cumulativeTitle
                if message['title'] not in cumulativeMessages:
                    continue
                for priority in cumulativeMessages[cumulativeTitle]['values'].keys():
                    for text in cumulativeMessages[cumulativeTitle]['values'][priority]:
                        admissionIds = cumulativeMessages[cumulativeTitle]['values'][priority][text]
                        self.setBaloonTip(self.root, True, text=text, title=title, priority=priority, admissionIds=admissionIds)
            
    def doClose(self):
        from mainlogic import _
        dlg = wx.MessageDialog(None, 
            _("Do you really want to quit?"),
            _("Confirm quit"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        dlg.Center() 
        result = dlg.ShowModal()
        dlg.Destroy()        
        if result == wx.ID_OK:
        #if True:
            self.doQuit()

    def doCloseBrowser(self):
        self.doLogout()

    def doCloseEditor(self):

        from mainlogic import _

        proceedWithClosing = False        
        if self.mainLogic.dataSession.modified and (self.mainLogic.dataSession.objects.anyModified() or self.mainLogic.dataSession.objectsAttributes.anyModified()):
            
            dlg = PSMessageDialog(None,
                _("Data has changed. Save now?"),
                _("Confirm save"), mode=2)
            result = dlg.ShowModal()
            dlg.Destroy()
        
            if dlg.returnValue == wx.ID_YES:
            
                self.doSaveAdmission()
                proceedWithClosing = True
                if self.mainLogic.getGcpChangedAttributes():
                    proceedWithClosing = False
            elif dlg.returnValue == wx.ID_NO:
                proceedWithClosing = True
            else:
                proceedWithClosing = False
        else:
            proceedWithClosing = True

        if proceedWithClosing:
            self.lastAdmissionKey = self.mainLogic.dataSession.admissionKey
            self.mainLogic.notificationCenter.postNotification("EditorIsClosing",self.editor)
            self.mainLogic.notificationCenter.removeObserver(self.editor)
            self.mainLogic.exitAdmission()
            self.editorToBrowser()

    def uploadDBCallback(self):
        dlg = wx.ProgressDialog(_("Please wait"), _("Upload in progress"), maximum=10, parent=None, style=wx.PD_APP_MODAL|wx.PD_SMOOTH)
        dlg.Pulse()
        result = self.mainLogic.uploadDB()
        dlg.Destroy()
        return result

    def statusMsg(self, msg):
        if self.root:
            self.root.SetStatusText(msg)

    def showHelp(self):
        try:
            import webbrowser
            webbrowser.open(psc.abspath('images/%s' % psc.manualName ,True))
        except:
            from mainlogic import _
            info = wx.Dialog(self.root, -1, "Help", size=wx.Size(300, 250))
            titleLabel = wx.StaticText(info, -1, "PROSAFE")
            copyrightText = _("PROSAFE Manual is still missing. Coming soon!!")
            copyrightLabel = wx.StaticText(info, -1, copyrightText)
            okButton = wx.Button(info, -1, _("Close"))
            sizer = wx.BoxSizer(wx.VERTICAL)
            vsizer = wx.BoxSizer(wx.VERTICAL)
            font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
            font.SetWeight(wx.FONTWEIGHT_BOLD)        
            info.Bind(wx.EVT_BUTTON, lambda event : info.Show(False), okButton)
            vsizer.AddSpacer(20)
            vsizer.Add(titleLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
            vsizer.AddSpacer(5)
            vsizer.AddSpacer(20)        
            vsizer.Add(copyrightLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
            vsizer.AddSpacer(20)
            vsizer.Add(okButton, 0, wx.ALIGN_CENTRE|wx.ALL)
            sizer.Add(vsizer,0,wx.ALIGN_CENTRE|wx.ALL,20)

            info.SetSizer(sizer)
            info.Layout()
            info.Fit()
            info.Center()
            info.SetFocus()
            info.ShowModal()
        
        
    def showAbout(self):
        from mainlogic import _
        info = wx.Dialog(self.root, -1, "About", size=wx.Size(300, 250))
        titleLabel = wx.StaticText(info, -1, "PROSAFE")
        versionLabel = wx.StaticText(info, -1, "Version " + PROSAFE_VERSION)
        copyrightText = """Copyright 2010-2011, Mario Negri Institute for Pharmacological Research.
All rights reserved.

The PROSAFE Project is supported by the European Commission
in the framework of the Public Health Program
(project reference number 2007331).

PROSAFE engine development: Orobix (www.orobix.com) and Mauro Bianchi.
 
The PROSAFE software is provided free-of-charge for research purposes.
Unauthorized redistribution in any form is prohibited.
"""
        
        disclaimerText = _("PROSAFE_DISCLAIMER")

        import textwrap
        disclaimerTextWrapped = textwrap.wrap(disclaimerText,70)
        copyrightLabel = wx.StaticText(info, -1, copyrightText + '\n' + '\n'.join(disclaimerTextWrapped))
        okButton = wx.Button(info, -1, _("Close"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetWeight(wx.FONTWEIGHT_BOLD)        
        info.Bind(wx.EVT_BUTTON, lambda event : info.Show(False), okButton)
        vsizer.AddSpacer(20)
        vsizer.Add(titleLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(5)
        vsizer.Add(versionLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)        
        homepageLink = wx.lib.hyperlink.HyperLinkCtrl(info, wx.ID_ANY, "prosafe.marionegri.it",URL="http://prosafe.marionegri.it")
        vsizer.Add(copyrightLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)
        vsizer.Add(homepageLink, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)
        vsizer.Add(okButton, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer,0,wx.ALIGN_CENTRE|wx.ALL,20)

        info.SetSizer(sizer)
        info.Layout()
        info.Fit()
        info.Center()
        info.SetFocus()
        info.ShowModal()

    def nonSupportedFeautureDialog(self, text):
        from mainlogic import _
        info = wx.Dialog(self.root, -1, "Analyzer", size=wx.Size(300, 250))
        copyrightLabel = wx.StaticText(info, -1, ''.join(text))
        okButton = wx.Button(info, -1, _("Close"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetWeight(wx.FONTWEIGHT_BOLD)        
        info.Bind(wx.EVT_BUTTON, lambda event : info.Show(False), okButton)
        vsizer.AddSpacer(20)        
        homepageLink = wx.lib.hyperlink.HyperLinkCtrl(info, wx.ID_ANY, _("Analyzer link"), URL="http://givitiweb.marionegri.it/Analyzer/")
        vsizer.Add(copyrightLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)
        vsizer.Add(homepageLink, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)
        vsizer.Add(okButton, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer,0,wx.ALIGN_CENTRE|wx.ALL,20)

        info.SetSizer(sizer)
        info.Layout()
        info.Fit()
        info.Center()
        info.SetFocus()
        info.ShowModal()        
