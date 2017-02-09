import shutil
import os
import sys
def abspath(path='./', verpath=False):
    returnpath = os.path.join(os.getcwd(),path)
    returnpath = os.path.abspath(returnpath) 
    return returnpath
    
if '--app' in sys.argv:
    appName = sys.argv[sys.argv.index('--app')+1]
    if not appName in ['prosafe', 'domus', 'adhd']:
        print 'wrong app name!!'
        sys.exit(0)
    print 'Configuring PROSAFE app %s' % appName
    config_all_path = abspath('config_all',True)
    config_app_path = os.path.join(config_all_path,appName)
    config_master_path = abspath('config_master',True)
    if not os.path.isdir(config_master_path):
        os.mkdir(config_master_path)
    if os.path.isdir(config_app_path):
        fileNames = os.listdir(config_master_path)
        for fileName in fileNames:
            filePath = os.path.join(config_master_path,fileName)
            if not os.path.isfile(filePath):
                continue
            os.remove(filePath)
        fileNames = os.listdir(config_app_path)
        for fileName in fileNames:
            filePath = os.path.join(config_app_path,fileName)
            import shutil
            shutil.copy(filePath,config_master_path)    
else:
    print 'PROSAFE must be configured before building package'
    print 'PLEASE: use --app argument.'
    sys.exit(0)

if os.path.exists('build'):
    print 'removing build directory'
    shutil.rmtree('build')
if os.path.exists('dist'):
    print 'removing dist directory'
    shutil.rmtree('dist')
if os.path.isfile('psconstants.py'):
    shutil.copyfile('psconstants.py', 'psconstantsoriginal.py')
    os.remove('psconstants.py')

    
if '--testmode' in sys.argv:
    print 'building package in test mode'
    shutil.copyfile('psconstantstest.py', 'psconstants.py')
else:
    shutil.copyfile('psconstantsoriginal.py', 'psconstants.py')
    
if '--updateminor' in sys.argv:
    f = open('psversion.py', 'rb')
    versionLine = f.readline()
    savedVersionLine = versionLine
    f.close()
    versionLine = versionLine.replace(' ', '')
    stringVersionIndex = versionLine.index('="') + 2
    versionLine = versionLine[stringVersionIndex:]
    versionLine = versionLine[:versionLine.index('"')]
    versionLineList = versionLine.split('.')
    newVersion = versionLineList[0] + '.' + versionLineList[1] + '.' + str(int(versionLineList[2]) + 1)
    newVersionLine = savedVersionLine.replace(versionLine, newVersion)
    f = open('psversion.py', 'wb')
    f.write(newVersionLine)
    f.close()

os.system("python setup.py.esky bdist_esky")

print 'restoring eventual non-test parameters'
os.remove('psconstants.py')
shutil.copyfile('psconstantsoriginal.py', 'psconstants.py')
print 'package creation completed!'




    
    
