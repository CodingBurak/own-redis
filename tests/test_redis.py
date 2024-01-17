import socket

import pytest
from unittest.mock import Mock, patch, AsyncMock

from commandhandler.handler import CommandHandler

from commandhandler.parser import CommandParser
from commandhandler.serializer import StringSerializer, NumberSerializer, SerializerFactory, Serializer
from main import handle_client, main, _handle_client
from storage.cache import CacheHolder, RedisCache


@pytest.fixture
def mock_reader_writer():
    reader = Mock()
    writer = Mock()
    writer.get_extra_info.return_value = ("127.0.0.1", "localhost")
    writer.drain = AsyncMock()

    # Create an AsyncMock object for reader.read that returns a coroutine
    async def read_coroutine(_):
        return b'*5\r\n$5\r\nLPUSH\r\n$6\r\nmylist\r\n$2\r\nee\r\n$2\r\nff\r\n$3\r\nggg\r\n'

    # to recreate new coroutines, use side effect, not return_value
    reader.read.side_effect = read_coroutine
    return reader, writer


@pytest.mark.asyncio
async def test_handle_client(mock_reader_writer):
    reader, writer = mock_reader_writer

    # Call the function to be tested
    await _handle_client(reader, writer, CacheHolder(), 'ip1')

    # Assert that the expected methods were called on the mocked writer object
    writer.write.assert_called_once()
    writer.close.assert_called_once()
    writer.drain.assert_called_once()


@pytest.mark.asyncio
async def test_main():
    with patch("asyncio.start_server") as start_server_mock:
        # Test main function
        await main()

        # Add assertions based on your specific implementation
        start_server_mock.assert_called_once_with(
            handle_client, host="localhost", port=6379, family=socket.AF_INET
        )


def test_handle_command():
    redis_cache = RedisCache("ip1")
    command_handler = CommandHandler(redis_cache)

    # Test handle_command for various commands
    result_set = command_handler.handle_command(["set", "key", "1"])
    assert isinstance(command_handler.serializer.strategy, StringSerializer) is True

    result_get = command_handler.handle_command(["get", "key"])
    assert isinstance(command_handler.serializer.strategy, StringSerializer) is True

    result_incr = command_handler.handle_command(["incr", "key"])
    assert isinstance(command_handler.serializer.strategy, NumberSerializer) is True
    # Add assertions based on your specific implementation and expected results
    assert result_set == '+OK\r\n'
    assert result_get == "$1\r\n1\r\n"
    assert result_incr == ':2\r\n'


@pytest.mark.parametrize("value_to_test, expected_result", [
    ("some_value", '$10\r\nsome_value\r\n'),
    (42, ':42\r\n'),
    ([1, 2, 3], '*3\r\n:1\r\n:2\r\n:3\r\n'),
])
def test_serialize(value_to_test, expected_result):
    serializer = Serializer()

    serializer.set_strategy(SerializerFactory.create_serializor(type(value_to_test)))
    result = serializer.serialize(value_to_test)

    assert result == expected_result


def test_parse_command():
    command_parser = CommandParser()

    # Test parse_command for various command types
    result_simple_string = command_parser.parse_command("+OK\r\n")
    result_error = command_parser.parse_command("-Error message\r\n")
    result_integer = command_parser.parse_command(":42\r\n")
    result_string = command_parser.parse_command("$5\r\nhello\r\n")
    result_array = command_parser.parse_command("*3\r\n:1\r\n:2\r\n:3\r\n")

    # Add assertions based on your specific implementation and expected results
    assert result_simple_string == ('OK','')
    assert result_error == ('Error message', '')
    assert result_integer == ('42', '')
    assert result_string == ('hello', '')
    assert result_array == ['1', '2', '3']

