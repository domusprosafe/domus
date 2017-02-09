import wx
import datetime
import re

def create(parent):
    return HourTextbox(parent)

class HourTextbox(wx.TextCtrl):

    #def init_ctrls(self, prnt):
    #    self.textCtrl1 = wx.TextCtrl(id=wx.NewId(), name='',
    #          parent=prnt, pos=wx.DefaultPosition, size=wx.DefaultSize,
    #          style=0, value='')
    #    self.textCtrl1.SetMaxLength(5)
    #    self.textCtrl1.SetForegroundColour(wx.Colour(169, 169, 169, 255))
    #    self.textCtrl1.Bind(wx.EVT_CHAR, self.OnTextCtrl1Char)
    #    self.textCtrl1.Bind(wx.EVT_LEFT_DOWN, self.OnTextCtrl1LeftClick)
    #    self.textCtrl1.Bind(wx.EVT_KILL_FOCUS, self.kill_focus)
    #    self.textCtrl1.Bind(wx.EVT_SET_FOCUS, self.normal_colour)
    #    self.regex = ''
    #    self.default = 'hh:mm'
    
    def GetValue(self):
        strTmp = self.Value
        if re.search(self.regex, strTmp) is None:
            strTmp = ''
        return strTmp
    
    def SetValue(self, hour):
        if re.search(self.regex, hour) is None:
            hour = self.default
            self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
        else:
            self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
        self.Value = hour
    
    def kill_focus(self, event):
        myText = event.GetEventObject().GetValue()
        if re.search(self.regex, myText) is None:
            self.SetValue(self.default)
            self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
        else:
            self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
        event.SetEventObject(self)
        event.Skip()
        #self.ProcessEvent(event)

    def normal_colour(self, event):
        event.Skip()
        self.SetForegroundColour(wx.Colour(0, 0, 0, 255))
   
    def __init__(self, parent, id, hour, name='', pos = wx.DefaultPosition, size = wx.DefaultSize, style=0, value='' ):
        wx.TextCtrl.__init__(self, parent = parent, id = id, name = name, pos = pos, size = size, style = style)  
        self.SetMaxLength(5)
        self.SetForegroundColour(wx.Colour(169, 169, 169, 255))
        self.Bind(wx.EVT_CHAR, self.OnTextCtrl1Char)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnTextCtrl1LeftClick)
        self.Bind(wx.EVT_KILL_FOCUS, self.kill_focus)
        self.Bind(wx.EVT_SET_FOCUS, self.normal_colour)
        self.default = 'hh:mm'
 
        self.regex = '^(([0-1][0-9])|([2][0-3]))[:]([0-5][0-9])$'      
        if re.search(self.regex, hour) is None:
            self.SetValue(self.default)
        else:
            self.SetValue(hour)

    def OnTextCtrl1LeftClick(self, event):
        if not event.GetEventObject().FindFocus() == self:
            if self.GetValue() == self.default or self.GetValue() == '':
                event.GetEventObject().SetFocus()
                event.GetEventObject().SetInsertionPoint(0)
                return
        event.Skip()   

    def OnTextCtrl1Char(self, event):
        myTxt = event.GetEventObject()
        ignore = [314, 315, 316, 317]
        if event.GetKeyCode() == 9:
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                self.Navigate()
        a = myTxt.GetSelection()[0]
        b = myTxt.GetSelection()[1]
        if a == b and a == len(self.default) and not event.GetKeyCode() in ignore and not event.GetKeyCode() == 8:
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
                    myTxt.Replace(myIndex, myIndex+1, self.default[myIndex])
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
                if myChar == ':':
                    myTxt.SetSelection(a+1, b+1)
                    return
                else:
                    if chr(event.GetUniChar()).isdigit():
                        #sostituisci il carattere
                        myTxt.Replace(a, b+1, chr(event.GetUniChar()))
                        myChar2 = myTxt.GetString(a+1, b+2)
                        if myChar2 == ':':
                            myTxt.SetSelection(a+2, b+2)
        return
    
