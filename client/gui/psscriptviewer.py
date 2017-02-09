import wx
import os
import sys
import datetime

class StandardPage(wx.Panel):
    def __init__(self, parent, thread):
        from mainlogic import _
        self.parent = parent
        text = thread.getDescription()
        if thread.isScriptBlockingProsafeAccess():  
            text = _(text) + '\n\n' + _('The execution of this script will stop Prosafe')
        else:
            text = _(text)
        wx.Panel.__init__(self, parent)
        self.thread = thread
        box = wx.BoxSizer(wx.VERTICAL)
        descriptionText = wx.StaticText(self, -1, text, (20,20))
        descriptionText.Wrap(descriptionText.GetSize().width)
        buttonRun = wx.Button(self, -1, _("Run!"))
        buttonRun.Bind(wx.EVT_BUTTON, self.OnButton)
        box.Add(descriptionText, 0, wx.ALL, 5)
        box.Add(buttonRun, 0, wx.ALL, 5)
        self.SetSizer(box)
        
    def OnButton(self, evt):
        from mainlogic import _
        if self.thread.restart:
            self.parent.GetParent().GetParent().shouldRestart = True
            
        self.thread.initialize()
        keepGoing = True
        max = self.thread.max
        dlg = wx.ProgressDialog(_("Executing script"),
                               _("Script is currently being executed"),
                               maximum = max,
                               parent=self,
                               style = 
                               #wx.PD_CAN_ABORT
                                 wx.PD_APP_MODAL
                                | wx.PD_ELAPSED_TIME
                                | wx.PD_REMAINING_TIME
                                )
        f = open('executedscript.txt', 'a')
        string = '\n script eseguito ' + self.thread.getName() + ' in data ' + datetime.datetime.now().isoformat() 
        f.write(string)
        f.close()
        self.thread.start()
        while keepGoing:
            (keepGoing, skip) = dlg.Update(self.thread.count, _("Script is currently being executed"))
            if not self.thread.running or self.thread.count == max:
                text = _("ENDED")
                if self.thread.endedWithError:
                    text = _("ERROR")
                (keepGoing, skip) = dlg.Update(max, text)
                self.thread.running = False
                break
        self.thread.reset()
        if self.parent.GetParent().GetParent().shouldRestart:
            self.parent.GetParent().GetParent().onCloseButton(evt)
        dlg.Destroy()
        
        

class ProsafeScriptViewer(wx.Frame):
    def __init__(self, scriptListCallBack, showLoginCallback, decryptScriptCallback, disposeCallback, connectCallback):
        from mainlogic import _
        self.scriptListCallBack = scriptListCallBack
        self.showLoginCallback = showLoginCallback
        self.decryptScriptCallback = decryptScriptCallback
        self.disposeCallback = disposeCallback
        self.connectCallback = connectCallback
        wx.Frame.__init__(self, None, title=_("Prosafe fixing script collection"), size=wx.Size(750,400))
        self.mainPanel = wx.Panel(self)
        self.scriptBook = wx.Notebook(self.mainPanel, style=wx.BK_DEFAULT)
        self.updatePages()
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.scriptBook, 4, wx.EXPAND)
        updatePagesButton = wx.Button(self.mainPanel, -1, _("Update script list"))
        updatePagesButton.Bind(wx.EVT_BUTTON, self.updatePages)
        buttonSizer.Add(updatePagesButton, 1, wx.ALL, 5)
        closeButton = wx.Button(self.mainPanel, -1, _("Return to login"))
        closeButton.Bind(wx.EVT_BUTTON, self.onCloseButton)
        buttonSizer.Add(closeButton, 1, wx.ALL, 5)
        sizer.Add(buttonSizer)
        self.mainPanel.SetSizer(sizer)
        self.shouldRestart = False
        self.Bind(wx.EVT_CLOSE, self.onCloseButton)
        self.disposeCallback()
    
    def onCloseButton(self, evt):
        self.Destroy()
        self.connectCallback()
        if not self.shouldRestart:
            self.showLoginCallback()
    
    def updatePages(self, evt=None):
        
        self.scriptBook.DeleteAllPages()        
        #parent class must be loaded before 
        f = open(os.path.join('scriptlist', 'prosafescript.py'), 'rb')
        baseClassEncFile = f.read()
        f.close()
        baseClassDecFile = self.decryptScriptCallback(baseClassEncFile, 'decrypt')
        f = open(os.path.join('scriptlist', 'prosafescript.py'), 'wb')
        f.write(baseClassDecFile)
        f.close()
        for script in self.scriptListCallBack():
            filename, extension = script.split('.')
            #avoiding unwanted files and extensions. Should we generalize?
            if filename == 'prosafescript' or extension == 'pyc':
                continue
            f = open(os.path.join('scriptlist', script), 'rb')
            encFile = f.read()
            f.close()
            decFile = self.decryptScriptCallback(encFile, 'decrypt')
            f = open(os.path.join('scriptlist', script), 'wb')
            f.write(decFile)
            f.close()
            filename, extension = script.split('.')
            #avoiding unwanted files and extensions. Should we generalize?
            if filename == 'prosafescript' or extension == 'pyc':
                continue
            scriptModule = __import__(filename, fromlist=[filename.split('_v')[0]])
            scriptClass = getattr(scriptModule, filename.split('_v')[0])
            scriptIstance = scriptClass()
            page = StandardPage(self.scriptBook, scriptIstance)
            self.scriptBook.AddPage(page, scriptIstance.getName())
            f = open(os.path.join('scriptlist', script), 'wb')
            f.write(encFile)
            f.close()
        self.scriptBook.Layout()
        self.mainPanel.Layout()
        f = open(os.path.join('scriptlist', 'prosafescript.py'), 'wb')
        f.write(baseClassEncFile)
        f.close()
    
if __name__ == "__main__":
    #app = wx.App()
    app = wx.PySimpleApp()
    ProsafeScriptViewer().Show()
    app.MainLoop()