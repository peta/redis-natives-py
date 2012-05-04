# -*- coding: utf-8 -*-
"""
All native datatypes.
"""

__version__ = '0.12'
__author__ = 'Peter Geil, updates by Chris Ridenour'

from collections import MutableMapping, Sequence
from time import time
from random import randint

from redis import Redis
from redis.exceptions import ResponseError

from redis_natives.errors import RedisTypeError, RedisKeyError, RedisValueError

__all__ = (
    "Primitive",
    "Set",
    "ZSet",
    "ZOrder",
    "Dict", 
    "List",
    "Sequence"
)


class RedisDataType(object):
    """
    Base class for all Redis datatypes. Implements basic stuff that is shared
    by all Redis datatypes (derived from it).
    """
    
    __slots__ = ("_pipe", "_client", "_key")
    
    def __init__(self, client, key):
        if not isinstance(key, str):
            raise RedisTypeError("Key must be type of string")
        self._key = str(key)
        if isinstance(client, Redis):
            self._client = client
            # Offer it by for bulk-commands
            self._pipe = client.pipeline()
        else:
            raise RedisTypeError("Argument 'client' must be instance of Redis")
        
    @property
    def key(self):
        """
        The database-internal key name of this object
        """
        return self._key
    
    @key.setter
    def key(self, val):
        self.rename(val)      
    
    @property
    def exists(self):
        """Returns ``True`` if an associated entity for this ``RedisDataType``
        instance already exists. Otherwise ``False``.
        """
        return self._client.exists(self.key)
    
    def type(self):
        """Return the internal name of a datatype. (Specific to Redis)
        """ 
        return self._client.type(self.key)

    def move(self, target):
        """Move this key with its assigned value into another database with
        index ``target``.
        """
        if isinstance(target, Redis):
            dbIndex = target.connection_pool.get_connection('').db
        elif isinstance(target, (int, long)):
            dbIndex = target
        else:
            raise RedisTypeError("Target must be either type of Redis or numerical")
        return self._client.move(self.key, dbIndex)
    
    def rename(self, newKey, overwrite=True):
        """Rename this key into ``newKey``
        """
        oldKey = self.key
        if overwrite:
            if self._client.rename(oldKey, newKey):
                self._key = newKey
                return True
        else:
            if self._client.renamenx(oldKey, newKey):
                self._key = newKey
                return True
        return False
    
    @property
    def expiration(self):
        """The time in *s* (seconds) until this key will be automatically
        removed due to an expiration clause set before.
        """
        return self._client.ttl(self.key)
    
    def let_expire(self, nSecs):
        """Let this key expire in ``nSecs`` seconds. After this time the 
        key with its assigned value will be removed/deleted irretrievably.
        """
        self._client.expire(self.key, int(nSecs))
    
    def let_expire_at(self, timestamp):
        """Let this key expire exactly at time ``timestamp``. When this time 
        arrives the key with its assigned value will be removed/deleted 
        irretrievably.
        """
        self._client.expireat(self.key, int(timestamp))



class RedisSortable(RedisDataType):
    """
    A ``RedisSortable`` base class for bound Redis ``RedisSortables``. 
    (Will probably be removed soon)
    """    
    def sort(self):
        # TODO: Implement using redis' generic SORT function
        raise NotImplementedError("Method 'sort' not yet implemented")   



class Primitive(RedisDataType):
    '''
    A ``Primitive`` is basically the same as a ``str``. It offers all the
    methods of a ``str`` plus functionality to increment/decrement its value.
    '''
    
    __slots__ = ("_key", "_client", "_pipe")
    
    def __init__(self, client, key, value=None):
        super(Primitive, self).__init__(client, key)
        if value is not None:
            self.value = str(value)
           
    #===========================================================================
    # Built-in methods
    #=========================================================================== 
    
    def __add__(self, val):
        return self.value + val
    
    def __iadd__(self, val):
        self._client.append(self.key, val)
        return self
    
    def __contains__(self, val):
        return val in self.value
    
    def __eq__(self, val):
        return self.value == val
    
    def __hash__(self):
        return self.value.__hash__()
    
    def __len__(self):
        return self.value.__len__()
    
    def __mul__(self, val):
        return self.value * val
    
    def __reduce__(self, *ka, **kwa):
        return self.value.__reduce__(*ka, **kwa)
    
    def __str__(self):
        return self.value
    
    __repr__ = __str__
    
    def _formatter_field_name_split(self, *ka, **kwa):
        return self.value._formatter_field_name_split(*ka, **kwa)

    def _formatter_parser(self, *ka, **kwa):
        return self.value._formatter_parser(*ka, **kwa)
    
    def __getslice__(self, i, j):
        return self._client.substr(self.key, i, j)
    
    def __getattr__(self, name):
        # Delegate all other lookups to str
        return self.value.__getattribute__(name)
    
    #===========================================================================
    # Custom methods
    #===========================================================================  
    
    @property
    def value(self):
        '''The current value of this object
        '''
        return self._client.get(self.key)
    
    @value.setter
    def value(self, value):
        self._client.set(self.key, value)

    @value.deleter
    def value(self):
        self._client.delete(self.key)
        
    def incr(self, by=1):
        '''
        Increment the value by value ``by``. (1 by default)
        '''
        try:
            return self._client.incr(self.key, by)
        except ResponseError:
            raise RedisTypeError(
                "Cannot increment Primitive with string-value")    

    def decr(self, by=1):
        '''
        Decrement the value by value ``by``. (1 by default)
        '''
        try:
            return self._client.decr(self.key, by)
        except ResponseError:
            raise RedisTypeError(
                "Cannot decrement Primitive with string-value")



class Set(RedisSortable):
    """
    Re-implements the complete interface of the native ``set`` datatype
    as a bound ``RedisDataType``. Use it exactly as you'd use a ``set``.
    """
    
    __slots__ = ("_key", "_client", "_pipe")
    
    def __init__(self, client, key, iter=[]):
        super(Set, self).__init__(client, key)
        if hasattr(iter, "__iter__") and len(iter):
            # TODO: What if the key already exists?
            for el in iter:
                self._pipe.sadd(key, el)
            self._pipe.execute() 
    
    #===========================================================================
    # Built-in methods
    #=========================================================================== 
    
    def __len__(self):
        return self._client.scard(self.key)
    
    def __contains__(self, value):
        return self._client.sismember(self.key, value)
    
    def __and__(self, other):
        # Remove __and__ due to inefficiency?
        return self._client.smembers(self.key) and other
    
    def __or__(self, other):
        # Remove __or__ due to inefficiency?
        return self._client.smembers(self.key) or other
    
    def __gt__(self, other):
        return self.__len__() > len(other)
    
    def __lt__(self, other):
        return self.__len__() < len(other)

    def __ge__(self, other):
        return self.__len__() >= len(other)
    
    def __le__(self, other):
        return self.__len__() <= len(other)
    
    def __iter__(self):
        # TODO: Is there a better way than getting ALL at once?
        for el in self._client.smembers(self.key):
            yield el
    
    def __repr__(self):
        return str(self._client.smembers(self.key))
    
    #===========================================================================
    # Built-in methods
    #=========================================================================== 
    
    def add(self, el):
        """
		Add element ``el`` to this ``Set``
        """
        return self._client.sadd(self.key, el)
    
    def clear(self):
        """
        Purge/delete all elements from this set
        """
        return self._client.delete(self.key)
    
    def copy(self, key):
        """
        Return copy of this ``Set`` as  
        """
        # TODO: Return native set-object instead of bound redis item?
        self._client.sunionstore(key, [self.key])
        return Set(key, self._client)
    
    def difference(self, *others):
        """
        Return the difference between this set and others as new set
        """
        rsetKeys, setElems = self._splitBySetType(*others)
        rsetElems = self._client.sdiff(rsetKeys)
        return rsetElems.difference(setElems)
    
    def difference_update(self, *others):
        """
        Remove all elements of other sets from this set
        """
        pipe = self._pipe
        for el in self.difference(*others):
            pipe.srem(self.key, el)
        pipe.execute()
        
    # TODO: Implement difference_copy?
    
    def discard(self, member):
        """
        Remove ``member`` form this set; Do nothing when element is not a member.
        """
        self._client.srem(self.key, member)
    
    def intersection(self, *others):
        """
        Return the intersection of this set and others as new set
        """
        rsetKeys, setElems = self._splitBySetType(*others)
        rsetElems = self._client.sinter(rsetKeys)
        return rsetElems.intersection(setElems)
    
    def intersection_update(self, *others):
        """
        Update this set with the intersection of itself and others
        """
        pipe = self._pipe
        for el in self.intersection(*others):
            pipe.srem(self.key, el)
        pipe.execute()
        
    # TODO: Implement intersection_copy?
    
    def pop(self, noRemove=False):
        """
        Remove and return a random element; When ``noRemove`` is ``True``
        element will not be removed. Raises ``KeyError`` if  set is empty.
        """
        if noRemove:
            return self._client.srandmember(self.key)
        else:
            return self._client.spop(self.key)

    def remove(self, el):
        """
        Remove element ``el`` from this set. ``el`` must be a member, 
        otherwise a ``KeyError`` is raised.
        """
        if not self._client.srem(self.key, el):
            raise RedisKeyError("Redis#%s, %s: Element '%s' doesn't exist" % \
                                (self._client.connection_pool.get_connection('').db, self.key, el))
            
    def symmetric_difference(self, *others):
        """
        Return the symmetric difference of this set and others as new set
        """
        rsetKeys, setElems = self._splitBySetType(*others)
        # server-side caching
        baseKey = int(time())
        keyUnion, keyInter = baseKey+"union", baseKey+"inter"
        rsetElems = self._pipe.sinterstore(keyUnion, rsetKeys) \
                              .sunionstore(keyInter, rsetKeys) \
                              .sdiff([keyUnion, keyInter]) \
                              .delete(keyUnion) \
                              .delete(keyInter) \
                        .execute()[2]
        return rsetElems.difference(setElems)  
             
    def symmetric_difference_update(self, *others):
        """
        Update this set with the symmetric difference of itself and others
        """
        pipe = self._pipe
        # Probably faster than getting another diff + iteratively deleting then
        pipe.delete(self.key)
        for el in self.symmetric_difference(*others):
            pipe.sadd(self.key, el)
        pipe.execute()
    
    # TODO: Implement symmetric_difference_copy?
        
    def union(self, *others):
        """
        Return the union of this set and others as new set
        """
        rsetKeys, setElems = self._splitBySetType(*others)
        rsetElems = self._client.sunion(rsetKeys)
        return rsetElems.union(setElems)
        
    def update(self, *others):
        """
        Update a set with the union of itself and others
        """
        pipe = self._pipe
        pipe.delete(self.key)
        for el in self.union(*others):
            pipe.sadd(self.key, el)
        pipe.execute()
        
    def isdisjoint(self, *others):
        """
        Return ``True`` if this set and ``others`` have null intersection
        """
        rsetKeys, setElems = self._splitBySetType(*others)
        rsetElems = self._client.sinter(rsetKeys)
        return rsetElems.isdisjoint(setElems)

    def issubset(self, *other):
        """
        Return ``True`` if this set is contained by another set (subset)
        """
        # TODO: Implement
        raise NotImplementedError("Set.issubset not implemented yet")
        
    def issuperset(self, other):
        """
        Return ``True`` if this set is contained by another set (subset)
        """
        # TODO: Implement
        raise NotImplementedError("Set.issuperset not implemented yet")
    
    #===========================================================================
    # Custom methods
    #===========================================================================  
   
    @staticmethod
    def _splitBySetType(*sets):
        """
        Separates all ``sets`` into native ``sets`` and ``Sets`` 
        and returns them in two lists
        """
        rsetKeys, setElems = [], []
        for s in sets:
            if isinstance(s, Set):
                rsetKeys.append(s.key)
            elif isinstance(s, (set, list)):
                setElems.extend(s)
            else:
                raise RedisTypeError("Object must me type of set/list")
        return rsetKeys, setElems
    
    def grab(self):
        """
        Return a random element from this set;
        Return value will be of ``NoneType`` when set is empty
        """
        return self._client.srandmember(self.key)




class ZOrder(object):
    """
    Enum with supported sort orders of ZSet
    """        
    def __new__(cls):
        return ZOrder
    
    @property
    def ASC(self):
        return 0
    
    @property
    def DESC(self):
        return 1
    
    

class ZSet(RedisSortable):
    """
    An Ordered-set datatype for Python. It's a mixture between Redis' ``ZSet``
    and a simple Set-type. Main difference is the concept of a score associated
    with every member of the set.
    """    
    
    __slots__ = ("_key", "_client", "_pipe")
        
    def __init__(self, client, key, iter=[]):
        super(ZSet, self).__init__(client, key)
        if hasattr(iter, "__iter__") and len(iter):
            # TODO: What if the key already exists?
            for score, val in iter:
                self._pipe.zadd(val, score)
            self._pipe.execute() 
    
    #===========================================================================
    # Built-in methods
    #=========================================================================== 
     
    def __len__(self):
        return self._client.zcard(self.key)
    
    def __contains__(self, value):
        # TODO: Remove __contains__ method due to inefficiency?
        return value in self._client.zrange(self.key, 0, -1)
    
    def __and__(self, other):
        return self._client.zrange(self.key, 0, -1) and other
    
    def __or__(self, other):
        return self._client.zrange(self.key, 0, -1) or other
    
    def __gt__(self, other):
        return self.__len__() > len(other)
    
    def __lt__(self, other):
        return self.__len__() < len(other)

    def __ge__(self, other):
        return self.__len__() >= len(other)
    
    def __le__(self, other):
        return self.__len__() <= len(other)
    
    def __iter__(self):
        # TODO: Is there a better way than getting ALL at once?
        for score, el in self._client.zrange(self.key, 0, -1, withscores=True):
            yield (score, el)
    
    def __repr__(self):
        return str(self._client.zrange(self.key, 0, -1, withscores=True))
       
    #===========================================================================
    # Native set methods
    #===========================================================================
    
    def add(self, el, score):
        """
        Add element ``el`` with ``score`` to this ``ZSet``
        """
        try:
            return self._client.zadd(self.key, str(el), long(score))
        except ValueError:
            return False
    
    def discard(self, member):
        """
        Remove ``member`` form this set; 
        Do nothing when element is not a member
        """
        self._client.zrem(self.key, member)
    
    def copy(self, key):
        """
        Return copy of this ``ZSet`` as new ``ZSet`` with key ``key``  
        """
        # TODO: Return native set-object instead of bound redis item?
        self._client.zunionstore(key, [self.key])
        return ZSet(self._client, key)
    
    def clear(self):
        """
        Purge/delete all elements from this set
        """
        return self._client.delete(self.key)
    
    def pop(self):
        """
		Remove and return a random element from the sorted set.
        Raises ``RedisKeyError`` if  set is empty.
        """		
        length = self.__len__()
        if (length == 0):
            raise RedisKeyError("ZSet is empty")
        idx = randint(0, length-1)
        return self._pipe.zrange(self.key, idx, idx) \
                         .zremrangebyrank(self.key, idx, idx) \
                   .execute()[0]                

    #===========================================================================
    # Custom methods
    #===========================================================================  
    
    def incr_score(self, el, by=1):
        """
        Increment score of ``el`` by value ``by``
        """
        return self._client.zincrby(self.key, el, by) 

    def rank_of(self, el, order=ZOrder.ASC):
        """
        Return the ordinal index of element ``el`` in the sorted set, 
        whereas the sortation is based on scores and ordered according 
        to the ``order`` enum.
        """
        if (order == ZOrder.ASC):
            return self._client.zrank(self.key, el)
        elif (order == ZOrder.DESC):
            return self._client.zrevrank(self.key, el)
    
    def score_of(self, el):
        """
        Return the associated score of element ``el`` in the sorted set.
        When ``el`` is not a member ``NoneType`` will be returned.        
        """
        return self._client.zscore(self.key, el)
    
    def range_by_rank(self, min, max, order=ZOrder.ASC):
        """
        Return a range of elements from the sorted set by specifying ``min``
        and ``max`` ordinal indexes, whereas the sortation is based on 
        scores and ordered according to the given ``order`` enum. 
        """
        if (order == ZOrder.ASC):
            return self._client.zrange(self.key, min, max)
        elif (order == ZOrder.DESC):
            return self._client.zrevrange(self.key, min, max)
    
    def range_by_score(self, min, max):
        """
        Return a range of elements from the sorted set by specifying ``min``
        and ``max`` score values, whereas the sortation is based on scores 
        with a descending order.
        """
        return self._client.zrangebyscore(self.key, min, max)

    def grab(self):
        """
        Return a random element from the sorted set
        """
        length = self.__len__()
        if (length == 0):
            return None
        idx = randint(0, length-1)
        return self._pipe.zrange(self.key, idx, idx)[0]
    
    def intersection_copy(self, dstKey, aggregate, *otherKeys):
        """
        Return the intersection of this set and others as new set
        """
        otherKeys.append(self.key)
        return self._client.zinterstore(dstKey, otherKeys, aggregate)
    
    def union_copy(self, dstKey, aggregate, *otherKeys):
        otherKeys.append(self.key)
        return self._client.zunionstore(dstKey, otherKeys, aggregate)
    
    def remove_range_by_rank(self, min, max):
        """
        Remove a range of elements from the sorted set by specifying the
        constraining ordinal indexes ``min`` and ``max``.
        """
        return self._client.zremrangebyrank(self.key, min, max)
        
    def remove_range_by_score(self, min, max):
        """
        Remove a range of elements from the sorted set by specifying the
        constraining score values ``min`` and ``max``.
        """        
        return self._client.zremrangebyscore(self.key, min, max)
    
            

class Dict(RedisDataType, MutableMapping):
    """
    Re-implements the complete interface of the native ``dict`` datatype
    as a bound ``RedisDataType``. Use it exactly as you'd use a ``dict``.
    """
    
    __slots__ = ("_key", "_client", "_pipe")
        
    def __init__(self, client, key, iter=None):
        super(Dict, self).__init__(client, key)
        if hasattr(iter, "iteritems") and len(iter):
            # TODO: What if the key already exists?         
            self._client.hmset(self.key, iter)
    
    #===========================================================================
    # Built-in methods
    #=========================================================================== 
     
    def __len__(self):
        return self._client.hlen(self.key)
    
    def __iter__(self):
        for k in self._client.hkeys(self.key):
            yield k
    
    def __contains__(self, key):
        return self._client.hexists(self.key, key)
    
    def __getattr__(self, key):
        # Kinda magic-behaviour
        return self._client.hget(self.key, key)
    
    def __getitem__(self, key):
        val = self._client.hget(self.key, key)
        if val is None:
            raise RedisKeyError("Field '" + key + "' doesn't exist")
        return val
    
    def __setitem__(self, key, value):
        self._client.hset(self.key, key, value)
    
    def __delitem__(self, key):
        if not self._client.hdel(self.key, key):
            raise RedisKeyError("Cannot delete field '" + key + \
                                "'. It doesn't exist") 
    
    def __str__(self):
        return str(self.__repr__())
        
    #===========================================================================
    # Native set methods
    #===========================================================================
    
    has_key = __contains__
    
    def clear(self):
        self._client.delete(self.key)
    
    def copy(self, key):
        # TODO: Return native dict instead of bound Dict?
        return Dict(key, self._client,
                         self._client.hgetall(self.key))
    
    def fromkeys(self, dstKey, keys, values=""):
        self._client.hmset(dstKey, dict.fromkeys(keys, values))
        return Dict(dstKey, self._client)
    
    def items(self):
        # dict.items() returns a list with k,v-tuples -- and so do we
        allItems = self._client.hgetall(self.key)
        return zip(allItems.keys(), allItems.values())
    
    def iteritems(self):
        return self._client.hgetall(self.key).iteritems()
        
    def iterkeys(self):
        return iter(self._client.hkeys(self.key))
    
    def itervalues(self):
        return iter(self._client.hvals(self.key))
    
    def keys(self):
        return self._client.hkeys(self.key)
    
    # Inherited mixin methods:
    #   - get
    #   - popitem
    #   - popdef
    
    def setdefault(self, key, default=None):
        try:
            return self[key]
        except RedisKeyError:
            self[key] = default
        return default
    
    def update(self, other, **others):
        pairs = []
        if hasattr(other, "keys"):
            for k in other:
                pairs.extend((k, other[k]))
        else:
            for (k, v) in other:
                pairs.extend((k, v))
        for k in others:
            pairs.extend((k, others[k]))
        # Using redis' bulk-hash-setter
        self._client.hmset(self.key, pairs)
    
    def values(self):
        return self._client.hvals(self.key)
    
    #===========================================================================
    # Custom methods
    #=========================================================================== 
    
    def incr(self, key, by=1):
        return self._client.hincrby(self.key, key, by)
        
        

class List(RedisSortable, Sequence):
    """
    Sequence datatype that tries to meme a native ``list`` datatype by 
    implementing *most* of its methods. Be aware that some methods still exist,
    but will throw ``NotImplementedError``s.
    """ 
    
    __slots__ = ("_key", "_client", "_pipe")
    
    # Though redis doesn't supprt list element removal by index, we're
    # exposing only a Sequence interface to a client. Methods like
    # __setitem__, insert, pop and sort will be available though, becuase
    # we can implement them with native redis functionality    
    
    def __init__(self, client, key, iter=[]):
        super(List, self).__init__(client, key)
        if hasattr(iter, "__iter__") and len(iter):
            # TODO: What if the key already exists?
            for val in iter:
                self._pipe.rpush(self.key, val)
            self._pipe.execute()      
    
    #===========================================================================
    # Built-in methods
    #===========================================================================     
    
    def __contains__(self, el):
        # As long as redis doesn't support lookups by value, we
        # have to use this inefficient workaround
        return el in self._client.lrange(self.key, 0, -1)
    
    def __iter__(self):
        for el in self._client.lrange(self.key, 0, -1):
            yield el 
    
    def __len__(self):
        return self._client.llen(self.key)
    
    def __reversed__(self):
        return self._client.lrange(self.key, 0, -1).reverse()
    
    def __getitem__(self, idx):
        return self._client.lindex(self.key, idx)
    
    def __setitem__(self, idx, el):
        try:
            self._client.lset(self.key, idx, el)
        except ResponseError:
            raise IndexError("Index out of range")
        
    # __delitem__ cannot be implemented (yet) without sideeffects
    def __delitem__(self, idx):
        raise NotImplementedError("Method '__delitem__' not implemented yet")    
        
    #===========================================================================
    # Native methods
    #===========================================================================
    
    def append(self, el):
        """Pushes element ``el`` at the end of this list.
        """
        self._client.rpush(self.key, el)
    
    def count(self, el):
        """Returns the number of occurences of value ``el`` within this list.
        """
        return self._client.lrange(self.key, 0, -1).count(el)    
    
    def extend(self, iter):
        """Extends this list with the elements of ther iterable ``iter``
        """
        if hasattr(iter, "__iter__"):
            map(lambda el: self._pipe.rpush(el), iter)
            self._pipe.execute()
        else:
            raise RedisTypeError("Argument must be iterable")
    
    def insert(self, idx, el):
        """Insert element ``el`` at index ``idx``
        """
        count = self._client.llen(self.key)
        if count < idx:
            raise IndexError("Index out of range")
        else:
            self._client.lset(self.key, idx, el)
    
    def index(self, el):
        """Return index of first occurence of value ``el`` within this list.
        """
        return self._client.lindex(self.key, el)
    
    def pop(self, idx=None):
        """Remove and return element at index ``idx``.
        """
        if idx is not None:
            return self._client.rpop(self.key)
        elif isinstance(idx, int):
            self.__delitem__(idx)
        else:
            raise RedisTypeError("Argument must be type of 'int' or 'NoneType'")
    
    def remove(self, val, n=1, all=False):
        """
        Removes ``n`` occurences of value ``el``. When ``n`` is ``0``
        all occurences will be removed. When ``n`` is negative the lookup 
        start at the end, otherwise from the beginning.
        
        Returns number of removed values as ``int``.
        """
        if all:
            if self._client.lrem(self.key, val, 0): return
        elif isinstance(n, int):
            if self._client.lrem(self.key, val, n): return
        else:
            raise RedisTypeError("Argument 'count' must be type of 'int'")
        raise RedisValueError("Value '" + str(val) + "' not present")
    
    def reverse(self):
        # Only there for the sake of completeness
        raise NotImplementedError("Method 'reverse' not yet implemented")
 
    
    
    
    
class Sequence(RedisSortable, Sequence):
    """
    Sequence datatype that implements all functions of ``Redis list`` datatypes. 
    Compared to ``List``, a ``Sequence`` doesn't try to meme a native 
    ``list`` datatype and instead exposes all native functionalities of Redis 
    for working with list datatypes.
    
    A typical use-case where this functionality is needed are f.e. FIFO/LIFO 
    processings. (stacks/queues)
    """ 
    
    __slots__ = ("_key", "_client", "_pipe")
    
    def __init__(self, client, key, reset=False):
        super(Sequence, self).__init__(client, key)
        # Removed the check for initial iter-values because Sequences
        # will be used for queue-specific stuff and because it matters
        # if b-lpop/b-rpop, I let it up to the user how to insert initials
        if reset:
            # When key already exists: FLush the bastard
            self._client.delete(self.key)
        
    #===========================================================================
    # Built-in/Required methods
    #===========================================================================     
    
    def __str__(self):
        return str(self._client.lrange(self.key, 0, -1))
        
    __repr__ = __str__
    
    def __contains__(self, el):
        # As long as redis doesn't support lookups by value, we
        # have to use this inefficient workaround
        return el in self._client.lrange(self.key, 0, -1)
    
    def __iter__(self):
        #for el in self._client.lrange(self.key, 0, -1):
        for i in range(self.__len__()):
            yield self._client.lindex(self.key, i)
    
    def __len__(self):
        return self._client.llen(self.key)
    
    def __reversed__(self):
        li = self._client.lrange(self.key, 0, -1)
        li.reverse()
        return iter(li)
    
    def __getitem__(self, idx):
        return self._client.lindex(self.key, idx)
    
    def __getslice__(self, start, end):
        return self._client.lrange(self.key, start, end) 
        
    def count(self, el):
        return self._client.lrange(self.key, 0, -1).count(el)    
    
    def index(self, el):
        # Expensive -- but there's no other way
        return self._client.lrange(self.key, 0, -1).index(el)
    
    #===========================================================================
    # Custom methods
    #===========================================================================
    
    def push_head(self, el):
        """
        Push value ``el`` in *front* of this list.
        """
        self._client.lpush(self.key, el)
        return 0
    
    def push_tail(self, el):
        """
        Push value ``el`` at the *end* of this list.
        """
        # Subtracting 1 so that we get the real index within the sequence
        return self._client.rpush(self.key, el) - 1
    
    def pop_head(self):
        """
        Remove and return the *first* element from this list
        """
        return self._client.lpop(self.key)
    
    def pop_tail(self):
        """
        Remove and return the *last* element from this list
        """
        return self._client.rpop(self.key)
    
    def bpop_head(self, keys=[], timeout=0):
        """
        ``pop_tail`` a value off of the first non-empty list named in the 
        ``keys`` list and return it together with the ``key`` that unblocked 
        it as a two-element tuple.

        If none of the lists in ``keys`` has a value to ``pop_tail``, then 
        block for ``timeout`` seconds, or until a value gets pushed on to 
        one of the lists.

        If ``timeout`` is 0, then block indefinitely.
        """
        # For more informations about blocking operations see:
        # ---> http://code.google.com/p/redis/wiki/BlpopCommand
        return self._client.blpop(keys.insert(0, self.key), timeout)
    
    def bpop_tail(self, keys=[], timeout=0):
        """
        ``pop_tail`` a value off of the first non-empty list named in the 
        ``keys`` list and return it together with the ``key`` that unblocked 
        it as a two-element tuple.

        If none of the lists in ``keys`` has a value to ``pop_tail``, then 
        block for ``timeout`` seconds, or until a value gets pushed on to 
        one of the lists.

        If ``timeout`` is 0, then block indefinitely.
        """
        # For more informations about blocking operations see:
        # ---> http://code.google.com/p/redis/wiki/BlpopCommand
        return self._client.brpop(keys.insert(0, self.key), timeout)
    
    def pop_tail_push_head(self, dstKey):
        """
        Removes the *last* element from this list, ``push_head`` it
        to the list with a key named ``dstKey`` (atomically) and finally
        return the value.
        """
        return self._client.rpoplpush(self.key, dstKey)       
    
    def range(self, start, end):
        """
        Returns all elements whose indexes are within the range of ``start``
        and ``end``. When ``start`` or ``end`` are negative the range is
        fetched relative from the end of this list.
        """
        if type(start) is type(end) is int:
            return self.__getslice__(start, end)
        else:
            raise RedisTypeError("Range indexes must be type of 'int'")
            
    def trim(self, start, end):
        """
        Removes/trims all values except those within the index range of 
        ``start`` and ``end``.
        """
        if type(start) is type(end) is int:
            self._client.ltrim(self.key, start, end)
        else:
            raise RedisTypeError("Range indexes must be type of 'int'")
    
    def remove(self, val, n=1, all=False):
        """
        Removes ``n`` occurences of value ``el``. When ``n`` is ``0``
        all occurences will be removed. When ``n`` is negative the lookup 
        start at the end, otherwise from the beginning.
        
        Returns number of removed values as ``int``.
        """
        if all:
            if self._client.lrem(self.key, val, 0): return
        elif isinstance(n, int):
            if self._client.lrem(self.key, val, n): return
        else:
            raise RedisTypeError("Argument 'count' must be type of 'int'")
        raise RedisValueError("Value '" + str(val) + "' not present")
    
    
    
if __name__ == "__main__":
    pass

    
    
    
    
