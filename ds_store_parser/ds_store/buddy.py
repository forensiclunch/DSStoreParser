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
        
    def zero_fill(self):
        len = self._size - self._pos
        zeroes = b'\0' * len
        self._value[self._pos:self._size] = zeroes
        self._dirty = True
        
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

    def flush(self):
        if self._dirty:
            size = self._root_block_size()
            self.allocate(size, 0)
            with self.get_block(0) as rblk:
                self._write_root_block_into(rblk)

            addr = self._offsets[0]
            offset = addr & ~0x1f
            size = 1 << (addr & 0x1f)

            self._file.seek(0, os.SEEK_SET)
            self._file.write(struct.pack(b'>I4sIII16s',
                                         1, b'Bud1',
                                         offset, size, offset,
                                         self._unknown1))

            self._dirty = False
            
        self._file.flush()
            
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

    def write(self, offset, data_or_format, *args):
        """Write data at `offset', or raise an exception.  `data_or_format'
           may either be the data to write, or a format string for `struct.pack',
           in which case we pack the additional arguments and write the
           resulting data."""
        # N.B. There is a fixed offset of four bytes(!)
        self._file.seek(offset + 4, os.SEEK_SET)

        if len(args):
            data = struct.pack(data_or_format, *args)
        else:
            data = data_or_format

        self._file.write(data)

    def get_block(self, block):
        try:
            addr = self._offsets[block]
        except IndexError:
            return None

        offset = addr & ~0x1f
        size = 1 << (addr & 0x1f)

        return Block(self, offset, size)
    
    def _root_block_size(self):
        """Return the number of bytes required by the root block."""
        # Offsets
        size = 8
        size += 4 * ((len(self._offsets) + 255) & ~255)

        # TOC
        size += 4
        size += sum([5 + len(s) for s in self._toc])

        # Free list
        size += sum([4 + 4 * len(fl) for fl in self._free])
        
        return size

    def _write_root_block_into(self, block):
        # Offsets
        block.write('>II', len(self._offsets), self._unknown2)
        block.write('>%uI' % len(self._offsets), *self._offsets)
        extra = len(self._offsets) & 255
        if extra:
            block.write(b'\0\0\0\0' * (256 - extra))

        # TOC
        keys = list(self._toc.keys())
        keys.sort()

        block.write('>I', len(keys))
        for k in keys:
            block.write('B', len(k))
            block.write(k)
            block.write('>I', self._toc[k])

        # Free list
        for w, f in enumerate(self._free):
            block.write('>I', len(f))
            if len(f):
                block.write('>%uI' % len(f), *f)

    def _buddy(self, offset, width):
        f = self._free[width]
        b = offset ^ (1 << width)
        
        try:
            ndx = f.index(b)
        except ValueError:
            ndx = None
            
        return (f, b, ndx)

    def _release(self, offset, width):
        # Coalesce
        while True:
            f,b,ndx = self._buddy(offset, width)

            if ndx is None:
                break
            
            offset &= b
            width += 1
            del f[ndx]
            
        # Add to the list
        bisect.insort(f, offset)

        # Mark as dirty
        self._dirty = True
    
    def _alloc(self, width):
        w = width
        while not self._free[w]:
            w += 1
        while w > width:
            offset = self._free[w].pop(0)
            w -= 1
            self._free[w] = [offset, offset ^ (1 << w)]
        self._dirty = True
        return self._free[width].pop(0)

    def allocate(self, bytes, block=None):
        """Allocate or reallocate a block such that it has space for at least
        `bytes' bytes."""
        if block is None:
            # Find the first unused block
            try:
                block = self._offsets.index(0)
            except ValueError:
                block = len(self._offsets)
                self._offsets.append(0)
        
        # Compute block width
        width = max(bytes.bit_length(), 5)

        addr = self._offsets[block]
        offset = addr & ~0x1f
        
        if addr:
            blkwidth = addr & 0x1f
            if blkwidth == width:
                return block
            self._release(offset, width)
            self._offsets[block] = 0

        offset = self._alloc(width)
        self._offsets[block] = offset | width
        return block
    
    def release(self, block):
        addr = self._offsets[block]

        if addr:
            width = addr & 0x1f
            offset = addr & ~0x1f
            self._release(offset, width)

        if block == len(self._offsets):
            del self._offsets[block]
        else:
            self._offsets[block] = 0

    def __len__(self):
        return len(self._toc)

    def __getitem__(self, key):
        if not isinstance(key, (str, unicode)):
            raise TypeError('Keys must be of string type')
        if not isinstance(key, bytes):
            key = key.encode('latin_1')
        return self._toc[key]

    def __setitem__(self, key, value):
        if not isinstance(key, (str, unicode)):
            raise TypeError('Keys must be of string type')
        if not isinstance(key, bytes):
            key = key.encode('latin_1')
        self._toc[key] = value
        self._dirty = True

    def __delitem__(self, key):
        if not isinstance(key, (str, unicode)):
            raise TypeError('Keys must be of string type')
        if not isinstance(key, bytes):
            key = key.encode('latin_1')
        del self._toc[key]
        self._dirty = True

    def iterkeys(self):
        return iterkeys(self._toc)

    def keys(self):
        return iterkeys(self._toc)

    def __iter__(self):
        return iterkeys(self._toc)

    def __contains__(self, key):
        return key in self._toc

