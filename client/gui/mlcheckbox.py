import wx
import textwrap
from psguiconstants import BACKGROUND_COLOUR

class MLCheckBox(wx.CheckBox):

        def __init__(self, parent, id=-1, label=wx.EmptyString, wrap=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, validator=wx.DefaultValidator, name=wx.CheckBoxNameStr):
            wx.CheckBox.__init__(self,parent,id,'',pos,size,style,validator,name)
            self._label = label
            self._wrap = wrap
            lines = self._label.split('\n')
            if self._wrap > 0:
                self._wrappedLabel = []
                for line in lines:
                    self._wrappedLabel.extend(textwrap.wrap(line,self._wrap,break_long_words=False))
            else:
                self._wrappedLabel = lines

            self._textHOffset = 20
            dc = wx.ClientDC(self)
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            dc.SetFont(font)
            maxWidth = 0
            totalHeight = 0
            lineHeight = 0
            for line in self._wrappedLabel:
                width, height = dc.GetTextExtent(line)
                maxWidth = max(maxWidth,width)
                lineHeight = height
                totalHeight += lineHeight 
            self._textHeight = totalHeight

            bestSize = wx.Size(self._textHOffset + maxWidth,totalHeight+1)
            if size.width != -1:
                bestSize.width = size.width
            if size.height != -1:
                bestSize.height = size.height

            self.SetInitialSize(bestSize)
            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.SetBackgroundColour(BACKGROUND_COLOUR)

        def OnPaint(self, event):
            dc = wx.PaintDC(self)
            self.Draw(dc)
            self.RefreshRect(wx.Rect(0,0,self._textHOffset,self.GetSize().height))
            event.Skip()

        def Draw(self, dc):
            dc.Clear()
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            dc.SetFont(font)
            dc.SetTextForeground(self.GetForegroundColour())
            height = self.GetSize().height
            if height > self._textHeight:
                offset = height / 2 - self._textHeight / 2
            else:
                offset = 0
            for line in self._wrappedLabel:
                width, height = dc.GetTextExtent(line)
                dc.DrawText(line,self._textHOffset,offset)
                offset += height


