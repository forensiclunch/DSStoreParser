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

class IlocCodec(object):
    @staticmethod
    def decode(bytesData):
        if isinstance(bytesData, bytearray):
            x, y, z = struct.unpack_from(b'>III', bytes(bytesData[:16]))
        else:
            x, y, z = struct.unpack(b'>III', bytesData[:16])
            
        h_str = str(bytesData).encode('hex')
        
        r_value_hor = x
        r_value_ver = y
        r_value_idx = z
        if r_value_hor == 4294967295L:
            r_value_hor = u"Null"
        if r_value_ver == 4294967295L:
            r_value_ver = u"Null"
        if r_value_idx == 4294967295L:
            r_value_idx = u"Null"

        val = "Location: ({0}, {1}), Selected Index: {2}, Unknown: {3}".format(
            unicode(r_value_hor), 
            unicode(r_value_ver), 
            unicode(r_value_idx),
            h_str[24:32]
        )

        return val

class IcvoCodec(object):
    @staticmethod
    def decode(bytesData):
        h_str = str(bytesData).encode('hex')
        i_type = h_str[:8].decode('hex')
        p_size = str(int(h_str[8:12], 16))
        g_align = h_str[12:20].decode('hex')
        g_align_loc = h_str[20:28].decode('hex')
        unknown = str(h_str[28:])
        
        val = "Type: {0}, IconPixelSize: {1}, GridAlign: {2}, GridAlignTo: {3}, Unknown: {4}".format(
            i_type,
            p_size,
            g_align,
            g_align_loc,
            unknown
        )
        
        return val
        
class Fwi0Codec(object):
    @staticmethod
    def decode(bytesData):
        if isinstance(bytesData, bytearray):
            w, x, y, z = struct.unpack_from(b'>HHHH', bytes(bytesData[:16]))
        else:
            w, x, y, z = struct.unpack(b'>HHHH', bytesData[:16])
            
        h_str = str(bytesData).encode('hex')
        
        h_array = (
            'top: ' + str(w),
            'left: ' + str(x),
            'bottom: ' + str(y),
            'right: ' + str(z),
            'view_type: ' + h_str[16:24].decode('hex'),
            'Unknown: ' + h_str[24:32]
        )
        
        val = str(h_array).replace("', u'",", ").replace("'","").replace("(u","(")
        
        return val
        
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
        
        val = str(h_array).replace("', u'",", ").replace("'","").replace("(u","(")
        
        return val

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
    b'Iloc': IlocCodec,
    b'icvo': IcvoCodec,
    b'fwi0': Fwi0Codec,
    b'dilc': DilcCodec,
    b'bwsp': PlistCodec,
    b'lsvp': PlistCodec,
    b'glvp': PlistCodec,
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

    def __iter__(self):
        return self._traverse(self._rootnode)
    
