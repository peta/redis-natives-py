"""
Annotations/hooks that alter the creation process of ``Redis natives``. 
"""

__version__ = '0.1'
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
    print attr + ": " + str(arg)        
    def hook(rDatatype):
        getattr(rDatatype, attr)(arg)
        return rDatatype    
    cls.after_create.append(hook)
    return cls

def temporary(after=None, at=None):
    """Marks created keys as temporary. They will be destroyed automatically
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
    print "ns: " + ns
    print "sep: " + sep
    cls.before_create.append(lambda key: ns + sep + key)
    return cls
    
def namespaced(ns="", sep=":"):
    """Embeds all created in a given namespace by prefixing their
    keys with namespace ``ns`` and separator ``sep``.
    """
    if type(ns) is type(sep) is str:
        return partial(_namespacedWrapper, ns, sep)
    return _namespacedWrapper("", "", ns)

def _indexedWrapper(rSet, cls):
    print "tracking '" + cls.__name__ + "' by '" + rSet.key + "'"
    def hook(rDatatype):
        rSet.add(rDatatype.key)
        return rDatatype
    cls.after_create.append(hook)

def indexed(index=None):
    """Keeps track of all created keys by adding them to the ``RedisSet``
    named ``index``.
    """
    if not isinstance(index, Set):
        return lambda cls: cls
    else:
        return partial(_indexedWrapper, index)

def _incrementalWrapper(rPrim, cls):
    print "set incremental for '" + cls.__name__ + "'"
    def hook(rDatatype):
        rPrim.incr()
        return rDatatype
    cls.after_create.append(hook)
    return cls

def incremental(rPrim=None):
    """Increments ``RedisPrimitive`` ``rPrim`` by value 1 for each
    created key.
    """
    if not isinstance(rPrim, Primitive):
        return lambda cls: cls
    else:
        return partial(_incrementalWrapper, rPrim) 


if __name__ == "__main__":
    pass
    