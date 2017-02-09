import wx
import wx.lib.customtreectrl as ct

ID_ACTION = 100
ID_CANCEL = 101

class PSExportGroupChooser(wx.Dialog):

    def __init__(self, parent, exportGroupsToTitles, GroupCrf):

        self.exportGroupsToTitles = exportGroupsToTitles
        self.GroupCrf = GroupCrf
        from mainlogic import _ 

        title = _("Choose export groups")
      
        wx.Dialog.__init__(self, parent, id=-1, title=title, pos=wx.DefaultPosition,size=wx.Size(300,550), style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER) 
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(5)
         
        
        label = wx.StaticText(self, -1, '')
        #hbox = wx.BoxSizer(wx.VERTICAL)
        #hbox.AddSpacer(5)
        sizer.Add(label)
        sizer.AddSpacer(5)

        titles = exportGroupsToTitles.values()
        titles.sort()
        self.titlesToGroups = dict([(el[1],el[0]) for el in exportGroupsToTitles.items()])
        # print 'DICTEMP :',GroupCrf
        # print 'contenuto di titlesToGroups :',self.titlesToGroups 
        # getAllActiveAdmissionsRawDataTable
        self.listbox = wx.CheckListBox(self, -1, wx.DefaultPosition, wx.DefaultSize, titles)
        sizer.Add(self.listbox, 1, wx.EXPAND | wx.ALL)
        self.listbox.Hide()
        
        #self.Bind(wx.EVT_LISTBOX, self.EvtListBox, lb)
        #self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, lb)
        #lb.SetSelection(0)

        #sizer.Add(hbox, 1, wx.EXPAND)
        ######################### replace CheckListBox with checkbox ############################
        il = wx.ImageList(16,16)
        self.fldridx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16,16)))
        self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, (16,16)))
        self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16,16)))
        
        self.tree = ct.CustomTreeCtrl(self,style=wx.TR_HAS_BUTTONS 
            | wx.TR_HAS_VARIABLE_ROW_HEIGHT
            # | wx.TR_HIDE_ROOT 
            | wx.TR_SINGLE
            | ct.TR_AUTO_CHECK_CHILD 
            | ct.TR_AUTO_CHECK_PARENT)
        
        self.tree.AssignImageList(il)
        # self.tree.Hide()
        root = self.tree.AddRoot(title)

        self.tree.SetItemPyData(root, None)
        # self.tree.SetItemImage(root, self.fldridx,wx.TreeItemIcon_Normal)
        # self.tree.SetItemImage(root, self.fldropenidx,wx.TreeItemIcon_Expanded)
        
        
        self.AddTreeNodes(root, GroupCrf)
        self.tree.Expand(root)
        self.tree.Bind(ct.EVT_TREE_ITEM_CHECKED, self.oncheck_elmt)
        
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL)
        ######################### End CheckListBox with checkbox ############################
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK)
        btnc = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        btn.SetDefault()
              
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)

        self.Bind(wx.EVT_BUTTON, self.doClose, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.doConfirm, id=wx.ID_OK)
       
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(5)
        
        self.SetSizer(sizer)
        

        self.chosenExportGroups = []
        
    
    def AddTreeNodes(self, parentItem, dico):
        # print 'OSO:',dico
        for item in dico:
            lst=[]
            if type(item) == str:
                newItem = self.tree.AppendItem(parentItem, item.capitalize(),ct_type=0)
                
            else:
                newItem = self.tree.AppendItem(parentItem, str(item).capitalize(),ct_type=0)
                self.tree.SetItemPyData(newItem, None)
                #self.AddTreeNodes(newItem, str(item))
            # print 'DICO:',dico
            # print 'keys:',item
            lst=dico[str(item)]
            for elt in sorted(lst):
                self.tree.AppendItem(newItem, elt,ct_type=1)
                self.tree.SetItemPyData(newItem, None)
            if item=='core':
                self.tree.Expand(newItem)            
    
    def oncheck_elmt(self, event):
        item = event.GetItem()
        elt_choosen=''
        elt_choosen=self.tree.GetItemText(item)
        # update list element choosen
        if elt_choosen in self.chosenExportGroups:
            for el in range(len(self.chosenExportGroups)):
                if str(elt_choosen) == str(self.chosenExportGroups[el-1]):
                    del self.chosenExportGroups[el-1]
        else:
            self.chosenExportGroups.append(elt_choosen)
        #print 'List to export variable :',self.chosenExportGroups
       
    
    def doConfirm(self, event):
        chosenExportTitles = []
        # for i in range(self.listbox.GetCount()):
            # if self.listbox.IsChecked(i):
                # chosenExportTitles.append(self.listbox.GetString(i))
        # self.chosenExportGroups = [self.titlesToGroups[el] for el in chosenExportTitles]
        self.chosenExportGroups = [self.titlesToGroups[el] for el in self.chosenExportGroups]
        print 'element chose:',self.chosenExportGroups
        self.GroupCrf=None
        self.EndModal(wx.ID_OK)
        
    def doClose(self,  event):
        chosenExportGroups = []
        self.chosenExportGroups2=[]
        self.EndModal(wx.ID_CANCEL)

    def getChosenGroups(self):
        return self.chosenExportGroups

