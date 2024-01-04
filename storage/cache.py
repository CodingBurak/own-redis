import asyncio
import json
import os
import time
from asyncio import Task, AbstractEventLoop
from typing import Optional


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


class CacheKeyMissingException(Exception):
    def __init__(self, message="Cache Key is missing"):
        self.message = message
        super().__init__(self.message)


# @singleton
class RedisCache:
    """
    Class for holding redis cache per client
    """
    # instead of a decorator we can declare the singleton definition in the dunder functions
    name: str
    data: dict = {}
    _expire_times: dict = {}
    FILE_STORE = "file_store_"

    def __init__(self, cache_name):
        if not cache_name:
            raise CacheKeyMissingException()
        self.name = cache_name  # Storing the name in the instance
        self.data = {}  # Using a dictionary to store key-value pairs
        self.tasks: dict[str, Task[_T]] = {}
        self.file_name = f"{self.FILE_STORE}{self.name}.json"  # file name to store, we distinguish each client

    def get_name(self):
        return self.name

    def __eq__(self, other: 'RedisCache'):
        return self.name == other.name

    def is_key_existing(self, keys):
        counter = 0
        for key in keys:
            counter = counter + 1 if self.data.get(key, None) else counter
        return counter

    def get_by_key(self, key):
        return self.data.get(key, None)

    def delete_by_key(self, key):
        deleted = False
        if key in self.data:
            del self.data[key]
            deleted = True
        if key in self._expire_times:
            del self._expire_times[key]
        if key in self.tasks:
            self.tasks[key].cancel()
            del self.tasks[key]
        return deleted

    def delete_by_keys(self, keys):
        counter = 0
        for key in keys:
            counter = counter + 1 if self.delete_by_key(key) else counter
        return counter

    def __str__(self):
        return f"{self.name} : {self.data}"

    def set_key_value(self, key, value):
        print(f"scheduled tasks {self.tasks.keys()}")
        value_to_set = value[0]
        if len(value) == 1:
            self.data[key] = value_to_set
        else:
            value_to_set, *rest = value
            print(f"{rest}")
            expire_type, ttl = rest

            if self.is_expiration_in_past(expire_type.lower(), ttl):
                return f"-ERR ${expire_type} is in the past"
            match expire_type.lower():
                case 'ex':
                    schedule_value = int(ttl)
                case 'px':
                    # takes ms need to convert
                    schedule_value = int(ttl) / 1000
                case 'exat':
                    schedule_value = int(ttl) - time.time()
                case 'pxat':
                    schedule_value = (int(ttl) / 1000) - time.time()
                case _:
                    return f"-ERR ${expire_type} is unknown"
            self._expire_times[key] = schedule_value
            # we will create for each expiration its own task
            self.data[key] = value_to_set
            self.tasks[key] = asyncio.create_task(self.schedule_cleanup(key, schedule_value), name=f"cleanup{key}")

        return value_to_set

    # schedule a task for each key with ttl
    async def schedule_cleanup(self, key, ttl):
        print(f"tasks {self.name} {self.tasks.keys()}")
        print(f"called schedule cleanup")
        await asyncio.sleep(ttl)
        print(f"schedule is done {self.name} {key}")
        self.delete_by_key(key)

    async def schedule_global_cleanup(self, seconds):
        """
        alternative approach; instead of scheduling multiple tasks, we can have just have one single
        coroutine running which checks every <seconds> if ANY of the data has expired, can sace resources
        but can have data, which is not cleaned up yet, a third approach will be, to delete on demand,
        when ever the data is accessed, check if the ttl is hit and delete. So if there are not many chache hits,
        we are just using up memory.
        :return:
        """
        while True:
            await asyncio.sleep(seconds)

            now = time.time()
            # we can add some grace period here, imagine the list is very large, we could fail to
            # clean up in worst case, but would be picked in next round
            expired_keys = [key for key, expire_time in self._expire_times.items() if expire_time < now]
            tasks = []
            for key in expired_keys:
                tasks.append(self.delete_by_key(key))

            await asyncio.gather(*tasks)

    def save(self):
        with open(self.file_name, 'w') as file:
            json.dump(self.data, file)

    @staticmethod
    def read_from_fs(file_name):
        try:
            with open(file_name, 'r') as file:
                return json.load(file)
        except IOError:
            return {}

    def lrange(self, values):
        if len(values) < 3:
            return "-ERR wrong number of arguments for command\r\n";
        key, start, end = values
        data = self.data.get(key, [])
        try:
            return data[int(start):int(end) + 1]
        except IndexError:
            return []

    def append_to_tail(self, values):
        key, *tail = values
        # as rpush inserts in order
        existing_data: list | None = self.data.get(key, None)
        if not existing_data:
            self.data[key] = list(tail)
        else:
            self.data[key].extend(list(values))
        return len(self.data.get(key))

    def append_to_head(self, values):
        key, *tail = values
        # as lpush inserts in reversed
        reversed_tail = tail[::-1]
        existing_data: list | None = self.data.get(key, None)
        if not existing_data:
            self.data[key] = list(reversed_tail)
        else:
            self.data[key].extend(list(reversed_tail))
        return len(self.data.get(key))

    def decrement(self, key) -> str | int:
        target = self.data.get(key, None)
        try:
            incremented_value = int(target) - 1
            self.data[key] = str(incremented_value)
            return incremented_value
        except ValueError:
            return "-value is not an integer or out of range"

    def increment(self, key) -> str | int:
        print(f"{key=}")
        target = self.data.get(key, None)
        try:
            incremented_value = int(target) + 1
            self.data[key] = str(incremented_value)
            return incremented_value
        except ValueError:
            return "-value is not an integer or out of range"

    def is_expiration_in_past(self, expire_type, ttl):
        if expire_type == "exat":
            return time.time() > ttl
        if expire_type == "pxat":
            return time.time() > ttl * 1000


class CacheHolder:
    _instance: 'CacheHolder' = None
    _client_caches: list[RedisCache] = []
    _loop: AbstractEventLoop = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._client_caches: list[RedisCache] = []
        return cls._instance

    @classmethod
    def get_client_cache(cls, name) -> Optional[RedisCache]:
        """
        gets the client cache by reading locally and from file system
        :param name:
        :return:
        """
        return next(
            (cache for cache in cls._instance._client_caches if cache.get_name() == name),
            None
        )

    @classmethod
    def get_client_fs(cls, name) -> Optional[RedisCache]:
        data_from_store = RedisCache.read_from_fs(f"{RedisCache.FILE_STORE}{name}.json")
        cache = cls._add_cache(name)
        cache.data = data_from_store
        return cache

    @classmethod
    def _add_cache(cls, name: str):
        new_cache = RedisCache(name)
        cls._instance._client_caches.append(new_cache)
        return new_cache

    @classmethod
    def is_existing(cls, name: str):
        cache = next(
            (cache for cache in cls._instance._client_caches if cache.get_name() == name),
            None
        )
        return bool(cache)

    @classmethod
    def is_in_fs_existing(cls, name: str):
        file_path = f"{RedisCache.FILE_STORE}{name}.json"
        return os.path.isfile(file_path)

    @classmethod
    def acquire_cache(cls, name) -> RedisCache:
        if cls.is_existing(name):
            return cls.get_client_cache(name)
        if cls.is_in_fs_existing(name):
            return cls.get_client_fs(name)
        return cls._add_cache(name)
