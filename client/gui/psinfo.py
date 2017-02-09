import wx
import threading
from psguiconstants import GUI_WINDOW_VARIANT
from notificationcenter import notificationCenter

class PSInfo(wx.Panel):

    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, -1)

        sizer = wx.GridSizer(1,1)
        self.SetSizer(sizer)

        self.textCtrl = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textCtrl.SetWindowVariant(GUI_WINDOW_VARIANT)
        sizer.Add(self.textCtrl,0,wx.EXPAND|wx.ALL)

        self.timer = None
        self.queuedInfoMessage = None

        self.showWelcomeMessage()

        notificationCenter.addObserver(self,self.onShowDocumentation,"ShowDocumentation")
        notificationCenter.addObserver(self,self.onHideDocumentation,"HideDocumentation")
        notificationCenter.addObserver(self,self.onEditorClosing,"EditorIsClosing")
        notificationCenter.addObserver(self,self.onPageChanged,"PageHasChanged")

    def onPageChanged(self,notifyingObject,userInfo=None):
        self.showWelcomeMessage()

    def onEditorClosing(self,notifyingObject,userInfo=None):
        #self.textTimer.Stop()
        notificationCenter.removeObserver(self)

    def onTimer(self):
        self.textCtrl.SetValue(self.queuedInfoMessage)

    def showWelcomeMessage(self):
        from mainlogic import _
        welcomeText = _('Hover the mouse on the item of interest to display its definition')
        self.textCtrl.SetValue(welcomeText)

    def onShowDocumentation(self,notifyingObject,userInfo=None):
        if 'message' not in userInfo:
            return
        self.queuedInfoMessage = userInfo['message']
        if self.timer is None:
            self.timer = threading.Timer(0.5,self.onTimer)
            self.timer.start()

    def onHideDocumentation(self,notifyingObject,userInfo=None):
        if self.timer is None:
            return
        self.timer.cancel()
        self.timer = None

