import wx
import psconstants as psc
import os
ID_ACTION = wx.ID_YES
ID_CANCEL = 101
ID_NOTHING = 102

class PSMessageDialog(wx.Dialog):

    def __init__(self, parent, question, title='Prosafe Dialog', mode=1, callback=None, size=wx.Size(-1,150)):

        """
        mode explanation:
        mode = 1 for yes / no dialog
        mode = 2 for yes / no / cancel dialog
        """
    
        from mainlogic import _ 
        wx.Dialog.__init__(self, parent, id=-1, title=title, pos=wx.DefaultPosition,size=size, style=wx.DEFAULT_DIALOG_STYLE | wx.CENTER, name="genericPsDialog") 
        imageFile =  os.path.join(psc.imagesPath, "question.png")
        bmp = wx.Image(imageFile,wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        sbitmap = wx.StaticBitmap(self,  -1,  bmp)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.returnValue = None
        label = wx.StaticText(self, -1, question)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(sbitmap, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        hbox.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(hbox, 10, wx.EXPAND)
                  
        box = wx.BoxSizer(wx.HORIZONTAL)         
        btn = wx.Button(self, wx.ID_YES, _("Yes"))
        btnn = wx.Button(self, ID_CANCEL, _("No"))
        btn.SetDefault()    
               
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)
        box.Add(btnn, 0, wx.ALIGN_CENTRE|wx.ALL)
        if mode==2:
            btnc = wx.Button(self, ID_NOTHING, _("Cancel"))
            box.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)
            self.Bind(wx.EVT_BUTTON, self.doNothing, id=ID_NOTHING)

        self.Bind(wx.EVT_BUTTON, self.doClose, id=ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.doAction, id=wx.ID_YES)
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE)
        sizer.AddSpacer(10)
        
        self.SetSizer(sizer)
        self.Layout()
         
    def doAction(self, event):
        #self.closeAdmissionCallback()
        self.returnValue = wx.ID_YES
        self.Destroy()
        
    def doClose(self,  event):
        self.returnValue  = wx.ID_NO
        self.Destroy()

    def doNothing(self, event):
        self.returnValue  = wx.ID_CANCEL
        self.Destroy()
        