import wx
import wx.lib.mixins.listctrl as listmix
import psconstants as psc

class CustColumnSorterMixin(listmix.ColumnSorterMixin):

    def __init__(self, numColumns):
        listmix.ColumnSorterMixin.__init__(self, numColumns)

    def OnSortOrderChanged(self):
        for i in range(self.GetItemCount()):
            if i % 2 == 0:
                self.SetItemBackgroundColour(i,(206, 218, 255))
            else:
                self.SetItemBackgroundColour(i,(255, 255, 255))

    def GetColumnSorter(self):
        return self.CustColumnSorter

    def CustColumnSorter(self, key1, key2):
        col, ascending = self.GetSortState()
        item1 = self.itemDataMap[key1][col]
        item2 = self.itemDataMap[key2][col]

        str1 = item1
        str2 = item2
        splititem1 = item1.split('/')
        splititem2 = item2.split('/')
        if len(splititem1) == 3 and len(splititem2) == 3:
            splititem1.reverse()
            splititem2.reverse()
            str1 = '-'.join(splititem1)
            str2 = '-'.join(splititem2)

        cmpVal = cmp(str1,str2)

        if cmpVal == 0:
            cmpVal = cmp(*self.GetSecondarySortValues(col, key1, key2))

        if ascending:
            return cmpVal
        else:
            return -cmpVal

class PSList(wx.ListView, CustColumnSorterMixin):

    def __init__(self, parent, centreCode, openAdmissionCallback, shouldAnonymizeData):
        
        wx.ListView.__init__(self, parent, id=-1, style=wx.LC_REPORT |wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)

        #TODO: mess in appconfig.py about grid column stuff
        self.shouldAnonymizeData = shouldAnonymizeData
        from mainlogic import _
        columns = []
        columns.append(_("Admission code"))
        for label in psc.gridColumnLabels:
            columns.append(_(label))
        columns.append(_("Core status"))
        columns.append(_("Petals complete"))

        CustColumnSorterMixin.__init__(self, len(columns))
 
        self.centreCode = centreCode

        self.sortColumn = 0
        self.sortAscending = 1

        self.openAdmissionCallback = openAdmissionCallback

        self.itemDataMap = dict()
        
        self.actualAdmissionKeysToAdmissionKeys = dict()

        from mainlogic import _
 
        #for i, key in enumerate(psc.gridColumnList):
        for i, key in enumerate(columns):
            #columnName = psc.gridColumnDict[key]
            columnName = key
            self.InsertColumn(i, _(columnName), format=wx.LIST_FORMAT_CENTRE)

        #bind double click event
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.openAdmission)
        list = self.GetListCtrl()
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, list)

        self.gridColumns = psc.gridColumnAttributes + ('statusValue','petalsComplete')
        
    def OnColClick(self, evt):
        oldCol = self._col
        self._col = col = evt.GetColumn()
        self._colSortFlag[col] = int(not self._colSortFlag[col])
        self.GetListCtrl().SortItems(self.GetColumnSorter())
        self.OnSortOrderChanged()

    def DoSort(self):
        self._col = self.sortColumn
        self._colSortFlag[self.sortColumn] = self.sortAscending
        self.GetListCtrl().SortItems(self.GetColumnSorter())
        self.OnSortOrderChanged()

    def OnSortOrderChanged(self):
        self.sortColumn, self.sortAscending = self.GetSortState()
        for i in range(self.GetItemCount()):
            if i % 2 == 0:
                self.SetItemBackgroundColour(i,(206, 218, 255))
            else:
                self.SetItemBackgroundColour(i,(255, 255, 255))

    def GetListCtrl(self):
        return self
 
    def selectItem(self,admissionKey):
        idx = self.FindItem(0,self.reformatAdmissionKey(admissionKey),False)
        if idx == -1:
            return
        self.Focus(idx)
        self.Select(idx,True)

    def updateColumnWidths(self):
        xSize = self.GetSize().x
        colsize = int(xSize / self.GetColumnCount())
        for i in range(self.GetColumnCount()):
            self.SetColumnWidth(i,colsize)
      
    def GetListCtrl(self):
        return self        
 
    #def dateToPretty(self,date):
    #    splitdate = date.split('-')
    #    splitdate.reverse()
    #    return '/'.join(splitdate)

    #def prettyToDate(self,date):
    #    splitdate = date.split('/')
    #    splitdate.reverse()
    #    return '-'.join(splitdate)

    def reformatAdmissionKey(self, admissionKey):
        actualAdmissionKey = admissionKey
        splitAdmissionKey = admissionKey.split('-')
        if len(splitAdmissionKey) == 4:
            actualAdmissionKey = '-'.join((splitAdmissionKey[0],splitAdmissionKey[1],splitAdmissionKey[3]))
        splitAdmissionKey = actualAdmissionKey.split('-')
        if len(splitAdmissionKey) == 3:
            if splitAdmissionKey[1] == '':
                actualAdmissionKey = '-'.join((splitAdmissionKey[0],self.centreCode,splitAdmissionKey[2]))
        splitAdmissionKey = actualAdmissionKey.split('-')
        if len(splitAdmissionKey) == 3:
            if splitAdmissionKey[2].isdigit():
                actualAdmissionKey = '-'.join((splitAdmissionKey[0],splitAdmissionKey[1],"%04d" % int(splitAdmissionKey[2])))
        return actualAdmissionKey 

    def refreshData(self, data, admissionsToEvaluate=None):
        from mainlogic import _
        if admissionsToEvaluate:
            admissionsToEvaluate = set(admissionsToEvaluate)
        self.itemDataMap = self.buildDataMap(data)
        self.DeleteAllItems()        
        rindex = 0
        #for item in data:
        #    for i, key in enumerate(psc.gridColumnList):
        #        columnName = psc.gridColumnDict[key]
        #        if key == 'admissionKey':
        #            self.InsertStringItem(rindex, item[key])
        #            continue
        #        if item[key] != None:
        #            value = item[key]
        #            if key in psc.gridColumnTypes and psc.gridColumnTypes[key] == 'datetime':
        #                value = self.dateToPretty(value)
        #            self.SetStringItem(rindex, i, unicode(value))
        #TODO MERGE: in psconstants, implement using generic psc.gridColumnTypes
        for item in data:
            actualAdmissionKey = self.reformatAdmissionKey(item['admissionKey'])
            self.actualAdmissionKeysToAdmissionKeys[actualAdmissionKey] = item['admissionKey']
            litem = self.InsertStringItem(rindex, actualAdmissionKey)
            colour = (255,255,255)
            if rindex % 2 == 0:
                colour = (206,218,255)
            self.SetItemBackgroundColour(litem,colour)
            cindex = 1
            textData = psc.rowDataToText(item)
            for key in self.gridColumns:
                value = textData[key]
                if not value and key != 'petalsComplete':
                    if self.shouldAnonymizeData:
                        value = '--------'
                    else:
                        value = ""
                
                if key == 'petalsComplete':
                    if value == True:
                        value = _("Yes")
                    elif value == False:
                        value = _("No")
                    else:
                        value = ""
                if key == 'statusValue' and admissionsToEvaluate and textData['admissionKey'] in admissionsToEvaluate:
                    value = "%s (%s)" % (value, _("updating"))
                
                if key in psc.gridColumnAttributes and value and self.shouldAnonymizeData:
                    value = '--------'
                self.SetStringItem(rindex, cindex, unicode(value))
                cindex += 1
            self.SetItemData(rindex, rindex)
            rindex += 1

    def buildDataMap(self, data):
        prov = dict()
        rindex = 0
        #for item in data:
        #    elementForDataMap = []
        #    for key in psc.gridColumnList:
        #TODO MERGE: in psconstants, implement using generic psc.gridColumnTypes
        for item in data:
            elementForDataMap = []
            actualAdmissionKey = self.reformatAdmissionKey(item['admissionKey'])
            elementForDataMap.append(actualAdmissionKey)
            for key in self.gridColumns:
                if key in item:
                    elementForDataMap.append(unicode(item[key]))
            prov[rindex] = tuple(elementForDataMap)
            rindex += 1
        return prov
 
    def getRowData(self, rowNo):
        rowText = {'admissionKey': self.actualAdmissionKeysToAdmissionKeys[self.GetItem(rowNo, 0).GetText()]}
        #print self.GetItem(rowNo, 0), self.GetItem(rowNo, 0).GetText(), self.actualAdmissionKeysToAdmissionKeys
        for i, attribute in enumerate(self.gridColumns):
            rowText[attribute] = self.GetItem(rowNo,i+1).GetText()
            #print self.GetItem(rowNo,i+1).GetText()
        out = psc.rowTextToData(rowText)
        return out

    def openAdmission(self, event):
        """ apre un ricovero aperto da doppio click sulla lista"""
        rowNo = event.GetIndex()
        rowData = self.getRowData(rowNo)
        self.openAdmissionCallback(rowData)

