# -*- coding: utf-8 -*-
import os
import bisect
import struct
import binascii

try:
    {}.iterkeys
    iterkeys = lambda x: x.iterkeys()
except AttributeError:
    iterkeys = lambda x: x.keys()
try:
    unicode
except NameError:
    unicode = str

class BuddyError(Exception):
    pass

class Block(object):
    def __init__(self, allocator, offset, size):
        self._allocator = allocator
        self._offset = offset
        self._size = size
        self._value = bytearray(allocator.read(offset, size))
        self._pos = 0
        self._dirty = False
        
    def __len__(self):
        return self._size

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    def close(self):
        if self._dirty:
            self.flush()

    def flush(self):
        if self._dirty:
            self._dirty = False
            self._allocator.write(self._offset, self._value)

    def invalidate(self):
        self._dirty = False
        
    def tell(self):
        return self._pos

    def seek(self, pos, whence=os.SEEK_SET):
        if whence == os.SEEK_CUR:
            pos += self._pos
        elif whence == os.SEEK_END:
            pos = self._size - pos

        if pos < 0 or pos > self._size:
            raise ValueError('Seek out of range in Block instance')

        self._pos = pos

    def read(self, size_or_format):
        if isinstance(size_or_format, (str, unicode, bytes)):
            size = struct.calcsize(size_or_format)
            fmt = size_or_format
        else:
            size = size_or_format
            fmt = None

        if self._size - self._pos < size:
            raise BuddyError('Unable to read %lu bytes in block' % size)

        data = self._value[self._pos:self._pos + size]
        self._pos += size
        
        if fmt is not None:
            if isinstance(data, bytearray):
                return struct.unpack_from(fmt, bytes(data))
            else:
                return struct.unpack(fmt, data)
        else:
            return data
        
    def __str__(self):
        return binascii.b2a_hex(self._value)
        
class Allocator(object):
    def __init__(self, the_file):
        self._file = the_file
        self._dirty = False

        self._file.seek(0)
        
        # Read the header
        magic1, magic2, offset, size, offset2, self._unknown1 \
          = self.read(-4, '>I4sIII16s')

        if magic2 != b'Bud1' or magic1 != 1:
            raise BuddyError('Not a buddy file')

        if offset != offset2:
            raise BuddyError('Root addresses differ')

        self._root = Block(self, offset, size)

        # Read the block offsets
        count, self._unknown2 = self._root.read('>II')
        self._offsets = []
        c = (count + 255) & ~255
        while c:
            self._offsets += self._root.read('>256I')
            c -= 256
        self._offsets = self._offsets[:count]
        
        # Read the TOC
        self._toc = {}
        count = self._root.read('>I')[0]
        for n in range(count):
            nlen = self._root.read('B')[0]
            name = bytes(self._root.read(nlen))
            value = self._root.read('>I')[0]
            self._toc[name] = value

        # Read the free lists
        self._free = []
        for n in range(32):
            count = self._root.read('>I')
            self._free.append(list(self._root.read('>%uI' % count)))
        
    @classmethod
    def open(cls, file_or_name, mode='r+'):
        if isinstance(file_or_name, (str, unicode)):
            if not 'b' in mode:
                mode = mode[:1] + 'b' + mode[1:]
            f = open(file_or_name, mode)
        else:
            f = file_or_name

        return Allocator(f)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    def close(self):
        self.flush()
        self._file.close()
            
    def read(self, offset, size_or_format):
        """Read data at `offset', or raise an exception.  `size_or_format'
           may either be a byte count, in which case we return raw data,
           or a format string for `struct.unpack', in which case we
           work out the size and unpack the data before returning it."""
        # N.B. There is a fixed offset of four bytes(!)
        self._file.seek(offset + 4, os.SEEK_SET)

        if isinstance(size_or_format, (str, unicode)):
            size = struct.calcsize(size_or_format)
            fmt = size_or_format
        else:
            size = size_or_format
            fmt = None
        
        ret = self._file.read(size)
        if len(ret) < size:
            ret += b'\0' * (size - len(ret))

        if fmt is not None:
            if isinstance(ret, bytearray):
                ret = struct.unpack_from(fmt, bytes(ret))
            else:
                ret = struct.unpack(fmt, ret)
            
        return ret

    def get_block(self, block):
        try:
            addr = self._offsets[block]
        except IndexError:
            return None

        offset = addr & ~0x1f
        size = 1 << (addr & 0x1f)

        return Block(self, offset, size)


    def __len__(self):
        return len(self._toc)

    def __getitem__(self, key):
        if not isinstance(key, (str, unicode)):
            raise TypeError('Keys must be of string type')
        if not isinstance(key, bytes):
            key = key.encode('latin_1')
        return self._toc[key]

    def iterkeys(self):
        return iterkeys(self._toc)

    def keys(self):
        return iterkeys(self._toc)

    def __iter__(self):
        return iterkeys(self._toc)

    def __contains__(self, key):
        return key in self._toc

