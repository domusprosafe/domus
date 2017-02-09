import wx

class PSHistoryWidget(wx.Panel):

    def __init__(self, parent, id, name="", size=wx.DefaultSize, pos=wx.DefaultPosition, columnNames=[], rows=[], timeStampAttributeFullName="", currentTimeStamp=None, timeStampSelectedCallback=None, timeStampActivatedCallback=None, pageLinkName=""):
        wx.Panel.__init__(self, parent, id, name=name, size=size, pos=pos)

        self.timeStampSelectedCallback = timeStampSelectedCallback
        self.timeStampActivatedCallback = timeStampActivatedCallback
        self.timeStampAttributeFullName = timeStampAttributeFullName
        self.pageLinkName = pageLinkName
        self.currentTimeStamp = currentTimeStamp

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        columnWidth = size[0] / len(columnNames) - 3

        self.historyList = wx.ListView(self, -1, size=size)

        for c, columnName in enumerate(columnNames):
            self.historyList.InsertColumn(c,columnName)
            self.historyList.SetColumnWidth(c,columnWidth)

        self.timeStampList = []

        for r, row in enumerate(rows):
            # print 'R:',r
            # print 'ROW:',row
            # print 'columnNames:',columnNames
            self.historyList.InsertStringItem(r,'')
            self.timeStampList.append(row['timeStamp'])
            for c, columnName in enumerate(columnNames):
                # print 'A C:',c
                # print 'A columnName:',columnName
                # print 'A row:',row
                self.historyList.SetStringItem(r,c,row[columnName])

        hbox.Add(self.historyList)
        vbox.Add(hbox)

        self.SetSizer(vbox)
        
        index = None
        try:
            index = self.timeStampList.index(currentTimeStamp)
        except BaseException, e:
            print e

        if index == None:
            if len(self.timeStampList) > 0:
                self.historyList.Select(len(self.timeStampList)-1)
        else:
            self.historyList.Select(index)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated)

        #wx.CallAfter(self.historyList.SetFocus())

    def onItemSelected(self, event):

        index = event.GetIndex()
        timeStamp = self.timeStampList[index]

        if timeStamp == self.currentTimeStamp:
            return

        self.currentTimeStamp = timeStamp

        self.timeStampSelectedCallback(self.timeStampAttributeFullName,timeStamp)

    def onItemActivated(self, event):

        index = event.GetIndex()
        timeStamp = self.timeStampList[index]

        wx.CallAfter(self.timeStampActivatedCallback,self.pageLinkName,timeStamp)

