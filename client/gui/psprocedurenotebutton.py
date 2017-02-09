import wx
import wx.lib.editor as editor


class psProcedureNoteButton(wx.BitmapButton): 
    
    def __init__(self, parent, id, bitmapPathWrite, bitmapPathRead, name, pos=(5, 5), size=(18, 18), callback=None):
        self.image1 = wx.Image(bitmapPathWrite, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.image2 = wx.Image(bitmapPathRead, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        wx.BitmapButton.__init__(self,parent=parent,  id=id, bitmap=self.image1, pos=pos, size = size, name = name)
        self.procedureName = name
        self.callback = callback
        self.Bind(wx.EVT_BUTTON, self.Open_Edit)
        self.textValue = ''
        self.originalTextValue = None
        self.info_boll()
    
    def Open_Edit(self, event):
        bt = event.GetEventObject()
        fen2=PageEditor(pageOne=self)
        if self.textValue != '' and self.textValue is not None:
            fen2.edit.SetValue(self.textValue)
        fen2.SetSize((300, 150))
        fen2.Centre()
        fen2.Show()
        self.info_boll()
        
    def info_boll(self):
        if self.textValue and self.textValue != '':
            self.setReadState()
        else:
            self.setWriteState()
            
    def setWriteState(self):
        from mainlogic import _
        self.SetBitmapLabel(self.image1)
        self.SetToolTipString(_("Click to add note"))
        
    def setReadState(self):
        self.SetBitmapLabel(self.image2)
        valueToSet = ''
        #for el in self.textValue:
         #   valueToSet += el + ' '
        #self.SetToolTipString(str.join('\n', self.textValue))
        self.SetToolTip(wx.ToolTip(self.textValue))
        
    def GetValue(self):
        if not self.textValue:
            self.textValue = ''
        return self.textValue
        
    def SetValue(self, value):
        if self.originalTextValue is None:
            self.originalTextValue = value
        if value:
            self.textValue = value
        self.info_boll()
        #if value and [el for el in value if el != '']:
        #    exec('self.textValue = ' + str(value))
        #self.info_boll()    
        
        
            
class PageEditor(wx.Frame):
    def __init__(self, pageOne=None):
        wx.Frame.__init__(self, None, style=wx.BORDER | wx.STAY_ON_TOP)
        self.pageOne = pageOne
        #self.edit = editor.Editor(self, -1,  size=(130,65), style=wx.SUNKEN_BORDER | wx.VSCROLL )
        self.edit= wx.TextCtrl(self, -1, size=(200, 100), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        
        from mainlogic import _
        Hbsizer = wx.BoxSizer(wx.VERTICAL)
        Hbsizer.Add(self.edit, 1, wx.EXPAND)
        #self.bt_copi = wx.Button(self, -1, label=_('Copy'), pos=(100,160), size=(75,23))
        #self.bt_copi.Bind(wx.EVT_BUTTON, self.clic_copi)
            
        #self.bt_cut = wx.Button(self, -1, label=_('Cut'), pos=(190,160), size=(75,23))
        #self.bt_cut.Bind(wx.EVT_BUTTON, self.clik_cup)
            
        #self.bt_past = wx.Button(self, -1, label=_('Paste'), pos=(280,160), size=(75,23))
        #self.bt_past.Bind(wx.EVT_BUTTON, self.clik_past)
        self.bt_undo = wx.Button(self, -1, label=_('Cancel'), pos=(100,160), size=(75,23))
        self.bt_undo.Bind(wx.EVT_BUTTON, self.cancelText)
        
        self.bt_clear = wx.Button(self, -1, label=_('Clear'), pos=(190,160), size=(75,23))
        self.bt_clear.Bind(wx.EVT_BUTTON, self.clearText)
        
        self.bt_save = wx.Button(self, -1, label=_('OK'), pos=(370,160), size=(75,23), name=self.pageOne.procedureName)
        self.bt_save.Bind(wx.EVT_BUTTON, self.savetext)
            
        Vbsizer = wx.BoxSizer(wx.HORIZONTAL)
        #Vbsizer.Add(self.bt_copi, wx.EXPAND)
        #Vbsizer.Add(self.bt_cut, wx.EXPAND)
        #Vbsizer.Add(self.bt_past, wx.EXPAND)
        Vbsizer.Add(self.bt_clear, wx.EXPAND)    
        Vbsizer.Add(self.bt_undo, wx.EXPAND)    
        Vbsizer.Add(self.bt_save, wx.EXPAND)    
        
        Hbsizer.Add(Vbsizer, 0, wx.EXPAND)
        self.SetSizer(Hbsizer)
        self.SetAutoLayout(1)
        Hbsizer.Fit(self)
        self.MakeModal()
        self.Show(1)
        
        
    def savetext(self, event):
        cpt=0
        self.pageOne.textValue = self.edit.GetValue()
        self.pageOne.info_boll()
        for k in range(len(self.edit.GetValue())):
            cpt=cpt+ len(self.edit.GetValue()[k])
            
        if cpt > 0:
            self.pageOne.SetBitmapLabel(self.pageOne.image2)
        if cpt == 0:
            from mainlogic import _
            self.pageOne.SetBitmapLabel(self.pageOne.image1)
            self.pageOne.SetToolTipString(_("Click to add Note"))
        self.pageOne.callback(event)
        self.MakeModal(False)
        self.Close(True)
        	
    def cancelText(self, event):
        self.pageOne.textValue = self.pageOne.originalTextValue
        self.MakeModal(False)
        self.Close(True)
            
    def clearText(self, event):
        self.edit.SetValue('')
        
