import wx
from wx.lib.scrolledpanel import ScrolledPanel

class PSScrolledPanel(ScrolledPanel):
    def __init__(self, parent, id, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name=''):
        ScrolledPanel.__init__(self, parent, id, pos, size, style, name)
        self.Bind(wx.EVT_CHILD_FOCUS, self.skipEvent)

    def skipEvent(self, event):
        event.Skip(False)

