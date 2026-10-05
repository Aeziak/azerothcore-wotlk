"""Minimal MPQ (v1) reader/writer for the WoW 3.3.5a client.

Reading supports the formats used by the stock 3.3.5a archives for text and DBC files:
zlib, bzip2 and PKWARE-imploded sectors, encrypted files and single-unit files.
Writing produces a plain v1 archive (zlib-compressed files, encrypted tables, (listfile)).
"""

import bz2
import struct
import zlib

_CRYPT = []


def _build_crypt_table():
    seed = 0x00100001
    table = [0] * 0x500
    for index1 in range(0x100):
        index2 = index1
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp1 = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp2 = seed & 0xFFFF
            table[index2] = temp1 | temp2
            index2 += 0x100
    return table


_CRYPT = _build_crypt_table()

HASH_TABLE_OFFSET = 0
HASH_NAME_A = 1
HASH_NAME_B = 2
HASH_FILE_KEY = 3

FLAG_IMPLODE = 0x00000100
FLAG_COMPRESS = 0x00000200
FLAG_ENCRYPTED = 0x00010000
FLAG_FIX_KEY = 0x00020000
FLAG_SINGLE_UNIT = 0x01000000
FLAG_SECTOR_CRC = 0x04000000
FLAG_EXISTS = 0x80000000


def hash_string(name, hash_type):
    seed1 = 0x7FED7FED
    seed2 = 0xEEEEEEEE
    for ch in name.upper().replace("/", "\\"):
        value = ord(ch)
        seed1 = _CRYPT[(hash_type << 8) + value] ^ ((seed1 + seed2) & 0xFFFFFFFF)
        seed2 = (value + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def _crypt(data, key, decrypt):
    count = len(data) // 4
    values = list(struct.unpack("<%dI" % count, data[:count * 4]))
    seed = 0xEEEEEEEE
    for i in range(count):
        seed = (seed + _CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        if decrypt:
            values[i] ^= (key + seed) & 0xFFFFFFFF
            plain = values[i]
        else:
            plain = values[i]
            values[i] ^= (key + seed) & 0xFFFFFFFF
        key = ((((~key) << 0x15) + 0x11111111) & 0xFFFFFFFF) | (key >> 0x0B)
        seed = (plain + seed + (seed << 5) + 3) & 0xFFFFFFFF
    return struct.pack("<%dI" % count, *values) + data[count * 4:]


def decrypt(data, key):
    return _crypt(data, key, True)


def encrypt(data, key):
    return _crypt(data, key, False)


def _file_key(name, block_offset, file_size, flags):
    key = hash_string(name.replace("/", "\\").split("\\")[-1], HASH_FILE_KEY)
    if flags & FLAG_FIX_KEY:
        key = ((key + block_offset) ^ file_size) & 0xFFFFFFFF
    return key


# --- PKWARE Data Compression Library "explode" (port of zlib's contrib/blast) ---

def _construct(lengths):
    count = [0] * 16
    for length in lengths:
        count[length] += 1
    offs = [0] * 16
    for i in range(1, 16):
        offs[i] = offs[i - 1] + count[i - 1]
    symbol = [0] * len(lengths)
    for sym, length in enumerate(lengths):
        if length:
            symbol[offs[length]] = sym
            offs[length] += 1
    return count, symbol


def _expand(rep):
    lengths = []
    for byte in rep:
        lengths += [(byte & 15) + 1] * ((byte >> 4) + 1)
    return _construct(lengths)


_LIT = _expand([11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8, 9, 7, 6, 7, 8, 7, 6, 55, 8,
                23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5, 7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8,
                11, 9, 12, 8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27, 44, 253, 253, 253,
                252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45, 44, 173])
_LEN = _expand([2, 35, 36, 53, 38, 23])
_DIST = _expand([2, 20, 53, 230, 247, 151, 248])
_BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]


def explode(data):
    pos = 0
    bitbuf = 0
    bitcnt = 0

    def bits(need):
        nonlocal pos, bitbuf, bitcnt
        val = bitbuf
        while bitcnt < need:
            val |= data[pos] << bitcnt
            pos += 1
            bitcnt += 8
        bitbuf = val >> need
        bitcnt -= need
        return val & ((1 << need) - 1)

    def decode(table):
        count, symbol = table
        code = first = index = 0
        for length in range(1, 16):
            code |= bits(1) ^ 1
            cnt = count[length]
            if code < first + cnt:
                return symbol[index + (code - first)]
            index += cnt
            first = (first + cnt) << 1
            code <<= 1
        raise ValueError("bad PKWARE code")

    lit = bits(8)
    dictbits = bits(8)
    out = bytearray()
    while True:
        if bits(1):
            symbol = decode(_LEN)
            length = _BASE[symbol] + bits(_EXTRA[symbol])
            if length == 519:
                break
            symbol = 2 if length == 2 else dictbits
            dist = (decode(_DIST) << symbol) + bits(symbol) + 1
            for _ in range(length):
                out.append(out[-dist])
        else:
            out.append(decode(_LIT) if lit else bits(8))
    return bytes(out)


def _decompress(data, expected):
    if len(data) >= expected:
        return data[:expected]
    mask = data[0]
    payload = data[1:]
    if mask == 0x02:
        return zlib.decompress(payload)
    if mask == 0x10:
        return bz2.decompress(payload)
    if mask == 0x08:
        return explode(payload)
    raise ValueError("unsupported MPQ compression 0x%02X" % mask)


class MpqArchive:
    def __init__(self, path):
        with open(path, "rb") as handle:
            self.data = handle.read()
        self.base = self.data.find(b"MPQ\x1a")
        while self.base >= 0 and self.base % 512:
            self.base = self.data.find(b"MPQ\x1a", self.base + 1)
        if self.base < 0:
            raise ValueError("not an MPQ archive: %s" % path)
        (_, _, _, _, sector_shift, hash_pos, block_pos, hash_count,
         block_count) = struct.unpack_from("<4sIIHHIIII", self.data, self.base)
        self.sector_size = 512 << sector_shift
        self.hash_table = self._table(hash_pos, hash_count, "(hash table)")
        self.block_table = self._table(block_pos, block_count, "(block table)")

    def _table(self, offset, count, name):
        raw = self.data[self.base + offset:self.base + offset + count * 16]
        raw = decrypt(raw, hash_string(name, HASH_FILE_KEY))
        return [struct.unpack_from("<IIII", raw, i * 16) for i in range(count)]

    def _find(self, name):
        count = len(self.hash_table)
        start = hash_string(name, HASH_TABLE_OFFSET) % count
        name_a = hash_string(name, HASH_NAME_A)
        name_b = hash_string(name, HASH_NAME_B)
        for i in range(count):
            entry = self.hash_table[(start + i) % count]
            if entry[3] == 0xFFFFFFFF:
                return None
            if entry[0] == name_a and entry[1] == name_b and entry[3] != 0xFFFFFFFE:
                return self.block_table[entry[3]]
        return None

    def has(self, name):
        block = self._find(name)
        return block is not None and block[3] & FLAG_EXISTS

    def read(self, name):
        block = self._find(name)
        if not block or not block[3] & FLAG_EXISTS:
            return None
        offset, packed, size, flags = block
        raw = self.data[self.base + offset:self.base + offset + packed]
        key = _file_key(name, offset, size, flags) if flags & FLAG_ENCRYPTED else None
        if flags & FLAG_SINGLE_UNIT:
            if key is not None:
                raw = decrypt(raw, key)
            if flags & FLAG_COMPRESS:
                return _decompress(raw, size)
            if flags & FLAG_IMPLODE and packed < size:
                return explode(raw)
            return raw[:size]
        if not flags & (FLAG_COMPRESS | FLAG_IMPLODE):
            out = bytearray()
            for index, start in enumerate(range(0, size, self.sector_size)):
                chunk = raw[start:start + self.sector_size]
                out += decrypt(chunk, (key + index) & 0xFFFFFFFF) if key is not None else chunk
            return bytes(out[:size])
        sectors = (size + self.sector_size - 1) // self.sector_size
        entries = sectors + 1 + (1 if flags & FLAG_SECTOR_CRC else 0)
        table = raw[:entries * 4]
        if key is not None:
            table = decrypt(table, (key - 1) & 0xFFFFFFFF)
        offsets = struct.unpack("<%dI" % entries, table)
        out = bytearray()
        for index in range(sectors):
            chunk = raw[offsets[index]:offsets[index + 1]]
            if key is not None:
                chunk = decrypt(chunk, (key + index) & 0xFFFFFFFF)
            expected = min(self.sector_size, size - index * self.sector_size)
            if flags & FLAG_COMPRESS:
                out += _decompress(chunk, expected)
            elif len(chunk) < expected:
                out += explode(chunk)
            else:
                out += chunk
        return bytes(out)


def read_from_chain(archives, name):
    """Return the file from the highest-priority archive (last in the list) that has it."""
    for archive in reversed(archives):
        content = archive.read(name)
        if content is not None:
            return content
    return None


def write_archive(path, files):
    """Write a v1 MPQ. `files` maps archive paths (backslash separated) to bytes."""
    files = dict(files)
    files["(listfile)"] = "\r\n".join(sorted(files)).encode("ascii") + b"\r\n"
    names = sorted(files)
    hash_count = 16
    while hash_count < len(names) * 2:
        hash_count *= 2
    sector_size = 4096
    body = bytearray()
    blocks = []
    header_size = 32
    for name in names:
        content = files[name]
        offset = header_size + len(body)
        sectors = max(1, (len(content) + sector_size - 1) // sector_size)
        chunks = []
        for index in range(sectors):
            plain = content[index * sector_size:(index + 1) * sector_size]
            packed = b"\x02" + zlib.compress(plain, 9)
            chunks.append(packed if len(packed) < len(plain) else plain)
        table_size = (sectors + 1) * 4
        positions = [table_size]
        for chunk in chunks:
            positions.append(positions[-1] + len(chunk))
        data = struct.pack("<%dI" % len(positions), *positions) + b"".join(chunks)
        body += data
        blocks.append((offset, len(data), len(content), FLAG_EXISTS | FLAG_COMPRESS))
    hash_table = [(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)] * hash_count
    for block_index, name in enumerate(names):
        slot = hash_string(name, HASH_TABLE_OFFSET) % hash_count
        while hash_table[slot][3] != 0xFFFFFFFF:
            slot = (slot + 1) % hash_count
        hash_table[slot] = (hash_string(name, HASH_NAME_A), hash_string(name, HASH_NAME_B), 0, block_index)
    raw_hash = b"".join(struct.pack("<IIHHI", a, b, 0, 0, idx) if idx != 0xFFFFFFFF
                        else struct.pack("<IIII", a, b, 0xFFFFFFFF, idx) for a, b, _, idx in hash_table)
    raw_block = b"".join(struct.pack("<IIII", *block) for block in blocks)
    hash_pos = header_size + len(body)
    block_pos = hash_pos + len(raw_hash)
    archive_size = block_pos + len(raw_block)
    header = struct.pack("<4sIIHHIIII", b"MPQ\x1a", header_size, archive_size, 0, (sector_size // 512).bit_length() - 1,
                         hash_pos, block_pos, hash_count, len(blocks))
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(body)
        handle.write(encrypt(raw_hash, hash_string("(hash table)", HASH_FILE_KEY)))
        handle.write(encrypt(raw_block, hash_string("(block table)", HASH_FILE_KEY)))
