#Boa:Dialog:calendarPopup
import wx
import wx.calendar
import datetime

CALENDAR_WIDTH = 208
SELECTED_FG = wx.Colour(0, 0, 0, 255)
INVISIBLE_HIGHLIGHT_FG = wx.Colour(0, 0, 0, 0)
INVISIBLE_HIGHLIGHT_BG = wx.Colour(255, 255, 255, 0)
VISIBLE_HIGHLIGHT_BG = wx.Colour(255, 200, 100, 0)
ID_ACTION = 100
ID_CANCEL = 101
butLabel = ''

class CalendarPopup(wx.Dialog):
    def _init_ctrls(self, prnt, mydatetoshow):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wx.NewId(), name='', parent=prnt,
            size=wx.DefaultSize,
            style=wx.SUNKEN_BORDER | wx.CAPTION | wx.STAY_ON_TOP, title='')
        if prnt:
            self.SetPosition(prnt.GetPosition())
        hSizer = wx.BoxSizer(wx.VERTICAL) 
        self.SetSizer(hSizer)
        date = self.choose_date(mydatetoshow)
        self.targetTxt = prnt
        self.cal = wx.calendar.CalendarCtrl(self,
          -1,
          date,
          pos = wx.Point(0,0),
          style = wx.calendar.CAL_MONDAY_FIRST
              | wx.calendar.CAL_SHOW_HOLIDAYS
        )
        self.SetClientSize((200,170))
        self.cal.Bind(wx.calendar.EVT_CALENDAR, self.day_toggled, id=self.cal.GetId())
        self.cal.Bind(wx.calendar.EVT_CALENDAR_SEL_CHANGED,
              self.highlight_changed,
              id=self.cal.GetId())
        self.cal.Bind(wx.EVT_RIGHT_DOWN, self.destroy_me,id=self.cal.GetId())
        self.Bind(wx.EVT_RIGHT_DOWN, self.destroy_me)
        self.Bind(wx.EVT_KILL_FOCUS, self.destroy_me)
        hSizer.Add(self.cal, 1, wx.ALIGN_LEFT |wx.EXPAND, 3)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL) 
        btn = wx.Button(self, ID_ACTION, "OK")
        btnc = wx.Button(self, ID_CANCEL, "C")
        btnSizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL)
        btnSizer.Add(btnc, 0, wx.ALIGN_CENTRE|wx.ALL)
        hSizer.Add(btnSizer, 0, wx.ALIGN_CENTRE|wx.ALL)
        btnSizer.Layout()
        hSizer.Layout()
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.destroy_me, id=ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.day_toggled, id=ID_ACTION)
        
    def __init__(self, parent, mydate, defaultformat, defaultparser):
        self.defaultformat = defaultformat
        self.defaultparser = defaultparser
        self._init_ctrls(parent, mydate)
        
    def choose_date(self, datetoshow):
        return datetoshow
        
    def shift_datetime(self, old_date, months):
        new_date = wx.DateTime()
        new_month = old_date.GetMonth() + months
        new_year = old_date.GetYear()
        if new_month < 0:
          new_month += 12
          new_year -= 1
        elif new_month > 11:
          new_month -= 12
          new_year += 1
        new_date.Set(old_date.GetDay(), new_month, new_year)
        return new_date
        
    def date_from_datetime(self, dt):
        new_date = datetime.date(dt.GetYear(), dt.GetMonth()+1, dt.GetDay())
        return new_date
        
    def show_highlight(self, calendar):
        calendar.SetHighlightColours(SELECTED_FG, VISIBLE_HIGHLIGHT_BG)
        
    def destroy_me(self, evt):
        self.Destroy()
        evt.Skip()

    def day_toggled(self, evt):
        cal = self.cal
        date = cal.GetDate()
        myDate = self.date_from_datetime(date)
        self.targetTxt.SetValue(myDate.strftime(self.defaultparser))
        self.Destroy()
        evt.Skip()

    def highlight_changed(self, evt, cal=None):
        if cal == None:
          cal = evt.GetEventObject()
        date = cal.GetDate()
        highlight = self.date_from_datetime(date)
        self.show_highlight(cal)
        cal.Refresh()
        evt.Skip()
