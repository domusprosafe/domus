from sqliteEncrypt import converter
import urllib
import urllib2
import sys
import os


if __name__ == '__main__':
    
    try:
        centreCode = sys.argv[1]
        try:
            lastInputDate = sys.argv[2]
        except:
            lastInputDate = ''
    except:
        print "Usage: prosafe_db_download centreCode [yyyy-mm-dd | 'yyyy-mm-dd HH:MM']"
        sys.exit(1)
    
    password = '123tryandguessthispassword456'    
    url = "https://psserver.marionegri.it/prosafeserver/downloadDbForCentre"
    
    req = urllib2.Request(url)
    data = urllib.urlencode([('password', password), 
                             ('centreCode', centreCode),
                             ('lastInputDate', lastInputDate),
                             ])
                             
    try:
        print "Downloading ..."
        remoteMsg = urllib2.urlopen(req, data)
    except:
        print "Error while downloading db. Please check server status"
        raise
        sys.exit(1)
    
    try:
        contentDisposition =  remoteMsg.info().getheader('Content-disposition')
        fileName = contentDisposition.split(";")[1].split("=")[1]
        tmpFileName = fileName + ".tmp"
    except:
        fileName = "prosafedata%s.sqlite" % centreCode
        tmpFileName = fileName + ".tmp"        
    
    f = open(tmpFileName, 'wb')
    f.write(remoteMsg.read())
    f.close()
    
    try:
        print "Encrypting"
        conv = converter("custom_encryption_key")
        conv.encryptFile(tmpFileName, fileName)
        os.remove(tmpFileName)
    except:
        print "Error in conversion"
        raise
        sys.exit(1)        
    
    print fileName
               