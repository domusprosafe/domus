import wx
import time
from psCalendar import CalendarTextbox
import psconstants as psc

class PSFilterControl(wx.Panel):

    def __init__(self, parent, label='', attrDataType=None, codingSet=None, attribute=None):
        
        self.attrDataType = attrDataType
        self.codingSet = codingSet
        self.attribute = attribute
        
        self.stringInput = None
        self.dateInput1 = None
        self.dateInput2 = None

        wx.Panel.__init__(self, parent, id=-1, size=(80,-1))
        
        if self.attribute:
            crfName, className, attributeName = self.attribute.split('.')

            self.attrDataType = psc.attrDataTypes[self.attribute]
            self.codingSet = psc.attrCodingSets[self.attribute]
            
            self.label = className
        
        if label != '':
            self.label = label
        
        self.opList = []
        self.defaultOpValue = ''
        self.actualOpValue = ''
        
        self.buildOplist()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL) 
        
        if self.label != '':
            self.labelWg = wx.StaticText(self, -1, self.label, size=wx.Size(120, -1))
            sizer.Add(self.labelWg, 0, wx.RIGHT | wx.EXPAND)
        
        if self.opList:
            self.opCb = wx.ComboBox(self, 500, self.defaultOpValue, (0,0), (120,-1), self.opList, wx.CB_DROPDOWN | wx.CB_READONLY)
            sizer.Add(self.opCb, 0,  wx.ALIGN_LEFT)
            self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, self.opCb)
        
        self.inputSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.buildInputControls(self.inputSizer)
        
        sizer.Add(self.inputSizer, wx.ALIGN_LEFT)
        
        self.SetSizer(sizer)
        sizer.Layout()
        
        self.baseCol = self.GetBackgroundColour()
        
    def EvtComboBox(self, evt):
        e = evt.GetString()

        if self.actualOpValue != e:
            self.actualOpValue = e      
            self.buildInputControls(self.inputSizer)
    
    def setFilterValue(self,opValue,values):
        self.actualOpValue = opValue
        self.opCb.SetValue(opValue)
       
        if self.attrDataType == 'string' and len(values) > 0:
            self.stringInput.SetValue(values[0])
        elif self.attrDataType == 'datetime' and len(values) > 0:
            thedate = wx.DateTime()
            try:
                thedate.ParseFormat(values[0],'%Y-%m-%d')
                self.dateInput1.SetValue(thedate)
            except:
                pass
            if len(values) > 1:
                try:
                    thedate.ParseFormat(values[1],'%Y-%m-%d')
                    self.dateInput2.SetValue(thedate)
                except:
                    pass

    def getFilterValue(self):
        fout = dict()
        fout['reverse'] = False
        fout['attribute'] = self.attribute
        fout['opvalue'] = self.actualOpValue
        fout['values'] = []
        
        from mainlogic import _

        if self.actualOpValue == _('is filled'):
            fout['conditions'] = [lambda value: value != None]
            return fout
            
        elif self.actualOpValue == _('is not filled'):
            fout['conditions'] = [lambda value: value == None]
            return fout
        
        elif self.attrDataType == 'string':
            vl = self.stringInput.GetValue()
            if not vl:
                return None
            fout['values'].append(vl)
            if self.actualOpValue == _("is"):
                fout['conditions'] = [lambda value: value.lower() == vl.lower()]
            elif self.actualOpValue == _("is not"):
                fout['conditions'] = [lambda value: value.lower() != vl.lower()]
            return fout

        elif self.attrDataType == 'datetime':
            vl = None
            vl2 = None
            try:
                vl = self.dateInput1.GetValue().FormatISODate()
                fout['values'].append(vl)
            except: 
                return None

            if self.actualOpValue == _("is"):
                fout['conditions'] = [lambda value: time.strptime(value,'%Y-%m-%d') == time.strptime(vl,'%Y-%m-%d')]
            elif self.actualOpValue == _("before"):
                fout['conditions'] = [lambda value: time.strptime(value,'%Y-%m-%d') < time.strptime(vl,'%Y-%m-%d')]
            elif self.actualOpValue == _("after"):
                fout['conditions'] = [lambda value: time.strptime(value,'%Y-%m-%d') > time.strptime(vl,'%Y-%m-%d')]
            elif self.actualOpValue == _("between"):
                try:
                    vl2 = self.dateInput2.GetValue().FormatISODate()
                    fout['values'].append(vl2)
                except: 
                    return None
                fout['conditions'] = [lambda value: time.strptime(value,'%Y-%m-%d') > time.strptime(vl,'%Y-%m-%d'),
                                      lambda value: time.strptime(value,'%Y-%m-%d') < time.strptime(vl2,'%Y-%m-%d')]
            return fout
            
        return None
    
    def buildOplist(self):
        from mainlogic import _
        if self.attrDataType == 'string':
            self.opList = [_("is"), _("is not"), _('is filled'), _('is not filled')]
            self.defaultOpValue =_("is")

        elif self.attrDataType == 'int' or  self.attrDataType == 'float':
            self.opList = ["=", "<", ">"]
            self.defaultOpValue = '='

        elif self.attrDataType == 'datetime':
            self.opList = [_("is"), _("before"), _("after"), _("between"), _('is filled'), _('is not filled')]
            self.defaultOpValue = _("is")

        self.actualOpValue = self.defaultOpValue
            
    def buildInputControls(self, sizer):

        #sizer.Clear(True)
        
        from mainlogic import _
        if self.actualOpValue == _('is filled') or self.actualOpValue ==  _('is not filled'):

            if self.attrDataType == 'string':
                if self.stringInput:
                    self.stringInput.Hide()

            elif self.attrDataType == 'datetime':
                if self.dateInput1:
                    self.dateInput1.Hide()
                if self.dateInput2:
                    self.andLabel.Hide()
                    self.dateInput2.Hide()

        else:

            if self.attrDataType == 'string':

                if not self.stringInput:
                    self.stringInput = wx.TextCtrl(self, -1, "", size=wx.DefaultSize)
                    sizer.Add(self.stringInput, 1, wx.EXPAND)
                self.stringInput.Show()

            elif self.attrDataType == 'datetime':

                if not self.dateInput1:
                    self.dateInput1 = CalendarTextbox(self, -1, wx.DateTime(), 'dd/mm/yyyy')
                    sizer.Add(self.dateInput1, 1, wx.EXPAND)
                self.dateInput1.Show()
                
                if self.opCb.GetValue()== _("between"):           
                    if not self.dateInput2:
                        sizer.AddSpacer(5)
                        self.andLabel = wx.StaticText(self, -1, _("and"), size=wx.Size(25, -1))
                        sizer.Add(self.andLabel, 0)
                        sizer.AddSpacer(5)
                        self.dateInput2 = CalendarTextbox(self, -1, wx.DateTime(), 'dd/mm/yyyy')
                        sizer.Add(self.dateInput2, 1, wx.EXPAND)      
                    self.andLabel.Show()
                    self.dateInput2.Show()

                else:
                    if self.dateInput2:
                        self.andLabel.Hide()
                        self.dateInput2.Hide()
        
        sizer.Layout()
        
    def setActiveColor(self):
        self.labelWg.SetBackgroundColour('yellow')
        self.Layout()
        
    def setInactiveColor(self):
        self.labelWg.SetBackgroundColour(self.baseCol)
        self.Layout()

