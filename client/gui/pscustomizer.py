import wx, copy, os
import string
import datetime 

class closedialog(wx.Dialog):
    def __init__(self, parent, title,var=None):
        from mainlogic import _
        wx.Dialog.__init__(self, parent, title=title, size=(350,200))
        self.page=''
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        import psconstants as psc
        import os
        png_image = wx.Image(os.path.join(psc.imagesPath,'Warning1.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        warning_img=wx.StaticBitmap(self,-1,png_image,pos=wx.Point(15,10))
        
        
        Label=wx.StaticText(self,label=_("Msgclosing") ,pos=wx.Point(35, 70))
        hbox.Add(Label,0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.bt_ok=wx.Button(self,label=_('bt_ok'),pos=wx.Point(100, 135))
        self.bt_non=wx.Button(self,label=_('bt_no'),pos=wx.Point(200, 135))
       
        self.bt_non.Bind(wx.EVT_BUTTON,self.onbt_no)
        self.bt_ok.Bind(wx.EVT_BUTTON,self.onbt_ok)
        
    def onbt_ok(self,  EVT):
        
        self.page='ok'
        self.Destroy()
        
    def onbt_no(self,  EVT):
        self.Destroy()
        
    # def onbt_anul(self,  EVT):
        # self.Destroy()
        
class changedialog(wx.Dialog):
    # def __init__(self, parent, title):
    def __init__(self, parent, title, group_name=None, old_name=None):
       
        wx.Dialog.__init__(self, parent, title=title, size=(400,250))
        # super(changedialog,self).__init__(parent=parent, title=title, size=(300,250))
        from mainlogic import _
        
        # self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.var_chang=''
        # self.var_chang=''
        panel=wx.Panel(self)
        vbox=wx.BoxSizer(wx.VERTICAL)
        
        sb_inf = wx.StaticBox(panel, label=_('Info'))
        #sb_info.set 
        sbs = wx.StaticBoxSizer(sb_inf, wx.VERTICAL)
        
        labelmsg=wx.StaticText(panel,-1,_('msginfo'),(-1, -1), (-1, -1), wx.ALIGN_RIGHT)
        labelmsg.SetForegroundColour('blue')
        label_group=wx.StaticText(panel,-1,_('Group_Name'),(-1, -1),wx.Size(150, 23), wx.ALIGN_LEFT)
        label_Oldname=wx.StaticText(panel,-1,_('Old_name'),(-1, -1),wx.Size(150, 23), wx.ALIGN_LEFT)
        label_Newname=wx.StaticText(panel,-1,_('Newn_Name'),(-1, -1),wx.Size(150, 23), wx.ALIGN_LEFT)
        
        
        txt_group = wx.TextCtrl(self, -1, '', size=(200, 23))
        txt_Oldname = wx.TextCtrl(self, -1, '', size=(200, 23))
        self.txt_Newname = wx.TextCtrl(panel, -1, '',size=(200, 23))
        
        if group_name!=None:
            txt_group.SetValue(group_name)
        
        if old_name!=None:
            txt_Oldname.SetValue(old_name)
        
        hsizer_GN = wx.BoxSizer(wx.HORIZONTAL)
        hsizer_GN.Add(label_group, 0)
        hsizer_GN.Add(txt_group, 0,wx.LEFT, 10)
        
        hsizer_ON = wx.BoxSizer(wx.HORIZONTAL)
        hsizer_ON.Add(label_Oldname, 0)
        hsizer_ON.Add(txt_Oldname, 1, wx.LEFT, 10)
        
        hsizer_NN = wx.BoxSizer(wx.HORIZONTAL)
        hsizer_NN.Add(label_Newname, 0)
        hsizer_NN.Add(self.txt_Newname, 0, wx.LEFT, 10)
        
        staline = wx.StaticLine(panel, wx.NewId(), (-1, -1), (-1, 2), wx.LI_HORIZONTAL)
        
        sbs.Add(labelmsg,0,flag= wx.ALIGN_CENTER|wx.ALL, border=10)
        
        hbox_BT = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_button=wx.Button(panel,label=_('save'))
        clos_button=wx.Button(panel,label=_('Close'))
        
        hbox_BT.Add(self.ok_button,0)
        hbox_BT.Add(clos_button, 0, wx.LEFT, 10)
        
        b = 10
        vsizer1 = wx.BoxSizer(wx.VERTICAL)
        vsizer1.Add(sbs, 0, wx.EXPAND | wx.ALL, b)
        vsizer1.Add(hsizer_GN, 0, wx.ALIGN_CENTER | wx.ALL, b)
        vsizer1.Add(hsizer_ON, 0, wx.ALIGN_CENTER | wx.ALL, b)
        vsizer1.Add(hsizer_NN, 0, wx.ALIGN_CENTER | wx.ALL, b)
        vsizer1.Add(staline, 0, wx.GROW | wx.ALL, b)
        
        vsizer1.Add(hbox_BT, 0, wx.ALIGN_CENTER | wx.ALL, b)
        panel.SetSizerAndFit(vsizer1)
        self.SetClientSize(panel.GetSize())
        
        self.ok_button.Bind(wx.EVT_BUTTON,self.Onsave)
        clos_button.Bind(wx.EVT_BUTTON,self.Onclose)
    
    def Onclose(self, Event):
        self.var_chang=''
        self.Destroy()
        

        
    def Onsave(self, Event):
        if len(self.txt_Newname.GetValue())> 2  and self.txt_Newname.GetValue()!='':
            val=self.txt_Newname.GetValue() 
            if self.txt_Newname.GetValue() !=None:
                self.var_chang=self.txt_Newname.GetValue()
                  
            self.Destroy()
        else:
            self.txt_Newname.SetBackgroundColour("pink")
            self.txt_Newname.SetFocus()
         



class PSFieldCustomizer(wx.Frame):

    def __init__(self,parent,callback=None, customizableFields=None, customizedFields=None,proceduresPersonalizations=None,removalOptions=None):
        from mainlogic import _
        wx.Frame.__init__(self, parent, -1, _("personazzazione"), style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        # def __init__(self,parent=None,id=1,title='',callback=None):
        self.Bind(wx.EVT_CLOSE, self.Onbt_canc)
        
        self.callback=callback
        self.var_tp={}
        menuBar=wx.MenuBar()
        menu=wx.Menu()
        self.customizableFields=customizableFields
        self.customizedFields=customizedFields
        self.proceduresPersonalizations=proceduresPersonalizations
        self.removalOptions=removalOptions
        item=menu.Append(-1,"%s\tCtrl-Q"%_("exit without to save"),_("Close"))
        item2=menu.Append(-1,"%s\tCtrl-S"%_("save to exit"),_("save"))
        self.Bind(wx.EVT_MENU,self.onExitApp,item2)
        self.Bind(wx.EVT_MENU,self.Onbt_canc,item)
        self.SetMenuBar(menuBar)
        vboxg1 = wx.GridSizer(2,2,1,20)
        menuBar.Append(menu,"&File")
        
        hbox = wx.BoxSizer(wx.VERTICAL)
        vBox = wx.BoxSizer(wx.VERTICAL)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox3= wx.BoxSizer(wx.VERTICAL)
        
        #create my panel
        pnl1 = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)
                
        #add my panel in the verital sizer
        vbox1.Add(pnl1,1,wx.EXPAND | wx.ALL,1)
        
        #intans my treebook
        self.win=ctrl_TreeBook(pnl1,-1,self.recup_perzo,self.customizableFields,self.customizedFields,self.proceduresPersonalizations,self.removalOptions)
        
        toolbar = wx.ToolBar(pnl1)
        import psconstants as psc
        import os
        btsave_image = wx.Image(os.path.join(psc.imagesPath, 'tsave.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        btcanc_image = wx.Image(os.path.join(psc.imagesPath, 'tcancel.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        
        bt_save=toolbar.AddLabelTool(wx.ID_ANY,'save',btsave_image,shortHelp=_("save to exit"))
        bt_canc=toolbar.AddLabelTool(wx.ID_ANY,'cancel',btcanc_image,shortHelp=_("exit without to save"))
        
        toolbar.Realize()
        
        self.Bind(wx.EVT_TOOL,self.onExitApp,bt_save)
        self.Bind(wx.EVT_TOOL, self.Onbt_canc,bt_canc)
        
        
        vBox.Add(self.win,1,wx.EXPAND)
        vBox.Add(toolbar,0,wx.EXPAND)
       
        pnl1.SetSizer(vBox)
        
        hbox.Add(vbox1, 1, wx.EXPAND)
        self.SetSizer(hbox)
    
    def Onbt_canc(self,EVT):
        from mainlogic import _
        var=''

        if self.win.cal_preliev !={} or self.win.cal_treatmnt!={} or self.win.cal!={}:
            var_close=closedialog(self,_("closing"),var=None)
            var_close.ShowModal()
            var=var_close.page
            if var=='ok':
                # print "we are there"
                # print 'trovato :',var
                self.Destroy()
        else:

            self.Destroy()
            
        
        
    def recup_perzo(self,var):
        self.Dico_recup=var    
        self.callback(var)
    
        
    def onExitApp(self,evt):
        #Recup personalization list:
        # self.win=ctrl_TreeBook(pnl1,-1,self.recup_perzo,customizableFields, customizedFields,proceduresPersonalizations,removalOptions)
        var_procedure={}
        var_Treatment={}
        var_preliev={}
        if self.win.cal=={}:
            var_procedure['core']=self.win.dic_custm
            
        else:
           var_procedure=self.win.cal
           
        if self.win.cal_treatmnt=={}:
            var_Treatment['core']=self.proceduresPersonalizations
            
        else:
            var_Treatment=self.win.cal_treatmnt

            
        if self.win.cal_preliev=={}:
            var_preliev['core']=self.removalOptions
        else:
            var_preliev=self.win.cal_preliev

        self.callback(var_procedure,var_Treatment,self.win.cal_cancel, var_preliev)    
        # self.callback(self.win.cal,self.win.cal_treatmnt,self.win.cal_cancel, self.win.cal_preliev)
        self.Destroy()
        

class ctrl_TreeBook(wx.Treebook):
    def __init__(self, parent, id,callback=None,customizableFields=None, customizedFields=None, proceduresPersonalizations=None,removalOptions=None):
        
        wx.Treebook.__init__(self, parent, id, style=wx.BK_DEFAULT)
        idGenerator=self.getNextID(50)
        self.callback=callback
        #self.callback_treatmnt=callback_treatmnt
        self.cal={}
        self.cal_treatmnt={}
        self.cal_cancel={}
        self.cal_preliev={}

        #Composition list element for each page in funtion TreeB_element
        #initilization listCrt in each pages
        self.init_lstCrt={}
        self.dic_custm={}
        self.dic_custm_val={}
        self.lischk=[]
        #self.liscan=[]
        self.dico_cs_lab={}
        self.dico_prova={}

        self.dico_prova=self.datbase_elemt(customizedFields)
                    
        # return dico_data_tre,dic_pag_nam,dico_db_data
        TreeB_element,self.dico_cs_lab,self.dico_DB_val=self.getPageList(customizableFields, customizedFields, proceduresPersonalizations,removalOptions)
       
        for el in self.dico_cs_lab:
            for k in self.dico_cs_lab[el]:
                self.init_lstCrt[k]=''
        self.dic_custm=copy.copy(self.dico_DB_val)
        
        #creat the the tree with the pages 
        for k,v in TreeB_element.items():
            from mainlogic import _
            # Parent page
            # win=self.make_Tree_Panel(k,'papa')
            if k=='core':
                win=self.make_Tree_Panel(k,'papa')
                self.AddPage(win,'%s                                              '%_(k).upper(),imageId=idGenerator.next())
                #creat the tree son child branch and pages
            
                #Solo la personalizzazine del CODE
                if v!=[]:
                    for sub in v:
                        for cle,elm in sub.items():
                            if cle !='':
                                if cle in self.dico_DB_val.keys():
                                    win=self.make_Tree_Panel(cle,'sottopagina',elm,self.dico_DB_val)
                                else:
                                    win=self.make_Tree_Panel(cle,'sottopagina',elm)
                                   
                                self.AddSubPage(win,_(cle),imageId=idGenerator.next())
        self.GetTreeCtrl().ExpandAll()    
            # This is a workaround for a sizing bug on Mac
        wx.FutureCall(100, self.AdjustSize)
    def datbase_elemt(self,var=None):
        list_tmp=[]
        dic_tmp={}
        if var!= None:
            for chiave in var:
                for i in var[chiave]:
                    list_tmp.append(i['name'])
                if list_tmp!=[]:
                    dic_tmp[chiave]=list_tmp
                    list_tmp=[]
            return dic_tmp
                
    def getNextID(self,count):
        'An ID generator'
        imID = 0
        while True:
            yield imID
            imID += 1
            if imID == count:
                imID = 0
                 
    def AdjustSize(self):
        self.GetTreeCtrl().InvalidateBestSize()
        self.SendSizeEvent()
         
    def varible_transf(self,var):
            self.cal=var
        
    def var_tras_treatmnt(self,var):
        # self.cal=var
        self.cal_treatmnt=var
    def var_tras_preliev(self,var):
        # self.cal=var
        self.cal_preliev=var    
    
    
    def make_Tree_Panel(self,page_Name=None,page_Type=None,costum_gruppo=None,db_elm=None,type=None):
        from mainlogic import _
        #Sottomaschera container
        p = wx.Panel(self, -1)
        # Sottomaschera contenitore che contiene la pagina, dove io uso un pannello
        win=wx.Panel(p,-1)
        
        
        
        #i sizer per personalisare i controlli di ogni pagine
        vboxg = wx.GridSizer(2,2,1,-70)
        vboxg1 = wx.GridSizer(2,3,1,20)
        sizer = wx.BoxSizer(wx.VERTICAL)
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox3 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
        #variabile local per each page
        m_dic={}
        #ctrl_dico={}
        dico_gruppo={}
        dico_can_elmts={}
        dico_elm_perso={}
        dico_val_label={}
        list_elm_check=[]
        list_check=[]
        lis_elt_add=[]
        dic_elt_add={}
        dic_tan_preliev={}
        
        #if click recupra del branch(pagina attiva) clikato
        nampage = None
        if page_Name is not None:
            nampage = page_Name
        k=[]
        
        #'Trattamenti' nome provisorio della costumer class PRESIDI
        if page_Type=='sottopagina':
            lst=[]
            for el in costum_gruppo:
                lst.append('%s'%el['label'])
                dico_val_label[el['label']]=el['name']
                #Pagina diversa di quella del tratameto e presidi
            if page_Name != 'Trattamenti' and  page_Name != 'prelieve':
                
                if db_elm != None:
                    if nampage in db_elm.keys():
                        for elts in db_elm['%s'%nampage].keys():
                            ds={}
                            for elt in db_elm['%s'%nampage][elts]:
                                ds[elt['label']]=elt['name']
                            if ds!={}: 
                                dico_elm_perso[elts] = ds
                    
                LCtrl = wx.ListCtrl(win, -1, size=(590,330), style=wx.LC_REPORT)
                LCtrl.InsertColumn(0, _("Nome lis"))
                LCtrl.InsertColumn(1, _("%s"%page_Name))
                LCtrl.SetColumnWidth(0, 265)
                LCtrl.SetColumnWidth(1, 295)
                
                txt=wx.StaticText(win, -1, _("%s"%page_Name).upper())
                
                #txt3=wx.StaticText(win, 0,'Aggiungere le %s personalizzate inserendo il nome e la tipologia '%page_Name)
                txt3=wx.StaticText(win, 0,_("msg procd"))
                # in via di allestimento
                txt3.SetForegroundColour('blue')
                
                Bt_Add = wx.Button(win, 10, _("Aggiungi"))
                Bt_Del = wx.Button(win, 11, _("modif"))
                Bt_Annul = wx.Button(win, 11, _("Elimina"))
                vboxg1.AddMany([ (Bt_Add,  wx.EXPAND|wx.TOP, 5),
                                (Bt_Del,wx.EXPAND|wx.TOP, 5),
                                (Bt_Annul,wx.EXPAND|wx.TOP, 5)])
            
                if lst!=[]:
                    lst=sorted(lst)
                # sizer for buttom add and remove
                txt_new = wx.TextCtrl(win, -1,name=_("%s"%page_Name),size=wx.Size(200, 20))
                
                txt_gruppo = wx.ComboBox(win, -1,"", size=wx.Size(300, 60), style = wx.TE_READONLY , choices=sorted(lst))
                if len(lst)==1:
                    txt_gruppo.SetStringSelection(lst[0])
                
                vboxg.AddMany([ (wx.StaticText(win, -1, '%s %s'%(_("Nome della"),_("%s"%page_Name))),0,wx.EXPAND|wx.TOP, 35),
                        (wx.StaticText(win, -1, '%s %s'%(_("Tipologia  di"),_("%s"%page_Name))), 0, wx.EXPAND|wx.TOP, 35),
                        (txt_new,0),
                        (txt_gruppo,0)])
            
                vbox1.Add(txt, 1,  wx.EXPAND|wx.TOP, 5)
                vbox1.Add(txt3,0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 5)
                vbox2.Add(vboxg1, 0,  wx.EXPAND|wx.TOP, 1)
                vbox3.Add(LCtrl, 1,  wx.EXPAND|wx.TOP, 1)
                
                sizer.Add(vbox1, 0, wx.ALL|wx.TOP,1)
                sizer.Add(vboxg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP,-15)
                sizer.Add(vbox2,0,wx.ALIGN_CENTER_HORIZONTAL|wx.TOP,-20)
                sizer.Add(vbox3,0, wx.EXPAND|wx.TOP, 10)
                
            else:
                BT_valide = wx.Button(win, -1, _("Salva Modifiche"))
                txt=wx.StaticText(win, -1, _("%s"%page_Name).upper())
                
                
                    

                BT_valide.Hide()
                #print '@@@@@@@@@@@@@@@@@@@ LS:',ls
                if page_Name == 'Trattamenti':
                    txt3=wx.StaticText(win, -1, label=_("msg Trattementi"))
                    #in via di allestimento
                    txt3.SetForegroundColour('blue')
                    # BT_valide.Disable()
                    if costum_gruppo!=None:
                        ls=[]
                        dic_labl_gruppo={}
                    if costum_gruppo!=None:    
                        for el in costum_gruppo:
                            ls.append(el['label'])
                            dic_labl_gruppo[el['label']]=el['value']
                    vbox1.Add(txt, 1,  wx.EXPAND|wx.TOP, 5)
                    vbox1.Add(txt3,0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 5)
                    ListCheck_box = wx.CheckListBox(win, -1,(1,25), (570,400), sorted(ls))    
                    
                    hbox1.Add(ListCheck_box, 1,  wx.EXPAND|wx.TOP, 5)
                    sizer.Add(vbox1, 0, wx.ALL|wx.TOP, 5)
                    sizer.Add(hbox1, 0,wx.ALL|wx.TOP, 5)
                else:
                    ls=[]
                    dic_labl_gruppo={}
                    for el in costum_gruppo:
                        ls.append(el['name'])
                        dic_labl_gruppo[el['label']]=el['value']
                    dic_prelv={}
                    dic_prelv['fabric']=['cornee','valvole cardiache','vasi sanguigni','cute','ossa','tendini','cartilagini','arti']
                    dic_prelv['organs']=['reni','cuore','fegato','polmoni','pancreas','intestino']
                    
                    txt3=wx.StaticText(win, -1, label=_("msg prelievi"))
                    txt3.SetForegroundColour('blue')
                    sb_preliev = wx.StaticBox(win, label=_("organi / tessuti"),size=(500,300))
                    #sb_preliev.SetForegroundColour("blue")
                    boxsizer_preliev= wx.StaticBoxSizer(sb_preliev, wx.VERTICAL)
                    if ls !=[]:
                        for el in sorted(ls):
                            box=wx.CheckBox(win, -1, _(el))
                            box.SetName(el)
                            
                            box.SetForegroundColour('blue')
                            list_check.append(box)
                            #box.Bind(wx.EVT_CHECKBOX,onSelecheck)
                            boxsizer_preliev.Add(box,1, wx.EXPAND|wx.TOP, 5)
                            
                            if el in dic_prelv.keys():
                                for el_list in sorted(dic_prelv[el]):
                                    boxsizer_preliev.Add(wx.StaticText(win, -1, _(el_list)),1, wx.EXPAND|wx.TOP, 5)
                    vbox1.Add(txt, 1,  wx.EXPAND|wx.TOP, 5)
                    vbox1.Add(txt3,0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 10)
                    sizer.Add(vbox1, 0, wx.ALL|wx.TOP, 5)
                    sizer.Add(boxsizer_preliev, 0, wx.ALL|wx.TOP, 20)    
                sizer.Add(BT_valide, 0,wx.ALL|wx.TOP, 5)
                
        else:
            # txt=wx.StaticText(win, -1, _("%s"%page_Name).upper())
            #HOME PAGE CORE
            if page_Name=='core':
                font1 = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                # txt3.SetFont(font1)
                #in via di allestimento
                txt1=wx.StaticText(win, -1, label=_("def_description"),size=(500,150))
                font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                txt1.SetFont(font)
                # vbox1.Add(txt, 1,  wx.EXPAND|wx.TOP, 5)
                
                #sb_prov.Add(txt,)
                
                # sb_prov = wx.StaticBox(win, label=_("provenienza e esito ti"),size=(500,300))
                sb_prov = wx.StaticBox(win, label=_('CAMPI PERSONAZZABILI'))
                sb_prov.SetFont(font1)
                sb_prov.SetForegroundColour("blue")
                boxsizer_sb_prov = wx.StaticBoxSizer(sb_prov, wx.VERTICAL)
                boxsizer_sb_prov.Add(txt1, 1,  wx.EXPAND|wx.ALL, 10)
                
                sizer.Add(boxsizer_sb_prov, 0, wx.ALL|wx.TOP, 5)
                # sizer.Add(boxsizer_degenza, 0, wx.ALL|wx.TOP, 20)
              
            
            
        win.SetSizer(sizer)
        p.win = win
        
        def writ_LCrt(var):
            # if page_Name != 'Trattamenti' :
            if page_Name != 'Trattamenti' and  page_Name != 'prelieve':
                #AUTOSELECT UPDATE LIST 
                if var in self.dico_DB_val.keys() and  self.init_lstCrt[page_Name]=='':
                    dic_lab={}
                    if costum_gruppo!= None:
                        for el in costum_gruppo:
                            dic_lab[el['name']]=el['label']
                    t_list=[]
                    if page_Name in self.dico_DB_val.keys():
                        for var1 in self.dico_DB_val[page_Name]:
                            for var_k in self.dico_DB_val[page_Name][var1]:
                                if var1 in dic_lab.keys():
                                    var1=dic_lab[var1]
                                t_list.append((var1,var_k['label']))
                    index=0
                    if t_list!=[]:
                        self.init_lstCrt[page_Name]='ok'
                        dic_grp={}
                        for val in t_list:
                            if val[0] not in dic_grp:
                                dic_grp[val[0]]=[val[1]]
                            else:
                                dic_grp[val[0]].append(val[1])
                        for el in sorted(dic_grp):
                            for i in sorted(dic_grp[el]):
                                LCtrl.InsertStringItem(index, str(i))
                                LCtrl.SetStringItem(index, 1, str(el))
                                if index %2:
                                    LCtrl.SetItemBackgroundColour(index,"white")
                                else:
                                    LCtrl.SetItemBackgroundColour(index,(192, 192, 192, 255))
                                index+=1
                        t_list=[]    
            else:
                #AUTOSELECT LIST-CHECK
                lst=[]
                if page_Name == 'Trattamenti' :
                    if self.init_lstCrt[page_Name]=='':
                        if costum_gruppo!= None:
                            for el in costum_gruppo:
                                if el['value']=='True':
                                    lst.append(el['label'])
                        
                        if lst !=[]:
                            self.lischk=lst
                            ListCheck_box.SetCheckedStrings((lst))
                       
                        lst_el=[]
                        a1=ListCheck_box.GetCheckedStrings()
                        for el in range(len(a1)):
                            lst_el.append(a1[el])
                        list_elm_check= lst_el
                        # for item in ListCheck_box.GetItems():
                            # idx=()
                        
                        self.init_lstCrt[page_Name]='ok'
                if page_Name == 'prelieve':
                    if self.init_lstCrt[page_Name]=='':
                        if costum_gruppo!= None:
                            for el in costum_gruppo:
                                if el['value']==True:
                                    for l in list_check:
                                        if el['name']==l.GetName():
                                            l.SetValue(True)
                                            l.Disable()
                                            
                        
                        
                        self.init_lstCrt[page_Name]='ok'
        
        def OnCPSize(evt, win=win):
            # position and refresh win
            win.SetPosition((0,0))
            win.SetSize(evt.GetSize())
            
            #inizialiare la listcrt si arrivano dati della DB(gia personalizate)
            writ_LCrt(page_Name)
            
            if page_Type=='sottopagina':
                #'Trattamenti' nome provisorio della costumer class PRESIDI
                if page_Name != 'Trattamenti' and  page_Name != 'prelieve':
                    Bt_Add.Bind(wx.EVT_BUTTON,OnAdd_chd)
                    Bt_Del.Bind(wx.EVT_BUTTON,OnChanged)
                    Bt_Del.Disable()
                    Bt_Annul.Bind(wx.EVT_BUTTON,OnAnnula)
                    Bt_Annul.Disable()
                    LCtrl.Bind(wx.wx.EVT_LIST_ITEM_SELECTED,OnItemselect)
                    
                else:
                    if page_Name == 'Trattamenti' :
                        ListCheck_box.Bind(wx.EVT_CHECKLISTBOX,check_elmt)
                    if page_Name == 'prelieve':
                        for l in list_check:
                            l.Bind(wx.EVT_CHECKBOX,Selecheck)
                    BT_valide.Bind(wx.EVT_BUTTON,Onvalide)
        
        def check_elmt(event):
            index = event.GetSelection()
            labl=ListCheck_box.GetString(index)
            ab=[]
            lte=[]
            ab1=ListCheck_box.GetCheckedStrings()
            if ListCheck_box.IsChecked(index):
                ListCheck_box.SetItemForegroundColour(index, 'Red')
                list_check=[]
                dic_tan_treat={}
                
                #lista degli element select in lis check
                a=ListCheck_box.GetCheckedStrings()
                for el in range(len(a)):
                    list_check.append(a[el])
                #print self.dic_custm
                
                list_elm_check= list_check
                # print 'origin list ',list_elm_check
                
                BT_valide.Disable()
                tmp_dic=[]
                
                for el in costum_gruppo:
                    if el['label'] in list_elm_check:
                        el['value']='True'
                        tmp_dic.append(el)
                pagnam='%s'%nampage
                if tmp_dic!=[]:
                    dic_tan_treat['core']={'%s'%nampage:tmp_dic}
                    # print 'FANTASTIC'
                    # print dic_tan_treat
                    self.var_tras_treatmnt(dic_tan_treat)
            else:    
                if labl in self.lischk:
                    lst=[]
                    lst.append(labl)
                    for i in range(len(ab1)):
                        lst.append(ab1[i])
                    #ab1=ab1.append(labl)
                    ListCheck_box.SetCheckedStrings((lst))
                    #ListCheck_box.SetCheckedStrings(([k for k in ab1+self.lischk if k not in ab1 and k mot in self.lischk]))
                    ListCheck_box.SetItemForegroundColour(index, 'Gray')
                else:
                    ListCheck_box.SetItemForegroundColour(index, 'Black')
                
                
            
            #Abitlitation Button Valide
            # ab=ListCheck_box.GetCheckedStrings()
            # for el in range(len(ab)):
                # lte.append(ab[el])
            # diff_lis = [i for i in list_elm_check+lte if i not in list_elm_check or i not in lte]
            

            # if diff_lis==[]:
                # if lte!=[]: 
                    # BT_valide.Disable()
            # else:
                # if lte!=[]: 
                    # BT_valide.Enable()
                # else:
                    # BT_valide.Disable()

                    
        def Selecheck(event):
            #dic_tan_preliev={}
            BT_valide.Enable()
            tmp_dic=[]
            cb=event.GetEventObject()
            
            name=cb.GetName()
            dic_preliev={}
            h={}
            for el in costum_gruppo:
                if el['name'] == name:
                    if cb.GetValue():
                        el['value']=cb.GetValue()
                    else:
                        el['value']=cb.GetValue()
                    h[name]=el['value']
                else:
                    h[el['name']]=el['value']
            
            if h!={}:
                dic_tan_preliev['%s'%nampage]=h
            
                dic_preliev['core']=dic_tan_preliev
                self.var_tras_preliev(dic_preliev)
            
            
            
        def OnItemselect(event):
            Bt_Del.Enable()
            index = LCtrl.GetFocusedItem()
            a=LCtrl.GetItem(index, 0).GetText()
            b=LCtrl.GetItem(index, 1).GetText()
            
            Bt_Annul.Disable()
            for el in lis_elt_add:
                if el[0]==a.lower() and el[1]==b.lower():
                    Bt_Del.Disable()
                    Bt_Annul.Enable()
                    
                    break
               
        def Onvalide(event):
            if page_Name != 'prelieve':
                list_check=[]
                dic_tan_treat={}
                
                #lista degli element select in lis check
                a=ListCheck_box.GetCheckedStrings()
                for el in range(len(a)):
                    list_check.append(a[el])
                
                list_elm_check= list_check
                
                BT_valide.Disable()
                tmp_dic=[]
                
                for el in costum_gruppo:
                    if el['label'] in list_elm_check:
                        el['value']='True'
                        tmp_dic.append(el)
                pagnam='%s'%nampage
                dic_tan_treat['core']={'%s'%nampage:tmp_dic}
                self.var_tras_treatmnt(dic_tan_treat)
            else:
                dic_preliev={}
                dic_preliev['core']=dic_tan_preliev
                self.var_tras_preliev(dic_preliev)
                    
            BT_valide.Disable()
        
        
        

        
        def OnAdd_chd(evt ):
            var=''
            result_tmp={}
            tpls=''
            val_name=txt_new.GetValue().capitalize()
            grp_name=txt_gruppo.GetValue()
            
            
            if val_name=='' or grp_name=='':
                return
            else:
                val_name=txt_new.GetValue().capitalize()
                grp_name=txt_gruppo.GetValue()
                if dico_elm_perso:
                    # vreif if the string insert existe
                    if grp_name in dico_val_label.keys():
                        if  dico_val_label[grp_name] in dico_elm_perso.keys():
                            if val_name in dico_elm_perso[dico_val_label[grp_name]].keys():
                                ShowMessage(val_name,grp_name)
                            else:var='ok'
                        else:var='ok'
                    else:var='ok'
                else:var='ok'
                if var=='ok':
                    dc={}
                    k=[]
                    num_items = LCtrl.GetItemCount()
                    dic_grp1={}
                    v_grup = ''
                    #save all items of my list Contrl
                    for i in range(num_items):
                        v_Name = LCtrl.GetItem(i,0).GetText()
                        v_grup = LCtrl.GetItem(i,1).GetText()
                        if v_grup not in dic_grp1:
                            dic_grp1[v_grup]=[v_Name]
                        else:
                            dic_grp1[v_grup].append(v_Name)
                        
                    #CLEAR all cellule off my list Contrl
                    LCtrl.DeleteAllItems()
                    
                    #Add the new item
                    if grp_name not in dic_grp1:
                        dic_grp1[grp_name]=[val_name]
                    else:
                        dic_grp1[grp_name].append(val_name)
                    tpls=(val_name.lower(),v_grup.lower())
                    lis_elt_add.append((val_name.lower(),grp_name.lower()))
                    index=0
                    for el in sorted(dic_grp1):
                        for i in sorted(dic_grp1[el]):
                            if str(i)!='' and str(el)!='':
                                LCtrl.InsertStringItem(index, str(i))
                                LCtrl.SetStringItem(index, 1, str(el))
                                #LCtrl.SetItemForegroundColour(index,"Red")
                                
                                #if index %2:
                                if str(i)==val_name and str(el)==grp_name:
                                    idx=index
                                    LCtrl.SetItemBackgroundColour(index,"Yellow")
                                    # if index %2:
                                        # LCtrl.SetItemBackgroundColour(index,"Yellow")
                                    # else:
                                        # LCtrl.SetItemBackgroundColour(index,(192, 192, 192, 255))
                                else:
                                    if index %2:
                                        LCtrl.SetItemBackgroundColour(index,"white")
                                        # LCtrl.GetItem(index).SetTextColour(wx.RED)
                                        #idx=index
                                    else:
                                        LCtrl.SetItemBackgroundColour(index,(192, 192, 192, 255))
                                
                                index+=1
                    
                    for el in costum_gruppo:
                        dico_val_label[el['label']]=el['name']    
                    ctrl_name=datetime.datetime.now().isoformat().replace('-', '').replace('.','').replace(':', '')
                    if db_elm != None:
                        dc['name']=ctrl_name
                        dc['label']=val_name
                        if grp_name in dico_val_label.keys():
                            if dico_val_label[grp_name] in db_elm['%s'%nampage].keys():
                                self.dic_custm['%s'%nampage][dico_val_label[grp_name]].append(dc)
                            else:
                                self.dic_custm['%s'%nampage][dico_val_label[grp_name]]=[dc]
                            d={}
                            
                            if  dico_val_label[grp_name] in dico_elm_perso.keys():
                                d=dico_elm_perso[dico_val_label[grp_name]]
                                d[val_name]=ctrl_name
                                dico_elm_perso[dico_val_label[grp_name]] = d
                            else:
                                d[val_name]=ctrl_name
                                dico_elm_perso[dico_val_label[grp_name]] = d   
                    else:
                        # If the page is without data of DB
                        dc['name']=ctrl_name
                        dc['label']=val_name
                        if dico_val_label[grp_name] in dico_gruppo:
                            dico_gruppo[dico_val_label[grp_name]].append(dc)
                            
                        else:
                            dico_gruppo[dico_val_label[grp_name]]=[dc]
                        
                        d={}
                        if dico_val_label[grp_name] in dico_elm_perso.keys():
                            d=dico_elm_perso[dico_val_label[grp_name]]
                            d[val_name]=ctrl_name
                            dico_elm_perso[dico_val_label[grp_name]] = d
                        else:
                            d[val_name]=ctrl_name
                            dico_elm_perso[dico_val_label[grp_name]] = d    
                        self.dic_custm['%s'%nampage]=dico_gruppo
                        #dic_elt_add[]=dico_gruppo
                    if len(lst)!=1:
                        txt_gruppo.Clear()
                        for el in lst:
                            txt_gruppo.Append(el)
                    # for idx in range(LCtrl.GetItemCount()):
                        # if idx %2 :
                            # LCtrl.SetItemBackgroundColour(idx,"white")
                        # else:
                            # LCtrl.SetItemBackgroundColour(idx,(192, 192, 192, 255))
                    if idx!='':
                        
                        item = LCtrl.GetItem(idx)
                        item.SetTextColour(wx.RED)
                    result_tmp['core']=self.dic_custm
                    self.varible_transf(result_tmp)
                    # for el in lst:
                        # txt_gruppo.Append(el)
                    txt_new.Clear()
                    var=''
                    
       
        # msg si una string esiste gia per un gruppo
        def ShowMessage(var_1=None,var_2=None):
            
            dial = wx.MessageDialog(None, "This customization '%s' for the Tipologia di Procedura '%s' is existing"%(var_1,var_2), 'Info', wx.OK)
            dial.ShowModal()
        
        
        def OnChanged(evt ,win=win):
            a=''
            b=''
            result_tmp={}
            index = LCtrl.GetFocusedItem()
            a='%s'%LCtrl.GetItem(index, 0).GetText()
            b='%s'%LCtrl.GetItem(index, 1).GetText()
            #Open the Dialoge frame to change the process name 
            ValChange=changedialog(win,title='%s'%nampage, group_name=b, old_name=a)
            ValChange.ShowModal()
            list_label=[]
            dic_data={}
            if ValChange.var_chang!='' and ValChange.var_chang!=None :
            # if ValChange.var_chang!='':
                if b in dico_val_label.keys():
                    if dico_val_label[b] in dico_elm_perso.keys():
                        dic_data = self.dic_custm['%s'%nampage]
                        if dico_val_label[b] in dic_data.keys():
                            lis_data= dic_data[dico_val_label[b]]
                            for var_label in lis_data:
                                list_label.append(var_label['label'].lower())
                            for el in lis_data:
                                if el['name']==dico_elm_perso[dico_val_label[b]][a]:
                                    tmp_dic={}
                                    if ValChange.var_chang.lower() not in list_label:
                                        #dico_elm_perso[dico_val_label[b]][ValChange.var_chang.capitalize].remove(el['name']
                                        LCtrl.DeleteItem(index)
                                        LCtrl.InsertStringItem(index, ValChange.var_chang.capitalize())
                                        LCtrl.SetStringItem(index, 1, b)    
                                        tmp_dic=dico_elm_perso[dico_val_label[b]]
                                        tmp_dic.keys().remove(a)
                                        tmp_dic[ValChange.var_chang.capitalize()]=el['name']
                                        el['label']=ValChange.var_chang.capitalize()
                                        # print 'brio',ValChange.var_chang.capitalize()
                                        dico_elm_perso[dico_val_label[b]]=tmp_dic
                                        #lis_data.remove(el)
                                        dic_data[dico_val_label[b]]=lis_data
                                        self.dic_custm['%s'%nampage]=dic_data
                                        dic_data={}
                                    else:
                                        ShowMessage(ValChange.var_chang,b)
                                    break
                
                
                Bt_Del.Disable()
                indx=0
                for el in range(LCtrl.GetItemCount()):
                    if el %2:
                        LCtrl.SetItemBackgroundColour(el,"white")
                    else:
                        LCtrl.SetItemBackgroundColour(el,(192, 192, 192, 255))
                    #indx+=1
                result_tmp['core']=self.dic_custm
                self.varible_transf(result_tmp)
        
        
        
        
        def OnAnnula(evt ,win=win):
            a=''
            b=''
            result_tmp={}
            index = LCtrl.GetFocusedItem()
            a='%s'%LCtrl.GetItem(index, 0).GetText()
            b='%s'%LCtrl.GetItem(index, 1).GetText()
            
            dic_data={}
            if b in dico_val_label.keys():
                #control the procedure exist with one personnalisation
                if dico_val_label[b] in dico_elm_perso.keys():
                    dic_data = self.dic_custm['%s'%nampage]
                    if dico_val_label[b] in dic_data.keys():
                        lis_data= dic_data[dico_val_label[b]]
                        for el in lis_data:
                            # if dico_val_label[b] in dico_elm_perso.keys():
                            if el['name']==dico_elm_perso[dico_val_label[b]][a]:
                                LCtrl.DeleteItem(index)
                                Bt_Annul.Disable()    
                                lis_data.remove(el)
                                dic_data[dico_val_label[b]]=lis_data
                                self.dic_custm['%s'%nampage]=dic_data
                                dic_data={}    
                                result_tmp['core']=self.dic_custm
                                self.varible_transf(result_tmp)
                                break
                        
            
            Bt_Del.Disable()
            indx=0
            for el in range(LCtrl.GetItemCount()):
                if el %2:
                    LCtrl.SetItemBackgroundColour(el,"white")
                else:
                    LCtrl.SetItemBackgroundColour(el,(192, 192, 192, 255))
                indx+=1
            
            
        p.Bind(wx.EVT_SIZE, OnCPSize)
        return p
        
        
    def getPageList(self, customfiled=None,custom=None, perso=None, rmv_option=None):
        from mainlogic import _
        #initial lis of tratement process
        
        dic_B={}
        dic_c={}
        lis_trat_proc=[
                {'name':'DrenTorc', 'value': 'False','label':_("Drenaggio toracico")},
                # {'name':'CatArte', 'value': 'False','label':_("Catetere arterioso")},
                {'name':'ContPazt', 'value': 'False','label':_("Contenimento del paziente")},
                {'name':'Toracent', 'value': 'False','label':_("Toracentesi")},
                {'name':'Paracent', 'value': 'False','label':_("Paracentesi")},
                {'name':'CatVesci', 'value': 'False','label':_("Catetere vescicale")},
                {'name':'Pacmak', 'value': 'False','label':_("Pacemaker")},
                {'name':'DiasterTer', 'value': 'False','label':_("Diastasi sternale terapeutica")},
                {'name':'MinDrenTo', 'value': 'False','label':_("Mini-drenaggio toracico")},
                {'name':'EcmVenArt', 'value': 'False','label':_("ECM veno-arterioso")},
                {'name':'BranTisOxy', 'value': 'False','label':_("Brain Tissue Oxygen")},
                {'name':'SjoDue', 'value': 'False','label':_("Sjo2")},
                {'name':'TpsComBar', 'value': 'False','label':_("TPS")},
                {'name':'CpfA', 'value': 'False','label':_("CPFA")},
                {'name':'ToraMy', 'value': 'False','label':_("Toraymyxin")},
                {'name':'Pronaz', 'value': 'False','label':_("Pronazione")},
                {'name':'DecapNei', 'value': 'False','label':_("Decapneizzazione")},
                {'name':'VentOsci', 'value': 'False','label':_("Ventilazione oscillatoria")},
                {'name':'Eletromia', 'value': 'False','label':_("Elettromiografia")},
                {'name':'BronCosp', 'value': 'False','label':_("Broncoscopia")},
                {'name':'EcoCard', 'value': 'False','label':_("Ecocardiografia")},
                {'name':'ProTromPro', 'value': 'False','label':_("Profilassi trombosi profonda")},
                {'name':'ProUlcGast', 'value': 'False','label':_("Profilassi ulcera gastrica")},
                {'name':'IgienCavo', 'value': 'False','label':_('Igiene cavo orale con clorexidina 2 volte al giorno')},
                {'name':'OpenAbdomen', 'value': 'False','label':_('Addome aperto')}
            ]
        lis_prelievi=[
                {'name':'organs', 'value':False,'label':_('organs')},
                {'name':'fabric', 'value':False,'label':_('fabric')}]
        #rmv_option={'prelieve':{'organs': False, 'fabric': True}}
        #Update la lista dei option prelievi se abbiamo dati provenienti dal CORE
        if rmv_option is not None:
            for val in rmv_option['prelieve'].keys():
                for i in  range(len(lis_prelievi)):
                    el = lis_prelievi[i]
                    for k in el:
                        if val==el[k]:
                            el['value']=rmv_option['prelieve'][val]
                
            
        dic_prelievi={'prelieve':lis_prelievi}
        dic_Tratement={'Trattamenti':lis_trat_proc}
        
        if perso=={}:
            perso = None
        
        dic_tmp=[]
        dic_name_tmp=[]
                
        if custom!= None:
            dic_B= custom
            
        if customfiled != None:
            dic_c = customfiled
                
        d_list=[]
        dico_prov={}
        dico_db_data={}
        dico_data_tre={}
        dic_pag_nam={}
        v={}
        
        
        # Creat element of dico_data_tre
        # This the dic witch has the format to creat the diff pages for the widget treebook pages
        
        if dic_c !={}:
            for el in dic_c:
                dico_data_tre[el]=[]
                dic_pag_nam[el]=dic_c[el].keys()
                #dico_DB_val_val[el]=[]
                for els in dic_c[el]:
                    dico_prov[els]=[]
                    for k in dic_c[el][els]:
                    #for i in els[k]:
                        for cle,val in k.items():
                            d={}
                            d['name']=cle
                            d['label']=val
                            d_list.append(d)
                            if custom!=None:
                                if cle in dic_B.keys():
                                    v[cle]=dic_B[cle]
                    if v != {}:
                        dico_db_data[els]=v
                        v={}
                                #d_list.append(v)
                                
                    if d_list!=[]:
                        dico_prov[els]=d_list
                        d_list=[]
                        dico_data_tre[el]=[dico_prov]
        
        # Add il dictionary for treatment  to creatt diff pages
        if 'core' not in dic_pag_nam:
            dic_pag_nam['core']=['Trattamenti','prelieve']
        else:
            dic_pag_nam['core'].append('Trattamenti')
            dic_pag_nam['core'].append('prelieve')
        if  perso != None:
            for el in perso['Trattamenti']:
                dic_name_tmp.append(el['name'])
                dic_tmp.append(el)
            for elmti  in lis_trat_proc:
                if elmti['name'] not in dic_name_tmp:
                    dic_tmp.append(elmti)
            dic_Tratement={'Trattamenti':dic_tmp}
            dico_data_tre['core'].append(dic_Tratement)
            dico_data_tre['core'].append(dic_prelievi)
        else:                
            if 'core' not in dico_data_tre:
                dico_data_tre['core']=[dic_prelievi,dic_Tratement]
            else:
                dico_data_tre['core'].append(dic_Tratement)
                dico_data_tre['core'].append(dic_prelievi)

        return dico_data_tre,dic_pag_nam,dico_db_data
        #return self.dico_prova,dic_label




    def OnRemove(self, event):
        index = self.lc.GetFocusedItem()
        self.lc.DeleteItem(index)


#Nota che questa funzione e fuori dalla indentazione della frame.
def fctChiudi():
    try:
        ret=wx.MessageBox('Vuoi uscire davvero?', 'Palindrome', wx.YES_NO | wx.CENTRE |wx.NO_DEFAULT)
        return ret
    except:
        message = "Atenzione! \n Ho intercettato un errore."
        caption = "Palindrome"
        wx.MessageBox(message, caption, wx.OK)

