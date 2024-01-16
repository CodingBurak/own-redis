# Redis Cache Server

## Overview

This project implements a simple Redis-like cache server that supports basic commands for key-value storage and retrieval. The server allows clients to connect and interact with the cache using a custom protocol. It supports commands such as `SET`, `GET`, `DEL`, `INCR`, `DECR`, `LPUSH`, `RPUSH`, `LRANGE`, `SAVE`, `PING`, `ECHO`, and `CONFIG`.

## Project Structure

The project has the following directory structure:
```
.
├── README.md
├── command_handler
│ ├── init.py
│ ├── handler.py
│ ├── parser.py
│ ├── serializer.py
│ └── utils.py
├── file_store_127.0.0.1.json
├── main.py
└── storage
├── init.py
└── cache.py
```

### Main Components

- **`main.py`**: Entry point for the cache server. It sets up a server to handle client connections and delegates command handling to the `CommandHandler`.

- **`command_handler` Directory**: Contains modules for handling commands, parsing commands, serializing responses, and utility functions.

- **`storage` Directory**: Manages the cache and file storage.

## How to Run

1. Make sure you have Python installed on your system.

2. Install the required dependencies:

   ```bash
   pip install asyncio
   ```
Run the cache server:

```bash
python main.py
```
The server will start listening on localhost:6379.

Usage
Connect to the server using a Redis client or a tool like redis-cli and send commands using the custom protocol.

Example:

```bash

$ redis-cli -h localhost -p 6379
localhost:6379> SET mykey myvalue
+OK
localhost:6379> GET mykey
$5
myvalue
```
Supported Commands
```
SET: Set the value of a key.
GET: Get the value of a key.
DEL: Delete one or more keys.
INCR: Increment the integer value of a key.
DECR: Decrement the integer value of a key.
LPUSH: Insert elements at the beginning of a list.
RPUSH: Insert elements at the end of a list.
LRANGE: Get a range of elements from a list.
SAVE: Save the cache to the file system.
PING: Ping the server.
ECHO: Echo the input.
```
Refer to the source code in command_handler/handler.py for a complete list of supported commands.

# Implementation Details

## main.py

The `main.py` file serves as the entry point for the Redis-like cache server. It orchestrates the setup of the server, handles incoming client connections, and delegates the processing of commands to the `CommandHandler`.

### Overview

- **File**: `main.py`
- **Responsibility**: Entry point for the Redis-like cache server.
- **Dependencies**: Requires the `asyncio` module and other components from the project.

### Functionality

1. **Server Initialization**: The script initializes the cache server using the `asyncio.start_server` function, specifying the host (`localhost`) and port (`6379`). It also sets up a callback function (`handle_client`) to handle incoming client connections.

2. **Client Connection Handling**: For each incoming client connection, the `handle_client` function is invoked. It extracts the client's IP address, creates a new `CommandParser` instance, and acquires the corresponding `Cache` instance using the `CacheHolder`. It then enters a loop to continuously read and handle client commands.

3. **Command Processing**: The `CommandParser` is responsible for parsing the incoming commands from clients. The parsed commands are then passed to the `CommandHandler` for execution. The `CommandHandler` processes the commands and returns the appropriate responses.

4. **Response Handling**: The server sends the responses back to the connected clients after processing each command. The responses are encoded as UTF-8 and sent using the `writer.write` method.

5. **Server Start**: Finally, the script calls `asyncio.run(main())` to start the server and listen for incoming client connections indefinitely.

### Usage

1. **Server Startup**: Execute the `main.py` script to start the Redis-like cache server.

   ```bash
   python main.py

## handler.py

The `handler.py` file contains the `CommandHandler` class, which is responsible for processing Redis-like commands received by the cache server. It interprets and executes these commands, interacting with the cache and providing appropriate responses to clients.

### Overview

- **File**: `handler.py`
- **Responsibility**: Command handling and interaction with the cache.
- **Dependencies**: Utilizes components from the project, including the `Serializer`, `SerializorFactory`, and the cache (`RedisCache`).

### Functionality

1. **Command Handling**: The `CommandHandler` class interprets Redis-like commands and executes corresponding actions on the cache. It supports a variety of commands such as `SET`, `GET`, `INCR`, `DECR`, `LPUSH`, `RPUSH`, `LRANGE`, and others.

2. **Command Mapping**: The class maintains a mapping of supported commands to their corresponding handler methods. If a command is not found in the mapping, a default error response is generated.

3. **Serialization**: The handler utilizes the `Serializer` and `SerializorFactory` to serialize command responses before sending them back to clients. This ensures proper formatting according to the Redis protocol.

4. **Error Handling**: In case of unsupported commands or errors during command execution, the `CommandHandler` generates appropriate error responses, maintaining compatibility with the Redis protocol.

5. **Custom Commands**: Developers can extend the `CommandHandler` to add support for custom commands or modify the behavior of existing ones. The handler is designed to be extensible and adaptable to different use cases.


### Design Patterns

#### 1. Functions Map

The `CommandHandler` class follows the Command Handler pattern, where each type of Redis command is encapsulated within a command class. It decouples the sender of the command (received from clients) from the object that processes the command, allowing for extensibility and easy addition of new commands.

#### 2. Factory Pattern

The `SerializorFactory` class implements the Factory Pattern. It provides an interface for creating different types of serializers based on the type of data to be serialized. This promotes flexibility in choosing the appropriate serialization strategy at runtime.

```python
# Example usage of the SerializorFactory
serializer_factory = SerializorFactory()
string_serializer = serializer_factory.create_serializor(str)
```

#### 3. Strategy Pattern
The Serializer class and its strategies (e.g., `StringSerializer`, `NumberSerializer`, `ArraySerializer`) embody the `Strategy Pattern`. This pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. The Serializer class can switch between different serialization strategies dynamically.

#### Setting a serialization strategy in the CommandHandler
handler = CommandHandler(redis_cache_instance)
handler.serializer.set_strategy(serializer_factory.create_serializor(str))


### Usage

The `CommandHandler` is instantiated in the `main.py` file and is responsible for processing commands received from clients. The `handle_command` method is called for each incoming command, and the appropriate response is returned.

### Example

```python
# Creating an instance of the CommandHandler
handler = CommandHandler(redis_cache_instance)

# Handling a command (e.g., SET key value)
response = handler.handle_command(["SET", "key", "value"])
print(response)
```

## cache.py

The `cache.py` file houses the `RedisCache` class, which serves as the in-memory cache for the Redis-like cache server. It manages key-value pairs, supports various data types, and handles expiration based on time-to-live (TTL). Additionally, it includes a `CacheHolder` class responsible for managing multiple client-specific caches.

### Overview

- **File**: `cache.py`
- **Responsibility**: Implementation of the in-memory cache and client-specific cache management.
- **Dependencies**: Uses asyncio for asynchronous task scheduling.

### Classes

#### 1. RedisCache

The `RedisCache` class represents the in-memory cache and is instantiated for each connected client. It includes methods for key-value operations, TTL-based expiration, and task scheduling for cleanup.

#### Key Methods:

- `is_key_existing(keys)`: Checks the existence of keys in the cache.
- `get_by_key(key)`: Retrieves a value by key.
- `delete_by_key(key)`: Deletes a key-value pair.
- `delete_by_keys(keys)`: Deletes multiple key-value pairs.
- `set_key_value(key, value)`: Sets a key-value pair with an optional TTL.
- `lrange(values)`: Retrieves a range of elements from a list.
- `append_to_tail(values)`: Appends elements to the tail of a list.
- `append_to_head(values)`: Appends elements to the head of a list.
- `decrement(key)`: Decrements the value associated with a key.
- `increment(key)`: Increments the value associated with a key.
- `schedule_cleanup(key, ttl)`: Asynchronously schedules the cleanup of a key after a specified TTL.
- `save()`: Persists the cache data to the file system.

#### 2. CacheHolder

The `CacheHolder` class follows the Singleton pattern and manages instances of the `RedisCache` class for different clients. It ensures that each client has a unique cache and can acquire it based on the client's name. The class also provides methods to check cache existence, both in-memory and on the file system.

#### Key Methods:

- `get_client_cache(name)`: Retrieves a client-specific cache from memory.
- `get_client_fs(name)`: Retrieves a client-specific cache from the file system.
- `is_existing(name)`: Checks if a client-specific cache exists in memory.
- `is_in_fs_existing(name)`: Checks if a client-specific cache exists on the file system.
- `acquire_cache(name)`: Acquires a client-specific cache, creating a new one if necessary.

### Design

1. **Singleton Pattern**: The `CacheHolder` class follows the Singleton pattern, ensuring a single instance manages all client-specific caches.

   - **Implementation**: The Singleton pattern is implemented using a private class variable `_instance` and a `__new__` method that creates a new instance only if `_instance` is `None`. This ensures that there is only one instance of `CacheHolder` throughout the application.

2. **Async Task Scheduling**: Asynchronous task scheduling is used for TTL-based key cleanup. This avoids blocking the event loop during waiting periods.

3. **File System Persistence**: Cache data is persisted to the file system using JSON, allowing data to be loaded from the file system on server restarts.

### Usage

The `RedisCache` and `CacheHolder` classes are essential components of the Redis-like cache server. They handle client-specific caching, TTL-based expiration, and data persistence.
## parser.py

The `parser.py` file contains the `CommandParser` class, responsible for parsing commands received by the Redis-like cache server. It implements handlers for different types of commands, including simple strings, errors, integers, strings, and arrays.

### Overview

- **File**: `parser.py`
- **Responsibility**: Parsing commands sent to the cache server.
- **Dependencies**: None.

### Class

#### 1. CommandParser

The `CommandParser` class is designed to interpret and handle various types of Redis-like commands. It uses different methods to handle different command prefixes, such as `+` for simple strings, `-` for errors, `:` for integers, `$` for strings, and `*` for arrays.

#### Key Methods:

- `parse_command(command)`: Parses the given command and dispatches it to the appropriate handler.
- `handle_simple_string(input)`: Handles simple string commands.
- `handle_error(input)`: Handles error commands.
- `handle_integer(input)`: Handles integer commands.
- `handle_string(input)`: Handles string commands.
- `handle_array(input)`: Handles array commands.

### Design

1. **Command Dispatching**: The `CommandParser` uses a dictionary (`command_mappings`) to dispatch commands to specific handler methods based on their prefixes.

2. **Error Handling**: If an unknown command prefix is encountered, the `command_not_found` method is invoked, providing an error message.

### Usage

The `CommandParser` is a crucial component of the Redis-like cache server, responsible for interpreting and directing incoming commands to the appropriate handlers.


## License

This script is part of the Redis-like cache server project and is licensed under the MIT License. See the project's [LICENSE](LICENSE) file for details.



# Customization
Feel free to customize the server and add more features based on your requirements. The project provides a basic framework that you can extend and enhance.
