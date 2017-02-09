import wx

ID_ACTION = 100
ID_CANCEL = 101

class PSAdmissionCloser(wx.Dialog):

    def __init__(self, parent, mode, closeAdmissionCallback, deleteAdmissionCallback, reopenAdmissionCallback,neededCrfs=None):

        self.closeAdmissionCallback = closeAdmissionCallback
        self.deleteAdmissionCallback = deleteAdmissionCallback
        self.reopenAdmissionCallback = reopenAdmissionCallback
       
        from mainlogic import _ 
        nonUsableCrfs = []
        usableCrfs = []
        if mode == 'CLOSE':
            for crfName, status in neededCrfs.iteritems():
                if status == '1':
                    nonUsableCrfs.append(crfName)
                else:
                    usableCrfs.append(crfName)
            title = _("Close Admission")
            butLabel = _("Close")
            action = self.doCloseAdmission
            labelText = _("Please select the crfs you want to close.")
        elif mode == 'DELETE':
            title = _("Delete Admission")
            butLabel = _("Delete")
            action = self.doDeleteAdmission
            labelText = _("You are DELETING this admission. Are you sure?")
        else:
            usableCrfs = neededCrfs.keys()
            title = _("Re-Open Admission")
            butLabel = _("Re-Open")
            action = self.doReOpenAdmission
            labelText = _("Please select the crfs you want to re-open.")
       
        wx.Dialog.__init__(self, parent, id=-1, title=title, pos=wx.DefaultPosition,size=wx.Size(500,400), style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER, name="admissioncloser") 
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)        
        if nonUsableCrfs:
            nonUsableCrfsString = '\n'.join(nonUsableCrfs)
            labelText = labelText + '\n' + _("The following crfs could not be closed because you cannot close a crfs that is in status 1.") + '\n\n' + nonUsableCrfsString
        label = wx.StaticText(self, -1, labelText)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(30)
        
        hbox.Add(label, 1, wx.EXPAND)
        hbox.AddSpacer(10)

        if usableCrfs:
            self.crfsCheckListBox = wx.CheckListBox(self, -1, (80, 50), wx.DefaultSize, usableCrfs)
            hbox.Add(self.crfsCheckListBox, 1,wx.EXPAND)
            hbox.AddSpacer(10)
        sizer.Add(hbox, 1, wx.EXPAND)
                  
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, ID_ACTION, butLabel)
        btnc = wx.Button(self, ID_CANCEL, _("Cancel"))
        btn.SetDefault()    
               
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)

        self.Bind(wx.EVT_BUTTON, self.doClose, id=ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, action, id=ID_ACTION)
       
        sizer.Add(box, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(10)
        
        self.SetSizer(sizer)
         
    def doCloseAdmission(self, event):
        crfs = [self.crfsCheckListBox.GetString(el) for el in self.crfsCheckListBox.GetChecked()]
        self.closeAdmissionCallback(crfs)
        self.Destroy()
        
    def doDeleteAdmission(self, event):
        self.deleteAdmissionCallback()
        self.Destroy()
        
    def doReOpenAdmission(self, event):
        crfs = [self.crfsCheckListBox.GetString(el) for el in self.crfsCheckListBox.GetChecked()]
        self.reopenAdmissionCallback(crfs)
        self.Destroy()
        
    def doClose(self,  event):
        self.Destroy()

