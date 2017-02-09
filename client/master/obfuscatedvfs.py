import apsw
import os, sys, time
import sqlite3

# Inheriting from a base of "" means the default vfs
class ObfuscatedVFS(apsw.VFS):
    def __init__(self, vfsname="obfu", key = '', basevfs=""):
        self.vfsname=vfsname
        self.basevfs=basevfs
        self.key = key
        apsw.VFS.__init__(self, self.vfsname, self.basevfs)

    # We want to return our own file implmentation, but also
    # want it to inherit
    def xOpen(self, name, flags):
        return ObfuscatedVFSFile(self.basevfs, name, flags, self.key)


# The file implementation where we override xRead and xWrite to call our
# encryption routine
class ObfuscatedVFSFile(apsw.VFSFile):
    def __init__(self, inheritfromvfsname, filename, flags, key = ''):
        
        apsw.VFSFile.__init__(self, inheritfromvfsname, filename, flags)
        self.key = key
    
    def encryptB(self,data):
        if not data: return data
        return self.xorCrypt(data)
        
    def decryptB(self,data):
        if not data: return data
        return self.xorCrypt(data)
        
    def xorCrypt(self,data):
        if not data: return data
        return "".join([chr(ord(x)^0xa5) for x in data])
 
    def xRead(self, amount, offset):
        #return self.encryptme(super(ObfuscatedVFSFile, self).xRead(amount, offset))
        return self.decryptB(super(ObfuscatedVFSFile, self).xRead(amount, offset))
    
    def xWrite(self, data, offset):
        #super(ObfuscatedVFSFile, self).xWrite(self.encryptme(data), offset)
        super(ObfuscatedVFSFile, self).xWrite(self.encryptB(data), offset)


if __name__ == '__main__':
    ## obfuvfs=ObfuscatedVFS()
    ## obfudb=apsw.Connection("myobfudb", vfs=obfuvfs.vfsname)
    ## #con = sqlite3.connect(obfudb)
    ## cur = obfudb.cursor()
    ## for r in cur.execute("select * from foo"):
        ## print r
        ## print cur.getdescription()
    ## obfudb.close()
    pass 

