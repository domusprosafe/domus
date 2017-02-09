import wx
import wx.lib.newevent
import glob
import os

import psconstants as psc
from pslist import PSList
 
from psstatbox import PSStatBox
#from psfilter import PSFilter
from pssimplefilter import PSSimpleFilter
from psCalendar import CalendarTextbox

from psproxydialog import PSProxyDialog
from pskeydialog import PSKeyDialog
from pskeydialog import PSSetKeyDialog

from psguiconstants import GUI_WINDOW_VARIANT

class PSBrowser(wx.Frame):


    def __init__(self, parent, id, title, userType, centreCode, filtersCallback, quickFiltersCallback, petalsCallback, exportDataCallback, exportDataOverviewCallback, uploadDBCallback, gridDataCallback, admissionsToEvaluateCallback, statsCallback, openAdmissionCallback, newAdmissionCallback, quickCompilationCallback, quickCompilationPagesCallback, userPrefsCallback, userManagerCallback, proxyCallback, testConnectionCallback, privateKeyCallback, setPrivateKeyCallback, dischargeLetterModelCallback, closeCallback, logoutCallback, helpCallback, aboutCallback, quickCompilationSelectionCallback, printCallback, showConfigurationCallback, showCustomizationCallback, onExportMappingCallback, moveMasterConfigurationCallback, showNotificationCallback, firstLogin=False, shouldAnonymizeData=False):
        wx.Frame.__init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="browser")
        self.shouldAnonymizeData = shouldAnonymizeData
        self.userType = userType
        self.firstLogin = firstLogin
        self.centreCode = centreCode
        self.onExportMappingCallback = onExportMappingCallback
        self.filtersCallback = filtersCallback
        self.quickFiltersCallback = quickFiltersCallback
        self.petalsCallback = petalsCallback
        self.exportDataCallback = exportDataCallback
        self.exportDataOverviewCallback = exportDataOverviewCallback
        self.uploadDBCallback = uploadDBCallback
        self.gridDataCallback = gridDataCallback
        self.admissionsToEvaluateCallback = admissionsToEvaluateCallback
        self.statsCallback = statsCallback
        self.openAdmissionCallback = openAdmissionCallback
        self.newAdmissionCallback = newAdmissionCallback
        self.quickCompilationCallback = quickCompilationCallback
        self.quickCompilationPagesCallback = quickCompilationPagesCallback
        self.userPrefsCallback = userPrefsCallback
        self.userManagerCallback = userManagerCallback
        self.proxyCallback = proxyCallback
        self.testConnectionCallback = testConnectionCallback
        self.privateKeyCallback = privateKeyCallback
        self.setPrivateKeyCallback = setPrivateKeyCallback
        self.dischargeLetterModelCallback = dischargeLetterModelCallback
        self.closeCallback = closeCallback
        self.logoutCallback = logoutCallback
        self.helpCallback = helpCallback
        self.aboutCallback = aboutCallback
        self.quickCompilationSelectionCallback = quickCompilationSelectionCallback
        self.printCallback = printCallback
        self.showConfigurationCallback = showConfigurationCallback
        self.showNotificationCallback = showNotificationCallback
        self.showCustomizationCallback = showCustomizationCallback
        self.moveMasterConfigurationCallback = moveMasterConfigurationCallback
                
        icon1 = wx.Icon(os.path.join(psc.imagesPath, 'man2.ico'), wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)
     
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.SetBackgroundColour(wx.NullColor);
      
        self.initMenu()
        self.initStatusBar()
        self.initToolBar()
        
        self.initFilter()

        self.initList()
        self.initStats()
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        
        #self.quickCompilationMode = None
        self.Bind(wx.EVT_CLOSE, self.onClose, self)
        self.Bind(wx.EVT_SIZE,self.onResize) 
        self.Bind(wx.EVT_MAXIMIZE,self.onResize) 
        self.Bind(wx.EVT_ACTIVATE,self.onShow) 

        NeedColumnWidthUpdateEvent, EVT_COL_WIDTH_UPDATE = wx.lib.newevent.NewEvent()
        self.Bind(EVT_COL_WIDTH_UPDATE,self.onNeedColumnWidthUpdate)
        self.needColumnWidthUpdateEvent = NeedColumnWidthUpdateEvent
        
    def onShow(self, event):
        if self.firstLogin and self.userType >= psc.USER_ADMIN:
            self.firstLogin = False
            wx.CallAfter(self.showPrivateKey)
        #wx.CallAfter(self.listView.SortListItems,1,False)
        event.Skip()

    def onNeedColumnWidthUpdate(self, event):
        self.listView.updateColumnWidths()

    def onResize(self, event):
        #self.listView.updateColumnWidths()
        wx.PostEvent(self,self.needColumnWidthUpdateEvent())
        event.Skip()

    def onClose(self, event):
        if event.GetClassName() == 'wxCommandEvent':
            self.closeCallback()
            return
        self.logoutCallback()

    def onLogout(self, event):
        self.logoutCallback()

    def onShowHelp(self, event):
        self.helpCallback()

    def onShowAbout(self, event):
        self.aboutCallback()

    def onUploadDB(self, event):
        self.uploadDBCallback()

    def initMenu(self):

        menuBar = wx.MenuBar()
        from mainlogic import _

        menu = wx.Menu()
        menuLogout = menu.Append(-1, _("&Log Out"))
        menuExit = menu.Append(-1, _("&Exit"))
        menuBar.Append(menu, _("&File"))
 
        if self.userType >= psc.USER_ADMIN:
            menuAdministration = wx.Menu()
            menuUsers = menuAdministration.Append(-1, _("Manage users"))
            menuAdministration.AppendSeparator()
            #if psc.appName == 'prosafe':
            if 'dischargeLetter' in psc.toolBarApplications:
                menuDischarge = menuAdministration.Append(-1, _("Discharge letter model"))
                menuAdministration.AppendSeparator()
                self.Bind(wx.EVT_MENU, self.onShowDischargeLetterModel, menuDischarge)
            if 'personalizations' in psc.toolBarApplications:
                menuCustomization = menuAdministration.Append(-1, _("Customization"))
                self.Bind(wx.EVT_MENU, self.onShowCustomization, menuCustomization)
            menuAdministration.AppendSeparator()
            menuProxy = menuAdministration.Append(-1, _("&Proxy settings"))
            menuAdministration.AppendSeparator()
            menuPrivateKey = menuAdministration.Append(-1, _("&Show private key"))
            menuSetPrivateKey = menuAdministration.Append(-1, _("&Modify private key"))

            menuBar.Append(menuAdministration, _("&Administration"))

            self.Bind(wx.EVT_MENU, self.onShowUserManager, menuUsers)     
            
            
            self.Bind(wx.EVT_MENU, self.onProxySettings, menuProxy)     
            self.Bind(wx.EVT_MENU, self.onPrivateKey, menuPrivateKey)     
            self.Bind(wx.EVT_MENU, self.onSetPrivateKey, menuSetPrivateKey)     
 
        menuH = wx.Menu()
        menuHelp = menuH.Append(-1,  _("&Application Help"))
        menuAbout = menuH.Append(-1,  _("&About"))
        menuBar.Append(menuH, _("&Help"))
        
        self.SetMenuBar(menuBar)
        
        self.Bind(wx.EVT_MENU, self.onClose, menuExit)
        self.Bind(wx.EVT_MENU, self.onLogout, menuLogout)
        self.Bind(wx.EVT_MENU, self.onShowHelp, menuHelp)
        self.Bind(wx.EVT_MENU, self.onShowAbout, menuAbout)
        
    def initStatusBar(self):
        # Crea una barra di stato con due pannelli.
        self.CreateStatusBar(4)
        # Imposta il testo della barra di stato.
        self.SetStatusText("")

    def initToolBar(self):
        from mainlogic import _
        #toolbar = self.CreateToolBar(style = wx.TB_HORIZONTAL | wx.TB_TEXT | wx.TB_FLAT)
        self.toolbar = self.CreateToolBar(style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT)
        self.toolbar.SetToolBitmapSize((48,48))
 
        if self.userType >= psc.USER_EDITOR:
            
            bmp_new = wx.Image(os.path.join(psc.imagesPath, 'new.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_new = self.toolbar.AddLabelTool(-1, _("New admission"), bmp_new, longHelp= _("Click to open a new admission"))
            self.Bind(wx.EVT_MENU, self.onNewAdmission, tool_new)
            self.toolbar.AddSeparator()
        
        if self.userType < psc.USER_ADMIN:
            bmp_userpref = wx.Image(os.path.join(psc.imagesPath, 'user.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_userpref = self.toolbar.AddLabelTool(-1, _("User preferences"), bmp_userpref, longHelp=_("Click to manage preferences"))
            self.Bind(wx.EVT_MENU, self.onShowUserPrefs, tool_userpref)
            self.toolbar.AddSeparator()
        
        #if self.userType >= psc.USER_EDITOR:
        #    
        #    bmp_new = wx.Image('images/upload.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #    tool_new = toolbar.AddLabelTool(-1, _("Upload data"), bmp_new, longHelp=_("Click to upload data to PROSAFE central server"))
        #    self.Bind(wx.EVT_MENU, self.onUploadDB, tool_new)
        #    toolbar.AddSeparator()
            
        if self.userType >= psc.USER_MANAGER:
            if 'export' in psc.toolBarApplications:
                bmp_new = wx.Image(os.path.join(psc.imagesPath, 'export.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                tool_new = self.toolbar.AddLabelTool(-1, _("Export data"), bmp_new, longHelp=_("Click to export data in CSV format"))
                self.Bind(wx.EVT_MENU, self.onExportData, tool_new)
            if 'overview' in psc.toolBarApplications:
                bmp_new = wx.Image(os.path.join(psc.imagesPath, 'descriptive.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                tool_export_overview = self.toolbar.AddLabelTool(-1, _("Get overview table"), bmp_new, longHelp=_("Click to get an overview table in excel format"))
                self.Bind(wx.EVT_MENU, self.onExportDataOverview, tool_export_overview)
            
            #bmp_new = wx.Image(os.path.join(psc.imagesPath, 'aspreadsheet.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            #tool_mapping = self.toolbar.AddLabelTool(-1, _("MAPPING"), bmp_new, longHelp=_("mapping"))
            #self.Bind(wx.EVT_MENU, self.onExportMapping, tool_mapping)
            
            self.toolbar.AddSeparator()
            
            #config
            """
            bmp_customize = wx.Image('images/customize.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_customize = self.toolbar.AddSimpleTool(-1, bmp_customize, "Fields customization", "Click to edit custom fields")
            self.Bind(wx.EVT_MENU, self.GetParent().showFieldsCustomizer, tool_customize)"""
            
            #self.toolbar.AddSeparator()
        
        if self.userType >= psc.USER_ADMIN:
            
            #TEMPORARY
            #master migration / database upload / force sync
            #bmp_move = wx.Image(os.path.join(psc.imagesPath, 'move.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            #tool_movemaster = self.toolbar.AddLabelTool(-1, _("Move master"), bmp_move, longHelp=_("Click to move master configuration"))
            #self.Bind(wx.EVT_MENU, self.moveMasterConfigurationCallback, tool_movemaster)
            
            
            #users
            bmp_configuration = wx.Image(os.path.join(psc.imagesPath, 'configuration.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_configuration = self.toolbar.AddLabelTool(-1, _("Manage configuration"), bmp_configuration, longHelp=_("Click to manage configuration"))
            self.Bind(wx.EVT_MENU, self.showConfigurationCallback, tool_configuration)
            
            ##config
            #bmp_configure = wx.Image('images/configure.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            #tool_configure = self.toolbar.AddLabelTool(-1, _("Configuration"), bmp_configure, longHelp=_("Click to edit software configuration"))
            #self.Bind(wx.EVT_MENU, self.GetParent().showClientConfig, tool_configure)
            
            self.toolbar.AddSeparator()
 
            #bmp_info = wx.Image(os.path.join(psc.imagesPath, 'editdischargeletter.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            #tool_info = self.toolbar.AddLabelTool(-1, _("Discharge letter model"), bmp_info, longHelp=_("Click to edit the discharge letter model"))
            #self.Bind(wx.EVT_MENU, self.onShowDischargeLetterModel, tool_info)
            #
            #self.toolbar.AddSeparator()
    
        #quick compilation 
        if self.userType >= psc.USER_EDITOR:
            if 'quickCompilation' in psc.toolBarApplications:
                bmp_quick = wx.Image(os.path.join(psc.imagesPath, 'quick.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                self.tool_quick = self.toolbar.AddLabelTool(-1, _("Quick compilation"), bmp_quick, longHelp=_("Click to open the selection of quick compilation mode"))
                self.Bind(wx.EVT_MENU, self.onQuickCompilation, self.tool_quick)
            if 'printList' in psc.toolBarApplications:
                bmp_print = wx.Image(os.path.join(psc.imagesPath, 'printer.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                self.tool_print = self.toolbar.AddLabelTool(-1, _("Print current list"), bmp_print, longHelp=_("Click to print the patient list with the current active filter"))
                self.Bind(wx.EVT_MENU, self.onPrint, self.tool_print)
        
        #notifications
        if 'notification' in psc.toolBarApplications:
            bmp_notification = wx.Image(os.path.join(psc.imagesPath, 'notification.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            self.tool_notification = self.toolbar.AddLabelTool(-1, _("notification"), bmp_notification, longHelp=_("View notifications"))
            self.Bind(wx.EVT_MENU, self.showNotification, self.tool_notification)
        
        #logout 
        bmp_logout = wx.Image(os.path.join(psc.imagesPath, 'logout.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_logout = self.toolbar.AddLabelTool(-1, _("Logout"), bmp_logout, longHelp=_("Click to logout"))
        self.Bind(wx.EVT_MENU, self.onLogout, tool_logout)
       
        quickCompilationPages = self.quickCompilationPagesCallback()
        choiceStrings = set()
        choiceStrings.add('')
        self.quickCompilationChoiceDict = dict()
        for crfName in quickCompilationPages:
            for version in quickCompilationPages[crfName]:
                for page in quickCompilationPages[crfName][version]:
                    #choiceString = '%s - %s' % (crfName,pageName)
                    choiceString = page['pageName']
                    choiceStrings.add(choiceString)
                    if choiceString not in self.quickCompilationChoiceDict:
                        self.quickCompilationChoiceDict[choiceString] = {'crfName':crfName, 'pageName':page['pageName'], 'crfVersions':[]}
                    self.quickCompilationChoiceDict[choiceString]['crfVersions'].append(version)
        
        #choiceStrings = list(choiceStrings)
        #choiceStrings.sort()
        #self.quickCompilationChoice = wx.Choice(self.toolbar, -1, choices=choiceStrings, size=wx.Size(-1,-1))
        #self.quickCompilationChoice.Bind(wx.EVT_CHOICE, self.onChooseQuickInsertCrf)

        #self.toolbar.AddSeparator()
        #self.toolbar.AddControl(wx.StaticText(self.toolbar,-1,_('Quick compilation')+':'))
        #self.toolbar.AddControl(self.quickCompilationChoice)
 
        #EXPORT
        """bmp_exp = wx.Image('images/spreadsheet.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_exp = self.toolbar.AddSimpleTool(-1, bmp_exp, "Export data", "Click to export data")
        self.Bind(wx.EVT_MENU, self.GetParent().showExport, tool_exp)"""
            
        self.toolbar.Realize()

    #def onChooseQuickInsertCrf(self, event):
    #    quickCompilationPages = self.quickCompilationPagesCallback(admissionData['admissionDate']) # dict by crfName -> [pageName1, pageName2, ...]

    def onQuickCompilation(self, event):
        #self.quickCompilationMode = self.quickCompilationSelectionCallback()
        self.quickCompilationSelectionCallback()
    
    def onPrint(self, event):
        self.printCallback()
        
    def showNotification(self, event):
        self.showNotificationCallback()
    
    def onShowDischargeLetterModel(self, event):
        self.dischargeLetterModelCallback()

    def onShowCustomization(self, event):
        self.showCustomizationCallback()
        
    def onProxySettings(self, event):
        address, username, password = self.proxyCallback()

        proxyDlg = PSProxyDialog(None,-1,activation=False,address=address,username=username,password=password,testConnectionCallback=self.testConnectionCallback)
        proxyDlg.Center()
        proxyDlg.ShowModal()

        if proxyDlg.exitFlag:
            proxyDlg.Destroy()
            return

        address = proxyDlg.address.GetValue()
        username = proxyDlg.username.GetValue()
        password = proxyDlg.password.GetValue()

        address = address.replace('http://','')

        self.proxyCallback(address,username,password)

        proxyDlg.Destroy()

    def onPrivateKey(self, event):
        self.showPrivateKey()

    def onSetPrivateKey(self, event):
        self.setPrivateKey()

    def setPrivateKey(self):
        keyDlg = PSSetKeyDialog(self,-1,self.privateKeyCallback,self.setPrivateKeyCallback)
        keyDlg.Center()
        keyDlg.ShowModal()

    def setPrivateKeyCallback(self,privateKey):
        self.setPrivateKeyCallback(privateKey)

    def showPrivateKey(self):
        privateKey = self.privateKeyCallback()
        keyDlg = PSKeyDialog(self,-1,privateKey)
        keyDlg.Center()
        keyDlg.ShowModal()

    def onShowUserPrefs(self, event):
        self.userPrefsCallback()

    def onShowUserManager(self, event):
        self.userManagerCallback()

    def onNewAdmission(self, event):
        self.newAdmissionCallback()
 
    def initFilter(self):
        self.sizer.AddSpacer(3)
        self.filterbox = PSSimpleFilter(self, -1, applyFiltersCallback = self.panelFiltersCallback)
        self.sizer.Add(self.filterbox, 0, wx.GROW)
    
    def initStats(self):
        self.sizer.AddSpacer(3)
        self.statbox = PSStatBox(self, -1, size=wx.Size(0, 100))
        self.sizer.Add(self.statbox, 1, wx.EXPAND)
        stats = self.statsCallback()
        self.statbox.refreshData(stats)
       
    def initList(self):
        self.sizer.AddSpacer(3)
        from mainlogic import _
        
        self.sizer.AddSpacer(5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddStretchSpacer()

        label = wx.StaticText(self, -1, _("Admission year")+":")
        from datetime import date
        currentYear = date.today().year
        years = range(2010,currentYear+1)
        self.yearChoice = wx.Choice(self, -1, size=wx.Size(100,-1), choices=['']+[str(el) for el in years])
        self.yearChoice.SetWindowVariant(GUI_WINDOW_VARIANT)
        #self.yearChoice.SetSelection(len(years))
        self.yearChoice.Bind(wx.EVT_CHOICE, self.onQuickFiltersChanged)
        hbox.Add(label)
        hbox.AddSpacer(5)
        hbox.Add(self.yearChoice)

        hbox.AddStretchSpacer()

        label = wx.StaticText(self, -1, _("Core status")+":")
        self.coreStatusChoice = wx.Choice(self, -1, choices=['','1','2','3','4','5','<3','<4'])
        self.coreStatusChoice.SetWindowVariant(GUI_WINDOW_VARIANT)
        self.coreStatusChoice.Bind(wx.EVT_CHOICE, self.onQuickFiltersChanged)
        hbox.Add(label)
        hbox.AddSpacer(5)
        hbox.Add(self.coreStatusChoice)

        hbox.AddStretchSpacer()
        if 'petals' in psc.toolBarApplications:
            label = wx.StaticText(self, -1, _("Petal status")+":")
            self.petalChoice = wx.Choice(self, -1, size=wx.Size(100,-1), choices=['']+self.petalsCallback())
            self.petalChoice.SetWindowVariant(GUI_WINDOW_VARIANT)
            self.petalChoice.Bind(wx.EVT_CHOICE, self.onQuickFiltersChanged)
            self.petalStatusChoice = wx.Choice(self, -1, choices=['','1','2','3','<3'])
            self.petalStatusChoice.SetWindowVariant(GUI_WINDOW_VARIANT)
            self.petalStatusChoice.Bind(wx.EVT_CHOICE, self.onQuickFiltersChanged)
            hbox.Add(label)
            hbox.AddSpacer(5)
            hbox.Add(self.petalChoice)
            hbox.AddSpacer(5)
            hbox.Add(self.petalStatusChoice)

        hbox.AddStretchSpacer()

        self.removeButton = wx.Button(self, -1, _("Remove quick filters"))
        self.removeButton.SetWindowVariant(GUI_WINDOW_VARIANT)
        self.removeButton.Bind(wx.EVT_BUTTON, self.onRemoveQuickFilters)
 
        hbox.Add(self.removeButton)
        hbox.AddSpacer(10)

        self.filterWarning = wx.StaticText(self, -1, _("The search filter is active"), style = wx.ALIGN_CENTRE)
        self.filterWarning.SetBackgroundColour('yellow')
        self.sizer.Add(self.filterWarning, 0, wx.EXPAND)
        self.sizer.Hide(self.filterWarning)
 
        self.yearWarning = wx.StaticText(self, -1, _("Only admissions for the current year are shown"), style = wx.ALIGN_CENTRE)
        self.yearWarning.SetBackgroundColour('light blue')
        self.sizer.Add(self.yearWarning, 0, wx.EXPAND)
        self.sizer.Hide(self.yearWarning)

        self.sizer.Add(hbox, 0, wx.EXPAND)

        vsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.listView = PSList(self, self.centreCode, self.onOpenAdmission, self.shouldAnonymizeData)
        vsizer.Add(self.listView, 1, wx.EXPAND)

        self.sizer.Add(vsizer, 8, wx.EXPAND)
        
        il = wx.ImageList(16,16, True)
        for name in glob.glob("smicon??.png"):
            bmp = wx.Bitmap(name, wx.BITMAP_TYPE_PNG)
            il_max = il.Add(bmp)

    def onOpenAdmission(self,admissionData):
        #quickCompilationSelection = self.quickCompilationMode
        quickCompilationSelection = self.quickCompilationSelectionCallback(returnPage=True)
        if not quickCompilationSelection:
            self.openAdmissionCallback(admissionData)
            return
        choiceDict = self.quickCompilationChoiceDict[quickCompilationSelection]
        quickCrfName = choiceDict['crfName']
        quickCrfVersions = choiceDict['crfVersions']
        quickPageName = choiceDict['pageName']
        isVersionValid = self.quickCompilationPagesCallback(quickCrfName,quickCrfVersions,admissionData['admissionDate'])
        from mainlogic import _
        if not isVersionValid:
            dlg = wx.MessageDialog(self, _("Quick compilation page not available for the CRF version associated to this admission."), _("Warning"), wx.OK)
            dlg.Center()
            dlg.ShowModal()
            return
        self.quickCompilationCallback(admissionData,quickCrfName,quickPageName)

    def sortList(self,sortColumn,sortAscending):
        self.listView.sortColumn = sortColumn
        self.listView.sortAscending = sortAscending
        self.listView.DoSort()

    def selectItem(self,admissionKey):
        self.listView.selectItem(admissionKey)

    def getSortStatus(self):
        return (self.listView.sortColumn, self.listView.sortAscending)

    #def onApplyDateRangeFilter(self,event):
    #    self.onQuickFiltersChanged(event)

    def onRemoveQuickFilters(self,event):
        quickFilters = dict()
        #quickFilters['FirstName'] = ''
        #quickFilters['LastName'] = ''
        #quickFilters['EhrId'] = ''
        #quickFilters['AdmissionMinDate'] = ''
        #quickFilters['AdmissionMaxDate'] = ''
        #quickFilters['AdmissionHours'] = ''
        quickFilters['AdmissionYear'] = ''
        quickFilters['CoreStatus'] = ''
        quickFilters['Petal'] = ''
        quickFilters['PetalStatus'] = ''
        cursor = wx.BusyCursor()
        self.quickFiltersCallback(quickFilters)

    def panelFiltersCallback(self,filtersDict):
        quickFilters = self.quickFiltersCallback()
        quickFilters.update(filtersDict)
        cursor = wx.BusyCursor()
        self.quickFiltersCallback(quickFilters)
        if [filtersDict[key] for key in filtersDict if filtersDict[key]]:
            self.sizer.Show(self.filterWarning)
        else:
            self.sizer.Hide(self.filterWarning)
        self.Layout()
        self.Refresh()

    def onQuickFiltersChanged(self,event):
        quickFilters = dict()
        #if self.dateMin.GetValue().IsValid():
        #    quickFilters['AdmissionMinDate'] = self.dateMin.GetValue().FormatISODate()
        #if self.dateMax.GetValue().IsValid():
        #    quickFilters['AdmissionMaxDate'] = self.dateMax.GetValue().FormatISODate()
        quickFilters['AdmissionYear'] = self.yearChoice.GetStringSelection()
        quickFilters['CoreStatus'] = self.coreStatusChoice.GetStringSelection()
        if psc.appName == 'prosafe':
            quickFilters['Petal'] = self.petalChoice.GetStringSelection()
            quickFilters['PetalStatus'] = self.petalStatusChoice.GetStringSelection()
        quickFilters.update(self.filterbox.getFiltersDict())
        cursor = wx.BusyCursor()
        self.quickFiltersCallback(quickFilters)

    def updateQuickFilterControls(self):
        quickFilters = self.quickFiltersCallback()
        #thisdate = wx.DateTime()
        #try:
        #    thisdate.ParseFormat(quickFilters['AdmissionMinDate'],'%Y-%m-%d')
        #    self.dateMin.SetValue(thisdate)
        #except:
        #    pass
        #try:
        #    thisdate.ParseFormat(quickFilters['AdmissionMaxDate'],'%Y-%m-%d')
        #    self.dateMax.SetValue(thisdate)
        #except:
        #    pass
        self.yearChoice.SetStringSelection(quickFilters['AdmissionYear'])
        if psc.appName == 'prosafe':
            self.petalChoice.SetStringSelection(quickFilters['Petal'])
            self.petalStatusChoice.SetStringSelection(quickFilters['PetalStatus'])
        self.coreStatusChoice.SetStringSelection(quickFilters['CoreStatus'])
        self.filterbox.updateFilterControls(quickFilters)
            
    def onExportData(self,event):
        self.exportDataCallback()
        
    def onExportDataOverview(self,event):
        self.exportDataOverviewCallback()
        
    def onExportMapping(self,event):
        self.onExportMappingCallback()

    def refreshList(self, flagMake=True):
        gridData = self.gridDataCallback()
        if flagMake:
            admissionsToEvaluate = self.admissionsToEvaluateCallback(gridData)
        else:
            admissionsToEvaluate = None
        self.listView.refreshData(gridData,admissionsToEvaluate)
        stats = self.statsCallback()
        self.statbox.refreshData(stats)
        self.updateQuickFilterControls()
        
    def populateList(self, flagMake=True):

        filters = self.filtersCallback()
        if not filters:
            self.sizer.Hide(self.filterWarning)
        else:
            self.sizer.Show(self.filterWarning)
 
        #if not currentYear:
        #    self.sizer.Hide(self.yearWarning)
        #else:
        #    self.sizer.Show(self.yearWarning)
        
        self.sizer.Layout()
        self.refreshList(flagMake)

    def uploadDB(self,event):
        result = self.uploadDBCallback()
        if result == True:
            dlg = wx.MessageDialog(self, _("Data has been successfully uploaded."), _("Success"), wx.OK)
            dlg.Center()
            dlg.ShowModal()
        else:
            dlg = wx.MessageDialog(self, _("Data upload failed, check network connection."), _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()

