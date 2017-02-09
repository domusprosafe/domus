import wx
from psmessagedialog import PSMessageDialog
import wx.lib.scrolledpanel as scrolled
import psconstants as psc
import os
from psevaluator import decodevalue, decode

ID_CREATE = 102

captionFont = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD)

class gcpScrollablePanel(scrolled.ScrolledPanel):
    def __init__(self, parent, id, pos, size):
        scrolled.ScrolledPanel.__init__(self, parent, -1, pos, size)

class PSGcpDialog(wx.Dialog):
    def __init__(self, parent, confirmCallBack, changedAttributes, isReadOnly=False, inputUserKey=None, position=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION|wx.FULL_REPAINT_ON_RESIZE):
        caption = 'GCP'
        from mainlogic import _
        self.inputUserKey = inputUserKey
        wx.Dialog.__init__(self, parent, -1, caption, position, size, style)
        x, y = position
        if x == -1 and y == -1:
            self.CenterOnScreen(wx.BOTH)
        
        self.changedAttributes = changedAttributes
        self.isReadOnly = isReadOnly
        self.confirmCallBack = confirmCallBack
        one, two = size
        newSize = wx.Size(one-10, two-10)
        three, four = position
        position = (three+ 5, four+4)
        panel = gcpScrollablePanel(self, -1, position, newSize)
        
        
        topSizer = wx.BoxSizer(wx.VERTICAL)
        titleSizer = wx.BoxSizer(wx.HORIZONTAL)
        helpLabel = wx.StaticText(panel, -1, _("Please provide the motivation of your changements."))
        titleSizer.Add(helpLabel, 0, wx.ALL, 5)
        
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(panel, ID_CREATE, label= _("Confirm"))
        btn.Bind(wx.EVT_BUTTON, self.onConfirm)
        closeBtn = wx.Button(panel, wx.ID_CLOSE, label= _("Close"))
        closeBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        buttonSizer.Add(btn, 0, wx.ALL, 5)
        buttonSizer.Add(closeBtn, 0, wx.ALL, 5)
        if self.isReadOnly:
            btn.Hide()
            helpLabel.SetLabel(_("This is the list of changements done for this admission."))
            
        sizer = wx.GridBagSizer(10,10)
        
        optionList = ['Input error', 'Communication error', 'Error on the report', 'Other error', 'Data not updated', 'Another reason which excludes the previous']
        self.optionDict = {}
        for value in optionList:
            self.optionDict[_(value)] = value
            
        labelClassName = wx.StaticText(panel, -1, _("CLASSNAME"))
        labelPrevious = wx.StaticText(panel, -1, _("PREVIOUS VALUE"))
        labelCurrent = wx.StaticText(panel, -1, _("CURRENT VALUE"))
        labelMotivation = wx.StaticText(panel, -1, _("REASON"))
        
        labelClassName.SetFont(captionFont)
        labelPrevious.SetFont(captionFont)
        labelCurrent.SetFont(captionFont)
        labelMotivation.SetFont(captionFont)
        rowCounter = 0
        
        sizer.Add(labelClassName, (rowCounter,0), (1,1), flag=wx.EXPAND|wx.ALL, border=10)
        sizer.Add(labelPrevious, (rowCounter,1), (1,1), flag=wx.EXPAND|wx.ALL, border=10)
        sizer.Add(labelCurrent, (rowCounter,2), (1,1), flag=wx.EXPAND|wx.ALL, border=10)
        sizer.Add(labelMotivation, (rowCounter,3), (1,1), flag=wx.EXPAND|wx.ALL, border=10)
        if self.isReadOnly:
            labelUser = wx.StaticText(panel, -1, _("USER"))
            labelUser.SetFont(captionFont)
            sizer.Add(labelUser, (rowCounter,4), (1,1), flag=wx.EXPAND|wx.ALL, border=10)

        self.comboBoxToClassNames = {}
        addedGroupLabels = []
        for className in changedAttributes.keys():
            for timeStamp in changedAttributes[className].keys():
                from operator import itemgetter
                mylist = sorted(changedAttributes[className][timeStamp], key=itemgetter('classInstanceNumber', 'attributeName'))
                for element in mylist:
                    rowCounter += 1
                    text = element['classNameTranslation']
                    if timeStamp > 1:
                        text = element['classNameTranslation'] + ' ' + str(timeStamp)
                    if 'groupLabel' in element and element['groupLabel'] not in addedGroupLabels:
                        text = decodevalue(element['groupLabel']).upper() + '\n\t' + text
                    if 'groupLabel' in element and element['groupLabel'] in addedGroupLabels:
                        text = '\t' + text
                    if 'groupLabel' in element and element['groupLabel'] not in addedGroupLabels:
                        addedGroupLabels.append(element['groupLabel'])
                    classLabel = wx.StaticText(panel, -1, text, size=wx.Size(-1,-1))
                    sizer.Add(classLabel,(rowCounter,0),(1,1), flag=wx.EXPAND|wx.ALL, border=10)
                    previousAttributeString = element['previousAttributeValue']
                    
                    if type(element['previousAttributeValue']) is list:
                        parsedList = self.normalizeAttributeValueList(element['previousAttributeValue'])
                        previousAttributeString = ', '.join(decode(parsedList))
                        #previousAttributeString = previousAttributeString.strip(',')
                    else:
                        previousAttributeString = str(previousAttributeString).replace('None', '')
                        if previousAttributeString in [True, 'True']:
                            previousAttributeString = 'core.yesNoCodification.yes'
                        if previousAttributeString in [False, 'False']:
                            previousAttributeString = 'core.yesNoCodification.no'
                        previousAttributeString = decodevalue(attributeString)    
                        
                    attributeString = element['attributeValue']
                    if type(element['attributeValue']) is list:
                        parsedList = self.normalizeAttributeValueList(element['attributeValue'])
                        attributeString = ', '.join(decode(parsedList))
                    else:
                        attributeString = str(attributeString).replace('None', '')
                        if attributeString in [True, 'True']:
                            attributeString = 'core.yesNoCodification.yes'
                        if attributeString in [False, 'False']:
                            attributeString = 'core.yesNoCodification.no'
                        attributeString = decodevalue(attributeString)                
                    label1 = wx.StaticText(panel, -1, previousAttributeString, size=wx.Size(200,-1))
                    label2 = wx.StaticText(panel, -1, attributeString, size=wx.Size(200,-1))
                    label1.Wrap(label1.GetSize().width) 
                    label2.Wrap(label2.GetSize().width) 
                    sizer.Add(label1,(rowCounter,1),(1,1), flag=wx.EXPAND|wx.ALL, border=10)
                    sizer.Add(label2, (rowCounter,2),(1,1), flag=wx.EXPAND|wx.ALL, border=10)
                    if not self.isReadOnly:
                        cb = wx.ComboBox(panel, -1 + rowCounter, "", wx.DefaultPosition, 
                                     (220, -1), [_(el) for el in optionList],
                                     wx.CB_DROPDOWN | wx.CB_READONLY                         
                                     )
                        if className not in self.comboBoxToClassNames:
                            self.comboBoxToClassNames[className] = {}
                        if timeStamp not in self.comboBoxToClassNames[className]:
                            self.comboBoxToClassNames[className][timeStamp] = []
                        self.comboBoxToClassNames[className][timeStamp].append({'combobox':cb, 'attributeName':element['attributeName'], 'classInstanceNumber':element['classInstanceNumber'], 'previousAttributeValue':element['previousAttributeValue'] , 'attributeValue':element['attributeValue'], 'datetime':element['datetime'], 'crfName':element['crfName']})
                        sizer.Add(cb, (rowCounter,3),(1,1), flag=wx.EXPAND|wx.ALL, border=10)
                    else:
                        label3 = wx.StaticText(panel, -1, _(element['motivation']), size=wx.Size(200,-1))
                        label3.Wrap(label3.GetSize().width) 
                        sizer.Add(label3, (rowCounter,3),(1,1), flag=wx.EXPAND|wx.ALL, border=10)
                        label4 = wx.StaticText(panel, -1, _(element['userKey']), size=wx.Size(200,-1))
                        label4.Wrap(label4.GetSize().width) 
                        sizer.Add(label4, (rowCounter,4),(1,1), flag=wx.EXPAND|wx.ALL, border=10)
        
        for i in range(4):
            sizer.AddGrowableCol(i)
        for i in range(rowCounter +1):
            sizer.AddGrowableRow(i)
        
        topSizer.Add(titleSizer, 0, wx.CENTER)
        topSizer.Add(wx.StaticLine(panel), 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(sizer, 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(wx.StaticLine(panel), 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(buttonSizer, 0, wx.CENTER)
        
        panel.SetSizer(topSizer)
        panel.SetupScrolling()
        self.SetSizeHints(250,200,size.width,size.height)
        topSizer.Fit(self)
        #panel.SetAutoLayout(1)
        #self.Layout()
        
    def normalizeAttributeValueList(self, list):
        returnList = list
        for el in returnList:
            if el in [None, 'None']:
                el = ''
            if el in [True, 'True']:
                el = 'core.yesNoCodification.yes'
            if el in [False, 'False']:
                el = 'core.yesNoCodification.no'
        return returnList
        

    def onClose(self, event):
        try:
            from mainlogic import _
            if not self.isReadOnly:
                dlg = PSMessageDialog(None,
                    _("Some data hasn't been confirmed. Do you really want to exit?"),
                    _("Confirm save"), mode=2)
                result = dlg.ShowModal()
                dlg.Destroy()    
                if dlg.returnValue == wx.ID_YES:
                    self.Destroy()
            else:
                self.Destroy()
        except BaseException, e:
            print e
            
    def onConfirm(self, event):
        from mainlogic import _
        confirmResult = {}
        abortConfirm = False
        for className in self.comboBoxToClassNames.keys():
            for timeStamp in self.comboBoxToClassNames[className]:
                for comboBoxDict in self.comboBoxToClassNames[className][timeStamp]:
                    confirmResultString = self.optionDict[comboBoxDict['combobox'].GetValue()]
                    if not confirmResultString:
                        abortConfirm = True
                        break
                    if className not in confirmResult:
                        confirmResult[className] = {}
                    if timeStamp not in confirmResult[className]:
                        confirmResult[className][timeStamp] = []
                    confirmResult[className][timeStamp].append({'previousAttributeValue':comboBoxDict['previousAttributeValue'], 'attributeValue':comboBoxDict['attributeValue'], 'motivation':confirmResultString, 'datetime':comboBoxDict['datetime'], 'attributeName':comboBoxDict['attributeName'], 'crfName':comboBoxDict['crfName'], 'classInstanceNumber':comboBoxDict['classInstanceNumber'], 'userKey':self.inputUserKey})
        if abortConfirm:
            wx.MessageBox(_("Data must be completed."), _("Error"))
            return
        self.confirmCallBack(confirmResult)
        self.Destroy()
