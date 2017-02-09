import wx
import wx.lib.newevent
from validators import PasswordOrEmptyValidator, NotEmptyValidator, UsernameValidator, PasswordValidator, PasswordAgainValidator
from pspwdchanger import PSPwdChanger
import psconstants as psc
import os

from wx.lib.buttons import GenBitmapTextButton

ID_SAVE = 100
ID_CANCEL = 101
ID_CREATE = 102
ID_TOGGLEENABLED = 103
ID_SAVEGROUP = 104
ID_EDIT = 105

class PSUserManager(wx.Frame):

    def __init__(self, parent, languages, usersCallback, createUserCallback, updateUserCallback, helpCallback, aboutCallback, position=wx.DefaultPosition, size=wx.DefaultSize):
        from mainlogic import _
       
        wx.Frame.__init__(self, parent, -1, _("User manager"), pos=position, size=size, style= wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT, name="usermmanager")

        self.languages = languages 
 
        self.usersCallback = usersCallback 
        self.createUserCallback = createUserCallback
        self.updateUserCallback = updateUserCallback
        self.helpCallback = helpCallback
        self.aboutCallback = aboutCallback
 
        icon1 = wx.Icon(os.path.join(psc.imagesPath, "man2.ico"), wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)
            
        self.users = self.usersCallback()
        
        self.panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self.panel, -1, _("This is a list of the users for this centre. Create a new user or double click on an existing user to edit it."))
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, 0, wx.EXPAND)
        sizer.Add(hbox,0,wx.ALL,10)
       
        self.userlist = PSUserList(self.panel, self.showUserEditor, self.showUserOneClikEditor)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.userlist, 1, wx.EXPAND)

        self.userlist.updateRows(self.users) 
        self.username=None
        sizer.Add(hbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
                          
        box = wx.BoxSizer(wx.HORIZONTAL)
		
        #png = wx.Image('images/adduser.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #btn = GenBitmapTextButton(self.panel, ID_CREATE, bitmap=png,  label= _("Create new user"))
        btn = wx.Button(self.panel, ID_CREATE, label= _("Create new user"))
        self.modifBtn = wx.Button(self.panel, ID_EDIT, label= _("Edit User"))
        closeBtn = wx.Button(self.panel, wx.ID_CLOSE, label= _("Close"))
        self.modifBtn.Disable()
        
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(self.modifBtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(closeBtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTRE | wx.TOP | wx.BOTTOM, 5)
        
        self.panel.SetSizer(sizer)
        
        self.Bind(wx.EVT_BUTTON, self.onCreateUser, id=ID_CREATE)
        self.Bind(wx.EVT_BUTTON, self.onModifUser, id=ID_EDIT)
        self.Bind(wx.EVT_BUTTON, self.onClose, id=wx.ID_CLOSE)
        #self.Bind(wx.EVT_CLOSE, self.onClose, self)
        self.Bind(wx.EVT_SIZE,self.onResize)
        self.Bind(wx.EVT_MAXIMIZE,self.onResize)
	
        NeedColumnWidthUpdateEvent, EVT_COL_WIDTH_UPDATE = wx.lib.newevent.NewEvent()
        self.Bind(EVT_COL_WIDTH_UPDATE,self.onNeedColumnWidthUpdate)
        self.needColumnWidthUpdateEvent = NeedColumnWidthUpdateEvent
        

    def onClose(self, event):
        self.Close()

    def onNeedColumnWidthUpdate(self, event):
        self.userlist.updateColumnWidths()

    def onResize(self, event):
        #self.userlist.updateColumnWidths()
        wx.PostEvent(self,self.needColumnWidthUpdateEvent())
        event.Skip()
    def onModifUser(self, event):
        self.showUserEditor(self.userName)
        self.modifBtn.Disable()
		

    def onCreateUser(self, event):
        self.userEditorNew = PSUserEditorNew(self,self.languages,self.doSaveNewUser)
        self.userEditorNew.Center()
        self.userEditorNew.ShowModal()
		
    def showUserOneClikEditor(self, username):
        self.userName = None
        if username != None:
            self.modifBtn.Enable()
            self.userName = username
		
    def showUserEditor(self, username):
        self.userEditor = PSUserEditor(self,self.users[username],self.languages,self.doUpdateUser)
        self.userEditor.Center()
        self.userEditor.ShowModal()
        #self.SetFocus()

    def doUpdateUser(self, user, name, surname, flgEnabled, userType, language, npassword):

        result = self.updateUserCallback(user['userKey'],name,surname,flgEnabled,userType,language,npassword)
        
        from mainlogic import _ 
        if result == True:
            dlg = wx.MessageDialog(self, _('User saved'), _('Success'), wx.OK )
            #self.users[user['username']]['flgEnabled'] = flgEnabled
            #self.users[user['username']]['userType'] = userType
            #self.users[user['username']]['language'] = language
            #if npassword:
            #    self.users[user['username']]['password'] = npassword
        else:
            dlg = wx.MessageDialog(self, _('Cannot save'), _('Error'), wx.OK )

        dlg.Center()
        dlg.ShowModal()
        
        self.users = self.usersCallback()
        self.userlist.updateRows(self.users)

    def doSaveNewUser(self, surname, name, username, language, userType, flgEnabled, npassword):

        result = self.createUserCallback(surname,name,username,language,userType,flgEnabled,npassword)

        from mainlogic import _

        if result == True:
            dlg = wx.MessageDialog(self, _('User saved'), _('Success'), wx.OK )
            #self.users[username] = dict()
            #self.users[username]['surname'] = surname
            #self.users[username]['name'] = name
            #self.users[username]['username'] = username
            #self.users[username]['language'] = language
            #self.users[username]['userType'] = userType
            #self.users[username]['flgEnabled'] = flgEnabled
            #self.users[username]['password'] = npassword
        elif result == False:
            dlg = wx.MessageDialog(self, _('Cannot save'), _('Error'), wx.OK )
        else:
            return result
        
        dlg.Center()
        dlg.ShowModal()

        self.users = self.usersCallback()
        self.userlist.updateRows(self.users)
        #self.Update()


class PSUserList(wx.ListView):
    
    def __init__(self, parent, editUserCallback, editUserOnselectCallback, size=wx.DefaultSize):

        wx.ListView.__init__(self, parent, id=-1, size=size, style=wx.LC_REPORT |wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)

        self.editUserCallback = editUserCallback
        self.editUserOnselectCallback = editUserOnselectCallback
       
        from mainlogic import _
        columns = [_("Surname"), _("Name"), _("Username"), _("Type") , _("Enabled") ]

        for col in columns:
            self.InsertColumn(columns.index(col), col, format=wx.LIST_FORMAT_CENTRE)

        self.rowsToUsernames = dict()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onEditUser)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onEditUser1)
		

    def updateColumnWidths(self):
        xSize = self.GetSize().x
        colsize = int(xSize / self.GetColumnCount())-1
        for i in range(self.GetColumnCount()):
            self.SetColumnWidth(i,colsize)
   	
    def onEditUser1(self, event):
        row = event.GetIndex()
        username = self.rowsToUsernames[row]
        self.editUserOnselectCallback(username)
        
	
			
    def onEditUser(self, event):
        row = event.GetIndex()
        username = self.rowsToUsernames[row]
        self.editUserCallback(username)
 
    def updateRows(self, users):
        self.DeleteAllItems()
        self.rowsToUsernames = dict()
        rindex = 0
        for key in users:
            user = users[key]
            self.rowsToUsernames[rindex] = user['username']
            self.InsertStringItem(rindex,user['surname'])
            self.SetStringItem(rindex,1,user['name'])
            self.SetStringItem(rindex,2,user['username']) 
            self.SetStringItem(rindex,3,psc.userTypeListRev[str(user['userType'])])  
            self.SetStringItem(rindex,4,str(bool(user['flgEnabled'])))  
            if bool(user['flgEnabled']) == False:
                self.SetItemBackgroundColour(rindex,'light grey')
            rindex += 1


class PSUserEditor(wx.Dialog):
    
    def __init__(self, parent, user, languages, updateUserCallback):

        from mainlogic import _

        wx.Dialog.__init__(self, parent, id=-1, title=_("Edit User"), pos=wx.DefaultPosition,
                           size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE,
                           name="usereditor") 

        self.user = user
        self.updateUserCallback = updateUserCallback
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        #font = wx.Font(10, wx.FONTFAMILY_DEFAULT , wx.NORMAL, wx.NORMAL)
        
        label = wx.StaticText(self, -1, _("Username") + ": " +"%s" % self.user['username'])
        #label.SetFont(font)
        vsizer.Add(label,0,wx.EXPAND | wx.ALL, 5)
        
        vsizer.AddSpacer(10)
        self.nbook = wx.Notebook(self, -1)
        self.propsdialog = PropertiesDialog(self.nbook, self.user, languages)
        self.nbook.AddPage(self.propsdialog, _("Properties"))
        
        #self.udialog = usertypeDialog(self.nbook, self.user)
        #self.nbook.AddPage(self.udialog, "Permissions")
         
        #self.langs = userLang(self.nbook, self.languages)
        #self.nbook.AddPage(self.langs, "Language")
        
        self.pwds = PSUserPwd(self.nbook)
        self.nbook.AddPage(self.pwds, _("Password"))
        
        vsizer.Add(self.nbook, 0, wx.EXPAND)
        vsizer.AddSpacer(20)
        
        btn = wx.Button(self, ID_SAVE, _("save"))
        btn.SetDefault()
        btnc = wx.Button(self, ID_CANCEL, _("Cancel"))
        
        self.Bind(wx.EVT_BUTTON, self.onClose, id=ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.onUpdateUser, id=ID_SAVE)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(btn, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(btnc, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        vsizer.Add(box, 0, wx.ALIGN_CENTRE | wx.ALIGN_BOTTOM)

        sizer.Add(vsizer, 0, wx.EXPAND | wx.ALL, 10)        

        self.SetSizer(sizer)
        self.Fit()
                
    def onClose(self, event):
        self.Destroy()
    
    def onUpdateUser(self, event):
	from mainlogic import _
        name = self.propsdialog.oname.GetValue()
        surname = self.propsdialog.osurname.GetValue()

        flgEnabled = int(self.propsdialog.rb.GetSelection())
        userTypeName= self.propsdialog.ousertype.GetValue()
        lang = self.propsdialog.languageCombo.GetValue()

        npassword = self.pwds.npassword.GetValue().strip()
        rnpassword = self.pwds.rnpassword.GetValue().strip()

        if npassword == '':
            npassword = None

        if rnpassword == '':
            rnpassword = None
        
        userType = psc.userTypeList[userTypeName]
        
        if npassword:
            if not rnpassword or rnpassword != npassword:
                passwordsok = False
            else:
                passwordsok = True
        else:
            passwordsok = True
         
        if flgEnabled == 1 and self.user['flgEnabled'] == 0:
            if not npassword:
                passwordsok = False

        if passwordsok == False and npassword == None:
            dlg = wx.MessageDialog(self, _("You cannot enable a user without setting a new password."), _("Password error"), wx.OK)
            dlg.Center()
            dlg.ShowModal()
 
        elif passwordsok == False:
            dlg = wx.MessageDialog(self, _("New password and confirmed password do not match."), _("Password error"), wx.OK)
            dlg.Center()
            dlg.ShowModal()
            
        else:
            self.updateUserCallback(self.user,name,surname,flgEnabled,userType,lang,npassword)
            self.Destroy()
        

class PropertiesDialog(wx.Panel):

    def __init__(self, parent, user, languages):

        wx.Panel.__init__(self, parent, -1)

        self.user = user
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
           
        from mainlogic import _ 

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Surname"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.osurname = wx.TextCtrl(self, -1, self.user['surname'], size=(80,-1), validator=NotEmptyValidator())
        box.Add(self.osurname, 4, wx.EXPAND)
        sizer.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        sizer.AddSpacer(10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Name"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.oname = wx.TextCtrl(self, -1, self.user['name'], size=(80,-1), validator=NotEmptyValidator())
        box.Add(self.oname, 4, wx.EXPAND)
        sizer.Add(box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        sizer.AddSpacer(20)

        self.rb = wx.RadioBox(self, -1, _("User state"), wx.DefaultPosition, wx.DefaultSize, [_("Disabled"),_("Enabled")])

        self.rb.SetSelection(int(bool(user['flgEnabled'])))

        if self.user['username'] == 'admin':
            self.rb.Disable()

        sizer.Add(self.rb, 0, wx.EXPAND | wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, 10)

        sizer.AddSpacer(20)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Language"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)

        languageList = languages[:]
        languageList.sort()
        currentLanguage = self.user['language']
        self.languageCombo = wx.ComboBox(self, 500, currentLanguage, choices=languageList, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        box.Add(self.languageCombo, 1, wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box,0,wx.EXPAND)

        sizer.AddSpacer(20)
 
        userTypeItems = psc.userTypeListRev.items()
        userTypeItems.sort()
        choices = [el[1] for el in userTypeItems]
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("User type"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
                
        """currentType = psc.userTypeListRev[str(user['userType'])]
        self.ousertype = wx.ComboBox(self, 200, currentType, choices=choices,style=wx.CB_DROPDOWN | wx.CB_READONLY  )
        box.Add(self.ousertype, 1, wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)"""
        
        hsizertype = wx.BoxSizer(wx.HORIZONTAL)
        #TODO: TRANSLATE CHOICES?
        currentType = psc.userTypeListRev[str(user['userType'])]        
        self.ousertype = wx.ComboBox(self, 200, currentType, choices=choices,style=wx.CB_DROPDOWN | wx.CB_READONLY)
        hsizertype.Add(self.ousertype, 4, wx.EXPAND)
        hsizertype.AddSpacer(5)
        btnExplanation = wx.Button(self, -1, "?")
        btnExplanation.Bind(wx.EVT_BUTTON, self.showTypeExplanation)
        hsizertype.Add(btnExplanation, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.Add(hsizertype, 4, wx.EXPAND)
        sizer.Add(box, 0, wx.EXPAND)
 
        if self.user['username'] == 'admin':
            self.ousertype.Disable()

        self.SetSizer(sizer)
    
    def showTypeExplanation(self, event):
        from mainlogic import _
        dlg = wx.MessageDialog(self, _("USER_TYPE_DESCRIPTION_STRING"), _("User type description"), wx.OK)
        dlg.Center()
        dlg.ShowModal()

   
class PSUserEditorNew(wx.Dialog):
    
    def __init__(self, parent, languages, saveNewUserCallback):

        from mainlogic import _

        wx.Dialog.__init__(self, parent, id=-1, title=_("Create new user"), pos=wx.DefaultPosition,
                           size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE | wx.WS_EX_VALIDATE_RECURSIVELY,
                           name="usereditornew")     

        self.saveNewUserCallback = saveNewUserCallback

        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Surname"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.osurname = wx.TextCtrl(self, -1, "", size=(80,-1), validator=NotEmptyValidator())
        box.Add(self.osurname, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)

        vsizer.AddSpacer(10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Name"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.oname = wx.TextCtrl(self, -1, "", size=(80,-1),   validator=NotEmptyValidator())
        box.Add(self.oname, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)
 
        vsizer.AddSpacer(10)
       
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Username"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.ousername = wx.TextCtrl(self, -1, "", size=(80,-1), validator=UsernameValidator())
        box.Add(self.ousername, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)
  
        vsizer.AddSpacer(10)
       
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.npassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD, validator=PasswordValidator())
        box.Add(self.npassword, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)
 
        vsizer.AddSpacer(10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Confirm password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.rnpassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD, validator=PasswordAgainValidator(self.npassword))
        box.Add(self.rnpassword, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)
 
        vsizer.AddSpacer(10)

        userTypeItems = psc.userTypeListRev.items()
        userTypeItems.sort()
        choices = [el[1] for el in userTypeItems]
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("User type"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        
        hsizertype = wx.BoxSizer(wx.HORIZONTAL)        
        self.ousertype = wx.ComboBox(self, 200, "", choices=choices,style=wx.CB_DROPDOWN | wx.CB_READONLY)
        hsizertype.Add(self.ousertype, 4, wx.EXPAND)
        hsizertype.AddSpacer(5)
        btnExplanation = wx.Button(self, -1, "?")
        btnExplanation.Bind(wx.EVT_BUTTON, self.showTypeExplanation)
        hsizertype.Add(btnExplanation, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.Add(hsizertype, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)
  
        vsizer.AddSpacer(10)
      
        choices  = languages[:]
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("User language"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.ouserlang = wx.ComboBox(self, 200, choices[0], choices=choices,style=wx.CB_DROPDOWN  | wx.CB_READONLY )
        box.Add(self.ouserlang, 4, wx.EXPAND)
        vsizer.Add(box, 0, wx.EXPAND)
   
        vsizer.AddSpacer(10)
      
        self.rb = wx.RadioBox(
                self, -1, _("Initial state"), wx.DefaultPosition, wx.DefaultSize,
                [_("Disabled"),_("Enabled")])
        self.rb.SetSelection(1)
        vsizer.AddSpacer(20)
        vsizer.Add(self.rb, 0, wx.EXPAND | wx.ALIGN_CENTRE)
                
        sizer.AddSpacer(20)
        sizer.Add(vsizer, 0, wx.EXPAND | wx.ALL, 10)
        sizer.AddSpacer(20)
        
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, ID_SAVE, _("save"))
        btn.SetDefault()
        
        self.Bind(wx.EVT_BUTTON, self.onSaveNewUser, id=ID_SAVE)
        
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL,5)
        btnc = wx.Button(self, ID_CANCEL, _("Cancel"))
                
        self.Bind(wx.EVT_BUTTON, self.onClose, id=ID_CANCEL)
        
        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL,5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(10)
        
        self.SetSizer(sizer)
        self.Fit()
                
    def onClose(self, event):
        self.Destroy()
        
    def showTypeExplanation(self, event):
        from mainlogic import _
        dlg = wx.MessageDialog(self, _("Explain user"), _("User type explanation"), wx.OK)
        dlg.Center()
        dlg.ShowModal()
        
    def onSaveNewUser(self, event):
        from mainlogic import _

        if self.Validate():
            langName =  self.ouserlang.GetValue()
            #lang = self.langList[langName]
            
            userTypeName = self.ousertype.GetValue()
            if not userTypeName:
                dlg = wx.MessageDialog(self, _("You cannot create a user without setting a user type."), _("User type error"), wx.OK)
                dlg.Center()
                dlg.ShowModal()
                return
                
            userType = psc.userTypeList[userTypeName]
            
            surname = self.osurname.GetValue()
            name =  self.oname.GetValue()
            username = self.ousername.GetValue()
           
            username = username.strip()
 
            flgEnabled = self.rb.GetSelection()

            npassword = self.npassword.GetValue()
            rnpassword = self.rnpassword.GetValue()
            npassword = npassword.strip()
            rnpassword = rnpassword.strip()
            if npassword == '':
                npassword = None
            if rnpassword == '':
                rnpassword = None

            if npassword:
                if not rnpassword or rnpassword != npassword:
                    passwordsok = False
                else:
                    passwordsok = True
            else:
                passwordsok = False
 
            if npassword == None:
                dlg = wx.MessageDialog(self, _("You cannot create a user without setting a password."), _("Password error"), wx.OK)
                dlg.Center()
                dlg.ShowModal()
     
            elif passwordsok == False:
                dlg = wx.MessageDialog(self, _("New password and confirmed password do not match."), _("Password error"), wx.OK)
                dlg.Center()
                dlg.ShowModal()
 
            else:
                userResume = (_("User data") + "\n\n" + _("Surname") + ": %s\n" + _("Name") + ": %s\n" + _("Username") + ": %s\n\n\n") % (surname, name, username)
                dlg = wx.MessageDialog(None, userResume + 
                _("Do you really want create this user? Remember that users cannot be deleted"),
                _("Confirm user creation"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
                dlg.Center() 
                result = dlg.ShowModal()
                
                if result == wx.ID_OK:
                    res = self.saveNewUserCallback(surname, name, username, langName, userType, flgEnabled, npassword)
                    if res == 'duplicate':
                        dlg = wx.MessageDialog(self, _("Username exists, please provide a different one."), _("Username error"), wx.OK)
                        dlg.Center()
                        dlg.ShowModal()
                        return
                    self.Destroy()


class PSUserPwd(wx.Panel):

    def __init__(self, parent):
        from mainlogic import _ 
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(30)
          
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("New password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.npassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD, validator=PasswordOrEmptyValidator())
        box.Add(self.npassword, 2,wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        sizer.AddSpacer(10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Confirm password"))
        box.Add(label, 1, wx.EXPAND)
        box.AddSpacer(5)
        self.rnpassword = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD, validator=PasswordAgainValidator(self.npassword))
        box.Add(self.rnpassword, 2,wx.EXPAND|wx.GROW)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        self.SetSizer(sizer)
        #sizer.Fit(self)

