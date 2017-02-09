import wx
import wx.richtext as rt
import rt_images as images
import re
import sys

class PSDischargeLetter(wx.Frame):

    def __init__(self, *args, **kw):

        if 'filename' not in kw:
            raise Exception('Error: No filename provided!')

        if 'mainLogic' not in kw:
            raise Exception('Error: No mainLogic provided!')

        if 'resetCallback' not in kw:
            raise Exception('Error: No resetCallback provided!')

        if 'undoResetCallback' not in kw:
            raise Exception('Error: No undoResetCallback provided!')

        self.filename = kw.pop('filename')
        self.mainLogic = kw.pop('mainLogic')
        self.resetCallback = kw.pop('resetCallback')
        self.undoResetCallback = kw.pop('undoResetCallback')
        self.editModel = kw.pop('editModel',False)

        wx.Frame.__init__(self, *args, **kw)

        if rt.RichTextBuffer.FindHandlerByType(rt.RICHTEXT_TYPE_XML) is None:
            rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler())

        self.styleChangeMode = 'character'

        self.MakeMenuBar()
        self.MakeToolBar()
        #self.CreateStatusBar()
        #self.SetStatusText("")

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        self.rtc = rt.RichTextCtrl(self, style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER);
        sizer.Add(self.rtc,1,wx.EXPAND)
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer()

        from mainlogic import _

        insertButton = wx.Button(self,-1,_("Insert variable"))
        insertButton.Bind(wx.EVT_BUTTON,self.OnInsertVariable)
        buttonSizer.Add(insertButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        removeButton = wx.Button(self,-1,_("Remove variable"))
        removeButton.Bind(wx.EVT_BUTTON,self.OnRemoveVariable)
        buttonSizer.Add(removeButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        addImageButton = wx.Button(self,-1,_("Add image"))
        addImageButton.Bind(wx.EVT_BUTTON,self.OnAddImage)
        buttonSizer.Add(addImageButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        sizer.AddSpacer(10)
        sizer.Add(buttonSizer,0,wx.EXPAND|wx.LEFT|wx.RIGHT,20)
        sizer.AddSpacer(10)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer()

        saveButton = wx.Button(self,wx.ID_SAVE)
        saveButton.Bind(wx.EVT_BUTTON,self.OnFileSave)
        buttonSizer.Add(saveButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        resetButton = wx.Button(self,-1,_("Reset"))
        resetButton.Bind(wx.EVT_BUTTON,self.OnReset)
        buttonSizer.Add(resetButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        undoResetButton = wx.Button(self,-1,_("Undo reset"))
        undoResetButton.Bind(wx.EVT_BUTTON,self.OnUndoReset)
        buttonSizer.Add(undoResetButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        printButton = wx.Button(self,wx.ID_PRINT)
        printButton.Bind(wx.EVT_BUTTON,self.OnPrint)
        buttonSizer.Add(printButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        #printPreviewButton = wx.Button(self,wx.ID_PREVIEW)
        #printPreviewButton.Bind(wx.EVT_BUTTON,self.OnPrintPreview)
        #buttonSizer.Add(printPreviewButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)

        closeButton = wx.Button(self,wx.ID_CLOSE)
        closeButton.Bind(wx.EVT_BUTTON,self.OnFileExit)
        buttonSizer.Add(closeButton,0,wx.ALIGN_RIGHT|wx.RIGHT,5)
 
        sizer.Add(buttonSizer,0,wx.EXPAND|wx.LEFT|wx.RIGHT,20)
        sizer.AddSpacer(10)

        self.rtcFeedbackEnabled = True

        self.tagList = []
        self.modified = False

        hframe = wx.Frame(self)
        hframe.Hide()
        self.ortc = rt.RichTextCtrl(hframe, style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER);
        #self.ortc = rt.RichTextCtrl(self, style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER);
        #sizer.Add(self.ortc,1,wx.EXPAND)

        if not self.editModel:
            insertButton.Hide()
            #removeButton.Hide()
        self.LoadFile()

        self.rtc.Bind(rt.EVT_RICHTEXT_CONTENT_INSERTED,self.OnContentInserted)
        self.rtc.Bind(rt.EVT_RICHTEXT_CONTENT_DELETED,self.OnContentDeleted)
        self.rtc.Bind(rt.EVT_RICHTEXT_STYLE_CHANGED,self.OnStyleChanged)
        self.rtc.Bind(wx.EVT_CHAR,self.OnEditEvent)
        self.rtc.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)

        wx.CallAfter(self.rtc.SetFocus)

    def Modified(self, modified=True):
        self.modified = modified

    def SetFontStyle(self, fontColor = None, fontBgColor = None, fontFace = None, fontSize = None,
                     fontBold = None, fontItalic = None, fontUnderline = None):
      if fontColor:
         self.textAttr.SetTextColour(fontColor)
      if fontBgColor:
         self.textAttr.SetBackgroundColour(fontBgColor)
      if fontFace:
         self.textAttr.SetFontFaceName(fontFace)
      if fontSize:
         self.textAttr.SetFontSize(fontSize)
      if fontBold != None:
         if fontBold:
            self.textAttr.SetFontWeight(wx.FONTWEIGHT_BOLD)
         else:
            self.textAttr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
      if fontItalic != None:
         if fontItalic:
            self.textAttr.SetFontStyle(wx.FONTSTYLE_ITALIC)
         else:
            self.textAttr.SetFontStyle(wx.FONTSTYLE_NORMAL)
      if fontUnderline != None:
         if fontUnderline:
            self.textAttr.SetFontUnderlined(True)
         else:
            self.textAttr.SetFontUnderlined(False)
      self.rtc.SetDefaultStyle(self.textAttr)

    def DecodeAttributeValues(self, crfName, className, attributeName, attributeValues, separator=', '):

        dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')

        textList = []
        if dataType == 'codingset':
            codingSetName = None
            codingSetFullName = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'codingSet')
            if codingSetFullName:
                codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
            decodedAttributeValues = []
            if codingSetName != None:
                for value in attributeValues:
                    valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(value)
                    decodedValue = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'value')
                    decodedAttributeValues.append(self.mainLogic.translateString(decodedValue))
                textList = decodedAttributeValues
            else:
                textList = [unicode(value).strip() for value in attributeValues]
        elif dataType == 'date':
            decodedAttributeValues = []
            for value in attributeValues:
                splitdate = value.split('-')
                decodedAttributeValues.append('%s/%s/%s' % (splitdate[2], splitdate[1], splitdate[0]))
            textList = decodedAttributeValues
        else:
            textList = [unicode(value).strip() for value in attributeValues]

        if not separator:
            return textList

        text = separator.join(textList)
        return text

    def GetImageList(self):
        bkpPosition = self.rtc.GetInsertionPoint()
        self.rtc.MoveEnd()
        position = self.rtc.GetInsertionPoint()
        imageList = []
        starts = []
        for i in range(position):
            leafObject = self.rtc.GetBuffer().GetLeafObjectAtPosition(i)
            if type(leafObject) == rt.RichTextImage:
                start = leafObject.GetRange()[0]
                if start in starts:
                    continue
                starts.append(start)
                imageList.append({'rtposition':start,'position':start})
        self.rtc.SetInsertionPoint(bkpPosition)
        return imageList
 
    def RenderText(self):
        self.tagList = []

        self.rtcFeedbackEnabled = False
        self.rtc.Clear()
        self.rtc.GetBuffer().Copy(self.ortc.GetBuffer())

        otext = self.GetTextWithImagePlaceholders(self.ortc.GetValue())
        rawstr = r"""\|[\w.]*\|"""
        expandedre = re.compile(rawstr, re.IGNORECASE)

        vars = expandedre.finditer(otext)
        for var in vars:
            tag = var.group()
            name = tag[1:-1]
            pieces = name.split('.')
            npieces = len(pieces)
            text = ""
            if self.editModel:
                if npieces == 3:
                    crfName = pieces[0]
                    className = pieces[1]
                    attributeName = pieces[2]
                    label = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'label')
                    if not label:
                        label = self.mainLogic.crfData.getPropertyForClass(crfName,className,'label')
                    if label:
                        label = self.mainLogic.translateString(label)
                    else:
                        label = tag[1:-1]
                    text = label.strip(': ')
                elif npieces == 2:
                    crfName = pieces[0]
                    itemName = pieces[1]
                    label = self.mainLogic.getFormatLabel(crfName,itemName)
                    if not label and self.mainLogic.isFormatForClass(crfName,itemName):
                        label = self.mainLogic.crfData.getPropertyForClass(crfName,itemName,'label')
                    if label:
                        label = self.mainLogic.translateString(label)
                    else:
                        label = tag[1:-1]
                    text = label.strip(': ')
                else:
                    #raise Exception('Error: invalid name %s',name)
                    print 'Error: invalid name %s' , name
                    text = name
            else:
                if npieces == 3:
                    crfName = pieces[0]
                    className = pieces[1]
                    attributeName = pieces[2]
                    dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
                    if dataType == 'object':
                        objectCodes = self.mainLogic.dataSession.getAttributeValuesForClass(crfName,className,attributeName)
                        textList = []
                        for objectCode in objectCodes:
                            classInfo = self.mainLogic.dataSession.getClassInfoForObjectCode(objectCode)
                            if not classInfo:
                                continue
                            crfName = classInfo['crfName']
                            className = classInfo['className']
                            classInstanceNumber = classInfo['classInstanceNumber']
                            classFormat = self.mainLogic.getFormatExpression(crfName,className)
                            attributeVars = expandedre.finditer(classFormat)
                            for attributeVar in attributeVars:
                                attributeTag = attributeVar.group()
                                attributeName = attributeTag[1:-1]
                                attributeValues = self.mainLogic.dataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
                                attributeText = self.DecodeAttributeValues(crfName,className,attributeName,attributeValues)
                                classFormat = classFormat.replace(attributeTag,repr(attributeText))
                            result = None
                            try:
                                exec(classFormat)
                            except BaseException, e:
                                print e
                                pass
                            if result:
                                textList.append(result)
                        text = '\n'.join(textList)
                    else:
                        attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(crfName,className,attributeName)
                        attributeText = self.DecodeAttributeValues(crfName,className,attributeName,attributeValues)
                        text = attributeText
                elif npieces == 2:
                    crfName = pieces[0]
                    itemName = pieces[1]
                    if self.mainLogic.isFormatForClass(crfName,itemName):
                        className = itemName
                        classInstanceNumbers = self.mainLogic.dataSession.getInstanceNumbersForClass(crfName,className)
                        textList = []
                        for classInstanceNumber in classInstanceNumbers:
                            classFormat = self.mainLogic.getFormatExpression(crfName,className)
                            classFormatLabel = self.mainLogic.getFormatLabel(crfName,className)
                            attributeVars = expandedre.finditer(classFormat)
                            for attributeVar in attributeVars:
                                attributeTag = attributeVar.group()
                                attributeName = attributeTag[1:-1]
                                attributeValues = self.mainLogic.dataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName)
                                attributeText = self.DecodeAttributeValues(crfName,className,attributeName,attributeValues)
                                classFormat = classFormat.replace(attributeTag,repr(attributeText))
                            result = None
                            try:
                                exec(classFormat)
                            except BaseException, e:
                                print e
                                pass
                            if result:
                                textList.append(result)
                        text = '\n'.join(textList)
                    else:
                        itemFormat = self.mainLogic.getFormatExpression(crfName,itemName)
                        textList = []
                        if itemFormat:
                            result = self.mainLogic.evaluator.eval(itemFormat,noCache=True)
                            if result:
                                textList.append(result)
                        text = '\n'.join(textList)
                else:
                    #raise Exception('Error: invalid name %s' % name)
                    print 'Error: invalid name %s' % name
                    text = name

            if not text:
                from mainlogic import _
                text = _('NA')

            self.ReplaceTag(tag,text)
        self.rtcFeedbackEnabled = True

    def GetTextWithImagePlaceholders(self, text):
        textWithPlaceholders = text[:]
        imageList = self.GetImageList()
        rtpositions = [el['rtposition'] for el in imageList]
        rtpositions.sort()
        for rtposition in rtpositions:
            textWithPlaceholders = textWithPlaceholders[:rtposition] + '@' + textWithPlaceholders[rtposition:]
        return textWithPlaceholders

    def ReplaceTag(self, tag, text):
        bkpPosition = self.rtc.GetInsertionPoint()
        counter = 0
        while True:
            begin = self.GetTextWithImagePlaceholders(self.rtc.GetValue()).find(tag)
            if begin == -1:
                break
            counter += 1
            obegin = -1
            oend = -1
            otext = self.GetTextWithImagePlaceholders(self.ortc.GetValue())
            for i in range(counter):
                obegin = otext.find(tag)
                if obegin+len(tag) < len(otext):
                    otext = otext[:obegin] + ' '*len(tag) + otext[obegin+len(tag)]
                else:
                    otext = otext[:obegin] + ' '*len(tag)
            end = begin + len(tag)
            oend = obegin + len(tag)
            self.rtc.BeginSuppressUndo()
            self.rtc.Remove(begin+1,end)
            self.rtc.SetInsertionPoint(begin+1)
            self.rtc.BeginTextColour('blue')
            try:
                text = text.decode('utf-8')
            except:
                pass
            self.rtc.WriteText(text)
            self.rtc.EndTextColour()
            self.rtc.Remove(begin,begin+1)
            self.rtc.EndSuppressUndo()
            self.tagList.append({'tag':tag, 'range':[obegin,oend], 'rtrange':[begin,begin+len(text)]})
        self.rtc.SetInsertionPoint(bkpPosition)
 
    def OnKeyDown(self,event):
        self.Modified()
        if event.GetKeyCode() not in [wx.WXK_DELETE, wx.WXK_BACK]:
            event.Skip()
            return
        position = self.rtc.GetInsertionPoint()
        selection = self.rtc.GetSelection()
        for entry in self.tagList:
            rtrange = entry['rtrange']
            if (rtrange[0] <= position and rtrange[1] >= position) or (rtrange[0] >= selection[0] and rtrange[0] <= selection[1]) or (rtrange[1] >= selection[0] and rtrange[1] <= selection[1]):
                return
        event.Skip()

    def OnEditEvent(self,event):
        self.Modified()
        if not self.rtcFeedbackEnabled:
            event.Skip()
            return
        position = self.rtc.GetInsertionPoint()
        selection = self.rtc.GetSelection()
        for entry in self.tagList:
            rtrange = entry['rtrange']
            if selection[0] == selection[1] and selection[0] < 0 and position == rtrange[1] and event.GetKeyCode() != wx.WXK_BACK:
                continue
            if (rtrange[0] <= position and rtrange[1] >= position) or (rtrange[0] >= selection[0] and rtrange[0] <= selection[1]) or (rtrange[1] >= selection[0] and rtrange[1] <= selection[1]):
            #TODO: in order to enable deleting whole tags, implement removing tags from the list in OnContentDeleted
            #if (rtrange[0] <= position and rtrange[1] >= position) or (rtrange[0] <= selection[0] and rtrange[0] >= selection[1]) or (rtrange[1] <= selection[0] and rtrange[1] >= selection[1]):
                return
        event.Skip()

    def OnContentInserted(self,event):
        self.Modified()
        if not self.rtcFeedbackEnabled:
            event.Skip()
            return
        addedRange = event.GetRange() 
        addedText = self.GetTextWithImagePlaceholders(self.rtc.GetValue())[addedRange[0]:addedRange[1]+1]

        if '@' in addedText:
            self.rtcFeedbackEnabled = False
            self.rtc.GetBuffer().DeleteRangeWithUndo(addedRange,self.rtc)
            self.rtcFeedbackEnabled = True
            event.Skip()
            return

        style = rt.TextAttrEx()
        self.rtc.GetStyle((addedRange[0]+addedRange[1])/2,style)
        style.SetTextColour('black')
        amount = addedRange[1] + 1 - addedRange[0]
        previousTags = 0
        for entry in self.tagList:
            if entry['rtrange'][0] <= addedRange[0] and entry['rtrange'][1] >= addedRange[0]:
                self.rtcFeedbackEnabled = False
                self.rtc.GetBuffer().DeleteRangeWithUndo(addedRange,self.rtc)
                self.rtcFeedbackEnabled = True
                event.Skip()
                return
            if entry['rtrange'][0] < addedRange[0]:
                previousTags += 1
                continue 
            entry['rtrange'][0] += amount
            entry['rtrange'][1] += amount
            entry['range'][0] += amount
            entry['range'][1] += amount
        shift = 0
        for i in range(previousTags):
            entry = self.tagList[i]
            shift += (entry['rtrange'][1] - entry['rtrange'][0]) - (entry['range'][1] - entry['range'][0])
        shiftedRange = (addedRange[0]-shift,addedRange[0]-shift+amount-1)
        if addedText and addedText != '@':
            self.ortc.GetBuffer().InsertTextWithUndo(shiftedRange[0],addedText,self.ortc)
        #self.rtc.SetStyleEx((addedRange[0],addedRange[1]+1),style,rt.RICHTEXT_SETSTYLE_CHARACTERS_ONLY)
        self.ortc.SetStyleEx((shiftedRange[0],shiftedRange[1]+1),style,rt.RICHTEXT_SETSTYLE_CHARACTERS_ONLY)
        #self.ortc.SetStyleEx((shiftedRange[0],shiftedRange[1]+1),style)

    def OnContentDeleted(self,event):
        self.Modified()
        if not self.rtcFeedbackEnabled:
            event.Skip()
            return
        deletedRange = event.GetRange() 
        amount = deletedRange[1] + 1 - deletedRange[0]
        previousTags = 0
        for entry in self.tagList:
            if entry['rtrange'][0] < deletedRange[0]:
                previousTags += 1
                continue 
            rtrange = entry['rtrange']
            if (rtrange[0] >= deletedRange[0] and rtrange[0] <= deletedRange[1]) or (rtrange[1] >= deletedRange[0] and rtrange[1] <= deletedRange[1]):
                self.RenderText()
                self.rtc.SetInsertionPoint(deletedRange[0])
                event.Skip()
                return
            entry['rtrange'][0] -= amount
            entry['rtrange'][1] -= amount
            entry['range'][0] -= amount
            entry['range'][1] -= amount
        #for entry in self.getImageList():
        #    if entry['rtposition'] < deletedRange[0]:
        #        continue
        #    entry['rtposition'] -= amount
        #    entry['position'] -= amount
        shift = 0
        for i in range(previousTags):
            entry = self.tagList[i]
            shift += (entry['rtrange'][1] - entry['rtrange'][0]) - (entry['range'][1] - entry['range'][0])
        self.ortc.GetBuffer().DeleteRangeWithUndo((deletedRange[0]-shift,deletedRange[1]-shift),self.ortc)

    def OnStyleChanged(self,event):
        self.Modified()
        if not self.rtcFeedbackEnabled:
            event.Skip()
            return
        changedRange = event.GetRange() 
        previousTags = [0, 0]
        for entry in self.tagList:
            if entry['rtrange'][0] < changedRange[0]:
                previousTags[0] += 1
            if entry['rtrange'][0] < changedRange[1]:
                previousTags[1] += 1
        shiftedRange = [changedRange[0], changedRange[1]]
        shift = 0
        for i in range(previousTags[0]):
            entry = self.tagList[i]
            shiftedRange[0] -= (entry['rtrange'][1] - entry['rtrange'][0]) - (entry['range'][1] - entry['range'][0])
        for i in range(previousTags[1]):
            entry = self.tagList[i]
            shiftedRange[1] -= (entry['rtrange'][1] - entry['rtrange'][0]) - (entry['range'][1] - entry['range'][0])
        style = rt.TextAttrEx()
        self.rtc.GetStyle((changedRange[0]+changedRange[1])/2,style)
        #flags = rt.RICHTEXT_SETSTYLE_NONE
        if changedRange[1] - changedRange[0] > 1:
            if self.styleChangeMode == 'paragraph':
                flags = rt.RICHTEXT_SETSTYLE_WITH_UNDO|rt.RICHTEXT_SETSTYLE_PARAGRAPHS_ONLY
            else:
                flags = rt.RICHTEXT_SETSTYLE_WITH_UNDO|rt.RICHTEXT_SETSTYLE_CHARACTERS_ONLY
            self.ortc.SetStyleEx((shiftedRange[0],shiftedRange[1]+1),style,flags)
        else:
            if self.styleChangeMode == 'paragraph':
                flags = rt.RICHTEXT_SETSTYLE_WITH_UNDO|rt.RICHTEXT_SETSTYLE_PARAGRAPHS_ONLY
                self.ortc.SetStyleEx((shiftedRange[0],shiftedRange[1]+1),style,flags)
            else:
                self.ortc.SetStyleEx((shiftedRange[0],shiftedRange[1]+1),style)
        self.styleChangeMode = 'character'
 
    def OnInsertVariable(self, evt):
        self.Modified()
        self.variablesDialog = wx.Dialog(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        formats = self.mainLogic.getAllFormats()
        formatLabels = [formats[el]['label'] for el in formats]
        choices = formatLabels
        self.variablesListBox = wx.ListBox(self.variablesDialog,-1,style=wx.LB_SINGLE|wx.LB_SORT,choices=choices)
        sizer.Add(self.variablesListBox,1,wx.EXPAND|wx.ALL,10)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        insertButton = wx.Button(self.variablesDialog,wx.ID_OK)
        insertButton.Bind(wx.EVT_BUTTON,self.OnListBoxOk)
        buttonSizer.Add(insertButton,0,wx.ALIGN_RIGHT|wx.ALL,5)

        cancelButton = wx.Button(self.variablesDialog,wx.ID_CANCEL)
        cancelButton.Bind(wx.EVT_BUTTON,self.OnListBoxCancel)
        buttonSizer.Add(cancelButton,0,wx.ALIGN_RIGHT|wx.ALL,5)
        sizer.Add(buttonSizer,0,wx.ALIGN_RIGHT|wx.ALL,5) 

        self.variablesDialog.SetSizer(sizer)
        self.variablesDialog.Center()
        self.variablesDialog.ShowModal()

    def OnListBoxOk(self, evt):
        selection = self.variablesListBox.GetStringSelection()
        formats = self.mainLogic.getAllFormats()
        itemFullNames = [el for el in formats if formats[el]['label'] == selection]
        if itemFullNames:
            #TODO: check that there is exactly one
            itemFullName = itemFullNames[0]
            position = self.rtc.GetInsertionPoint()
            self.rtc.GetBuffer().InsertTextWithUndo(position,'|%s|' % itemFullName,self.rtc)
            self.RenderText()
            self.rtc.SetInsertionPoint(position)
        self.variablesDialog.Destroy()
        self.variablesDialog = None

    def OnListBoxCancel(self, evt):
        self.variablesDialog.Destroy()
        self.variablesDialog = None

    def OnRemoveVariable(self, evt):
        self.Modified()
        position = self.rtc.GetInsertionPoint()
        previousTags = 0
        indexToRemove = -1
        for i, entry in enumerate(self.tagList):
            if entry['rtrange'][0] <= position and entry['rtrange'][1] >= position:
                indexToRemove = i
                break
        if indexToRemove == -1:
            return
        entry = self.tagList.pop(indexToRemove)
        self.rtcFeedbackEnabled = False
        self.ortc.GetBuffer().DeleteRangeWithUndo((entry['range'][0],entry['range'][1]-1),self.ortc)
        self.rtcFeedbackEnabled = True
        self.RenderText()
        self.rtc.SetInsertionPoint(entry['rtrange'][0])

    def OnAddImage(self, evt):
        self.Modified()
        from mainlogic import _
        imageFileName = wx.FileSelector(_("Choose image file"),wildcard="PNG files (*.png)|*.png|BMP files (*.bmp)|*.bmp|GIF files (*.gif)|*.gif|JPEG Files (*.jpeg)|*.jpeg|JPG Files (*.jpg)|*.jpg",default_extension='png',flags=wx.FD_OPEN)
        if not imageFileName:
            return
        position = self.rtc.GetInsertionPoint()
        previousTags = 0
        for entry in self.tagList:
            if entry['rtrange'][0] < position:
                previousTags += 1
                continue 
        shift = 0
        for i in range(previousTags):
            entry = self.tagList[i]
            shift += (entry['rtrange'][1] - entry['rtrange'][0]) - (entry['range'][1] - entry['range'][0])
        oposition = position - shift
        self.ortc.SetInsertionPoint(oposition)
        style = rt.TextAttrEx()
        self.rtc.GetStyle(position,style)
        self.ortc.WriteImageFile(imageFileName,wx.BITMAP_TYPE_ANY)
        self.ortc.SetStyleEx((oposition-1,oposition),style)
        self.RenderText()
 
    def OnURL(self, evt):
        wx.MessageBox(evt.GetString(), "URL Clicked")

    def LoadFile(self):
        self.ortc.Clear()
        self.ortc.LoadFile(self.filename,rt.RICHTEXT_TYPE_XML)
        self.RenderText()
        self.Modified(False)

    def OnReset(self, evt):
        from mainlogic import _
        dlg = wx.MessageDialog(None, 
             _("Do you really want to reset the document and discard your edits?"),
             _("Confirm reset"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        dlg.Center()
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            return
        self.ortc.SaveFile(self.filename,rt.RICHTEXT_TYPE_XML)
        self.resetCallback()
        self.LoadFile()
        self.Modified(False)

    def OnUndoReset(self, evt):
        from mainlogic import _
        dlg = wx.MessageDialog(None, 
             _("Do you really want to revert the document to your previous version?"),
             _("Confirm reset"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        dlg.Center()
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            return
        self.undoResetCallback()
        self.LoadFile()
        self.Modified(False)

    def OnFileSave(self, evt):
        self.ortc.SaveFile(self.filename,rt.RICHTEXT_TYPE_XML)

    def OnFileExit(self, evt):
        from mainlogic import _
        if self.modified:
            dlg = wx.MessageDialog(None, 
                 _("Do you really want to quit? All unsaved changes will be lost"),
                 _("Confirm quit"), wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            dlg.Center()
            result = dlg.ShowModal()
            if result != wx.ID_OK:
                return
        self.Close(True)
      
    def OnBold(self, evt):
        self.rtc.ApplyBoldToSelection()
        
    def OnItalic(self, evt): 
        self.rtc.ApplyItalicToSelection()
        
    def OnUnderline(self, evt):
        self.rtc.ApplyUnderlineToSelection()
        
    def OnAlignLeft(self, evt):
        self.styleChangeMode = 'paragraph'
        self.rtc.ApplyAlignmentToSelection(rt.TEXT_ALIGNMENT_LEFT)
        
    def OnAlignRight(self, evt):
        self.styleChangeMode = 'paragraph'
        self.rtc.ApplyAlignmentToSelection(rt.TEXT_ALIGNMENT_RIGHT)
        
    def OnAlignCenter(self, evt):
        self.styleChangeMode = 'paragraph'
        self.rtc.ApplyAlignmentToSelection(rt.TEXT_ALIGNMENT_CENTRE)
        
    def OnIndentMore(self, evt):
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_LEFT_INDENT)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

            attr.SetLeftIndent(attr.GetLeftIndent() + 100)
            attr.SetFlags(rt.TEXT_ATTR_LEFT_INDENT)
            self.rtc.SetStyle(r, attr)
       
    def OnIndentLess(self, evt):
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_LEFT_INDENT)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

        if attr.GetLeftIndent() >= 100:
            attr.SetLeftIndent(attr.GetLeftIndent() - 100)
            attr.SetFlags(rt.TEXT_ATTR_LEFT_INDENT)
            self.rtc.SetStyle(r, attr)
        
    def OnParagraphSpacingMore(self, evt):
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_PARA_SPACING_AFTER)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

            attr.SetParagraphSpacingAfter(attr.GetParagraphSpacingAfter() + 20);
            attr.SetFlags(rt.TEXT_ATTR_PARA_SPACING_AFTER)
            self.rtc.SetStyle(r, attr)
        
    def OnParagraphSpacingLess(self, evt):
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_PARA_SPACING_AFTER)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

            if attr.GetParagraphSpacingAfter() >= 20:
                attr.SetParagraphSpacingAfter(attr.GetParagraphSpacingAfter() - 20);
                attr.SetFlags(rt.TEXT_ATTR_PARA_SPACING_AFTER)
                self.rtc.SetStyle(r, attr)
        
    def OnLineSpacingSingle(self, evt): 
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_LINE_SPACING)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

            attr.SetFlags(rt.TEXT_ATTR_LINE_SPACING)
            attr.SetLineSpacing(10)
            self.rtc.SetStyle(r, attr)
                
    def OnLineSpacingHalf(self, evt):
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_LINE_SPACING)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

            attr.SetFlags(rt.TEXT_ATTR_LINE_SPACING)
            attr.SetLineSpacing(15)
            self.rtc.SetStyle(r, attr)

    def OnLineSpacingDouble(self, evt):
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_LINE_SPACING)
        ip = self.rtc.GetInsertionPoint()
        if self.rtc.GetStyle(ip, attr):
            r = rt.RichTextRange(ip, ip)
            if self.rtc.HasSelection():
                r = self.rtc.GetSelectionRange()

            attr.SetFlags(rt.TEXT_ATTR_LINE_SPACING)
            attr.SetLineSpacing(20)
            self.rtc.SetStyle(r, attr)

    def OnFont(self, evt):
        if not self.rtc.HasSelection():
            return

        r = self.rtc.GetSelectionRange()
        fontData = wx.FontData()
        fontData.EnableEffects(False)
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_FONT)
        if self.rtc.GetStyle(self.rtc.GetInsertionPoint(), attr):
            fontData.SetInitialFont(attr.GetFont())

        dlg = wx.FontDialog(self, fontData)
        if dlg.ShowModal() == wx.ID_OK:
            fontData = dlg.GetFontData()
            font = fontData.GetChosenFont()
            if font:
                attr.SetFlags(rt.TEXT_ATTR_FONT)
                attr.SetFont(font)
                if r[0] < 0 and r[1] < 0:
                    self.styleChangeMode = 'paragraph'
                    i = self.rtc.GetInsertionPoint()
                    self.rtc.SetStyle((i,i+1),attr)
                else:
                    self.rtc.SetStyle(r, attr)
        dlg.Destroy()

    def OnColour(self, evt):
        colourData = wx.ColourData()
        attr = rt.TextAttrEx()
        attr.SetFlags(rt.TEXT_ATTR_TEXT_COLOUR)
        if self.rtc.GetStyle(self.rtc.GetInsertionPoint(), attr):
            colourData.SetColour(attr.GetTextColour())

        dlg = wx.ColourDialog(self, colourData)
        if dlg.ShowModal() == wx.ID_OK:
            colourData = dlg.GetColourData()
            colour = colourData.GetColour()
            if colour:
                if not self.rtc.HasSelection():
                    self.rtc.BeginTextColour(colour)
                else:
                    r = self.rtc.GetSelectionRange()
                    attr.SetFlags(rt.TEXT_ATTR_TEXT_COLOUR)
                    attr.SetTextColour(colour)
                    self.rtc.SetStyle(r, attr)
        dlg.Destroy()

    def OnUpdateBold(self, evt):
        evt.Check(self.rtc.IsSelectionBold())
    
    def OnUpdateItalic(self, evt): 
        evt.Check(self.rtc.IsSelectionItalics())
    
    def OnUpdateUnderline(self, evt): 
        evt.Check(self.rtc.IsSelectionUnderlined())
    
    def OnUpdateAlignLeft(self, evt):
        evt.Check(self.rtc.IsSelectionAligned(rt.TEXT_ALIGNMENT_LEFT))
        
    def OnUpdateAlignCenter(self, evt):
        evt.Check(self.rtc.IsSelectionAligned(rt.TEXT_ALIGNMENT_CENTRE))
        
    def OnUpdateAlignRight(self, evt):
        evt.Check(self.rtc.IsSelectionAligned(rt.TEXT_ALIGNMENT_RIGHT))
 
    def OnPrintPreview(self, evt):
        rtPrinting = rt.RichTextPrinting(parentWindow=self)
        rtPrinting.GetPageSetupData().SetMarginTopLeft((10.0,10.0))
        rtPrinting.GetPageSetupData().SetMarginBottomRight((10.0,10.0))
        rtPrinting.PreviewBuffer(self.rtc.GetBuffer())
   
    def OnPrint(self, evt):
        rtPrinting = rt.RichTextPrinting(parentWindow=self)
        rtPrinting.GetPageSetupData().SetMarginTopLeft((10.0,10.0))
        rtPrinting.GetPageSetupData().SetMarginBottomRight((10.0,10.0))
        rtPrinting.PrintBuffer(self.rtc.GetBuffer())

    def ForwardEvent(self, evt):
        # The RichTextCtrl can handle menu and update events for undo,
        # redo, cut, copy, paste, delete, and select all, so just
        # forward the event to it.
        self.rtc.ProcessEvent(evt)

    def MakeMenuBar(self):
        def doBind(item, handler, updateUI=None):
            self.Bind(wx.EVT_MENU, handler, item)
            if updateUI is not None:
                self.Bind(wx.EVT_UPDATE_UI, updateUI, item)
            
        fileMenu = wx.Menu()
        doBind( fileMenu.Append(-1, "&Save\tCtrl+S", "Save letter"),
                self.OnFileSave )
        fileMenu.AppendSeparator()
        doBind( fileMenu.Append(-1, "&Print...", "Print letter"),
                self.OnPrint)
        fileMenu.AppendSeparator()
        doBind( fileMenu.Append(-1, "&Close\tCtrl+Q", "Close editor"),
                self.OnFileExit )
        
        editMenu = wx.Menu()
        doBind( editMenu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z"),
                self.ForwardEvent, self.ForwardEvent)
        doBind( editMenu.Append(wx.ID_REDO, "&Redo\tCtrl+Y"),
                self.ForwardEvent, self.ForwardEvent )
        editMenu.AppendSeparator()
        doBind( editMenu.Append(wx.ID_CUT, "Cu&t\tCtrl+X"),
                self.ForwardEvent, self.ForwardEvent )
        doBind( editMenu.Append(wx.ID_COPY, "&Copy\tCtrl+C"),
                self.ForwardEvent, self.ForwardEvent)
        doBind( editMenu.Append(wx.ID_PASTE, "&Paste\tCtrl+V"),
                self.ForwardEvent, self.ForwardEvent)
        doBind( editMenu.Append(wx.ID_CLEAR, "&Delete\tDel"),
                self.ForwardEvent, self.ForwardEvent)
        editMenu.AppendSeparator()
        doBind( editMenu.Append(wx.ID_SELECTALL, "Select A&ll\tCtrl+A"),
                self.ForwardEvent, self.ForwardEvent )
        
        #doBind( editMenu.AppendSeparator(),  )
        #doBind( editMenu.Append(-1, "&Find...\tCtrl+F"),  )
        #doBind( editMenu.Append(-1, "&Replace...\tCtrl+R"),  )

        formatMenu = wx.Menu()
        doBind( formatMenu.AppendCheckItem(-1, "&Bold\tCtrl+B"),
                self.OnBold, self.OnUpdateBold)
        doBind( formatMenu.AppendCheckItem(-1, "&Italic\tCtrl+I"),
                self.OnItalic, self.OnUpdateItalic)
        doBind( formatMenu.AppendCheckItem(-1, "&Underline\tCtrl+U"),
                self.OnUnderline, self.OnUpdateUnderline)
        formatMenu.AppendSeparator()
        doBind( formatMenu.AppendCheckItem(-1, "L&eft Align"),
                self.OnAlignLeft, self.OnUpdateAlignLeft)
        doBind( formatMenu.AppendCheckItem(-1, "&Centre"),
                self.OnAlignCenter, self.OnUpdateAlignCenter)
        doBind( formatMenu.AppendCheckItem(-1, "&Right Align"),
                self.OnAlignRight, self.OnUpdateAlignRight)
        formatMenu.AppendSeparator()
        doBind( formatMenu.Append(-1, "Indent &More"), self.OnIndentMore)
        doBind( formatMenu.Append(-1, "Indent &Less"), self.OnIndentLess)
        formatMenu.AppendSeparator()
        doBind( formatMenu.Append(-1, "Increase Paragraph &Spacing"), self.OnParagraphSpacingMore)
        doBind( formatMenu.Append(-1, "Decrease &Paragraph Spacing"), self.OnParagraphSpacingLess)
        formatMenu.AppendSeparator()
        doBind( formatMenu.Append(-1, "Normal Line Spacing"), self.OnLineSpacingSingle)
        doBind( formatMenu.Append(-1, "1.5 Line Spacing"), self.OnLineSpacingHalf)
        doBind( formatMenu.Append(-1, "Double Line Spacing"), self.OnLineSpacingDouble)
        formatMenu.AppendSeparator()
        doBind( formatMenu.Append(-1, "&Font..."), self.OnFont)
        
        mb = wx.MenuBar()
        mb.Append(fileMenu, "&File")
        mb.Append(editMenu, "&Edit")
        mb.Append(formatMenu, "F&ormat")
        self.SetMenuBar(mb)

    def MakeToolBar(self):
        def doBind(item, handler, updateUI=None):
            self.Bind(wx.EVT_TOOL, handler, item)
            if updateUI is not None:
                self.Bind(wx.EVT_UPDATE_UI, updateUI, item)
        
        tbar = self.CreateToolBar()
        #doBind( tbar.AddTool(-1, images._rt_open.GetBitmap(),
        #                    shortHelpString="Open"), self.OnFileOpen)
        doBind( tbar.AddTool(-1, images._rt_save.GetBitmap(),
                            shortHelpString="Save"), self.OnFileSave)
        tbar.AddSeparator()
        doBind( tbar.AddTool(wx.ID_CUT, images._rt_cut.GetBitmap(),
                            shortHelpString="Cut"), self.ForwardEvent, self.ForwardEvent)
        doBind( tbar.AddTool(wx.ID_COPY, images._rt_copy.GetBitmap(),
                            shortHelpString="Copy"), self.ForwardEvent, self.ForwardEvent)
        doBind( tbar.AddTool(wx.ID_PASTE, images._rt_paste.GetBitmap(),
                            shortHelpString="Paste"), self.ForwardEvent, self.ForwardEvent)
        tbar.AddSeparator()
        doBind( tbar.AddTool(wx.ID_UNDO, images._rt_undo.GetBitmap(),
                            shortHelpString="Undo"), self.ForwardEvent, self.ForwardEvent)
        doBind( tbar.AddTool(wx.ID_REDO, images._rt_redo.GetBitmap(),
                            shortHelpString="Redo"), self.ForwardEvent, self.ForwardEvent)
        tbar.AddSeparator()
        doBind( tbar.AddTool(-1, images._rt_bold.GetBitmap(), isToggle=True,
                            shortHelpString="Bold"), self.OnBold, self.OnUpdateBold)
        doBind( tbar.AddTool(-1, images._rt_italic.GetBitmap(), isToggle=True,
                            shortHelpString="Italic"), self.OnItalic, self.OnUpdateItalic)
        doBind( tbar.AddTool(-1, images._rt_underline.GetBitmap(), isToggle=True,
                            shortHelpString="Underline"), self.OnUnderline, self.OnUpdateUnderline)
        tbar.AddSeparator()
        doBind( tbar.AddTool(-1, images._rt_alignleft.GetBitmap(), isToggle=True,
                            shortHelpString="Align Left"), self.OnAlignLeft, self.OnUpdateAlignLeft)
        doBind( tbar.AddTool(-1, images._rt_centre.GetBitmap(), isToggle=True,
                            shortHelpString="Center"), self.OnAlignCenter, self.OnUpdateAlignCenter)
        doBind( tbar.AddTool(-1, images._rt_alignright.GetBitmap(), isToggle=True,
                            shortHelpString="Align Right"), self.OnAlignRight, self.OnUpdateAlignRight)
        tbar.AddSeparator()
        doBind( tbar.AddTool(-1, images._rt_indentless.GetBitmap(),
                            shortHelpString="Indent Less"), self.OnIndentLess)
        doBind( tbar.AddTool(-1, images._rt_indentmore.GetBitmap(),
                            shortHelpString="Indent More"), self.OnIndentMore)
        tbar.AddSeparator()
        doBind( tbar.AddTool(-1, images._rt_font.GetBitmap(),
                            shortHelpString="Font"), self.OnFont)
        doBind( tbar.AddTool(-1, images._rt_colour.GetBitmap(),
                            shortHelpString="Font Colour"), self.OnColour)

        tbar.Realize()

#def AddRTCHandlers():
#
#    if rt.RichTextBuffer.FindHandlerByType(rt.RICHTEXT_TYPE_XML) is not None:
#        return
#   
#    rt.RichTextBuffer.AddHandler(rt.RichTextXMLHandler())



if __name__=='__main__':

    app = wx.App(False)

    #AddRTCHandlers()

    frame = PSDischargeLetter(None)
    frame.SetSize((1200,800))
    frame.Center()
    frame.Show(True)
    app.MainLoop()


