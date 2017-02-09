import wx, sys
import  wx.lib.mixins.listctrl  as  listmix
# from mainlogic import _
class MyListCtrlListmix(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        
class PSRestorableDeleted(wx.Dialog):
    # from mainlogic import _
    def __init__(self, var_data=None, varcallback=None):
        from mainlogic import _
        wx.Dialog.__init__(self, None, -1, _("hospitalization unactivated"), size=(800, 400))
        
        self.varcallback = varcallback
        self.var_data = var_data
        tID = wx.NewId()
        self.dic_elm = []
        self.data = {}
        
        for dicData in self.var_data:
            patienData = {}
            for data_el in self.var_data[dicData]:
                for key , val in data_el.items():
                    patienData[key] = val
            data_lastName = patienData['crfs.core.lastName.lastName']
            data_firstName = patienData['crfs.core.firstName.firstName']
            data_admissionCode = patienData['admissionKey']
            data_admissionData = patienData['crfs.core.icuAdmDate.icuAdmDate']
            data_birthday = patienData['crfs.core.birthDate.birthDate']
            self.dic_elm.append((data_admissionCode, data_admissionData, data_firstName, data_lastName, data_birthday))
            self.data['%s' % patienData['admissionKey']] = patienData
        
        self.select_patient = ''
        self.currentItem = 0
        panel = wx.Panel(self, -1)
        
        
        
        vs = wx.BoxSizer(wx.VERTICAL)
        rev = wx.StaticText(panel, -1, _("The patients presented in the list are those deleted from prosafe list."))
        # rev.SetForegroundColour('white')
        
        
        box1_title = wx.StaticBox(self, -1, _("Deleted patient restoring."))
        box1_title.SetForegroundColour('Blue')
        
        box1 = wx.StaticBoxSizer(box1_title, wx.VERTICAL)
        
        # rev.SetBackgroundColour('black')
        
        self.list_ctrl = MyListCtrlListmix(panel, -1, size=(786, 450),
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_SUNKEN
                                 # | wx.BORDER_NONE
                                 # | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 # | wx.LC_NO_HEADER
                                 # | wx.LC_VRULES
                                 # | wx.LC_HRULES
                                 # | wx.LC_SINGLE_SEL
                                 )
                                 
        self.list_ctrl.InsertColumn(0, _('Admission code'))
        self.list_ctrl.InsertColumn(1, _('Admission date'))
        self.list_ctrl.InsertColumn(2, _('Last Name'))
        self.list_ctrl.InsertColumn(3, _('First Name'))
        self.list_ctrl.InsertColumn(4, _('Date of birth'))
        
        ind = 0
        if self.dic_elm != []:
            for elm in self.dic_elm:
                # print 'verif',elm
                index = self.list_ctrl.InsertStringItem(sys.maxint, unicode(elm[0]))
                
                self.list_ctrl.SetStringItem(index, 1, unicode(elm[1]))
                self.list_ctrl.SetStringItem(index, 2, unicode(elm[2]))
                self.list_ctrl.SetStringItem(index, 3, unicode(elm[3]))
                self.list_ctrl.SetStringItem(index, 4, unicode(elm[4]))
                
                if ind % 2:
                    self.list_ctrl.SetItemBackgroundColour(index, "white")
                else:
                    self.list_ctrl.SetItemBackgroundColour(index, (152, 192, 192, 255))
                ind += 1
            self.list_ctrl.SetColumnWidth(0, 158)
            self.list_ctrl.SetColumnWidth(1, 157)
            self.list_ctrl.SetColumnWidth(2, 157)
            self.list_ctrl.SetColumnWidth(3, 157)
            self.list_ctrl.SetColumnWidth(4, 158)
        self.bt_sav_tmp = wx.Button(panel, -1, 'Restore', (60, 23))
        self.bt_sav_tmp.Disable()
        box1.Add(rev, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        
        vs.Add(box1, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        vs.Add(self.list_ctrl, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        vs.Add(self.bt_sav_tmp, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        panel.SetSizerAndFit(vs)
        self.Fit()
        self.list_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect_attrib)
        
        self.bt_sav_tmp.Bind(wx.EVT_BUTTON, self.OnSelect_attrib1)
        
    def OnSelect_attrib1(self, event):
        # print 'data select',self.select_patient
        # k=self.list_ctrl.GetItemText(self.currentItem)
        k = self.select_patient
        self.select_line(self.data[k])
        self.Close()
        
    def verifdata(self, var):
        for el in var:
            if len(el) == 1:
                return el[0]
    def OnDoubleClick(self, event):
        # print "self.list_ctrl Double click select item:",self.list_ctrl.GetItemText(self.currentItem)
        k = self.list_ctrl.GetItemText(self.currentItem)
        self.select_line(self.data[k])
        self.Close()
        
    def OnSelect_attrib(self, event):
        self.bt_sav_tmp.Enable()
        self.currentItem = event.m_itemIndex
        self.select_patient = self.getColumnText(self.currentItem, 0)
    
    def getColumnText(self, index, col):
        item = self.list_ctrl.GetItem(index, col)
        return item.GetText()
        
    def select_line(self, var):
        self.varcallback(var)
        self.Close()
