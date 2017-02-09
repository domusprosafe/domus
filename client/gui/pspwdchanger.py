import wx
from validators import PasswordValidator
from validators import NotEmptyValidator
import psconstants as psc

ID_SAVE = 100
ID_CANCEL = 101

class PSPwdChanger(wx.Dialog):

    def __init__(self, parent, userInfo, changePasswordCallback, changeName=False):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1, title=_('Change password'), size=wx.Size(300,300), style=wx.DEFAULT_DIALOG_STYLE|wx.WS_EX_VALIDATE_RECURSIVELY, name="pwdchanger")
        self.userInfo = userInfo
        self.changePasswordCallback = changePasswordCallback
        self.changeName = changeName
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(30)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("New password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.npassword = wx.TextCtrl(self, -1, "", size=(80,-1),style=wx.TE_PASSWORD, validator=PasswordValidator())
        box.Add(self.npassword, 2,wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        sizer.AddSpacer(10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Confirm password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.rnpassword = wx.TextCtrl(self, -1, "", size=(80,-1),style=wx.TE_PASSWORD)
        box.Add(self.rnpassword, 2,wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        if self.changeName:

            sizer.AddSpacer(10)

            box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, _("Surname"))
            box.Add(label, 1, wx.EXPAND)
            box.AddSpacer(5)
            self.osurname = wx.TextCtrl(self, -1, '', size=(80,-1), validator=NotEmptyValidator())
            box.Add(self.osurname, 4, wx.EXPAND)
            sizer.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

            sizer.AddSpacer(10)

            box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, _("Name"))
            box.Add(label, 1, wx.EXPAND)
            box.AddSpacer(5)
            self.oname = wx.TextCtrl(self, -1, '', size=(80,-1), validator=NotEmptyValidator())
            box.Add(self.oname, 4, wx.EXPAND)
            sizer.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        sizer.AddSpacer(20)

        btn = wx.Button(self, ID_SAVE, _("OK"))
        btnc = wx.Button(self, ID_CANCEL, _("Cancel"))
        btn.SetDefault()
        
        sizer.AddSpacer(20)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(btn, 0)
        sizer.AddSpacer(10)
        box.Add(btnc, 0)
        sizer.Add(box, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(20)
        
        self.Bind(wx.EVT_BUTTON, self.doSavePwd, id=ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.doCancel, id=ID_CANCEL)
        
        self.SetSizer(sizer)
        self.Fit()
        
    def doCancel(self,event):
        self.userInfo['password'] = None
        self.EndModal(0)
        
    def doSavePwd(self, event):
                       
        name = ''
        surname = '' 
        if self.changeName:
            name = self.oname.GetValue()
            surname = self.osurname.GetValue()

        npassword = self.npassword.GetValue()
        rnpassword = self.rnpassword.GetValue()

        npassword = npassword.strip()
        rnpassword = rnpassword.strip()

        from mainlogic import _

        if self.Validate(): 
            if not npassword or npassword == self.userInfo['password']:
                dlg = wx.MessageDialog(self, _("You must enter a new password"), _('Error'), wx.OK )
                dlg.ShowModal()
            elif npassword != rnpassword:
                dlg = wx.MessageDialog(self, _('New password and confirmed password do not match'), _('Error'), wx.OK )
                dlg.ShowModal()
            else:
                self.userInfo['password'] = None
                saveOk = self.changePasswordCallback(self.userInfo['username'],npassword,name,surname)
                if saveOk == True:
                    dlg = wx.MessageDialog(self, _('New password saved'), _('Success'), wx.OK )
                    self.userInfo['password'] = npassword
                    self.EndModal(1)
                else:
                    dlg = wx.MessageDialog(self, _('Password save failed'), _('Error'), wx.OK )
                dlg.ShowModal()


