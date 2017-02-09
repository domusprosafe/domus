import wx

class PSProxyDialog(wx.Dialog):

    def __init__(self, parent, id, activation=False, address=None, username=None, password=None, testConnectionCallback=None):

        wx.Dialog.__init__(self, parent, id=-1, title='Connection', pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.CENTER | wx.STAY_ON_TOP, name="connectionframe")

        from mainlogic import _

        self.testConnectionCallback = testConnectionCallback

        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "Proxy settings\n")
        vsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        vsizer.AddSpacer(20)

        if not address:
            address = ''
        if not username:
            username = ''
        if not password:
            password = ''

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Address", size=(100,-1))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.RIGHT, 10)
        self.address = wx.TextCtrl(self, -1, address, size=(300,-1))
        box.Add(self.address, 1, wx.ALIGN_LEFT|wx.ALL, 0)
        vsizer.Add(box, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Username", size=(100,-1))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.RIGHT, 10)
        self.username = wx.TextCtrl(self, -1, username, size=(150,-1))
        box.Add(self.username, 1, wx.ALIGN_LEFT|wx.ALL, 0)
        vsizer.Add(box, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Password", size=(100,-1))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.RIGHT, 10)
        self.password = wx.TextCtrl(self, -1, password, size=(150,-1),style=wx.TE_PASSWORD)
        box.Add(self.password, 1, wx.ALIGN_LEFT|wx.ALL, 0)
        vsizer.Add(box, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)

        labelProxySample = wx.StaticText(self, -1, _("Address format example: http://proxynameexample (http://proxy.name.com)"), size=(-1,-1))
        vsizer.Add(labelProxySample, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)
        labelProxySampleTwo = wx.StaticText(self, -1, _("Address format example with port: http://proxynameexample:port (http://proxy.name.com:8080)"), size=(-1,-1))
        vsizer.Add(labelProxySampleTwo, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)
        labelProxyAdviceIp = wx.StaticText(self, -1, _("Prosafe may not be able to solve the proxy name. You can eventually set the ip address instead of the proxy name."), size=(-1,-1))
        vsizer.Add(labelProxyAdviceIp, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)
        labelProxyUserAndPassword = wx.StaticText(self, -1, _("Username and password can be left blank when not needed."), size=(-1,-1))
        vsizer.Add(labelProxyUserAndPassword, 0, wx.ALIGN_LEFT|wx.BOTTOM, 5)
        if activation:
            btn = wx.Button(self, -1, 'Connect')
            btn.SetDefault()
            btnOut = wx.Button(self, -1, 'Exit')
        else:
            btnTest = wx.Button(self, -1, 'Test')
            btnTest.SetDefault()
            btn = wx.Button(self, -1, _('Save'))
            btnOut = wx.Button(self, -1, _('Cancel'))
            btnOut.SetDefault()
            btnTest.Bind(wx.EVT_BUTTON, self.doTest)
 
        btn.Bind(wx.EVT_BUTTON, self.doConnect)
        btnOut.Bind(wx.EVT_BUTTON, self.doExit)
        vsizer.AddSpacer(25)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        if not activation:
            btnSizer.Add(btnTest, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btnSizer.Add(btnOut, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.messageText = wx.StaticText(self, -1)
        vsizer.Add(self.messageText, 0, wx.ALIGN_CENTRE|wx.ALL)

        vsizer.Add(btnSizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        vsizer.AddSpacer(10)

        sizer.Add(vsizer,0,wx.ALL,10)

        self.SetSizer(sizer)
        self.Fit()

        self.exitFlag = False

    def doTest(self, event):
        address = self.address.GetValue()
        address = address.replace('http://','')
        username = self.username.GetValue()
        password = self.password.GetValue()
        busyCursor = wx.BusyCursor()
        connected = self.testConnectionCallback(address,username,password)
        del busyCursor
        from mainlogic import _
        #TODO: TRANSLATE
        if connected:
            self.messageText.SetLabel(_("Connection successful"))
        else:
            self.messageText.SetLabel(_("Connection failed"))
        self.Layout()

    def doConnect(self, event):
        self.Hide()

    def doExit(self, event):
        self.exitFlag = True
        self.Hide()


