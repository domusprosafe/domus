import Pyro.core
import os, stat
import sys
import hashlib
from psconstants import abspath
import zipfile

def md5_for_file(filename, block_size = 1024 * 8):
    f = open(filename, 'rb')
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    f.close()
    return md5.hexdigest()


def createZip(path, zipfiledest, setPassword=''):
    def walktree (top = ".", depthfirst = True):
        names = os.listdir(top)
        if not depthfirst:
            yield top, names
        for name in names:
            try:
                st = os.lstat(os.path.join(top,name))
            except os.error:
                continue
            if stat.S_ISDIR(st.st_mode):
                for (newtop, children) in walktree(os.path.join(top,name),depthfirst):
                    yield newtop, children
        if depthfirst:
            yield top, names

    list=[]
    if os.path.isfile(path):
        list = [path]
    else:
        for (basepath, children) in walktree(path,False):
              for child in children:
                  f=os.path.join(basepath,child)
                  if os.path.isfile(f):
                        f = f.encode(sys.getfilesystemencoding())
                        list.append(f)

    f=open(zipfiledest,'wb')
    file = zipfile.ZipFile(f,'w')
    for fname in list:
        nfname=os.path.join(os.path.basename(path),fname[len(path)+1:])
        file.write(fname, nfname , zipfile.ZIP_DEFLATED)
    if setPassword:
        file.setpassword(setPassword)
    file.close()
    f.close()

class FileManager(Pyro.core.ObjBase):
    
    def __init__(self, dataPath):
        Pyro.core.ObjBase.__init__(self)
        self.dataPath = dataPath

    def resolvePath(self,path,relativeTo=None):
        if relativeTo == 'version':
            return abspath(path,True)
        elif relativeTo == 'data':
            #return abspath(os.path.join('data',path),False)
            return os.path.join(self.dataPath,path)
        else:
            return abspath(path,False)
 
    def getFileNamesInPath(self,path,extension=None,relativeTo=None):
        path = self.resolvePath(path,relativeTo)
        filenames = os.listdir(path)
        if extension:
            filenames = [filename for filename in filenames if os.path.splitext(filename)[1] == extension]
        return filenames

    def getFileNamesInPathWithMD5(self,path,extension=None,relativeTo=None):
        path = self.resolvePath(path,relativeTo)
        filenames = self.getFileNamesInPath(path,extension)
        filenamesWithMD5 = dict()
        for filename in filenames:
            filenamesWithMD5[filename] = md5_for_file(os.path.join(path,filename))
        return filenamesWithMD5

    def zipFile(self,path,filename,relativeTo=None):
        path = self.resolvePath(path,relativeTo)
        filename = abspath(filename,False)
        createZip(path,filename)
        #createZip(abspath(path,relativeToVersion),abspath(filename,relativeToVersion))

    def getFileContents(self,path,filename,relativeTo=None):
        path = self.resolvePath(path,relativeTo)
        if not os.path.exists(path):
            return None
        #print "FileManager.getFileContents: ", path, filename
        filepath = os.path.join(path,filename)
        f = open(filepath,'rb')
        contents = f.read()
        f.close()
        return contents

    def putFileContents(self,path,filename,contents,relativeTo=None): 
        path = self.resolvePath(path,relativeTo)
        #print "FileManager.putFileContents: ", path, filename
        filepath = os.path.join(path,filename)
        f = open(filepath,'wb')
        f.write(contents)
        f.close()

