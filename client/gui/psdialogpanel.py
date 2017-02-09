import wx
from guigenerator import GuiGenerator
from psguiconstants import BACKGROUND_COLOUR

class PSDialogPanel(wx.Panel):
        
    def __init__(self, parent, mainLogic, showPageCallback, data):
        wx.Panel.__init__(self, parent, -1)

        self.parent = parent
        
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        
        self.mainLogic = mainLogic

        self.showPageCallback = showPageCallback

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
        innerSizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(innerSizer,0,wx.ALL,10)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(hsizer,0,wx.ALL|wx.ALIGN_RIGHT,20)

        from mainlogic import _

        okButton = wx.Button(self,wx.ID_OK)
        openAdmissionButton = wx.Button(self,-1,_("Open patient"))
        openNextAdmissionButton = wx.Button(self,wx.ID_OK,_("Open Next"))
        cancelButton = wx.Button(self,wx.ID_CANCEL)

        self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
        openAdmissionButton.Bind(wx.EVT_BUTTON, self.onOpenAdmission)
        openNextAdmissionButton.Bind(wx.EVT_BUTTON, self.onOpenNextAdmission)

        self.shouldOpenAdmission = False
        self.shouldOpenNextAdmission = False

        hsizer.Add(okButton,0,wx.BOTTOM,20)
        hsizer.AddSpacer(10)
        hsizer.Add(openAdmissionButton,0,wx.BOTTOM,20)
        hsizer.AddSpacer(10)
        hsizer.Add(openNextAdmissionButton,0,wx.BOTTOM,20)
        hsizer.AddSpacer(10)
        hsizer.Add(cancelButton,0,wx.BOTTOM,20)

        self.guiGenerator = GuiGenerator(self,innerSizer,self.mainLogic,self.showPageCallback)

        self.mainLogic.notificationCenter.addObserver(self,self.onDataUpdated,"DataHasBeenUpdated",self.mainLogic.dataSession)
        self.mainLogic.notificationCenter.addObserver(self,self.onDataNotUpdated,"DataCannotBeUpdated",self.mainLogic.dataSession)

        self.Layout()

    def onOk(self,event):
        self.guiGenerator.killFocus()
        event.Skip()
        
    def onOpenNextAdmission(self,event):
        self.guiGenerator.killFocus()
        self.shouldOpenNextAdmission = True
        # event.Skip()
        self.parent.EndModal(100001)
	
    def onOpenAdmission(self,event):
        self.guiGenerator.killFocus()
        self.shouldOpenAdmission = True
        self.parent.EndModal(100001)

    def onDataUpdated(self, notifyingObject, userInfo=None):
        self.guiGenerator.updateGui()
    
    def onDataNotUpdated(self, notifyingObject, userInfo=None):
        self.guiGenerator.updateGui()
        
    def showPage(self,crfName,pageName):
        self.SetLabel(pageName)
        self.guiGenerator.showPage(crfName,pageName,decoration=False)
        
        self.mainLogic.notificationCenter.postNotification("PageHasChanged",self)
        #self.Layout()
        #self.Refresh()

