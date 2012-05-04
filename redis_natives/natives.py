"""
Main module with the ``RedisNativeFactory``. 
"""

__version__ = '0.12'
__author__ = 'Peter Geil'

from functools import partial

from redis_natives import datatypes


class RedisNativeFactory(object):
    """
    Creates instances of Redis natives with a preset ``Redis`` client and
    one or more optional annotation hooks. Normally you won't use 
    ``RedisNativeFactory`` directly, instead create for every as many subclasses
    as you want/need whereby you can annotate each subclass individually.
    
    Note 1: You should override the inherited ``before_create`` and 
    ``after_create`` lists with new ones, otherwise the annotations you add
    will be applied to *all* ``RedisNativeFactory`` subclasses.
 
    Note 2: ``RedisNativeFactory`` is implemented as Singleton. Instead of
    requesting the shared instance over and over again, keep a reference to
    the returned instance (basically a constructor function) as more appropriately
    named variable.
    
    Example:
    ----
    
        from redis import Redis    
        from redis_natives.natives import RedisNativeFactory
        from redis_natives.datatypes import Primitive, Set
        
        rClient = Redis(db=0)
        
        myHitCounter = Primitive(rClient, "global:counter:hits")
        myHitIndex = Set(rClient, "global:index:hitsToday")
        
        @namespaced("hit")
        @indexed(myHitIndex)
        @incremental(myHitCounter)
        class HitFactory(RedisNativeFactory):
            client = Redis(db=1)
            before_create = []
            after_create = []
        
        # Keeping a reference to the constructor
        Hit = HitFactory().Primitive
        
        myIP = Hit("%s:ip" % myHitIndex, "123.123.123.123")
        myReferrer = Hit("%s:referrer" % myHitIndex, "http://twitter.com")
        # your turn! ...
        
    """    
    _instance = None
    
    client = None
    before_create = []
    after_create = []
    
    def __new__(cls, *ka, **kwa):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *ka, **kwa)
        return cls._instance
    
    # Available properties:
    #  - Primitive
    #  - Set
    #  - ZSet
    #  - Dict
    #  - List
    #  - Sequence
    
    def __getattr__(self, name):
        if name in datatypes.__all__:
            cls = getattr(datatypes, name)
            return partial(self._createInstance, self.__class__, cls)
        else:
            raise AttributeError("Property " + name + " doesn't exist")
        
    @staticmethod
    def _createInstance(cls, templateCls, key=None, *ka, **kwa):
        key = "" if (key is None) else key
        for beforeHook in cls.before_create:
            key = beforeHook(key)
        inst = templateCls(cls.client, key, *ka, **kwa)
        for afterHook in cls.after_create:
            afterHook(inst)
        return inst    

    
if __name__ == "__main__":
    pass
    