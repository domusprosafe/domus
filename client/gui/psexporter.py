import wx
import os

ID_SAVE = 100
ID_CANCEL = 101

class PSExporter(wx.Dialog):
    def __init__(self, parent, mainLogic):
       
        wx.Dialog.__init__(self, parent, id=-1, title=_("Export data"), pos=wx.DefaultPosition,size=wx.Size(500,400), style=   wx.DEFAULT_DIALOG_STYLE,
            name="exporter") 
        
        #recupero lista utenti
        self.mainLogic = mainLogic
         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(30)
         
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)        
        
        label = wx.StaticText(self, -1, "Please select an export format")
         
        sizer.AddSpacer(30)
        sizer.Add(label, 0)
        sizer.AddSpacer(30)
        
        self.radio1 = wx.RadioButton( self, -1, _("CSV format"), style = wx.RB_GROUP )
        self.radio2 = wx.RadioButton( self, -1, _("Excel format") )
        sizer.Add(self.radio1, 0)
        sizer.Add(self.radio2, 0)
         
                  
        #buttons    
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, ID_SAVE, "Save")
        
        #event binding
        self.Bind(wx.EVT_BUTTON, self.doExport, id=ID_SAVE)
        
        #add to sizer
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)

        btnc = wx.Button(self, ID_CANCEL, "Cancel")
        btn.SetDefault()
       
        
        #add to sizer
        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(box, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(10)
        
        hbox.Add(sizer,  1,  wx.EXPAND)
        hbox.AddSpacer(30)
        self.SetSizer(hbox)
        
         #event binding
        self.Bind(wx.EVT_BUTTON, self.doClose, id=ID_CANCEL)
       
    def doClose(self, event):
        self.Destroy()
    
           
    def doExport(self, event):
                
        
        
        #format
        val1 = self.radio1.GetValue()
        val2 = self.radio2.GetValue()
            
        #csv    
        if(val1):
            format = 'csv'
            wildcard = "CSV file(*.csv)|*.csv"
            
        else:
            format = 'excel'
            wildcard = "Excel file(*.xls)|*.xls"
        
        print format
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir="", 
            defaultFile="prosafe_export", wildcard=wildcard, style=wx.SAVE
            )
            
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            print 'You selected "%s"' % path
        
            
            #saving via mainLogic
            #td = genThreadDialog(self, "Saving", self.mainLogic.exportData,  path,  format)
            #saveOk = td.getResult()
            try:
               saveOk = self.mainLogic.exportData(path,format)
            except:
               saveOk = False

            if saveOk == True:
                dlgok = wx.MessageDialog(self, _('Data saved'), _('Save OK!'), wx.OK)
            else:
                dlgok = wx.MessageDialog(self, _('Cannot save'), _('Save KO!'), wx.OK)

            dlgok.ShowModal()
            dlgok.Destroy()
        dlg.Destroy()
