# -*- coding: utf-8 -*-

import wx
from psversion import PROSAFE_VERSION
import os
import psconstants as psc
import wx.lib.platebtn as platebtn
import wx.lib.agw.genericmessagedialog as GMD

ID_LOGIN = 100
ID_OUT = 101
ID_IMPORT = 102


class LoginDialog(wx.Dialog):
    def __init__(self, parent, loginCallback, quitCallback, requestNewPasswordCallback, isMaster, getCentreCodeCallback):
        from mainlogic import _
        #wx.Dialog.__init__(self, parent, id=-1, title='Login', pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.CENTER | wx.STAY_ON_TOP, name="loginframe")
        wx.Dialog.__init__(self, parent, id=-1, title=_("Login"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.MINIMIZE_BOX | wx.CENTER | wx.SYSTEM_MENU, name="loginframe") 

        self.getCentreCodeCallback  = getCentreCodeCallback
        self.loginCallback = loginCallback
        self.quitCallback = quitCallback
        self.requestNewPasswordCallback = requestNewPasswordCallback

        self.imageFile =  psc.splashFile
        bmp = wx.Image(self.imageFile,wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        sbitmap = wx.StaticBitmap(self,  -1,  bmp)
        centreCode = self.getCentreCodeCallback()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbitmap,0)
        #font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        #font.SetWeight(wx.FONTWEIGHT_BOLD)
        psversion = PROSAFE_VERSION
        if len(PROSAFE_VERSION.split('.')) > 3:
            psversion = '.'.join(PROSAFE_VERSION.split('.')[:-1])
        label = wx.StaticText(self, -1, _("Welcome to PROSAFE - Version ") + psversion)
        labelCentreCode = wx.StaticText(self, -1, _("CentreCode") + centreCode)
        font = label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        label.SetFont(font)
        labelCentreCode.SetFont(font)
        sizer.AddSpacer(10)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(10)
        sizer.Add(labelCentreCode, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Please log in with your username and password"))
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(35)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Username"))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.RIGHT, 10)

        self.user = wx.TextCtrl(self, -1, "", size=(150,-1))
        box.Add(self.user, 1, wx.ALIGN_CENTRE|wx.ALL, 0)

        #sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 10)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Password"))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.RIGHT, 10)

        self.password = wx.TextCtrl(self, -1, "", size=(150,-1),style=wx.TE_PASSWORD)
        box.Add(self.password, 1, wx.ALIGN_CENTRE|wx.ALL, 0)

        #sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.BOTTOM, 25)
                       
        questionLabel = wx.StaticText(self, -1, _('In case you are admin and you lost your password:'))
        sizer.Add(questionLabel, 0, wx.ALIGN_CENTRE|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        reqSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.requestLabel = wx.StaticText(self, -1, _('Request new admin password'))
        self.requestLabel.SetForegroundColour("Blue")
        self.requestLabel.Bind(wx.EVT_LEFT_UP, self.doRequestNewPassword)
        self.requestLabel.Bind(wx.EVT_ENTER_WINDOW, self.doHighlight)
        self.requestLabel.Bind(wx.EVT_LEAVE_WINDOW, self.undoHighlight)
        reqSizer.Add(self.requestLabel, 0, wx.ALIGN_CENTRE, 0)
        sizer.Add(reqSizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        sizer.AddSpacer(20)
        if 'scripts' in psc.toolBarApplications:
            self.fixerCheckBox = wx.CheckBox(self, -1, _("Fixer login"))
            fixerSizer = wx.BoxSizer(wx.HORIZONTAL)
            fixerSizer.Add(self.fixerCheckBox, 0, wx.ALL, 1)
            sizer.Add(fixerSizer, 0, wx.ALIGN_CENTRE|wx.TOP|wx.LEFT|wx.RIGHT, 5)
            
            fixerSizerHelp = wx.BoxSizer(wx.HORIZONTAL)
            fixerExplanationButton = platebtn.PlateButton(self, wx.ID_ANY, " ? ", None)
            fixerExplanationButton.Bind(wx.EVT_BUTTON, self.onFixerExplanationButton)
            fixerSizerHelp.Add(fixerExplanationButton, 0, wx.ALL, 1)        
            sizer.Add(fixerSizerHelp, 0, wx.ALIGN_CENTRE|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        
            if not isMaster:
                fixerExplanationButton.Show(False)
                self.fixerCheckBox.Show(False)
        
        btn = wx.Button(self, ID_LOGIN, _('Login'))
        btn.SetDefault()
        btnOut = wx.Button(self, ID_OUT, _('Exit'))
        
        self.Bind(wx.EVT_BUTTON, self.doLogin, id=ID_LOGIN)
        self.Bind(wx.EVT_BUTTON, self.doDestroy, id=ID_OUT)
        self.Bind(wx.EVT_CLOSE, self.doClose, self)
        sizer.AddSpacer(15)
        #sizer.Add(btn, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        #sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btnSizer.Add(btnOut, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSpacer(10)

        self.SetSizer(sizer)
        self.Fit()
        
    def onFixerExplanationButton(self, event):
        from mainlogic import _
        fixerExplanationMessage = _("Checking this button allows (ONLY) the admin user to access the fixing scripts collection." )
        title = _("Some explanation about fixer access.")
        dlg = GMD.GenericMessageDialog(self, fixerExplanationMessage,title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def doHighlight(self, event):
        font = self.requestLabel.GetFont()
        font.SetUnderlined(True)
        self.requestLabel.SetFont(font)

    def undoHighlight(self, event):
        font = self.requestLabel.GetFont()
        font.SetUnderlined(False)
        self.requestLabel.SetFont(font)

    def doLogin(self, event):
        user = self.user.GetValue()
        password = self.password.GetValue()
        fixerValue = None
        if 'scripts' in psc.toolBarApplications:
            fixerValue = self.fixerCheckBox.GetValue()
        self.loginCallback(user,password,fixerValue) 
    
    def doClose(self, event):
        self.quitCallback()

    def doDestroy(self, event):
        self.quitCallback()

    def doRequestNewPassword(self, event):
        from mainlogic import _
        from psmessagedialog import PSMessageDialog
        dlg = PSMessageDialog(None,
                            _("Really request a new password for user 'admin'?"),
                            _("Confirm"))
        dlg.Center()
        result = dlg.ShowModal()
        
        if dlg.returnValue == wx.ID_YES:
            requestResult = self.requestNewPasswordCallback()

            if requestResult:
                dlg = wx.MessageDialog(None, 
                                    _("A new password has been sent to the admin email address as specified in the PROSAFE Web Center. The old password will be working as usual until it is changed."),
                                    _("Request sent"), wx.OK | wx.ICON_INFORMATION)
                dlg.Center()
                dlg.ShowModal()
            else:
                dlg = wx.MessageDialog(None, 
                                    _("Error sending request to server. Internet connection might be down or unreacheable."),
                                    _("Request error"), wx.OK | wx.ICON_ERROR)
                dlg.Center()
                dlg.ShowModal()


class ActivationDialog(wx.Dialog):

    def __init__(self, parent, verifyActivationCallback, importMasterDataCallback):
    
        from mainlogic import _
        
        self.CREATE_NEW_DB_STRING = _("Create new database (First master installation) - Crea un nuovo database (prima installazione di un Master)")
        self.IMPORT_FROM_DATA_STRING = _("Import data from package when moving master (masterdata.pmd) - Importa dati per spostamento master (masterdata.pmd)")
    
        #wx.Dialog.__init__(self, parent, id=-1, title='Activation', pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.CENTER | wx.STAY_ON_TOP, name="activationframe")
        wx.Dialog.__init__(self, parent, id=-1, title=_("Activation"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.CENTER, name="activationframe")
 
        self.verifyActivationCallback = verifyActivationCallback
        self.importMasterDataCallback = importMasterDataCallback
 
        self.imageFile =  os.path.join(psc.imagesPath, "logologin.png")
        bmp = wx.Image(self.imageFile,wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        sbitmap = wx.StaticBitmap(self, -1, bmp)
        
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(outerSizer)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbitmap, 0, wx.ALIGN_CENTRE|wx.ALL)
        outerSizer.Add(sizer,0,wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT,border=20)

        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetWeight(wx.FONTWEIGHT_BOLD)

        label = wx.StaticText(self, -1, _("Welcome to PROSAFE"))
        label.SetFont(font)
        sizer.AddSpacer(10)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(20)
        label = wx.StaticText(self, -1, _("Please register your PROSAFE client with the Centre Code and the Activation Key you received via mail."))
        label.Wrap(350)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(20)

        gridSizer = wx.FlexGridSizer(2,2)
        sizer.Add(gridSizer, 0, wx.ALIGN_CENTRE|wx.ALL)

        label = wx.StaticText(self, -1, _("Centre code"))
        gridSizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        self.centreCode = wx.TextCtrl(self, -1, "", size=(300,-1))
        gridSizer.Add(self.centreCode, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        label = wx.StaticText(self, -1, _("Activation key"))
        gridSizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        self.activationKey = wx.TextCtrl(self, -1, "", size=(300,-1))
        gridSizer.Add(self.activationKey, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, ID_LOGIN, _("Verify activation key"))
        btnOut = wx.Button(self, ID_OUT, _("Exit"))
        
        optionList = [self.CREATE_NEW_DB_STRING, self.IMPORT_FROM_DATA_STRING]
        self.radioBox =  wx.RadioBox(self, -1, _("Activation options"), wx.DefaultPosition, wx.DefaultSize, optionList, 1, wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.onRadioBoxCheckChanged, self.radioBox)
        
        btn.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.onVerifyActivationCode, id=ID_LOGIN)
        self.Bind(wx.EVT_BUTTON, self.onDestroy, id=ID_OUT)
        self.Bind(wx.EVT_BUTTON, self.onImport, id=ID_IMPORT)

        sizer.AddSpacer(5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(btnOut, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        #box.Add(btnImport, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.AddSpacer(10)
        sizer.Add(self.radioBox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.AddSpacer(10)
        self.importStatusStaticText = wx.StaticText(self, -1, '', (20, 120))
        sizer.Add(self.importStatusStaticText, 0, wx.EXPAND|wx.ALL, 0)
        box = wx.BoxSizer(wx.VERTICAL)
        self.btnImport = wx.Button(self, ID_IMPORT, _("Import master data"))
        box.Add(self.btnImport, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Fit()
        self.centrecode = False
        self.btnImport.Show(False)

    def onRadioBoxCheckChanged(self, event):
        from mainlogic import _
        self.importStatusStaticText.SetLabel("")
        if event.GetString() == self.IMPORT_FROM_DATA_STRING:
            self.btnImport.Show(True)
            return
        self.btnImport.Show(False)
        
    def onImport(self, event):
        if not self.continueCurrentAction('import'):
            return
        result = self.importMasterDataCallback()
        from mainlogic import _
        if result == True:
            self.importStatusStaticText.SetLabel(_("Data succesfully loaded"))
            self.importStatusStaticText.SetForegroundColour((34,139,34))
            self.radioBox.Enable(False)
            self.btnImport.Show(False)
        
    def onDestroy(self, event):
        self.Show(False)
        self.centrecode = False
        
    def checkFileInDefaultDataFolder(self):
        import os
        from psconstants import abspath
        dataPath = abspath('data')
        if os.path.exists(dataPath):
            fileList = os.listdir(dataPath)
            #if 'prosafestore.sqlite' in fileList or 'appdata.xml' in fileList:
            if 'appdata.xml' in fileList:
                return False
        return True
        
    def continueCurrentAction(self, action):
        from mainlogic import _
        if action == 'activation':
            if self.radioBox.GetStringSelection() == self.IMPORT_FROM_DATA_STRING and self.importStatusStaticText.GetLabel() != _("Data succesfully loaded") :
                self.importStatusStaticText.SetLabel(_("CANNOT ACTIVATE OLD MASTER IF YOU DIDN'T IMPORT THE OLD PACKAGE"))
                self.importStatusStaticText.SetForegroundColour((172,34,34))
                return False
            #if self.radioBox.GetStringSelection() == self.CREATE_NEW_DB_STRING and not self.checkFileInDefaultDataFolder():
            #    self.importStatusStaticText.SetLabel(_("CANNOT ACTIVATE NEW MASTER IF DATA FOLDER IS NOT EMPTY."))
            #    self.importStatusStaticText.SetForegroundColour((172,34,34))
            #    return False
        else:
            if not self.checkFileInDefaultDataFolder():
                self.importStatusStaticText.SetLabel(_("CANNOT ACTIVATE NEW MASTER IF DATA FOLDER IS NOT EMPTY."))
                self.importStatusStaticText.SetForegroundColour((172,34,34))
                return False
        return True
        
    def onVerifyActivationCode(self, event):
        if not self.continueCurrentAction('activation'):
            return
        from mainlogic import _
        centreCode = self.centreCode.GetValue()
        activationKey = self.activationKey.GetValue()
        self.centrecode = self.verifyActivationCallback(centreCode,activationKey) 
        if self.centrecode:
            wx.MessageBox(_("Your PROSAFE client activation is completed."), _("Activation completed!"))
            #qui magari � il caso di mettere una domanda yes/no con la richiesta di una prima configurazione iniziale? 
            #ad esempio, per configurare subito la propria lingua e le varie opzioni? 
            self.Show(False)
        else:
            wx.MessageBox(_("The activation key is not valid. Please try again."), _("Activation NOT completed!"))

