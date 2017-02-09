import sys

import wx
import wx.lib.agw.ultimatelistctrl as ULC
import wx.lib.hyperlink as hyperlink

class PSNotificationViewer(wx.Frame):

    def __init__(self, notificationList, showEditorCallback):

        from mainlogic import _
        self.showEditorCallback = showEditorCallback
        wx.Frame.__init__(self, None, -1, _("Prosafe Notification"), style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.CLOSE_BOX)
        self.panel = wx.Panel(self)
        self.notificationListCtrl = ULC.UltimateListCtrl(self.panel, wx.ID_ANY, agwStyle=ULC.ULC_REPORT | ULC.ULC_VRULES | ULC.ULC_HRULES | ULC.ULC_SINGLE_SEL | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT |  ULC.ULC_BORDER_SELECT)
        
        self.notificationListCtrl.InsertColumn(0, _("NOTIFICATION NUMBER"))
        self.notificationListCtrl.InsertColumn(1, _("NOTIFICATION TITLE"))
        self.notificationListCtrl.InsertColumn(2, _("NOTIFICATION TEXT"))
        self.notificationListCtrl.InsertColumn(3, _("NOTIFICATION LINK"))
        self.index = 0
        self.populateItemList(notificationList)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notificationListCtrl, 4, wx.EXPAND|wx.ALL, 5)
        
        separator = wx.StaticLine(self.panel, wx.NewId(), (-1, -1), (-1, 2), wx.LI_HORIZONTAL)
        sizer.Add(separator,0,wx.GROW | wx.ALL, 10)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.closeButton=wx.Button(self.panel,label=_('Close'))
        self.closeButton.Bind(wx.EVT_BUTTON, self.closeNotificationViewer)
        buttonSizer.Add(self.closeButton, 1, wx.RIGHT, 5)
        sizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        
        self.panel.SetSizer(sizer)
        self.adjustSize()
        self.notificationListCtrl.Layout()
        self.Layout()
        
    def closeNotificationViewer(self, event):
        self.MakeModal(False)
        self.Destroy()
        
    def adjustSize(self):
        width = self.notificationListCtrl.GetColumnWidth(0) + self.notificationListCtrl.GetColumnWidth(1) + self.notificationListCtrl.GetColumnWidth(2) + self.notificationListCtrl.GetColumnWidth(3)
        self.SetSize((width+15, 400))
        
    def populateItemList(self, itemList):
        bestTitleColumnWidth = -1
        bestTitleColumnHeight = -1
        bestTextColumnWidth = -1
        bestTextColumnHeight = -1
        from mainlogic import _
        for number, notification in enumerate(itemList):
            title = wx.StaticText(self.notificationListCtrl,-1,notification['title'],(-1, -1), (-1, -1), wx.ALIGN_LEFT)
            #text = wx.StaticText(self.notificationListCtrl,-1,notification['text'],(-1, -1), (-1, -1), wx.ALIGN_LEFT)
            textForListCtrl = _(notification['text'])
            httpStartIndex = notification['text'].find('http://')
            extractedLink = ''
            if httpStartIndex > -1:
                firstSpaceAfterHttpIndex = notification['text'].find(' ', httpStartIndex)
                if firstSpaceAfterHttpIndex  > -1:
                    extractedLink = notification['text'][httpStartIndex:firstSpaceAfterHttpIndex]
                else:
                    extractedLink = notification['text'][httpStartIndex:]
                textForListCtrl = notification['text'].replace(extractedLink, '')
            text = wx.StaticText(self.notificationListCtrl, -1, textForListCtrl, size=wx.Size(300, -1))
            text.Wrap(text.GetSize().width) 
            control = None
            if extractedLink:
                control = hyperlink.HyperLinkCtrl(self.notificationListCtrl, -1, _('CLICCA QUI'),
                                         URL=extractedLink)
            elif 'admissionReference' in notification.keys() and notification['admissionReference']:
                control = hyperlink.HyperLinkCtrl(self.notificationListCtrl, -1, notification['admissionReference'],
                                         URL=notification['admissionReference'])
                control.Bind(wx.EVT_HYPERLINK, self.onLinkClicked)
                control.Bind(wx.EVT_LEFT_UP, self.onLinkClicked)
            titleSize = title.GetSize()
            textSize = text.GetSize()
            if titleSize[0] > bestTitleColumnWidth:
                bestTitleColumnWidth = titleSize[0]
            if textSize[0] > bestTextColumnWidth:
                bestTextColumnWidth = textSize[0]
            height = max([titleSize[1], textSize[1]])
            index = self.notificationListCtrl.InsertStringItem(sys.maxint, str(number+1))
            self.notificationListCtrl.SetItemWindow(index, 1, title, expand=True)
            self.notificationListCtrl.SetItemWindow(index, 2, text, expand=False)
            if control:
                self.notificationListCtrl.SetItemWindow(index, 3, control, expand=True)
            
            #self.notificationListCtrl.SetItemWindow(index, 3, text, expand=True)
        self.notificationListCtrl.SetColumnWidth(0, 50)
        self.notificationListCtrl.SetColumnWidth(1, bestTitleColumnWidth)
        self.notificationListCtrl.SetColumnWidth(2, bestTextColumnWidth)
        self.notificationListCtrl.SetColumnWidth(3, bestTextColumnWidth)
        
        
    def onLinkClicked(self, event):
        data = {}
        data['admissionKey'] = event.GetEventObject()._URL
        self.showEditorCallback(data)
        self.Destroy()
        
if __name__ == '__main__':        
    app = wx.App(0)
    longMessageList= [{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'}, {'priority': u'medium', 'text': u"Il tuo prosafe non \xe8 aggiornato all'ultima versione. Riavvia il tuo Prosafe Master.\r\nSe \xe8 la prima volta che visualizzi questo messaggio dall'ultimo aggiornamento, riavvia il tuo Prosafe Master.\r\nAltrimenti segui le istruzioni fornite nel seguente link:\r\n\r\nhttp://prosafe.marionegri.it", 'title': u'Aggiornamento Prosafe','priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'}, {'priority': u'medium', 'text': u"Il tuo prosafe non \xe8 aggiornato all'ultima versione. Riavvia il tuo Prosafe Master.\r\nSe \xe8 la prima volta che visualizzi questo messaggio dall'ultimo aggiornamento, riavvia il tuo Prosafe Master.\r\nAltrimenti segui le istruzioni fornite nel seguente link:\r\n\r\nhttp://prosafe.marionegri.it", 'title': u'Aggiornamento Prosafe'}]
    messageList= [{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'},{'priority': u'high', 'text': u'Non hai aggiornato i dati dello Start WEB.\r\nSei pregato di collegarti al seguente sito ed aggiornare i tuoi dati.\r\n\r\nhttp://giviti2.marionegri.it/startRegionale/start.html', 'title': u'Aggiornamento Start WEB'}]
    frame = PSNotificationViewer(messageList)
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
