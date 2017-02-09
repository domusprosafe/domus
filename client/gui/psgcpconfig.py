import wx
#from genthreaddialog import genThreadDialog

ID_SAVE = 100
ID_CANCEL = 101

class PSGcpConfig(wx.Dialog):
    def __init__(self, parent, mainLogic):
       
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1, title=_("GCP Configuration"), pos=wx.DefaultPosition,size=wx.Size(500,400), style=   wx.DEFAULT_DIALOG_STYLE,
            name="usermanager") 
        
        #recupero lista utenti
        self.mainLogic = mainLogic
         
        sizer = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, -1, _("GCP_INSTRUCTION"), size=wx.Size(400, -1))
        disclaimerLabel = wx.StaticText(self, -1, _("GCP_WARNING"), size=wx.Size(400, -1))
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        disclaimerLabel.SetFont(font)
        disclaimerLabel.SetForegroundColour(wx.RED)
        label.Wrap(label.GetSize().width) 
        disclaimerLabel.Wrap(disclaimerLabel.GetSize().width) 
        
        hbox.Add(label, 1, wx.EXPAND|wx.ALL, border=10)
        hbox.Add(disclaimerLabel, 1, wx.EXPAND|wx.ALL, border=10)
        
        disclaimerLabel.Show(False)
        optionList = [_("GCP compilation enabled"), _("GCP compilation disabled")]
        self.radioBox =  wx.RadioBox(self, -1, _("Activation options"), wx.DefaultPosition, wx.DefaultSize, optionList, 1, wx.RA_SPECIFY_COLS)
        #self.Bind(wx.EVT_RADIOBOX, self.onRadioBoxCheckChanged, radioBox)
        hbox.Add(self.radioBox, 1, wx.EXPAND|wx.ALL, border=10)

        
        sizer.Add(hbox, 1, wx.EXPAND)
        self.radioBox.SetSelection(0)
        if not self.mainLogic.gcpActive:
            self.radioBox.SetSelection(1)
        #buttons    
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, ID_SAVE, _("Save"))
        
        #event binding
        self.Bind(wx.EVT_BUTTON, self.doSaveClientConfig, id=ID_SAVE)
        
        #add to sizer
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)

        btnc = wx.Button(self, ID_CANCEL, _("Cancel"))
        btn.SetDefault()
        #event binding
        self.Bind(wx.EVT_BUTTON, self.doClose, id=ID_CANCEL)
        
        #add to sizer
        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(box, 0, wx.ALIGN_CENTRE)

        
        self.SetSizer(sizer)
        
        if self.mainLogic.forceGcp:
            btn.Enable(False)
            self.radioBox.Enable(False)
            disclaimerLabel.Show(True)
            
         
    def doClose(self, event):
        self.Destroy()
           
    def doSaveClientConfig(self, event):
        from mainlogic import _
        if self.radioBox.GetStringSelection() == _("GCP compilation enabled"):
            self.mainLogic.gcpActive = True
        elif self.radioBox.GetStringSelection() == _("GCP compilation disabled"):
            self.mainLogic.gcpActive = False
        self.mainLogic.setGcpSetting(self.mainLogic.gcpActive)
        dlg = wx.MessageDialog(None, 
            _("GCP settings saved correctly!"),
            _("GCP settings saved correctly!"), wx.OK | wx.ICON_EXCLAMATION)
        dlg.Center()
        dlg.ShowModal()
        dlg.Destroy()
        self.Destroy()
        
