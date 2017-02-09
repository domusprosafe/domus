import wx
import datetime
import psconstants as psc
from psfiltercontrol import PSFilterControl

class PSFilter(wx.CollapsiblePane):
    
    def __init__(self, parent, id, filtersCallback, title="Browser filter"):
        from mainlogic import _
        wx.CollapsiblePane.__init__(self, parent, id, label=_("Data filter"), size=wx.Size(0,200), style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
       
        self.filtersCallback = filtersCallback 
        
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self)
        self.MakePaneContent(self.GetPane())
        self.updateFilterControls()

        #event binding
        #self.Bind(wx.EVT_BUTTON, self.doAddFilter, self.addFieldBtn)

    def updateFilterControls(self):

        from mainlogic import _
        filters = self.filtersCallback()
        for filter in filters:
            for ctrl in self.GetPane().GetChildren():
               if type(ctrl) == PSFilterControl:
                   if ctrl.attribute != filter['attribute']:
                      continue
                   ctrl.setFilterValue(filter['opvalue'],filter['values'])
                   if filter['opvalue'] != "":
                       ctrl.setActiveColor()
                   else:
                       ctrl.setInactiveColor()
        if filters:
            self.btnSizer.Show(self.removeBtn)
            self.applyBtn.SetLabel(_("Update filter"))
            self.sizer.Layout()
        else:
            self.btnSizer.Hide(self.removeBtn)
            self.applyBtn.SetLabel( _("Apply filter"))
            self.sizer.Layout()

    def OnPaneChanged(self, evt=None):

        self.Layout()
        self.GetParent().Layout()
        self.GetParent().Refresh()

    def MakePaneContent(self, pane):

        from mainlogic import _
        sizer = wx.BoxSizer(wx.VERTICAL)

        vsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.AddSpacer(5)
        sizer.AddSpacer(5)

        numberOfFilters = len(psc.filterList)
 
        sizerLeft = wx.BoxSizer(wx.VERTICAL)

        for key in psc.filterList[:numberOfFilters/2]:
            ctrl = PSFilterControl(pane,attribute=psc.basedataAttributeDict[key],label=psc.filterDict[key])
            sizerLeft.Add(ctrl,0,wx.GROW)
        
        vsizer.Add(sizerLeft)
        vsizer.AddSpacer(15)
        
        sizerRight = wx.BoxSizer(wx.VERTICAL)

        for key in psc.filterList[numberOfFilters/2:]:
            ctrl = PSFilterControl(pane,attribute=psc.basedataAttributeDict[key],label=psc.filterDict[key])
            sizerRight.Add(ctrl,0,wx.GROW)
 
        vsizer.Add(sizerRight)

        sizer.Add(vsizer,0)
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
        filters = []
        for ctrl in self.GetPane().GetChildren():
           if type(ctrl) == PSFilterControl:
               flv = ctrl.getFilterValue()
               if  flv != None:
                   print "!!!!!", flv
                   filters.append(flv)
                   ctrl.setActiveColor()
               else:
                   ctrl.setInactiveColor()

        print "########" * 10
        print filters
        self.filtersCallback(filters)

        if filters:
            self.btnSizer.Show(self.removeBtn)
            self.applyBtn.SetLabel(_("Update filter"))
            self.sizer.Layout()

    def doRemoveFilter(self, event):

        from mainlogic import _
        filters = []
        self.filtersCallback(filters)
        for ctrl in self.GetPane().GetChildren():
            if type(ctrl) == PSFilterControl:
                ctrl.setInactiveColor()

        self.btnSizer.Hide(self.removeBtn)
        self.applyBtn.SetLabel( _("Apply filter"))
        self.sizer.Layout()

