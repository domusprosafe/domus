import wx
import os
from psconstants import abspath
from psformatslistctrl import PSFormatList

class PSDischargeLetterDialog(wx.Frame):

    def __init__(self, parent, getLetterCallback, composeLetterCallback, getLetterModelFileNamesCallback, getNewLetterFileNameCallback, oldLetterCallback, closeLetterCallback, showNotesForDischargeLetterCallback, newSystemEnabled=True, position=wx.DefaultPosition, size=wx.DefaultSize):
        from mainlogic import _
       
        wx.Frame.__init__(self, parent, -1, _("Discharge letter"), pos=position, size=size, style= wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT, name="dischargeletter")

        self.getLetterCallback = getLetterCallback
        self.composeLetterCallback = composeLetterCallback
        self.getLetterModelFileNamesCallback = getLetterModelFileNamesCallback
        self.getNewLetterFileNameCallback = getNewLetterFileNameCallback
        self.oldLetterCallback = oldLetterCallback
        self.closeLetterCallback = closeLetterCallback
        self.showNotesForDischargeLetterCallback = showNotesForDischargeLetterCallback

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        letterModelFileNamesDict = self.getLetterModelFileNamesCallback()
        letterModelFileNamesDict['docx'].sort()
        letterModelFileNamesDict['odt'].sort()
        letterModelFileNamesDict['rtf'].sort()
        letterModelFileNames = letterModelFileNamesDict['docx'] + letterModelFileNamesDict['odt'] + letterModelFileNamesDict['rtf']

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        helpButton = wx.Button(self, -1, label= _("Instruction"))
        notesButton = wx.Button(self, -1, label= _("Update discharge letter notes"))
        hbox.Add(helpButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(notesButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox,0,wx.ALIGN_CENTRE|wx.ALL,10)
        
        box_label2 = wx.StaticBox( self, -1, _("Create new letter" ))
        buttonbox2 = wx.StaticBoxSizer( box_label2, wx.HORIZONTAL )
        
        self.selectExtensionLabel = wx.StaticText(self, -1, _("Select model"))
        
        self.letterModelChoice = wx.Choice(self, -1, choices=letterModelFileNames, size=wx.Size(200,-1))
        composeButton = wx.Button(self, -1, label= _("Create new letter"))
        buttonbox2.Add(self.selectExtensionLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        buttonbox2.Add(self.letterModelChoice, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        buttonbox2.Add(composeButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        sizer.Add(buttonbox2,0,wx.ALIGN_CENTRE|wx.ALL,10)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        warningLabel = wx.StaticText(self, -1, _("Warning before create letter"))
        hbox.Add(warningLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox,0,wx.ALIGN_CENTRE|wx.ALL,10)

        box_label = wx.StaticBox( self, -1, _("Created letters" ))
        buttonbox = wx.StaticBoxSizer( box_label, wx.HORIZONTAL )
        
        #hbox = wx.BoxSizer(wx.HORIZONTAL)
        getLetterButton = wx.Button(self, -1, label= _("Browse created letters"))
        buttonbox.Add(getLetterButton, 1, wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(buttonbox,1,wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL,10)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        oldLetterButton = wx.Button(self, -1, label= _("Old system"))
        closeButton = wx.Button(self, -1, label= _("Close"))
        
        #notesButton = wx.Button(self, -1, label= _("Update discharge letter notes"))
        hbox.Add(oldLetterButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(closeButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        #hbox.Add(notesButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox,0,wx.ALIGN_CENTRE|wx.ALL,10)

        getLetterButton.Bind(wx.EVT_BUTTON,self.onGetLetter)
        composeButton.Bind(wx.EVT_BUTTON,self.onLetterCompose)
        oldLetterButton.Bind(wx.EVT_BUTTON,self.onOldLetter)
        closeButton.Bind(wx.EVT_BUTTON,self.onClose)
        helpButton.Bind(wx.EVT_BUTTON,self.onHelp)
        notesButton.Bind(wx.EVT_BUTTON,self.onNotes)

        self.Fit()
        if not newSystemEnabled:
            getLetterButton.Enable(False)
            composeButton.Enable(False)
            self.letterModelChoice.Enable(False)
        
        self.Bind(wx.EVT_CLOSE, self.onClose)
            

    def onOldLetter(self, event):
        from mainlogic import _
        dlg = wx.MessageDialog(None, 
                _("Create letter advice"),
                _("Warning"), wx.YES_NO | wx.ICON_QUESTION)
        dlg.Center()
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.oldLetterCallback()

    def onGetLetter(self, event):
        self.getLetterCallback()

    def onLetterCompose(self, event):
        letterModelFileName = self.letterModelChoice.GetStringSelection()
        from mainlogic import _
        if not self.letterModelChoice.GetItems():
            dlg = wx.MessageDialog(None, 
                _("No model was found. Please contact the PROSAFE administrator."),
                _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
        else:
            if letterModelFileName:
                format = os.path.splitext(letterModelFileName)[1][1:]
                letterName = os.path.splitext(letterModelFileName)[0]
                letterFileName = self.getNewLetterFileNameCallback(format, letterName)
                self.composeLetterCallback(letterModelFileName,letterFileName)
            else:
                dlg = wx.MessageDialog(None, 
                    _("No model was selected."),
                    _("Warning"), wx.OK | wx.ICON_ERROR)
                dlg.Center()
                dlg.ShowModal()
    
    def onClose(self, event):
        self.closeLetterCallback()
        if type(event.GetEventObject()) == wx.Button:
            self.Close(True)
        event.Skip()
        
    def onHelp(self, event):
        import webbrowser
        webbrowser.open(abspath('images/dischargeLetterInstruction.html',True))
        #sys.exit(0)
    
    def onNotes(self, event):
        self.Close(True)
        self.showNotesForDischargeLetterCallback()


class PSDischargeLetterModelDialog(wx.Frame):

    def __init__(self, parent, getLetterModelCallback, copyLetterMasterModelCallback, getLetterMasterModelFileNamesCallback, getNewLetterModelFileNameCallback, oldLetterModelCallback, closeLetterModelCallback, getFormatsAndDescriptionCallback, position=wx.DefaultPosition, size=wx.DefaultSize):
        from mainlogic import _
       
        wx.Frame.__init__(self, parent, -1, _("Discharge letter model"), pos=position, size=size, style= wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT, name="dischargelettermodel")

        self.getLetterModelCallback = getLetterModelCallback
        self.copyLetterMasterModelCallback = copyLetterMasterModelCallback
        self.getLetterMasterModelFileNamesCallback = getLetterMasterModelFileNamesCallback
        self.getNewLetterModelFileNameCallback = getNewLetterModelFileNameCallback
        self.oldLetterModelCallback = oldLetterModelCallback
        self.closeLetterModelCallback = closeLetterModelCallback
        self.getFormatsAndDescriptionCallback = getFormatsAndDescriptionCallback

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        masterModelFileNamesDict = self.getLetterMasterModelFileNamesCallback()
        masterModelFileNamesDict['docx'].sort()
        masterModelFileNamesDict['odt'].sort()
        masterModelFileNamesDict['rtf'].sort()
        masterModelFileNames = masterModelFileNamesDict['docx'] + masterModelFileNamesDict['odt'] + masterModelFileNamesDict['rtf']
        self.definitionDict = {}
        from mainlogic import _
        self.definitionDict[masterModelFileNamesDict['docx'][0].split('.')[0]] = _('Discharge model advice')
        self.definitionDict[masterModelFileNamesDict['docx'][1].split('.')[0]] = _('Admission model advice')
        extensions=[x for x in set([el.split('.')[1] for el in masterModelFileNames])]
        
        self.extensionsDict = dict()
        for ext in extensions:
            self.extensionsDict[ext] = _(ext)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        #oldLetterModelButton = wx.Button(self, -1, label= _("Old system"))
        #closeButton = wx.Button(self, -1, label= _("Close"))
        helpMasterButton = wx.Button(self, -1, label= _("Instruction"))
        #hbox.Add(oldLetterModelButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        #hbox.Add(closeButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(helpMasterButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox,0,wx.ALIGN_CENTRE|wx.ALL,10)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        box_label2 = wx.StaticBox( self, -1, _("Select and use model" ))
        buttonbox2 = wx.StaticBoxSizer( box_label2, wx.HORIZONTAL )
        
        self.modelExplanationLabel = wx.StaticText(self, -1, "")
        
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.selectExtensionLabel = wx.StaticText(self, -1, _("Avalaible models"))
        self.masterModelChoice = wx.Choice(self, -1, choices=[el.split('.')[0] for el in masterModelFileNamesDict['docx']], size=wx.Size(170,-1))
        vbox.Add(self.selectExtensionLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbox.Add(self.masterModelChoice, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(vbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.selectExtensionTypeLabel = wx.StaticText(self, -1, _("Extension"))
        self.masterModelExtensionChoice = wx.Choice(self, -1, choices=[ext for ext in self.extensionsDict.itervalues()], size=wx.Size(170,-1))
        vbox.Add(self.selectExtensionTypeLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbox.Add(self.masterModelExtensionChoice, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(vbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.selectNameLabel = wx.StaticText(self, -1, _("New file name"))
        self.dischargeLetterModelNameText = wx.TextCtrl(self, -1, "", size=(120,-1))
        vbox.Add(self.selectNameLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbox.Add(self.dischargeLetterModelNameText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(vbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        getLetterMasterModelButton = wx.Button(self, -1, label= _("Select model to be used"))
        
        
        #buttonbox2.Add(self.selectExtensionLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        #buttonbox2.Add(self.masterModelChoice, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        #buttonbox2.Add(self.masterModelExtensionChoice, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        #buttonbox2.Add(self.dischargeLetterModelNameText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        hbox.Add(getLetterMasterModelButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vbox.Add(self.modelExplanationLabel, 0, wx.ALIGN_LEFT|wx.ALL,10)
        buttonbox2.Add(vbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(buttonbox2,0,wx.ALIGN_CENTRE|wx.ALL,10)
        
        modifyExplanationLabel = wx.StaticText(self, -1, _("Modify hint"))
        box_label = wx.StaticBox(self, -1, _("Usable models" ))
        buttonbox = wx.StaticBoxSizer( box_label, wx.VERTICAL)
        buttonbox.Add(modifyExplanationLabel, 1, wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL, 5)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        getLetterModelButton = wx.Button(self, -1, label= _("Browse usable models"))
        hbox.Add(getLetterModelButton, 1, wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL, 5)
        
        showFormatsButton = wx.Button(self, -1, label= _("Formats"))
        hbox.Add(showFormatsButton, 1, wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL, 5)
        buttonbox.Add(hbox, 0, wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(buttonbox,1,wx.EXPAND|wx.ALIGN_CENTRE|wx.ALL,10)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        #oldLetterModelButton = wx.Button(self, -1, label= _("Old system"))
        closeButton = wx.Button(self, -1, label= _("Close"))
        #helpMasterButton = wx.Button(self, -1, label= _("Instruction"))
        #hbox.Add(oldLetterModelButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        hbox.Add(closeButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        #hbox.Add(helpMasterButton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox,0,wx.ALIGN_CENTRE|wx.ALL,10)
        

        getLetterModelButton.Bind(wx.EVT_BUTTON,self.onGetLetterModel)
        getLetterMasterModelButton.Bind(wx.EVT_BUTTON,self.onGetLetterMasterModel)
        #oldLetterModelButton.Bind(wx.EVT_BUTTON,self.onOldLetterModel)
        closeButton.Bind(wx.EVT_BUTTON,self.onClose)
        helpMasterButton.Bind(wx.EVT_BUTTON,self.onHelp)
        showFormatsButton.Bind(wx.EVT_BUTTON,self.onShowFormats)
        self.masterModelChoice.Bind(wx.EVT_CHOICE, self.onChoiceSelectedItemChanged)        
        self.Fit()
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def onChoiceSelectedItemChanged(self, event):
        self.modelExplanationLabel.SetLabel(self.definitionDict[event.GetString()])
        event.Skip()
    
    def onShowFormats(self, event):
        formatsAndDescription = self.getFormatsAndDescriptionCallback()
        showFormatFrame = PSFormatList(parent=self, formatsAndDescriptionsDict=formatsAndDescription)
        showFormatFrame.Center()
        size = self.GetSize()
        showFormatFrame.SetSize((min(size[0]-100,800),size[1]-100))
        showFormatFrame.Show()
    
    def onOldLetterModel(self, event):
        self.oldLetterModelCallback()

    def onGetLetterModel(self, event):
        self.getLetterModelCallback()
        
    def onHelp(self, event):
        import webbrowser
        webbrowser.open(abspath('images/dischargeLetterModelInstruction.html',True))
        #sys.exit(0)

    def onGetLetterMasterModel(self, event):
        from mainlogic import _
        if self.masterModelChoice.GetStringSelection() == '' or self.masterModelExtensionChoice.GetStringSelection() == '':
            return
            
        masterModelExtension = ''
        for key, value in self.extensionsDict.iteritems():
            if value == self.masterModelExtensionChoice.GetStringSelection():
                masterModelExtension = key
            
        masterModelFileName = self.masterModelChoice.GetStringSelection() + '.' + masterModelExtension
        if not self.masterModelChoice.GetItems():
            dlg = wx.MessageDialog(None, 
                _("No model was found. Please contact the PROSAFE administrator."),
                _("ERROR"), wx.OK | wx.ICON_ERROR)
            dlg.Center()
            dlg.ShowModal()
        else:
            if masterModelFileName:
                userModelName = ''
                if self.dischargeLetterModelNameText.GetValue():
                    userModelName = self.dischargeLetterModelNameText.GetValue()
                format = os.path.splitext(masterModelFileName)[1][1:]
                modelName = os.path.splitext(masterModelFileName)[0]
                modelFileName = self.getNewLetterModelFileNameCallback(format, modelName, userModelName)
                self.copyLetterMasterModelCallback(masterModelFileName,modelFileName)
                dlg = wx.MessageDialog(None, 
                    _("Usable model added succesfully!"),
                    _("Success"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.Center()
                dlg.ShowModal()
            else:
                dlg = wx.MessageDialog(None, 
                    _("No model was selected."),
                    _("Warning"), wx.OK | wx.ICON_ERROR)
                dlg.Center()
                dlg.ShowModal()

    def onClose(self, event):
        self.closeLetterModelCallback()
        if type(event.GetEventObject()) == wx.Button:
            self.Close(True)
        event.Skip()


