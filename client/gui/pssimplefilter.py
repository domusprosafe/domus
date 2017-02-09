import wx
import datetime
from psCalendar import CalendarTextbox
import psconstants

class PSSimpleFilter(wx.CollapsiblePane):
    
    def __init__(self, parent, id, applyFiltersCallback, title="Browser filter"):
        from mainlogic import _
        wx.CollapsiblePane.__init__(self, parent, id, label=_("Data filter"), size=wx.Size(0,200), style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
       
        self.applyFiltersCallback = applyFiltersCallback 
        self.ctrls = dict()
        
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self)
        self.MakePaneContent(self.GetPane())
        self.filtersDict = None

    def updateFilterControls(self, filtersDict):
        self.filtersDict = filtersDict
        for key in self.ctrls:
            if key not in filtersDict:
                self.ctrls[key].SetValue('')
                continue
            value = filtersDict[key]
            if type(self.ctrls[key]) == CalendarTextbox:
                valueTmp = wx.DateTime()
                valueTmp.ParseFormat(value, '%Y-%m-%d')
                if valueTmp.IsValid():
                    value = valueTmp
                else:
                    value = ''
            self.ctrls[key].SetValue(value)

    def getFiltersDict(self):
        self.filtersDict = dict()
        for key in self.ctrls:
            value = self.ctrls[key].GetValue()
            if type(value) == wx.DateTime:
                if value.IsValid():
                    value = value.FormatISODate()
                else:
                    value = ''
            self.filtersDict[key] = value
        return self.filtersDict

    def OnPaneChanged(self, evt=None):
        #self.updateFilterControls()
        self.Layout()
        self.GetParent().Layout()
        self.GetParent().Refresh()

    def MakePaneContent(self, pane):

        from mainlogic import _
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)

        self.ctrls = dict()       
 
        label = wx.StaticText(pane, -1, _("First Name"))
        ctrl = wx.TextCtrl(pane, -1, "")
        hsizer.Add(label)
        hsizer.AddSpacer(5)
        hsizer.Add(ctrl)
        self.ctrls['FirstName'] = ctrl

        hsizer.AddSpacer(30)

        label = wx.StaticText(pane, -1, _("Last Name"))
        ctrl = wx.TextCtrl(pane, -1, "")
        hsizer.Add(label)
        hsizer.AddSpacer(5)
        hsizer.Add(ctrl)
        self.ctrls['LastName'] = ctrl

        hsizer.AddSpacer(30)

        label = wx.StaticText(pane, -1, _("Medical record id"))
        ctrl = wx.TextCtrl(pane, -1, "")
        hsizer.Add(label)
        hsizer.AddSpacer(5)
        hsizer.Add(ctrl)
        self.ctrls['EhrId'] = ctrl

        sizer.Add(hsizer)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
 
        label = wx.StaticText(pane, -1, _("Admission date")+" "+_("from"))
        from datetime import date
        ctrl = CalendarTextbox(pane, -1, wx.DateTime(), 'dd/mm/yyyy')
        hsizer.Add(label)
        hsizer.AddSpacer(5)
        hsizer.Add(ctrl)
        self.ctrls['AdmissionMinDate'] = ctrl

        hsizer.AddSpacer(5)

        label = wx.StaticText(pane, -1, _("to"))
        from datetime import date
        ctrl = CalendarTextbox(pane, -1, wx.DateTime(), 'dd/mm/yyyy')
        hsizer.Add(label)
        hsizer.AddSpacer(5)
        hsizer.Add(ctrl)
        self.ctrls['AdmissionMaxDate'] = ctrl

        hsizer.AddSpacer(30)

        if psconstants.appName == 'prosafe':

            label = wx.StaticText(pane, -1, _("Duration of admission (hours)") + " <=")
            ctrl = wx.TextCtrl(pane, -1, "")
            hsizer.Add(label)
            hsizer.AddSpacer(5)
            hsizer.Add(ctrl)
            self.ctrls['AdmissionHours'] = ctrl

            hsizer.AddSpacer(30)

        sizer.Add(hsizer, 0)

        sizer.AddSpacer(10)
        
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.applyBtn = wx.Button(pane, -1, _("Apply filter"))
        self.btnSizer.Add(self.applyBtn, 0, wx.ALIGN_CENTRE)

        self.removeBtn = wx.Button(pane, -1, _("Remove filter"))
        self.btnSizer.Add(self.removeBtn, 0, wx.ALIGN_CENTRE)
        self.btnSizer.Hide(self.removeBtn)
        
        sizer.Add(self.btnSizer, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(5)
        
        self.Bind(wx.EVT_BUTTON, self.doApplyFilter, self.applyBtn)
        self.Bind(wx.EVT_BUTTON, self.doRemoveFilter, self.removeBtn)

        pane.SetSizer(sizer)
        sizer.Layout()
        self.sizer = sizer
    
    def doApplyFilter(self, event):

        from mainlogic import _

        self.filtersDict = self.getFiltersDict()

        if self.filtersDict:
            self.applyFiltersCallback(self.filtersDict)
            self.btnSizer.Show(self.removeBtn)
            self.applyBtn.SetLabel(_("Update filter"))
            self.sizer.Layout()            

    def doRemoveFilter(self, event):

        from mainlogic import _

        self.filtersDict = dict()
        self.filtersDict['FirstName'] = ''
        self.filtersDict['LastName'] = ''
        self.filtersDict['EhrId'] = ''
        self.filtersDict['AdmissionMinDate'] = ''
        self.filtersDict['AdmissionMaxDate'] = ''
        self.filtersDict['AdmissionHours'] = ''
        self.applyFiltersCallback(self.filtersDict)
        self.updateFilterControls(self.filtersDict)

        self.btnSizer.Hide(self.removeBtn)
        self.applyBtn.SetLabel( _("Apply filter"))
        self.sizer.Layout()

