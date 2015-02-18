import asyncio
import struct

from .types import IntLengthEncoded, StringLengthEncoded


class ColumnDefinition:
    def __init__(self, name):
        self.name = name

    def write(self, stream):
        packet = [
            StringLengthEncoded.write(b'def'),
            StringLengthEncoded.write(b''),
            StringLengthEncoded.write(b''),
            StringLengthEncoded.write(b''),
            StringLengthEncoded.write(self.name.encode('ascii')),
            StringLengthEncoded.write(self.name.encode('ascii')),
            b'\x0c',
            b'\x21\x00',
            b'\x10\x00\x00\x00',
            b'\x0f',
            b'\x00\x00',
            b'\x00',
            b'\x00'*2,
        ]

        p = b''.join(packet)
        stream.write(p)


class ColumnDefinitionList:
    def __init__(self, columns=None):
        self.columns = columns or []

    def write(self, stream):
        p = IntLengthEncoded.write(len(self.columns))

        stream.write(p)

        for i in self.columns:
            i.write(stream)


class ResultSet:
    def __init__(self, values):
        self.values = values

    def write(self, stream):
        s = StringLengthEncoded.write

        packet = []

        for i in self.values:
            if i is None:
                packet.append(b'\xfb')
            else:
                packet.append(s(str(i).encode('ascii')))

        p = b''.join(packet)
        stream.write(p)
