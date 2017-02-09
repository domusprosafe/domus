import wx
import datetime
import re
import datetime
import time

def create(parent):
    return TimerTextbox(parent)

class TimerTextbox(wx.StaticText):
    def GetLabel(self):
        strTmp = self.Label
        return strTmp
        
    def SetValue(self, data):
        self.recup = data
        
    def SetLabel(self, hour):
        self.Label = hour
    
    def __init__(self, parent, id, hour, name='', pos = wx.DefaultPosition, size = wx.DefaultSize, style=0 ):
        wx.StaticText.__init__(self, parent = parent, id = id, name = name, pos = pos, size = size, style = style)  
        # self.SetMaxLength(5)
        self.recup=hour
        # self.SetBackgroundColour('black')
        # self.SetBackgroundColour(wx.Colour(169, 169, 169, 255))
        # self.SetForegroundColour(wx.Colour(0, 255, 0))
        # self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
        self.timer = wx.Timer(self)
        font = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.SetFont(font)
        self.SetLabel("00:00:00")
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(1000)
        

    def update(self, event):
        if self.recup != None and self.recup != '':
            dat=self.recup.split(' ')[0]
            tim=self.recup.split(' ')[1]
            
            dataTime = datetime.datetime(int(dat.split('-')[0]), int(dat.split('-')[1]), int(dat.split('-')[2]), int(tim.split(':')[0]), int(tim.split(':')[1]))
            res = dataTime - datetime.datetime.today()
            strdat = str(res)
            self.SetBackgroundColour(wx.Colour(0, 0, 0, 255))
            self.SetForegroundColour(wx.Colour(0, 255, 0, 255))
            if res.days == -1 :
                
                self.SetLabel("00:00:00")
                
            else:
                if res.days == 0:
                    strdat = str(res)[:8]
                    if '.' in strdat:
                        strdat = str(res)[:7]
                    self.SetLabel(strdat)
        else:
            self.SetLabel("00:00:00")
            # self.timer.Stop()