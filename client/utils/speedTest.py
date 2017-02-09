import sys
sys.path.append("./master")
sys.path.append("../master")
import apsw
import sqlite3
from obfuscatedvfs import ObfuscatedVFS
import os
import datetime


class speedTester(object):
    
    def __init__(self,key):
        self.key = key
                   
    def test(self, inputfilename, query):
        startTime =  datetime.datetime.now()
        obfuvfs=ObfuscatedVFS(key=self.key)
        sourceConn =  apsw.Connection(inputfilename, vfs=obfuvfs.vfsname)     
        def rowtrace(cursor, row):
            """Called with each row of results before they are handed off.  You can return None to
            cause the row to be skipped or a different set of values to return"""
            out = dict()
            description = cursor.getdescription()
            colnames = [item[0] for item in description]
            for i, item in enumerate(colnames):
                out[item] = row[i]
            
            return out

        
        cur = sourceConn.cursor()
        cur.setrowtrace(rowtrace)
        results = cur.execute(query)

        #list(results)
        #for rs in results.fetchall():
        #for rs in results:
        #    pass
        
        print datetime.datetime.now() - startTime   
        sourceConn.close()    
        
    
    
if __name__ == '__main__':
    
    test = speedTester('custom_encryption_key')
    

    inputfilename = sys.argv[1]
    query = sys.argv[2]
    
    #test.test(inputfilename, "SELECT * from currentObjectData")
    test.test(inputfilename, query)
    
    
