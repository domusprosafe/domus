import wx

class PSStatBox(wx.Panel):
    
    def __init__(self, parent, id=-1, title="Admission statistics", size=wx.Size(0, 100)):
        
        wx.Panel.__init__(self, parent, id, size=size)        

        vsizer = wx.BoxSizer(wx.VERTICAL)
        sizer=wx.BoxSizer(wx.HORIZONTAL)
        
        from mainlogic import _

        tx = wx.StaticText(self, -1, _("Admission statistics"), style=wx.ALIGN_CENTRE)
        f = tx.GetFont()
        f.SetWeight(wx.BOLD)
        tx.SetFont(f) 
        
        vsizer.AddSpacer(5)
        vsizer.Add(tx, 1, wx.EXPAND)
       
        numLabel =  wx.StaticText(self, -1, _("Shown/Total: "), style=wx.ALIGN_RIGHT)
        stat1Label =  wx.StaticText(self, -1, "Status 1: ", style=wx.ALIGN_RIGHT)
        stat2Label =  wx.StaticText(self, -1, "Status 2: ", style=wx.ALIGN_RIGHT)
        stat3Label =  wx.StaticText(self, -1, "Status 3: ", style=wx.ALIGN_RIGHT)
        stat4Label =  wx.StaticText(self, -1, "Status 4: ", style=wx.ALIGN_RIGHT)
        stat5Label =  wx.StaticText(self, -1, "Status 5: ", style=wx.ALIGN_RIGHT)
        
        self.numStat =  wx.StaticText(self, -1, "")
        self.numStat.SetForegroundColour('Red')
        
        self.stat1Stat = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
        self.stat1Stat.SetForegroundColour('Red')
        
        self.stat2Stat = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
        self.stat2Stat.SetForegroundColour('Red')
        
        self.stat3Stat = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
        self.stat3Stat.SetForegroundColour('Red')
        
        self.stat4Stat = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
        self.stat4Stat.SetForegroundColour('Red')
        
        self.stat5Stat = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
        self.stat5Stat.SetForegroundColour('Red')
        
        sizer.AddSpacer(10)
                
        sizer.Add(numLabel, 1,wx.EXPAND)
        sizer.Add(self.numStat, 1, wx.EXPAND)        
        
        sizer.Add(stat1Label, 1, wx.EXPAND)
        sizer.Add(self.stat1Stat, 1, wx.EXPAND)
        
        sizer.Add(stat2Label, 1, wx.EXPAND )
        sizer.Add(self.stat2Stat, 1, wx.EXPAND)
        
        sizer.Add(stat3Label, 1, wx.EXPAND)
        sizer.Add(self.stat3Stat, 1, wx.EXPAND)
        
        sizer.Add(stat4Label, 1, wx.EXPAND)
        sizer.Add(self.stat4Stat, 1, wx.EXPAND)
        
        sizer.Add(stat5Label, 1, wx.EXPAND)
        sizer.Add(self.stat5Stat, 1, wx.EXPAND)
    
        sizer.AddSpacer(10)
     
        vsizer.Add(sizer,1, wx.EXPAND|wx.ALIGN_CENTRE)
        
        self.SetSizer(vsizer)
        sizer.Layout()
        
    def refreshData(self, data):
        
        self.numStat.SetLabel("%d/%d" % (data['visualized'], data['total']))
        self.stat1Stat.SetLabel("%d" % data['status1'])
        self.stat2Stat.SetLabel("%d" % data['status2'])
        self.stat3Stat.SetLabel("%d" % data['status3'])
        self.stat4Stat.SetLabel("%d" % data['status4'])
        self.stat5Stat.SetLabel("%d" % data['status5'])
        wx.Panel.Refresh(self)
 
