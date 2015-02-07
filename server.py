import asyncio
import logging

from mysqlproto.protocol import start_mysql_server
from mysqlproto.protocol.flags import Capability
from mysqlproto.protocol.handshake import HandshakeV10, HandshakeResponse41, AuthSwitchRequest


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))


@asyncio.coroutine
def handle_server(server_reader, server_writer):
    seq = 0

    handshake = HandshakeV10()
    handshake.write(server_writer, seq)
    seq += 1
    yield from server_writer.drain()

    handshake_response = yield from HandshakeResponse41.read(server_reader.packet(seq), handshake.capability)
    seq += 1
    print("<=", handshake_response.__dict__)

    if (Capability.PLUGIN_AUTH in handshake_response.capability_effective and
            handshake.auth_plugin != handshake_response.auth_plugin):
        AuthSwitchRequest().write(server_writer, seq)
        seq += 1
        yield from server_writer.drain()

        auth_response = yield from server_reader.packet(seq).read()
        seq += 1
        print("<=", auth_response)

    data = (b'\x00' +
            b'\x00' +
            b'\x00' +
            b'\x02\x00' +
            b'\x00\x00')
    print("=>", data)
    server_writer.write(seq, data)
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
