import wx, copy
import wx.lib.scrolledpanel as scrolled
import datetime as dt
import psconstants as psc
from psguiconstants import GUI_WINDOW_VARIANT
import os


text = """OBJECTIF: 
"""

class myFrame(wx.Panel):
    def __init__(self, listPeriods, parent=None, id=1, title='', pos = None, size = wx.Size(-1, -1), name='', callback=None): 
        wx.Panel.__init__(self, parent, id, size=parent.GetSize(), pos=pos, name=name, style=wx.BORDER_RAISED | wx.FULL_REPAINT_ON_RESIZE | wx.BORDER_RAISED)
        print 'listPeriods', listPeriods
        self.listPeriods = listPeriods
        self.bt2=''
        self.bt1=''
        self.dicoColor={'wx.Red':1, 'wx.Yellow':2, wx.Colour(248, 248, 248):3}
        self.listperiodo=[]
        self.periodoButtonT=[]
        self.col=[]
        self.col2=[]
        self.mycoleur=''
        self.tptable=[]
        jour = 0
        self.dico_statu_Bt={}
        self.dicoStatuButton={}
        self.dicoData={}
        self.dicoButton={}
        self.vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.callback = callback
        
        #Add panel
        conteneur = wx.Panel(self)
        
        
        
        #Add Font
        self.font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(9)
        
        #Add SIZER
        vbox= wx.BoxSizer (wx.VERTICAL)
        hbox= wx.BoxSizer (wx.HORIZONTAL)
        varchamp=''
        
        
        #Add descrition 
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st2 = wx.StaticText(conteneur, label='Periodo di prescrizione')
        st2.SetFont(self.font)
        hbox2.Add(st2)
        vbox.Add(hbox2, flag=wx.LEFT | wx.TOP, border=10)
        vbox.Add((-1, 5))
        
        #Add SIZER CADRE
        self.cadre = testPanel(conteneur, -1, pos=wx.Point(5,5), size=wx.Size(950, 400), style=wx.SUNKEN_BORDER)
        self.cadre.SetupScrolling() 
        hbox.Add(self.cadre, proportion=1, flag=wx.EXPAND)
        vbox.Add(hbox, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
        vbox.Add((1, 15))
        
        
        #Add Control Button non compilato
        self.btst = wx.Button(conteneur, -1, "Giorno con vasoattiva\n non compilato", size=(155,45), style=wx.STATIC_BORDER)
        self.btst.SetFont(self.font)
        #btst1.SetBackgroundColour("Yellow")
        self.btst.SetForegroundColour("Gray")
        self.btst.SetBackgroundColour("White")
        self.btst.Bind(wx.EVT_BUTTON, self.Kliselbt)
        #Add Control Button Giorni con 1 
        self.btst1 = wx.Button(conteneur, -1, "Giorno con 1 \n vasoattiva / inotropo", size=(155,45), style=wx.STATIC_BORDER)
        self.btst1.SetFont(self.font)
        self.btst1.SetBackgroundColour("Yellow")
        self.btst1.SetForegroundColour("Gray")
        self.btst1.Bind(wx.EVT_BUTTON, self.Kliselbt)
        
        #Add Control Button Giorni con 2 o piu
        self.btst2 = wx.Button(conteneur, -1, "Giorni con 2 o piu \n vasoattivi / inotropi", name="pipo" ,size=(155,45), style=wx.STATIC_BORDER)
        self.btst2.SetFont(self.font)
        self.btst2.SetBackgroundColour("Red")
        self.btst2.SetForegroundColour("Gray")
        self.btst2.Bind(wx.EVT_BUTTON, self.Kliselbt)
         
        #Add Control Radio Button 
        """self.btsalva = wx.Button(conteneur, -1, "Salva", size=(75,35), style=wx.STATIC_BORDER)
        self.btsalva.Bind(wx.EVT_BUTTON, self.savestatuts)
        self.btsalva.SetFont(self.font)"""
        #hsavsizer.Add(self.btsalva, flag=wx.LEFT, border=497)
        sampleList = ['Precoce', 'Tempestiva  ', 'Ritardata  ']
        txt1 = wx.StaticText(conteneur, -1, "Per compilare i Farmaci vasoattivi, selezionare uno dei pulsanti giallo, rosso o bianco \nsuccessivamente cliccare sulle date interessate.")
        txt1.SetForegroundColour("Blue")
        #txt1.SetFont(self.font)       
        txt2=wx.StaticText(conteneur, -1, "Per selezionare piu date contemporaneamente, cliccare sulla data di inizio selezione \ne successivamente tenendo premuto il tasto SHIFT sulla data di fine selezione.")
        txt2.SetForegroundColour("Blue")
        #txt2.SetFont(self.font)
        #vbox.Add(btst, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        
        gs = wx.BoxSizer(wx.HORIZONTAL)
        #gs.Add(rb, 0, wx.RIGHT, 5)
        gs.Add(self.btst, 0, flag=wx.LEFT, border=1)
        gs.Add(self.btst1,flag=wx.LEFT, border=30)
        gs.Add(self.btst2, flag=wx.LEFT, border=30)
        
        """gs.Add(self.btsalva, flag=wx.LEFT, border=110)"""
        #vbox1.Add(rb, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10) 
        vbox.Add(gs, flag=wx.CENTER, border=20) 
        #vbox.Add((1, -10))
        
        hs = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add((-1, -50))
        
        #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        #Add Control Button non compilato
        """self.bton = wx.Button(conteneur, -1, "", size=(170,55), style=wx.STATIC_BORDER)
        self.bton.SetFont(self.font)
        #btst1.SetBackgroundColour("Yellow")
        self.bton.SetForegroundColour("Gray")
        self.bton.SetBackgroundColour("White")
        #self.bton.Hide()
        
        #Add Control Button Giorni con 1 
        self.bton1 = wx.Button(conteneur, -1, "", size=(170,55), style=wx.STATIC_BORDER)
        self.bton1.SetFont(self.font)
        self.bton1.SetBackgroundColour("Yellow")
        #self.bton1.Hide()
        
        #Add Control Button Giorni con 2 o piu
        self.bton2 = wx.Button(conteneur, -1, "" ,size=(170,55), style=wx.STATIC_BORDER)
        self.bton2.SetFont(self.font)
        self.bton2.SetBackgroundColour("Red")
        #self.bton2.Hide()
          
        gsbton = wx.BoxSizer(wx.HORIZONTAL)
        #gs.Add(rb, 0, wx.RIGHT, 5)
        gsbton.Add(self.bton, 0, flag=wx.LEFT, border=-260)
        gsbton.Add(self.bton1,flag=wx.LEFT|wx.RIGHT, border=15)
        gsbton.Add(self.bton2, flag=wx.RIGHT, border=5)
        
        #vbox1.Add(rb, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10) 
        vbox.Add(gsbton, flag=wx.CENTER, border=10) """
        
        vbox.AddSpacer(70)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add((1, 5))
        #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        
        hs.Add(txt1, flag=wx.LEFT , border=20)
        #vbox.Add((-1, 1))
        hs.Add(txt2, flag=wx.LEFT , border=20)
        vbox.Add(hs)
        vbox.Add((-1, 10))
        self.priodopres()
        
        #print self.dicoData
        #print self.dicoData['2011-10-01']
        conteneur.SetSizer(vbox)
        conteneur.SetSize(self.GetSize())
        conteneur.Fit()
        conteneur.Layout()
        self.colorwirt(self.btst)
        
    def priodopres(self):

        self.listperiodo = str(self.listPeriods)
        exec('self.listperiodo = ' + self.listperiodo)
        for periodo in self.listperiodo:
            if periodo and len(periodo) == 2:
                self.creatjour(periodo[0],periodo[1])    
    
        self.cadre.SetSizer(self.vbox1)   
        #self.cadre.Fit()   
        self.vbox1.Layout()
        
        
    def creatjour(self, datinit, datend):
        #BTday =wx.Button(self.cadre, -1,size=(50, 50),style=wx.RAISED_BORDER )
        hbox = wx.BoxSizer(wx.HORIZONTAL)    
        vbox = wx.BoxSizer(wx.VERTICAL)
       
        self.formadate(datinit, datend)
        numDays = self.recupdays(datinit, datend)
        numdate = len(numDays)
        lisjust=[]
       #CREATION BUTTON a l'inizione prim caricamento dati
        for k in range(numdate):
            grid1 = wx.GridBagSizer(1, 2)
            x=0
            y=1
            
            grid1.Add(wx.StaticText(self.cadre, 0, '%s' %self.NbMonth[k], (5, 5)), pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=15)
            listaBottoni = []
            for day in numDays[k]:
                Bt = wx.Button(self.cadre, -1, label=self.dicoData[day], name=day, size=(50,50), style=wx.STATIC_BORDER)
                # couleur=self.setBt(day)
                Bt.SetBackgroundColour('White')
                Bt.Bind(wx.EVT_BUTTON, self.likselct)
                # Bt est il Button generato salva in un diszionario: self.dicoButton[day] =Bt
                listaBottoni.append(Bt)
                self.dicoButton[day] =Bt
                #self.periodoButtonT=[day]=[]
            lisjust = lisjust + listaBottoni
            gs = wx.FlexGridSizer(3, 11, 3, 3)
            gs.AddMany(lisjust)
            lisjust=[]
            grid1.Add(gs, pos=(0,1), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=1)
        #vbox.Add((-1, 15))   
            self.vbox1.Add(grid1, proportion=0, flag=wx.ALL|wx.EXPAND, border=2)
    
    
        
    def recupdays(self, datinit, datend):
    
        dataInizio = dt.datetime.strptime(datinit, '%Y-%m-%d')
        dataFine = dt.datetime.strptime(datend, '%Y-%m-%d')
        Settima = ['Lun', 'Mar', 'Mer', 'Gio','Ven', 'Sab', 'Dom']
        
        valdat=''
        valdays=''
        Mesi={'1':'Gen',
                   '2':'Feb',
                   '3':'Mar',
                   '4':'Apr',
                   '5':'Mag',
                   '6':'Giu',
                   '7':'Lug',
                   '8':'Ago',
                   '9':'Set',
                   '10':'Ott',
                   '11':'Nov',
                   '12':'Dic'}
        meseSalvato = 0
        self.NbMonth=[]
        listaGiorni = []
        listaTmp = []
        anomese=''
        while (dataInizio <= dataFine):
            if dataInizio.month != meseSalvato:
                if listaTmp:
                    listaGiorni.append(listaTmp)
                    listaTmp = []
                valdat=dt.date(dataInizio.year, dataInizio.month, dataInizio.day).isoformat()
                valdays= '%s\n%d\n%s' % (Settima[dt.date.weekday(dataInizio)], dataInizio.day, Mesi[str(dataInizio.month)])
                self.dicoData[valdat] =valdays
                #self.dico_other[]
                listaTmp.append(valdat)
                dataInizio = dataInizio + dt.timedelta(days=1)
                meseSalvato = dataInizio.month
                anomese = '%s-%d' % ( Mesi[str(dataInizio.month)],dataInizio.year)
                if anomese not in self.NbMonth:
                    self.NbMonth.append(anomese)
            else:
                valdat=dt.date(dataInizio.year, dataInizio.month, dataInizio.day).isoformat()
                valdays= '%s\n%d\n%s' % (Settima[dt.date.weekday(dataInizio)], dataInizio.day, Mesi[str(dataInizio.month)])
                self.dicoData[valdat] =valdays
                listaTmp.append(valdat)
                anomese = '%s-%d' % ( Mesi[str(dataInizio.month)],dataInizio.year)
                dataInizio = dataInizio + dt.timedelta(days=1)
                if anomese not in self.NbMonth:
                    self.NbMonth.append(anomese)

        if listaTmp is not None:
            listaGiorni.append(listaTmp)
        
        return listaGiorni
     
    #data in formato normal per visualisalo gg/mese/anno    
    def formadate(self, datinit, datend):
                
        # split the datinit end datend string into month, day, year
        year_init, month_init, day_init = datinit.split("-")
        year_end, month_end, day_end  = datend.split("-")
        
        dt_init =dt.date(int(year_init), int(month_init), int(day_init)).strftime("%d/%m/%y")
        dt_end =dt.date(int(year_end), int(month_end), int(day_end)).strftime("%d/%m/%y")
        
        #first sizer
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st2 = wx.StaticText(self.cadre, label='Periodo : dal %s al %s ' % (dt_init, dt_end))
        st2.SetFont(self.font)
        hbox2.Add(st2)
        self.vbox1.Add(hbox2, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=10)
        self.vbox1.Add((1, 1))
    
    def retoucolor(self, namebt):
        colo=self.dicoButton[namebt].GetBackgroundColour()
        if colo==wx.Colour(255, 255, 0):
            return 1
        if colo==wx.Colour(255, 0, 0):
            return 2
        return 0
            
    def SetValue(self, valueDict):
        #adapter for Prosafe: checks if dict is in str/unicode format and eventually turns it up in a real dict
        if not self.listPeriods:
            valueDict = {}

        if type(valueDict) == str or type(valueDict) == unicode:
            myDict = dict()
            valueDict = valueDict.replace('{','').replace('}','').replace(' ','')
            valueList = valueDict.split(',')
            for val in valueList:
                if not val:
                    break
                val1, val2 = val.split(':')
                myDict[val1.replace('\'', '')] = int(val2)
            valueDict = myDict
        
        keepKeys = []
        if type(valueDict) == dict:
            for key in valueDict:
                colourForButton = self.takcolor(valueDict[key])
                if key in self.dicoButton.keys():
                    self.dicoButton[key].SetBackgroundColour(colourForButton)
                else:
                    keepKeys.append(key)
        
        for key in keepKeys:
            valueDict.pop(key)
        if not valueDict:
            self.callback(None)
        
    def GetValue(self):
        valueDict = dict()
        if self.listPeriods:
            for key in self.dicoButton.keys():
                valueDict[key] = self.retoucolor(key)
        return str(valueDict)
        
    def takcolor(self, val):
        if val==0:
            return wx.Colour(248, 248, 248)
        if val==1 :
            return wx.Colour(255, 255, 0)
        if val==2:
            return wx.Colour(255, 0, 0)
        
    
    def Kliselbt(self, event):
        self.col2=[]
        Btn=event.GetEventObject()
        Btn.SetForegroundColour("Black")
        self.col2.append(Btn.GetBackgroundColour())
        self.colorwirt(Btn)
        #print self.dicoButton['2010-08-06'].GetBackgroundColour()
    
    def colorwirt(self, name):
        miocursore=''
        if name == self.btst :
            #change Button and mouse color
            self.btst1.SetForegroundColour("Gray")
            self.btst2.SetForegroundColour("Gray")
            """self.bton.Show()
            self.bton1.Hide()
            self.bton2.Hide()"""
            wx.Icon(os.path.join(psc.imagesPath, "hdwhite.cur"), wx.BITMAP_TYPE_ICO)
            miocursore= wx.Cursor(os.path.join(psc.imagesPath, "hdwhite.cur"),wx.BITMAP_TYPE_CUR)
            self.cadre.SetCursor(miocursore)
        
        if name == self.btst1 :
            #change Button and mouse color
            """self.bton1.Show()
            self.bton2.Hide()
            self.bton.Hide()"""
            
            self.btst.SetForegroundColour("Gray")
            self.btst2.SetForegroundColour("Gray")
            
            miocursore = wx.Cursor(os.path.join(psc.imagesPath, "hdyellow.cur"), wx.BITMAP_TYPE_CUR)
            self.cadre.SetCursor(miocursore)
            
            
        if name == self.btst2 :
            #change Button and mouse color
            self.btst1.SetForegroundColour("Gray")
            self.btst.SetForegroundColour("Gray")
            """self.bton2.Show()
            self.bton.Hide()
            self.bton1.Hide()"""
            miocursore = wx.Cursor(os.path.join(psc.imagesPath, "harred.cur"), wx.BITMAP_TYPE_CUR)
            self.cadre.SetCursor(miocursore)
            
    #Salvare lo statut delle Button
    """def savestatuts(self, event):
        return self.GetValue()"""
        
    
    def OnCloseMe(self, event):
        self.Close(True)

    
    def likselct(self, event):
        colo=''
        
        couleur =''
        Btn=event.GetEventObject()
        #giorno farmacho con un clic su un giorno 
        if not wx.GetKeyState(wx.WXK_SHIFT):
            if self.col2:
                Btn.SetBackgroundColour(self.col2[0])
            else: pass
                       
            self.tptable=[]
                #colo=Btn.GetBackgroundColour()
            self.col.append(couleur)  
                
            self.tptable.append(Btn.GetName())
        #giorno farmacho con un Shift su piu giorni    
        if wx.GetKeyState(wx.WXK_SHIFT):
            #Btn.SetBackgroundColour(self.col2[0])
            self.tptable.append(Btn.GetName())
            if len(self.tptable) == 2:
                if self.tptable[0] == self.tptable[1]:
                   self.tptable[0]=copy.copy(self.tptable[1]) 
                if self.tptable[0] != self.tptable[1]:
                    self.bt2 = self.tptable[0]
                    self.bt1 = self.tptable[1]
                    dataInizio = min(dt.datetime.strptime(self.bt1, '%Y-%m-%d'), dt.datetime.strptime(self.bt2, '%Y-%m-%d'))
                    dataFine = max(dt.datetime.strptime(self.bt1, '%Y-%m-%d'), dt.datetime.strptime(self.bt2, '%Y-%m-%d'))
                    
                    btname=''
                    while (dataInizio <= dataFine):
                        btname='%d-%02d-%02d' % (dataInizio.year, dataInizio.month, dataInizio.day)
                        if btname in self.dicoButton.keys():     
                            if self.col and self.col2 and self.dicoButton:
                                self.dicoButton[btname].SetBackgroundColour(self.col2[0])
                            else: pass
                        else: pass
                        dataInizio = dataInizio + dt.timedelta(days=1)
                    self.tptable=[]
                    #self.tptable=[]
            if len(self.tptable) > 2: self.tptable=[]
        self.callback(event)
    
        
class testPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, id, pos, size, style):
        scrolled.ScrolledPanel.__init__(self, parent, -1, pos, size, style)
    
class monAppli(wx.App):
    def OnInit(self):
        listPeriods = [['2010-08-06','2010-11-15'],['2010-11-25','2010-12-10'],['2011-01-01','2011-02-15'],['2011-02-20','2011-03-10']]
        
        fr = wx.Frame(None, pos=wx.DefaultPosition, size=wx.DefaultSize,  name="main frame", )
        fen=myFrame(parent = fr, title='PETALO Start', listPeriods = listPeriods)
        valueDict = dict()
        valueDict["2010-08-06"]= 1
        valueDict["2010-08-07"]= 1
        valueDict["2010-08-08"]= 1
        valueDict["2010-08-09"]= 1
        
        fen.SetValue(valueDict)
        fen.SetSize(wx.Size(860,550))
        fr.SetSize(wx.Size(860,550))
        fr.Centre()
        fr.Show()
        return True

        
if __name__ == '__main__':
    app = monAppli(redirect=False)
    app.MainLoop()    