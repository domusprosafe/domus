import wx
from psCalendarPopup import CalendarPopup
from wx import WXK_CANCEL, WXK_DELETE
import datetime

def create(parent):
    return CalendarTextbox(parent)

class CalendarTextbox(wx.TextCtrl):
   
  def GetValue(self):
    strTmp = self.Value
    if wx.DateTime().ParseFormat(strTmp, format=self.defaultparser) == -1:
        return wx.DateTime()
    if bool([el for el in [x in strTmp for x in 'ymd'] if el]):
        return wx.DateTime()
    strSplit = strTmp.split('/')
    value = wx.DateTimeFromDMY(int(strSplit[self.defaultparser.split('/').index('%d')]), int(strSplit[self.defaultparser.split('/').index('%m')]) -1, int(strSplit[self.defaultparser.split('/').index('%Y')]))
    if value.IsEarlierThan(wx.DateTimeFromDMY(01,01,1800)):
        return wx.DateTime()
    return value
    
  def SetValue(self, wxdatetime):
    if isinstance(wxdatetime, str):
        if wxdatetime == self.defaultformat:
          self.Value = self.defaultformat
        elif wx.DateTime().ParseFormat(wxdatetime, format=self.defaultparser):
          self.Value = wxdatetime
          self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
    else:
        if wxdatetime.IsValid():
            dateTmp = wxdatetime.FormatISODate().split('-')            
            self.Value = str(dateTmp[2]) + '/' + str(dateTmp[1]) + '/' + str(dateTmp[0])
            self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
        else:
            self.Value = self.defaultformat

  def kill_focus(self, event):
    myText = event.GetEventObject().GetValue()
    if isinstance(myText, str):
        if wx.DateTime().ParseFormat(myText, format=self.defaultparser) == -1:
          self.SetValue(self.defaultformat)
          self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
        else:
          self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
    else:
        if myText.IsValid() == False:
            self.SetValue(self.defaultformat)
            self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
        else:
            self.SetForegroundColour(wx.Colour(0, 0, 0, 255))            
    event.SetEventObject(self)
    event.Skip()
    
  def normal_colour(self, event):
    self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
    event.GetEventObject().Bind(wx.EVT_KILL_FOCUS, self.kill_focus, event.GetEventObject())
    
  def __init__(self, parent, id, dateforconstructor=wx.DateTime(), defaultformat = 'dd/mm/yyyy', name='', pos = None, size = wx.DefaultSize, style=0, value='', validator = wx.DefaultValidator):
    wx.TextCtrl.__init__(self, parent = parent, id = id, name = name, pos = pos, size = size, style = 0, validator = validator)
    
    self.SetMaxLength(10)
    self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
    self.Bind(wx.EVT_CHAR, self.OnTextCtrl1Char)
    self.Bind(wx.EVT_LEFT_DOWN, self.OnTextCtrl1LeftClick)
    self.Bind(wx.EVT_LEFT_DCLICK, self.OnTextCtrl1LeftDclick)
    self.Bind(wx.EVT_KILL_FOCUS, self.kill_focus, self)
    self.Bind(wx.EVT_SET_FOCUS, self.normal_colour, self)
    self.Bind(wx.EVT_TEXT_ENTER, self.OnTextCtrl1LeftDclick)
    self.defaultformat = defaultformat
    if self.defaultformat == 'dd/mm/yyyy':
      self.defaultparser = '%d/%m/%Y'
    else:
      self.defaultparser = '%m/%d/%Y'
    self.validator = validator
    if dateforconstructor.IsValid():
      pythonDate = datetime.date(dateforconstructor.GetYear(), dateforconstructor.GetMonth()+1, dateforconstructor.GetDay())
      self.SetValue(pythonDate.strftime(self.defaultparser))
    else:
      self.SetValue(self.defaultformat)

  def OnTextCtrl1LeftClick(self, event):
    if not event.GetEventObject().FindFocus() == self:
        if (isinstance(self.GetValue(), str) and self.GetValue() == self.defaultformat) or str(self.GetValue()) == "INVALID DateTime":
          event.GetEventObject().SetFocus()
          event.GetEventObject().SetInsertionPoint(0)
        else:
          event.Skip()
    else:
        event.Skip()

  def OnTextCtrl1LeftDclick(self, event):
    defaultformat = self.defaultformat
    dateToParse = self.GetValue()
    calendar = CalendarPopup(self, self.GetValue(), self.defaultformat, self.defaultparser)
    calendar.SetPosition(wx.Point(self.GetScreenPosition()[0], self.GetScreenPosition()[1]))
    calendar.ShowModal()
    #calendar.SetFocus()

  def OnTextCtrl1Char(self, event):
    defaultformat = self.defaultformat
    myTxt = event.GetEventObject()
    ignore = [314, 315, 316, 317]
    if event.GetKeyCode() == 9:
        if event.ShiftDown():
          self.Navigate(wx.NavigationKeyEvent.IsBackward)
        else:
          self.Navigate()
    a = myTxt.GetSelection()[0]
    b = myTxt.GetSelection()[1]
    if a == b and a == len(defaultformat) and not (event.GetKeyCode() in ignore) and event.GetKeyCode() <> 8:
      return
    if event.GetKeyCode() in ignore:
      event.Skip()
      
    elif event.GetKeyCode() == 8 or event.GetKeyCode() == 127:
      strTmp = myTxt.GetStringSelection()
      if len(strTmp.strip()) == 0:
        if event.GetKeyCode() == 8:
          #caso del del: da -1 a 0
          myIndex = a-1
        else:
          myIndex = a
        strTmp = '1'
      else:
        myIndex = myTxt.GetSelection()[0]
      #permetti solo canc e del per tutti i caratteri selezionati
      if myIndex >= 0:
        n = 0
        while n < len(strTmp):
          myTxt.Replace(myIndex, myIndex+1, defaultformat[myIndex])
          n += 1
          myIndex += 1
      if event.GetKeyCode() == 8:
        myIndex = myIndex -1
      myTxt.SetSelection(myIndex, myIndex)
    else:
      if myTxt.GetSelection()[0] <> myTxt.GetSelection()[1]:
        myTxt.SetInsertionPoint(myTxt.GetSelection()[0])
      if myTxt.GetSelection()[0] == myTxt.GetSelection()[1]:
        #nessun carattere selezionato
        #seleziona da selection 0 a selection 0 + 1 e in caso metti un numero
        a = myTxt.GetSelection()[0]
        b = myTxt.GetSelection()[1]
        myChar = myTxt.GetString(a, b+1)
        # controlla se diverso dai separatori
        if myChar in ['-', '/']:
          myTxt.SetSelection(a+1, b+1)
          return
        else:
          if chr(event.GetUniChar()).isdigit():
            #sostituisci il carattere
            myTxt.Replace(a, b+1, chr(event.GetUniChar()))
            myChar2 = myTxt.GetString(a+1, b+2)
            if myChar2 in ['-', '/']:
              myTxt.SetSelection(a+2, b+2)
    return
    
