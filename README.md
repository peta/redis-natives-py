# redis-natives-py #

A thin abstraction layer on top of [redis-py](http://github.com/andymccurdy/redis-py) that 
exposes Redis entities as native Python datatypes. Simple, plain but powerful. No ORMing 
or model-messing -- this isn't the real purpose of high performance key-value-stores like Redis.

- - - -

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

- - - -

# Features #

* Bound instances; no caching; changes are immediately reflected to the dstore
* Support for key namespaces along with other utilities (see __RedisNativeFactory__ and __annotations__)
* Most datatypes implement same interface as builtin pendants -- uncomplicated integration in existing systems

- - - -

# FAQ #

### What about performance in general? ###

I wrote _redis-natives-py_ with performance in mind. I tried to avoid expensive operations where
I could what resulted in an optimized and refactored piece of code that tries to exploit Redis
capabilities as best and efficient as possible while keeping its memory footprint
as small as possible. Reliable profiling result and further code improvements will follow.

When you have questions or problems with _redis-natives-py_ please contact me via email or
file a bug/ticket in the issue tracker.

- - - -

# Demo: URL shorter service (Will follow soon)#

Interesting demo project that shows how to use _redis-natives-py_ together with [bottle.py]() 
in order to write a full-fledged URL shortener service that even offers hit tracking and statistics.

- - - -

# Examples & Further informations #



Though _redis-natives-py_ bases on [redis-py](http://github.com/andymccurdy/redis-py) it is
assumed that you already have it installed and made it working properly. I will omit the following
two lines in every example so don't wonder where ``rClient`` and ``rnatives`` are coming from.

	from redis import Redis
	import redis_natives_py as rnatives
	
	# Our Redis client instance
	rClient = Redis()

## Functionality shared by _all_ datatypes ##

All datatypes share the following interface that allows you to perform redis-specific tasks
directly on the entity/instance you want:

* Getter/setter property called ``key``. Changes will be reflected to the store immediately.
* ``type()`` return the Redis-internal datatype name of the associated value
* ``move(redisClient/id)`` moves the key into the database currently selected in the given ``Redis`` instance or described by integer ``id``
* ``rename(newKey, overwrite=True)`` renames the current entity-key to ``newKey`` overwriting an exisiting key with the same name if ``overwrite`` is ``True``
* Property ``expiration`` yields the remaining time in seconds when the entity was marked as volatile before
* ``let_expire(nSecs)`` marks the entity as volatile and determines that it will be automatically destroyed in ``nSecs``
* ``let_expire_at(timestamp)`` same as line above, but this time it will be destroyed at given time ``timestamp``


## Primitives ##

You can work with Primitives exactly as you'd like to with builtin Strings. Primitives expose the 
same interface as String plus a bit more.

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

## Sets ##

You can work with Sets exactly as you'd like to with builtin Sets.