try:
    import redis
    print("Redis package is installed")
    try:
        import redis.asyncio as aioredis
        print("redis.asyncio is available")
    except ImportError:
        try:
            import aioredis
            print("aioredis package is available")
        except ImportError:
            print("No async Redis client available")
except ImportError:
    print("Redis package is NOT installed")