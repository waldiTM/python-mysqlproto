import asyncio
import struct

from .flags import Capability, CapabilitySet, Status, StatusSet, CharacterSet


class HandshakeV10:
    pass


class HandshakeResponse41:
    _packet_1 = struct.Struct('<IIB23x')

    def __init__(self):
        self.capability = CapabilitySet()

    @classmethod
    @asyncio.coroutine
    def read(cls, packet, capability_announced):
        data = yield from packet.read()
        print("<=", repr(data))

        ret = cls()

        d = cls._packet_1.unpack(data[:cls._packet_1.size])
        ret.capability.int = d[0]
        ret.capability_effective = ret.capability & capability_announced
        ret.max_packet_size = d[1]
        ret.character_set = CharacterSet(d[2])

        if not Capability.PROTOCOL_41 in ret.capability:
            raise RuntimeError

        cur = cls._packet_1.size
        end = data.index(b'\x00', cur)
        ret.user = data[cur:end]
        cur = end + 1

        if Capability.PLUGIN_AUTH_LENENC_CLIENT_DATA in ret.capability_effective:
            raise NotImplementedError
        elif Capability.SECURE_CONNECTION in ret.capability_effective:
            i = data[cur]
            end = cur + i + 1
            ret.auth_response = data[cur + 1:end]
            cur = end
        else:
            raise NotImplementedError

        if Capability.CONNECT_WITH_DB in ret.capability_effective:
            end = data.index(b'\x00', cur)
            ret.database = data[cur:end]
            cur = end + 1

        if Capability.PLUGIN_AUTH in ret.capability_effective:
            end = data.index(b'\x00', cur)
            ret.auth_plugin = data[cur:end]
            cur = end + 1

        if Capability.CONNECT_ATTRS in ret.capability_effective:
            raise NotImplementedError

        return ret

