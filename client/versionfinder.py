import os
import re
import stat
import urllib2
import zipfile
import shutil
import tempfile
from urlparse import urlparse, urljoin
import psconstants

from esky.bootstrap import parse_version, join_app_version
from esky.errors import *

from esky.finder import DefaultVersionFinder

class DownloadStopped(Exception):
    def __init__(self, err):
        Exception.__init__(self, err)

class ProsafeVersionFinder(DefaultVersionFinder):
    def __init__(self, url, lockfile):
        DefaultVersionFinder.__init__(self, url)
        self.stopped = False        
        self.lockfile = lockfile
        
    def _fetch_file(self,app,url):
        infile = self.open_url(urljoin(self.download_url,url))
        nm = os.path.basename(urlparse(url).path)
        outfilenm = os.path.join(self._workdir(app,"downloads"),nm)
        if not os.path.exists(outfilenm):
            partfilenm = outfilenm + ".part"
            partfile = open(partfilenm,"wb")
            try:
                data = infile.read(1024*512)
                while data:
                    if os.path.exists(self.lockfile):
                        self.stopped = True
                        raise DownloadStopped("Download stopped")
                    partfile.write(data)
                    data = infile.read(1024*512)
            except DownloadStopped:
                infile.close()
                partfile.close()
                os.unlink(partfilenm)
                os.unlink(self.lockfile)
                raise
            except Exception:
                infile.close()
                partfile.close()
                os.unlink(partfilenm)
                print str(Exception)
                raise
        
            infile.close()
            partfile.close()
            os.rename(partfilenm,outfilenm)            
            #copy to currentupdate folder for clients update
            newpath = os.path.abspath(os.path.join(psconstants.abspath('currentupdate'),os.path.basename(outfilenm)))
            shutil.copyfile(outfilenm, newpath)
        
        return outfilenm 
