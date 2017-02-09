import wx
#from genthreaddialog import genThreadDialog

ID_SAVE = 100
ID_CANCEL = 101

class PSFieldsCustomizer(wx.Dialog):
    def __init__(self, parent, mainLogic):
       
        wx.Dialog.__init__(self, parent, id=-1, title="Fields customization", pos=wx.DefaultPosition,size=wx.Size(500,400), style=   wx.DEFAULT_DIALOG_STYLE,
            name="usermanager") 
        
        self.mainLogic = mainLogic
         
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)        
        
        label = wx.StaticText(self, -1, "Here goes the label.")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(30)
        hbox.Add(label, 1, wx.EXPAND)
        hbox.AddSpacer(30)
        sizer.Add(hbox, 1, wx.EXPAND)
        
         
                  
        #buttons    
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, ID_SAVE, "Save")
        
        #event binding
        self.Bind(wx.EVT_BUTTON, self.doSaveFieldsCustomization, id=ID_SAVE)
        
        #add to sizer
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)

        btnc = wx.Button(self, ID_CANCEL, "Cancel")
        btn.SetDefault()
        #event binding
        self.Bind(wx.EVT_BUTTON, self.doClose, id=ID_CANCEL)
        
        #add to sizer
        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(box, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(10)
        
        self.SetSizer(sizer)
         
    def doClose(self, event):
        self.Destroy()
    
           
    def doSaveFieldsCustomization(self, event):
                
        #saving users via mainLogic
        #td = genThreadDialog(self, "Saving", self.mainLogic.saveClientConfig)
        #saveOk = td.getResult()
        
        saveOk = False;
        if(saveOk == True):
           dlg = wx.MessageDialog(self, 'User saved', 'Save OK!', wx.OK )
        else:
           dlg = wx.MessageDialog(self, 'Cannot save', 'Save KO!', wx.OK )
        
        dlg.ShowModal()
        dlg.Destroy()
        
