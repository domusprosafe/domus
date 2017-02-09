import wx
import os
import psconstants as psc
        
class transientPopup(wx.Dialog):
    def __init__(self, parent, onShowUserPrefs=None, dischargeLetterModelCallback=None, showUserManager=None, showCustomizationEditorCallback=None,showRestorableDeletedCallback=None,moveMasterConfigurationCallback=None,gcpSettingsCallback=None):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1, title=_('Manage configuration'), pos=wx.DefaultPosition, size=wx.Size(200,100), style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER, name="userprefs")
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        #userPreferences
        self.onShowUserPrefs = onShowUserPrefs
        label = wx.StaticText(self, -1, _("User preferences"))
        bmp_userpref = wx.Image(os.path.join(psc.imagesPath, 'user.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_userpref = wx.BitmapButton(self, -1, bmp_userpref, wx.DefaultPosition, (bmp_userpref.GetWidth()+10, bmp_userpref.GetHeight()+10), wx.BU_AUTODRAW)
        self.Bind(wx.EVT_BUTTON, self.onShowUserPrefsButton, tool_userpref)
        sizer.AddSpacer(10) 
        vsizer.Add(tool_userpref, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        
        if 'dischargeLetter' in psc.toolBarApplications:
            vsizer = wx.BoxSizer(wx.VERTICAL)
            #discharge letter model editor
            self.dischargeLetterModelCallback = dischargeLetterModelCallback
            label = wx.StaticText(self, -1, _("Discharge letter model"))
            bmp_discharge = wx.Image(os.path.join(psc.imagesPath, 'editdischargeletter.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_discharge = wx.BitmapButton(self, -1, bmp_discharge, wx.DefaultPosition, (bmp_discharge.GetWidth()+10, bmp_discharge.GetHeight()+10), wx.BU_AUTODRAW)
            self.Bind(wx.EVT_BUTTON, self.onDischargeLetterModelCallback, tool_discharge)
            sizer.AddSpacer(10) 
            vsizer.Add(tool_discharge, 0, wx.ALIGN_CENTRE|wx.ALL)
            vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
            sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        #user manager
        self.showUserManager = showUserManager
        label = wx.StaticText(self, -1, _("Manage users"))
        bmp_manager = wx.Image(os.path.join(psc.imagesPath, 'users.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_manager = wx.BitmapButton(self, -1, bmp_manager, wx.DefaultPosition, (bmp_manager.GetWidth()+10, bmp_manager.GetHeight()+10), wx.BU_AUTODRAW)
        self.Bind(wx.EVT_BUTTON, self.onShowUserManager, tool_manager)
        sizer.AddSpacer(10)
        vsizer.Add(tool_manager, 0, wx.ALIGN_CENTRE|wx.ALL)        
        vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        
        if 'personalizations' in psc.toolBarApplications:
            vsizer = wx.BoxSizer(wx.VERTICAL)
            #user manager
            self.showCustomizationEditorCallback = showCustomizationEditorCallback
            label = wx.StaticText(self, -1, _("Customization"))
            bmp_custom = wx.Image(os.path.join(psc.imagesPath, 'customize.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_custom = wx.BitmapButton(self, -1, bmp_custom, wx.DefaultPosition, (bmp_custom.GetWidth()+10, bmp_custom.GetHeight()+10), wx.BU_AUTODRAW)
            self.Bind(wx.EVT_BUTTON, self.onShowCustomizationEditorCallback, tool_custom)
            sizer.AddSpacer(10)
            vsizer.Add(tool_custom, 0, wx.ALIGN_CENTRE|wx.ALL)        
            vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
            sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.showRestorableDeleted=showRestorableDeletedCallback
        label = wx.StaticText(self, -1, _("hospitalization unactivated"))
        bmp_delete = wx.Image(os.path.join(psc.imagesPath, 'patientDel.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_deleted = wx.BitmapButton(self, -1, bmp_delete, wx.DefaultPosition, (bmp_delete.GetWidth()+10, bmp_delete.GetHeight()+10), wx.BU_AUTODRAW)
        self.Bind(wx.EVT_BUTTON, self.onShowRestorableDeletedCallback, tool_deleted)
        sizer.AddSpacer(10)
        vsizer.Add(tool_deleted, 0, wx.ALIGN_CENTRE|wx.ALL)        
        vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.moveMasterConfigurationCallback=moveMasterConfigurationCallback
        label = wx.StaticText(self, -1, _("Move master"))
        bmp_move = wx.Image(os.path.join(psc.imagesPath, 'move.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        tool_movemaster = wx.BitmapButton(self, -1, bmp_move, wx.DefaultPosition, (bmp_delete.GetWidth()+10, bmp_delete.GetHeight()+10), wx.BU_AUTODRAW)
        self.Bind(wx.EVT_BUTTON, self.onMoveMasterConfigurationCallback, tool_movemaster)
        sizer.AddSpacer(10)
        vsizer.Add(tool_movemaster, 0, wx.ALIGN_CENTRE|wx.ALL)        
        vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        
        if 'gcp' in psc.toolBarApplications:
            vsizer = wx.BoxSizer(wx.VERTICAL)
            self.gcpSettingsCallback=gcpSettingsCallback
            label = wx.StaticText(self, -1, _("GCP settings"))
            bmp_gcp = wx.Image(os.path.join(psc.imagesPath, 'gcpconfiguration.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool_gcp = wx.BitmapButton(self, -1, bmp_gcp, wx.DefaultPosition, (bmp_delete.GetWidth()+10, bmp_delete.GetHeight()+10), wx.BU_AUTODRAW)
            self.Bind(wx.EVT_BUTTON, self.onGcpSettingsCallback, tool_gcp)
            sizer.AddSpacer(10)
            vsizer.Add(tool_gcp, 0, wx.ALIGN_CENTRE|wx.ALL)        
            vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
            sizer.Add(vsizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        
        
        sizer.AddSpacer(10)
        self.SetSizerAndFit(sizer)
        #self.Fit()
        #self.Layout()
        
        
    def onShowUserPrefsButton(self, event):
        self.onShowUserPrefs()
        self.Close()
        
    def onDischargeLetterModelCallback(self, event):
        self.dischargeLetterModelCallback()
        self.Close()
        
    def onShowUserManager(self, event):
        self.showUserManager()
        self.Close()
        
    def onShowCustomizationEditorCallback(self, event):
        self.showCustomizationEditorCallback()
        self.Close()
    
    def onShowRestorableDeletedCallback(self, event):
        self.showRestorableDeleted()
        # self.Close()
        
    def onMoveMasterConfigurationCallback(self, event):
        self.moveMasterConfigurationCallback()
        self.Close()
        
    def onGcpSettingsCallback(self, event):
        self.gcpSettingsCallback()
        self.Close()
        