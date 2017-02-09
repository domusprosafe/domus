import wx
import  wx.lib.scrolledpanel as scrolled
import psconstants as psc
import os

class imageZoomDialog(wx.Dialog):
    def __init__(self, parent, id,img=None):
        wx.Dialog.__init__(self, parent, id,  size=(1050,710), style=0)
        #self.bmp = wx.Bitmap('%s.tif' % self.im_name)
        self.imageList = [el for el in os.listdir(psc.imagesPath) if el.startswith(img)]
        self.imageDict = dict()
        if len(self.imageList) > 1:
            for imageName in self.imageList:
                if '_' in imageName and len(imageName.split('_')) > 2:
                    continue
                sequenceNumber = imageName.split('_')[1].split('.')[0] 
                self.imageDict[int(sequenceNumber)] = imageName
        if not self.imageList:
            return
        if not self.imageDict:
            #self.bmp = wx.Image(os.path.join(psc.imagesPath, self.imageList[0]), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            self.bmp = wx.Bitmap(os.path.join(psc.imagesPath, self.imageList[0]))
        else:
            self.bmp = wx.Bitmap(os.path.join(psc.imagesPath, self.imageDict[min(self.imageDict.keys())]))
            self.currentImageIndex = min(self.imageDict.keys())
            #self.bmp = wx.Image(os.path.join(psc.imagesPath, self.imageDict[min(self.imageDict.keys())]), wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer = wx.BoxSizer(wx.VERTICAL)

        self.mpos = (0,0)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.SampleSize = 200
        self.ZoomedSize = 300


        self.addBtn = wx.Button(self, wx.ID_OK)

        self.viewBtn = wx.Button(self,size=wx.Size(20, 20))
        self.viewBtn.SetLabel('>')
        #self.viewBtn.Hide()
        self.Bind(wx.EVT_BUTTON,self.chang_img,self.viewBtn)

        self.viewBtn1 = wx.Button(self,size=wx.Size(20, 20))
        self.viewBtn1.SetLabel('<')
        #self.viewBtn1.Hide()
        #if self.im_name=='DI_non_swelling':
        #    self.viewBtn.Show()
        #    self.viewBtn1.Show()
        if len(self.imageList) < 2:
            self.viewBtn.Hide()
            self.viewBtn1.Hide()

        self.Bind(wx.EVT_BUTTON,self.chang_img1,self.viewBtn1)
        #sizer.Add(btn, 0, wx.ALL, 5)
        sizer.Add(self.viewBtn1, 0, wx.ALL, 5)
        sizer.AddSpacer(10)
        sizer.Add(self.viewBtn, 0, wx.ALL, 5)
        sizer.AddSpacer(10)
        sizer.Add(self.addBtn, 0, wx.ALL, 5)

        hSizer.Add(sizer,0,wx.ALIGN_CENTER|wx.BOTTOM, 5)
        hSizer.Add((1,1), 1, wx.EXPAND)
        hSizer.Add(sizer, 0,wx.ALIGN_CENTER|wx.TOP, 10)
        hSizer.Add((1,1), 0, wx.ALL,1)
        #sizer2.Add(self.addBtn,0,wx.ALIGN_CENTER,50)
        self.SetSizer(hSizer)
    
    def chang_img(self, event):
        self.currentImageIndex = self.currentImageIndex + 1
        if self.currentImageIndex not in self.imageDict.keys():
            self.currentImageIndex = min(self.imageDict.keys())
        self.bmp = wx.Bitmap(os.path.join(psc.imagesPath, self.imageDict[self.currentImageIndex]))
        self.mpos = (0,0)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.SampleSize = 200
        self.ZoomedSize = 300
        
    def chang_img1(self, event):
        self.currentImageIndex = self.currentImageIndex - 1
        if self.currentImageIndex not in self.imageDict.keys():
            self.currentImageIndex = max(self.imageDict.keys())
        self.bmp = wx.Bitmap(os.path.join(psc.imagesPath, self.imageDict[self.currentImageIndex]))
        self.mpos = (0,0)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.SampleSize = 200
        self.ZoomedSize = 300
        
    def OnMouseMove(self, event):
        self.mpos = event.GetPosition()
        self.Refresh(False)
        event.Skip()
        
    def OnPaint(self, event):
        self.size = self.GetSize()
        x = max(self.mpos[0]-20, -5)
        y = max(self.mpos[1]-20, -5)
        zoomed = None
        try:
            zoomed = self.bmp.GetSubBitmap((x-self.SampleSize/2, y-self.SampleSize/2, self.SampleSize, self.SampleSize)).ConvertToImage()
            zoomed.Rescale(self.ZoomedSize, self.ZoomedSize)
            zoomed = zoomed.ConvertToBitmap()
        except Exception, e:
            zoomed = None
            event.Skip()
            
        offscreenBMP = wx.EmptyBitmap(*self.size)
        self.offDC = wx.MemoryDC()
        self.offDC.SelectObject(offscreenBMP)
        self.offDC.Clear()
        self.offDC.BeginDrawing()
        self.offDC.DrawBitmap(self.bmp, 0, 0, True)
        if zoomed is not None:
            self.offDC.DrawBitmap(zoomed, x - self.ZoomedSize/2, y - self.ZoomedSize/2, True)
        self.offDC.EndDrawing()
        self.dc = wx.PaintDC(self)
        self.dc.Blit(0, 0, self.size[0], self.size[1], self.offDC, 0, 0)
        event.Skip()