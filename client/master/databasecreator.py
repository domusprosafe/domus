import os
import sqlite3

class DatabaseCreator:
    def __init__(self, fileToCheck, scriptToExecute, updateScripts=[], useAPSW=False, encryptionKey=''):
        self.fileToCheck = fileToCheck
        self.scriptToExecute = scriptToExecute
        self.updateScripts = updateScripts
        self.useAPSW = useAPSW
        self.encryptionKey = encryptionKey
        
    def run(self):
        #reading sql script, from file or string
        if os.path.isfile(self.scriptToExecute):
            f = open(self.scriptToExecute, "rb")
            script = f.read()
            f.close()
        elif type(self.scriptToExecute) == type(''):
            script = self.scriptToExecute
 
        if not os.path.exists(self.fileToCheck):
            self.createDbFile()
            self.executeScript(script)
            print  "Database %s successfully created" % self.fileToCheck
        else:
            #print "Database %s already exists" % self.fileToCheck
            pass

        for updateScript in self.updateScripts:
            try:
                self.executeScript(updateScript)
            except Exception, e:
                pass
                #print updateScript
                #print e

    def createDbFile(self):
 
        #creating destination path for database
        destinationAbsPath = os.path.abspath(self.fileToCheck) 
        destinationBasePath = os.path.split(destinationAbsPath)[0]
        if not os.path.isdir(destinationBasePath):
            try:
                os.mkdir(destinationBasePath)
            except:
                raise Exception("You cannot create the contaning folder for database %s. (check path name or permissions)" % self.fileToCheck  ) 
 
    def executeScript(self, script):
       
        #destination file will be created by sqlite3 if not present
        if self.useAPSW:
            import apsw
            from obfuscatedvfs import ObfuscatedVFS
            obfuvfs = ObfuscatedVFS(key=self.encryptionKey)
            conn = apsw.Connection(self.fileToCheck,vfs=obfuvfs.vfsname)
            #conn = apsw.Connection(self.fileToCheck)
            cursor = conn.cursor()
            try:
                cursor.execute(script)
            except Exception, e:
                cursor.close()
                conn.close() 
                raise Exception("Execution of SQL script failed.Base exception:%s" % str(e))  
            cursor.close()
            conn.close()
        else:
            conn = sqlite3.connect(self.fileToCheck)
            try:
                conn.executescript(script)
            except Exception, e:
                conn.close()
                raise Exception("Execution of SQL script failed.Base exception:%s" % str(e))  
            conn.close()
        
#test        
if __name__ == "__main__":
    
    testDatabaseCreator = DatabaseCreator('./data/test.sqlite', './test.sql')
    testDatabaseCreator.run()
    
    testDatabaseCreator = DatabaseCreator('./data/testdirect.sqlite',"""CREATE TABLE classProperty (
  id INTEGER PRIMARY KEY NOT NULL,
  idClass int(11) NOT NULL,
  propertyName VARCHAR(45),
  propertyValue VARCHAR(1000)
)""")
    testDatabaseCreator.run()
    
    #this should fail
    testDatabaseCreator = DatabaseCreator('zzz:/data/testdirect.sqlite',"""CREATE TABLE classProperty (
  id INTEGER PRIMARY KEY NOT NULL,
  idClass int(11) NOT NULL,
  propertyName VARCHAR(45),
  propertyValue VARCHAR(1000)
)""")
    testDatabaseCreator.run()
    
