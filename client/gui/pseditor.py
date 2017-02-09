import wx
import datetime
import psconstants as psc
from psguiconstants import GUI_WINDOW_VARIANT
import psconstants as psc
from pstree import PSTree
from psrightpanel import PSRightPanel
from pserrors import PSErrors
from psinfo import PSInfo
from psadmissioncloser import PSAdmissionCloser
from psevaluator import years
from psevaluator import nowdateiso
from psevaluator import valuetodate
from notificationcenter import notificationCenter
import sys
import os

class PSEditor(wx.Frame): 
    def __init__(self, parent, id, title, mainLogic, userType, saveAdmissionCallback, closeAdmissionCallback, deleteAdmissionCallback, reopenAdmissionCallback, basedataCallback, statusCallback, updateStatusCallback, errorsCallback, userPrefsCallback, dischargeLetterCallback, closeCallback, helpCallback, aboutCallback, gcpViewerCallback):

        from mainlogic import _

        wx.Frame.__init__(self, parent, id, "", pos=wx.DefaultPosition,size=wx.DefaultSize, style= wx.DEFAULT_FRAME_STYLE, name="editor")

        self.mainLogic = mainLogic

        self.userType = userType
        self.saveAdmissionCallback = saveAdmissionCallback
        self.closeAdmissionCallback = closeAdmissionCallback
        self.deleteAdmissionCallback = deleteAdmissionCallback
        self.reopenAdmissionCallback = reopenAdmissionCallback
        self.basedataCallback = basedataCallback
        self.statusCallback = statusCallback
        self.updateStatusCallback = updateStatusCallback
        self.errorsCallback = errorsCallback
        self.userPrefsCallback = userPrefsCallback
        self.dischargeLetterCallback = dischargeLetterCallback
        self.closeCallback = closeCallback
        self.helpCallback = helpCallback
        self.aboutCallback = aboutCallback
        self.gcpViewerCallback = gcpViewerCallback
 
        self.Freeze()
 
        icon1 = wx.Icon(os.path.join(psc.imagesPath, "man2.ico"), wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)
        self.initMenu()
        self.initStatusBar()
        self.initToolBar()
        
        self.horizontalSplitter = wx.SplitterWindow(self,-1,style=wx.SP_3DSASH)
        self.horizontalSplitter.SetMinimumPaneSize(20)
        self.verticalSplitter = wx.SplitterWindow(self.horizontalSplitter,-1,style=wx.SP_3DSASH)
        self.verticalSplitter.SetMinimumPaneSize(20)

        self.consoleSplitter = wx.SplitterWindow(self.horizontalSplitter,-1,style=wx.SP_3DSASH)
        self.consoleSplitter.SetMinimumPaneSize(20)
 
        self.displaySize = wx.DisplaySize()
        if self.displaySize[0] > 800:
            self.compactLayout = False
        else:
            self.compactLayout = True

        self.consolePanel = wx.Notebook(self.consoleSplitter, -1)
        self.consolePanel.SetWindowVariant(GUI_WINDOW_VARIANT)

        self.errorsPanel = PSErrors(self.consolePanel,self.mainLogic,self.showPageCallback,contentType="errors") 
        self.warningsPanel = PSErrors(self.consolePanel,self.mainLogic,self.showPageCallback,contentType="warnings") 
        if self.compactLayout:
            self.infoPanel = PSInfo(self.consolePanel) 
        else:
            self.infoPanel = PSInfo(self.consoleSplitter) 
        self.infoPanel.SetWindowVariant(GUI_WINDOW_VARIANT)

        self.consolePanel.AddPage(self.errorsPanel,_("Errors"))
        self.consolePanel.AddPage(self.warningsPanel,_("Warnings"))
        if self.compactLayout:
            self.consolePanel.AddPage(self.infoPanel,_("Info"))
        self.updateConsolePanelText()

        if self.compactLayout:
            fooPanel = wx.Panel(self.consoleSplitter,-1)
            self.consoleSplitter.SplitVertically(self.consolePanel,fooPanel)
            self.consoleSplitter.Unsplit(fooPanel)
        else:
            self.consoleSplitter.SplitVertically(self.consolePanel,self.infoPanel)
            self.consoleSplitter.SetSashGravity(0.5)

        #height = parent.GetSize().GetHeight() - 10
        height = 20
        self.horizontalSplitter.SplitHorizontally(self.verticalSplitter,self.consoleSplitter,height)
        self.horizontalSplitter.SetSashGravity(1.0)
        self.horizontalSplitter.Unsplit(self.consoleSplitter)

        self.leftPanel = PSTree(self.verticalSplitter,self,self.mainLogic)
        self.leftPanel.SetQuickBestSize(False)
        self.rightPanel = PSRightPanel(self.verticalSplitter,self.mainLogic,self.showPageCallback)

        self.floatingFrame = wx.Dialog(self,-1,style=wx.BORDER_NONE)
 
        self.leftPanel.Bind(wx.EVT_ENTER_WINDOW,self.onEnterLeftPanel)
        self.leftPanel.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveLeftPanel)

        self.verticalSplitter.SplitVertically(self.leftPanel,self.rightPanel,300)
        
        self.Bind(wx.EVT_CLOSE,self.onClose,self) 
        
        self.userSashPosition = -1
        self.backupSashPosition = -1
        self.visibilityLeft = False

        notificationCenter.addObserver(self,self.onDataModifiedForbidden,"DataModifiedForbidden",self.mainLogic.dataSession)
        notificationCenter.addObserver(self,self.onBasedataUpdated,"BasedataHasBeenUpdated")
        notificationCenter.addObserver(self,self.onStatusUpdated,"StatusHasBeenUpdated")
        #notificationCenter.addObserver(self,self.onEnsureRightPanelVisibility,"EnsureRightPanelVisibility")
        notificationCenter.addObserver(self,self.onErrorsChanged,"ErrorsHaveChanged",self.mainLogic.dataSession)
        notificationCenter.addObserver(self,self.onErrorsUpdated,"ErrorsHaveBeenUpdated",self.mainLogic.dataSession)
        notificationCenter.addObserver(self,self.onErrorsAndWarningsFound,"ErrorsAndWarningsHaveBeenFound")
        notificationCenter.addObserver(self,self.onAdmissionDataSaved,"EditorDataHaveBeenSaved")
        self.updateTitle()

        self.rightPanel.Bind(wx.EVT_ENTER_WINDOW,self.onEnterRightPanel)
        self.Thaw()
        
    def removeObservers(self):
        self.rightPanel.removeObservers()
        notificationCenter.removeObserver(self)
    
    def onShowHelp(self, event):
        self.helpCallback()

    def onShowAbout(self, event):
        self.aboutCallback()

    def showCoreSummaryPage(self):
        self.leftPanel.selectPage(psc.coreCrfName,None)

    def onEnterRightPanel(self,event):
        #self.rightPanel.SetFocus()
        pass

    def updateConsolePanelText(self):
        from mainlogic import _
        errorsAndWarnings = self.errorsCallback()
        numberOfErrors = errorsAndWarnings['errors']
        numberOfUnacceptedWarnings = errorsAndWarnings['warnings']
        errorsText = _("Errors") + " (%d)" % numberOfErrors
        warningsText = _("Warnings") + " (%d)" % numberOfUnacceptedWarnings
        self.consolePanel.SetPageText(0,errorsText)
        self.consolePanel.SetPageText(1,warningsText)
        self.SetStatusText("  %s   %s" % (errorsText,warningsText))

    def onErrorsChanged(self,notifyingObject,userInfo=None):
        self.updateConsolePanelText()

    def onErrorsUpdated(self,notifyingObject,userInfo=None):
        self.updateConsolePanelText()

    def showFloatingFrame(self):
        self.backupSashPosition = self.verticalSplitter.GetSashPosition()
        newSize = (self.leftPanel.GetBestSize()[0]+20,self.leftPanel.GetSize()[1])
        self.floatingFrame.SetSize(newSize)
        position = self.leftPanel.GetScreenPosition()
        if sys.platform in ['win32']:
            position = (position[0]-2, position[1]-2)
        self.floatingFrame.SetPosition(position)
        self.leftPanel.Reparent(self.floatingFrame)
        self.leftPanel.SetSize(newSize)
        self.leftPanel.Refresh()
        self.floatingFrame.Show()

    def hideFloatingFrame(self):
        self.floatingFrame.Hide()
        self.leftPanel.Reparent(self.verticalSplitter)
        self.verticalSplitter.SetSashPosition(self.verticalSplitter.GetSashPosition(),True)

    def onEnterLeftPanel(self,event):
        actualWidth = self.leftPanel.GetSize().width
        minWidth = self.leftPanel.GetBestSize().width
        if actualWidth >= minWidth:
            event.Skip()
            return
        self.showFloatingFrame()

    def onLeaveLeftPanel(self,event):
        if not self.floatingFrame.IsShown():
            event.Skip()
            return
        self.hideFloatingFrame()

    def onToggleLeftPanelVisibility(self,event):
        if self.visibilityLeft:
            self.visibilityLeft = False
            self.verticalSplitter.SetSashPosition(self.backupSashPosition,True)
        else:
            self.ensureLeftPanelVisibility()

    def ensureLeftPanelVisibility(self):
        self.visibilityLeft = True
        actualWidth = self.verticalSplitter.GetSashPosition()
        minWidth = self.leftPanel.GetBestSize().width
        if actualWidth >= minWidth:
            return
        self.backupSashPosition = self.verticalSplitter.GetSashPosition()
        sashPosition = minWidth
        self.verticalSplitter.SetSashPosition(sashPosition,True)

    def onEnsureRightPanelVisibility(self,notifyingObject,userInfo=None):
        if self.floatingFrame.IsShown():
            self.hideFloatingFrame()
        self.visibilityLeft = False
        minWidth = userInfo["minWidth"]
        actualWidth = userInfo["actualWidth"]
        if actualWidth >= minWidth:
            self.ensureLeftPanelVisibility()
            return
        sashPosition = self.verticalSplitter.GetSashPosition()
        newSashPosition = sashPosition - (minWidth-actualWidth) - 20
        if newSashPosition < 50:
            newSashPosition = 50
        self.verticalSplitter.SetSashPosition(newSashPosition,True)

    def onBasedataUpdated(self,notifyingObject,userInfo=None):
        self.updateTitle()
    
    def onStatusUpdated(self,notifyingObject,userInfo=None):
        self.refreshMenu()
        self.Refresh()
        self.Update()

    def updateTitle(self):
        from mainlogic import _
        basedata = self.basedataCallback()
        if not basedata:
            self.SetTitle("")
            return
        clientMasterString = "Client"
        if self.mainLogic.isMaster:
            clientMasterString = "Master"
        onlineOfflineString = "Offline"
        if self.mainLogic.networkManager.couldConnect():
            onlineOfflineString = "Online"

        #print "BASEDATA", basedata
        #evaluatedAge = self.mainLogic.evaluator.eval("result = |core.age.value|[0]")
        evaluatedAge = self.mainLogic.evaluator.eval("result = |%s|[0]" % psc.ageAttr)
        #TODO MERGE
        if self.mainLogic.shouldAnonymizeData:
            title = "PROSAFE %s (%s)" % (clientMasterString, onlineOfflineString)
        else:
            title = "PROSAFE %s (%s) - %s %s %s %s %s %s" % (clientMasterString, onlineOfflineString, _("Patient: "), basedata['lastName'], basedata['firstName'], _("  Age: ") + str(evaluatedAge), _("  Admitted: ") + datetime.datetime.strftime(valuetodate(basedata['admissionDate']), "%d/%m/%Y"),  _("  Status: ") + str(self.statusCallback()))
        
        self.SetTitle(title)

    def onDataModifiedForbidden(self,notifyingObject,userInfo=None):
        from mainlogic import _
        dlg = wx.MessageDialog(None, 
            _("Cannot modify data in Status 4 or 5."),
            _("ERROR"), wx.OK | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    def onErrorsAndWarningsFound(self,notifyingObject,userInfo):
        from mainlogic import _
        anyErrors = userInfo['errors']
        anyUnacceptedWarnings = userInfo['warnings']
        if anyErrors and anyUnacceptedWarnings:
            self.SetStatusText(_("There are errors and unaccepted warnings. Please review and correct."))
            self.showErrorsInConsolePanel()
        elif anyErrors:
            self.SetStatusText(_("There are errors. Please review and correct."))
            self.showErrorsInConsolePanel()
        elif anyUnacceptedWarnings:
            self.SetStatusText(_("There are unaccepted warnings. Please review, correct or accept."))
            self.showWarningsInConsolePanel()

    def onAdmissionDataSaved(self,notifyingObject,userInfo=None):
        from mainlogic import _
        self.SetStatusText(_("Data saved."))
        self.updateTitle()

    def showPageCallback(self, crfName, pageName, timeStamp=None):
        self.leftPanel.selectPage(crfName,pageName,timeStamp)

    def onClose(self, event):
        self.rightPanel.guiGenerator.killFocus()
        self.closeCallback()

    def initMenu(self):
        menuBar = wx.MenuBar()
        from mainlogic import _
        menu = wx.Menu()
        
        menuExit = menu.Append(-1, _("&Exit"))
        menuBar.Append(menu, _("&File"))
 
        menuCloseAdmission = None
        menuReOpenAdmission = None
        menuDeleteAdmission = None

        if self.userType >= psc.USER_MANAGER: 
        
            self.menuA = wx.Menu()
            menuCloseAdmission = self.menuA.Append(1001,  _("&Close admission"))
            menuReOpenAdmission = self.menuA.Append(1002,  _("&Re-Open admission"))
            self.menuA.AppendSeparator()
            menuDeleteAdmission = self.menuA.Append(-1,  _("&Delete admission"))
            menuBar.Append(self.menuA, _("&Admission"))
        
        menuH = wx.Menu()
        menuHelp = menuH.Append(-1,  _("&Application Help"))
        menuAbout = menuH.Append(-1,  _("&About"))
        menuBar.Append(menuH, _("&Help"))

        if self.userType >= psc.USER_MANAGER: 
            menuCloseAdmission.Enable(False) 
            menuReOpenAdmission.Enable(False)
            for crfName in self.mainLogic.crfData.getCrfNames():
                if self.statusCallback(crfName) in ['4', '5']:
                    menuReOpenAdmission.Enable(True)
                else:
                    menuCloseAdmission.Enable(True)
                
 
        self.SetMenuBar(menuBar)
        
        self.Bind(wx.EVT_MENU, self.closeEditor, menuExit)
        if self.userType >= psc.USER_MANAGER: 
            self.Bind(wx.EVT_MENU,self.doCloseAdmission,menuCloseAdmission)
            self.Bind(wx.EVT_MENU,self.doReOpenAdmission,menuReOpenAdmission)
            self.Bind(wx.EVT_MENU,self.doDeleteAdmission,menuDeleteAdmission)
 
        self.Bind(wx.EVT_MENU,self.onShowHelp,menuHelp)
        self.Bind(wx.EVT_MENU,self.onShowAbout,menuAbout)

    def closeEditor(self, evt):
        self.closeCallback()
        
    def refreshMenu(self):
        self.initMenu()
    
    def initStatusBar(self):
        self.CreateStatusBar()
        self.SetStatusText("")
    
    def initToolBar(self):
        toolbar = self.CreateToolBar(style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT)
        toolbar.SetToolBitmapSize((48,48))
        from mainlogic import _

        bmp_back = wx.Image(os.path.join(psc.imagesPath, 'back.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_back = toolbar.AddLabelTool(-1, _("Exit"), bmp_back, longHelp=_("Click to go back to admissions list"))
        self.Bind(wx.EVT_MENU, self.onClose, tool_back)
        toolbar.AddSeparator()        
        
        #bmp_userpref = wx.Image('images/user.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #tool_userpref = toolbar.AddLabelTool(-1, _("User preferences"), bmp_userpref, longHelp=_("Click to manage preferences"))
        #self.Bind(wx.EVT_MENU, self.onShowUserPrefs, tool_userpref)
        #toolbar.AddSeparator()
            
        #if self.userType >= psc.USER_MANAGER:            
        #    #config
        #    """
        #    bmp_customize = wx.Image('images/customize.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #    tool_customize = toolbar.AddLabelTool(-1, bmp_customize, "Fields customization", "Click to edit custom fields")
        #    self.Bind(wx.EVT_MENU, self.GetParent().showFieldsCustomizer, tool_customize)
        #    toolbar.AddSeparator()"""
        #    pass
        
        #if self.userType >= psc.USER_ADMIN:
        #    #users
        #    bmp_users = wx.Image('images/users.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #    tool_users = toolbar.AddLabelTool(-1, _("Users"), bmp_users, longHelp=_("Click to manage users"))
        #    self.Bind(wx.EVT_MENU, self.GetParent().onShowUserManager, tool_users)
        #    
        #    #config
        #    bmp_configure = wx.Image('images/configure.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #    tool_configure = toolbar.AddLabelTool(-1, _("Configuration"), bmp_configure, longHelp=_("Click to edit software configuration"))
        #    self.Bind(wx.EVT_MENU, self.GetParent().showClientConfig, tool_configure)
        #    
        #    toolbar.AddSeparator()
            
        if self.userType >= psc.USER_VIEWER:
            bmp_save = wx.Image(os.path.join(psc.imagesPath, 'save.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_save = toolbar.AddLabelTool(-1, _("save"), bmp_save, longHelp=_("Click to save"))
            self.Bind(wx.EVT_MENU, self.onSave, tool_save)
            toolbar.AddSeparator()

        bmp_errors = wx.Image(os.path.join(psc.imagesPath, 'error.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_errors = toolbar.AddLabelTool(-1, _("Errors"), bmp_errors, longHelp=_("Click to show errors"))
        self.Bind(wx.EVT_MENU, self.onShowErrors, tool_errors)

        bmp_warnings = wx.Image(os.path.join(psc.imagesPath, 'warning.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_warnings = toolbar.AddLabelTool(-1, _("Warnings"), bmp_warnings, longHelp=_("Click to show warnings"))
        self.Bind(wx.EVT_MENU, self.onShowWarnings, tool_warnings)

        bmp_info = wx.Image(os.path.join(psc.imagesPath, 'info.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_info = toolbar.AddLabelTool(-1, _("Info"), bmp_info, longHelp=_("Click to show info"))
        self.Bind(wx.EVT_MENU, self.onShowInfo, tool_info)
        
        if self.userType > psc.USER_VIEWER and 'gcp' in psc.toolBarApplications and self.mainLogic.gcpActive:
            bmp_gcp = wx.Image(os.path.join(psc.imagesPath, 'gcp.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_gcp = toolbar.AddLabelTool(-1, _("GCP Log"), bmp_gcp, longHelp=_("Click to view the GCP log"))
            self.Bind(wx.EVT_MENU, self.onShowGcpLog, tool_gcp)
       
        toolbar.AddSeparator()
 
        bmp_info = wx.Image(os.path.join(psc.imagesPath, 'refresh.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_info = toolbar.AddLabelTool(-1, _("Update status"), bmp_info, longHelp=_("Click to update status"))
        self.Bind(wx.EVT_MENU, self.onUpdateStatus, tool_info)
 
        #toolbar.AddSeparator()
 
        #bmp_info = wx.Image('images/info.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        ##TODO: TRANSLATE
        #tool_info = toolbar.AddLabelTool(-1, _("Toggle tree"), bmp_info, longHelp=_("Click to toggle tree visibility in left panel"))
        #self.Bind(wx.EVT_MENU, self.onToggleLeftPanelVisibility, tool_info)
 
        if 'dischargeLetter' in psc.toolBarApplications:
            toolbar.AddSeparator()
     
            bmp_info = wx.Image(os.path.join(psc.imagesPath, 'dischargeletter.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_info = toolbar.AddLabelTool(-1, _("Discharge letter"), bmp_info, longHelp=_("Click to edit discharge letter for the current admission"))
            self.Bind(wx.EVT_MENU, self.onShowDischargeLetter, tool_info)
        
        #logout    
        #bmp_logout = wx.Image('images/logout.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #tool_logout = toolbar.AddLabelTool(-1, "Logout", bmp_logout, longHelp="Click to logout")
        #self.Bind(wx.EVT_MENU, self.GetParent().doLogout, tool_logout)
       
        #toolbar.AddSeparator()

        #bmp_info = wx.Image(os.path.join(psc.imagesPath, 'refresh.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #tool_info = toolbar.AddLabelTool(-1, _("New visit"), bmp_info, longHelp=_("Click to create new follow-up visit"))
        #self.Bind(wx.EVT_MENU, self.onNewVisit, tool_info)
 
        #bmp_info = wx.Image(os.path.join(psc.imagesPath, 'refresh.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #tool_info = toolbar.AddLabelTool(-1, _("Delete visit"), bmp_info, longHelp=_("Click to delete the current follow-up visit"))
        #self.Bind(wx.EVT_MENU, self.onDeleteVisit, tool_info)
 
        #final toolbar setup 
        toolbar.Realize()

    #def onNewVisit(self, event):
    #    timeStamps = self.mainLogic.dataSession.getAllTimeStampsForClass(psc.coreCrfName,'dynPage')
    #    timeStamp = 2
    #    if timeStamps:
    #        timeStamp = max(timeStamps) + 1
    #    self.mainLogic.dataSession.registerTimeStampForClass(psc.coreCrfName,'dynPage',timeStamp)
    #    self.mainLogic.dataSession.updateDataNoNotify(psc.coreCrfName,'timeStamp',1,'timeStamp',timeStamp)
    #    self.mainLogic.dataSession.updateData(psc.coreCrfName,'dynPage',1,'dynPage','domus.pageCodification.followUp')
    #    userInfo = {'crfName': psc.coreCrfName}
    #    self.mainLogic.notificationCenter.postNotification('DynPageHasChanged',self,userInfo)

    #def onDeleteVisit(self, event):
    #    currentTimeStamp = self.mainLogic.dataSession.getAttributeValuesForObject(psc.coreCrfName,'timeStamp',1,'timeStamp')
    #    if not currentTimeStamp:
    #        return
    #    currentTimeStamp = currentTimeStamp[0]
    #    timeStamps = self.mainLogic.dataSession.getAllTimeStampsForClass(psc.coreCrfName,'dynPage')
    #    timeStamps.sort()
    #    try:
    #        index = timeStamps.index(currentTimeStamp)
    #    except:
    #        return
    #    if index+1 < len(timeStamps):
    #        timeStamp = timeStamps[index+1]
    #    else:
    #        timeStamp = timeStamps[index-1]
    #    for (crfName,className) in self.mainLogic.dataSession.classNamesToTimeStamps:
    #        timeStampAttributeFullName = self.mainLogic.crfData.getPropertyForClass(crfName,className,'timeStamp')
    #        if timeStampAttributeFullName != '%s.%s.%s' % (psc.coreCrfName,'timeStamp','timeStamp'):
    #            continue
    #        attributeNames = self.mainLogic.crfData.getAttributeNamesForClass(crfName,className)
    #        for attributeName in attributeNames:
    #            multiInstance = self.mainLogic.dataSession.isMultiInstance(crfName,className,attributeName)
    #            if multiInstance:
    #                self.mainLogic.dataSession.updateData(crfName,className,1,attributeName,[])
    #            else:
    #                self.mainLogic.dataSession.updateData(crfName,className,1,attributeName,None)
    #        self.mainLogic.dataSession.unregisterTimeStampForClass(crfName,className,currentTimeStamp)
    #    self.mainLogic.dataSession.updateDataNoNotify(psc.coreCrfName,'timeStamp',1,'timeStamp',timeStamp)
    #    userInfo = {'crfName': psc.coreCrfName}
    #    self.mainLogic.notificationCenter.postNotification('DynPageHasChanged',self,userInfo)
 
    def onShowDischargeLetter(self, event):
        self.dischargeLetterCallback()
        
    def onShowGcpLog(self, event):
        self.gcpViewerCallback()

    def onUpdateStatus(self, event):
        self.rightPanel.guiGenerator.killFocus()
        self.updateStatusCallback()

    def onShowUserPrefs(self, event):
        self.userPrefsCallback()

    def showConsolePanel(self):
        consolePanelSize = 300
        if self.displaySize[1] <= 600:
            consolePanelSize = 200
        sashPosition = self.GetSize().GetHeight() - consolePanelSize
        self.horizontalSplitter.SplitHorizontally(self.verticalSplitter,self.consoleSplitter,sashPosition)
        self.horizontalSplitter.SetSashGravity(1.0)
        self.errorsPanel.updateGui()
        self.warningsPanel.updateGui()
        self.errorsPanel.registerForNotifications()
        self.warningsPanel.registerForNotifications()
 
    def hideConsolePanel(self):
        self.horizontalSplitter.Unsplit(self.consoleSplitter)
        self.errorsPanel.unregisterForNotifications()
        self.warningsPanel.unregisterForNotifications()
 
    def isConsolePanelShown(self):
        return self.horizontalSplitter.IsSplit()

    def isErrorsShownInConsolePanel(self):
        return self.consolePanel.GetSelection() == 0

    def isWarningsShownInConsolePanel(self):
        return self.consolePanel.GetSelection() == 1

    def isInfoShownInConsolePanel(self):
        if self.compactLayout:
            return self.consolePanel.GetSelection() == 2
        return True

    def showErrorsInConsolePanel(self):
        if not self.isConsolePanelShown():
            self.showConsolePanel()
        self.consolePanel.SetSelection(0)
 
    def showWarningsInConsolePanel(self):
        if not self.isConsolePanelShown():
            self.showConsolePanel()
        self.consolePanel.SetSelection(1)
 
    def showInfoInConsolePanel(self):
        if not self.isConsolePanelShown():
            self.showConsolePanel()
        if self.compactLayout:
            self.consolePanel.SetSelection(2)
 
    def onShowErrors(self, event):
        self.showErrorsInConsolePanel()

    def onShowWarnings(self, event):
        self.showWarningsInConsolePanel()

    def onShowInfo(self, event):
        if self.isConsolePanelShown() and self.isInfoShownInConsolePanel():
            self.hideConsolePanel()
            return
        self.showInfoInConsolePanel()
   
    def onSave(self,  event):
        self.rightPanel.guiGenerator.killFocus()
        self.saveAdmissionCallback()

    def doCloseAdmission(self, event):
        neededCrfs = {}
        for crfName in self.mainLogic.crfData.getCrfNames():
            if self.statusCallback(crfName) not in ['4', '5']:
                neededCrfs[crfName] = self.statusCallback(crfName)
        closer = PSAdmissionCloser(self,"CLOSE",self.closeAdmissionCallback,self.deleteAdmissionCallback,self.reopenAdmissionCallback,neededCrfs)
        closer.Center()
        closer.ShowModal()
        
    def doReOpenAdmission(self, event):
        neededCrfs = {}
        for crfName in self.mainLogic.crfData.getCrfNames():
            if self.statusCallback(crfName) in ['4', '5']:
                neededCrfs[crfName] = self.statusCallback(crfName)
        closer = PSAdmissionCloser(self,"REOPEN",self.closeAdmissionCallback,self.deleteAdmissionCallback,self.reopenAdmissionCallback,neededCrfs)
        closer.Center()
        closer.ShowModal()
        
    def doDeleteAdmission(self, event):
        closer = PSAdmissionCloser(self,"DELETE",self.closeAdmissionCallback,self.deleteAdmissionCallback,self.reopenAdmissionCallback)
        closer.Center()
        closer.ShowModal()
        self.closeCallback()

