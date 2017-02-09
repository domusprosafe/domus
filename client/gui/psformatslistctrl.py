import sys
import wx
import wx.lib.mixins.listctrl as listmix

class PSFormatList(wx.Frame):
    def __init__(self, parent, title='', formatsAndDescriptionsDict={}):
        from mainlogic import _
        wx.Frame.__init__(self, parent, -1, title=_("Formats"), pos=wx.DefaultPosition, size=wx.DefaultSize, style= wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN, name="browser")

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundColour(wx.NullColor);
        
        self.BtnCopy = wx.Button(self, -1,_("copy"))
        self.BtnCopy.Bind(wx.EVT_BUTTON, self.onCopy)
        instructionLabel = wx.StaticText(self, -1, _("Formats usage instruction"))
        
        #self.sizer.AddStretchSpacer()
        self.listView = PSFormatListCtrl(parent=self, formatsAndDescriptionsDict=formatsAndDescriptionsDict)
        self.listView.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.sizer.Add(instructionLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.Add(self.listView, 1, wx.EXPAND | wx.ALL, 10)
        self.sizer.Add(self.BtnCopy, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        
        self.SetSizer(self.sizer)
        self.listView.Fit()
        #self.SetAutoLayout(True)
        
    def onCopy(self, event):
        txt=''
        for elt in self.listView.get_selected_items():
            txt=txt+'\n'+elt
        if txt != '':
            self.dataObj = wx.TextDataObject()
            self.dataObj.SetText(txt)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(self.dataObj)
                wx.TheClipboard.Close()
            else:
                wx.MessageBox("Unable to open the clipboard", "Error")
        
    def OnItemDeselected(self, event):
        return
        self.listView.ClearAll()
        self.listView.Populate()
        
        
class PSFormatListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):

    def __init__(self, parent, ID=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, formatsAndDescriptionsDict={}):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style = wx.LC_REPORT
                                 | wx.BORDER_NONE
                                 | wx.LC_SORT_ASCENDING)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listeSelct=[]
        self.listctrldata = {}
        self.convertFormatsDictToListData(formatsAndDescriptionsDict)
        self.Populate()
        # listmix.TextEditMixin.__init__(self)
        
    def Populate(self):
        # for normal, simple columns, you can add them like this:
        from mainlogic import _
        self.InsertColumn(0, _("Description"))
        self.InsertColumn(1, _("Format name"))
        items = self.listctrldata.items()
        for key, data in items:
            index = self.InsertStringItem(sys.maxint, data[0])
            self.SetStringItem(index, 0, data[1])
            self.SetStringItem(index, 1, '$%s$' % data[0])
            self.SetItemData(index, key)

        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        #self.SetColumnWidth(0, 300)
        #self.SetColumnWidth(1, 300)
        self.currentItem = 0
        
    def get_selected_items(self):
        """
        Ottiene gli elementi selezionati per il controllo elenco.
        La selezione viene restituito come un elenco di indici selezionati,
        basso al piu alto.
        """

        selection = []
        current = -1
        while True:
            next = self.GetNextSelected(current)
            if next == -1:
                return selection
            description = self.GetItem(next,0).GetText()
            varName = self.GetItem(next,1).GetText()
            selection.append('%s :\n%s'%(description, varName))
            current = next

    def GetNextSelected(self, current):
        """Returns next selected item, or -1 when no more"""
        return self.GetNextItem(current, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)    


    def convertFormatsDictToListData(self, data):
        counter = 1
        for itemFullName in data:
            if not data[itemFullName]:
                data[itemFullName] = ''
            self.listctrldata[counter] = (itemFullName, data[itemFullName])
            counter += 1