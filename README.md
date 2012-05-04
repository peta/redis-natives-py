# redis-natives-py #

A thin abstraction layer on top of [redis-py](http://github.com/andymccurdy/redis-py) that 
exposes Redis entities as native Python datatypes. Simple, plain but powerful. No ORMing 
or model-messing -- this isn't the real purpose of high performance key-value-stores like Redis.

# Available datatypes #

* Primitive* (string)
* Set*
* ZSet
* Dict*
* List*
* Sequence

Every datatype instance is directly bound its accordant Redis entity. No caching. Changes are reflected
immediately to the database and thereby thread-safe and guaranteed to be consistent. Furthermore
all datatypes marked with __*__ implement (almost) exactly the same interface as their builtin relatives.
That allows for a whole range of new use-cases which don't have to be directly connected to the
persistence/database layer.

# Features #

* Bound instances; no caching; changes are immediately reflected to the dstore
* Support for key namespaces along with other utilities (see __RedisNativeFactory__ and __annotations__)
* Most datatypes implement same interface as builtin pendants -- uncomplicated integration in existing systems

# FAQ #

### What about performance in general? ###

I wrote _redis-natives-py_ with performance in mind. I tried to avoid expensive operations where
I could what resulted in a solid piece of code that tries to exploit Redis
capabilities as best and efficient as possible while keeping its memory footprint
as small as possible.

When you have questions or problems with _redis-natives-py_ please contact me via email or
file a bug/ticket in the issue tracker.


# Examples - Datatypes #

Though _redis-natives-py_ bases on [redis-py](http://github.com/andymccurdy/redis-py) it is
assumed that you already have it installed and made it working properly. I will omit the following
two lines in every example so don't wonder where ``rClient`` and ``rnatives`` are coming from.

	from redis import Redis
	import redis_natives_py as rnatives
	
	# Our Redis client instance
	rClient = Redis()

## Functionality shared by _all_ datatypes ##

All datatypes share the following methods/properties that allow you to perform Redis-specific tasks
directly on the entity/instance you want:

* Getter/setter property called ``key``. Changes will be reflected to the store immediately.
* ``type()`` return the Redis-internal datatype name of the associated value
* ``move(redisClient/id)`` moves the key into the database currently selected in the given ``Redis`` instance or described by integer ``id``
* ``rename(newKey, overwrite=True)`` renames the current entity-key to ``newKey`` overwriting an exisiting key with the same name if ``overwrite`` is ``True``
* Property ``expiration`` yields the remaining time in seconds until the entity will be destroyed when it was marked as volatile before
* ``let_expire(nSecs)`` marks the entity as volatile and determines that it will be automatically destroyed in ``nSecs``
* ``let_expire_at(timestamp)`` same as line above, but this time it will be destroyed at given time ``timestamp``


## Primitive ##

You can work with ``Primitive`` exactly as you'd like to with builtin Strings. Primitives expose the 
same interface as String plus something more.

	from rn.datatypes import Primitive

	myTweet = Primitive(rClient, "message:123", "I love PlusFM!")
	myTweet += " P.s.: Bassdrive too!"	
	print "What did I say? " + myTweet.upper()
	# >> I LOVE PLUSFM! P.S.: BASSDRIVE TOO!

When working with Primitive integers there are ``Primitive.incr(by=1)`` and ``Primitive.decr(by=1)``
for incr-/decrementing values.

	from rn.datatypes import Primitive

	myCounter = Primitive(rClient, "counter:messages", 0)
	myCounter.incr()
	myCounter.incr(5)
	myCounter.decr(2)
	# >> 4

## Set ##

You can work with ``Set`` exactly as you'd like to with builtin Sets. Set operations like ``difference`` and 
``intersection`` are of course performed completely on the datastore-side. You even can pass an arbitrary number of Python sets 
and operate with them.

	# No need to give an example on native Python Sets

#### Special methods ####

``Set`` has an additional method called ``grab()`` that simply returns a random element from the ``Set``.

#### Restrictions ####

At the moment ``Set`` doesn't support the methods ``issubset(*others)`` and ``issuperset(other)``. But I will add them 
soon. 

	
## ZSet ##

A special datatype is the ``ZSet`` -- an ordered set. The main characteristic is the concept of a 
score associated to every set element.

	from rn.datatypes import ZSet

	mostPopular = ZSet(rClient, "rank:messages")
	mostPopular.add("message:123", 0)
	mostPopular.incr_score("message:123")
	mostPopular.rank_of("message:123")
	# > 1
	
And when you want to query the 10 most popular messages:

	from random import randint
	from rn.datatypes import ZSet

	mostPopular = ZSet(rClient, "rank:messages")
	
	for i in range(20):
		mostPopular.add("message:%s" % i, 0)
	for i in range(20):
		mostPopular.incr_score("message:%s" % randint(0, 19))
	# Will return the Top-10
	mostPopular.range_by_rank(0, 10, ZOrder.DESC)
 
## Dict ##

You can work with ``Dict`` exactly as you'd like to with builtin Dicts. 

	# No need to give an example on native Python Dicts

#### Special methods ####

``Dict`` has an additional method called ``incr(key, by=1)`` that increments the value associated to ``key`` 
by a given ``int``.

## Sequence ##

The ``Sequence`` datatype implements all functions of ``Redis list`` datatypes. 
Compared to ``List``, a ``Sequence`` doesn't try to meme a native 
``list`` datatype but instead exposes all native functionalities of Redis 
for working with list datatypes.

A typical use-case where this functionality is needed are f.e. FIFO/LIFO 
processings. (stacks/queues)

	lookupQueue = Sequence(rClient, "ipLookups")
	lookupQueue.push_head("123.123.123.123")
	lookupQueue.push_head("124.124.124.124")
	lookupQueue.pop_tail()
	# > 123.123.123.123


# Examples - Annotations & RedisNativeFactory #

When you work with with ``redis_natives`` it might become odd to everytime pass in an instance of ``redis.Redis`` or 
to keep track of all created keys. Even more when you work with pseudo-namespaces (f.e. "global:counter:message") and construct 
the key names in advance. That's why I introduced ``annotations`` which can be applied to a custom ``RedisNativeFactory`` 
subclass.

## RedisNativeFactory ##

Creates instances of Redis natives with a preset ``Redis`` client and one or more optional annotation hooks. Normally 
you won't use ``RedisNativeFactory`` directly, instead create a custom subclass for every entity type requirement you
have. Create as many subclasses as you want/need whereby you can annotate each subclass individually.

Note 1: You should override the inherited ``before_create`` and ``after_create`` lists with new ones, otherwise the 
annotations you add will be applied to *all* ``RedisNativeFactory`` subclasses. 

Note 2: ``RedisNativeFactory`` is implemented as Singleton. Instead of requesting the shared instance over and over again, keep a reference to
the returned instance (basically a constructor function) under an appropriately named variable.

## @namespaced(ns, sep=":") ##

To implicitly embed created keys in one or more namespaces, you use the annotation called ``namespaced(ns, sep=":")``.
They're applied using the decorator syntax to your custom ``RedisNativeFactory`` subclass. Namespaces are constructed from 
top to bottowm whereat you can combine as many namespaces as you like.

	from rn.natives import RedisNativeFactory
	from rn.datatypes import Primitive
	from rn.annotations import namespaced

	@namespaced("a")
	@namespaced("b")
	@namespaced("c")
	class FooFactory(RedisNativeFactory):
	    client = rClient
	    before_create = []
	    after_create = []

	fk = FooFactory().Primitive("fooKey", "barValue")
	print fk
	# > barValue
	print fk.key
	# > a:b:c:fooKey

## @temporary(after=None, at=None) ##

To implicity mark all keys created by a specific ``RedisNativeFactory`` as volatile, you use the annotation called ``@temporary(after=None, at=None)``.
You can either specify if a entity should be automatically destroyed ``after`` a given number of seconds or ``at`` a given timestamp.

__Note Redis' [special handling of volatile keys](http://code.google.com/p/redis/wiki/ExpireCommand)__

	from time import sleep

	from rn.natives import RedisNativeFactory
	from rn.datatypes import Primitive
	from rn.annotations import temporary

	@temporary(after=10)
	class FooFactory(RedisNativeFactory):
	    client = rClient
	    before_create = []
	    after_create = []

	fk = FooFactory().Primitive("fooKey", "Gone in 10 seconds")
	print fk.expiration
	# > 10
	sleep(10)
	print rClient.exists(fk.key)
	# > False
	print fk
	# > TypeError: __repr__ returned non-string (type NoneType)

## @indexed(idxSet) ##

When you must keep reversed/additional indexes of certain entities, the annotation called ``indexed(idxSet)`` will be handy for you. 
For every entity created by the annotated ``RedisNativeFactory`` it will automatically add the entity's key to the given Redis ``Set`` 
``idxSet``.

	from rn.natives import RedisNativeFactory
	from rn.datatypes import Primitive, Set
	from rn.annotations import indexed

	myIndex = Set(rClient, "global:index:createdToday")

	@indexed(myIndex)
	class FooFactory(RedisNativeFactory):
	    client = rClient
	    before_create = []
	    after_create = []

	FooFactory().Primitive("fooKey", "I'm listed in global:index:createdToday too!")
	print myIndex
	# > set(["fooKey"])

## @incremental(rPrim) ##

When you annotate a ``RedisNativeFactory`` with ``@incremental(rPrim)`` the given Redis ``Primitive`` ``rPrim`` will be incremented 
by value 1 for every entity created.

	from rn.natives import RedisNativeFactory
	from rn.datatypes import Primitive
	from rn.annotations import incremental

	myCounter = Primitive(rClient, "global:counter:messages")

	@incremental(myCounter)
	class FooFactory(RedisNativeFactory):
	    client = rClient
	    before_create = []
	    after_create = []

	ff = FooFactory().Primitive
	for i in range(100):
		ff("id-%s" % i, "msgbody-%s" % i)
	print myCounter
	# > 100


## @autonamed(obj) ##

Instead of passing a key-name for every entity to the Datatype constructor, you pass an __arbitrary__ object that is 
__representable as ``str``__ and everytime an entity creation is triggered, ``obj`` is asked to return a ``str`` 
representation of itself that will be used as key name.

	from rn.natives import RedisNativeFactory
	from rn.datatypes import Primitive
	from rn.annotations import incremental, autonamed

	myCounter = Primitive(rClient, "global:counter:messages", 0)

	@incremental(myCounter)
	@autonamed(myCounter)
	class FooFactory(RedisNativeFactory):
	    client = rClient
	    before_create = []
	    after_create = []

	ff = FooFactory().Primitive
	for i in range(100):
		latestKey = ff("id-", "msgbody-%s" % i)
	print myCounter
	# > 100
	print latestKey.key + ": " + latestKey
	# > id-100: msgbody-99

_Note that ``latestKey.key`` has 100 as suffix just because the annotation ``incremental`` was applied before ``autonamed``. Switch 
their order, and ``latestKey.key`` will have the same suffix as the message body._

