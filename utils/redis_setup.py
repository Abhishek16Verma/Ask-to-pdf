import redis

class RedisClient:
    def __init__(self, host='127.0.0.1', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

r_session_storage = RedisClient()
r_session_storage.set("1", "Hello, Avi. This is a test message stored in Redis.")
print(r_session_storage.get("1"))  # Output: Hello, Avi. This is a test message stored in Redis.