import asyncio
import socket
from asyncio import StreamReader, StreamWriter
from command_handler.handler import CommandHandler
from command_handler.parser import CommandParser
from storage.cache import CacheHolder

HOST: str = "localhost"
PORT: int = 6379


async def handle_client(reader: StreamReader, writer: StreamWriter, cache_holder: CacheHolder):
    ip, host = writer.get_extra_info('peername')
    print(f"Client connected from {ip}")

    while True:
        parser = CommandParser()
        cache = cache_holder.acquire_cache(ip)
        data = await reader.read(1024)

        encoded = data.decode("utf-8")
        if not encoded:
            break
        parsed_resp = parser.parse_command(encoded)
        handler = CommandHandler(cache)
        handled_resp = handler.handle_command(parsed_resp)
        writer.write(handled_resp.encode())
        await writer.drain()
        writer.close()


async def main():
    cache_holder = CacheHolder()

    server = await asyncio.start_server(lambda r, w: handle_client(r, w, cache_holder),
                                        host=HOST, port=PORT,
                                        family=socket.AF_INET)
    await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
