import sqlite3
import hashlib
import math
import zlib 
import sys
import datetime
import os
        
def rowSetHash(rows):
    result = hashlib.md5()
    for row in rows:
        for field in row:
            result.update(str(field))
    return result.hexdigest()

## {{{ http://code.activestate.com/recipes/425397/ (r1)
def split_seq(seq, p):
    newseq = []
    n = len(seq) / p    # min items per subsequence
    r = len(seq) % p    # remaindered items
    b,e = 0, n + min(1, r)  # first split
    for i in range(p):
        newseq.append(seq[b:e])
        r = max(0, r-1)  # use up remainders
        b,e = e, e + n + min(1, r)  # min(1,r) is always 0 or 1

    return newseq
## end of http://code.activestate.com/recipes/425397/ }}}



class SynchTableSqlite:
    
    def __init__(self, sqlitedb, tablename, token, hashFields = [], bufferFields=[], minDataChunk = 4, encryptionKey='', useAPSW=False):
        
        self.sqlitedb = sqlitedb
        self.tablename = tablename
        self.token = str(token)
        
        self.tablenameTemp = "temp_"+self.tablename + self.token
        self.viewname = "view_"+self.tablename  + self.token
        
        self.hashFields = hashFields
        self.bufferFields = bufferFields 
        self.minDataChunk = minDataChunk
        
        self.encryptionKey = encryptionKey
        self.useAPSW = useAPSW
        
        self.stats = None
        
        self.connection = None
        self.connect()
        
        cursor = self.connection.cursor();
        cursor.execute("PRAGMA table_info(%s)" % self.tablename)
        tuplesColumns =  cursor.fetchall()
        self.columns = [t[1] for t in tuplesColumns]
        
        cursor.close()
        self.connection.close()
                
        if not self.hashFields:
            self.hashFields = self.columns
        
        self.fields = ','.join(['"'+f+'"' for f in self.hashFields])
        self.allFields = ','.join(['"'+f+'"' for f in self.columns])
        
        self.hashFieldsIndexes = [self.columns.index(f) for f in self.hashFields]
        
        self.rows = list()
        self.numrows = 0
        #initial stats
        self.tableStats()
        self.inserted = 0
        
    def connect(self):
        if self.useAPSW:
            import apsw
            from obfuscatedvfs import ObfuscatedVFS
            obfuvfs = ObfuscatedVFS(key=self.encryptionKey)
            self.connection = apsw.Connection(self.sqlitedb,vfs=obfuvfs.vfsname)
        else:
            self.connection = sqlite3.connect(self.sqlitedb)    
            self.connection.text_factory = str
    
    def tableStats(self): 
        self.rows = list()
        self.numrows = 0 
        
        self.connect()
        
        tempTableQuery = "CREATE TABLE IF NOT EXISTS \"%s\" AS SELECT * FROM \"%s\" WHERE 0" % (self.tablenameTemp, self.tablename)
        viewQuery = "CREATE VIEW IF NOT EXISTS \"%s\" AS SELECT * FROM \"%s\" UNION SELECT * FROM \"%s\" " % (self.viewname, self.tablename, self.tablenameTemp)
               
        cursor = self.connection.cursor()
        cursor.execute(tempTableQuery)
        cursor.execute(viewQuery)
        
        query = "SELECT %s FROM %s ORDER BY %s" % (self.fields, self.viewname, self.fields)
        rs = cursor.execute(query)
        results = rs.fetchall()
        
        for idx, row in enumerate(results):
            self.rows.append(tuple([str(x) for x in row])) 
            
        self.numrows = len(self.rows)
        
        if self.numrows:
            self.minRow = self.rows[0]
            self.maxRow = self.rows[-1]
        else:
            self.minRow = None
            self.maxRow = None
            
        cursor.close()
        self.connection.close() 
        self.stats = self.computeInitialStats()        
        
        
    def computeInitialStats(self, numintervals = 4):
        if not self.stats:
            intervals = self.partitionInterval(numintervals=numintervals)
            stats = self.rowSetStatsForIntervals(intervals)
            return stats
        else:
            return self.stats            
    
    
    def rowSetStats(self, fromRow = None, fromIncluded=True, toRow = None, toIncluded=True, rows=False):
        
        self.connect()
         
        fromIndex = self.getMinRowIndexMatching(fromRow, fromIncluded) 
        toIndex = self.getMaxRowIndexMatching(toRow, toIncluded)
          
        out = dict()
        
        if fromIndex is not None and toIndex is not None and toIndex-fromIndex >= 0:
            numrows = len(self.rows[fromIndex:toIndex+1])
            out['minRow'] = self.rows[fromIndex]
            out['maxRow'] = self.rows[toIndex]
            out['hash'] = rowSetHash(self.rows[fromIndex:toIndex+1]) 
            out['numrows'] = numrows
            
            if numrows <= self.minDataChunk or rows==True:
                #get complete rows from database only when needed
                out['rows'] = []
                query = "SELECT * FROM (SELECT * FROM %s ORDER BY %s) LIMIT %d OFFSET %d" % (self.viewname, self.fields, numrows, fromIndex)
                
                cursor = self.connection.cursor()
                results = cursor.execute(query)
                
                for r in results.fetchall():
                    newRow = []
                    for i,col in enumerate(self.columns):
                        if col in self.bufferFields:
                            newRow.append(buffer(r[i]))
                        else:
                            newRow.append(str(r[i]))   
                    rowforquery = tuple([str(x) for x in newRow])
                    out['rows'].append(rowforquery) 
                   
        else: 
            out['minRow'] = None
            out['maxRow'] = None
            out['hash'] = None
            out['numrows'] = 0 
        
        out['matching'] = False
        
        try:
            cursor.close()  
        except:
            pass
        self.connection.close()
        return out
    
    
        
    def getRowsForInterval(self, fromRow = None, fromIncluded=True, toRow = None, toIncluded=True):
     
        fromIndex = self.getMinRowIndexMatching(fromRow, fromIncluded) 
        toIndex = self.getMaxRowIndexMatching(toRow, toIncluded)
        out = self.rows[fromIndex:toIndex+1] 
        return out
        
        
    def insertRow(self, row):
        
        self.connect()
        newRow = []
        for i,col in enumerate(self.columns):
            if col in self.bufferFields:
                newRow.append(buffer(row[i]))
            else:
                newRow.append(str(row[i]))   
       
        
        placeholders = ['p'+str(i) for i in range(len(newRow))]
        placeholdersstring = ', '.join([':'+p for p in placeholders])
        
        
        query = "INSERT INTO \"%s\" (%s) values (%s)" % (self.tablenameTemp, self.allFields, placeholdersstring)
        params = dict()
        for i, p in enumerate(placeholders):
            params[p] = newRow[i]
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        cursor.close()
        self.connection.close()
        self.inserted += 1
        
        
    def printStats(self, stats, out=sys.stdout):
        
        out.write (str(datetime.datetime.now()))
        out.write('\n\n') 
        for x in stats:
            s = '' 
            for xx in stats[x]:
                s += str(xx) + ': '
                s += str(stats[x][xx])
                s += '\n'
            out.write(s)
            out.write('\n')
         
    
    
    def updateStats(self, statDict): 
        
        inserted = False
        insertedRows = []
                
        for stat in statDict:
            rowsToInsert = []
            if 'rows' in statDict[stat]:
                for row in statDict[stat]['rows']:
                    hashRow = tuple([row[i] for i in self.hashFieldsIndexes])
                    if hashRow not in self.rows and row not in insertedRows:
                        rowsToInsert.append(row)
                        
            for row in rowsToInsert:
                self.insertRow(row)
                insertedRows.append(row)
                inserted = True
                        
            
        if inserted:
            self.tableStats()
        
        
        self.expandAndEvaluateStats(statDict)         
        return self.stats
    
    
    def expandAndEvaluateStats(self, statDict):
        #updating local stats after insert
               
        out = dict()
        
        for stat in statDict:
            if stat not in self.stats:            
                out[stat] = self.rowSetStats(*stat)                
                
        for stat in self.stats:
            
            if stat not in statDict or statDict[stat]['numrows'] == 0:
                out[stat] = self.rowSetStats(*stat, rows=True)     
                continue
            
            equal = self.stats[stat]['hash'] == statDict[stat]['hash']
                        
            if equal == True:                
                out[stat] = self.stats[stat]
                if "rows" in self.stats[stat]:
                    out[stat]['rows'] = []                
                continue
            
            if self.stats[stat]['numrows'] <= self.minDataChunk:
                out[stat] =  self.rowSetStats(*stat, rows=True)        
                
            else:
                for i in self.partitionInterval(*stat, numintervals=2):
                    newStat = self.rowSetStats(*i) 
                    out[i] = newStat
                 
        self.stats = out    
    
    def mergeChanges(self):
        self.connect()
        cursor = self.connection.cursor()
        
        commitQuery = "INSERT INTO \"%s\" SELECT * FROM \"%s\" " % (self.tablename, self.tablenameTemp)
        cursor.execute(commitQuery)
                
        viewQuery = "DROP VIEW \"%s\" " % self.viewname
        tempTableQuery = "DROP TABLE \"%s\" " % self.tablenameTemp
        cursor.execute(tempTableQuery)
        cursor.execute(viewQuery)
        
        cursor.close()
        self.connection.close()       
        
         
    def getMinRowIndexMatching(self, fromRow=None, fromIncluded=True):
        
        if fromRow == None:
            fromRow = self.minRow
        
        if fromIncluded:
            try:
                fromIndex = self.rows.index(fromRow)
            except:
                fromIndex = None
        
        if not fromIncluded or fromIndex is None:
            fromIndex = 0
            found = False
            for e, row in enumerate(self.rows):
                if row > fromRow:
                    found = True
                    break
                fromIndex += 1 
            if not found:
                fromIndex = None
        return fromIndex    
    
    def getMaxRowIndexMatching(self, toRow, toIncluded=True):
      
        if toRow == None:
            toRow = self.maxRow
        
        if toIncluded:
            try:
                toIndex = self.rows.index(toRow)
            except:
                toIndex = None
        
        if not toIncluded or toIndex is None:
            found = False
            toIndex = len(self.rows) - 1
            for e, row in enumerate(reversed(self.rows)):
                if row < toRow:
                    found = True
                    break
                toIndex -= 1
            if not found:
                #pass
                toIndex = None
        return toIndex
   
         
    def partitionInterval(self, fromRow = None, fromIncluded=True, toRow = None, toIncluded=True,numintervals=1):
         
        fromIndex = self.getMinRowIndexMatching(fromRow, fromIncluded) 
        toIndex = self.getMaxRowIndexMatching(toRow, toIncluded)
        
        if toIndex is None or fromIndex is None :
            return  [(fromRow, fromIncluded, toRow, toIncluded)]
        numrows = toIndex - fromIndex + 1     
        if numintervals > numrows:
            numintervals = numrows
            
        pieces = split_seq(self.rows[fromIndex:toIndex+1],numintervals)
        out = [(p[0], True, p[-1], True) for p in pieces]        
        return out
            
         
    def rowSetStatsForIntervals(self, intervals):
        out = dict()
        for i in intervals:   
            row = self.rowSetStats(*i)
            out[i] = row
        
        return out    
    
    
    def isMatching(self, statDict):
                
        rowsInStatDict =0
        for stat in statDict:
            if 'rows' in statDict[stat]:
                rowsInStatDict += len(statDict[stat]['rows'])
                
        #check if tables are empty
        #if self.numrows == 0 and sum([statDict[x]['numrows'] for x in statDict]) ==0:
        if self.numrows == 0 and rowsInStatDict == 0:
            return True
        out = True
                
        for stat in self.stats:
            if stat not in statDict:
                return False
            
            if self.stats[stat]['hash'] !=  statDict[stat]['hash']:                    
                return False 
           
        return out
        

    

if __name__ == '__main__':
    local = SynchTableSqlite('prosafedata.sqlite', 'objectdata', 'atoken', ['objectCode']) 
    #local.printStats(local.stats)
    remote = SynchTableSqlite('aa.sqlite', 'objectdata', 'atoken', ['objectCode'])    
    cycles = 0
    while not remote.isMatching(remote.stats):
        cycles +=1
        rmstats = remote.updateStats(local.stats)   
        lcstats = local.updateStats(remote.stats)     
        #remote.printStats(rmstats)
    
    local.mergeChanges()
    remote.mergeChanges()
    
    print "Total cycles", cycles
    print "Inserted", local.inserted
    
    
            
                 
        
        

