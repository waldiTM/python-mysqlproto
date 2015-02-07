import asyncio
import struct


class MysqlPacketReader:
    __slots__ = '_stream', '__length', '__seq_next', '__follow'

    def __init__(self, stream, seq):
        self._stream = stream
        self.__length = 0
        self.__seq_next = seq
        self.__follow = True

    def _check_lead(self, ldata):
        if not ldata or len(ldata) != 4:
            raise RuntimeError

        l1, l2, seq = struct.unpack("<HBB", ldata)
        l = l1 + (l2 << 16)

        if seq != self.__seq_next:
            raise RuntimeError('Wrong sequence, expected {}, got {}'.format(self.__seq_next, seq))

        self.__length = l
        self.__seq_next += 1
        if l < 0xffffff:
            self.__follow = False

    @asyncio.coroutine
    def read(self, size=None):
        if not self.__length:
            if self.__follow:
                ldata = yield from self._stream.read(4)
                self._check_lead(ldata)
            else:
                return ''

        if not size or size >= self.__length:
            size = self.__length

        data = yield from self._stream.read(size)
        self.__length -= len(data)
        return data


class MysqlStreamReader:
    __slots__ = '_inner'

    def __init__(self, inner):
        self._inner = inner

    def packet(self, seq):
        return MysqlPacketReader(self._inner, seq)


class MysqlStreamWriter:
    def __init__(self, inner):
        self._inner = inner
        self._seq = 0

    def close(self):
        self._inner.close()

    @asyncio.coroutine
    def drain(self):
        return self._inner.drain()

    def write(self, data, seq=None):
        l = len(data)
        if l >= 0xffff:
            raise NotImplementedError

        if seq is None:
            seq = self._seq

        ldata = struct.pack("<HBB", l, 0, seq)
        print("=> seq", seq)
        self._inner.write(ldata)
        self._inner.write(data)

        self._seq = (seq + 1) & 0xff



@asyncio.coroutine
def start_mysql_server(client_connected_cb, host=None, port=None, **kwds):
    @asyncio.coroutine
    def cb(reader, writer):
        reader_m = MysqlStreamReader(reader)
        writer_m = MysqlStreamWriter(writer)
        return client_connected_cb(reader_m, writer_m)

    return asyncio.start_server(cb, host, port, **kwds)
