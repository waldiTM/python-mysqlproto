import asyncio
import logging

from mysqlproto.protocol import start_mysql_server
from mysqlproto.protocol.base import OK, ERR, EOF
from mysqlproto.protocol.flags import Capability
from mysqlproto.protocol.handshake import HandshakeV10, HandshakeResponse41, AuthSwitchRequest
from mysqlproto.protocol.query import ColumnDefinition, ColumnDefinitionList, ResultSet


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))


@asyncio.coroutine
def handle_server(server_reader, server_writer):
    handshake = HandshakeV10()
    handshake.write(server_writer)
    yield from server_writer.drain()

    handshake_response = yield from HandshakeResponse41.read(server_reader.packet(), handshake.capability)
    print("<=", handshake_response.__dict__)

    capability = handshake_response.capability_effective

    if (Capability.PLUGIN_AUTH in capability and
            handshake.auth_plugin != handshake_response.auth_plugin):
        AuthSwitchRequest().write(server_writer)
        yield from server_writer.drain()

        auth_response = yield from server_reader.packet().read()
        print("<=", auth_response)

    result = OK(capability, handshake.status)
    result.write(server_writer)
    yield from server_writer.drain()

    while True:
        server_writer.reset()
        packet = server_reader.packet()
        cmd = (yield from packet.read(1))[0]
        print("<=", cmd)

        if cmd == 1:
            return

        elif cmd == 3:
            query = (yield from packet.read()).decode('ascii')
            print("<=   query:", query)

            if query == 'select 1':
                ColumnDefinitionList((ColumnDefinition('database'),)).write(server_writer)
                EOF(capability, handshake.status).write(server_writer)
                ResultSet(('test',)).write(server_writer)
                result = EOF(capability, handshake.status)
            else:
                result = OK(capability, handshake.status)

        else:
            result = ERR(capability)

        result.write(server_writer)
        yield from server_writer.drain()


logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
f = start_mysql_server(handle_server, host=None, port=3306)
loop.run_until_complete(f)
loop.run_forever()
