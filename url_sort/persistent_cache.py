#! /usr/bin/env python3
"""
Disk cache for Python functions.

Function names and arguments must be strings, which makes this suitable for holding filenames in and filenames out of long-running 
processing functions.

By default, cache databases are uniquely named based on hostname. For extra credit, implement a different key-value store if you're 
clustering your batch processing.

See the included _test() function for an example application.
"""
import logging
logger=logging.getLogger(__name__)
debug, info, warn, error, panic = logger.debug, logger.info, logger.warn, logger.error, logger.critical

from datetime import datetime, timedelta
import os, os.path
import shelve as kvs # key-value store, keys must be strings
import uuid

now = datetime.now
host_id = uuid.getnode()

class MemoResult:
    # Subclasses should implement .unbox()
    def __init__(self, expires=None, **kwargs):
        n = self.mtime = now()
        if expires and not isinstance(expires, datetime):
            expires = n + timedelta(**expires)
        self.expires = expires
        self.__dict__.update(kwargs)
    def get_age(self):
        return now()-self.mtime
    def is_expired(self):
        if self.expires:
            if self.expires is True:
                return True
            return self.expires < now()
class MemoFail(MemoResult):
    def __repr__(self):
        return "<failed %s ago>" % self.get_age()
    def unbox(self):
        return self.error_type(*self.error_args)
class MemoSuccess(MemoResult):
    def __repr__(self):
        return "<succeeded %s ago>" % self.get_age()
    def unbox(self):
        return self.result
class MemoDeleted(MemoResult):
    """
    Placeholder in case the backing store cannot safely delete.
    """
    def __repr__(self):
        return "<deleted %s ago>" % self.get_age()
    def __bool__(self):
        return None

class SquashBase:
    """
    Subclass this, implementing the dict-like self.entries and the map and unmap functions _to_key and _from_key
    """
    @staticmethod
    def _to_key(arg):
        return '\0'.join(arg)
    @staticmethod
    def _from_key(arg):
        return arg.split('\0')
    def __len__(self):
        return len(self.entries)
    def __contains__(self, key):
        """
        Checks fresh elements only.
        """
        k =  self._to_key(key)
        if k in self.entries:
            return not self[key].is_expired()
    def __getitem__(self, arg):
        # arg ought to be a tuple or list
        """
        Returns non-deleted contents, expired or not.
        """
        k = self._to_key(arg)
        v = self.entries[k]
        return v or None
    def __setitem__(self, arg, value):
        # arg ought to be a tuple or list
        k = self._to_key(arg)
        self.entries[k] = value
    def __delitem__(self, arg):
        k = self._to_key(arg)
        del self.entries[k]
    def __iter__(self):
        """
        Returns non-deleted arguments, expired or not.
        """
        for k, v in self.entries.items():
            if isinstance(v, MemoDeleted):
                continue
            yield self._from_key(k)
class MemoBase:
    """
    Subclass this, it's just a context manager.
    """
    def __init__(self, filename='.%x.cache' % host_id):
        self.kvs_filename = filename = os.path.expanduser(filename)
        self.entries = kvs.open(filename)
    def close(self):
        self.entries.close()
    def __enter__(self):
        info("%d entries already memoized", len(self))
        return self
    def __exit__(self, e_type, e, traceback):
        # be sure to return True if any exception handling occurred
        self.close()
### If `del` is not allowed by your store, try this:
#    def __delitem__(self, arg):
#        k = self._to_key(arg)
#        self.entries[k] = MemoDeleted()
###

class TextArgMemo(MemoBase, SquashBase):
    def wrap(self, f, expires=None, handle=(Exception)):
        """

        Example arguments:
            expires={ 'days': 365 }
            handle=(MyOwnError)
        """
        fname = f.__name__
        def wrapper(*args, **kwargs):
            key = [ fname, *args ]
            if key in self:
                debug("Cache hit: %s%s", fname, args)
                return self[key].unbox()
            try:
                value = f(*args, **kwargs)
            except handle as e:
                error("%s%s failed: %s", fname, args, e or '(no message)')
                self[key] = MemoFail(error_type=type(e), error_args=e.args, expires=expires)
                return e
            else:
                debug("%s%s succeeded", fname, args)
                self[key] = MemoSuccess(result=value, expires=expires)
                return value
        return wrapper
    def describe(self):
        print(len(self), "entries in '%s':" % self.kvs_filename)
        for key in self:
            fname, *args = key
            print( "\t%s%s" %(fname, tuple(args)) )
    def before(self, before):
        if not isinstance(before, datetime):
            before = now() - timedelta(**before)
        for mr in self.entries.values():
            if (before < mr.mtime):
                yield mr.unbox()
    def after(self, after):
        if not isinstance(after, datetime):
            after = now() - timedelta(**after)
        for mr in self.entries.values():
            if (mr.mtime < after):
                yield mr.unbox()

def _test():
    def crazy_function(filename, *args):
        assert os.path.isfile(filename), "We can't stop here, this is bat country!"
        return os.stat(filename)
    with TextArgMemo() as memo:
        crazy_memo = memo.wrap(crazy_function, expires={ 'seconds': 15 })
        for root, ds, fs in os.walk('.'):
            files = [ os.path.join(root, f) for f in fs ]
            for fn in files:
                cached = crazy_memo(fn)
                try:
                    value = crazy_function(fn)
                except Exception as e:
                    print(fn, "error is "+("fresh" if e.args == cached.args else "stale"))
                else:
                    print(fn, "result is "+("fresh" if value == cached else "stale"))


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    _test()
    with TextArgMemo() as memo:
        memo.describe()

