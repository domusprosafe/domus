import wx

ID_ACTION = 100
ID_CANCEL = 101

class PSQuickCompilationPagesChooser(wx.Dialog):

    def __init__(self, parent, quickCompilationPagesCallback, language, lastQuickCompilationMode):
        
        self.quickCompilationPagesCallback = quickCompilationPagesCallback
       
        from mainlogic import _ 

        title = _("Choose quick compilation mode")
        self.lastQuickCompilationMode = lastQuickCompilationMode
        wx.Dialog.__init__(self, parent, id=-1, title=title, pos=wx.DefaultPosition,size=wx.Size(400,500), style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER) 
        
        self.language = language
        font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        font1 = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        
        sb = wx.StaticBox(self, label="Option compilation")
        sb.SetFont(font)
        sb.SetForegroundColour("blue")
        boxsize = wx.StaticBoxSizer(sb, wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(5)    
        label1 = wx.StaticText(self, -1, _("Quick compilation intro"))
        label1.SetFont(font1)
        boxsize.Add(label1)
        #hbox = wx.BoxSizer(wx.VERTICAL)
        #hbox.AddSpacer(5)
        sizer.Add(boxsize,1, wx.EXPAND | wx.ALL, 5)
        sizer.AddSpacer(5)
        pages = quickCompilationPagesCallback()
        addedPages = []
        radioControls = []
        vsizer = wx.BoxSizer(wx.VERTICAL)
        from mainlogic import _        
        self.normalCompilationValue = _("Default compilation")
        radio = wx.RadioButton(self, -1, self.normalCompilationValue)
        radio.Bind(wx.EVT_RADIOBUTTON, self.onRadioButton)
        vsizer.Add(radio)
        sizer.AddSpacer(10)
        for crfName in pages:
            sizer.AddSpacer(10)
            # sb = wx.StaticBox(self, label="Option compilation")
            # sb.SetFont(font)
            # sb.SetForegroundColour("blue")
            crfLabel = wx.StaticBox(self, -1, _('CRF: ') + crfName)
            font = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD)
            crfLabel.SetFont(font)
            crfLabel.SetForegroundColour("blue")
            boxsiz = wx.StaticBoxSizer(crfLabel, wx.VERTICAL)
            # vsizer.Add(crfLabel)
            vsizer.AddSpacer(10)
            for version in pages[crfName]:
                for page in pages[crfName][version]:
                    displayName = page['pageName']
                    
                    if self.language != 'Italiano':
                        if displayName == 'Attivazione CAM in paziente deceduto in TI':
                            displayName = 'Prompting the Brain Death Committee'
                        elif displayName == 'Esito ospedaliero':
                            displayName = 'Hospital outcome'

                    if displayName in addedPages:
                        continue
                    radio = wx.RadioButton(self, -1, displayName)
                    #if page['pageName'] in addedPages:
                    #    continue
                    #radio = wx.RadioButton(self, -1, page['pageName'])
                    radioControls.append(radio)
                    radio.Bind(wx.EVT_RADIOBUTTON, self.onRadioButton)
                    descriptionLabel = wx.StaticText(self, -1, page['pageDescription'])
                    boxsiz.AddSpacer(5)
                    boxsiz.Add(radio)
                    boxsiz.Add(descriptionLabel)
                    addedPages.append(displayName)
                    #addedPages.append(page['pageName'])
            vsizer.Add(boxsiz)    
            vsizer.AddSpacer(15)
        for radio in radioControls:
            if radio.GetLabelText() == lastQuickCompilationMode:
                radio.SetValue(1)
                break
            else:
                radio.SetValue(0)
        sizer.Add(vsizer, 2, wx.ALIGN_LEFT|wx.LEFT, border=5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK)
        btnc = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        btn.SetDefault()
               
        box.Add(btn)
        box.Add(btnc, 1, flag=wx.LEFT|wx.BOTTOM, border=5)

        
        self.Bind(wx.EVT_BUTTON, self.doClose, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.doConfirm, id=wx.ID_OK)
       
        sizer.Add(box,flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10)
        self.SetSizer(sizer)
        self.Layout()
        self.chosenPage = lastQuickCompilationMode
       
    def onRadioButton(self, event):
        if event.GetEventObject().GetLabelText() == self.normalCompilationValue:
            self.chosenPage = ''
            return
        self.chosenPage = event.GetEventObject().GetLabelText()
       
    def doConfirm(self, event):
        self.EndModal(wx.ID_OK)
        
    def doClose(self,  event):
        self.chosenPage = self.lastQuickCompilationMode
        self.EndModal(wx.ID_CANCEL)
        
    def transformChosenPage(self, string):
        if self.language != 'Italiano':
            if string == 'Prompting the Brain Death Committee':
                string = 'Attivazione CAM in paziente deceduto in TI'
            elif string == 'Hospital outcome':
                string = 'Esito ospedaliero'
        return string
        
        
    def getChosenPage(self):
        return self.transformChosenPage(self.chosenPage)

