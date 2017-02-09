import sys
sys.path.append('../master')

if __name__ == '__main__':
    
    try:
        fileNameA = sys.argv[1]
        fileNameB = sys.argv[2]
    except:
        print "Usage: db_compare.py filenameA.sqlite filenameB.sqlite"
        print
        sys.exit(1)
    
    if "--nocrypt"  in sys.argv:
        useSqlite = True
    else:
        useSqlite = False
    
    if "--limitdates" in sys.argv:
        limitingDates = True
    else:
        limitingDates = False
        
    
    if useSqlite:
        import sqlite3 as sqlite
        connectionA = sqlite.connect(fileNameA)
        connectionB = sqlite.connect(fileNameB)
    else:
        import apsw
        from obfuscatedvfs import ObfuscatedVFS
        obfuvfs = ObfuscatedVFS(key='custom_encryption_key')
        connectionA = apsw.Connection(fileNameA, vfs=obfuvfs.vfsname)
        connectionB = apsw.Connection(fileNameB, vfs=obfuvfs.vfsname)
    
    tables = dict()
    
    cursorA = connectionA.cursor()
    cursorB = connectionB.cursor()
    
    query = "select name from sqlite_master where type = 'table'"
    results = cursorA.execute(query)
    for r in results:
        tables[r[0]] = False
    
    for table in tables:
        print "Analyzing table %s" % table,
        
        maxDate = None
        whereClause = ""
        if limitingDates:
            if table == 'admissionDeleted':
                try:
                    query = "SELECT max(deleteDate) FROM %s" % table
                    maxDate = cursorA.execute(query).fetchall()[0]
                    if maxDate[0] is not None:
                        whereClause = " WHERE deleteDate < '%s'" % maxDate 
                    else:
                        whereClause = " WHERE 0"
                except:
                    pass
                
            else:
                try:
                    query = "SELECT max(inputDate) FROM '%s'" % table
                    maxDate = cursorA.execute(query).fetchall()[0]
                    if maxDate[0] is not None:
                        whereClause = " WHERE inputDate < '%s'" % maxDate
                    else:
                        whereClause = " WHERE 0"
                except:
                    pass
                
        
        
        results = cursorA.execute("PRAGMA table_info(%s)" % table).fetchall()
        columns = [r[1] for r in results]
        columns_query = []
        for c in columns:
            if c not in ['inputDate', 'deleteDate']:
                columns_query.append(" %s " % c)
            else:
                columns_query.append(" DATETIME(%s) " % c)
            
        columns_query_string = ','.join(columns_query)
        
        query = "SELECT %s FROM %s " % (columns_query_string,table)
        query += whereClause
        
        resultsA = cursorA.execute(query).fetchall()
        resultsB = cursorB.execute(query).fetchall()
                
        matching = True
        for r in resultsA:
            if r not in resultsB:
                matching = False
                break
            else:
                matching = True
        
        print 
        
        if matching:        
            for r in resultsB:
                if r in resultsA:
                    pass
                else:
                    matching = False
                    #break
        
        tables[table] = matching
        print table + " matching: "  + str(tables[table])
    
    print
    
        
    
    connectionA.close()
    connectionB.close()
    