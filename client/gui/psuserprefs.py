import wx
import psconstants as psc
from validators import PasswordOrEmptyValidator, PasswordAgainValidator

ID_SAVE = 100
ID_CANCEL = 101
ID_SAVE_AND_EXIT = 102
 
class PSUserPrefs(wx.Dialog):
    def __init__(self, parent, mainLogic):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1, title=_('User preferences'), pos=wx.DefaultPosition, size=wx.Size(300,300), style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER, name="userprefs")
        
        self.mainLogic = mainLogic

        self.username = self.mainLogic.username
        self.translationMode = self.mainLogic.translationMode
                
        sizer = wx.BoxSizer(wx.VERTICAL)
                
        self.nbook = wx.Notebook(self, -1)
               
        #userlanguage
        self.langs = UserLang(self.nbook, self.mainLogic)
        self.nbook.AddPage(self.langs, _("Language"))
        
        #passwords
        self.pwds = userPwd(self.nbook)
        self.nbook.AddPage(self.pwds, "Password")
        
        #translation mode
        self.translation = TranslationMode(self.nbook, self.mainLogic)
        self.nbook.AddPage(self.translation, _("Translation mode"))
        
        sizer.Add(self.nbook, 1, wx.EXPAND)
 
        #buttons 
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, ID_SAVE, _('Save'))
        btnDue = wx.Button(self, ID_SAVE_AND_EXIT, _('Save and exit'))
        
        #event binding
        self.Bind(wx.EVT_BUTTON, self.doSaveUserPrefs, id=ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.doSaveUserPrefs, id=ID_SAVE_AND_EXIT)

        box.Add(btnDue, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.AddSpacer(5)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.AddSpacer(5)
        btnc = wx.Button(self, ID_CANCEL, _('Cancel'))
 
        btnDue.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.doClose, id=ID_CANCEL)

        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)

        sizer.AddSpacer(10) 
        sizer.Add(box, 0, wx.ALIGN_CENTRE | wx.ALIGN_BOTTOM)
        sizer.AddSpacer(10) 
        
        self.SetSizer(sizer)
        self.Fit()
    
    def doClose(self, event):
        self.Destroy()
        
    def doSaveUserPrefs(self, event):
        """saves the preferences set for the selected tab, either lang or passwords"""
        from mainlogic import _
        if self.nbook.GetSelection() == 0:
            #page selected is lang page
            lang =  self.langs.lang.GetValue()
            saveOk = self.mainLogic.doSaveUserLang(self.mainLogic.username, lang)
            if(saveOk == True):
               dlg = wx.MessageDialog(self, _('Language preferences saved'), _('Language preferences saved'), wx.OK )
            else:
               dlg = wx.MessageDialog(self, _('Errors occured while saving language preferences'), _('Language preferences NOT saved!'), wx.OK )
            dlg.ShowModal()
            dlg.Destroy()
        elif self.nbook.GetSelection() == 1:
            #page selected is passwords page
            opassword =  self.pwds.opassword.GetValue()
            npassword =  self.pwds.npassword.GetValue()
            rnpassword =  self.pwds.rnpassword.GetValue()
            opassword = opassword.strip()
            npassword = npassword.strip()
            rnpassword = rnpassword.strip()
            if self.pwds.Validate():
                if len(npassword) == 0 or len(opassword) == 0 or len(rnpassword) == 0:
                    dlg = wx.MessageDialog(self, _('Please fill each field'), _('Blank fields'), wx.OK )
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    if self.mainLogic.doControlPwd(self.mainLogic.username, opassword) == True:
                        #old password is correct
                        if opassword != npassword:
                            saveOk = self.mainLogic.doSavePassword(self.mainLogic.username, npassword)
                            if(saveOk == True):
                               dlg = wx.MessageDialog(self, _('New password saved'), _('New password saved'), wx.OK )
                            else:
                               dlg = wx.MessageDialog(self, _('Errors occured while saving new password.'), _('New password not saved'), wx.OK )
                        else:
                            dlg = wx.MessageDialog(self, _('New password must be different from old password'), _('New password not saved'), wx.OK )
                        
                        dlg.ShowModal()
                        dlg.Destroy()
                    else:
                        dlg = wx.MessageDialog(self, _('Old password is wrong'), _('New password not saved'), wx.OK )
                        dlg.ShowModal()
                        dlg.Destroy()
            self.pwds.opassword.SetValue('')
            self.pwds.npassword.SetValue('')
            self.pwds.rnpassword.SetValue('')
        elif self.nbook.GetSelection() == 2:
            translationModeDialogString = ''
            if self.translation.radioBox.GetStringSelection() == _("Activated"):
                self.mainLogic.setTranslationModeSetting(True)
                translationModeDialogString = _('Translation mode has been activated!')
            elif self.translation.radioBox.GetStringSelection() == _("Deactivated"):
                self.mainLogic.setTranslationModeSetting(False)
                translationModeDialogString = _('Translation mode has been deactivated!')
            dlg = wx.MessageDialog(self,translationModeDialogString, _('Translation mode'), wx.OK )
            dlg.ShowModal()
            dlg.Destroy()
        if event.Id == 102:
            self.doClose(None)
 
class userPwd(wx.Panel):

    def __init__(self, parent):
        from mainlogic import _
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(30)
           
        #OLD password    
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10) 
        label = wx.StaticText(self, -1, _("Old Password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.opassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD)
        box.Add(self.opassword, 2, wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)
           
        #new password    
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("New password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.npassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD, validator=PasswordOrEmptyValidator())
        box.Add(self.npassword, 2,wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        #new password again
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Confirm password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.rnpassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD, validator=PasswordAgainValidator(self.npassword))
        box.Add(self.rnpassword, 2, wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)
        sizer.AddSpacer(30)

        #final setup
        self.SetSizer(sizer)
        self.Fit()
         
         
class UserLang(wx.Panel):
    def __init__(self, parent, mainLogic):
        from mainlogic import _ 
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(30)
           
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        
        label = wx.StaticText(self, -1, _("Language"))
        box.Add(label, 1,  wx.ALIGN_RIGHT)
        
        box.AddSpacer(5)
        
        langList = mainLogic.getLanguageNames()
        
        currentLang = mainLogic.userLanguage
        
        self.lang = wx.ComboBox(self, 500, currentLang, choices=langList,style=wx.CB_DROPDOWN  | wx.CB_READONLY  )
        box.Add(self.lang, 2, wx.EXPAND)
        box.AddSpacer(10)
        
        sizer.Add(box, 0,  wx.EXPAND)
        sizer.AddSpacer(10)

        #final setup
        self.SetSizer(sizer)
        #
        #sizer.Fit(self)
        
class TranslationMode(wx.Panel):
    def __init__(self, parent, mainLogic):
        from mainlogic import _ 
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(30)
           
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        translationMode = mainLogic.translationMode
        label = wx.StaticText(self, -1, _("Translation mode"))
        box.Add(label, 1,  wx.ALIGN_RIGHT)
        
        box.AddSpacer(5)
        
        optionList = [_("Activated"), _("Deactivated")]
        self.radioBox =  wx.RadioBox(self, -1, _("Activation options"), wx.DefaultPosition, wx.DefaultSize, optionList, 1, wx.RA_SPECIFY_COLS)
        if translationMode:
            self.radioBox.SetSelection(0)
        else:
            self.radioBox.SetSelection(1)
        
        box.Add(self.radioBox, 2, wx.EXPAND)
        box.AddSpacer(10)
        
        sizer.Add(box, 0,  wx.EXPAND)
        sizer.AddSpacer(10)

        #final setup
        self.SetSizer(sizer)
        #
        #sizer.Fit(self)
