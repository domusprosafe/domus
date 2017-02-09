import sys
import os
sys.path.append('./utils')
sys.path.append('./master')
from appdatamanager import AppdataManager
from dbmigrator import DBMigrator

if __name__ == '__main__':

    datapath = 'data'
    if len(sys.argv) > 1:
        datapath = sys.argv[1]

    print 'Renaming files in directory %s' % os.path.abspath(datapath)
    os.rename(os.path.join(datapath,'prosafedata.sqlite'),os.path.join(datapath,'prosafedata.sqlite.broken'))
    os.rename(os.path.join(datapath,'prosafedata.sqlite.old.sqlite'),os.path.join(datapath,'prosafedata.sqlite'))

    print 'Migrating DB'
    migrator = DBMigrator(datapath)     
    migrator.migrate() 
    print 'Done migrating DB'

    print 'Encoding appdata.xml'
    key = 'custom_encryption_key'
    appdataManager = AppdataManager(os.path.join(datapath,'appdata.xml'),key)
    appdataManager.loadAppdata(False)
    print appdataManager.getAppdataString()
    appdataManager.writeAppdata(True)
    print 'Done encoding appdata.xml'

