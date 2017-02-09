import wx

class PSGridSizer(wx.GridBagSizer):
    def __init__(self, rows, cols, maxcolitems=0):
        wx.GridBagSizer.__init__(self, rows, cols)
        self.rows = rows
        self.cols = cols
        self.maxcolitems = maxcolitems
        self.children = []

    def Add(self, window, proportion=0, flag=0, border=0):
        actlen = len(self.GetChildren())
        if self.maxcolitems == 0:
            currentcolumn = 0
            currentrow = actlen
        else:
            currentcolumn = actlen / self.maxcolitems
            currentrow = actlen % self.maxcolitems
        try:
            wx.GridBagSizer.Add(self, window, (currentrow,currentcolumn), wx.DefaultSpan, flag, border)
            self.children.append(window)
        except:
            raise

    def Detach(self, window):
        if window in self.children:
            self.children.remove(window)
        return wx.GridBagSizer.Detach(self, window)

    def Remove(self, window):
        if window in self.children:
            self.children.remove(window)
        return wx.GridBagSizer.Remove(self, window)

    def Compact(self):
        shownItemIds = []
        for i in range(len(self.children)):
            if not self.GetItem(i).IsShown():
                continue
            if i < len(self.children)-1 and type(self.GetItem(i).GetWindow()) == wx.StaticText and type(self.GetItem(i+1).GetWindow()) == wx.StaticText:
            #if (i < len(self.children)-1 and type(self.GetItem(i).GetWindow()) == wx.StaticText and type(self.GetItem(i+1).GetWindow()) == wx.StaticText) or (i < len(self.children)-1 and type(self.GetItem(i).GetWindow()) == wx.StaticText):
                self.GetItem(i).Hide()
                continue
            shownItemIds.append(i)
        itemcount = len(shownItemIds)
        done = False
        offset = 0
        maxcolitems = self.maxcolitems
        while not done:
            if maxcolitems != 0:
                cols = itemcount / maxcolitems + 1
                voids = maxcolitems - itemcount % maxcolitems - 1
                maxcolitems -= voids/cols
            else:
                if self.cols not in [0,1]:
                    cols = self.cols
                    maxcolitems = itemcount / (cols-1)
                    voids = maxcolitems - itemcount % maxcolitems - 1
                    maxcolitems -= voids/cols
                else:
                    cols = 1
                    maxcolitems = itemcount
            maxcolitems += offset
            done = True
            if cols == 1:
                break
            for c in range(cols):
                id = (c+1) * maxcolitems - 1
                if id >= len(shownItemIds):
                    break
                i = shownItemIds[id]
                if i >= len(self.children):
                    break
                if type(self.GetItem(i).GetWindow()) == wx.StaticText:
                    offset += 1
                    done = False
            if offset == 10:
                break
 
        lastpos = None
        r = 0
        c = 0
        gr = 1000
        for i in range(len(self.children)):
            self.SetItemPosition(i,(gr,0))
            gr += 1
        for i in range(len(self.children)):
            if not self.GetItem(i).IsShown():
                continue
            pos = self.GetItemPosition(i)
            ret = self.SetItemPosition(i,(r,c))
            if maxcolitems == 0:
                r += 1
            else:
                if r < maxcolitems-1:
                    r += 1
                else:
                    r = 0
                    c += 1


class PSFlexGridSizer(wx.FlexGridSizer):
    def __init__(self, rows, cols, maxcolitems=0):
        wx.FlexGridSizer.__init__(self, rows, cols)


