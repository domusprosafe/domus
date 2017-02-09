import sys
sys.path.append("../master")

import apsw
import sqlite3
from obfuscatedvfs import ObfuscatedVFS
import iterdump
import os


class converter(object):
    
    def __init__(self,key):
        self.key = key
                   
    
    def encryptFile(self, sourcefile, destfile):
        
        try:
            os.remove(destfile)
        except:
            pass
        
        sourceConn =  apsw.Connection(sourcefile)
        obfuvfs=ObfuscatedVFS(key=self.key)
        destConn=apsw.Connection(destfile, vfs=obfuvfs.vfsname)
        cur = destConn.cursor()
        
        dump = iterdump._iterdump(sourceConn)
        for du in dump:
            cur.execute(du)
        cur.close()
              
        sourceConn.close()    
        destConn.close()
        

    
    def decryptFile(self, sourcefile, destfile):
        
        try:
            os.remove(destfile)
        except:
            pass
        
        obfuvfs=ObfuscatedVFS(key=self.key)
        sourceConn =  apsw.Connection(sourcefile, vfs=obfuvfs.vfsname)     
        destConn=apsw.Connection(destfile)
        
        cur = destConn.cursor()
        dump = iterdump._iterdump(sourceConn)
        for du in dump:
            cur.execute(du)
        
        cur.close()
        sourceConn.close()    
        destConn.close()
        
    
    
if __name__ == '__main__':
    
    conv = converter('custom_encryption_key')
    import sys

    operation = sys.argv[1]
    if 'folder' in operation:
        if operation == '--encryptfolder':
            for file in os.listdir('./databases/'):
                print "encrypting files from folder:", file
                conv.encryptFile('./databases/' + file, 'prosafedata' + file)

        elif operation == '--decryptfolder':
            for file in os.listdir('./databases'):
                print "decrypting files from folder", file
                conv.decryptFile('./databases/' + file, 'prosafedata' + file)
    else:
        inputfilename = sys.argv[2]
        outputfilename = sys.argv[3]
        if operation == '--encrypt':
            print "encrypt..."
            conv.encryptFile(inputfilename, outputfilename)

        elif operation == '--decrypt':
            print "decrypt..."
            conv.decryptFile(inputfilename, outputfilename)

    