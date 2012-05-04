"""
Annotations/hooks that alter the creation process of ``Redis natives``. 
"""

__version__ = '0.12'
__author__ = 'Peter Geil'

from functools import partial

from redis_natives.datatypes import Set, Primitive

__all__ = (
    "temporary",
    "namespaced",
    "indexed",
    "incremental"
)


def _temporaryWrapper(attr, arg, cls):
    def hook(rDatatype):
        getattr(rDatatype, attr)(arg)
        return rDatatype    
    cls.after_create.append(hook)
    return cls

def temporary(after=None, at=None):
    """Marks created keys as volatile. They will be destroyed automatically
    ``after`` seconds or at given time ``at``.
    """
    if after is at is None:
        return lambda cls: cls
    else:        
        if (after is None):
            attr = "let_expire_at"
            arg = at
        else:
            attr = "let_expire"
            arg = after
        return partial(_temporaryWrapper, attr, arg)

def _namespacedWrapper(ns, sep, cls):
    cls.before_create.append(lambda key: ns + sep + key)
    return cls
    
def namespaced(ns, sep=":"):
    """Embeds all created in a given namespace by prefixing their
    keys with namespace ``ns`` and separator ``sep``.
    """
    if type(ns) is type(sep) is str:
        return partial(_namespacedWrapper, ns, sep)
    return lambda cls: cls

def _indexedWrapper(rSet, cls):
    def hook(rDatatype):
        rSet.add(rDatatype.key)
        return rDatatype
    cls.after_create.append(hook)
    return cls

def indexed(idxSet):
    """Keeps track of all created keys by adding them to the ``RedisSet``
    named ``index``.
    """
    if not isinstance(idxSet, Set):
        return lambda cls: cls
    else:
        return partial(_indexedWrapper, idxSet)

def _incrementalWrapper(rPrim, cls):
    def hook(rDatatype):
        rPrim.incr()
        return rDatatype
    cls.after_create.append(hook)
    return cls

def incremental(rPrim):
    """Increments ``RedisPrimitive`` ``rPrim`` by value 1 for each
    created key.
    """
    if not isinstance(rPrim, Primitive):
        return lambda cls: cls
    else:
        return partial(_incrementalWrapper, rPrim) 

def _autonamedWrapper(name, cls):
    cls.before_create.append(lambda key: key + str(name))
    return cls

def autonamed(obj):
    """Instead of passing a key-name for every entity to the Datatype constructor, 
    you pass an arbitrary object that is representable as ``str`` and everytime 
    an entity creation is triggered, ``obj`` is asked to return a ``str`` representation 
    that will be used as key name.
    """
    if hasattr(obj, "__str__"):
        return partial(_autonamedWrapper, obj)
    return lambda cls: cls 


if __name__ == "__main__":
    pass
    