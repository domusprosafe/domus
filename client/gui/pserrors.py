import wx
import psconstants as psc
from psscrolledpanel import PSScrolledPanel

from guigenerator import GuiGenerator

from notificationcenter import notificationCenter

class PSErrors(PSScrolledPanel):

    def __init__(self, parent, mainLogic, showPageCallback, contentType="errors"):

        PSScrolledPanel.__init__(self, parent, -1)
        from mainlogic import _
        self.mainLogic = mainLogic
        self.showPageCallback = showPageCallback
        self.contentType = contentType

        crfString = _("Crf")
        errorString = _("ERROR")
        warningString = _("Warning")
        acceptedString = _("Accepted")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        self.SetBackgroundColour('white')

        self.interfaceXML = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <interfaces>
          <interface item="errorList" name="default">
            <row>
              <label width="100" notexpand="1">%s</label>
              <label width="500" notexpand="1">%s</label>
            </row>
              <linepanel height="1"/>
            <dyninterface class="errorList" attribute="errorList" interfacename="default"/>
          </interface>
        
          <interface class="errorDetail" name="default">
            <row>
              <readonly evaluate="%s.errorDetail.errorCrfLabel" targetinstance="self" width="100"/>
              <readonly evaluate="%s.errorDetail.errorId" targetinstance="self" width="500"/>
              <comment><pagelink/>to go back to the incriminated page</comment>
            </row>
          </interface>
         
          <interface item="warningList" name="default">
            <row>
              <label width="100" notexpand="1">%s</label>
              <label width="500" notexpand="1">%s</label>
              <label width="100" notexpand="1">%s</label>
            </row>
              <linepanel height="1"/>
            <dyninterface class="warningList" attribute="warningList" interfacename="default"/>
          </interface>
        
          <interface class="warningDetail" name="default">
            <row>
              <readonly evaluate="%s.warningDetail.warningCrfLabel" targetinstance="self" width="100"/>
              <readonly evaluate="%s.warningDetail.warningId" targetinstance="self" width="500"/>
              <input type="simplecheckbox" width="100" attribute="accepted"/>
              <comment><pagelink/>to go back to the incriminated page, or incorporate link in the message</comment>
            </row>
          </interface>
        </interfaces>
        """
        self.interfaceXML = self.interfaceXML % (crfString, errorString, psc.coreCrfName, psc.coreCrfName, crfString, warningString, acceptedString, psc.coreCrfName, psc.coreCrfName)
        self.guiGenerator = GuiGenerator(self,sizer,self.mainLogic,self.showPageCallback)
        #self.guiGenerator.loadInterfaceString(psc.coreCrfName,self.interfaceXML)

        from xml.etree import cElementTree as etree
        interfaceElement = etree.fromstring(self.interfaceXML)
        self.guiGenerator.loadInterfaceString(psc.coreCrfName,interfaceElement)

        from xml.etree import cElementTree as etree
        if self.contentType == "errors":
            pageXML = '<page><interface item="errorList" name="default"/></page>'
        else:
            pageXML = '<page><interface item="warningList" name="default"/></page>'

        self.pageElement = etree.fromstring(pageXML)
 
        self.guiGenerator.objectGuis = dict()
        self.guiGenerator.itemGuis = []

        self.guiGenerator.rootPanel.Freeze()
        try:
            self.guiGenerator.interfacePanel = self.guiGenerator.rootPanel
            self.guiGenerator.interfaceSizer = self.guiGenerator.rootSizer
 
            self.guiGenerator.rootSizer.Clear(True)
            self.guiGenerator.sizersFromRoot = [self.guiGenerator.interfaceSizer]

            self.guiGenerator.iterate(psc.coreCrfName,self.pageElement)

            self.guiGenerator.rootPanel.Layout()
            self.guiGenerator.rootPanel.SetupScrolling(scrollToTop=False)
            self.guiGenerator.rootPanel.Refresh()
            self.guiGenerator.rootPanel.Thaw()
        except:
            self.guiGenerator.rootPanel.Thaw()
            raise

    def registerForNotifications(self):
        notificationCenter.addObserver(self,self.onErrorsChanged,"ErrorsHaveChanged",self.mainLogic.dataSession)
 
    def unregisterForNotifications(self):
        notificationCenter.removeObserver(self,"ErrorsHaveChanged",self.mainLogic.dataSession)
 
    def onErrorsChanged(self,notifyingObject):
        self.updateGui()
    
    def updateGui(self):
        self.guiGenerator.rootPanel.Freeze()
        self.guiGenerator.rootSizer.Clear(True)
        self.guiGenerator.iterate(psc.coreCrfName,self.pageElement)
        self.guiGenerator.rootPanel.Layout()
        self.guiGenerator.rootPanel.SetupScrolling(scrollToTop=False)
        self.guiGenerator.rootPanel.Refresh()
        self.guiGenerator.rootPanel.Thaw()

