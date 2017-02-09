import sys
import os
import itertools
import operator
from datetime import datetime
import time
import re
import sqlite3
from collections import defaultdict
from threading import RLock

from uuid import uuid4
from simplejson import loads, dumps
from sqlalchemy import create_engine
#from sqlalchemy.databases import sqlite
#from sqlalchemy.dialects.mssql import pyodbc, mxodbc, pymssql
from sqlalchemy.dialects import sqlite

#import iso8601

import zlib
import base64

from operators import Operator, Equal

class ConflictError(Exception):
        pass

class InvalidError(Exception):
    pass

# http://lists.initd.org/pipermail/pysqlite/2005-November/000253.html
def regexp(expr, item):
    p = re.compile(expr)
    return p.match(item) is not None


class EntryManager(object):
    def __init__(self, index='index.db', **kwargs):
        self.lock = defaultdict(RLock)
        # create tables?
        if not os.path.exists(index):
            with self.lock[index]:
                conn = sqlite3.connect(index)
                conn.executescript("""
                    CREATE TABLE flat (id VARCHAR(255), updated timestamp, position CHAR(255), leaf NUMERIC);
                    CREATE INDEX flatid ON flat (id);
                    CREATE INDEX idposition ON flat (id, position);
                    CREATE TABLE hstore (id VARCHAR(255), dumps NUMERIC); CREATE INDEX hstoreid ON hstore (id);
                    CREATE TABLE store (id VARCHAR(255), dumps NUMERIC); CREATE INDEX storeid ON store (id);""")
                conn.close()

        self.index = index
        self.connect()

    def connect(self):
        self.pool = create_engine('sqlite:///' + self.index)
        
    def dispose(self):
        self.pool.dispose()
        
        
    def create(self, entry=None, indexed_entry=None, indexed_keys=None, **kwargs):
        """
        Add a new entry to the store.

        This can be done by passing a dict, keyword arguments, or a combination of both::

            >>> from jsonstore import EntryManager
            >>> em = EntryManager('test.db')
            >>> em.create({'name': 'Roberto'}, gender='male')

        """
        if entry is None:
            entry = kwargs
        else:
            assert isinstance(entry, dict), "Entry must be instance of ``dict``!"
            entry.update(kwargs)

        id_ = entry.setdefault('__id__', str(uuid4()))
        if indexed_entry != None:
            indexed_entry['__id__'] = id_
        conn = self.pool.connect()
        result = conn.execute("SELECT id FROM flat WHERE id=?", (id_,))
        if result.fetchone():
            raise ConflictError('Conflict, the id "%s" already exists!' % id_)

        # Store entry.
        with self.lock[id_]:
            self._store_entry(entry, indexed_entry=indexed_entry, indexed_keys=indexed_keys)
        return self._load_entry(id_)

    def delete(self, id_):
        """
        Delete a single entry from the store.

        Simply specify the id of the entry to be deleted::

            >>> from jsonstore import EntryManager
            >>> em = EntryManager('test.db')
            >>> em.delete(1)               # delete entry with id "1"

        The deleted entry is returned, in order to be sure that the proper 
        entry was deleted.

        """
        with self.lock[id_]:
            entry = self._load_entry(id_)
            self._delete_entry(id_)
        return entry

    def update(self, entry=None, entry_id=None, indexed_entry=None, indexed_keys=None, condition=lambda old: True, **kwargs): 
        """
        Conditionally update an entry.

        This method allows an entry to be updated, as long as a condition is met. This avoids
        conflicts when two clients are trying to update an entry at the same time.

        Here's a simple example::

            >>> from jsonstore import EntryManager
            >>> em = EntryManager('test.db')
            >>> entry = em.search(__id__=1)[0]

        Suppose we have some hashing function ``hash``, we can then use it to check if the
        entry hasn't been modified before we updated it::
        
            >>> def condition(old, entry=entry):
            ...     return hash(old) == hash(entry)
            >>> entry['foo'] = 'bar' 
            >>> em.update(entry, condition)

        This is used by the REST store for conditional PUT, using etags.

        """
        if entry is None:
            entry = kwargs
        else:
            assert isinstance(entry, dict), "Entry must be instance of ``dict``!"
            entry.update(kwargs)

        if entry_id:
            entry['__id__'] = entry_id
            if indexed_entry != None:
                indexed_entry['__id__'] = entry_id

        id_ = entry['__id__']
        with self.lock[id_]:
            old = self._load_entry(id_)
            if not condition(old):
                raise ConflictError('Pre-condition failed!')
            #self._delete_entry(id_)
            self._store_entry(entry, old_entry=old, indexed_entry=indexed_entry, indexed_keys=indexed_keys, update=True)
            new = self._load_entry(id_)
        return new

    def search(self, obj=None, size=None, offset=0, count=False, **kwargs):
        if count:
            return self.search_ids(obj=obj,size=size,offset=offset,count=count,**kwargs)
        else:
            return [self._load_entry(_id) for _id in self.search_ids(obj=obj,size=size,offset=offset,count=count,**kwargs)]

    def search_ids(self, obj=None, size=None, offset=0, count=False, **kwargs):
        """
        Search database using a JSON object::

            >>> from jsonstore import EntryManager
            >>> from jsonstore.operators import GreaterThan
            >>> em = EntryManager('test.db')
            >>> em.search(type='post', comments=GreaterThan(0))
        
        The algorithm works by flattening the JSON object (the "key"), and searching the
        index table for each leaf of the key using an OR. We then get those ids where the
        number of results is equal to the number of leaves in the key.
        
        """
        if obj is None:
            obj = kwargs
        else:
            assert isinstance(obj, dict), "Search key must be instance of ``dict``!"
            obj.update(kwargs)

        # Check for id.
        obj = obj.copy()
        id_ = obj.pop('__id__', None)

        # Flatten the JSON key object.
        pairs = list(flatten(obj))
        pairs.sort()
        groups = itertools.groupby(pairs, operator.itemgetter(0))

        query = ["SELECT DISTINCT id FROM flat"]
        condition = []
        params = []

        # Check groups from groupby, they should be joined within
        # using an OR.
        leaves = 0
        for (key, group) in groups:
            group = list(group)
            subquery = []
            for position, leaf in group:
                params.append(position)
                if not isinstance(leaf, Operator):
                    leaf = Equal(leaf)
                subquery.append("(position=? AND leaf %s)" % leaf)
                params.extend(leaf.params)
                leaves += 1

            condition.append(' OR '.join(subquery))

        # Build query.
        if condition or id_ is not None:
            query.append("WHERE")
        if id_ is not None:
            query.append("id=?")
            params.insert(0, id_)
            if condition:
                query.append("AND")
        if condition:
            # Join all conditions with an OR.
            query.append("(%s)" % " OR ".join(condition))
        if leaves:
            query.append("GROUP BY id HAVING COUNT(*)=%d" % leaves)
        query.append("ORDER BY updated DESC")
        if size is not None or offset:
            if size is None:
                size = sys.maxint  # we *need* a limit if offset is set
            query.append("LIMIT %s" % size)
        if offset:
            query.append("OFFSET %s" % offset)
        query = ' '.join(query)

        conn = self.pool.connect()
        if count:
            result = conn.execute(
                    "SELECT COUNT(*) FROM (%s) AS ITEMS"
                    % query, tuple(params)).fetchone()[0]
            conn.close()
            return result
        else:
            result = conn.execute(query, tuple(params)).fetchall()
            conn.close()
            return [ row[0] for row in result ]

    def load_value_list(self, id_, positions):
        conn = self.pool.connect()
        if id_ == None:
            bindings = ",".join("?"*len(positions))
            result = conn.execute("SELECT id, position, leaf FROM flat WHERE position IN (%s)" % bindings, positions).fetchall()
            dict_result = {}
            for row in result:
                if row[0] not in dict_result:
                    dict_result[row[0]] = []
                dict_result[row[0]].append({row[1]: row[2]})
            result = dict_result
        elif type(id_) == str:
            bindings = ",".join("?"*len(positions))
            bindingValues = [id_]
            bindingValues.extend(positions)
            result = conn.execute("SELECT position, leaf FROM flat WHERE id=? AND position IN (%s)" % bindings, bindingValues).fetchall()
            result = [{row[0]: row[1]} for row in result]
        else:
            id_bindings = ",".join("?"*len(id_))
            position_bindings = ",".join("?"*len(positions))
            bindingValues = id_[:]
            bindingValues.extend(positions)
            result = conn.execute("SELECT id, position, leaf FROM flat WHERE id IN (%s) AND position IN (%s)" % (id_bindings, position_bindings), bindingValues).fetchall()
            dict_result = {}
            for row in result:
                if row[0] not in dict_result:
                    dict_result[row[0]] = []
                dict_result[row[0]].append({row[1]: row[2]})
            result = dict_result
        #if not result:
        #    raise InvalidError('No such entry: "%s" "%s"' % (id_, position))
        conn.close()
        return result

    def load_values(self, id_, position):
        conn = self.pool.connect()
        if id_ == None:
            result = conn.execute("SELECT id, leaf FROM flat WHERE position=?", (position,)).fetchall()
            dict_result = {}
            for row in result:
                dict_result[row[0]] = row[1]
            result = dict_result
        else:
            result = conn.execute("SELECT leaf FROM flat WHERE id=? AND position=?", (id_,position)).fetchall()
            result = [row[0] for row in result]
        #if not result:
        #    raise InvalidError('No such entry: "%s" "%s"' % (id_, position))
        conn.close()
        return result

    def load_value(self, id_, position):
        conn = self.pool.connect()
        if id_ == None:
            result = conn.execute("SELECT id, leaf FROM flat WHERE position=?", (position,)).fetchone()
            try:
                result = {result[0]: result[1]}
            except:
                pass
        else:
            result = conn.execute("SELECT leaf FROM flat WHERE id=? AND position=?", (id_,position)).fetchone()
            try:
                result = result[0]
            except:
                pass
        if not result:
            result = None
            #raise InvalidError('No such entry: "%s" "%s"' % (id_, position))
        conn.close()
        return result

    def _load_entry(self, id_):
        """
        Load a single entry from the store by id.

        """
        conn = self.pool.connect()
        result = conn.execute("SELECT dumps FROM store WHERE id=?", (id_,)).fetchone()
        if not result:
            raise InvalidError('No such entry: "%s"' % id_)

        result = result[0]

        result = base64.b64decode(result)
        result = zlib.decompress(result)

        result = loads(result)
        #result['__updated__'] = iso8601.parse_date(result['__updated__'])
        conn.close()
        return result

    def date_handler(self,obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    def _store_entry(self, entry, old_entry=None, indexed_entry=None, indexed_keys=None, update=False):
        """
        Store a single entry in the store.

        """
        if indexed_entry == None:
            indexed_entry = entry

        updated_datetime = datetime.utcnow()
        updated_iso = updated_datetime.isoformat()

        entry['__updated__'] = updated_iso

        if indexed_entry != None:
            indexed_entry['__updated__'] = updated_iso

        indexes = [(indexed_entry['__id__'], updated_datetime, k, v)
                for (k, v) in flatten(indexed_entry) if k != '__id__']

        if indexed_keys:
            indexes = [el for el in indexes if el[2].startswith('crfs.') == False or el[2] in indexed_keys]

        entry_id = entry['__id__']
        entry = dumps(entry, default=self.date_handler)
        old_entry = dumps(old_entry, default=self.date_handler)

        entry = zlib.compress(entry)
        entry = base64.b64encode(entry)
        old_entry = zlib.compress(entry)
        old_entry = base64.b64encode(entry)
        
        conn = self.pool.connect()
        transaction = conn.begin()
        try:
            if update:
                conn.execute("DELETE FROM flat WHERE id=?;", (entry_id,))
                conn.execute("DELETE FROM store WHERE id=?;", (entry_id,))
            conn.execute("""
            INSERT INTO flat (id, updated, position, leaf)
            VALUES (?, ?, ?, ?);
            """, indexes)
            conn.execute("""
                INSERT INTO store (id, dumps)
                VALUES (?, ?);
            """, (entry_id, entry))
            conn.execute("""
                INSERT INTO hstore (id, dumps)
                VALUES (?, ?);            
            """, (entry_id, old_entry))
            transaction.commit()
        except BaseException, e:
            transaction.rollback()
        conn.close()

        
        

    def _delete_entry(self, id_):
        """
        Delete a single entry from the store by id.

        """
        conn = self.pool.connect()
        conn.execute("DELETE FROM flat WHERE id=?;", (id_,))
        conn.execute("DELETE FROM store WHERE id=?;", (id_,))
        conn.close()
        
    def needsRestore(self):
        result = False
        conn = self.pool.connect()
        flat = conn.execute("SELECT * FROM flat")
        if not [el for el in flat]:
            store = conn.execute("SELECT * FROM store")
            if [el for el in store]:
                result = True
        
        conn.close()
        return result
        
    def getStore(self):
        conn = self.pool.connect()
        rows = conn.execute("SELECT id, dumps FROM store")
        return [el for el in rows]        

    def emptyFlat(self):
        try:
            conn = self.pool.connect()
            rows = conn.execute("DELETE FROM flat")
            return True
        except BaseException, e:
            print e
        return False

def escape(name):
    try:
        return name.replace('.', '%2E')
    except TypeError:
        return name


def flatten(obj, keys=[]):
    key = '.'.join(keys)
    if isinstance(obj, list):
        for item in obj:
            for pair in flatten(item, keys):
                yield pair
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith('#'):
                newkeys = keys
            else:
                newkeys = keys + [escape(k)]
            for pair in flatten(v, newkeys):
                yield pair
    else:
        yield key, obj
