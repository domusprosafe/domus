import  wx

class PSProgressBar(wx.Frame):
    def __init__(self, parent, max):
        wx.Frame.__init__(self, parent, -1)
        self.parent = parent
        self.max = max
        self.message = ''
        self.count = 0
        self.stepMultiplicator = 1
        self.ruleMultiplicator = 1
        self.imStopping = False
               
    def StartProgressBar(self, title=""):
        
        self.dlg = wx.ProgressDialog(title,
                               "",
                               maximum = self.max,
                               parent=self.parent,
                                style =  wx.PD_APP_MODAL
                                | wx.PD_CAN_ABORT
                                | wx.PD_ELAPSED_TIME
                                #| wx.PD_ESTIMATED_TIME
                                | wx.PD_REMAINING_TIME
                                )
                                
    
                                
    def Step(self, stepValue=1, message='', relativeStep=False, isRule=False):
        self.message = message
        keepGoing = True        
        if self.count < self.max - self.max / 10:
            if relativeStep :
                addValue = stepValue * self.stepMultiplicator
            elif isRule :
                addValue = stepValue * self.ruleMultiplicator
            else: 
                addValue = stepValue
            self.count += addValue            
            (keepGoing, skip) = self.dlg.Update(self.count, self.message)
        if not keepGoing:            
            self.imStopping = True
            #self.dlg.Destroy()        
            return False        
        return True
        
    def Stop(self, message):
        self.message = message
        keepGoing = True
        self.count +=  self.max - self.count
        (keepGoing, skip) = self.dlg.Update(self.count, self.message)
        if not keepGoing or not skip:
            self.dlg.Destroy()        
            return False
        return True
        
    
        