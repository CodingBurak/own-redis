import asyncio
import socket
from asyncio import StreamReader, StreamWriter
from commandhandler.handler import CommandHandler
from commandhandler.parser import CommandParser
from storage.cache import CacheHolder

HOST: str = "localhost"
PORT: int = 6379


class BreakExceptionMarker(Exception): pass


async def _handle_client(reader, writer, cache_holder, ip, ):
    parser = CommandParser()
    cache = cache_holder.acquire_cache(ip)
    data = await reader.read(1024)
    print(f"incoming data {data}")
    encoded = data.decode("utf-8")
    if not encoded:
        raise BreakExceptionMarker
    parsed_resp = parser.parse_command(encoded)
    handler = CommandHandler(cache)
    handled_resp = handler.handle_command(parsed_resp)
    print(f"{handled_resp=}")
    writer.write(handled_resp.encode())
    await writer.drain()
    writer.close()


async def handle_client(reader: StreamReader, writer: StreamWriter):
    ip, host = writer.get_extra_info('peername')
    print(f"Client connected from {ip}")
    cache_holder = CacheHolder()
    try:
        while True:
            await _handle_client(reader, writer, cache_holder, ip)
    except BreakExceptionMarker:
        pass


async def main():
    server = await asyncio.start_server(handle_client,
                                        host=HOST, port=PORT,
                                        family=socket.AF_INET)
    await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
