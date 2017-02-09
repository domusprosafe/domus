# -*- coding: utf-8 -*-
#from profilehooks import profile
import wx
import wx.lib.masked as masked
import wx.lib.expando as expando
import string
import re
import validators
import copy
import wx.lib.scrolledpanel as scrolled
import textwrap
import psconstants as psc
from psguiconstants import BACKGROUND_TEXTBOX_NOTFILLED
from psguiconstants import GUI_WINDOW_VARIANT
from psguiconstants import ENFORCE_SYSTEM_FONT
from psguiconstants import BACKGROUND_COLOUR
from psCalendar import CalendarTextbox
from psstartwidget import myFrame
from psHour import HourTextbox
from psHourtimer import TimerTextbox
from mlcheckbox import MLCheckBox
from mlradiobutton import MLRadioButton
from pschecklistbox import PSCheckListBox
from psgridsizer import PSGridSizer
from psgridsizer import PSFlexGridSizer
from pshistorywidget import PSHistoryWidget
from psprocedurenotebutton import psProcedureNoteButton
import psevaluator
import os
from pspopinfo import popInfoDialog
from psimagezoom import imageZoomDialog
from pslogging import PsLogger


class ItemGui(object):

    def __init__(self,mainLogic,crfName,xmlFragment,callbacksDict):

        self.mainLogic = mainLogic

        self.crfName = crfName
        self.xmlFragment = xmlFragment
        self.callbacksDict = callbacksDict

        self.timeStampAttributeFullName = None
        self.timeStamp = None

        self.sizersFromRoot = None

        #self.tooltips = dict()
        self.labelWidgets = []
        self.readonlyWidgets = []
        self.pagelinkWidgets = dict()
        self.buttonWidgets = dict()
        #self.addbuttonWidgets = dict()
        self.addselectWidgets = dict()
        self.addselectChoices = dict()
        self.addselectButtons = dict()
        self.dynnumberWidgets = dict()
        self.dialogWidgets = []
        self.cursorWidgets = dict()

        self.parent = None
        self.panel = None
        self.targetSizer = None
        self.sizersFromRoot = []
        self.classesWithNoCodingSet = []

        eventNames = [el for el in dir(wx) if el.startswith('EVT')]
        self.eventTypeIdToName = dict()
        for eventName in eventNames:
            exec('if type(wx.%s) == wx._core.PyEventBinder: self.eventTypeIdToName[wx.%s.typeId] = eventName'%(eventName, eventName))

    def setTimeStamp(self,timeStampAttributeFullName,timeStamp):
        self.timeStampAttributeFullName = timeStampAttributeFullName
        self.timeStamp = timeStamp

    def buildGui(self,parent,parentSizer):
        self.parent = parent
        self.parentSizer = parentSizer

        #containerPanel = wx.Panel(self.parent,-1)
        #self.parentSizer.Add(containerPanel,flag=wx.EXPAND)
        #import wx.lib.scrolledpanel as scrolled
        #containerSizer = wx.BoxSizer(wx.VERTICAL)
        #containerPanel.SetSizer(containerSizer)
        #containerPanel.SetAutoLayout(1)
        #self.panel = scrolled.ScrolledPanel(containerPanel,-1)
        #self.panel.SetAutoLayout(1)
        #containerSizer.Add(self.panel)

        self.panel = wx.Panel(self.parent,-1)
        self.targetSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.targetSizer)
        self.panel.SetAutoLayout(1)

        self.parentSizer.Add(self.panel,flag=wx.EXPAND)

        xmlElement = self.xmlFragment

        #self.expandInterface(xmlElement)
        self.sizersFromRoot = [self.targetSizer]

        self.iterate(xmlElement)

        #self.panel.SetupScrolling(scrollToTop=False)
        self.updateGui()

    def composeTooltip(self, title, message):
        infoText = "%s\n---\n%s" % (title,message)
        return infoText

    def createTooltip(self, widget, title, message):
        infoText = self.composeTooltip(title,message)
        widget.infoText = infoText

    def iterate(self, item):

        if item.tag in ('row','column'):

            try: 
                n = int(item.get('n'))
            except: 
                n = 1

            try: 
                maxcolitems = int(item.get('maxcolitems'))
            except: 
                maxcolitems = 0

            type = item.get('type')
            if type in (None,'Flex'):
                sizerClass = PSFlexGridSizer
            elif type == 'Grid':
                sizerClass = PSGridSizer

            if item.tag == 'row':
                sizer = sizerClass(n,0,maxcolitems)
            elif item.tag == 'column':
                sizer = sizerClass(0,n,maxcolitems)

            try:
                width = int(item.get('width'))
            except:
                width = 200
            sizer.SetMinSize(wx.Size(width,-1))

            self.sizersFromRoot[-1].AddSpacer(3)
            self.sizersFromRoot[-1].Add(sizer)
            self.sizersFromRoot.append(sizer)

        elif item.tag == 'spacer':
            try: 
                size = int(item.get('size'))
            except: 
                size = 5
            self.sizersFromRoot[-1].AddSpacer(size)

        elif item.tag == 'box':
            label = item.get('label')
            if label:
                labelText = self.mainLogic.translateString(label)
            else:
                label = ''
                labelText = ''
            try:
                width = int(item.get('width'))
            except:
                width = -1
            widget = wx.StaticBox(self.panel, -1, labelText, name=label, size=wx.Size(width,-1))
            widget.SetWindowVariant(GUI_WINDOW_VARIANT)
            sizer = wx.StaticBoxSizer(widget, wx.VERTICAL)
            self.sizersFromRoot[-1].Add(sizer,flag=wx.EXPAND)
            self.sizersFromRoot.append(sizer)

        elif item.tag == 'comment':
            return

        else:
            tag = item.tag

            #if str(item.get('notexpand')) != 'None' or item.tag == 'addbutton':
            if False:
                flags = wx.ALL
            else:
                flags = wx.EXPAND | wx.ALL
            if str(item.get('center')) != 'None':
                flags |= wx.ALIGN_CENTER_HORIZONTAL
            try:
                border = int(item.get('border'))
            except:
                if item.tag == 'input' and item.get('type') in ('checkbox',):
                    border = 1
                else:
                    border = 2

            widgets = self.createWidgets(item, None) 
            if widgets:
                for widget in widgets:
                    widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    self.sizersFromRoot[-1].Add(widget,0,flags,border)

        for child in item.getchildren():
            self.iterate(child)

        if item.tag in ('row','column','box'):
            self.sizersFromRoot.pop()

    def createWidgets(self, element, lblname=None):
        """Istanzia il corretto widget a partire dal tag XML corrispondente"""
        #ifclass = self.className
        from mainlogic import _
        widgets = [] 
        if element.tag == 'label': 
            id = self.callbacksDict['getNewIdCallback']()
            #id = 0
            if lblname is None:
                labelname = "label" + str(id)
            else:
                labelname = lblname
            try: 
                width = int(element.get('width'))
            except: 
                #width = 200
                width = -1
           
            font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
            size = element.get('size')
            if size != None:
                font.SetPointSize(int(size))
            weight = element.get('weight')
            if weight != None:
                weight = str(weight).lower()
                if weight == 'bold':
                    font.SetWeight(wx.FONTWEIGHT_BOLD)
                if weight == 'light':
                    font.SetWeight(wx.FONTWEIGHT_LIGHT)
            style = element.get('style')
            if style != None:
                style = str(style).lower()
                if style == 'italic':
                    font.SetStyle(wx.FONTSTYLE_ITALIC)
                if style == 'slant':
                    font.SetStyle(wx.FONTSTYLE_SLANT)
            valuefrom = element.get('valuefrom')
            labelText = '' 
            tooltipTitle = ''
            tooltipText = ''
            if element.text:
                labelText = self.mainLogic.translateString(element.text)
            elif valuefrom != None:
                splitClassName = self.mainLogic.crfData.splitClassName(valuefrom)
                splitAttributeName = self.mainLogic.crfData.splitAttributeName(valuefrom)
                if splitClassName != None:
                    
                    labelValue = self.mainLogic.crfData.getPropertyForClass(splitClassName[0],splitClassName[1],'label')
                    if labelValue:
                        labelText = self.mainLogic.translateString(labelValue)
                        tooltipTitle = labelText
                        tooltipValue = self.mainLogic.crfData.getPropertyForClass(splitClassName[0],splitClassName[1],'toolTip')
                        if tooltipValue:
                            tooltipText = self.mainLogic.translateString(tooltipValue)
                elif splitAttributeName != None:
                    codingSetName = self.mainLogic.dataSession.getCodingSetNameForAttribute(splitAttributeName[0],splitAttributeName[1], splitAttributeName[2])
                    if codingSetName:
                        crfNameForCodingSet, codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetName)
                        if not self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(crfNameForCodingSet, codingSetName):
                            return
                    labelValue = self.mainLogic.crfData.getPropertyForAttribute(splitAttributeName[0],splitAttributeName[1],splitAttributeName[2],'label')
                    if labelValue:
                        labelText = self.mainLogic.translateString(labelValue)
                        tooltipTitle = labelText
                        tooltipValue = self.mainLogic.crfData.getPropertyForAttribute(splitAttributeName[0],splitAttributeName[1],splitAttributeName[2],'toolTip')
                        if tooltipValue:
                            tooltipText = self.mainLogic.translateString(tooltipValue)
 
            widget = wx.StaticText(self.panel, -1, labelText, name=labelname, style = wx.ST_NO_AUTORESIZE, size=wx.Size(width,-1))
           
            if not ENFORCE_SYSTEM_FONT:
                widget.SetFont(font)
            if element.get('setsize') != None and element.get('size') != None and int(element.get('setsize')) == 1:
                font.SetPointSize(int(element.get('size')))
                widget.SetFont(font)
            
            widget.Wrap(width)
                
            if tooltipTitle: 
                self.createTooltip(widget,tooltipTitle,tooltipText)

            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

            background = element.get('background')
            if background != None:
                background = str(background)
                widget.SetBackgroundColour(background)
            
            foreground = element.get('color')
            if foreground != None:
                foreground = str(foreground)
                widget.SetForegroundColour(foreground)
                            
            self.labelWidgets.append(widget)
            widgets.append(widget)
 
        elif element.tag == 'readonly':
            id = self.callbacksDict['getNewIdCallback']()
            #id = 0
            evaluate = element.get('evaluate')
            expression = element.get('expression')
            #labelname = "ro" + str(id) + evaluate.replace(' ','')
            labelname = "ro" + str(id)
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            norefresh = element.get('norefresh')
            basevalue = element.get('basevalue')
            if not basevalue:
                basevalue = ''
            visible = element.get('visible')
            targetinstance = element.get('targetinstance')
            tooltipfromvalue = element.get('tooltipfromvalue')
            if tooltipfromvalue != "0":
                tooltipfromvalue = True
            else:
                tooltipfromvalue = False

            if basevalue == 'None': 
                basevalue = ''
            linebreaks = element.get('linebreaks')
            if linebreaks == "0":
                linebreaks = False
            else:
                linebreaks = True

            tooltipTitle = ''
            tooltipText = ''
            if not tooltipfromvalue:
                splitClassName = self.mainLogic.crfData.splitClassName(evaluate)
                splitAttributeName = self.mainLogic.crfData.splitAttributeName(evaluate)
                if splitClassName != None:
                    titleValue = self.mainLogic.crfData.getPropertyForClass(splitClassName[0],splitClassName[1],'label')
                    if titleValue:
                        tooltipTitle = self.mainLogic.translateString(titleValue)
                    tooltipValue = self.mainLogic.crfData.getPropertyForClass(splitClassName[0],splitClassName[1],'toolTip')
                    if tooltipValue:
                        tooltipText = self.mainLogic.translateString(tooltipValue)
                elif splitAttributeName != None:
                    titleValue = self.mainLogic.crfData.getPropertyForAttribute(splitAttributeName[0],splitAttributeName[1],splitAttributeName[2],'label')
                    if titleValue:
                        tooltipTitle = self.mainLogic.translateString(titleValue)
                    tooltipValue = self.mainLogic.crfData.getPropertyForAttribute(splitAttributeName[0],splitAttributeName[1],splitAttributeName[2],'toolTip')
                    if tooltipValue:
                        tooltipText = self.mainLogic.translateString(tooltipValue)
                    else:
                        titleValue = self.mainLogic.crfData.getPropertyForClass(splitAttributeName[0],splitAttributeName[1],'label')
                        if titleValue:
                            tooltipTitle = self.mainLogic.translateString(titleValue)
                        tooltipValue = self.mainLogic.crfData.getPropertyForClass(splitAttributeName[0],splitAttributeName[1],'toolTip')
                        if tooltipValue:
                            tooltipText = self.mainLogic.translateString(tooltipValue)
                if not tooltipTitle and basevalue:
                    tooltipTitle = self.mainLogic.translateString(basevalue)
                if tooltipText == '':
                    tooltipValue = element.get('toolTip')
                    if tooltipValue:
                        tooltipText = self.mainLogic.translateString(tooltipValue)

            font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
            size = element.get('size')
            if size != None:
                font.SetPointSize(int(size))
            weight = element.get('weight')
            if weight != None:
                weight = str(weight).lower()
                if weight == 'bold':
                    font.SetWeight(wx.FONTWEIGHT_BOLD)
                if weight == 'light':
                    font.SetWeight(wx.FONTWEIGHT_LIGHT)
            style = element.get('style')
            if style != None:
                style = str(style).lower()
                if style == 'italic':
                    font.SetStyle(wx.FONTSTYLE_ITALIC)
                if style == 'slant':
                    font.SetStyle(wx.FONTSTYLE_SLANT)
            widget = wx.StaticText(self.panel, -1, '', size=wx.Size(width,-1), name=labelname)
            if not ENFORCE_SYSTEM_FONT:
                widget.SetFont(font)
            if element.get('setsize') != None and element.get('size') != None and int(element.get('setsize')) == 1:
                font.SetPointSize(int(element.get('size')))
                widget.SetFont(font)
            background = element.get('background')
            if background != None:
                background = str(background)
                widget.SetBackgroundColour(background)
            
            foreground = element.get('color')
            if foreground != None:
                foreground = str(foreground)
                widget.SetForegroundColour(foreground)

            self.readonlyWidgets.append({'widget':widget,'basevalue':basevalue,'norefresh':norefresh,'width':width,'linebreaks':linebreaks,'evaluate':evaluate,'targetinstance':targetinstance,'visible':visible,'tooltipfromvalue':tooltipfromvalue,'expression':expression})
            widgets.append(widget)

            if tooltipTitle or tooltipText: 
                self.createTooltip(widget,tooltipTitle,tooltipText)
            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)
            
            
        
        elif element.tag == 'image':
            path = element.get('path')
            if path is not None:
                #path = str(path)
                import os
                path = os.path.join(psc.abspath(verpath=True),path)
                png = wx.Image(path,wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                widget = wx.StaticBitmap(self.panel, -1, png, size = (png.GetWidth(), png.GetHeight()))
            widgets.append(widget)
 
        #TODO: there's no itemvalue anymore, just iterate over coding set
        #elif element.tag == 'addbutton':
        #    itemvalue = element.get('itemvalue')
        #    label = element.get('label')
        #    containerCrfName = self.crfName
        #    containerClassName = element.get('containerclass')
        #    containerAttributeName = element.get('containerattribute')
        #    label = element.get('label')
        #    if label != None:
        #        label = self.mainLogic.translateString(str(label))
        #    widget = wx.Button(self.panel, -1, label, style=wx.BU_EXACTFIT, name=itemvalue)

        #    #widget = wx.StaticText(self.panel, -1, label)
        #    self.addbuttonWidgets[itemvalue] = {'widget':widget, 'containercrf':containerCrfName, 'containerclass':containerClassName, 'containerattribute':containerAttributeName, 'itemvalue':itemvalue}
        #    widget.Bind(wx.EVT_BUTTON, self.addDynInterfaceButton)
        #    widgets.append(widget)

        elif element.tag == 'addselect':
            containerCrfName = self.crfName
            containerClassName = element.get('containerclass')
            containerAttributeName = element.get('containerattribute')
            containerCodingSetFullName = self.mainLogic.crfData.getPropertyForAttribute(containerCrfName,containerClassName,containerAttributeName,'codingSet')
            containerCodingSetName = self.mainLogic.crfData.splitCodingSetName(containerCodingSetFullName)[1]
            containerCodingSetValueNames = self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(containerCrfName,containerCodingSetName)

            decoratedCodingSetValueNames = []
            for containerCodingSetValueName in containerCodingSetValueNames:
                positionWeight = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'positionWeight')
                groupName = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'groupName')
                if positionWeight == None or not positionWeight.isdigit():
                    positionWeight = 10000
                decoratedCodingSetValueNames.append((groupName,int(positionWeight),containerCodingSetValueName))
            decoratedCodingSetValueNames.sort()
            groupNames = [entry[0] for entry in decoratedCodingSetValueNames]
            containerCodingSetValueNames = [entry[2] for entry in decoratedCodingSetValueNames]

            choiceStrings = ['Click here to add...']
            self.addselectChoices[(containerCrfName,containerClassName,containerAttributeName)] = dict()
            tooltipTitleValue = self.mainlogic.crfData.getPropertyForClass(containerCrfName,containerClassName,'label')
            tooltipTitle = ''
            if tooltipTitleValue:
                tooltipTitle = self.mainLogic.translateString(tooltipTitleValue)
            tooltipTexts = []
            for containerCodingSetValueName in containerCodingSetValueNames:
                itemValue = self.mainLogic.crfData.joinCodingSetValueName(containerCrfName,containerCodingSetName,containerCodingSetValueName)
                value = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'value')
                translatedString = self.mainLogic.translateString(value)
                self.addselectChoices[(containerCrfName,containerClassName,containerAttributeName)][translatedString] = itemValue
                choiceStrings.append(translatedString)
                tooltipValue = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'toolTip')
                tooltipTranslatedValue = ''
                if tooltipValue:
                    tooltipTranslatedValue = self.mainLogic.translateString(tooltipValue)
                if not tooltipTranslatedValue:
                    tooltipTranslatedValue = '-'
                tooltipTexts.append((translatedString,'%s: %s' % (translatedString,tooltipTranslatedValue)))
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
 
            name = self.mainLogic.crfData.joinAttributeName(containerCrfName,containerClassName,containerAttributeName)
            #widget = wx.ComboBox(self.panel, -1, choiceStrings[0], choices=choiceStrings, style=wx.CB_DROPDOWN|wx.CB_READONLY, size=wx.Size(width,-1),name='.'.join((containerCrfName,containerClassName,containerAttributeName)))
            widget = wx.Choice(self.panel, -1, choices=choiceStrings, size=wx.Size(width,-1), name='.'.join((containerCrfName,containerClassName,containerAttributeName)))
            #widget.Bind(wx.EVT_TEXT, self.addDynInterfaceSelect)
            widget.Bind(wx.EVT_CHOICE, self.addDynInterfaceSelect)
            #TODO: add reference to coding set here
            self.addselectWidgets[(containerCrfName,containerClassName,containerAttributeName)] = {'widget':widget,'tooltipTitle':tooltipTitle,'tooltipTexts':tooltipTexts}
            widgets.append(widget)

            if tooltipTitle or tooltipTexts: 
                tooltipText = '\n\n'.join([line for entry,line in tooltipTexts])
                self.createTooltip(widget,tooltipTitle,tooltipText)
            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

        elif element.tag == 'addselectlist':
            containerCrfName = self.crfName
            containerClassName = element.get('containerclass')
            containerAttributeName = element.get('containerattribute')
            containerCodingSetFullName = self.mainLogic.crfData.getPropertyForAttribute(containerCrfName,containerClassName,containerAttributeName,'codingSet')
            containerCodingSetName = self.mainLogic.crfData.splitCodingSetName(containerCodingSetFullName)[1]
            containerCodingSetValueNames = self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(containerCrfName,containerCodingSetName)

            decoratedCodingSetValueNames = []
            for containerCodingSetValueName in containerCodingSetValueNames:
                positionWeight = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'positionWeight')
                groupName = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'groupName')
                if positionWeight == None or not positionWeight.isdigit():
                    positionWeight = 10000
                decoratedCodingSetValueNames.append((groupName,int(positionWeight),containerCodingSetValueName))
            decoratedCodingSetValueNames.sort()
            groupNames = [entry[0] for entry in decoratedCodingSetValueNames]
            containerCodingSetValueNames = [entry[2] for entry in decoratedCodingSetValueNames]

            choiceStrings = []
            addselectChoices = dict()
            tooltipTitleValue = self.mainLogic.crfData.getPropertyForClass(containerCrfName,containerClassName,'label')
            tooltipTitle = ''
            if tooltipTitleValue:
                tooltipTitle = self.mainLogic.translateString(tooltipTitleValue)
            tooltipTexts = []
            for containerCodingSetValueName in containerCodingSetValueNames:
                itemValue = self.mainLogic.crfData.joinCodingSetValueName(containerCrfName,containerCodingSetName,containerCodingSetValueName)
                value = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'value')
                translatedString = self.mainLogic.translateString(value)
                addselectChoices[translatedString] = dict()
                addselectChoices[translatedString]['itemValue'] = itemValue
                choiceStrings.append(translatedString)
                tooltipValue = self.mainLogic.crfData.getPropertyForCodingSetValue(containerCrfName,containerCodingSetName,containerCodingSetValueName,'toolTip')
                tooltipTranslatedValue = ''
                if tooltipValue:
                    tooltipTranslatedValue = self.mainLogic.translateString(tooltipValue)
                if not tooltipTranslatedValue:
                    tooltipTranslatedValue = '-'
                addselectChoices[translatedString]['tooltipMessage'] = self.composeTooltip(translatedString,tooltipTranslatedValue)
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
 
            name = self.mainLogic.crfData.joinAttributeName(containerCrfName,containerClassName,containerAttributeName)

            label = element.get('label')
            if label != None:
                label = self.mainLogic.translateString(label)
            else:
                label= _("Select...")
            widget = wx.Button(self.panel, -1, label, name=name)
            widget.Bind(wx.EVT_BUTTON, self.showAddDynInterfaceList)

            self.addselectButtons[(containerCrfName,containerClassName,containerAttributeName)] = {'widget':widget,'tooltipTitle':tooltipTitle,'addselectChoices':addselectChoices,'choiceStrings':choiceStrings}
            widgets.append(widget)

            if tooltipTitle or tooltipTexts: 
                tooltipText = '\n\n'.join([line for entry,line in tooltipTexts])
                self.createTooltip(widget,tooltipTitle,tooltipText)
            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

        elif element.tag == 'removebutton':
            import os
            deleteImagePath = os.path.join(psc.imagesPath,'Delete.png')
            deleteImage = wx.Image(deleteImagePath, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            label = element.get('label')
            if label != None:
                label = self.mainLogic.translateString(label)
            else:
                label= _("Remove")
            widget = wx.BitmapButton(self.panel, id=-1, bitmap=deleteImage, size = (deleteImage.GetWidth()+2, deleteImage.GetHeight()+2), name = label)
            #widget = wx.Button(self.panel, -1, label)
            widget.SetToolTipString(_("Click to delete procedure"))
            widget.Bind(wx.EVT_BUTTON, self.removeDynInterface)
            widgets.append(widget)

        elif element.tag == 'dynnumber':
            label = element.get('label')
            if label != None:
                label = self.mainLogic.translateString(label)
            crfName = self.crfName
            containerClassName = element.get('containerclass')
            containerAttributeName = element.get('containerattribute')
            className = element.get('class')
            if label: 
                widget = wx.StaticText(self.panel, -1, label)
                widgets.append(widget)
            widget = wx.SpinCtrl(self.panel, -1)
            widget.Bind(wx.EVT_SPINCTRL, self.dynNumberSet)
            self.dynnumberWidgets[widget] = {'className':className,'containerClassName':containerClassName,'containerAttributeName':containerAttributeName}
            widgets.append(widget)

        elif element.tag == 'dyninterface':
            className = element.get('class')
            attributeName = element.get('attribute')
            interfaceName = element.get('interfacename')
            self.callbacksDict['onCreateObjectGuiCallback'](self.crfName,className,attributeName,interfaceName,self.panel,self.sizersFromRoot[-1])

        elif element.tag == 'arrowcursor':
            cursorName = element.get('cursor')
            containerName = element.get('container')

            widget = wx.Button(self.panel, -1, _("Previous"))
            widget.Bind(wx.EVT_BUTTON, self.cursorPreviousInContainer)
            widgets.append(widget)

            self.cursorWidgets[widget] = {'cursor':cursorName, 'container':containerName}

            widget = wx.Button(self.panel, -1, _("Next"))
            widget.Bind(wx.EVT_BUTTON, self.cursorNextInContainer)
            widgets.append(widget)
            
            self.cursorWidgets[widget] = {'cursor':cursorName, 'container':containerName}

        elif element.tag == 'historywidget':

            try:
                width = int(element.get('width'))
            except:
                width = 200

            try:
                height = int(element.get('height'))
            except:
                height = 300
 
            attributeFullNames = element.get('attributes')
            attributeFullNames = [el.strip() for el in attributeFullNames.split(';')]

            pageLinkName = element.get('pagelink')

            timeStampAttributeFullName = element.get('timeStamp')
            minTimeStamp = element.get('minTimeStamp')
            if minTimeStamp != None:
                minTimeStamp = int(minTimeStamp)

            columnNames = []
            counterLabel = None
            if element.get('counter') == "1":
                counterLabel = element.get('counterLabel')
                if counterLabel:
                    columnNames.append(self.mainLogic.translateString(counterLabel))
                else:
                    columnNames.append(self.mainLogic.translateString('Id'))

            attributeFullNamesToLabels = dict()
            for attributeFullName in attributeFullNames:
                crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
                attributeLabelValue = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'label')
                if not attributeLabelValue:
                    attributeLabelValue = attributeFullName
                else:
                    attributeLabelValue = self.mainLogic.translateString(attributeLabelValue)
                columnNames.append(attributeLabelValue)
                attributeFullNamesToLabels[attributeFullName] = self.mainLogic.translateString(attributeLabelValue)
 
            
            rows = []
            timeStamps = set()
            timeStampCrfName, timeStampClassName, timeStampAttributeName = self.mainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
            for className in self.mainLogic.crfData.getClassesByPropertyWithValue(timeStampCrfName, 'timeStamp', timeStampAttributeFullName):
                timeStampsForClass = self.mainLogic.dataSession.getAllTimeStampsForClass(timeStampCrfName,className) #attributeName is not used
                timeStamps.update(timeStampsForClass)
                
            timeStamps = [x for x in timeStamps if x >= minTimeStamp]
            #for attributeFullName in attributeFullNames:
                #currentTimeStampAttributeFullName = self.mainLogic.crfData.getPropertyForClass(crfName,className,'timeStamp')
                #if currentTimeStampAttributeFullName != timeStampAttributeFullName:
                #    continue
                #crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
                #attributeValuesDict = self.mainLogic.dataSession.getAllAttributeValuesForClass(crfName,className,attributeName,timeDict=True)
                #for timeStamp in attributeValuesDict:
                #    if attributeValuesDict[timeStamp] == None:
                #        continue
                #    if minTimeStamp != None:
                #        if timeStamp < minTimeStamp:
                #            continue
                #    timeStamps.add(timeStamp)

            sortByAttributeFullName = self.mainLogic.crfData.getPropertyForAttribute(timeStampCrfName,timeStampClassName,timeStampAttributeName,'sortBy')

            if sortByAttributeFullName:
                sortByCrfName, sortByClassName, sortByAttributeName = self.mainLogic.crfData.splitAttributeName(sortByAttributeFullName)
                timeStampToSortByValuesDict = self.mainLogic.dataSession.getAllAttributeValuesForClass(sortByCrfName,sortByClassName,sortByAttributeName,timeDict=True)
                sortByToTimeStampPairs = [(v,k) for k,v in timeStampToSortByValuesDict.iteritems()]
                sortByToTimeStampPairs.sort()
                sortedTimeStamps = [el[1] for el in sortByToTimeStampPairs]
                extraTimeStamps = [el for el in timeStamps if el not in sortedTimeStamps]
                sortedTimeStamps = sortedTimeStamps + extraTimeStamps
            else:
                sortedTimeStamps = timeStamps

            for i, timeStamp in enumerate(sortedTimeStamps):
                row = {'timeStamp':timeStamp}
                if counterLabel:
                    row[self.mainLogic.translateString(counterLabel)] = str(i+1)
                for attributeFullName in attributeFullNames:
                    currentTimeStampAttributeFullName = self.mainLogic.crfData.getPropertyForClass(crfName,className,'timeStamp')
                    if currentTimeStampAttributeFullName != timeStampAttributeFullName:
                        continue
                    crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
                    attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(crfName,className,attributeName,timeStamp)
                    objectCode = self.mainLogic.dataSession.getObjectCode(crfName,className,1,timeStamp)
                    if not attributeValues:
                        row[attributeFullNamesToLabels[attributeFullName]] = ""
                    elif len(attributeValues) == 1:
                        row[attributeFullNamesToLabels[attributeFullName]] = psevaluator.decodevalue(attributeValues[0])
                    else:
                        row[attributeFullNamesToLabels[attributeFullName]] = ';'.join(psevaluator.decode(attributeValues))
                rows.append(row)

            timeStampCrfName, timeStampClassName, timeStampAttributeName = self.mainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
            timeStampAttributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(timeStampCrfName,timeStampClassName,timeStampAttributeName)
            currentTimeStamp = None
            if timeStampAttributeValues:
                currentTimeStamp = timeStampAttributeValues[0]

            widget = PSHistoryWidget(self.panel, -1, "", size=wx.Size(width,height), pos=wx.DefaultPosition, columnNames=columnNames, rows=rows, currentTimeStamp=currentTimeStamp, timeStampAttributeFullName=timeStampAttributeFullName, timeStampSelectedCallback=self.timeStampSelectedCallback, timeStampActivatedCallback=self.callbacksDict['onPageLinkCallback'], pageLinkName=pageLinkName)
            widgets.append(widget)
 
        elif element.tag == 'button':
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            label = element.get('label')
            enabled = element.get('enabled')
            visible = element.get('visible')
            onclick = element.get('onclick')
            tooltipValue = element.get('toolTip')
            label = self.mainLogic.translateString(label)
            widget = wx.Button(self.panel, -1, label, size=wx.Size(width,-1))
            widget.Bind(wx.EVT_BUTTON, self.buttonClicked)
            widgets.append(widget)
            self.buttonWidgets[widget] = {'enabled':enabled,'visible':visible,'width':width,'onclick':onclick}
            tooltipTitle = label
            tooltipText = ''
            if tooltipValue:
                tooltipText = self.mainLogic.translateString(tooltipValue)
            if tooltipTitle or tooltipText: 
                self.createTooltip(widget,tooltipTitle,tooltipText)
            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

        elif element.tag == 'pagelink':
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            enabled = element.get('enabled')
            visible = element.get('visible')
            pagename = element.get('pagename')
            onclick = element.get('onclick')
            evaluateTimeStamp = element.get('evaluateTimeStamp')
            tooltipValue = element.get('toolTip')
            if pagename != None:
                label = self.mainLogic.translateString(pagename)
                widget = wx.Button(self.panel, -1, label, size=wx.Size(width,-1), name=pagename)
                widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
                widgets.append(widget)
                self.pagelinkWidgets[widget] = {'enabled':enabled,'visible':visible,'width':width,'onclick':onclick,'evaluateTimeStamp':evaluateTimeStamp}
                tooltipTitle = label
                tooltipText = ''
                if tooltipValue:
                    tooltipText = self.mainLogic.translateString(tooltipValue)
                if tooltipTitle or tooltipText: 
                    self.createTooltip(widget,tooltipTitle,tooltipText)
                widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
                widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

        elif element.tag == 'urlbutton':
            #added urlbutton element and corrispondent behaviour
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            enabled = element.get('enabled')
            visible = element.get('visible')
            linkname = element.get('linkname')
            url = element.get('url')
            evaluateParameters = element.get('evaluateParameters')
            onclick = element.get('onclick')
            if linkname != None:
                label = self.mainLogic.translateString(str(linkname))
                widget = wx.Button(self.panel, -1, label, size=wx.Size(width,-1), name=url)
                widget.Bind(wx.EVT_BUTTON, self.urlButtonClicked)
                widgets.append(widget)
                self.pagelinkWidgets[widget] = {'enabled':enabled,'visible':visible,'width':width,'evaluateParameters':evaluateParameters}
                widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
                widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)
        elif element.tag == 'imagezoom':
            imagename = element.get('imagename')
            labelname = element.get('label')
            visible = element.get('visible')
            enabled = element.get('enabled')
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            labelname = self.mainLogic.translateString(str(labelname))
            widget = wx.Button(self.panel, -1, labelname, size=wx.Size(width,-1), name=imagename)
            widget.Bind(wx.EVT_BUTTON, self.neuroImageButtonClicked)
            widgets.append(widget)
            self.pagelinkWidgets[widget] = {'enabled':enabled,'visible':visible}
            
        elif element.tag == 'popinfo':
            popname = element.get('textinfo')
            labelname = element.get('label')
            visible = element.get('visible')
            enabled = element.get('enabled')
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            popname = self.mainLogic.translateString(str(popname))
            labelname = self.mainLogic.translateString(str(labelname))
            widget = wx.Button(self.panel, -1, labelname, size=wx.Size(width,-1), name=popname)
            widget.Bind(wx.EVT_BUTTON, self.popButtonClicked)
            widgets.append(widget)
            self.pagelinkWidgets[widget] = {'enabled':enabled,'visible':visible}
        #elif element.tag == 'dialog':
        #    try: 
        #        width = int(element.get('width'))
        #    except: 
        #        width = -1
        #    enabled = element.get('enabled')
        #    visible = element.get('visible')
        #    pagename = element.get('class')
        #    pagename = element.get('name')
        #    tooltipValue = element.get('toolTip')
        #    if dialog != None:
        #        label = self.mainLogic.translateString(str(pagename))
        #        widget = wx.Button(self.panel, -1, label, size=wx.Size(width,-1), name=pagename)
        #        widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
        #        widgets.append(widget)
        #        self.pagelinkWidgets.append({'widget':widget,'enabled':enabled,'visible':visible,'width':width})
        #        tooltipTitle = label
        #        tooltipText = ''
        #        if tooltipValue:
        #            tooltipText = self.mainLogic.translateString(tooltipValue)
        #        if tooltipTitle or tooltipText: 
        #            self.createTooltip(widget,tooltipTitle,tooltipText)
        #        widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
        #        widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)

        elif element.tag == 'linepanel':           
            try: 
                width = int(element.get('width'))
            except: 
                width = -1
            try: 
                height = int(element.get('height'))
            except: 
                height = -1
            widget = wx.Panel(self.panel, -1, size=wx.Size(width,height))
            widget.SetBackgroundColour('gray')
            widgets.append(widget)

        for widget in widgets:
            widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
            widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)
            pass
            
        return widgets
 
    #def addDynInterfaceButton(self,event):
    #    button = event.GetEventObject()
    #    buttonWidgetInfo = self.addbuttonWidgets[button.GetName()]
    #    containerCrf = buttonWidgetInfo['containercrf']
    #    containerClassName = buttonWidgetInfo['containerclass']
    #    containerAttributeName = buttonWidgetInfo['containerattribute']
    #    itemValue = buttonWidgetInfo['itemvalue']
    #    #############################################################################################################
    #    #TODO: the following doesn't work, since containerClassName and attribute do not know about the coding set, it's all put together in the interface, which may cause problems
    #    #codingSetName = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,containerClassName,containerAttributeName,'codingSet')
    #    #codingSetName = 
    #    #className = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,,itemValue,'dynclass')
    #    #className = self.mainLogic.crfData.classIdsToNames[int(self.mainLogic.crfData.codingSetValuesProperties['dynclass'][int(itemValue)])]
    #    #attributeName = self.mainLogic.crfData.attributeIdsToNames[int(self.mainLogic.crfData.codingSetValuesProperties['dynattribute'][int(itemValue)])]
    #    #self.callbacksDict['onAddDynInterfaceCallback'](containerClassName,containerAttributeName,className,attributeName,itemValue)

    def timeStampSelectedCallback(self, timeStampAttributeFullName, timeStamp):
        timeStampCrfName, timeStampClassName, timeStampAttributeName = self.mainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
        self.mainLogic.dataSession.updateDataNoNotify(timeStampCrfName,timeStampClassName,1,timeStampAttributeName,timeStamp)
        userInfo = {'crfName': psc.coreCrfName}
        self.mainLogic.notificationCenter.postNotification('DynPageHasChanged',self,userInfo)

    def addDynInterfaceSelect(self,event):
        widget = event.GetEventObject()
        name = widget.GetName()
        containerCrfName, containerClassName, containerAttributeName = self.mainLogic.crfData.splitAttributeName(name)
        selectWidgetInfo = self.addselectWidgets[(containerCrfName,containerClassName,containerAttributeName)]
        #selectedValue = widget.GetValue()
        selectedValue = event.GetString()
        if (containerCrfName,containerClassName,containerAttributeName) not in self.addselectChoices or selectedValue not in self.addselectChoices[(containerCrfName,containerClassName,containerAttributeName)]: 
            return
        itemValue = self.addselectChoices[(containerCrfName,containerClassName,containerAttributeName)][selectedValue]
        crfName, codingSetName, codingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(itemValue)
        #className = self.mainLogic.crfData.getPropertyForCodingSetValue(crfName,codingSetName,codingSetValueName,'dynclass')
        attributeFullName = self.mainLogic.crfData.getPropertyForCodingSetValue(crfName,codingSetName,codingSetValueName,'dynattribute')
        crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
        self.callbacksDict['onAddDynInterfaceCallback'](containerCrfName,containerClassName,containerAttributeName,crfName,className,attributeName,itemValue)

    def removeDynInterface(self,event):
        self.callbacksDict['onRemoveDynInterfaceCallback'](self.crfName,self.className,self.classInstanceNumber,self.containerCrfName,self.containerClassName,self.containerClassInstanceNumber,self.containerAttributeName)

    def dynNumberSet(self,event):
        widget = event.GetEventObject()
        number = widget.GetValue()
        className = self.dynnumberWidgets[widget]['className']
        containerClassName = self.dynnumberWidgets[widget]['containerClassName']
        containerAttributeName = self.dynnumberWidgets[widget]['containerAttributeName']
        self.callbacksDict['onDynNumberSetCallback'](self.crfName,containerClassName,containerAttributeName,className,number)

    def showAddDynInterfaceList(self,event):
        widget = event.GetEventObject()
        name = widget.GetName()
        containerCrfName, containerClassName, containerAttributeName = self.mainLogic.crfData.splitAttributeName(name)
        selectButtonInfo = self.addselectButtons[(containerCrfName,containerClassName,containerAttributeName)]
        addselectChoices = selectButtonInfo['addselectChoices']
        choiceStrings = selectButtonInfo['choiceStrings']

        visibleChoiceStrings = []
        enabledValues = []
        for value in choiceStrings:
            itemValue = addselectChoices[value]['itemValue']
            valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(itemValue)
            attributeFullName = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynattribute')
            crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
            visibleExpression = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'visible')
            if visibleExpression:
                visible = bool(self.mainLogic.evaluator.eval(visibleExpression))
                if visible == False:
                    continue
            visibleChoiceStrings.append(value)
            maxOccurrences = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynmaxoccurrences')
            if maxOccurrences == None:
                enabledValues.append(value)
                continue
            attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(valueCrfName,className,attributeName)
            if not attributeValues:
                enabledValues.append(value)
                continue
            numberOfOccurrences = len([el for el in attributeValues if el == itemValue])
            if numberOfOccurrences < int(maxOccurrences):
                enabledValues.append(value)

        choiceStrings = visibleChoiceStrings

        tooltipStrings = [addselectChoices[choiceString]['tooltipMessage'] for choiceString in choiceStrings] 

        listbox = PSCheckListBox(self.panel, -1, choiceStrings=choiceStrings, enabledChoiceStrings=enabledValues, tooltipStrings=tooltipStrings, tooltipCallback=self.listboxTooltipCallback, size=wx.DefaultSize, style=wx.SUNKEN_BORDER | wx.CAPTION | wx.STAY_ON_TOP)
        listbox.SetWindowVariant(GUI_WINDOW_VARIANT)
        listbox.CenterOnParent()
        listbox.ShowModal()
        choices = listbox.choices
        listbox.Destroy()

        for choice in choices:
            itemValue = addselectChoices[choice]['itemValue']
            crfName, codingSetName, codingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(itemValue)
            attributeFullName = self.mainLogic.crfData.getPropertyForCodingSetValue(crfName,codingSetName,codingSetValueName,'dynattribute')
            crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
            self.callbacksDict['onAddDynInterfaceCallback'](containerCrfName,containerClassName,containerAttributeName,crfName,className,attributeName,itemValue)

    def listboxTooltipCallback(self, show, tooltipString=''):
        if show:
            self.callbacksDict['onShowDocumentationCallback'](tooltipString)
        else:
            self.callbacksDict['onHideDocumentationCallback']()
 
    def buttonClicked(self,event):
        button = event.GetEventObject()
        onclick = self.buttonWidgets[button]['onclick']
        crfName = None
        className = None
        classInstanceNumber = None
        if type(self) is ObjectGui:
            crfName = self.crfName
            className = self.className
            classInstanceNumber = self.classInstanceNumber
        if onclick:
            self.mainLogic.evaluator.eval(onclick,lhsCrfName=crfName,lhsClassName=className,lhsClassInstanceNumber=classInstanceNumber,noCache=True)
    
    def neuroImageButtonClicked(self, event): 
        button = event.GetEventObject()
        imagename = button.GetName()
        widget = imageZoomDialog(None, -1, imagename)
        widget.Centre()
        widget.Show(True)
    
    def popButtonClicked(self,event):
        button = event.GetEventObject()
        popinfoname = button.GetName()
        popinoLabel = button.GetLabel()
        widget = popInfoDialog(None, -1, popinoLabel, popinfoname )
        # widget.Centre()
        # widget.Show(True)
        
        
    def urlButtonClicked(self,event):
        button = event.GetEventObject()
        url = button.GetName()
        baseurl = url
        parameter = self.callbacksDict['onUrlButtonCallback'](self.pagelinkWidgets[button]['evaluateParameters'])
        if parameter:
            import base64
            import urllib
            parameter = base64.b64encode(parameter)
            url = base64.b64encode(url + '?')
            url = base64.b64decode(url) + urllib.quote(base64.b64decode(parameter).replace("/", "%2F"))
            #url = url.replace(" ", "%20")
            print url
            url = url.replace("#", "%23")
            #url = url.replace("/", "%2F")
            url = url.replace('"', '%22')
            url = url.replace('%3D', '=')
            url = url.replace('%26', '&')
            
            
            
        #parameter = parameter.encode('utf-8')
        #TODO daniele: insert opening url 
        from mainlogic import _
        msgBody = _("PROSAFE is trying to open the page: ")
        msgPrompt = _("Continue?")
        message = msgBody + '\n\n' + baseurl + '\n\n' + msgPrompt
        dlg = wx.MessageDialog(None, message, _("Opening web page"), wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            #url = urllib.quote(url)
            wx.LaunchDefaultBrowser(url)
        
    def pageLinkClicked(self,event):
        button = event.GetEventObject()
        crfName = None
        className = None
        classInstanceNumber = None
        if type(self) is ObjectGui:
            crfName = self.crfName
            className = self.className
            classInstanceNumber = self.classInstanceNumber
        self.callbacksDict['onPageLinkCallback'](button.GetName(),self.timeStamp,self.pagelinkWidgets[button]['evaluateTimeStamp'],self.pagelinkWidgets[button]['onclick'],crfName,className,classInstanceNumber)

    def cursorPreviousInContainer(self,event):
        button = event.GetEventObject()
        cursorName = self.cursorWidgets[button]['cursor']
        containerName = self.cursorWidgets[button]['container']
        containerCrfName, containerClassName, containerAttributeName = self.mainLogic.crfData.splitAttributeName(containerName)
        cursorCrfName, cursorClassName, cursorAttributeName = self.mainLogic.crfData.splitAttributeName(cursorName)
        self.callbacksDict['onCursorMoveInContainer']('backward',containerCrfName,containerClassName,containerAttributeName,cursorCrfName,cursorClassName,cursorAttributeName)

    def cursorNextInContainer(self,event):
        button = event.GetEventObject()
        cursorName = self.cursorWidgets[button]['cursor']
        containerName = self.cursorWidgets[button]['container']
        containerCrfName, containerClassName, containerAttributeName = self.mainLogic.crfData.splitAttributeName(containerName)
        cursorCrfName, cursorClassName, cursorAttributeName = self.mainLogic.crfData.splitAttributeName(cursorName)
        self.callbacksDict['onCursorMoveInContainer']('forward',containerCrfName,containerClassName,containerAttributeName,cursorCrfName,cursorClassName,cursorAttributeName)

    def updateGui(self):

        crfName = None
        className = None
        classInstanceNumber = None
        if type(self) is ObjectGui:
            crfName = self.crfName
            className = self.className
            classInstanceNumber = self.classInstanceNumber
 
        forceRefresh = True
        for widget, widgetDict in self.buttonWidgets.items() + self.pagelinkWidgets.items():
            enabledExpression = widgetDict['enabled']
            if enabledExpression:
                enabled = self.mainLogic.evaluator.eval(enabledExpression,crfName,className,classInstanceNumber)
                if enabled:
                    widget.Enable()
                else:
                    widget.Disable()
            visibleExpression = widgetDict['visible']
            if visibleExpression:
                visible = self.mainLogic.evaluator.eval(visibleExpression,crfName,className,classInstanceNumber)
                if visible:
                    widget.Show()
                else:
                    widget.Hide()
            
        for widgetDict in self.readonlyWidgets:
            widget = widgetDict['widget']
            width = widgetDict['width']
            basevalue = widgetDict['basevalue']
            norefresh = widgetDict['norefresh']
            linebreaks = widgetDict['linebreaks']
            evaluate = widgetDict['evaluate']
            expression = widgetDict['expression']
            targetinstance = widgetDict['targetinstance']
            tooltipfromvalue = widgetDict['tooltipfromvalue']
            if not forceRefresh and norefresh:
                continue

            visibleExpression = widgetDict['visible']
            if visibleExpression:
                visible = self.mainLogic.evaluator.eval(visibleExpression)
                if visible:
                    widget.Show()
                else:
                    widget.Hide()
                    continue
 
            textList = []
            tooltipTitleList = []
            tooltipTextList = []

            if evaluate:
                fields = evaluate.split(',')
                for field in fields:
                    pieces = field.strip().split('.')
                    if len(pieces) != 3:
                        print 'ERROR IN EVALUATION EXPRESSION (guigenerator): %s', expression
                        continue
                    crfName = pieces[0]
                    className = pieces[1]
                    attributeName = pieces[2]

                    if targetinstance == 'self':
                        if type(self) is not ObjectGui:
                            print 'ERROR: targetinstance=self can only be used with ObjectGui instances'
                            attributeValues = []
                        elif className != self.className:
                            print 'ERROR: targetinstance=self can only if expression is referred to current class. Got %s and %s (current) instead' % (className, self.className)
                            attributeValues = []
                        else:
                            attributeValues = self.mainLogic.dataSession.getAttributeValuesForObject(crfName,className,self.classInstanceNumber,attributeName)
                    else:
                        attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(crfName,className,attributeName)

                    codingSetName = None
                    codingSetFullName = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'codingSet')
                    if codingSetFullName:
                        codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
                    dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')

                    separator = ', '
                    if linebreaks:
                        separator = '\n'
                    decodedAttributeValues = []
                    decodedTooltipTexts = []
                    if codingSetName != None:
                        for value in attributeValues:
                            valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(value)
                            #decodedValue = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'value')
                            #decodedAttributeValues.append(self.mainLogic.translateString(decodedValue))
                            decodedAttributeValues.append(psevaluator.decodevalue(value))
                            if tooltipfromvalue:
                                decodedTooltipValue = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'toolTip')
                                if decodedTooltipValue:
                                    decodedTooltipTexts.append(self.mainLogic.translateString(decodedTooltipValue))
                                else:
                                    decodedTooltipTexts.append('')
                        text = separator.join(decodedAttributeValues)
                        if tooltipfromvalue:
                            tooltipTitleList.extend(decodedAttributeValues)
                            tooltipTextList.extend(decodedTooltipTexts)
                    elif dataType == 'error':
                        for value in attributeValues:
                            errorInfo = self.mainLogic.crfData.getErrorInfoForId(crfName,value)
                            if not errorInfo:
                                continue
                            decodedValue = errorInfo['textId']
                            decodedAttributeValues.append(self.mainLogic.translateString('@@@%s@@@' % decodedValue))
                            errorResult = self.mainLogic.evaluator.eval(errorInfo['expression'])
                            if errorInfo.get('appendResultToText') == "1":
                                decodedAttributeValues.append(errorResult)
                        text = separator.join(decodedAttributeValues)
                    elif dataType == 'float':
                        text = separator.join(["%0.2f" % value for value in attributeValues])
                    else:
                        text = separator.join([psevaluator.decodevalue(unicode(value)) for value in attributeValues])
                    if text:
                        textList.append(text)

                text = separator.join(textList)

            elif expression:
                result = self.mainLogic.evaluator.eval(expression)
                if result == None:
                    result = ''
                text = unicode(result)

            basevalueText = self.mainLogic.translateString(basevalue)

            if tooltipfromvalue:
                if len(tooltipTitleList) > 1:
                    tooltipTitle = basevalueText
                    tooltipText = '\n'.join(["%s: %s" % (atitle,atext) for atitle,atext in zip(tooltipTitleList,tooltipTextList)])
                else:
                    tooltipTitle = basevalueText + ''.join(tooltipTitleList)
                    tooltipText = ''.join(tooltipTextList)
                if tooltipTitle or tooltipText:
                    self.createTooltip(widget,tooltipTitle,tooltipText)

            sizer = widget.GetContainingSizer()
            if text in ['False','',False]:
                text = ''
                if widget.IsShown(): 
                    sizer.Show(widget,False,True)
                    sizer.Layout()
            else:
                newLabel = text
                if basevalueText:
                    if linebreaks:
                        newLabel = separator.join((basevalueText,text))
                    else:
                        newLabel = basevalueText + text
                widget.SetLabel(newLabel)
                sizer = widget.GetContainingSizer()
                widget.Wrap(width)
                if not widget.IsShown(): 
                    sizer.Show(widget,True,True)
                    sizer.Layout()
                    self.panel.GetSizer().Layout()

        self.evaluateDynCodingSetStates()

    def evaluateDynCodingSetStates(self):
       
        #for name in self.addbuttonWidgets:
        #    buttonWidgetInfo = self.addbuttonWidgets[name]
        #    itemValue = buttonWidgetInfo['itemvalue']
        #    valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(itemValue)
        #    className = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynclass')
        #    attributeName = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynattribute')
        #    maxOccurrences = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynmaxoccurrences')
        #    if maxOccurrences == None:
        #        buttonWidgetInfo['widget'].Enable()
        #    attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(valueCrfName,className,attributeName)
        #    if not attributeValues:
        #        buttonWidgetInfo['widget'].Enable()
        #        continue
        #    numberOfOccurrences = len([el for el in attributeValues if el == itemValue])
        #    if numberOfOccurrences >= int(maxOccurrences):
        #        buttonWidgetInfo['widget'].Disable()
        #    else:
        #        buttonWidgetInfo['widget'].Enable()
           
        #TODO: evaluate codingSetProperties (e.g. visibility) 
        for name in self.addselectWidgets:
            containerCrfName, containerClassName, containerAttributeName = name
            selectWidgetInfo = self.addselectWidgets[name]
            if (containerCrfName,containerClassName,containerAttributeName) not in self.addselectChoices: 
                print 'ERROR: container crf, class and attribute not in addselectChoices'
                continue
            widget = selectWidgetInfo['widget']
            values = widget.GetStrings()
            enabledValues = [values[0]]
            for value in values[1:]:
                if value not in self.addselectChoices[(containerCrfName,containerClassName,containerAttributeName)]:
                    print 'ERROR: value not in addselectChoices'
                    continue
                itemValue = self.addselectChoices[(containerCrfName,containerClassName,containerAttributeName)][value]
                valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(itemValue)
                #className = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynclass')
                attributeFullName = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynattribute')
                crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
                visibleExpression = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'visible')
                if visibleExpression:
                    visible = bool(self.mainLogic.evaluator.eval(visibleExpression))
                    if visible == False:
                        continue
                maxOccurrences = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'dynmaxoccurrences')
                if maxOccurrences == None:
                    enabledValues.append(value)
                    continue
                attributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(valueCrfName,className,attributeName)
                if not attributeValues:
                    enabledValues.append(value)
                    continue
                numberOfOccurrences = len([el for el in attributeValues if el == itemValue])
                if numberOfOccurrences < int(maxOccurrences):
                    enabledValues.append(value)
            if enabledValues != values:
                widget.Clear()
                for value in enabledValues:
                    widget.Append(value)
                widget.SetSelection(0)
                if selectWidgetInfo['tooltipTitle'] or selectWidgetInfo['tooltipTexts']:
                    tooltipText = '\n\n'.join([line for entry,line in selectWidgetInfo['tooltipTexts'] if entry in enabledValues])
                    self.createTooltip(widget,selectWidgetInfo['tooltipTitle'],tooltipText)

    def onEnterWidget(self,event):
        widget = event.GetEventObject()
        try:
            self.callbacksDict['onShowDocumentationCallback'](widget.infoText)
        except:
            pass
        event.Skip()

    def onLeaveWidget(self,event):
        widget = event.GetEventObject()
        self.callbacksDict['onHideDocumentationCallback']()
        event.Skip()


class ObjectGui(ItemGui):

    def __init__(self,mainLogic,crfName,className,classInstanceNumber,name,xmlFragment,callbacksDict):

        ItemGui.__init__(self,mainLogic,crfName,xmlFragment,callbacksDict)

        self.className = className
        self.classInstanceNumber = classInstanceNumber
        self.name = name

        ns = mainLogic.dataSession.getInstanceNumbersForClass(crfName,className)
        mainLogic.dataSession.registerInstanceNumberForClass(crfName,className,classInstanceNumber)
        ns2 = mainLogic.dataSession.getInstanceNumbersForClass(crfName,className)

        self.attributeKeys = None

        self.inputWidgets = dict()
        self.inputWidgetsReadonlyState = dict()
        self.inputTypes = dict()
        self.choices = dict()
        self.sizers = dict()
        self.confirmWidgets = dict()

    def setContainerClassInfo(self,containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName):
        self.containerCrfName = containerCrfName
        self.containerClassName = containerClassName
        self.containerClassInstanceNumber = containerClassInstanceNumber
        self.containerAttributeName = containerAttributeName

    def createWidgets(self,element,lblname=None):
        """Istanzia il corretto widget a partire dal tag XML corrispondente"""
        ifclass = self.className
       
        widgets = []

        if element.tag == 'input':

            inputType = element.get('type')
            attribute = element.get('attribute')
            widgetReadonlyStateValue = element.get('readonly')
            widgetReadonlyState = False
            if widgetReadonlyStateValue == "1":
                widgetReadonlyState = True
            instno = element.get('instance')
            if instno is not None:
                instance = str(instno)
            else:
                instance = '1'
            
            inputType = element.get('type')

            tooltipText = []
            inputWidgets = []
            if inputType == 'textbox':
                if element.get('mask') == "1":
                    mask = True
                else:
                    mask = False
                    
                try:
                    size = int(element.get('size'))
                except:
                    size = 100
                if element.get('expandable') == "1":
                    expandable = True
                else:
                    expandable = False
                try:
                    height = int(element.get('height'))
                    style = wx.TE_MULTILINE|wx.TE_WORDWRAP
                except:
                    height = -1
                    style = 0
                
                if not expandable:
                    if mask :
                        widget = masked.TextCtrl(self.panel,-1, mask = 'N{3}-N{3}-N{3}', formatcodes = "!>-_FS",fillChar=('X'), name=attribute)
                    else:
                        widget = wx.TextCtrl(self.panel, -1, "", size=wx.Size(size,height), style=style, name=attribute)
                        widget.Bind(expando.EVT_ETC_LAYOUT_NEEDED, self.onRefit)
                else:
                    if mask :
                        widget = masked.TextCtrl(self.panel,-1,mask='N{3}-N{3}-N{3}',formatcodes="!>-_FS",fillChar=('X'), name=attribute)
                    else:
                        widget = expando.ExpandoTextCtrl(self.panel, -1, "", size=wx.Size(size,-1), style=style, name=attribute)
                        widget.Bind(expando.EVT_ETC_LAYOUT_NEEDED, self.onRefit)
                widget.Bind(wx.EVT_CHAR, self.onText)
                widget.Bind(wx.EVT_KILL_FOCUS, self.onChange)
                # widget.Bind(expando.EVT_ETC_LAYOUT_NEEDED, self.onRefit)
                widgets.append(widget)
                inputWidgets.append(widget)
             
            elif inputType == 'date':
                widget = CalendarTextbox(self.panel, -1, wx.DateTime(), 'dd/mm/yyyy', size=wx.Size(100,-1), name=attribute)
                widget.Bind(wx.EVT_CHAR, self.onText)
                widget.Bind(wx.EVT_KILL_FOCUS, self.onChange)

                widgets.append(widget)
                inputWidgets.append(widget)
            
            elif inputType == 'notebutton':
                widget = psProcedureNoteButton(parent=self.panel, id=-1, bitmapPathWrite=os.path.join(psc.imagesPath,'write.png'), bitmapPathRead=os.path.join(psc.imagesPath,'read.png'), name=attribute, callback=self.onProcedureOnChange)
                widgets.append(widget)
                inputWidgets.append(widget)
                
            elif inputType == 'startwidget':
                widget = myFrame(parent=self.panel, id=-1, listPeriods = self.mainLogic.evaluator.eval("result = |start.vasoactivePeriods.value|[0]"), name=attribute, callback=self.onStartOnChange)
                widgets.append(widget)
                inputWidgets.append(widget)
                             
            elif inputType == 'time':
                try:
                    size = int(element.get('size'))
                except:
                    size = 100
                widget = HourTextbox(self.panel, -1, "", size=wx.Size(size,-1), name=attribute)
                widget.Bind(wx.EVT_CHAR, self.onText)
                widget.Bind(wx.EVT_KILL_FOCUS, self.onChange)

                widgets.append(widget)
                inputWidgets.append(widget)
                
            elif inputType == 'timer':
                try:
                    size = int(element.get('size'))
                except:
                    size = 100
                widget = TimerTextbox(self.panel, -1, "", size=wx.Size(size,-1), name=attribute)
                widget.Bind(wx.EVT_CHAR, self.onText)
                widget.Bind(wx.EVT_KILL_FOCUS, self.onChange)

                widgets.append(widget)
                inputWidgets.append(widget)
                
            elif inputType == 'simplecheckbox':
                label = element.get('label')
                nolabel = element.get('nolabel')
                cblabel = ''
                if label != None:
                    cblabel = self.mainLogic.translateString(label)
                elif nolabel != "1":
                    attributeLabelValue = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,self.className,attribute,'label')
                    classLabelValue = self.mainLogic.crfData.getPropertyForClass(self.crfName,self.className,'label')
                    if attributeLabelValue:
                        cblabel = self.mainLogic.translateString(attributeLabelValue)
                    elif classLabelValue:
                        cblabel = self.mainLogic.translateString(classLabelValue)
                try:
                    wrap = int(element.get('wrap'))
                except:
                    wrap = -1

                #TODO: handle centering controls in parent sizer
                center = element.get('center')
                    
                if not self.choices.has_key(attribute):
                    self.choices[attribute] = dict()

                try:
                    itemValue = element.get('itemvalue')
                except:
                    itemValue = None
                id = self.callbacksDict['getNewIdCallback']()
                #id = 0
                self.choices[attribute][id] = itemValue

                try: 
                    width = int(element.get('width'))
                except: 
                    width = -1
                
                try: 
                    ww =  element.get('fontweight')
                except: 
                    ww = wx.NORMAL
                
                try: 
                    ws =  int(element.get('fontsize'))
                except: 
                    ws = None
                labelValue = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,self.className,attribute,'label')
                if not labelValue:
                    labelValue = self.mainLogic.crfData.getPropertyForClass(self.crfName,self.className,'label')
                if labelValue:
                    labelText = self.mainLogic.translateString(labelValue)
                    tooltipTitle = "%s: %s" % (labelText, cblabel)
                else:
                    tooltipTitle = "%s" % cblabel
                
                tooltipProperty = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,self.className,attribute,'toolTip')
                tooltipText.append((tooltipTitle,tooltipProperty))
                #widget = wx.CheckBox(self.panel, id, cblabel, name=attribute, size = wx.Size(width, -1))
                widget = MLCheckBox(self.panel, id, cblabel, wrap=wrap, name=attribute, size = wx.Size(width, -1))
                
                widget.Bind(wx.EVT_CHECKBOX, self.onChange)
                
                #tooltipText.append((cblabel,""))
                
               

                if not ENFORCE_SYSTEM_FONT:
                    if ww == 'bold':
                        f = widget.GetFont()
                        f.SetWeight(wx.FONTWEIGHT_BOLD)
                        widget.SetFont(f)
                        
                    if ws != None:
                        f = widget.GetFont()
                        f.SetPointSize(ws)
                        widget.SetFont(f)

                widgets.append(widget)
                inputWidgets.append(widget)
           
            elif inputType == 'checkbox':

                try: 
                    width = int(element.get('width'))
                except: 
                    width = -1
                
                try: 
                    ww = element.get('fontweight')
                except: 
                    ww = wx.NORMAL
                
                try: 
                    ws = int(element.get('fontsize'))
                except: 
                    ws = None

                try: 
                    nogname = element.get('nogname')
                except: 
                    nogname = None

                try:
                    wrap = int(element.get('wrap'))
                except:
                    wrap = -1

                
                codingSetFullName = self.mainLogic.dataSession.getCodingSetNameForAttribute(self.crfName,self.className,attribute,self.classInstanceNumber)
                if not codingSetFullName:
                    return

                codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
                codingSetValueNames = self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(self.crfName,codingSetName)
                    

                decoratedCodingSetValueNames = []
                for codingSetValueName in codingSetValueNames:
                    positionWeight = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'positionWeight')
                    groupName = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'groupName')
                    if nogname == "1":
                        groupName = None
                    if positionWeight == None or not positionWeight.isdigit():
                        positionWeight = 10000
                    decoratedCodingSetValueNames.append((groupName,int(positionWeight),codingSetValueName))
                decoratedCodingSetValueNames.sort()
                groupNames = [entry[0] for entry in decoratedCodingSetValueNames]
                codingSetValueNames = [entry[2] for entry in decoratedCodingSetValueNames]

                self.choices[attribute] = dict()
                id = self.callbacksDict['getNewIdCallback']()
                #id = 0
                i = 0
                for codingSetValueName in codingSetValueNames:
                    if groupNames[i] != None and (i == 0 or groupNames[i] != groupNames[i-1]):
                        tooltipText.append(None)
                        groupLabel = self.mainLogic.translateString(groupNames[i])
                        widget = wx.StaticText(self.panel, -1, groupLabel)
                        widget.SetForegroundColour('Blue')
                        widgets.append(widget) 
                    i += 1

                    name = self.mainLogic.crfData.joinCodingSetValueName(self.crfName,codingSetName,codingSetValueName)
                    value = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'value')

                    cblabel = self.mainLogic.translateString(value)
                    self.choices[attribute][id] = name

                    #widget = wx.CheckBox(self.panel, id, cblabel, name=attribute, size = wx.Size(width, -1))
                    widget = MLCheckBox(self.panel, id, cblabel, wrap=wrap, name=attribute, size = wx.Size(width, -1))

                    widget.Bind(wx.EVT_CHECKBOX, self.onChange)
 
                    if not ENFORCE_SYSTEM_FONT:
                        if ww == 'bold':
                            f = widget.GetFont()
                            f.SetWeight(wx.FONTWEIGHT_BOLD)
                            widget.SetFont(f)
                            
                        if ws != None:
                            f = widget.GetFont()
                            f.SetPointSize(ws)
                            widget.SetFont(f)

                    widgets.append(widget)

                    inputWidgets.append(widget)

                    labelValue = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,self.className,attribute,'label')
                    if not labelValue:
                        labelValue = self.mainLogic.crfData.getPropertyForClass(self.crfName,self.className,'label')
                    if labelValue:
                        labelText = self.mainLogic.translateString(labelValue)
                        tooltipTitle = "%s: %s" % (labelText, cblabel)
                    else:
                        tooltipTitle = "%s" % cblabel
                    tooltipText.append((tooltipTitle,self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'toolTip')))
                    id += 1

                    #pagelink = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'pagelink')
                    #if pagelink != None:
                    #    label = self.mainLogic.translateString(str(pagelink))
                    #    widget = wx.Button(self.panel, -1, label, size=wx.Size(-1,-1), name=pagelink)
                    #    widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
                    #    widgets.append(widget)
                    #    tooltipText.append(None)
                
            elif inputType == 'radio':

                try: 
                    width = int(element.get('width'))
                except: 
                    width = -1
 
                try: 
                    nogname =  element.get('nogname')
                except: 
                    nogname = None

                try:
                    wrap = int(element.get('wrap'))
                except:
                    wrap = -1

                codingSetFullName = self.mainLogic.dataSession.getCodingSetNameForAttribute(self.crfName,self.className,attribute,self.classInstanceNumber)

                codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
                codingSetValueNames = self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(self.crfName,codingSetName)
                if not codingSetValueNames:
                    self.classesWithNoCodingSet.append(self.className)
                    return
                decoratedCodingSetValueNames = []
                try:
                    for codingSetValueName in codingSetValueNames:
                        positionWeight = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'positionWeight')
                        groupName = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'groupName')
                        if nogname == "1":
                            groupName = None
                        if positionWeight == None or not positionWeight.isdigit():
                            positionWeight = 10000
                        decoratedCodingSetValueNames.append((groupName,int(positionWeight),codingSetValueName))
                    decoratedCodingSetValueNames.sort()
                    groupNames = [entry[0] for entry in decoratedCodingSetValueNames]
                    codingSetValueNames = [entry[2] for entry in decoratedCodingSetValueNames]
                except BaseException, e:
                    PsLogger().warning(['GuiGeneratorTag','ExceptionTag'], str(e))

                self.choices[attribute] = dict()
                id = self.callbacksDict['getNewIdCallback']()
                firstId = id
                #id = 0
                i = 0
                for codingSetValueName in codingSetValueNames:

                    if groupNames[i] != None and (i == 0 or groupNames[i] != groupNames[i-1]):
                        tooltipText.append(None)
                        groupLabel = self.mainLogic.translateString(groupNames[i])
                        widget = wx.StaticText(self.panel, -1, groupLabel)
                        widget.SetForegroundColour('Blue')
                        widgets.append(widget) 
                    i += 1

                    name = self.mainLogic.crfData.joinCodingSetValueName(self.crfName,codingSetName,codingSetValueName)
                    value = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'value')

                    cblabel = self.mainLogic.translateString(value)
                    self.choices[attribute][id] = name


                    codingSetFullName = self.mainLogic.dataSession.getCodingSetNameForAttribute(self.crfName,self.className,attribute,self.classInstanceNumber)
                    codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
                    labelValue = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,self.className,attribute,'label')
                    if not labelValue:
                        labelValue = self.mainLogic.crfData.getPropertyForClass(self.crfName,self.className,'label')
                    if labelValue:
                        labelText = self.mainLogic.translateString(labelValue)
                        tooltipTitle = "%s: %s" % (labelText, cblabel)
                    else:
                        tooltipTitle = "%s" % cblabel
                    tooltipProperty = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'toolTip')
                    if not tooltipProperty:
                        tooltipProperty = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,self.className,attribute,'toolTip')
                    tooltipText.append((tooltipTitle,tooltipProperty))

                    if id == firstId:
                        #widget = wx.RadioButton(self.panel, id, cblabel, style=wx.RB_GROUP, name=attribute, size=wx.Size(width,-1))
                        widget = MLRadioButton(self.panel, id, cblabel, wrap=wrap, style=wx.RB_GROUP, name=attribute, size=wx.Size(width,-1))
                    else:    
                        #widget = wx.RadioButton(self.panel, id, cblabel, name=attribute, size=wx.Size(width,-1))
                        widget = MLRadioButton(self.panel, id, cblabel, wrap=wrap, name=attribute, size=wx.Size(width,-1))

                    widget.SetValue(0)
                    widget.Bind(wx.EVT_MOUSE_EVENTS, self.radioHandler)
                    widgets.append(widget)
                    inputWidgets.append(widget)
                    id += 1
            
            elif inputType == 'select':

                try: 
                    width = int(element.get('width'))
                except: 
                    width = -1
 
                self.choices[attribute] = dict()
                choiceStrings = ['']

                codingSetFullName = self.mainLogic.dataSession.getCodingSetNameForAttribute(self.crfName,self.className,attribute,self.classInstanceNumber)
                codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
                codingSetValueNames = self.mainLogic.crfData.getCodingSetValueNamesForCodingSet(self.crfName,codingSetName)

                decoratedCodingSetValueNames = []
                for codingSetValueName in codingSetValueNames:
                    positionWeight = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'positionWeight')
                    if positionWeight == None or not positionWeight.isdigit():
                        decoratedCodingSetValueNames = []
                        break
                    decoratedCodingSetValueNames.append((int(positionWeight),codingSetValueName))
                if decoratedCodingSetValueNames:
                    decoratedCodingSetValueNames.sort()
                    codingSetValueNames = [entry[1] for entry in decoratedCodingSetValueNames]

                id = 1
                for codingSetValueName in codingSetValueNames:
                    value = self.mainLogic.crfData.getPropertyForCodingSetValue(self.crfName,codingSetName,codingSetValueName,'value')
                    translatedString = self.mainLogic.translateString(value)
                    name = self.mainLogic.crfData.joinCodingSetValueName(self.crfName,codingSetName,codingSetValueName)
                    self.choices[attribute][id] = name
                    choiceStrings.append(translatedString)
                    id += 1
                #widget = wx.ComboBox(self.panel, -1, choiceStrings[0], choices=choiceStrings ,style=wx.CB_DROPDOWN|wx.CB_READONLY, size=wx.Size(width,-1), name=attribute)
                widget = wx.Choice(self.panel, -1, choices=choiceStrings, size=wx.Size(width,-1), name=attribute)
                if choiceStrings == ['']:
                    widget.Show(False)
                
                #widget.Bind(wx.EVT_TEXT, self.onChange)
                widget.Bind(wx.EVT_CHOICE, self.onChange)
                widgets.append(widget)
                inputWidgets.append(widget)

            if not tooltipText:
                labelText = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,ifclass,attribute,'label')
                #descriptionText = self.mainLogic.crfData.getPropertyForAttribute(self.crfName,ifclass,attribute,'description')
                if labelText:
                    tooltipTitles = [self.mainLogic.translateString(labelText)] * len(widgets)
                else:
                    #tooltipTitles = [descriptionText] * len(widgets)
                    tooltipTitles = [""] * len(widgets)
                tooltipMessages = [""] * len(widgets)
                tooltipText = zip(tooltipTitles,tooltipMessages)

            for i in range(len(widgets)):
                widget = widgets[i]
                if tooltipText[i] == None:
                    continue
                title = tooltipText[i][0]
                text = tooltipText[i][1]
                if text == None:
                    text = ""
                self.createTooltip(widget,title,self.mainLogic.translateString(text))

            if self.inputWidgets.has_key(attribute):
                self.inputWidgets[attribute].extend(inputWidgets)
            else:
                self.inputWidgets[attribute] = inputWidgets
                self.inputTypes[attribute] = inputType
                self.inputWidgetsReadonlyState[attribute] = widgetReadonlyState

            if widgetReadonlyState: 
                for widget in inputWidgets:
                    widget.Disable()

            if widgets:
                self.sizers[attribute] = self.sizersFromRoot[-1]

            for widget in inputWidgets:
                widget.Bind(wx.EVT_ENTER_WINDOW,self.onEnterWidget)
                widget.Bind(wx.EVT_LEAVE_WINDOW,self.onLeaveWidget)
        
            if element.get('confirm') == "1":

                for widget in inputWidgets:
                    confirmText = element.get('confirmtext')
                    if confirmText:
                        confirmText = self.mainLogic.translateString(confirmText)
                    self.confirmWidgets[widget] = confirmText

        else:
            widgets = ItemGui.createWidgets(self,element,lblname)

            
            
        #Temporarily disable TAB navigation key for generated widgets
        if widgets:
            for widget in widgets:
                if str(type(widget)) == "<class 'mlradiobutton.MLRadioButton'>":
                    widget.Bind(wx.EVT_SET_FOCUS, self.onFocusGainedByRadio)
                else:
                    widget.Bind(wx.EVT_NAVIGATION_KEY, self.onNavigationKeyDown)
        return widgets

    
    def onFocusGainedByRadio(self, event):
        return
        
    def onNavigationKeyDown(self, event):
        event.Skip()
    
    def radioHandler(self, event):
        """handle deselection of radiobuttons"""
        if self.eventTypeIdToName[event.GetEventType()] != 'EVT_LEFT_UP':
            return
        
        obj =  event.GetEventObject()
        value = obj.GetValue()
        event.GetEventObject().SetFocus()
        if value == False:
            obj.SetValue(True)
        else:
            obj.SetValue(False)
        self.onChange(event)
 
    def onRefit(self, event):
        self.onChange(event)

    def onText(self, event):

        obj =  event.GetEventObject()
        attributeName = obj.GetName()
        widgetReadonlyState = self.inputWidgetsReadonlyState[attributeName]

        if widgetReadonlyState:
            if event.GetKeyCode() == 9:
                if event.ShiftDown():
                  obj.Navigate(wx.NavigationKeyEvent.IsBackward)
                else:
                  obj.Navigate()
        else:
            event.Skip()
 
    def changeBackgroundColor(self, obj, attributeName):
        widgetList = self.inputWidgets[attributeName]
        for widget in widgetList:
            value = widget.GetValue()
            if value:
                widget.SetBackgroundColour('white')
            else:
                widget.SetBackgroundColour(BACKGROUND_TEXTBOX_NOTFILLED)
        
    def onStartOnChange(self, event):
        attributeName = 'value'
        attributeValue, invalidValue = self.getValueForAttribute(attributeName) 
        if event:
            self.onChangeAttribute(event.GetEventObject(),attributeName,attributeValue,invalidValue)
        if event:
            event.Skip()
    
    def onChange(self, event):
        if not self.mainLogic.dataSession:
            event.Skip()
            return

        obj =  event.GetEventObject()
        attributeName = obj.GetName()
        attributeValue, invalidValue = self.getValueForAttribute(attributeName) 

        focused = self.panel.FindFocus()
        if focused and type(focused) == wx.TextCtrl and focused.GetName() != attributeName:
            self.callbacksDict['unfocusingCallback'](focused)

        self.onChangeAttribute(obj,attributeName,attributeValue,invalidValue)
        event.Skip()
   
    def onProcedureOnChange(self, event):
        if not self.mainLogic.dataSession:
            event.Skip()
            return
        obj =  event.GetEventObject()
        attributeName = obj.GetName()
        attributeValue, invalidValue = self.getValueForAttribute(attributeName) 

        focused = self.panel.FindFocus()
        if focused and type(focused) == wx.TextCtrl and focused.GetName() != attributeName:
            self.callbacksDict['unfocusingCallback'](focused)

        self.onChangeAttribute(obj,attributeName,attributeValue,invalidValue)
        event.Skip()
   
    def getValueForAttribute(self, attributeName):
        
        multiInstance = self.mainLogic.dataSession.isMultiInstance(self.crfName,self.className,attributeName)
        requiredForStatus = self.mainLogic.crfData.getPropertyForClass(self.crfName,self.className,'requiredForStatus')

        inputType = self.inputTypes[attributeName]
        widgetList = self.inputWidgets[attributeName]
        widgetReadonlyState = self.inputWidgetsReadonlyState[attributeName]

        if widgetReadonlyState:
            self.updateGui()
            return

        invalidValue = False

        attributeValue = []
        for widget in widgetList:
            try:
                value = widget.GetValue()
            except BaseException, e:
                PsLogger().warning(['GuiGeneratorTag','ExceptionTag'], str(e))
                print e
                try:
                    value = widget.GetSelection()
                except:
                    raise

            if inputType == 'date':
                try:
                    value = value.FormatISODate()
                except:
                    invalidValue = True
                    value = None
                #if value is None:
                #    if requiredForStatus:
                #        widget.SetBackgroundColour(BACKGROUND_TEXTBOX_NOTFILLED)
                #else:
                #    widget.SetBackgroundColour('white')
                attributeValue.append(value)
            
            elif inputType == 'select':
                #if value != "":
                if value != 0:
                    #value = self.choices[attributeName][widget.GetStrings().index(value)]
                    value = self.choices[attributeName][value]
                else:
                    invalidValue = True
                    value = None
                attributeValue.append(value)

            elif inputType == 'radio':
                if value == True:
                    value = self.choices[attributeName][widget.GetId()]
                    attributeValue.append(value)
                    break

            elif inputType == 'checkbox':
                if value == True:
                    value = self.choices[attributeName][widget.GetId()]
                    attributeValue.append(value)

            elif inputType == 'simplecheckbox':
                attributeValue.append(value)
                
            elif inputType == 'startwidget':
                value = repr(value)
                attributeValue.append(value)
                
            elif inputType == 'notebutton':
                value = widget.GetValue()
                attributeValue.append(value)
            else:
                if not inputType == 'textbox':
                    value = str(value).strip()
                value = self.mainLogic.dataSession.castValueForObjectAttribute(self.crfName,self.className,attributeName,value)
                if value in [None,""]:
                    invalidValue = True
                    value = None
                #if value is None:
                #    if requiredForStatus:
                #        widget.SetBackgroundColour(BACKGROUND_TEXTBOX_NOTFILLED)
                #else:
                #    widget.SetBackgroundColour('white')
                attributeValue.append(value)

        if not multiInstance:
            if attributeValue:
                attributeValue = attributeValue[0]
            else:
                attributeValue = None

        return attributeValue, invalidValue
 
    def onChangeAttribute(self, widget, attributeName, attributeValue, invalidValue = False):
        if widget in self.confirmWidgets:
            if [el for el in self.mainLogic.dataSession.undecryptableClasses if el['className'] == self.className and el['value'] == attributeValue]:
                return
            confirmText = self.confirmWidgets[widget]
            currentValues = self.mainLogic.dataSession.getAttributeValuesForObject(self.crfName,self.className,self.classInstanceNumber,attributeName)
            if currentValues:
                dlg = wx.MessageDialog(None,confirmText, "", wx.YES_NO | wx.ICON_QUESTION)
                dlg.Center()
                result = dlg.ShowModal()
                if result == wx.ID_NO:
                    self.updateGui()
                    return 
        if [el for el in self.mainLogic.dataSession.undecryptableClasses if el['className'] == self.className and el['value'] == attributeValue]:
            return
        updated = self.mainLogic.dataSession.updateData(self.crfName,self.className,self.classInstanceNumber,attributeName,attributeValue)
        if not updated and invalidValue:
            self.updateGui()

    def updateGui(self):

        #TODO: if timestamp is not last, we have to go in readonly mode (prepare readonly mode in buildGui)

        from mainlogic import _

        for attributeName in self.inputWidgets:
            inputType = self.inputTypes[attributeName]
            widgetList = self.inputWidgets[attributeName]
            if not widgetList:
                continue

            values = self.mainLogic.dataSession.getAttributeValuesForObject(self.crfName,self.className,self.classInstanceNumber,attributeName)

            multiInstance = self.mainLogic.dataSession.isMultiInstance(self.crfName,self.className,attributeName)
            codingSetName = None

            codingSetFullName = self.mainLogic.dataSession.getCodingSetNameForAttribute(self.crfName,self.className,attributeName,self.classInstanceNumber)
            if codingSetFullName:
                codingSetName = self.mainLogic.crfData.splitCodingSetName(codingSetFullName)[1]
            requiredForStatus = self.mainLogic.crfData.getPropertyForClass(self.crfName,self.className,'requiredForStatus')
            enabled = self.mainLogic.dataSession.getClassProperty(self.crfName,self.className,'enabled')

            if not multiInstance:
                if values:
                    value = values[0]
                else:
                    value = None
                if [el for el in self.mainLogic.dataSession.undecryptableClasses if el['className'] == self.className and el['value'] == value]:
                    value = _("ENCRYPTED")
                    
            widget = widgetList[0]

            if inputType in ['textbox','time']:
                widget.SetBackgroundColour('white')
                if value is None:
                    if requiredForStatus and enabled:
                        widget.SetBackgroundColour(BACKGROUND_TEXTBOX_NOTFILLED)
                    value = ""
                widget.SetValue(unicode(value))
                
            elif inputType == 'timer':
                widget.SetBackgroundColour('white')
                if value is None:
                    if requiredForStatus and enabled:
                        widget.SetBackgroundColour(BACKGROUND_TEXTBOX_NOTFILLED)
                    value = ""
                widget.SetValue(unicode(value))


            elif inputType == 'date':
                widget.SetBackgroundColour('white')
                if value is None:
                    value = ""
                    if requiredForStatus and enabled:
                        widget.SetBackgroundColour(BACKGROUND_TEXTBOX_NOTFILLED)
                thisdate = wx.DateTime()
                try:
                    thisdate.ParseFormat(value, '%Y-%m-%d')
                    widget.SetValue(thisdate)
                except:
                    pass

            elif inputType == 'radio':
                if not value:
                    value = None
                if value in (None,"ENCRYPTED",_("ENCRYPTED")):
                    for widget in widgetList:
                        widget.SetValue(False)
                else:
                    valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(value)
                    codingSetValue = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'value')
                    for widget in widgetList:
                        if self.choices[attributeName][widget.GetId()] == value: 
                            widget.SetValue(True)
                        else:
                            widget.SetValue(False)

            elif inputType == 'checkbox':
                for widget in widgetList:
                    widget.SetValue(False)
                for value in values:
                    if value in (None,"ENCRYPTED",_("ENCRYPTED")):
                        continue
                    #FIXME: avoid comparing translated strings, use @@@ strings
                    valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(value)
                    codingSetValue = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'value')
                    for widget in widgetList:
                        if self.choices[attributeName][widget.GetId()] == value: 
                            widget.SetValue(True)
                            break
            
            elif inputType == 'simplecheckbox':
                if value in (None, False, "ENCRYPTED", _("ENCRYPTED")):
                    widget.SetValue(False)
                else:
                    widget.SetValue(True)
                    
            elif inputType == 'startwidget':
                if value is None:
                    widget.SetValue(dict())
                else:
                    exec("value = " + value)
                    widget.SetValue(value)
                    
            elif inputType == 'notebutton':
                if value is None:
                    widget.SetValue([])
                else:
                    widget.SetValue(value)
            
            elif inputType == 'select':
                if value in (None,"ENCRYPTED",_("ENCRYPTED")):
                    #widget.SetValue("")
                    widget.SetSelection(0)
                else:
                    valueCrfName, valueCodingSetName, valueCodingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(value)
                    codingSetValue = self.mainLogic.crfData.getPropertyForCodingSetValue(valueCrfName,valueCodingSetName,valueCodingSetValueName,'value')
                    #widget.SetValue(self.mainLogic.translateString(codingSetValue))
                    widget.SetSelection(widget.GetStrings().index(self.mainLogic.translateString(codingSetValue)))

        ItemGui.updateGui(self)

        self.evaluateVisibility()
        self.evaluateEnabledState()
        #TODO: move from here to datasession once we have notification-based updates
        self.evaluateCodingSetStates()
        #TODO: to be safe we call this one again (it is called first in ItemGui.updateGui)
        self.evaluateDynCodingSetStates()

    def evaluateVisibility(self):
        result = self.mainLogic.dataSession.getClassProperty(self.crfName,self.className,'visibility')
        if result != None:
            self.panel.Show(result)
            return
        self.panel.Show(True)

    def evaluateEnabledState(self):
        result = self.mainLogic.dataSession.getClassProperty(self.crfName,self.className,'enabled')
        if result != None:
            if result:
                for child in self.panel.GetChildren():
                    if type(child) == wx.StaticText:
                        continue
                    child.SetForegroundColour(wx.BLACK)
            else:
                for child in self.panel.GetChildren():
                    if type(child) == wx.StaticText:
                        continue
                    child.SetForegroundColour(wx.LIGHT_GREY)
            self.panel.Enable(result)
            return
        self.panel.Enable(True)

    #def evaluateCodingSetVisibility(self,itemValue):
    #    evaluator = self.mainLogic.evaluator
    #    itemValue = int(itemValue)
    #    if itemValue in self.mainLogic.crfData.codingSetValuesProperties['visible']:
    #        expression = self.mainLogic.crfData.codingSetValuesProperties['visible'][itemValue]
    #        result = bool(evaluator.eval(expression))
    #    return result

    #def evaluateCodingSetEnabledState(self,itemValue):
    #    evaluator = self.mainLogic.evaluator
    #    itemValue = int(itemValue)
    #    if itemValue in self.mainLogic.crfData.codingSetValuesProperties['enabled']:
    #        expression = self.mainLogic.crfData.codingSetValuesProperties['enabled'][itemValue]
    #        result = bool(evaluator.eval(expression))
    #    return result

    ###################################################################
    
    def evaluateCodingSetStates(self):
        result = self.mainLogic.dataSession.getClassProperty(self.crfName,self.className,'visibility')
        if not result:
            return
        self.mainLogic.beginCriticalSection()
        anyUpdated = False
        evaluator = self.mainLogic.evaluator
        for attributeName in self.choices:
            choiceDict = self.choices[attributeName]
            widgets = self.inputWidgets[attributeName]
            inputType = self.inputTypes[attributeName]
            sizer = self.sizers[attributeName]
            if inputType == 'select':
                widget = widgets[0]
                selectChoices = choiceDict.keys()
            for key in choiceDict:
                itemValue = choiceDict[key]
                if itemValue == None:
                    continue

                visible, enabled, updated = self.mainLogic.dataSession.evaluateCodingSetStates(self.crfName,self.className,attributeName,self.classInstanceNumber,itemValue)
                if updated:
                    anyUpdated = True
                if inputType == 'select':
                    if visible == False or enabled == False:
                        selectChoices.remove(key)
                else:
                    for widget in widgets:
                        if widget.GetId() == key:
                            widget.Show(visible)
                            widget.Enable(enabled)
                            if enabled:
                                widget.SetForegroundColour(wx.BLACK)
                            else:
                                widget.SetForegroundColour(wx.LIGHT_GREY)
            try:
                sizer.Compact()
            except:
                pass
            if inputType == 'select' and selectChoices != choiceDict.keys():
                widget.Clear()
                widget.Append('')
                for choice in selectChoices:
                    widget.Append(choice)
        if anyUpdated:
            self.mainLogic.dataSession.evaluateCalculated(self.crfName)
            self.mainLogic.dataSession.evaluateErrors(self.crfName)
            self.mainLogic.dataSession.postUpdateDataNotification()
        self.mainLogic.endCriticalSection()
 

class GuiGenerator:

    def __init__(self,rootPanel,rootSizer,mainLogic,showPageCallback):
        from mainlogic import _
        self.classInterfaceXML = dict()
        self.itemInterfaceXML = dict()
        self.objectGuis = dict()
        self.itemGuis = []
        self.mainLogic = mainLogic
        self.rootPanel = rootPanel
        self.rootSizer = rootSizer
        self.currentCrfName = None
        self.currentPageName = None
        self.currentPageNameSuffix = None
        self.currentTimeStampAttributeFullName = None
        self.currentTimeStamp = None
        self.showPageCallback = showPageCallback
        self.interfacePanel = None

        self.showComplete = False
        self.showIncomplete = True

        #self.inspector = wx.Frame(rootPanel, style=wx.FRAME_FLOAT_ON_PARENT|wx.FRAME_NO_TASKBAR|wx.POPUP_WINDOW)
        self.currentWidgetId = 0
        self.needsRebuild = False
        self.showingSummaryPage = False

        self.sizersFromRoot = []
        self.callbacksDict = {
                              #'onChangeCallback':self.onChangeCallback, 
                              'onAddDynInterfaceCallback':self.onAddDynInterfaceCallback, 
                              'onRemoveDynInterfaceCallback':self.onRemoveDynInterfaceCallback, 
                              'onDynNumberSetCallback':self.onDynNumberSetCallback, 
                              'onCreateObjectGuiCallback':self.onCreateObjectGuiCallback,
                              'onPageLinkCallback':self.onPageLinkCallback,
                              'onUrlButtonCallback':self.onUrlButtonCallback,
                              'onCursorMoveInContainer':self.onCursorMoveInContainer,
                              'onShowDocumentationCallback':self.onShowDocumentationCallback,
                              'onHideDocumentationCallback':self.onHideDocumentationCallback,
                              'getNewIdCallback':self.getNewIdCallback,
                              'unfocusingCallback':self.unfocusingCallback
                             }

        for crfName in self.mainLogic.crfData.getCrfNames():
            self.loadInterfaceString(crfName,self.mainLogic.interfacesXML[crfName])

        self.mainLogic.notificationCenter.addObserver(self,self.onPageShouldBeRebuilt,"PageShouldBeRebuilt")
        self.mainLogic.notificationCenter.addObserver(self,self.onStatusUpdated,"StatusHasBeenUpdated")
        self.mainLogic.notificationCenter.addObserver(self,self.onTimeStampUpdated,"TimeStampHasBeenUpdated")

    def removeObservers(self):
        self.mainLogic.notificationCenter.removeObserver(self)

    def getNewIdCallback(self):
        self.currentWidgetId += 1
        return self.currentWidgetId

    def unfocusingCallback(self,focusedWidget):
        if focusedWidget:
            attributeName = focusedWidget.GetName()
            event = wx.FocusEvent(wx.wxEVT_KILL_FOCUS)
            event.SetEventObject(focusedWidget)
            for crfName,className,classInstanceNumber in self.objectGuis:
                objectGui = self.objectGuis[(crfName,className,classInstanceNumber)]
                if attributeName in objectGui.inputWidgets and focusedWidget in objectGui.inputWidgets[attributeName]:
                    attributeValue, invalidValue = objectGui.getValueForAttribute(attributeName)
                    objectGui.onChangeAttribute(focusedWidget,attributeName,attributeValue,invalidValue)

    
    def loadInterfaceString(self, crfName, xml):

        self.classInterfaceXML[crfName] = dict()
        self.itemInterfaceXML[crfName] = dict()
        tree = xml
        for interface in tree.findall("interface"):
            ifclass = interface.get("class")
            ifitem = interface.get("item")
            ifname = interface.get("name")
            xmlFragment = interface
            if ifclass:
                self.classInterfaceXML[crfName][(ifclass,ifname)] = xmlFragment
            elif ifitem:
                self.itemInterfaceXML[crfName][(ifitem,ifname)] = xmlFragment

    def onPageShouldBeRebuilt(self,notifyingObject,userInfo=None):
        self.needsRebuild = True

    def onTimeStampUpdated(self,notifyingObject,userInfo=None):
        self.rebuildPage()
 
    def onStatusUpdated(self,notifyingObject):
        if self.showingSummaryPage:
            self.showSummaryPage(self.currentCrfName)
 
    def updateGui(self):
        if not self.interfacePanel:
            return

        #if self.needsRebuild:
        #    self.needsRebuild = False
        #    self.rebuildPage()
        #    return

        for itemGui in self.itemGuis:
            itemGui.updateGui()

        self.interfacePanel.Layout()
        #TODO: use notifications
        self.rootPanel.SetupScrolling(scrollToTop=False)
        self.interfacePanel.Refresh()

    def onShowDocumentationCallback(self,message):
        userInfo = {'message':message}
        self.mainLogic.notificationCenter.postNotification("ShowDocumentation",self,userInfo)

    def onHideDocumentationCallback(self):
        self.mainLogic.notificationCenter.postNotification("HideDocumentation",self)

    def onPageLinkCallback(self,pageName,timeStamp,evaluateTimeStamp=None,onclick=None,crfName=None,className=None,classInstanceNumber=None):
        #TODO: either notify somebody or do this by sending notification (e.g. to PSEditor)
        #self.showPage(self.mainLogic.pagesXML[self.mainLogic.currentCrf][pageName]['xml'])
        if evaluateTimeStamp:
            timeStamp = self.mainLogic.evaluator.eval(evaluateTimeStamp,lhsCrfName=crfName,lhsClassName=className,lhsClassInstanceNumber=classInstanceNumber,noCache=True)
        if onclick:
            self.mainLogic.evaluator.eval(onclick,lhsCrfName=crfName,lhsClassName=className,lhsClassInstanceNumber=classInstanceNumber,noCache=True)
        self.showPageCallback(self.currentCrfName,pageName,timeStamp)
        
    def onUrlButtonCallback(self,evaluateParameters,crfName=None,className=None,classInstanceNumber=None):
        #TODO: either notify somebody or do this by sending notification (e.g. to PSEditor)
        #self.showPage(self.mainLogic.pagesXML[self.mainLogic.currentCrf][pageName]['xml'])
        print evaluateParameters
        if evaluateParameters:
            return self.mainLogic.evaluator.eval(evaluateParameters,lhsCrfName=crfName,lhsClassName=className,lhsClassInstanceNumber=classInstanceNumber,noCache=True)
        #self.showPageCallback(self.currentCrfName,pageName)

    def onCursorMoveInContainer(self,direction,containerCrfName,containerClassName,containerAttributeName,cursorCrfName,cursorClassName,cursorAttributeName):
        objectCodes = self.mainLogic.dataSession.getAttributeValuesForClass(containerCrfName,containerClassName,containerAttributeName)
        cursorObjectCodes = self.mainLogic.dataSession.getAttributeValuesForClass(cursorCrfName,cursorClassName,cursorAttributeName)
        if not objectCodes:
            return

        if not cursorObjectCodes or not cursorObjectCodes[0] in objectCodes:
            if direction == 'forward':
                cursorObjectCode = objectCodes[0]
            elif direction == 'backward':
                cursorObjectCode = objectCodes[-1]
        else:
            cursorObjectCode = cursorObjectCodes[0]
            if direction == 'forward':
                cursorObjectCode = objectCodes[(objectCodes.index(cursorObjectCode)+1)%len(objectCodes)]
            elif direction == 'backward':
                cursorObjectCode = objectCodes[(objectCodes.index(cursorObjectCode)+len(objectCodes)-1)%len(objectCodes)]
        cursorObjectCodes = [cursorObjectCode]
        self.mainLogic.dataSession.updateData(cursorCrfName,cursorClassName,1,cursorAttributeName,cursorObjectCodes)
        
        self.rebuildPage()

    def onAddDynInterfaceCallback(self,containerCrfName,containerClassName,containerAttributeName,crfName,className,attributeName,itemValue):
        self.mainLogic.beginCriticalSection()
        classInstanceNumber = self.mainLogic.dataSession.addNewObjectToContainer(crfName,className,containerCrfName,containerClassName,containerAttributeName,evaluateGlobals=True)
        self.mainLogic.dataSession.updateData(crfName,className,classInstanceNumber,attributeName,itemValue)
        self.mainLogic.endCriticalSection()
        self.rebuildPage()

    def onRemoveDynInterfaceCallback(self,crfName,className,classInstanceNumber,containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName):
        self.mainLogic.beginCriticalSection()
        self.mainLogic.dataSession.removeObjectInContainer(crfName,className,classInstanceNumber,containerCrfName,containerClassName,containerAttributeName,evaluateGlobals=True,notifyUpdateData=True)
        self.mainLogic.endCriticalSection()
        self.rebuildPage()

    def onDynNumberSetCallback(self,crfName,containerClassName,containerAttributeName,className,number):
        return
    #    self.mainLogic.beginCriticalSection()
    #    #for i in range(number):
    #    classInstanceNumber = self.mainLogic.dataSession.addNewObjectToContainer(crfName,className,crfName,containerClassName,containerAttributeName)
    #    self.mainLogic.dataSession.updateData(crfName,className,classInstanceNumber,'pdnHospitalizationStartDate','2011-01-01')
    #    #if numberOfHospitalizations == []:
    #    #    updateData('domus.pdnHospitalizationList.pdnHospitalizationList',[])
    #    #else:
    #    #    numberOfHospitalizations = numberOfHospitalizations[0]
    #    #    hospitalizationList = |domus.pdnHospitalizationList.pdnHospitalizationList|
    #    #    hospitalizationListLength = len(hospitalizationList)
    #    #    if hospitalizationListLength == numberOfHospitalizations:
    #    #        pass
    #    #    elif hospitalizationListLength > numberOfHospitalizations:
    #    #        updateData('domus.pdnHospitalizationList.pdnHospitalizationList',hospitalizationList[:numberOfHospitalizations])
    #    #    else:
    #    #        helperDataSession = helperMainLogic.dataSession
    #    #        for i in range(numberOfHospitalizations - hospitalizationListLength):
    #    #            helperDataSession.addNewObjectToContainer(crfName,className,crfName,containerClassName,containerAttributeName)
    #    self.mainLogic.dataSession.evaluateGlobals()
    #    self.mainLogic.endCriticalSection()
    #    self.rebuildPage()

    def onCreateObjectGuiCallback(self,containerCrfName,containerClassName,containerAttributeName,interfaceName,parent,sizer):

        dataSession = self.mainLogic.dataSession
        containerClassInstanceNumbers = dataSession.getInstanceNumbersForClass(containerCrfName,containerClassName)

        if len(containerClassInstanceNumbers) > 1:
            print "Error: container class %s should not have more than one instance", containerClassName
            return
        if not containerClassInstanceNumbers:
            containerClassInstanceNumbers = dataSession.registerSingleInstanceNumberForClass(containerCrfName,containerClassName)
        containerClassInstanceNumber = containerClassInstanceNumbers[0]

        #TODO: check that container attribute is of type object
        attributeValues = dataSession.getAttributeValuesForObject(containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName)

        for objectCode in attributeValues:

            classInfo = dataSession.getClassInfoForObjectCode(objectCode)
            if not classInfo:
                continue

            crfName = classInfo['crfName']
            className = classInfo['className']
            classInstanceNumber = classInfo['classInstanceNumber']
            #print crfName, className, classInstanceNumber
            #print self.classInterfaceXML[crfName]
            objectGui = ObjectGui(self.mainLogic,crfName,className,classInstanceNumber,interfaceName,self.classInterfaceXML[crfName][(className,interfaceName)],self.callbacksDict)
            objectGui.setContainerClassInfo(containerCrfName,containerClassName,containerClassInstanceNumber,containerAttributeName)
            self.objectGuis[(crfName,className,classInstanceNumber)] = objectGui
            self.itemGuis.append(objectGui)
            objectGui.buildGui(parent,sizer)

    def iterate(self, crfName, item):

        if item.tag in ('row','column'):
            try: 
                n = int(item.get('n'))
            except: 
                n = 1
            try: 
                maxcolitems = int(item.get('maxcolitems'))
            except: 
                maxcolitems = 0
            type = item.get('type')
            if type in (None,'Flex'):
                #sizerClass = wx.FlexGridSizer
                sizerClass = PSFlexGridSizer
            elif type == 'Grid':
                sizerClass = PSGridSizer
            if item.tag == 'row':
                sizer = sizerClass(n,0,maxcolitems)
            elif item.tag == 'column':
                sizer = sizerClass(0,n,maxcolitems)
            try:
                width = int(item.get('width'))
            except:
                width = 200
            sizer.SetMinSize(wx.Size(width,-1))
            self.sizersFromRoot[-1].AddSpacer(3)
            self.sizersFromRoot[-1].Add(sizer)
            self.sizersFromRoot.append(sizer)

        elif item.tag == 'box':
            label = item.get('label')
            if label:
                labelText = self.mainLogic.translateString(label)
            else:
                label = ''
                labelText = ''
            try:
                width = int(item.get('width'))
            except:
                width = -1
            widget = wx.StaticBox(self.interfacePanel, -1, labelText, name=label, size=wx.Size(width,-1))
            widget.SetWindowVariant(GUI_WINDOW_VARIANT)
            sizer = wx.StaticBoxSizer(widget, wx.VERTICAL)
            self.sizersFromRoot[-1].Add(sizer,flag=wx.EXPAND)
            self.sizersFromRoot.append(sizer)

        elif item.tag == 'spacer':
            try: 
                size = int(item.get('size'))
            except: 
                size = 5
            self.sizersFromRoot[-1].AddSpacer(size)
            return

        elif item.tag == 'interface':
            self.createInterface(crfName,item)
            return

        elif item.tag == 'linepanel':           
            try: 
                width = int(item.get('width'))
            except: 
                width = -1
            try: 
                height = int(item.get('height'))
            except: 
                height = -1
            widget = wx.Panel(self.interfacePanel, -1, size=wx.Size(width,height))
            widget.SetBackgroundColour('gray')
            self.sizersFromRoot[-1].Add(widget,flag=wx.EXPAND)
            return
 
        elif item.tag == 'comment':
            return

        for child in item.getchildren():
            self.iterate(crfName,child)

        if item.tag in ('row','column','box'):
            self.sizersFromRoot.pop()

    def createInterface(self,crfName,item):
        ifclass = item.get('class')
        ifitem = item.get('item')
        ifname = item.get('name')
        ifinstancenumber = 1
        if ifclass:
            objectGui = ObjectGui(self.mainLogic,crfName,ifclass,ifinstancenumber,ifname,self.classInterfaceXML[crfName][(ifclass,ifname)],self.callbacksDict)
            self.objectGuis[(crfName,ifclass,ifinstancenumber)] = objectGui
            self.itemGuis.append(objectGui)
            objectGui.buildGui(self.interfacePanel,self.sizersFromRoot[-1])
        else:
            if ifitem:
                xmlFragment = self.itemInterfaceXML[crfName][(ifitem,ifname)]
            else:
                xmlFragment = item
            itemGui = ItemGui(self.mainLogic,crfName,xmlFragment,self.callbacksDict)
            self.itemGuis.append(itemGui)
            itemGui.buildGui(self.interfacePanel,self.sizersFromRoot[-1])

        #for itemGui in self.itemGuis:
        #    itemGui.buildGui(self.rootPanel,self.sizer[-1])

    def rebuildPage(self):
        if not self.currentPageName:
            return
        found = False
        for key in self.mainLogic.pageHierarchyExpanded[self.currentCrfName]:
            for (currentName, currentNameSuffix, currentTimeStampAttributeFullName, currentTimeStamp) in self.mainLogic.pageHierarchyExpanded[self.currentCrfName][key]:
                if currentName == self.currentPageName and currentTimeStamp == self.currentTimeStamp:
                    found = True
                    self.currentPageNameSuffix = currentNameSuffix
                    break
            if found:
                break
        self.showPage(self.currentCrfName,self.currentPageName,self.currentPageNameSuffix,self.currentTimeStampAttributeFullName,self.currentTimeStamp)

    def pageLinkClicked(self,event):
        button = event.GetEventObject()
        timeStamp = None
        try:
            #bitmapButton does not have timeStamp but we should find the proper one
            if type(button) is wx._controls.BitmapButton:
                if [el for el in self.mainLogic.pageHierarchyExpanded[self.currentCrfName] if button.GetName() in el]:
                    timeStamp = [el for el in self.mainLogic.pageHierarchyExpanded[self.currentCrfName] if button.GetName() in el and el[3] == self.currentTimeStamp][0][3]
            else:
                timeStamp = button.timeStamp
        except:
            pass
        self.onPageLinkCallback(button.GetName(),timeStamp,None,None)
        
    def urlButtonClicked(self,event):
        button = event.GetEventObject()
        self.onUrlButtonCallback(button.GetName())

    def killFocus(self):
        focusedWindow = self.rootPanel.FindFocus()
        if focusedWindow:
            event = wx.FocusEvent(wx.wxEVT_KILL_FOCUS)
            event.SetEventObject(focusedWindow)
            focusedWindow.ProcessEvent(event)

    def valueToUnicode(self,value):
        if value == None:
            return u''
        if type(value) == bool:
            if value:
                return self.mainLogic.translateString('Yes')
            else:
                return self.mainLogic.translateString('No')
        return unicode(value)

    def onShowComplete(self,event):
        self.showSummaryPage(self.currentCrfName,event.GetEventObject().GetValue(),self.showIncomplete)
    
    def onShowIncomplete(self,event):
        self.showSummaryPage(self.currentCrfName,self.showComplete,event.GetEventObject().GetValue())

    def statusActivPetal(self, msg, font,posSize):
        from mainlogic import _
        width = 400.0
        tableSizer = PSFlexGridSizer(0,2,0)
        
        dicoPetals = self.mainLogic.StatusPetal()
        
        viewStatus = ''
        if dicoPetals != {}:
            if len(dicoPetals) <= 1:
                if "core" not in dicoPetals:
                    viewStatus = "ok"
            else:
                viewStatus = "ok"
        if viewStatus == "ok":
            titlept = wx.StaticBox(self.rootPanel, -1, _("Summary petal status"))
            boxsizer = wx.StaticBoxSizer(titlept, wx.VERTICAL)
            posSize.Add(boxsizer,flag=wx.EXPAND|wx.LEFT , border=250)
            
            def OnSelect(event):
                ctrlev = event.GetEventObject()
                if not ctrlev.IsChecked():
                    ctrlev.SetValue(True)
            
            # titlept = wx.StaticText(self.rootPanel, -1, _("Summary petal status"))
            titlept.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
            # tableSizer.Add(titlept, 0, wx.ALL, 4)
            # tableSizer.AddSpacer(5)
            viewStatus = ''

            for petal in dicoPetals:
                if str(petal) != "core" and dicoPetals[petal] != '0' :
                    widgetString = "  %s  => Status %s: %s" % (_(str(petal)).capitalize(),dicoPetals[petal],self.mainLogic.translateString(msg[dicoPetals[petal]]))
                    # widget = wx.CheckBox(self.rootPanel, -1, widgetString, size=wx.Size(width,-1), name=petal)
                    widget = wx.StaticText(self.rootPanel, -1, widgetString, size=wx.Size(width,-1), name=petal)
                    # widget.SetValue(True)
                    widget.SetForegroundColour("#AA3333")
                    if not ENFORCE_SYSTEM_FONT:
                        widget.SetFont(font)
                    widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    # widget.Bind(wx.EVT_CHECKBOX,OnSelect)
                    boxsizer.Add(widget,flag=wx.EXPAND|wx.ALL, border=5)
                    
                    # widget.SetBackgroundColour(backcolor) 
            
                    # if not ENFORCE_SYSTEM_FONT:
                        # widget.SetFont(font)
                    # widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    # tableSizer.Add(widget,0,wx.ALL,4)
                    # tableSizer.AddSpacer(1)
            dicoPetals={}

    def showSummaryPage(self,crfName,showComplete=None,showIncomplete=None):

        self.currentCrfName = crfName
        self.currentPageName = None
        self.currentPageNameSuffix = None
        self.currentTimeStampAttributeFullName = None
        self.currentTimeStamp = None
 
        if showComplete != None:
            self.showComplete = showComplete
        if showIncomplete != None:
            self.showIncomplete = showIncomplete

        self.showingSummaryPage = True
        try:
            self.rootPanel.Freeze()
        except:
            return
        self.rootSizer.Clear(True)
        titleHorizontalSizer = wx.BoxSizer(wx.HORIZONTAL)
        """
        from mainlogic import _
        #widget = wx.Button(self.rootPanel, -1, u"\u2191", size=wx.Size(30,-1), name='')
        bmp_check = wx.Image(os.path.join(psc.imagesPath,'check.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        widget = wx.BitmapButton(self.rootPanel, -1, bitmap=bmp_check, size=(bmp_check.GetWidth()+10, bmp_check.GetHeight()+10), name='')
        widget.SetToolTip(wx.ToolTip(_("Go to the summary page")))
        widget.SetWindowVariant(GUI_WINDOW_VARIANT)
        widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
        widget.Disable()
        titleHorizontalSizer.Add(widget,0,flag=wx.RIGHT,border=10)
       
        bmp_check = wx.Image(os.path.join(psc.imagesPath,'left.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        widget = wx.BitmapButton(self.rootPanel, -1, bitmap=bmp_check, size=(bmp_check.GetWidth()+10, bmp_check.GetHeight()+10), name='')
        widget.SetToolTip(wx.ToolTip(_("Go to the upper page")))
        widget.SetWindowVariant(GUI_WINDOW_VARIANT)
        widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
        widget.Disable()
        titleHorizontalSizer.Add(widget,0,flag=wx.RIGHT,border=10)"""
 
        innerTitleSizer = wx.BoxSizer(wx.VERTICAL)

        titleHorizontalSizer.Add(innerTitleSizer)

        from mainlogic import _

        translatedPageName = self.mainLogic.translateString(self.mainLogic.crfData.getPropertyForCrf(crfName,'label'))
        translatedPageTitle = translatedPageName + ': ' + self.mainLogic.translateString(_('summary page'))
        title = wx.StaticText(self.rootPanel, -1, translatedPageTitle)
        title.SetFont(wx.Font(16, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        innerTitleSizer.Add(title)

        #widget = wx.Button(self.rootPanel, -1, u"\u2190", size=wx.Size(30,-1), name='')
        #widget = wx.Button(self.rootPanel, -1, "<-", size=wx.Size(30,-1), name='')

        status = self.mainLogic.dataSession.getAdmissionStatus(crfName)
        coreStatusStrings = {
            '1':"Errors or unaccepted warnings present",
            '2':"Compilation incomplete",
            '3':"Compilation complete (except suspension)",
            '4':"Compilation complete (including suspension)",
            '5':"Admission closed"}
        petalStatusStrings = {
            '0':"Petal disabled",
            '1':"Errors or unaccepted warnings present",
            '2':"Compilation incomplete",
            '3':"Compilation complete",
            '4':"Compilation complete (including suspension)",
            '5':"Admission closed"}
        
        coreStatusBackgroundColors = {
            '1':"#f94f6f",
            '2':"#fff88e",
            '3':"#fff88e",
            '4':"#8eff99",
            '5':""}
            
        petalStatusBackgroundColors = {
            '0':"",
            '1':"#f94f6f",
            '2':"#fff88e",
            '3':"#8eff99",
            '4':"#8eff99",
            '5':""}
            
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        statusBackgroundColors = coreStatusBackgroundColors
        statusStrings = coreStatusStrings
        # if crfName == psc.coreCrfName:
            # self.statusActivPetal(petalStatusStrings, font)
        if status != None:
            if crfName != psc.coreCrfName:
                statusStrings = petalStatusStrings
                statusBackgroundColors = petalStatusBackgroundColors
            breadcrumsString = "Status %s: %s" % (str(status),self.mainLogic.translateString(statusStrings[status]))
            breadcrumsText = wx.StaticText(self.rootPanel, -1, breadcrumsString)
            if statusBackgroundColors[status] != "":
                breadcrumsText.SetBackgroundColour(statusBackgroundColors[status])
            breadcrumsText.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.BOLD))
            innerTitleSizer.Add(breadcrumsText,5,flag=wx.TOP,border=5)

        self.rootSizer.Add(titleHorizontalSizer)
        self.rootSizer.AddSpacer(25)
 
        sizer = wx.BoxSizer(wx.VERTICAL)
        Hsizer = wx.BoxSizer(wx.HORIZONTAL)
        Hsizer.Add(sizer)
        if crfName == psc.coreCrfName:
            self.statusActivPetal(petalStatusStrings, font, Hsizer)
        
        self.rootSizer.Add(Hsizer)
        if status == '0':
            enabledText = self.mainLogic.crfData.getPropertyForCrf(crfName,'enabledText')
            if enabledText:
                enabledText = self.mainLogic.translateString(enabledText)
                enabledTextWidget = wx.StaticText(self.rootPanel, -1, enabledText)
                sizer.Add(enabledTextWidget)
            self.rootPanel.Layout()
            self.rootPanel.SetupScrolling(scrollToTop=False)
            self.rootPanel.Refresh()
            self.rootPanel.Thaw()
            return

        widget = wx.CheckBox(self.rootPanel, -1, _("Show complete"), size = wx.Size(-1, -1))
        widget.SetValue(self.showComplete)
        widget.Bind(wx.EVT_CHECKBOX, self.onShowComplete)
        widget.SetWindowVariant(GUI_WINDOW_VARIANT)
        sizer.Add(widget)
        sizer.AddSpacer(5)
 
        widget = wx.CheckBox(self.rootPanel, -1, _("Show incomplete"), size = wx.Size(-1, -1))
        widget.SetValue(self.showIncomplete)
        widget.Bind(wx.EVT_CHECKBOX, self.onShowIncomplete)
        widget.SetWindowVariant(GUI_WINDOW_VARIANT)
        
        sizer.Add(widget)
        sizer.AddSpacer(15)
 
        tableSizer = PSFlexGridSizer(0,2,0)
        self.rootSizer.Add(tableSizer)

        width = 300.0
        # font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)

        pagesToVisit = [('None',None,None,None)]
        depthFirstPages = []
        while pagesToVisit:
            parentName,parentNameSuffix,timeStampAttributeFullName,timeStamp = pagesToVisit.pop(0)
            depthFirstPages.append((parentName,parentNameSuffix,timeStampAttributeFullName,timeStamp))
            if (parentName,parentNameSuffix,timeStampAttributeFullName,timeStamp) in self.mainLogic.pageHierarchyExpanded[crfName]:
                childPages = self.mainLogic.pageHierarchyExpanded[crfName][(parentName,parentNameSuffix,timeStampAttributeFullName,timeStamp)][:]
                childPages.extend(pagesToVisit)
                pagesToVisit = childPages
        depthFirstPages.pop(0)

        compiledTree = []
        
        for pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp in depthFirstPages:
            pageTree = []
            pageXML = self.mainLogic.pagesXML[crfName][pageName]['xml']
            visibilityExpression = self.mainLogic.pagesXML[crfName][pageName]['visible']
            visible = True
            if visibilityExpression:
                visible = self.mainLogic.evaluator.eval(visibilityExpression)
            if not (visible or visible == None):
                continue
            compiledTree.append((pageName, pageNameSuffix, timeStamp, pageTree))

            # TODO: If not current timestamp, show only compiled (or even nothing, as a first iteration just keep the "open" timeStamp)

            pageElement = pageXML
            for interface in pageElement.getiterator("interface"):
                classNamesAndInstanceNumbers = []
                itemName = interface.get('item')
                if itemName != None:
                    attributeNames = self.mainLogic.crfData.getSortedAttributeNamesForClass(crfName,itemName)
                    if attributeNames == None:
                        continue
                    objectCodes = []
                    for attributeName in attributeNames:
                        dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,itemName,attributeName,'dataType')
                        if dataType == 'object' and self.mainLogic.dataSession.isMultiInstance(crfName,itemName,attributeName):
                            isCursor = self.mainLogic.crfData.getPropertyForAttribute(crfName,itemName,attributeName,'cursor')
                            if isCursor == "1":
                                continue
                            #TODO: assumption: container class has classInstanceNumber 1
                            values = self.mainLogic.dataSession.getAttributeValuesForClass(crfName,itemName,attributeName)
                            objectCodes.extend(values)
                    for objectCode in objectCodes:
                        classInfo = self.mainLogic.dataSession.getClassInfoForObjectCode(objectCode)
                        if classInfo == None:
                            print 'Empty class info for objectCode %s', objectCode
                            continue
                        className = classInfo['className']
                        classInstanceNumber = classInfo['classInstanceNumber']
                        result = self.mainLogic.dataSession.getClassProperty(crfName,className,'visibility')
                        if not result:
                            continue
                        result = not self.mainLogic.dataSession.getClassProperty(crfName,className,'enabled') and not self.mainLogic.crfData.getPropertyForClass(crfName,className,'keepValueIfDisabled')
                        if result:
                            continue
                        classNamesAndInstanceNumbers.append((className,classInstanceNumber))
                else:
                    className = interface.get('class')
                    if className == None:
                        continue
                    classNamesAndInstanceNumbers.append((className,1))

                for className, classInstanceNumber in classNamesAndInstanceNumbers:
                    
                    classTimeStamp = None
                    classTimeStampAttributeName = self.mainLogic.crfData.getPropertyForClass(crfName, className, 'timeStamp')
                    if classTimeStampAttributeName != None and classTimeStampAttributeName == timeStampAttributeFullName :
                        classTimeStamp = timeStamp
                        tsCrfName, tsClassName, tsAttributeName = self.mainLogic.crfData.splitAttributeName(classTimeStampAttributeName)
                        self.mainLogic.dataSession.updateData(tsCrfName,tsClassName,1,tsAttributeName,classTimeStamp,notifyUpdateData=False)

                    result = self.mainLogic.dataSession.getClassProperty(crfName,className,'visibility')
                    if not result:
                        continue
                    result = not self.mainLogic.dataSession.getClassProperty(crfName,className,'enabled') and not self.mainLogic.crfData.getPropertyForClass(crfName,className,'keepValueIfDisabled')
                    if result:
                        continue
                    requiredForStatus = self.mainLogic.crfData.getPropertyForClass(crfName,className,'requiredForStatus')
                    includeInSummary = self.mainLogic.crfData.getPropertyForClass(crfName,className,'includeInSummary')
                    if requiredForStatus == None and includeInSummary != "1":
                        continue
                    classTree = []
                    pageTree.append((className,classTree))
                    attributeNames = self.mainLogic.crfData.getSortedAttributeNamesForClass(crfName,className)
                    for attributeName in attributeNames:
                        if self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'excludeFromStatus'):
                            continue
                        attributeIncludeInSummary = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'includeInSummary')
                        if attributeIncludeInSummary == '0':
                            continue
                        attributeValues = self.mainLogic.dataSession.getAttributeValuesForObject(crfName,className,classInstanceNumber,attributeName, classTimeStamp)
                        if not self.showIncomplete and not attributeValues:
                            continue
                        if not self.showComplete and attributeValues:
                            continue
                        if not attributeValues and includeInSummary:
                            continue
                        classTree.append((attributeName,attributeValues))
 
        lastPageLabel = None
        
        for pageName, pageNameSuffix, timeStamp, pageTree in compiledTree:
            pageLabel = self.mainLogic.translateString(pageName)
            if pageNameSuffix != None:
                pageLabel = pageLabel + " - " + pageNameSuffix
            elif timeStamp != None:
                pageLabel = pageLabel + " - " + str(timeStamp)
               
            for className, classTree in pageTree:
                classLabel = self.mainLogic.crfData.getPropertyForClass(crfName,className,'label')
                if classLabel:
                    classLabel = self.mainLogic.translateString(classLabel).replace('\n', ' ')
                attributeLabelsAndValues = []
                for attributeName, attributeValues in classTree:
                    attributeLabel = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'label')
                    if not classLabel and not attributeLabel:
                        print 'WARNING: no class or attribute label for %s' % self.mainLogic.crfData.joinAttributeName(crfName,className,attributeName)
                    if attributeLabel:
                        attributeLabel = self.mainLogic.translateString(attributeLabel).replace('\n', ' ')
                    dataType = self.mainLogic.crfData.getPropertyForAttribute(crfName,className,attributeName,'dataType')
                    if dataType == 'codingset':
                        codingSetValues = []
                        for attributeValue in attributeValues:
                            try:
                                codingSetCrfName, codingSetName, codingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(attributeValue)
                                codingSetValue = self.mainLogic.crfData.getPropertyForCodingSetValue(codingSetCrfName,codingSetName,codingSetValueName,'value')
                                codingSetValues.append(codingSetValue)
                            except BaseException, e:
                                PsLogger().warning(['GuiGeneratorTag','ExceptionTag'], str(e))
                                print 'Cannot decode coding set value name %s for summary page' % str(attributeValue)
                        if codingSetValues:
                            attributeValues = [self.mainLogic.translateString(value) for value in codingSetValues if value]
                        else:
                            attributeValues = ""
                    elif dataType == 'datetime':
                        attributeValues = psevaluator.decode(attributeValues,self.mainLogic)
                    attributeLabelsAndValues.append((attributeLabel,attributeValues))

                if not attributeLabelsAndValues:
                    continue
                if pageLabel != lastPageLabel:
                    widget = wx.StaticText(self.rootPanel, -1, pageLabel, size=wx.Size(width,-1), name=pageName)
                    widget.timeStamp = timeStamp
                    widget.Wrap(width) 
                    if not ENFORCE_SYSTEM_FONT:
                        widget.SetFont(font)
                    widget.SetForegroundColour('Blue')
                    widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    widget.Bind(wx.EVT_LEFT_DCLICK, self.showPageHandler)
                    tableSizer.Add(widget,0,wx.ALL,4)
                    tableSizer.AddSpacer(1)
                    lastPageLabel = pageLabel
                classLabelSet = False
                if classLabel and not (len(attributeLabelsAndValues) == 1 and (attributeLabelsAndValues[0][0] == classLabel or attributeLabelsAndValues[0][0] == None)):
                    widget = wx.StaticText(self.rootPanel, -1, 4*' '+classLabel, size=wx.Size(width,-1), name=pageName)
                    widget.timeStamp = timeStamp
                    widget.Wrap(width) 
                    if not ENFORCE_SYSTEM_FONT:
                        widget.SetFont(font)
                    widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    if self.showIncomplete:
                        allComplete = True
                        for attributeLabelAndValues in attributeLabelsAndValues:
                            if not attributeLabelAndValues[1]:
                                allComplete = False
                                break
                        if not allComplete:
                            widget.SetForegroundColour('Red')
                    widget.Bind(wx.EVT_LEFT_DCLICK, self.showPageHandler)
                    tableSizer.Add(widget,0,wx.ALL,4)
                    tableSizer.AddSpacer(1)
                    classLabelSet = True
                for attributeLabelAndValues in attributeLabelsAndValues:
                    label = attributeLabelAndValues[0]
                    if not label and len(attributeLabelsAndValues) == 1:
                        label = classLabel
                    #if not label and len(pageTree) == 1:
                    if not label:
                        label = pageLabel
                    if not label:
                        continue
                    indent = 4
                    if classLabelSet:
                        indent = 8
                    widget = wx.StaticText(self.rootPanel, -1, indent*' '+label, size=wx.Size(width,-1), name=pageName)
                    widget.timeStamp = timeStamp
                    widget.Wrap(width) 
                    if not ENFORCE_SYSTEM_FONT:
                        widget.SetFont(font)
                    widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    if self.showIncomplete and not attributeLabelAndValues[1]:
                        widget.SetForegroundColour('Red')
                    widget.Bind(wx.EVT_LEFT_DCLICK, self.showPageHandler)
                    tableSizer.Add(widget,0,wx.ALL,4)
                    stringValues = '\n'.join([self.valueToUnicode(value) for value in attributeLabelAndValues[1]])
                    widget = wx.StaticText(self.rootPanel, -1, stringValues, size=wx.Size(width,-1), name=pageName)
                    widget.timeStamp = timeStamp
                    widget.Wrap(width) 
                    if not ENFORCE_SYSTEM_FONT:
                        widget.SetFont(font)
                    widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                    widget.Bind(wx.EVT_LEFT_DCLICK, self.showPageHandler)
                    tableSizer.Add(widget,0,wx.ALL,4)
        self.rootPanel.Layout()
        self.rootPanel.SetupScrolling(scrollToTop=False)
        self.rootPanel.Refresh()
        self.rootPanel.Thaw()

    def showPageHandler(self, event):
        widget = event.GetEventObject()
        pageName = widget.GetName()
        timeStamp = widget.timeStamp
        self.showPageCallback(self.currentCrfName,pageName,timeStamp)

    def showPageReadonly(self,crfName,pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp):
        self.showPage(crfName,pageName,pageNameSuffix,timeStampAttributeFullName=timeStampAttributeFullName,timeStamp=timeStamp,readonly=True)

    def showPage(self,crfName,pageName,pageNameSuffix=None,timeStampAttributeFullName=None,timeStamp=None,readonly=False,decoration=True):

        self.killFocus()

        if not self.mainLogic.dataSession:
            return

        if timeStampAttributeFullName:
            timeStampCrfName, timeStampClassName, timeStampAttributeName = self.mainLogic.crfData.splitAttributeName(timeStampAttributeFullName)
            self.mainLogic.dataSession.updateDataNoNotify(timeStampCrfName,timeStampClassName,1,timeStampAttributeName,timeStamp)

        if pageName not in self.mainLogic.pagesXML[crfName]:
            if self.currentPageName:
                onleave = self.mainLogic.pagesXML[self.currentCrfName][self.currentPageName]['onleave']
                if onleave:
                    self.mainLogic.evaluator.eval(onleave,noCache=True)
            self.currentCrfName = crfName
            self.currentPageName = None
            self.currentPageNameSuffix = None
            self.currentTimeStampAttributeFullName = None
            self.currentTimeStamp = None
            self.showSummaryPage(crfName)
            return

        self.showingSummaryPage = False
        onleave = None
        onenter = None

        if pageName != self.currentPageName or timeStamp != self.currentTimeStamp or crfName != self.currentCrfName:
            if self.currentPageName:
                onleave = self.mainLogic.pagesXML[self.currentCrfName][self.currentPageName]['onleave']
            onenter = self.mainLogic.pagesXML[crfName][pageName]['onenter']

        self.currentCrfName = crfName
        self.currentPageName = pageName
        self.currentPageNameSuffix = pageNameSuffix
        self.currentTimeStampAttributeFullName = timeStampAttributeFullName
        self.currentTimeStamp = timeStamp
        pageXML = self.mainLogic.pagesXML[crfName][pageName]['xml']

        if onleave:
            self.mainLogic.evaluator.eval(onleave,noCache=True)

        visibilityExpression = self.mainLogic.pagesXML[crfName][pageName]['visible']
        if visibilityExpression:
            visible = self.mainLogic.evaluator.eval(visibilityExpression)
        else:
            visible = True

        if onenter:
            self.mainLogic.evaluator.eval(onenter,noCache=True)

        #self.onChangePage()
        #self.rootSizer = wx.BoxSizer(wx.VERTICAL)
        #self.rootPanel.SetSizer(self.rootSizer)
        #self.rootPanel.Layout()

        self.objectGuis = dict()
        self.itemGuis = []

        pageNamesFromRoot = []
        parentName = pageName
        if decoration:
            parentNameSuffix = pageNameSuffix
            parentTimeStampAttributeFullName = timeStampAttributeFullName
            parentTimeStamp = timeStamp
            while parentName != 'None':
                pageNamesFromRoot.append((parentName,parentNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp))
                found = False
                for key in self.mainLogic.pageHierarchyExpanded[crfName]:
                    if (parentName,parentNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp) in self.mainLogic.pageHierarchyExpanded[crfName][key]:
                        parentName,parentNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp = key
                        found = True
                        break
                if not found:
                    timeStampTag = timeStamp
                    if timeStamp == None:
                        timeStampTag = 0
                    #raise Exception('Cannot reconstruct page hierarchy for page "%s" at timeStamp %d' % (pageName,timeStampTag))
                    print 'Cannot reconstruct page hierarchy for page "%s" at timeStamp %d' % (pageName,timeStampTag)
                    return

        #TODO: deal with crf names - add tag to xml
        #pageNamesFromRoot.append(crfName)
        pageNamesFromRoot.append((self.mainLogic.translateString(self.mainLogic.crfData.getPropertyForCrf(crfName,'label')),None,None,None))
        pageNamesFromRoot.reverse()

        translatedPageNamesFromRoot = []
        for name, nameSuffix, pageTimeStampAttributeFullName, pageTimeStamp in pageNamesFromRoot:
            if nameSuffix:
                translatedPageNamesFromRoot.append("%s - %s" % (self.mainLogic.translateString(name), nameSuffix))
            else:
                translatedPageNamesFromRoot.append(self.mainLogic.translateString(name))

        translatedPageName = self.mainLogic.translateString(pageName)
        if pageNameSuffix:
            translatedPageName = "%s - %s" % (self.mainLogic.translateString(pageName), pageNameSuffix)

        ### DIALOG
        #frame = wx.Frame(self.rootPanel,-1,style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        #self.rootPanel = scrolled.ScrolledPanel(frame,-1)
        #self.rootSizer = wx.BoxSizer(wx.VERTICAL)
        #self.rootPanel.SetSizer(self.rootSizer)
        ##self.rootPanel.Reparent(frame)
        #frame.Show()
        #frame.Fit()
        #frame.MakeModal()
        ###

        self.rootPanel.Freeze()

        try:
            self.rootSizer.Clear(True)

            self.titlePanel = self.rootPanel
            self.titleSizer = self.rootSizer
            self.interfacePanel = self.rootPanel
            self.interfaceSizer = self.rootSizer
            #self.titlePanel = self.interfacePanel
            #self.titleSizer = self.interfaceSizer
            #self.interfacePanel = self.titlePanel
            #self.interfaceSizer = self.titleSizer
 
            if decoration:
                titleHorizontalSizer = wx.BoxSizer(wx.HORIZONTAL)

                #widget = wx.Button(self.titlePanel, -1, u"\u2191", size=wx.Size(30,-1), name='')
                from mainlogic import _
                bmp_check = wx.Image(os.path.join(psc.imagesPath,'check.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                widget = wx.BitmapButton(self.titlePanel, -1, bitmap=bmp_check, size=(bmp_check.GetWidth()+10, bmp_check.GetHeight()+10), name='')
                widget.SetToolTip(wx.ToolTip(_("Go to the summary page")))
                widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
                if len(pageNamesFromRoot) == 1:
                    widget.Disable()
                titleHorizontalSizer.Add(widget,0,flag=wx.RIGHT,border=10)

                if len(pageNamesFromRoot) in (1,2):
                    pageName = ''
                else:
                    pageName = pageNamesFromRoot[-2][0]
 
                bmp_left = wx.Image(os.path.join(psc.imagesPath,'left.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                widget = wx.BitmapButton(self.titlePanel, -1, bitmap=bmp_left, size=(bmp_left.GetWidth()+10, bmp_left.GetHeight()+10), name=pageName)
                widget.SetToolTip(wx.ToolTip(_("Go to the upper page")))
                widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
                if len(pageNamesFromRoot) == 1:
                    widget.Disable()
                titleHorizontalSizer.Add(widget,0,flag=wx.RIGHT,border=10)

                innerTitleSizer = wx.BoxSizer(wx.VERTICAL)

                titleHorizontalSizer.Add(innerTitleSizer)

                title = wx.StaticText(self.titlePanel, -1, translatedPageName)
                title.SetFont(wx.Font(16, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
                innerTitleSizer.Add(title)
                   
                #bmp_left = wx.Image('images/left.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap()
                #widget = wx.BitmapButton(self.titlePanel, -1, bitmap=bmp_left, size=(bmp_left.GetWidth()+10, bmp_left.GetHeight()+10), name=pageName)
                #widget.SetWindowVariant(GUI_WINDOW_VARIANT)
                #widget.Bind(wx.EVT_BUTTON, self.pageLinkClicked)
                #if len(pageNamesFromRoot) == 1:
                #    widget.Disable()
                #innerTitleSizer.Add(widget,0,flag=wx.RIGHT,border=10)

                #breadcrumsString = u"\u2192".join(translatedPageNamesFromRoot)
                breadcrumsString = u"->".join(translatedPageNamesFromRoot)
                breadcrumsText = wx.StaticText(self.titlePanel, -1, breadcrumsString)
                breadcrumsText.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL))
                innerTitleSizer.Add(breadcrumsText,5,flag=wx.TOP,border=5)

                #self.titleSizer.Add(innerTitleSizer)
                #self.titleSizer.AddSpacer(25)
 
                self.titleSizer.Add(titleHorizontalSizer)
                self.titleSizer.AddSpacer(25)
           
                #line = wx.Panel(self.titlePanel, -1, size=wx.Size(-1,1))
                #line.SetBackgroundColour('gray')
                #self.titleSizer.Add(line,flag=wx.EXPAND)

            else:
                titleHorizontalSizer = wx.BoxSizer(wx.HORIZONTAL)
                innerTitleSizer = wx.BoxSizer(wx.VERTICAL)
                titleHorizontalSizer.Add(innerTitleSizer)
                title = wx.StaticText(self.titlePanel, -1, translatedPageName)
                title.SetFont(wx.Font(16, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
                innerTitleSizer.Add(title)
                self.titleSizer.Add(titleHorizontalSizer)
                self.titleSizer.AddSpacer(25)
 
            if visible:

                self.sizersFromRoot = [self.interfaceSizer]

                pageElement = pageXML
                self.iterate(crfName,pageElement)

                for el in self.itemGuis:
                    el.setTimeStamp(timeStampAttributeFullName,timeStamp)

            self.rootPanel.Layout()
            try:
                self.rootPanel.SetupScrolling(scrollToTop=False)
            except:
                pass
            actualWidth = self.rootPanel.GetSize().width
            minWidth = self.rootPanel.GetSizer().GetMinSize().width
            userInfo = {"minWidth":minWidth, "actualWidth":actualWidth}
            self.mainLogic.notificationCenter.postNotification("EnsureRightPanelVisibility",self,userInfo)
            self.rootPanel.Refresh()
            self.rootPanel.Thaw()
        except:
            self.rootPanel.Thaw()
            raise
    
    
