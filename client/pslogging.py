import logging
import logging.handlers
import ConfigParser
import os
import sys
import inspect
from itertools import count

LOGTAGS = ['ExceptionTag', 'AppdataTag', 'BrowserTag', 'MainLogicTag', 'ProsafeMasterTag', 'MainControllerTag', 'GuiGeneratorTag', 'DataSessionTag', 'DataConfigurationTag', 'MainModuleTag', 'AppdataLockTag', 'EvaluatorTag', 'RequiredForStatusTag']

class Whitelist(logging.Filter):
    def __init__(self, whitelist):
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)
        
def singleton(class_):
    instances = {}
    def getInstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getInstance

@singleton
class PsLogger(logging.getLoggerClass()):
    _ids = count(0)
    def __init__(self):
        self.id = self._ids.next()
        print 'self.id', self.id
        self.loggers = dict((value, logging.getLogger(value)) for value in LOGTAGS)
        self.loggers['UnknownTag'] = logging.getLogger('UnknownTag')
        self.readBasicConfig()
        logging.basicConfig(level=logging.ERROR,format=self.format,datefmt=self.datefmt)
        level=eval(self.level)
        for log in LOGTAGS:
            self.loggers[log].setLevel(level)
        hdlr = logging.handlers.RotatingFileHandler('./logs/debug.log', maxBytes=eval(self.size), backupCount=eval(self.backupCount))
        formatter = logging.Formatter(self.format.replace('%%', '%'))
        hdlr.setFormatter(formatter)
        if logging.root.handlers:
            logging.root.handlers[0].stream = sys.stdout
        logging.root.addHandler(hdlr) 
        whitelist = self.readWhiteList()
        
        for handler in logging.root.handlers:
            handler.addFilter(Whitelist(whitelist))
        
    def info(self, lognames, text):
        try:
            text = ', '.join([inspect.getouterframes(inspect.currentframe(), 2)[1][3], text])
        except:
            pass
        for logname in self.stringToList(lognames):
            if logname not in self.loggers:
                self.loggers['UnknownTag'].info(text)
            else:
                self.loggers[logname].info(text)

    def warning(self, lognames, text):
        try:
            text = ', '.join([inspect.getouterframes(inspect.currentframe(), 2)[1][3], text])            
        except:
            pass
        for logname in self.stringToList(lognames):
            if logname not in self.loggers:
                self.loggers['UnknownTag'].info(text)
            else:
                self.loggers[logname].warning(text)
        
    def error(self, lognames, text):
        try:
            text = ', '.join([inspect.getouterframes(inspect.currentframe(), 2)[1][3], text])            
        except:
            pass
        for logname in self.stringToList(lognames):
            if logname not in self.loggers:
                self.loggers['UnknownTag'].info(text)
            else:
                self.loggers[logname].error(text)    
    
    def critical(self, lognames, text):
        try:
            text = ', '.join([inspect.getouterframes(inspect.currentframe(), 2)[1][3], text])
        except:
            pass
        for logname in self.stringToList(lognames):
            if logname not in self.loggers:
                self.loggers['UnknownTag'].info(text)
            else:
                self.loggers[logname].critical(text)

    def debug(self, lognames, text):
        try:
            text = ', '.join([inspect.getouterframes(inspect.currentframe(), 2)[1][3], text])
        except:
            pass
        for logname in self.stringToList(lognames):
            if logname not in self.loggers:
                self.loggers['UnknownTag'].info(text)
            else:
                self.loggers[logname].debug(text)
    
    def exception(self, lognames, text):
        try:
            text = ', '.join([inspect.getouterframes(inspect.currentframe(), 2)[1][3], text])
        except:
            pass
        for logname in self.stringToList(lognames):
            if logname not in self.loggers:
                self.loggers['UnknownTag'].info(text)
            else:
                self.loggers[logname].exception(text)
        
    def stringToList(self, argument):
        if type(argument) == str:
            argument = [argument]
        return argument
        
    def readWhiteList(self):
        wl = []
        if os.path.exists('./logs/whitelist.txt'):
            f = open('./logs/whitelist.txt', 'rb')
            content = f.read()
            f.close()
            wl = [el for el in content.replace("\n","").replace("\r", "").replace(" ","").split(",") if el]
        if wl:
            wl.append('UnknownTag')
        return wl
        
    def createBasicConfig(self):
        config = ConfigParser.SafeConfigParser()
        config.add_section('BasicConfig')
        config.set('BasicConfig','level','logging.INFO')
        config.set('BasicConfig','format','%%(asctime)s %%(name)-20s %%(levelname)-8s %%(message)s')
        config.set('BasicConfig','datefmt','%%m-%%d %%H:%%M')
        config.set('BasicConfig','backupCount','5')
        config.set('BasicConfig','size','3145728')
        with open('./logs/logging.cfg','wb') as configfile:
            config.write(configfile)
        
    def readBasicConfig(self):
        if not os.path.exists('./logs/logging.cfg'):
            self.createBasicConfig()
        config = ConfigParser.SafeConfigParser()
        config.read('./logs/logging.cfg')
        self.level = config.get('BasicConfig','level').format()
        self.format = config.get('BasicConfig','format').format()
        self.datefmt = config.get('BasicConfig','datefmt').format()
        self.backupCount = config.get('BasicConfig','backupCount').format()
        self.size = config.get('BasicConfig','size').format()
        
if __name__ == '__main__':
    psl = PsLogger()
    
    psl.warning(LOG_EXCEPTION_TAG, 'uno')
    psl.info(LOG_APPDATA_TAG, 'due')
    psl.error(LOG_BROWSER_TAG, 'tre')
    