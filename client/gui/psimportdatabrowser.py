# -*- coding: utf-8 -*-

import wx
import wx.lib.filebrowsebutton as filebrowse
from psversion import PROSAFE_VERSION
import os
import psconstants as psc

ID_LOGIN = 100
ID_OUT = 101
ID_IMPORT = 102

class ImportDataBrowserDialog(wx.Dialog):

    def __init__(self, parent, importDataFromPackageCallback):
        from mainlogic import _
        #wx.Dialog.__init__(self, parent, id=-1, title='Activation', pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.CENTER | wx.STAY_ON_TOP, name="activationframe")
        wx.Dialog.__init__(self, parent, id=-1, title=_("Data import"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.CAPTION | wx.CENTER, name="activationframe")
 
        self.importDataFromPackageCallback = importDataFromPackageCallback
        self.imageFile =  os.path.join(psc.imagesPath, "logologin.png")
        bmp = wx.Image(self.imageFile,wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        sbitmap = wx.StaticBitmap(self, -1, bmp)
        self.dataImportCompleted = False
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(outerSizer)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbitmap, 0, wx.ALIGN_CENTRE|wx.ALL)
        outerSizer.Add(sizer,0,wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT,border=20)

        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetWeight(wx.FONTWEIGHT_BOLD)

        label = wx.StaticText(self, -1, _("PROSAFE - Master data import"))
        label.SetFont(font)
        sizer.AddSpacer(10)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(20)
        label = wx.StaticText(self, -1, _("Please select the masterdata.zip file to restore data from the old PROSAFE master"))
        label.Wrap(350)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL)
        sizer.AddSpacer(20)

        gridSizer = wx.FlexGridSizer(2,2)
        sizer.Add(gridSizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        self.btn = filebrowse.FileBrowseButton(self, -1, size=(450, -1), changeCallback = self.getPathFromFileBrowseButton, fileMask = '*.pmd')
        btnOut = wx.Button(self, ID_OUT, _("Exit"))
        btnImport = wx.Button(self, ID_IMPORT, _("Start data import"))
        
        self.Bind(wx.EVT_BUTTON, self.onDestroy, id=ID_OUT)
        self.Bind(wx.EVT_BUTTON, self.onStartImport, id=ID_IMPORT)

        sizer.AddSpacer(5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(btnOut, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(btnImport, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.AddSpacer(10)
        self.path = ''
        self.Fit()
        
    def getImportStatus(self):
        return self.dataImportCompleted
        
    def getPathFromFileBrowseButton(self, event):
        self.path = event.GetString()

    def onStartImport(self, event):
        result = self.importDataFromPackageCallback(self.path)
        if result == True:
            self.dataImportCompleted = True
            self.Show(False)
        
        
    def onDestroy(self, event):
        self.Show(False)