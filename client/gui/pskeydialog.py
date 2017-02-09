import wx
from wx.html import HtmlEasyPrinting
from validators import NotEmptyValidator

    
class Printer(HtmlEasyPrinting):
    def __init__(self):
        HtmlEasyPrinting.__init__(self)

    def GetHtmlText(self,text):
        html_text = text.replace('\n\n','<P>')
        html_text = text.replace('\n', '<BR>')
        return html_text

    def Print(self, text, doc_name):
        self.SetHeader(doc_name)
        self.PrintText(self.GetHtmlText(text),doc_name)

    def PreviewText(self, text, doc_name):
        self.SetHeader(doc_name)
        HtmlEasyPrinting.PreviewText(self, self.GetHtmlText(text))


class PSKeyDialog(wx.Dialog):

    def __init__(self, parent, id, privateKey):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1,
              pos=wx.DefaultPosition, size=wx.DefaultSize,
              style=wx.CAPTION | wx.CENTER, title=_('Please read carefully'), name='keydialog')

        self.privateKey = privateKey        
       
        disclaimerMessage = _('PRIVATE_KEY_MESSAGE') % privateKey
        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, _("Please read carefully").upper() + "\n")
        label.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, True, 'Tahoma'))
        vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)

        box = wx.BoxSizer(wx.HORIZONTAL)
        msgLabel = wx.StaticText(self, -1, disclaimerMessage)
        box.Add(msgLabel, 0, wx.ALIGN_LEFT|wx.RIGHT, 10)
        vsizer.Add(box, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btn.Bind(wx.EVT_BUTTON, self.doExit)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _("save"))
        btn.Bind(wx.EVT_BUTTON, self.doSave)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _("Print"))
        btn.Bind(wx.EVT_BUTTON, self.doPrint)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        vsizer.AddSpacer(25)
        vsizer.Add(btnSizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vsizer.AddSpacer(10)

        sizer.Add(vsizer,0,wx.ALL,10)

        self.SetSizer(sizer)
        self.Fit()

        self.exitFlag = False

    def doPrint(self, event):
        from mainlogic import _
        printer = Printer()
        printer.PreviewText(self.privateKey, _("PROSAFE PRIVATE KEY - KEEP CONFIDENTIAL"))

    def doSave(self, event):
        from mainlogic import _
        import os
        dlg = wx.FileDialog(self, _("Save location"), os.getcwd(), "", "*.txt", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path:
                try:
                    if not os.path.isdir(os.path.split(path)[0]):
                        raise BaseException
                    f = open(path,'w')
                    f.write("%s\n" % _("PROSAFE PRIVATE KEY - KEEP CONFIDENTIAL"))
                    f.write("%s\n" % self.privateKey)
                    f.close()
                except BaseException:
                    wx.MessageBox(_("Save error"),parent=self)

    def doExit(self, event):
        self.Destroy()



class PSSetKeyDialog(wx.Dialog):

    def __init__(self, parent, id, privateKeyCallback, setPrivateKeyCallback):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, id=-1,
              pos=wx.DefaultPosition, size=wx.DefaultSize,
              style=wx.CAPTION | wx.CENTER, title=_('Private key'), name='setkeydialog')

        self.privateKeyCallback = privateKeyCallback
        self.setPrivateKeyCallback = setPrivateKeyCallback
      
        privateKey = self.privateKeyCallback() 
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(25)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.AddSpacer(10)
        label = wx.StaticText(self, -1, _("Private key:"))
        box.Add(label, 1, wx.EXPAND)
        self.keyText = wx.TextCtrl(self, -1, privateKey, size=(300,-1), validator=NotEmptyValidator())
        box.Add(self.keyText, 2)
        box.AddSpacer(10)
        sizer.Add(box, 1, wx.EXPAND)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, -1, _("save"))
        btn.Bind(wx.EVT_BUTTON, self.doSet)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _("Reset"))
        btn.Bind(wx.EVT_BUTTON, self.doReset)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _("Close"))
        btn.SetDefault()
        btn.Bind(wx.EVT_BUTTON, self.doExit)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSpacer(25)
        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.AddSpacer(10)

        self.SetSizer(sizer)
        self.Fit()

    def doReset(self, event):
        self.setPrivateKeyCallback(None)
        privateKey = self.privateKeyCallback()
        self.keyText.SetValue(privateKey)

    def doSet(self, event):
        privateKey = self.keyText.GetValue()
        privateKey = privateKey.strip()
        self.setPrivateKeyCallback(privateKey)

    def doExit(self, event):
        self.Destroy()

