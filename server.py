import asyncio
import logging

from mysqlproto.protocol import start_mysql_server
from mysqlproto.protocol.handshake import HandshakeV10, HandshakeResponse41


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))


@asyncio.coroutine
def handle_server(server_reader, server_writer):
    handshake = HandshakeV10()
    handshake.write(server_writer)
    yield from server_writer.drain()

    handshake_response = yield from HandshakeResponse41.read(server_reader.packet(1), handshake.capability)
    print("<=", handshake_response.__dict__)

    data = (b'\x00' +
            b'\x00' +
            b'\x00' +
            b'\x02\x00' +
            b'\x00\x00')
    print("=>", data)
    server_writer.write(2, data)
    yield from server_writer.drain()

    while True:
        data = yield from server_reader.packet(0).read()
        print("<=", data)

        data = (b'\xff' +
                b'\x48\x04' +
                b'#HY000' +
                b'Go away')
        print("=>", data)
        server_writer.write(1, data)
        yield from server_writer.drain()


logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
f = start_mysql_server(handle_server, host=None, port=3306)
loop.run_until_complete(f)
loop.run_forever()
