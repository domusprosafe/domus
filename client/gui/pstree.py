import wx
import sys
from psguiconstants import GUI_WINDOW_VARIANT
from notificationcenter import notificationCenter
from psevaluator import decodevalue
import psconstants as psc

class PSTree(wx.TreeCtrl):
    
    isDeletingAllItems = False
    """Albero di navigazione presente nel pannello sinistro dell'editor"""
    
    def __init__(self, parent, editor, mainLogic):
        
        wx.TreeCtrl.__init__(self,parent,-1,style = wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT)

        self.editor = editor

        self.SetWindowVariant(GUI_WINDOW_VARIANT)
        self.SetIndent(8) 
        self.mainLogic = mainLogic
        
        #TODO: put patient name and stuff outside the tree
        #title =  '%s %s' % (data['lastname'], data['firstname'])
        
        self.itemIds = []
        self.visibilityDict = dict()
        self.pageNamesToItemIds = dict()
        self.pageNamesToSuffixes = dict()
        self.crfNamesToItemIds = dict()
        self.keyAttributeFullNames = set()

        self.pageHierarchy = self.mainLogic.pageHierarchy
        self.pagesXML = self.mainLogic.pagesXML
        self.pagesToTimeStampAttributes = dict()
        self.loadTree() 
        #self.expandCrfs()  
        self.expandAllExpandable()  

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.itemChanged)
        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.itemChanging)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.itemExpandedOrCollapsed)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.forbidItemExpand)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.itemExpandedOrCollapsed)

        notificationCenter.addObserver(self,self.onDataUpdated,"DataHasBeenUpdated")
        notificationCenter.addObserver(self,self.onDataUpdated,"CrfEnabledHasBeenUpdated")
        notificationCenter.addObserver(self,self.onEditorClosing,"EditorIsClosing")
        notificationCenter.addObserver(self,self.onDynPageChanged,"DynPageHasChanged")
        notificationCenter.addObserver(self,self.onAttributeSet,"AttributeHasBeenSet")
    
        self.currentCrfName = None
        self.currentPageName = None
        self.currentTimeStamp = None
        
        self.allow = True
        if sys.platform in ['darwin']:
            self.allow = False
            self.Bind(wx.EVT_LEFT_UP, self.leftUp)

    def DeleteAllItems(self, *args, **kwargs):
        self.isDeletingAllItems = True
        return wx.TreeCtrl.DeleteAllItems(self, *args, **kwargs)

    def leftUp(self,event):
        itemId, where = self.HitTest(event.GetPosition())
        if where & wx.TREE_HITTEST_ONITEMLABEL:
            self.allow = True
            self.SelectItem(itemId)
            self.allow = False
        event.Skip()
        
    def expandAllExpandable(self):
        self.ExpandAll()
        for crf in self.pageNamesToItemIds.keys():
            for page in self.pagesXML[crf]:
                if self.pagesXML[crf][page]['unexpandable'] == '1' or self.pagesXML[crf][page]['collapsed'] == '1':
                    #plz collapse page
                    if 'dynpage' in self.pagesXML[crf][page]:
                        dynPageNames = self.getDynamicPageNames(crf,page)
                        if dynPageNames:
                            pageName = dynPageNames[0][1]
			else:
			    pageName = page
                    else:
                        pageName = page
                    for key in self.pageNamesToItemIds[crf].keys():
                        if pageName in key:
                            pageId = self.pageNamesToItemIds[crf][key]
                            self.Collapse(pageId)
    
    def forbidItemExpand(self, event):
        #pageName = self.GetItemData(event.GetItem())
        #pageId = event.GetItem()
        pageKey = None
        temporaryCrf = None
        for crf in self.pageNamesToItemIds.keys():
            if event.GetItem() in self.pageNamesToItemIds[crf].values():
                for key, id in self.pageNamesToItemIds[crf].iteritems():
                    if id == event.GetItem():
                        pageKey = key 
                        temporaryCrf = crf
                        break
        if pageKey:
            if self.pagesXML[temporaryCrf][pageKey[0]]['unexpandable']:
                event.Veto()
                return
        
    def itemExpandedOrCollapsed(self,event):
        self.InvalidateBestSize()

    def onEditorClosing(self,notifyingObject,userInfo=None):
        notificationCenter.removeObserver(self)

    def onDataUpdated(self,notifyingObject,userInfo=None):
        self.evaluateVisibility()
 
    def onAttributeSet(self,notifyingObject,userInfo=None):
        attributeFullName = self.mainLogic.crfData.joinAttributeName(userInfo['crfName'],userInfo['className'],userInfo['attributeName'])
        if attributeFullName not in self.keyAttributeFullNames:
            return
        #crfName,pageName,timeStampAttributeFullName,timeStamp = self.GetItemPyData(self.GetSelection())
        self.reloadTree()
        wx.CallAfter(self.editor.rightPanel.showCurrentPage)
        
        
    def reloadTree(self):
        self.Show(False)
        self.DeleteAllItems()
        self.loadTree()
        self.expandAllExpandable()
        self.Show(True)
    
    
    def onDynPageChanged(self,notifyingObject,userInfo=None):
        self.reloadTree()
        #wx.CallAfter(self.editor.rightPanel.showSummaryPage,userInfo['crfName'])
        #wx.CallAfter(self.selectPage,userInfo['crfName'],force=True)
        found = False
        pageNameFound = False
        maxTimeStamp = None
        for crfName in self.pageNamesToItemIds:
            if crfName != self.currentCrfName:
                continue
            for (pageName, timeStamp) in self.pageNamesToItemIds[crfName]:
                if pageName != self.currentPageName:
                    continue
                pageNameFound = True
                maxTimeStamp = max(timeStamp,maxTimeStamp)
                if timeStamp == self.currentTimeStamp:
                    found = True
        
        if 'pageName' in userInfo:
            self.currentPageName = '@@@%d@@@' % userInfo['pageName']
        if 'timeStamp' in userInfo:
            self.currentTimeStamp = userInfo['timeStamp']
        if found:
            wx.CallAfter(self.selectPage,self.currentCrfName,self.currentPageName,timeStamp=self.currentTimeStamp,force=True)
        elif pageNameFound:
            wx.CallAfter(self.selectPage,self.currentCrfName,self.currentPageName,timeStamp=maxTimeStamp,force=True)
        else:
            wx.CallAfter(self.editor.rightPanel.showSummaryPage,userInfo['crfName'])

    def addPageToTree(self,crfName,pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp,parentPageName,parentPageNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp):
        itemData = wx.TreeItemData()
        itemData.SetData((crfName,pageName,timeStampAttributeFullName,timeStamp))
        pageNameString = self.mainLogic.translateString(pageName)
        if pageNameSuffix:
            pageNameString = "%s - %s" % (pageNameString, pageNameSuffix)
        itemId = self.AppendItem(self.itemIds[-1],pageNameString,data=itemData)
        self.pageNamesToItemIds[crfName][(pageName,timeStamp)] = itemId
        self.visibilityDict[(crfName,parentPageName,parentTimeStamp)] = True
        self.itemIds.append(itemId)
        parentKey = (parentPageName,parentPageNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp)
        if parentKey not in self.mainLogic.pageHierarchyExpanded[crfName]:
            self.mainLogic.pageHierarchyExpanded[crfName][parentKey] = []
        self.mainLogic.pageHierarchyExpanded[crfName][parentKey].append((pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp))
        if crfName not in self.pageNamesToSuffixes:
            self.pageNamesToSuffixes[crfName] = dict()
        self.pageNamesToSuffixes[crfName][(pageName,timeStamp)] = pageNameSuffix
        self.iterate(crfName,pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp)
        self.itemIds.pop()

    def getDynamicPageNames(self,crfName,pageName):
        dynamicPageNames = []
        attributeFullName = self.pagesXML[crfName][pageName]['attribute']
        crfName, className, attributeName = self.mainLogic.crfData.splitAttributeName(attributeFullName)
        valuesDict = self.mainLogic.dataSession.getAllAttributeValuesForClass(crfName,className,attributeName,timeDict=True)
        if not valuesDict:
            return dict()
        timeStamps = self.mainLogic.dataSession.getAllTimeStampsForClass(crfName,className,sorted=True)
        for timeStamp in timeStamps:
            if not valuesDict[timeStamp]:
                continue
            pageCodingSetName = valuesDict[timeStamp][0]
            codingSetCrfName, codingSetName, codingSetValueName = self.mainLogic.crfData.splitCodingSetValueName(pageCodingSetName)
            dynamicPageName = self.mainLogic.crfData.getPropertyForCodingSetValue(codingSetCrfName,codingSetName,codingSetValueName,'value')
            dynamicPageNames.append([timeStamp,dynamicPageName])
        return dynamicPageNames

    def iterate(self,crfName,pageName='None',pageNameSuffix=None,parentTimeStampAttributeFullName=None,parentTimeStamp=None):
        if pageName not in self.pageHierarchy[crfName]:
            return
        for childPageName in self.pageHierarchy[crfName][pageName]:
            if 'dynpage' in self.pagesXML[crfName][childPageName]:
                currentonly = self.pagesXML[crfName][childPageName]['currentonly']
                dynamicPageNames = self.getDynamicPageNames(crfName,childPageName)
                pageAttributeFullName = self.pagesXML[crfName][childPageName]['attribute']
                pageCrfName, pageClassName, pageAttributeName = self.mainLogic.crfData.splitAttributeName(pageAttributeFullName)
                timeStampAttributeFullName = self.mainLogic.crfData.getPropertyForClass(pageCrfName,pageClassName,'timeStamp')
                for timeStamp, dynamicPageName in dynamicPageNames:
                    if currentonly == "1" and timeStamp != self.mainLogic.dataSession.getTimeStampForClass(pageCrfName,pageClassName):
                        continue
                    dynamicPageNameSuffix = unicode(timeStamp)
                    if 'appendtonamedefault' in self.pagesXML[crfName][childPageName] and self.pagesXML[crfName][childPageName]['appendtonamedefault'] != None: 
                        dynamicPageNameSuffix = self.mainLogic.translateString(self.pagesXML[crfName][childPageName]['appendtonamedefault'])
                    if 'appendtoname' in self.pagesXML[crfName][childPageName] and self.pagesXML[crfName][childPageName]['appendtoname'] != None: 
                        appendAttributeFullName = self.pagesXML[crfName][childPageName]['appendtoname']
                        self.keyAttributeFullNames.add(appendAttributeFullName)
                        appendCrfName, appendClassName, appendAttributeName = self.mainLogic.crfData.splitAttributeName(appendAttributeFullName)
                        appendAttributeValues = self.mainLogic.dataSession.getAttributeValuesForClass(appendCrfName,appendClassName,appendAttributeName,timeStamp)
                        if appendAttributeValues:
                            dynamicPageNameSuffix = decodevalue(appendAttributeValues[0])
                    self.addPageToTree(crfName,dynamicPageName,dynamicPageNameSuffix,timeStampAttributeFullName,timeStamp,pageName,pageNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp)
            else:
                self.addPageToTree(crfName,childPageName,None,parentTimeStampAttributeFullName,parentTimeStamp,pageName,pageNameSuffix,parentTimeStampAttributeFullName,parentTimeStamp)

    def setPageVisibility(self,crfName,pageName,parentPageName,timeStamp=None,parentTimeStamp=None):
        if (pageName,timeStamp) not in self.pageNamesToItemIds[crfName]:
            return
        itemId = self.pageNamesToItemIds[crfName][(pageName,timeStamp)]
        if self.itemIdsVisibility[(crfName,parentPageName,parentTimeStamp)] == False or (parentPageName=='None' and not self.mainLogic.dataSession.getCrfProperty(crfName,'enabled')):
            self.SetItemTextColour(itemId,(200,200,200))
            self.itemIdsVisibility[(crfName,pageName,timeStamp)] = False
        self.iterateVisibility(crfName,pageName,timeStamp)

    def iterateVisibility(self,crfName,pageName='None',parentTimeStamp=None):
        if pageName != 'None' and pageName not in self.pageHierarchy[crfName]:
            return
        for childPageName in self.pageHierarchy[crfName][pageName]:
            if 'dynpage' in self.pagesXML[crfName][childPageName]:
                dynamicPageNames = self.getDynamicPageNames(crfName,childPageName)
                for timeStamp, dynamicPageName in dynamicPageNames:
                    self.setPageVisibility(crfName,dynamicPageName,pageName,timeStamp,parentTimeStamp)
            else:
                self.setPageVisibility(crfName,childPageName,pageName,parentTimeStamp,parentTimeStamp)

    def evaluateVisibility(self):
        for crfName in self.crfNamesToItemIds:
            itemId = self.crfNamesToItemIds[crfName]
            visible = self.mainLogic.dataSession.getCrfProperty(crfName,'enabled')
            self.SetItemTextColour(itemId,'blue')
            self.itemIdsVisibility[(crfName,'None',None)] = True
            for pageName, timeStamp in self.pageNamesToItemIds[crfName]:
                itemId = self.pageNamesToItemIds[crfName][(pageName,timeStamp)]
                visibilityExpression = self.pagesXML[crfName][pageName]['visible']
                visible = True
                if visibilityExpression:
                    visible = self.mainLogic.evaluator.eval(visibilityExpression)
                if visible or visible == None:
                    self.SetItemTextColour(itemId,'black')
                    self.itemIdsVisibility[(crfName,pageName,timeStamp)] = True
                else:
                    self.SetItemTextColour(itemId,(200,200,200))
                    self.itemIdsVisibility[(crfName,pageName,timeStamp)] = False
            self.iterateVisibility(crfName)

    def loadTree(self):
        self.Freeze()
        self.isDeletingAllItems = False
        rootId = self.AddRoot("HiddenRoot")
        self.itemIds = [rootId]
        self.crfNamesToItemIds = dict()
        self.pageNamesToItemIds = dict()
        self.itemIdsVisibility = dict()
        for crfName in self.mainLogic.crfData.getCrfNames():
            itemData = wx.TreeItemData()
            itemData.SetData((crfName,'None','',None))
            crfLabel = self.mainLogic.translateString(self.mainLogic.crfData.getPropertyForCrf(crfName,'label'))
            itemId = self.AppendItem(self.itemIds[-1],crfLabel,data=itemData)
            self.crfNamesToItemIds[crfName] = itemId
            self.pageNamesToItemIds[crfName] = dict()
            self.itemIdsVisibility[(crfName,'None',None)] = True
            self.itemIds.append(itemId)
            self.mainLogic.pageHierarchyExpanded[crfName] = dict()
            self.iterate(crfName) 
            self.itemIds.pop()
        self.evaluateVisibility()
        self.Thaw()

    def expandChildren(self, treeItem):
        subItem = self.GetFirstChild(treeItem)[0]
        while subItem.IsOk():
            self.Expand(subItem)
            subItem = self.GetNextSibling(subItem)

    def expandCrfs(self): 
        self.Freeze()
        for crfName in self.crfNamesToItemIds:
            self.Expand(self.crfNamesToItemIds[crfName])
        self.expandChildren(self.crfNamesToItemIds[psc.coreCrfName])
        self.Thaw()
 
    def itemChanged(self,event):
        if not self.allow:
            event.Veto()
            return
        if self.isDeletingAllItems:
            return        
        crfName,pageName,timeStampAttributeFullName,timeStamp = self.GetItemPyData(self.GetSelection())
        if not self.mainLogic.dataSession:
            return
        pageNameSuffix = None
        if (pageName,timeStamp) in self.pageNamesToSuffixes[crfName]:
            pageNameSuffix = self.pageNamesToSuffixes[crfName][(pageName,timeStamp)]
        self.currentCrfName = crfName
        self.currentPageName = pageName
        self.currentTimeStamp = timeStamp
        self.editor.rightPanel.showPage(crfName,pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp)
        #self.evaluateVisibility()

    def itemChanging(self,event):
        if not self.allow:
            event.Veto()
            return
        if self.isDeletingAllItems:
            return 
        crfName,pageName,timeStampAttributeFullName,timeStamp = self.GetItemPyData(event.GetItem())
        acceptSelection = True
        if (crfName,pageName,timeStamp) in self.itemIdsVisibility:
            acceptSelection = self.itemIdsVisibility[(crfName,pageName,timeStamp)]
        if not acceptSelection:
            event.Veto() 

    def selectPage(self,crfName,pageName,timeStamp=None,force=False):
        if not pageName:
            itemId = self.crfNamesToItemIds[crfName]
        else:
            itemId = self.pageNamesToItemIds[crfName].get((pageName,timeStamp))
        if itemId != None and itemId != self.GetSelection():
            self.allow = True
            self.SelectItem(itemId)
            if sys.platform in ['darwin']:
                self.allow = False

