from typing import Callable

from commandhandler.serializer import SerializerFactory, Serializer
from commandhandler.utils import SIMPLE_STRING
from storage.cache import RedisCache


class CommandHandler:

    def __init__(self, redis_cache: RedisCache):
        default_handlers: dict[str, Callable] = {
            'set': self.handle_set,
            'exists': self.handle_exists,
            'del': self.handle_del,
            'incr': self.handle_incr,
            'decr': self.handle_decr,
            'lpush': self.handle_lpush,
            'rpush': self.handle_rpush,
            'lrange': self.handle_lrange,
            'get': self.handle_get,
            'save': self.handle_save,
            'command': self.handle_command,
            'ping': self.handle_ping,
            'echo': self.handle_echo,
            'config': self.handle_config,
        }
        self.command_mappings = default_handlers
        self.serializor_factory = SerializerFactory()
        self.serializer: Serializer = Serializer()
        self.redis_cache = redis_cache

    def handle_command(self, commands: list[str]):
        command, *params = commands
        command = command.lower()
        print(f"commands in handle_command {commands}")
        return self.command_mappings.get(command, lambda: self.command_not_found(command))(*params)

    def handle_config(self, *commands):
        print(f"commands {commands}")
        self.serializer.set_strategy(self.serializor_factory.create_serializor(list))
        return self.serializer.serialize(f"{SIMPLE_STRING}OK")

    def command_not_found(self, input):
        return f"-ERR Command not found! {input}"

    def handle_exists(self, *value):
        from_store = self.redis_cache.is_key_existing(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_del(self, *value):
        from_store = self.redis_cache.delete_by_keys(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_incr(self, value):
        from_store = self.redis_cache.increment(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_decr(self, value):
        from_store = self.redis_cache.decrement(value)

        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_lpush(self, *value):
        from_store = self.redis_cache.append_to_head(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_rpush(self, *value):

        from_store = self.redis_cache.append_to_tail(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_lrange(self, *value):
        from_store = self.redis_cache.lrange(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_get(self, value):
        from_store = self.redis_cache.get_by_key(value)
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(from_store)))
        return self.serializer.serialize(from_store)

    def handle_set(self, *data):
        key, *value = data
        self.serializer.set_strategy(self.serializor_factory.create_serializor(str))
        self.redis_cache.set_key_value(key, value)
        return self.serializer.serialize(f"{SIMPLE_STRING}OK")
    def handle_save(self, _=None):
        try:
            self.redis_cache.save()
            self.serializer.set_strategy(self.serializor_factory.create_serializor(str))
            return self.serializer.serialize(f"{SIMPLE_STRING}OK")
        except Exception:
            return self.serializer.serialize("-ERR save to FileSystem failed")

    def handle_ping(self, _=None):
        self.serializer.set_strategy(self.serializor_factory.create_serializor(str))
        return self.serializer.serialize(f"{SIMPLE_STRING}PONG")

    def handle_echo(self, value):
        print(f"echo value {value}")
        self.serializer.set_strategy(self.serializor_factory.create_serializor(type(value)))
        return self.serializer.serialize(value)
