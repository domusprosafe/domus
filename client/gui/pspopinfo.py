import wx
# import  wx.lib.scrolledpanel as scrolled
# import psconstants as psc
import os

class popInfoDialog(wx.Dialog):
    def __init__(self, parent, id,title=None, mesHelpe=None):
        wx.Dialog.__init__(self, parent, id,  size=wx.Size(300, 250))
        
        # self = wx.Dialog(self.root, -1, "About", size=wx.Size(300, 250))
        titleLabel = wx.StaticText(self, -1, title)
        # helpLabel = wx.StaticText(self, -1, mesHelpe)
        
        helpLabel = wx.TextCtrl(self, size=wx.Size(400, 350), style=wx.TE_MULTILINE | wx.TE_READONLY )
        helpLabel.SetValue(mesHelpe)

        
        
        from mainlogic import _
        
        copyrightLabel = wx.StaticText(self, -1, _('Mario Negri') )
        okButton = wx.Button(self, -1, _("Close"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetWeight(wx.FONTWEIGHT_BOLD)        
        okButton.Bind(wx.EVT_BUTTON, self.okButtonclik)
        vsizer.AddSpacer(10)
        
        vsizer.Add(titleLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(10)
        
        vsizer.Add(helpLabel, 0, wx.ALL)
        vsizer.AddSpacer(10)        
        
        vsizer.Add(copyrightLabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(10)
        
        vsizer.AddSpacer(10)
        
        vsizer.Add(okButton, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.Add(vsizer,0,wx.ALIGN_CENTRE|wx.ALL,20)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        self.Center()
        self.SetFocus()
        self.ShowModal()
        
    def okButtonclik(self, event):
        self.Close()
        