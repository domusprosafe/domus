import wx
import psconstants as psc

class PSAdmissionsUpdate(wx.Dialog):

    def __init__(self, parent, admissionsToUpdate, updateAdmissionsCallback, stopUpdateAdmissionsCallback):

        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1, title=_('Admissions update'), size=wx.Size(300,300), style=wx.DEFAULT_DIALOG_STYLE)

        self.admissionsToUpdate = admissionsToUpdate
        self.updateAdmissionsCallback = updateAdmissionsCallback
        self.stopUpdateAdmissionsCallback = stopUpdateAdmissionsCallback
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(30)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        self.label = wx.StaticText(self, -1, _("There are %d admissions that need to be updated. Proceed?") % len(admissionsToUpdate))
        box.Add(self.label, 1, wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        sizer.AddSpacer(20)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        self.gauge = wx.Gauge(self, -1, 100)
        box.Add(self.gauge, 1, wx.EXPAND)
        box.AddSpacer(10)
        sizer.Add(box, 0, wx.EXPAND)

        self.updateButton = wx.Button(self, -1, _("Update"))
        self.closeButton = wx.Button(self, -1, _("Close"))
        self.updateButton.SetDefault()
        
        sizer.AddSpacer(20)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.updateButton,0)
        box.AddSpacer(5)
        box.Add(self.closeButton,0)
        sizer.Add(box,0,wx.ALIGN_CENTRE)
        sizer.AddSpacer(20)
        
        self.Bind(wx.EVT_BUTTON,self.doProceed,self.updateButton)
        self.Bind(wx.EVT_BUTTON,self.doClose,self.closeButton)
        
        self.SetSizer(sizer)
        self.Fit()

    def doClose(self,event):
        self.stopUpdateAdmissionsCallback()
        self.EndModal(0)
        
    def doProceed(self, event):
        self.updateButton.Disable()
        self.progressCallback(0,len(self.admissionsToUpdate))
        self.updateAdmissionsCallback(self.admissionsToUpdate,self.progressCallback)

    def progressCallback(self, current, total):
        from mainlogic import _
        wx.CallAfter(self.label.SetLabel,_("Updated %d admissions, %d left.") % (current, total-current))
        wx.CallAfter(self.gauge.SetValue,int(float(current)/total*100))

