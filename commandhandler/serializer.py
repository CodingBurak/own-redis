from abc import abstractmethod
from collections import defaultdict
from typing import Callable

from commandhandler.utils import NULL_RESP


class SerializationStrategy:
    @abstractmethod
    def serialize(self, value):
        pass

    def concat_crlf(self, value):
        return f"{value}\r\n"


class StringSerializer(SerializationStrategy):
    def serialize(self, value):
        if value.startswith('+') or (not value.isdigit() and value.startswith('-')):
            return self.concat_crlf(value)
        return f"{self.concat_crlf(f'${len(value)}')}{self.concat_crlf(value)}"


class NumberSerializer(SerializationStrategy):
    def serialize(self, value):
        return self.concat_crlf(f":{value}")


class NoneSerializer(SerializationStrategy):
    def serialize(self, value):
        return NULL_RESP


class ArraySerializer(SerializationStrategy):
    def serialize(self, value):
        print(f"array serializer {value}")
        serialized_values = [SerializerFactory.create_serializor(type(val)).serialize(val)
                             for val in value]
        return self.concat_crlf(f"*{len(serialized_values)}") + ''.join(serialized_values)


class Serializer:
    def __init__(self):
        self.strategy: SerializationStrategy | None = None

    def set_strategy(self, strategy: SerializationStrategy):
        self.strategy = strategy

    def serialize(self, value):
        if self.strategy:
            return self.strategy.serialize(value)
        raise ValueError("strategy for serialisation not set")


SerializerInputType = str | list | int | None


class SerializerFactory:
    strategy_types: dict[object, SerializationStrategy | Callable] = defaultdict(
        lambda val: ValueError(f"Unsupported type: {type(val)}"), {
            type(None): NoneSerializer,
            str: StringSerializer,
            int: NumberSerializer,
            list: ArraySerializer
        })

    @staticmethod
    def create_serializor(value: SerializerInputType) -> SerializationStrategy:
        print(f"value {value}")
        strategy: SerializationStrategy | Callable = SerializerFactory.strategy_types.get(value)
        print(f"strategy {strategy}")
        if issubclass(strategy, SerializationStrategy):
            return strategy()
        else:
            raise strategy()
