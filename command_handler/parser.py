from typing import Callable

from command_handler.utils import split_by_CRLF


class CommandParser:

    def __init__(self):
        default_handlers: dict[str, Callable] = {
            '+': self.handle_simple_string,
            '-': self.handle_error,
            ':': self.handle_integer,
            '$': self.handle_string,
            '*': self.handle_array,
            }
        self.command_mappings = default_handlers

    def parse_command(self, command: str):
        return self.command_mappings.get(command[0], lambda: self.command_not_found)(command[1:])

    def command_not_found(self, input):
        return f"Command not found! {input}"

    def handle_simple_string(self, input):
        return split_by_CRLF(input)

    def handle_error(self, input):
        return split_by_CRLF(input)

    def handle_integer(self, input):
        return split_by_CRLF(input)

    def handle_string(self, input):
        command_length, rest = split_by_CRLF(input)
        count = int(command_length)
        value, remaining_tail = rest[:count], rest[count + 2:]  # +2 for skipping '\r\n'
        return value, remaining_tail

    def handle_array(self, input):
        command_length, rest = split_by_CRLF(input)
        count = int(command_length)

        rest_data = rest
        items = []
        # Loop 'count' times to populate the 'items' list
        for _ in range(count):
            # parse rest_data
            parsed_item, new_tail = self.parse_command(rest_data)
            # Update with newTail
            rest_data = new_tail
            # Append parsedItem to the 'items' list
            items.append(parsed_item)

        return items

