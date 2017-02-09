import wx
import datetime
import time

class NotEmptyValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return NotEmptyValidator()
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if text == '':
            #wx.MessageBox("This field must contain some text!", "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
            wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True
    

class NotEmptyOrFutureDateValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return NotEmptyOrFutureDateValidator()
    
    def Validate(self, win):
        print 'validating NotEmptyOrFutureDateValidator'
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if text.IsValid() == False:
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False

        isoDate = text.FormatISODate()
        date = datetime.date(*(time.strptime(isoDate,"%Y-%m-%d")[:3]))
        if date > datetime.date.today():
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False

        textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        textCtrl.Refresh()
        return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True

class NotEmptyOrFutureOrPastDateValidator(wx.PyValidator):
    def __init__(self, functionForValidDate):
        self.functionForValidDate = functionForValidDate
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return NotEmptyOrFutureOrPastDateValidator(self.functionForValidDate)
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if text.IsValid() == False:
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False

        isoDate = text.FormatISODate()
        date = datetime.date(*(time.strptime(isoDate,"%Y-%m-%d")[:3]))
        if date > datetime.date.today():
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        import psconstants
        if not self.functionForValidDate(psconstants.coreCrfName, isoDate):
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False

        textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        textCtrl.Refresh()
        return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True

        
class UsernameValidator(wx.PyValidator):
    
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return UsernameValidator()
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()

        if text == '' or ' ' in text:
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True
    


class PasswordValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return PasswordValidator()
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if len(text) < 8:
            wx.MessageBox("Password must be 8 or more characters in length.", "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
            wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True
    

class PasswordOrEmptyValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return PasswordOrEmptyValidator()
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if len(text) < 8 and text != '':
            wx.MessageBox("Password must be 8 or more characters in length.", "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
            wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True



    
class PasswordAgainValidator(wx.PyValidator):
    def __init__(self, othercontrol):
        wx.PyValidator.__init__(self)
        self.othercontrol = othercontrol
        
    def Clone(self):
        return PasswordAgainValidator(self.othercontrol)
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if text != self.othercontrol.GetValue():
            wx.MessageBox("Password mismatch.", "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
            wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True


class HourValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return NotEmptyValidator()
    
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        if self.ValidHour(text) == False:
            #wx.MessageBox("This field must contain a valid hour in the form HH:MM!", "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(
            wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
        
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True
    
    def ValidHour(self,  hourstring):
        pieces = hourstring.split(':')
        if len(pieces) != 2:
            return False
        else:
            try:
                hours = int (pieces[0])
                mins = int (pieces[1])
            except:
                return False
            
            if hours > 23 or hours < 0:
                return False
            
            if mins > 59 or mins < 0:
                return False
            
        return True
