import wx
from psgridsizer import PSGridSizer
from mlcheckbox import MLCheckBox
from psguiconstants import GUI_WINDOW_VARIANT

class PSCheckListBox(wx.Dialog):

    def __init__(self, parent, id, title="", choiceStrings=[], enabledChoiceStrings=[], tooltipStrings=[], tooltipCallback=None, size=wx.DefaultSize, style=0):

        wx.Dialog.__init__(self, parent, id, size=size, style=wx.BORDER_SIMPLE)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.tooltipCallback = tooltipCallback

        if not tooltipStrings:
            tooltipStrings = ['']*len(choiceStrings)

        self.checkboxes = []
        checkboxSizer = PSGridSizer(0,2,25)
        wrap = 300
        width = 300
        checkboxSizer.SetHGap(2)
        checkboxSizer.SetVGap(2)
        for choice, tooltipString in zip(choiceStrings,tooltipStrings):
            widget = MLCheckBox(self, id, choice, wrap=wrap, name=choice, size = wx.Size(width, -1))
            widget.SetWindowVariant(GUI_WINDOW_VARIANT)
            checkboxSizer.Add(widget)
            #checkboxSizer.SetItemSpan(widget, (1, 1))
            self.checkboxes.append(widget)
            widget.infoText = tooltipString
            if not choice in enabledChoiceStrings:
                widget.SetForegroundColour(wx.LIGHT_GREY)
                widget.Disable()
            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

        checkboxSizer.Compact()

        sizer.Add(checkboxSizer,0,wx.ALL,10)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetWindowVariant(GUI_WINDOW_VARIANT)
        self.Bind(wx.EVT_BUTTON, self.OnOK, btn)

        sizer.AddSpacer(10)
        sizer.Add(btn,0,wx.ALIGN_CENTER|wx.BOTTOM,10)

        self.SetSizer(sizer)
        self.SetBackgroundColour(wx.WHITE)
        self.Fit()

        self.choices = None

    def OnOK(self, evt):
        self.choices = [checkbox.GetName() for checkbox in self.checkboxes if checkbox.GetValue() == True]
        self.EndModal(0)

    def onEnterWidget(self,event):
        widget = event.GetEventObject()
        try:
            self.tooltipCallback(True,widget.infoText)
        except:            
            pass
        event.Skip()
    
    def onLeaveWidget(self,event):
        widget = event.GetEventObject()
        self.tooltipCallback(False)
        event.Skip()

