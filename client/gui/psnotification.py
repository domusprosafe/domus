import wx
from wx.lib.agw import toasterbox as TB
import wx.lib.hyperlink as hyperlink

styleDictionary = {
'low': {'backgroundColour':wx.Colour(139,213,137), 'textColour':wx.Colour(9,56,8), 'linkColour':wx.Colour(9,56,8),'visitedLinkColour':wx.Colour(9,56,8), 'hoverColour':wx.Colour(139,213,137), 'hoverBackground':wx.Colour(9,56,8)} ,
'normal': {'backgroundColour':wx.Colour(139,213,137), 'textColour':wx.Colour(9,56,8), 'linkColour':wx.Colour(9,56,8),'visitedLinkColour':wx.Colour(9,56,8), 'hoverColour':wx.Colour(139,213,137), 'hoverBackground':wx.Colour(9,56,8)} ,
'medium': {'backgroundColour':wx.Colour(255,194,75), 'textColour':wx.Colour(95,72,28), 'linkColour':wx.Colour(95,72,28),'visitedLinkColour':wx.Colour(95,72,28), 'hoverColour':wx.Colour(255,194,75), 'hoverBackground':wx.Colour(95,72,28)},
'high': {'backgroundColour':wx.Colour(223,118,119), 'textColour':wx.Colour(85,18,18), 'linkColour':wx.Colour(85,18,18),'visitedLinkColour':wx.Colour(85,18,18), 'hoverColour':wx.Colour(223,118,119), 'hoverBackground':wx.Colour(85,18,18)}
}

class PSNotification(TB.ToasterBox):    
    def __init__(self, target, text, title, priority, admissionIds, showEditorCallback=None, showNotificationViewerCallback=None):
        from mainlogic import _
        text = _(text)
        title = _(title)
        self.priority = priority
        linkFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, False)
        self.admissionIds = admissionIds
        self.showEditorCallback = showEditorCallback
        self.showNotificationViewerCallback = showNotificationViewerCallback
        windowstyle = TB.TB_DEFAULT_STYLE
        tbstyle = TB.TB_COMPLEX
        closingstyle = TB.TB_ONCLICK
        TB.ToasterBox.__init__(self, target, tbstyle, windowstyle, closingstyle)
        self.SetTitle(title)
        self.SetPopupSize((200, 150))
        x, y = target.GetSize()
        x = x - 250
        y = y - 250
        self.SetPopupPosition((x, y))
        self.SetPopupPauseTime(25000)
        self.SetPopupScrollSpeed(8)
        
        tbpanel = self.GetToasterBoxWindow()
        #panel = wx.Panel(tbpanel, -1, style=wx.RAISED_BORDER)
        #panel = wx.Panel(tbpanel, -1, style=wx.SUNKEN_BORDER)
        panel = wx.Panel(tbpanel, -1, style=wx.DOUBLE_BORDER)
        #wx.DOUBLE_BORDER, wx.SIMPLE_BORDER
        
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        httpStartIndex = text.find('http://')
        extractedLink = ''
        #Mostra elenco dei pazienti con followup da compilare
        self.moreAdmissionIdsText = _('SHOW ADMISSION LIST')
        if httpStartIndex > -1:
            firstSpaceAfterHttpIndex = text.find(' ', httpStartIndex)
            if firstSpaceAfterHttpIndex  > -1:
                extractedLink = text[httpStartIndex:firstSpaceAfterHttpIndex]
            else:
                extractedLink = text[httpStartIndex:]
            text = text.replace(extractedLink, '')
        sttext = wx.StaticText(panel, -1, text, (10, 10), (-1, -1))
        
        sttext.SetBackgroundColour(styleDictionary[priority]['backgroundColour'])
        sttext.Wrap(sttext.GetSize().width) 
        vsizer.Add(sttext, 1, flag=wx.EXPAND|wx.ALL, border=5)
        #vsizer.AddSpacer(1)
        linkSizer = wx.BoxSizer(wx.VERTICAL)
        if extractedLink or self.admissionIds:
            if extractedLink:
                hl = hyperlink.HyperLinkCtrl(panel, -1, _('CLICK HERE'),
                                         URL=extractedLink)
                                         
            if self.admissionIds:
                if len(self.admissionIds) == 1:
                    admissionId = self.admissionIds[0]
                    hl = hyperlink.HyperLinkCtrl(panel, -1, admissionId, URL=admissionId)
                    hl.Bind(wx.EVT_HYPERLINK, self.onLinkClicked)
                    hl.Bind(wx.EVT_LEFT_UP, self.onLinkClicked)
                else:
                    hl = hyperlink.HyperLinkCtrl(panel, -1, self.moreAdmissionIdsText, URL=self.moreAdmissionIdsText)
                    hl.Bind(wx.EVT_HYPERLINK, self.onLinkClicked)
                    hl.Bind(wx.EVT_LEFT_UP, self.onLinkClicked)
            hl.Bind(wx.EVT_ENTER_WINDOW, self.setBackgroundHover)
            hl.Bind(wx.EVT_LEAVE_WINDOW, self.resetBackgroundHover)
            hl.SetBackgroundColour(styleDictionary[priority]['backgroundColour'])
            hl.SetColours(styleDictionary[priority]['linkColour'], styleDictionary[priority]['visitedLinkColour'], styleDictionary[priority]['hoverColour'])
            hl.SetUnderlines(False, False, False)
            hl.EnableRollover(True)
            hl.SetBold(True)
            hl.DoPopup(False)
            hl.UpdateLink()
            linkSizer.Add(hl, 0, flag=wx.EXPAND|wx.ALL, border=5) 
            linkSizer.AddSpacer(1)
            
        sizer.Add(vsizer, 2, flag=wx.EXPAND|wx.ALL)
        if extractedLink or self.admissionIds:
            sizer.Add(linkSizer, 1, wx.ALIGN_BOTTOM)
        #sizer.Layout()
        panel.SetBackgroundColour(styleDictionary[priority]['backgroundColour'])
        panel.SetSizer(sizer)
        self.AddPanel(panel)
        sizer.Fit(tbpanel)
        
        sttext.Bind(wx.EVT_LEFT_DOWN, self.onClick)
        
    #def OnClose(self, event):
    #    print 'closing'
    #    event.Skip()
    def onClick(self, event):
        try:
            self.GetToasterBoxWindow().NotifyTimer(None)
        except:
            self.Notify()
            pass
        self.Destroy()
    
    def setBackgroundHover(self, event):
        hl = event.GetEventObject()
        hl.SetBackgroundColour(styleDictionary[self.priority]['hoverBackground'])
        hl.UpdateLink()
    
    def resetBackgroundHover(self, event):
        hl = event.GetEventObject()
        hl.SetBackgroundColour(styleDictionary[self.priority]['backgroundColour'])        
        hl.UpdateLink()
        
    def onLinkClicked(self, event):
        if event.GetEventObject()._URL != self.moreAdmissionIdsText:
            data = {}
            data['admissionKey'] = event.GetEventObject()._URL
            self.showEditorCallback(data)
        else:
            self.showNotificationViewerCallback()
            