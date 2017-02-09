# -*- coding: utf-8 -*-

import wx
from validators import NotEmptyValidator, NotEmptyOrFutureDateValidator, NotEmptyOrFutureOrPastDateValidator
import psconstants as psc
from psCalendar import CalendarTextbox

class PSAdmissionDialog(wx.Dialog):
    
    """Dialogo mostrato alla creazione di un nuovo ricovero"""
    
    def __init__(self, parent, mainLogic):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1, title = _("New admission"), pos=wx.DefaultPosition,
                           size=wx.Size(350,300), style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.WS_EX_VALIDATE_RECURSIVELY,
                           name="admissionDialog")       
        self.mainLogic = mainLogic
        
        #sexCrf, sexClassName, sexAttributeName = self.mainLogic.crfData.splitAttributeName(psc.sexAttr)
        #sexCodingSet = self.mainLogic.crfData.getPropertyForAttribute(sexCrf,sexClassName,sexAttributeName,'codingSet')

        #sexCodingSetValues = self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(sexCrf,sexCodingSet)
        #self.sexNames = [''] + [self.mainLogic.translateString(self.mainLogic.crfData.getPropertyForCodingSetValue(sexCrf,sexCodingSet,sexCodingSetValue,'value')) for sexCodingSetValue in sexCodingSetValues]
        #self.sexValues = [None] + [self.mainLogic.crfData.joinCodingSetValueName(sexCrf,sexCodingSet,sexCodingSetValue) for sexCodingSetValue in sexCodingSetValues]

        #TODO: this should be taken from data configuration (basedata crf)
        self.sexNames = [''] + [_("%s") % self.mainLogic.translateString(psc.sexCodingSetValues[sexCodingSetValue]) for sexCodingSetValue in psc.sexCodingSetValues]
        self.sexValues = [None] + [sexCodingSetValue for sexCodingSetValue in psc.sexCodingSetValues]
        self.anonymized = 'IL' in self.mainLogic.centrecode
        sizer = wx.BoxSizer(wx.VERTICAL)   
        sizer.AddSpacer(20)     
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("In order to open a new admission, please fill in the following information. Fields marked with an asterisk (*) are required."))
        box.Add(label, 1, wx.EXPAND )
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND | wx.GROW)
        sizer.AddSpacer(10)  
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Last name(*)"))
        box.Add(label, 1, wx.EXPAND)
        self.lastname = wx.TextCtrl(self, -1, "", size=(80,-1), validator=NotEmptyValidator())
        box.Add(self.lastname, 2)
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("First name(*)"))
        box.Add(label, 1, wx.EXPAND)
        self.firstname = wx.TextCtrl(self, -1, "", size=(80,-1), validator=NotEmptyValidator())
        box.Add(self.firstname, 2)
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND)
        
        if self.anonymized : # TI has anonimized anagraphics
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.AddSpacer(10)
            
            from mlradiobutton import MLRadioButton
            self.radioNotReadmission = MLRadioButton(self, label=_("Not a readmission"), name=_("Not a readmission"), style=wx.RB_GROUP)
            self.radioNotReadmission.Bind(wx.EVT_RADIOBUTTON, self.NotAReadmissionButtonClicked)
            self.radioReadmission = MLRadioButton(self, label=_("Readmission"), name=_("Readmission"))
            self.radioReadmission.Bind(wx.EVT_RADIOBUTTON, self.ReadmissionButtonClicked)
            
            self.radioNotReadmission.SetFocus()
            self.radioNotReadmission.SetValue(0)
            self.radioReadmission.SetValue(0)
            
            box.Add(self.radioNotReadmission, 0, wx.ALIGN_LEFT)
            box.Add(self.radioReadmission, 0, wx.ALIGN_LEFT)
            sizer.Add(box, 1, wx.EXPAND)
        
            self.NotAReadmissionButtonClicked(wx.EVT_RADIOBUTTON)
        
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Date of birth(*)"))
        box.Add(label, 1, wx.EXPAND)
        self.birth = CalendarTextbox(self, -1, wx.DateTime(), 'dd/mm/yyyy', validator=NotEmptyOrFutureDateValidator())
        #self.birth = wx.DatePickerCtrl(self, -1, style = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY  | wx.DP_ALLOWNONE )
        box.Add(self.birth, 2)
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Sex"))
        box.Add(label, 1, wx.EXPAND)
        choices = self.sexNames
        self.sex = wx.ComboBox(self, 200, choices[0], choices=choices,style=wx.CB_DROPDOWN  | wx.CB_READONLY )
        box.Add(self.sex, 2)
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Admission date(*)"))
        box.Add(label, 1, wx.EXPAND)
        #self.admdate = wx.DatePickerCtrl(self, -1, style = wx.DP_DROPDOWN
        #                              | wx.DP_SHOWCENTURY )
        self.admdate = CalendarTextbox(self, -1, wx.DateTime(), 'dd/mm/yyyy', validator=NotEmptyOrFutureOrPastDateValidator(self.mainLogic.getCrfValidVersion))
        box.Add(self.admdate, 2)
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND)
        
        #buttons
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        btn = wx.Button(self, wx.ID_OK, _("OK"))
        if self.anonymized:
            btn.Bind(wx.EVT_BUTTON, self.checkRadioButton)
        btnc = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        btn.SetDefault()
        box.Add(btnc, 0, wx.ALIGN_CENTRE)
        box.Add(btn, 0, wx.ALIGN_CENTRE)
        
        sizer.AddSpacer(20)
        sizer.Add(box, 1, wx.ALIGN_CENTRE)
        
        self.SetSizer(sizer)
        
    def checkRadioButton(self, event):
        if self.radioNotReadmission.GetValue() == False and self.radioReadmission.GetValue() == False :
            self.radioNotReadmission.SetBackgroundColour("pink")
            self.radioReadmission.SetBackgroundColour("pink")
            self.radioNotReadmission.Refresh()
            self.radioReadmission.Refresh()
            return
        else:
            self.radioNotReadmission.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            self.radioReadmission.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            self.radioNotReadmission.Refresh()
            self.radioReadmission.Refresh()
            event.Skip()
    
    def SetDefaultValueAndActivation(self, textControl, defaultValue, activation):
        
        textControl.SetValue(defaultValue)
        textControl.SetEditable(activation)
        
        if activation :
            colour = wx.WHITE
        else :
            colour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT)

        textControl.SetBackgroundColour(colour)
    
    
    def ReadmissionButtonClicked(self, event):
        self.SetDefaultValueAndActivation(self.lastname, "Patient-", True)
        self.SetDefaultValueAndActivation(self.firstname, "Patient-", False)
        self.lastname.Bind(wx.EVT_TEXT, self.UpdateFirstName)
        
    def NotAReadmissionButtonClicked(self, event):
        if self.lastname.GetValue() == '' or self.lastname.GetValue() == "Patient-":
            patientName = self.GetNextAnonimizedName()
            self.SetDefaultValueAndActivation(self.lastname, patientName, False)
            self.SetDefaultValueAndActivation(self.firstname, patientName, False)
            self.lastname.Bind(wx.EVT_TEXT, None)
        
    def GetNextAnonimizedName (self) :
        return "Patient-%06d" % self.mainLogic.getNextLocalId('admission')
    
    def UpdateFirstName (self, event) :
        self.firstname.SetValue(self.lastname.GetValue())
        
    def GetData(self):
        """ritorna di dati del nuovo ricovero. deve gestire anche il caso di riammissione. Casi:
        1) nuovo ricovero: vengono ritornati i dati di base
        2) riammissione : come sopra ma ritorna anche l'admissionKey dell'ammissione precedente
        3) ammissione errata (caso di paziente gia presente in TI): ritorna False
        """
        out = dict()
        lastname = self.lastname.GetValue()
        firstname = self.firstname.GetValue()
        birth = self.birth.GetValue()
        sex = self.sex.GetValue()
        if self.anonymized:
            readmission = self.radioReadmission.GetValue()
        admdate = self.admdate.GetValue()
        
        out['lastName'] = lastname
        out['firstName'] = firstname
        try:
            out['birthDate'] = birth.FormatISODate()
        except:
            out['birthDate'] = None
            
        out['sex'] = self.sexValues[self.sexNames.index(sex)]
        
        try:
            out['admissionDate'] = admdate.FormatISODate()
        except:
            out['admissionDate'] = None
 
        out['admissionKey'] = -1
        
        return out
