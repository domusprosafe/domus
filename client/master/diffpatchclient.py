import sys
sys.path.append('../')

import urllib
import urllib2
import pickle
import zlib
import os
import xml.etree.ElementTree as etree
from diff_match_patch import diff_match_patch
import time
import hashlib
import psconstants

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

class DiffPatchClient(object):

    def __init__(self, path, serverUrl):
        self.path = path
        self.serverUrl = serverUrl
        self.filemap = None
        if not os.path.isdir(path):
            os.mkdir(path)

    def performDiffPatch(self):
        print "CRF synchronization"
        self.scanFiles()
        patches = self.requestPatches()
        patchesDict = self.decompressAndUnpickle(patches)
        result = self.applyPatches(patchesDict, None)
        return result
 
    def scanFiles(self):
        out = dict() 
        for file in os.listdir(self.path):
            #print file
            if os.path.splitext(file)[1] != '.xml':
                continue
            try:
                filename = os.path.normpath(os.path.join(self.path, file))
                #to be ok a file must have a version and a crfname (or a name in case of crfname itself)
                fileIsOk = False
                for event, elem in etree.iterparse(filename):
                    tag = elem.tag
                    if tag == "crf":
                        version = elem.get('version')
                        if not version:
                            break
                        basedata = elem.get('basedata')
                        if not basedata:
                            basedata = 0
                        crfname = elem.get('name')
                        majorversion = version.split('.')[0]
                        #print "%s %s" % (tag,version)
                        if (crfname, majorversion, basedata) not in out:
                            out[(crfname, majorversion, basedata)] = dict()
                        if version not in out[(crfname, majorversion, basedata)]:
                            out[(crfname, majorversion, basedata)][version] = dict()
                        if 'config' not in out[(crfname, majorversion, basedata)][version]:
                            out[(crfname, majorversion, basedata)][version]['config'] = dict()   
                            out[(crfname, majorversion, basedata)][version]['config']['filename'] = os.path.basename(filename)
                            out[(crfname, majorversion, basedata)][version]['config']['md5'] = md5_for_file(filename)
                        fileIsOk = True
                        break
                        
                    elif tag in  ["languages", "pages", "interfaces"]:
                        try:
                            version = elem.get('version')
                            if not version:
                                break
                            basedata = elem.get('basedata')
                            if not basedata:
                                basedata = 0
                            crfname = elem.get('crf')
                            majorversion = version.split('.')[0]
                            if (crfname, majorversion, basedata) not in out:
                                out[(crfname, majorversion, basedata)] = dict()
                            if version not in out[(crfname, majorversion, basedata)]:
                                out[(crfname, majorversion, basedata)][version] = dict()
                            if tag not in out[(crfname, majorversion, basedata)][version]:
                                out[(crfname, majorversion, basedata)][version][tag] = dict()
                                out[(crfname, majorversion, basedata)][version][tag]['filename'] = os.path.basename(filename)
                                out[(crfname, majorversion, basedata)][version][tag]['md5'] = md5_for_file(filename)
                            #print "%s %s %s" % (crfname, tag,version)
                        except:
                            raise
                        fileIsOk = True
                        break
            except BaseException, e:
                print e
                pass
 
        self.filemap = out
    
    def requestPatches(self):
        
        #baseVersions = []
        #for crf in self.filemap:
        #    bestVersion =  sorted(self.filemap[crf].keys())[-1]
        #    baseVersions.append(bestVersion)
        #baseVersionsString = '+'.join(baseVersions)
        #
        #if baseVersions is not None:
        #    url = self.serverUrl + '?baseVersionsString=%s' % baseVersionsString
        #else:
        #    url = self.serverUrl

        filemapForServer = dict()
        for crf in self.filemap:
            bestVersion =  sorted(self.filemap[crf].keys())[-1]
            if crf not in filemapForServer:
                filemapForServer[crf] = dict()
            filemapForServer[crf][bestVersion] = self.filemap[crf][bestVersion]
        
        url = self.serverUrl

        req = urllib2.Request(url)
        data = urllib.urlencode({'clientFilemap':self.pickleAndCompress(filemapForServer)})
        f = urllib2.urlopen(url,data)

        return f.read()

    def maxVersion(self, versions):
        splitVersions = [el.split('.') for el in versions]
        paddedVersions = ['%010d.%010d.%010d' % (int(el[0]),int(el[1]),int(el[2])) for el in splitVersions]
        maxVersion = max(paddedVersions)
        splitMaxVersion = maxVersion.split('.')
        return '%d.%d.%d' % (int(splitMaxVersion[0]),int(splitMaxVersion[1]),int(splitMaxVersion[2]))
 
    def applyPatches(self, patchesDict, baseVersion):

        result = []
        for crfname in patchesDict:
            for version in [v for v in patchesDict[crfname] if v != baseVersion]:
                max_minor_version = max([ver for ver in patchesDict[crfname]])
                #max_minor_version = self.maxVersion(patchesDict[crfname].keys())

                for filetype in patchesDict[crfname][version]:
                    if version != max_minor_version:
                        continue
                    filename = patchesDict[crfname][version][filetype]['filename']
                    baseFilename = os.path.basename(filename)
                    targetFilename = os.path.join(self.path,baseFilename)
                    tempFilename = os.path.join(self.path,'temp'+baseFilename)
                    gdiffer = diff_match_patch()
                    patch = gdiffer.patch_fromText(patchesDict[crfname][version][filetype]['patch'])

                    if not patch:
                        continue

                    baseVersion = patchesDict[crfname][version][filetype]['baseversion']
                    if baseVersion is None:
                        print 'Creating new', crfname, version, filetype
                        sourceData = ''
                    else:
                        print 'Patching', crfname, version, filetype
                        sourceFilename = os.path.basename(self.path, self.filemap[crfname][baseVersion][filetype]['filename'])
                        f = open(sourceFilename, 'rb')
                        sourceData = f.read()
                        f.close()

                    data = gdiffer.patch_apply(patch,sourceData)[0]

                    f = open(tempFilename,'wb')
                    f.write(data)
                    f.close()

                    os.rename(tempFilename,targetFilename)

                    result.append(os.path.split(targetFilename)[1]) 

        return result
        
    def pickleAndCompress(self, data):
        rData = repr(data)
        cmpData = zlib.compress(rData)
        return cmpData
            
    def decompressAndUnpickle(self, data):
        dcmpData = zlib.decompress(data)
        unpData = eval(dcmpData)
        return unpData


from threading import Thread
from timesleep import MasterTimeSleep
from networkmanager import QueryServer

class DiffPatchClientManager(object):

    def __init__(self, centreCode, updatedCallback=None):
        self.loopActive = True
        self.firstRun = False
        self.updatedCallback = updatedCallback
        self.centreCode = centreCode

    def performDiffPatch(self, path, serverUrl):
        try:
            diffPatch = DiffPatchClient(path,serverUrl)
            result = diffPatch.performDiffPatch()
            if result:
                self.updatedCallback(result)
        except BaseException, e:
            print e
            print "Couldn't perform CRF synchronization. Waiting until next attempt."
            pass
        self.firstRun = True

    def loop(self, path, serverUrl, timeInterval):
        while True and self.loopActive:
            if QueryServer(self.centreCode,'SynchCRFs','Allow',True):
                self.performDiffPatch(path,serverUrl)
                QueryServer(self.centreCode,'SynchCRFs','Done',True)
            self.firstRun = True
            if not MasterTimeSleep(timeInterval):
                break

    def startLoop(self, path, serverUrl, timeInterval):
        print "Starting DiffPatchClient loop"
        diffPatchClientThread = Thread(target = self.loop, kwargs = {'path':path, 'serverUrl':serverUrl, 'timeInterval':timeInterval})
        diffPatchClientThread.daemon = True
        diffPatchClientThread.start()

    def terminateLoop(self):
        self.loopActive = False


if __name__ == '__main__':
    pass
    #diffPatch = DiffPatchClientManager('config_client','http://localhost:8080/getPatches')
    #diffPatch.scanFiles()
    #patches = diffPatch.requestPatches()
    #patchesDict =  diffPatch.decompressAndUnpickle(patches)
    #diffPatch.applyPatches(patchesDict,None)

