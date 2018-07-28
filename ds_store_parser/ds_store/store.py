# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import binascii
import struct
import biplist
import mac_alias

try:
    next
except NameError:
    next = lambda x: x.next()
try:
    unicode
except NameError:
    unicode = str

from . import buddy

class ILocCodec(object):
    @staticmethod
    def decode(bytesData):
        if isinstance(bytesData, bytearray):
            x, y, z = struct.unpack_from(b'>III', bytes(bytesData[:16]))
        else:
            x, y, z = struct.unpack(b'>III', bytesData[:16])
        h_str = str(bytesData).encode('hex')
        h_array = (
            h_str[:8],
            h_str[8:16],
            h_str[16:24],
            h_str[24:32]
        )
        return (x, y, z, h_array)
        
class DilcCodec(object):
    @staticmethod
    def decode(bytesData):
        if isinstance(bytesData, bytearray):
            u, v, w, x, y, z = struct.unpack_from(b'>IIIIII', bytes(bytesData[:32]))
        else:
            u, v, w, x, y, z = struct.unpack(b'>IIIIII', bytesData[:32])
        h_str = str(bytesData).encode('hex')
        if int(h_str[16:24], 16) > 65535:
            h_pos = "IconPosFromRight: " + str(4294967295 - int(h_str[16:24], 16))
        else:
            h_pos = "IconPosFromLeft: " + str(int(h_str[16:24], 16))
            
        if int(h_str[24:32], 16) > 65535:
            v_pos = "IconPosFromBottom: " + str(4294967295 - int(h_str[24:32], 16))
        else:
            v_pos = "IconPosFromTop: " + str(int(h_str[24:32], 16))
        h_array = (
            "Unk1: "+h_str[:8],
            "GridQuadrant: "+str(int(h_str[8:12],16)),        # short?: Indicates the quadrant on the screen the icon is located. 1=top right, 2=bottom right, 3=bottom left, 4=top left
            "Unk2: "+h_str[12:16],       # short?: Unknown. Values other than 0 have been observed
            h_pos,       # position from right/left of screen. 0xFF indicates right position
            v_pos,       # position from top/bottom of screen. 0xFF indicates bottom position
            "GridIconPosFromLeft: "+str(int(h_str[32:40], 16)),       # position from left
            "GridIconPosFromTop: "+str(int(h_str[40:48], 16)),       # position from top
            "Unk3: "+h_str[48:56],
            "Unk4: "+h_str[56:64]
        )
        return str(h_array).replace("', u'",", ").replace("'","").replace("(u","(")

class PlistCodec(object):
    @staticmethod
    def decode(bytes):
        return biplist.readPlistFromString(bytes)

class BookmarkCodec(object):
    @staticmethod
    def decode(bytes):
        return mac_alias.Bookmark.from_bytes(bytes)

# This list tells the code how to decode particular kinds of entry in the
# .DS_Store file.  This is really a convenience, and we currently only
# support a tiny subset of the possible entry types.
codecs = {
    b'Iloc': ILocCodec,
    b'dilc': DilcCodec,
    b'bwsp': PlistCodec,
    b'lsvp': PlistCodec,
    b'lsvP': PlistCodec,
    b'icvp': PlistCodec,
    b'lsvC': PlistCodec,
    b'pBBk': BookmarkCodec
    }

class DSStoreEntry(object):
    """Holds the data from an entry in a ``.DS_Store`` file.  Note that this is
    not meant to represent the entry itself---i.e. if you change the type
    or value, your changes will *not* be reflected in the underlying file.

    If you want to make a change, you should either use the :class:`DSStore`
    object's :meth:`DSStore.insert` method (which will replace a key if it
    already exists), or the mapping access mode for :class:`DSStore` (often
    simpler anyway).
    """
    def __init__(self, filename, code, typecode, value=None):
        if str != bytes and type(filename) == bytes:
            filename = filename.decode('utf-8')

        if not isinstance(code, bytes):
            code = code.encode('latin_1')

        self.filename = filename
        self.code = code
        self.type = typecode
        self.value = value
        
    @classmethod
    def read(cls, block):
        """Read a ``.DS_Store`` entry from the containing Block"""
        # First read the filename
        nlen = block.read(b'>I')[0]
        filename = block.read(2 * nlen).decode('utf-16be')

        # Next, read the code and type
        code, typecode = block.read(b'>4s4s')

        # Finally, read the data
        if typecode == b'bool':
            value = block.read(b'>?')[0]
        elif typecode == b'long' or typecode == b'shor':
            value = block.read(b'>I')[0]
        elif typecode == b'blob':
            vlen = block.read(b'>I')[0]
            value = block.read(vlen)

            codec = codecs.get(code, None)
            if codec:
                value = codec.decode(value)
                typecode = codec
        elif typecode == b'ustr':
            vlen = block.read(b'>I')[0]
            value = block.read(2 * vlen).decode('utf-16be')
        elif typecode == b'type':
            value = block.read(b'>4s')[0]
        elif typecode == b'comp' or typecode == b'dutc':
            value = block.read(b'>Q')[0]
        else:
            raise ValueError('Unknown type code "%s"' % typecode)

        return DSStoreEntry(filename, code, typecode, value)

    def __lt__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        sfl = self.filename.lower()
        ofl = other.filename.lower()
        return (sfl < ofl
                or (self.filename == other.filename
                    and self.code < other.code))

    def __le__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        sfl = self.filename.lower()
        ofl = other.filename.lower()
        return (sfl < ofl
                or (sfl == ofl
                    and self.code <= other.code))

    def __eq__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        sfl = self.filename.lower()
        ofl = other.filename.lower()
        return (sfl == ofl
                and self.code == other.code)

    def __ne__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        sfl = self.filename.lower()
        ofl = other.filename.lower()
        return (sfl != ofl
                or self.code != other.code)

    def __gt__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        sfl = self.filename.lower()
        ofl = other.filename.lower()
        
        selfCode = self.code
        if str != bytes and type(selfCode) is bytes:
            selfCode = selfCode.decode('utf-8')
        otherCode = other.code
        if str != bytes and type(otherCode) is bytes:
            otherCode = otherCode.decode('utf-8')
        
        return (sfl > ofl or (sfl == ofl and selfCode > otherCode))

    def __ge__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        sfl = self.filename.lower()
        ofl = other.filename.lower()
        return (sfl > ofl
                or (sfl == ofl
                    and self.code >= other.code))

    def __cmp__(self, other):
        if not isinstance(other, DSStoreEntry):
            raise TypeError('Can only compare against other DSStoreEntry objects')
        r = cmp(self.filename.lower(), other.filename.lower())
        if r:
            return r
        return cmp(self.code, other.code)
    
    def byte_length(self):
        """Compute the length of this entry, in bytes"""
        utf16 = self.filename.encode('utf-16be')
        l = 4 + len(utf16) + 8

        if isinstance(self.type, unicode):
            entry_type = self.type.encode('latin_1')
            value = self.value
        elif isinstance(self.type, (bytes, str)):
            entry_type = self.type
            value = self.value
        else:
            entry_type = b'blob'
            value = self.type.encode(self.value)
            
        if entry_type == b'bool':
            l += 1
        elif entry_type == b'long' or entry_type == b'shor':
            l += 4
        elif entry_type == b'blob':
            l += 4 + len(value)
        elif entry_type == b'ustr':
            utf16 = value.encode('utf-16be')
            l += 4 + len(utf16)
        elif entry_type == b'type':
            l += 4
        elif entry_type == b'comp' or entry_type == b'dutc':
            l += 8
        else:
            raise ValueError('Unknown type code "%s"' % entry_type)

        return l
    
    def __repr__(self):
        return '<%s %s>' % (self.filename, self.code)

class DSStore(object):
    """Python interface to a ``.DS_Store`` file.  Works by manipulating the file
    on the disk---so this code will work with ``.DS_Store`` files for *very*
    large directories.

    A :class:`DSStore` object can be used as if it was a mapping, e.g.::

      d['foobar.dat']['Iloc']

    will fetch the "Iloc" record for "foobar.dat", or raise :class:`KeyError` if
    there is no such record.  If used in this manner, the :class:`DSStore` object
    will return (type, value) tuples, unless the type is "blob" and the module
    knows how to decode it.

    Currently, we know how to decode "Iloc", "bwsp", "lsvp", "lsvP" and "icvp"
    blobs.  "Iloc" decodes to an (x, y) tuple, while the others are all decoded
    using ``biplist``.

    Assignment also works, e.g.::

      d['foobar.dat']['note'] = ('ustr', u'Hello World!')

    as does deletion with ``del``::

      del d['foobar.dat']['note']

    This is usually going to be the most convenient interface, though
    occasionally (for instance when creating a new ``.DS_Store`` file) you
    may wish to drop down to using :class:`DSStoreEntry` objects directly."""
    def __init__(self, store):
        self._store = store
        self._superblk = self._store['DSDB']
        with self._get_block(self._superblk) as s:
            self._rootnode, self._levels, self._records, \
            self._nodes, self._page_size = s.read(b'>IIIII')
        self._min_usage = 2 * self._page_size // 3
        self._dirty = False
        
    @classmethod
    def open(cls, file_or_name, mode='r+', initial_entries=None):
        """Open a ``.DS_Store`` file; pass either a Python file object, or a
        filename in the ``file_or_name`` argument and a file access mode in
        the ``mode`` argument.  If you are creating a new file using the "w"
        or "w+" modes, you may also specify a list of entries with which
        to initialise the file."""
        store = buddy.Allocator.open(file_or_name, mode)
                
        return DSStore(store)

    def _get_block(self, number):
        return self._store.get_block(number)

    def flush(self):
        """Flush any dirty data back to the file."""
        if self._dirty:
            self._dirty = False

            with self._get_block(self._superblk) as s:
                s.write(b'>IIIII', self._rootnode, self._levels, self._records,
                        self._nodes, self._page_size)
        self._store.flush()

    def close(self):
        """Flush dirty data and close the underlying file."""
        self.flush()
        self._store.close()
        
    def __enter__(self):
        return self

    # Iterate over the tree, starting at `node'
    def _traverse(self, node):
        if node is None:
            node = self._rootnode
        with self._get_block(node) as block:
            next_node, count = block.read(b'>II')
            if next_node:
                for n in range(count):
                    ptr = block.read(b'>I')[0]
                    for e in self._traverse(ptr):
                        yield e
                    e = DSStoreEntry.read(block)
                    yield e
                for e in self._traverse(next_node):
                    yield e
            else:
                for n in range(count):
                    e = DSStoreEntry.read(block)
                    yield e
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        
    def __len__(self):
        return self._records

    def __iter__(self):
        return self._traverse(self._rootnode)

    class Partial(object):
        """This is used to implement indexing."""
        def __init__(self, store, filename):
            self._store = store
            self._filename = filename

        def __getitem__(self, code):
            if code is None:
                raise KeyError('no such key - [%s][None]' % self._filename)

            if not isinstance(code, bytes):
                code = code.encode('latin_1')

            try:
                item = next(self._store.find(self._filename, code))
            except StopIteration:
                raise KeyError('no such key - [%s][%s]' % (self._filename,
                               code))

            if not isinstance(item.type, (bytes, str, unicode)):
                return item.value
            
            return (item.type, item.value)
            
        def __setitem__(self, code, value):
            if code is None:
                raise KeyError('bad key - [%s][None]' % self._filename)

            if not isinstance(code, bytes):
                code = code.encode('latin_1')

            codec = codecs.get(code, None)
            if codec:
                entry_type = codec
                entry_value = value
            else:
                entry_type = value[0]
                entry_value = value[1]
            
            self._store.insert(DSStoreEntry(self._filename, code,
                                             entry_type, entry_value))

        def __delitem__(self, code):
            if code is None:
                raise KeyError('no such key - [%s][None]' % self._filename)

            self._store.delete(self._filename, code)

        def __iter__(self):
            for item in self._store.find(self._filename):
                yield item

    def __getitem__(self, filename):
        return self.Partial(self, filename)
    
