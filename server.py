import asyncio
import logging

from mysqlproto.protocol import start_mysql_server


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))


@asyncio.coroutine
def handle_server(server_reader, server_writer):
    data = (b'\x0a'+
            b'0alpha\x00' +
            b'\x00\x00\x00\x00' +
            b'\x01'*8 + 
            b'\x00' + 
            b'\x1f\xa2' +
            b'\x21' +
            b'\x00\x00' +
            b'\x00\x00' +
            b'\x00'+
            b'\x00'*10 +
            b'\x01'*12 + b'\x00')
    print("=>", data)
    server_writer.write(0, data)
    yield from server_writer.drain()

    data = yield from server_reader.packet(1).read()
    print("<=", data)

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
