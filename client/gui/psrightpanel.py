import wx
from guigenerator import GuiGenerator
from psscrolledpanel import PSScrolledPanel
from psguiconstants import BACKGROUND_COLOUR

class PSRightPanel(PSScrolledPanel):
        
    def __init__(self, parent, mainLogic, showPageCallback):
        PSScrolledPanel.__init__(self, parent, -1)
        
        self.SetBackgroundColour(BACKGROUND_COLOUR)

        self.mainLogic = mainLogic

        self.showPageCallback = showPageCallback

        #staticBox = wx.StaticBox(self)       
        #sizer = wx.StaticBoxSizer(staticBox,wx.VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
        innerSizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(innerSizer,0,wx.ALL,20)

        #self.crfPanel = wx.Panel(self,-1)
        #self.crfPanel.SetMinSize((400,600))
        #self.crfPanel.SetBackgroundColour('white')

        #sizer.Add(self.crfPanel,flag=wx.ALL,border=10)

        self.guiGenerator = GuiGenerator(self,innerSizer,self.mainLogic,self.showPageCallback)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

        self.mainLogic.notificationCenter.addObserver(self,self.onDataUpdated,"DataHasBeenUpdated",self.mainLogic.dataSession)
        self.mainLogic.notificationCenter.addObserver(self,self.onDataNotUpdated,"DataCannotBeUpdated",self.mainLogic.dataSession)

        self.Layout()

    def removeObservers(self):
        self.guiGenerator.removeObservers()
        self.mainLogic.notificationCenter.removeObserver(self)

    def onDataUpdated(self, notifyingObject, userInfo=None):
        if self.guiGenerator.needsRebuild:
            wx.CallAfter(self.showCurrentPage)
            return
        self.guiGenerator.updateGui()
    
    def onDataNotUpdated(self, notifyingObject, userInfo=None):
        self.guiGenerator.updateGui()
        
    def onKeyDown(self,  event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
           self.showEvaluator(self,  None)
        event.Skip()
    
    def doAlert(self, event):
        print 'psrightpanel alert!'
       
    def showCurrentPage(self):
        self.guiGenerator.rebuildPage()
        self.mainLogic.notificationCenter.postNotification("PageHasChanged",self)

    def showSummaryPage(self,crfName):
        self.guiGenerator.showPage(crfName,'None')
        self.mainLogic.notificationCenter.postNotification("PageHasChanged",self)
 
    def showPage(self,crfName,pageName,pageNameSuffix=None,timeStampAttributeFullName=None,timeStamp=None):
        self.guiGenerator.showPage(crfName,pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp)
        self.mainLogic.notificationCenter.postNotification("PageHasChanged",self)
 
    def showPageReadonly(self,crfName,pageName,pageNameSuffix=None,timeStampAttributeFullName=None,timeStamp=None):
        self.guiGenerator.showPageReadonly(crfName,pageName,pageNameSuffix,timeStampAttributeFullName,timeStamp)
        self.mainLogic.notificationCenter.postNotification("PageHasChanged",self)
        
    def showEvaluator(self,  event):
        dlg = EvaluatorDialog(self)
        dlg.Show()
       
    def showSession(self,  event):
        dlg = SessionDialog(self)
        dlg.Show()









class PSRightPanelControls(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
         
        self.mainLogic = self.editor.mainLogic
                       
        sizer = wx.BoxSizer(wx.VERTICAL)
        btn = wx.Button(self, 10000, 'Reload Config')
        btn2 = wx.Button(self, 10001, 'Expressions')
        #session watcher
        btn3 = wx.Button(self, 10002, 'Session')
        
        self.Bind(wx.EVT_BUTTON, self.reloadConfig, id=10000)
        self.Bind(wx.EVT_BUTTON, self.editor.showEvaluator, id=10001)
        self.Bind(wx.EVT_BUTTON, self.editor.showSession, id=10002)
        sizer.Add(btn, 0, wx.ALIGN_CENTRE) 
        sizer.Add(btn2, 0, wx.ALIGN_CENTRE) 
        sizer.Add(btn3, 0, wx.ALIGN_CENTRE) 
        self.SetSizer(sizer)
        
    def reloadConfig(self,  event):
        """ricarica la configurazione"""
        #td = genThreadDialog(self.editor, _("Reloading configuration"), self.mainLogic.loadConfig)
        #loginResult = td.getResult()
        loginResult = self.mainLogic.loadConfig()



class EvaluatorDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=-1,  pos=wx.DefaultPosition,
                           size=wx.Size(400,300), style = wx.DEFAULT_DIALOG_STYLE,
                           name='dialog',  title="Evaluator")    
         
        self.mainLogic = self.editor.mainLogic
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.input = wx.TextCtrl(self, -1, "",  style=wx.TE_MULTILINE| wx.TE_PROCESS_TAB )
       
        self.button =wx.Button(self,  -1,  "Evaluate") 
        self.output = wx.TextCtrl(self, -1, "",)
        self.sizer.Add(self.input,  1,  wx.EXPAND)
        self.sizer.Add(self.button,  0  )
        self.sizer.Add(self.output,  1,  wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.Bind(wx.EVT_BUTTON, self.evaluate, self.button)
        self.Bind(wx.EVT_CHAR, self.skip)
        
    def evaluate(self, event):
        evaluator = self.mainLogic.evaluator
        
        expression = self.input.GetValue()
        result = evaluator.eval(expression)
        self.output.SetValue(str(result))
        
    def skip(self,  event):
        event.Skip()

        
#import UltimateListCtrl as ULC
        
class SessionDialog(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=-1,  pos=wx.DefaultPosition,
                           size=wx.Size(400,300), style = wx.DEFAULT_FRAME_STYLE,
                           name='Session_evaluator',  title="Session")    
        self.mainLogic = self.editor.mainLogic
        
        self.nbook = wx.Notebook(self, -1)
        objPanel = wx.Panel(self.nbook,  -1)
        attrPanel = wx.Panel(self.nbook,  -1)
                
        self.nbook.AddPage(objPanel, "Objects")
        self.nbook.AddPage(attrPanel, "Attributes")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        objSizer = wx.BoxSizer(wx.VERTICAL)
        attrSizer = wx.BoxSizer(wx.VERTICAL)
        
        objPanel.SetSizer(objSizer)
        attrPanel.SetSizer(attrSizer)
        
        self.button =wx.Button(self,  -1,  "Refresh") 
         
        self.list_admobj =    ULC.UltimateListCtrl(objPanel, id=-1, style=wx.LC_REPORT |wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        self.list_patobj =    ULC.UltimateListCtrl(objPanel, id=-1, style=wx.LC_REPORT |wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        
        
        self.list_admattr =    ULC.UltimateListCtrl(attrPanel, id=-1, style=wx.LC_REPORT |wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        self.list_patattr =    ULC.UltimateListCtrl(attrPanel, id=-1, style=wx.LC_REPORT |wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)
 
        
        columns = [u'externalKey', u'multiInstanceNumber', u'localId', u'objectCode', u'inputUserKey', u'inputDate', u'idClass', u'idActionReason']
        for c,  col in enumerate(columns):
            self.list_patobj.InsertColumn(c, col, format=wx.LIST_FORMAT_CENTRE, width=150)
            self.list_admobj.InsertColumn(c, col, format=wx.LIST_FORMAT_CENTRE, width=150)
        
        columns_attrs= [u'objectCode', u'multiInstanceNumber', u'inputUserKey',  u'value', u'inputDate', u'idAttribute']
        for c,  col in enumerate(columns_attrs):
            self.list_patattr.InsertColumn(c, col, format=wx.LIST_FORMAT_CENTRE, width=150)
            self.list_admattr.InsertColumn(c, col, format=wx.LIST_FORMAT_CENTRE, width=150)
        
         
        sizer.Add(self.button,  0  )
        sizer.Add(self.nbook,  1,  wx.EXPAND  )
        #objects
        objSizer.Add(self.list_patobj,  1,  wx.EXPAND)
        objSizer.Add(self.list_admobj,  1,  wx.EXPAND)
        #attributes
        attrSizer.Add(self.list_patattr,  1,  wx.EXPAND)
        attrSizer.Add(self.list_admattr,  1,  wx.EXPAND) 
        
        self.SetSizer(sizer)
        sizer.Layout()
        objSizer.Layout()
        attrSizer.Layout()
         
        self.Bind(wx.EVT_BUTTON, self.refresh, self.button)
        
        #self.Bind(wx.EVT_CHAR, self.skip)
        self.list_admobj.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showObject)
        self.list_patobj.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showObject)
        
        self.list_admattr.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showAttribute)
        self.list_patattr.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showAttribute)
        
        self.refresh(None)
        
    def refresh(self, event):
        #result1 =  self.mainLogic.dataSession.savedObjects['patient']
        result1 =  self.mainLogic.dataSession.getObjects()
        self.list_patobj.Freeze()
        self.list_patobj.DeleteAllItems()
        columns = [u'externalKey', u'multiInstanceNumber', u'localId', u'objectCode', u'inputUserKey', u'inputDate', u'idClass', u'idActionReason']
        for r,  res in enumerate(result1):
            ii = self.list_patobj.InsertStringItem(r,res['externalKey'])
            for col, text in enumerate(columns[1:]):
                self.list_patobj.SetStringItem(r, col+1, str(res[text]))

        result2 = self.mainLogic.dataSession.getObjects()
        count = self.list_patobj.GetItemCount()
        for r,  res in enumerate(result2):
            ii = self.list_patobj.InsertStringItem(r + count ,res['externalKey'])
            self.list_patobj.SetItemBackgroundColour(ii, wx.NamedColour(wx.RED))
            for col, text in enumerate(columns[1:]):
                self.list_patobj.SetStringItem(r + count,  col+1, str(res[text]))
            
        self.list_patobj.Thaw()
        self.list_patobj.Update()
   
        ##oggetti admission
        #result1 =  self.mainLogic.dataSession.savedObjects['admission']
        result1 =  self.mainLogic.dataSession.getObjectsAdmission()
        self.list_admobj.Freeze()
        self.list_admobj.DeleteAllItems()
        columns = [u'externalKey', u'multiInstanceNumber', u'localId', u'objectCode', u'inputUserKey', u'inputDate', u'idClass', u'idActionReason']
        for r,  res in enumerate(result1):
            ii = self.list_admobj.InsertStringItem(r,res['externalKey'])
            for col, text in enumerate(columns[1:]):
                self.list_admobj.SetStringItem(r, col+1, str(res[text]))
      
        result2 = self.mainLogic.dataSession.getObjectsAdmission()
        count = self.list_admobj.GetItemCount()
        for r,  res in enumerate(result2):
            ii = self.list_admobj.InsertStringItem(r + count ,res['externalKey'])
            self.list_admobj.SetItemBackgroundColour(ii, wx.NamedColour(wx.RED))
            for col, text in enumerate(columns[1:]):
                self.list_admobj.SetStringItem(r + count, col+1, str(res[text]))
                 
        
        self.list_admobj.Thaw()
        self.list_admobj.Update()
        
        print "WARNING: UNTESTED CODE AFTER MERGING DBs, EvaluatorDialog.refresh"
        #attributi
        #result1 =  self.mainLogic.dataSession.savedObjectsAttributes['patient']
        result1 =  self.mainLogic.dataSession.getObjectsAttributes()
        self.list_patattr.Freeze()
        self.list_patattr.DeleteAllItems()
        columns_attrs = [u'objectCode', u'multiInstanceNumber', u'inputUserKey',  u'value', u'inputDate', u'idAttribute']
        for r,  res in enumerate(result1):
            ii = self.list_patattr.InsertStringItem(r,res['objectCode'])
            for col, text in enumerate(columns_attrs[1:]):
                self.list_patattr.SetStringItem(r, col+1, str(res[text]))

        result2 = self.mainLogic.dataSession.getObjectsAttributes()
        count = self.list_patattr.GetItemCount()
        for r,  res in enumerate(result2):
            ii = self.list_patattr.InsertStringItem(r + count ,res['objectCode'])
            self.list_patattr.SetItemBackgroundColour(ii, wx.NamedColour(wx.RED))
            for col, text in enumerate(columns_attrs[1:]):
                self.list_patattr.SetStringItem(r + count,  col+1, str(res[text]))
            
        self.list_patattr.Thaw()
        self.list_patattr.Update()
        
        #result1 =  self.mainLogic.dataSession.savedObjectsAttributes['admission']
        result1 =  self.mainLogic.dataSession.getObjectsAttributes()
        self.list_admattr.Freeze()
        self.list_admattr.DeleteAllItems()
        columns_attrs = [u'objectCode', u'multiInstanceNumber', u'inputUserKey',  u'value', u'inputDate', u'idAttribute']
        for r,  res in enumerate(result1):
            ii = self.list_admattr.InsertStringItem(r,res['objectCode'])
            for col, text in enumerate(columns_attrs[1:]):
                self.list_admattr.SetStringItem(r, col+1, str(res[text]))
      
        #self.output1.SetValue(str(result1))
        result2 = self.mainLogic.dataSession.getObjectsAttributes()
        count = self.list_admattr.GetItemCount()
        for r,  res in enumerate(result2):
            ii = self.list_admattr.InsertStringItem(r + count ,res['objectCode'])
            self.list_admattr.SetItemBackgroundColour(ii, wx.NamedColour(wx.RED))
            for col, text in enumerate(columns_attrs[1:]):
                self.list_admattr.SetStringItem(r + count,  col+1, str(res[text]))
            
        self.list_admattr.Thaw()
        self.list_admattr.Update()
        #objSizer.Layout()
        #attrSizer.Layout()
        
        
    def skip(self,  event):
        event.Skip()
        
    def showObject(self,  event):
        
        rowNo = event.GetIndex()
        win = event.GetEventObject()
        id = int(win.GetItem(rowNo, 6).GetText())
        
        info = self.mainLogic.crfData.getClassInfoFromId(id)
        infos = ''
 
        for k in sorted(info.keys()):
            infos+= '%s=\t%s\n' % (k,  info[k]) 
        dlg = wx.MessageDialog(None, 
            _(infos),
            _("Object info"), wx.OK| wx.ICON_QUESTION)
            
        dlg.ShowModal()
        dlg.Destroy()
        
    def showAttribute(self,  event):
        
        rowNo = event.GetIndex()
        win = event.GetEventObject()
        id = int(win.GetItem(rowNo, 5).GetText())
        ocode = str(win.GetItem(rowNo, 0).GetText())
        
        info = self.mainLogic.crfData.getAttributeInfoFromId(id)
        infos = ''
 
        for k in sorted(info.keys()):
            infos+= '%s=\t%s\n' % (k,  info[k]) 
        
        #objs = [o for o in self.mainLogic.dataSession.savedObjects[info['internalKeyTable']]+self.mainLogic.dataSession.objects[info['internalKeyTable']] if o['objectCode'] == ocode]
        objs = [o for o in self.mainLogic.dataSession.getObjects(info['internalKeyTable'])+self.mainLogic.dataSession.getObjects(info['internalKeyTable']) if o['objectCode'] == ocode]
        infos += '\n'
        if objs:
            infos += 'Associated object:'
            for o in objs:
                infos +='\n'
                for k in sorted(o.keys()):
                    infos+= '%s=\t%s\n' % (k,  o[k]) 
                infos += '----------------\n'
                infoobj = self.mainLogic.crfData.getClassInfoFromId(int(o['idClass']))
                for k in sorted(infoobj.keys()):
                    infos+= '%s=\t%s\n' % (k,  infoobj[k]) 
                
        else:
            infos += 'No Associated object!'
        
        dlg = wx.MessageDialog(None, 
            _(infos),
            _("Attribute info"), wx.OK |wx.ICON_QUESTION)
            
        dlg.ShowModal()
        dlg.Destroy()
