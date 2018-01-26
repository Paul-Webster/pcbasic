"""
PC-BASIC - font.py
Font handling

(c) 2014--2018 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import os
import logging

try:
    import numpy
except ImportError:
    numpy = None


DEFAULT_FONT = {
    '\x00': '\x00\x00\x00\x00\x00\x00\x00\x00', '\x83': '8l\x00x\x0c|\xccv', '\x04': '\x108|\xfe|8\x10\x00', '\x87': '\x00|\xc6\xc0\xc6|\x18p', '\x08': '\xff\xff\xe7\xc3\xc3\xe7\xff\xff', '\x8b': '\x00f\x008\x18\x18\x18<', '\x0c': '<fff<\x18~\x18', '\x8f': '8l8|\xc6\xfe\xc6\xc6', '\x10': '\x80\xe0\xf8\xfe\xf8\xe0\x80\x00', '\x93': '8l\x00|\xc6\xc6\xc6|', '\x14': '\x7f\xdb\xdb{\x1b\x1b\x1b\x00', '\x97': '`0\x00\xcc\xcc\xcc\xccv', '\x18': '\x18<~\x18\x18\x18\x18\x00', '\x9b': '\x18\x18~\xc0\xc0~\x18\x18', '\x1c': '\x00\x00\xc0\xc0\xc0\xfe\x00\x00', '\x9f': '\x0e\x1b\x18<\x18\x18\xd8p', ' ': '\x00\x00\x00\x00\x00\x00\x00\x00', '\xa3': '\x180\x00\xcc\xcc\xcc\xccv', '$': '\x00\x18>`<\x06|\x18', '\xa7': '\x008ll8\x00|\x00', '(': '\x00\x0c\x18000\x18\x0c', '\xab': 'c\xe6l~3f\xcc\x0f', ',': '\x00\x00\x00\x00\x00\x18\x180', '\xaf': '\x00\x00\x00\xccf3f\xcc', '0': '\x008l\xc6\xd6\xc6l8', '\xb3': '\x18\x18\x18\x18\x18\x18\x18\x18', '4': '\x00\x1c<l\xcc\xfe\x0c\x1e', '\xb7': '\x00\x00\x00\x00\xfe666', '8': '\x00|\xc6\xc6|\xc6\xc6|', '\xbb': '\x00\x00\xfe\x06\xf6666', '<': '\x00\x06\x0c\x180\x18\x0c\x06', '\xbf': '\x00\x00\x00\x00\xf8\x18\x18\x18', '@': '\x00|\xc6\xde\xde\xde\xc0x', '\xc3': '\x18\x18\x18\x18\x1f\x18\x18\x18', 'D': '\x00\xf8lfffl\xf8', '\xc7': '66667666', 'H': '\x00\xc6\xc6\xc6\xfe\xc6\xc6\xc6', '\xcb': '\x00\x00\xff\x00\xf7666', 'L': '\x00\xf0```bf\xfe', '\xcf': '\x18\x18\xff\x00\xff\x00\x00\x00', 'P': '\x00\xfcff|``\xf0', '\xd3': '6666?\x00\x00\x00', 'T': '\x00~~Z\x18\x18\x18<', '\xd7': '6666\xff666', 'X': '\x00\xc6\xc6l8l\xc6\xc6', '\xdb': '\xff\xff\xff\xff\xff\xff\xff\xff', '\\': '\x00\xc0`0\x18\x0c\x06\x02', '\xdf': '\xff\xff\xff\xff\x00\x00\x00\x00', '`': '0\x18\x0c\x00\x00\x00\x00\x00', '\xe3': '\x00\x00\x00\xfellll', 'd': '\x00\x1c\x0c|\xcc\xcc\xccv', '\xe7': '\x00\x00\x00\xfe006\x1c', 'h': '\x00\xe0`lvff\xe6', '\xeb': '\x00<`8|\xc6\xc6|', 'l': '\x008\x18\x18\x18\x18\x18<', '\xef': '\x00|\xc6\xc6\xc6\xc6\xc6\x00', 'p': '\x00\x00\x00\xdcf|`\xf0', '\xf3': '\x00\x0c\x180\x18\x0c\x00~', 't': '\x0000\xfc006\x1c', '\xf7': '\x00\x00v\xdc\x00v\xdc\x00', 'x': '\x00\x00\x00\xc6l8l\xc6', '\xfb': '\x0f\x0c\x0c\x0c\xecl<\x1c', '|': '\x00\x18\x18\x18\x18\x18\x18\x18', '\xff': '\x00\x00\x00\x00\x00\x00\x00\x00', '\x80': '<f\xc0\xc0f<\x18p', '\x03': 'l\xfe\xfe\xfe|8\x10\x00', '\x84': '\x00\xcc\x00x\x0c|\xccv', '\x07': '\x00\x00\x18<<\x18\x00\x00', '\x88': '8l\x00|\xc6\xfe\xc0|', '\x0b': '\x0f\x07\x0f}\xcc\xcc\xccx', '\x8c': '8l\x008\x18\x18\x18<', '\x0f': '\x18\xdb<\xe7\xe7<\xdb\x18', '\x90': '\x0c\x18\xfe\xc0\xf8\xc0\xc0\xfe', '\x13': 'fffff\x00f\x00', '\x94': '\x00\xc6\x00|\xc6\xc6\xc6|', '\x17': '\x18<~\x18~<\x18\xff', '\x98': '\x00\xc6\x00\xc6\xc6~\x06\xfc', '\x1b': '\x000`\xfe`0\x00\x00', '\x9c': '8ld\xf0``f\xfc', '\x1f': '\x00\xff\xff~<\x18\x00\x00', '\xa0': '\x180\x00x\x0c|\xccv', '#': '\x00ll\xfel\xfell', '\xa4': 'v\xdc\x00\xdcffff', "'": '\x00\x18\x180\x00\x00\x00\x00', '\xa8': '\x000\x0000`\xc6|', '+': '\x00\x00\x18\x18~\x18\x18\x00', '\xac': 'c\xe6lz6j\xdf\x06', '/': '\x00\x06\x0c\x180`\xc0\x80', '\xb0': '"\x88"\x88"\x88"\x88', '3': '\x00|\xc6\x06<\x06\xc6|', '\xb4': '\x18\x18\x18\x18\xf8\x18\x18\x18', '7': '\x00\xfe\xc6\x0c\x18000', '\xb8': '\x00\x00\xf8\x18\xf8\x18\x18\x18', ';': '\x00\x18\x18\x00\x00\x18\x180', '\xbc': '66\xf6\x06\xfe\x00\x00\x00', '?': '\x00|\xc6\x0c\x18\x18\x00\x18', '\xc0': '\x18\x18\x18\x18\x1f\x00\x00\x00', 'C': '\x00<f\xc0\xc0\xc0f<', '\xc4': '\x00\x00\x00\x00\xff\x00\x00\x00', 'G': '\x00<f\xc0\xc0\xcef:', '\xc8': '6670?\x00\x00\x00', 'K': '\x00\xe6flxlf\xe6', '\xcc': '66707666', 'O': '\x00|\xc6\xc6\xc6\xc6\xc6|', '\xd0': '6666\xff\x00\x00\x00', 'S': '\x00<f0\x18\x0cf<', '\xd4': '\x18\x18\x1f\x18\x1f\x00\x00\x00', 'W': '\x00\xc6\xc6\xc6\xd6\xd6\xfel', '\xd8': '\x18\x18\xff\x18\xff\x18\x18\x18', '[': '\x00<00000<', '\xdc': '\x00\x00\x00\x00\xff\xff\xff\xff', '_': '\x00\x00\x00\x00\x00\x00\x00\xff', '\xe0': '\x00\x00\x00v\xdc\xc8\xdcv', 'c': '\x00\x00\x00|\xc6\xc0\xc6|', '\xe4': '\x00\xfe\xc6`0`\xc6\xfe', 'g': '\x00\x00\x00v\xcc|\x0c\xf8', '\xe8': '\x00\x10|\xd6\xd6\xd6|\x10', 'k': '\x00\xe0`flxl\xe6', '\xec': '\x00\x00~\xdb\xdb~\x00\x00', 'o': '\x00\x00\x00|\xc6\xc6\xc6|', '\xf0': '\x00\x00\xfe\x00\xfe\x00\xfe\x00', 's': '\x00\x00\x00~\xc0|\x06\xfc', '\xf4': '\x0e\x1b\x1b\x18\x18\x18\x18\x18', 'w': '\x00\x00\x00\xc6\xd6\xd6\xfel', '\xf8': '\x008ll8\x00\x00\x00', '{': '\x00\x0e\x18\x18p\x18\x18\x0e', '\xfc': '\x00l6666\x00\x00', '\x7f': '\x00\x00\x108l\xc6\xc6\xfe', '\x81': '\x00\xcc\x00\xcc\xcc\xcc\xccv', '\x02': '~\xff\xdb\xff\xc3\xe7\xff~', '\x85': '`0\x00x\x0c|\xccv', '\x06': '\x108|\xfe\xfe|\x108', '\x89': '\x00\xc6\x00|\xc6\xfe\xc0|', '\n': '\xff\xc3\x99\xbd\xbd\x99\xc3\xff', '\x8d': '0\x18\x008\x18\x18\x18<', '\x0e': '\x7fc\x7fccg\xe6\xc0', '\x91': '\x00\x00\x00\xec6~\xd8n', '\x12': '\x18<~\x18\x18~<\x18', '\x95': '0\x18\x00|\xc6\xc6\xc6|', '\x16': '\x00\x00\x00\x00~~~\x00', '\x99': '\xc6\x008l\xc6\xc6l8', '\x1a': '\x00\x18\x0c\xfe\x0c\x18\x00\x00', '\x9d': 'ff<~\x18~\x18\x18', '\x1e': '\x00\x18<~\xff\xff\x00\x00', '\xa1': '\x0c\x18\x008\x18\x18\x18<', '"': '\x00ff$\x00\x00\x00\x00', '\xa5': 'v\xdc\x00\xe6\xf6\xde\xce\xc6', '&': '\x008l8v\xdc\xccv', '\xa9': '\x00\x00\x00\xfe\xc0\xc0\x00\x00', '*': '\x00\x00f<\xff<f\x00', '\xad': '\x00\x18\x00\x18\x18<<\x18', '.': '\x00\x00\x00\x00\x00\x00\x18\x18', '\xb1': 'U\xaaU\xaaU\xaaU\xaa', '2': '\x00|\xc6\x06\x1c0f\xfe', '\xb5': '\x18\x18\xf8\x18\xf8\x18\x18\x18', '6': '\x008`\xc0\xfc\xc6\xc6|', '\xb9': '66\xf6\x06\xf6666', ':': '\x00\x00\x18\x18\x00\x00\x18\x18', '\xbd': '6666\xfe\x00\x00\x00', '>': '\x00`0\x18\x0c\x180`', '\xc1': '\x18\x18\x18\x18\xff\x00\x00\x00', 'B': '\x00\xfcff|ff\xfc', '\xc5': '\x18\x18\x18\x18\xff\x18\x18\x18', 'F': '\x00\xfebhxh`\xf0', '\xc9': '\x00\x00?07666', 'J': '\x00\x1e\x0c\x0c\x0c\xcc\xccx', '\xcd': '\x00\x00\xff\x00\xff\x00\x00\x00', 'N': '\x00\xc6\xe6\xf6\xde\xce\xc6\xc6', '\xd1': '\x00\x00\xff\x00\xff\x18\x18\x18', 'R': '\x00\xfcff|lf\xe6', '\xd5': '\x00\x00\x1f\x18\x1f\x18\x18\x18', 'V': '\x00\xc6\xc6\xc6\xc6\xc6l8', '\xd9': '\x18\x18\x18\x18\xf8\x00\x00\x00', 'Z': '\x00\xfe\xc6\x8c\x182f\xfe', '\xdd': '\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0', '^': '\x108l\x00\x00\x00\x00\x00', '\xe1': 'x\xcc\xd8\xcc\xc6\xc6\xcc\x00', 'b': '\x00\xe0`|fff\xdc', '\xe5': '\x00\x00\x00~\xd8\xd8\xd8p', 'f': '\x00<f`\xf8``\xf0', '\xe9': '\x00|\xc6\xc6\xfe\xc6\xc6|', 'j': '\x00\x06\x00\x06\x06\x06f<', '\xed': '\x00\x00\x00\\\xd6\xd6|\x10', 'n': '\x00\x00\x00\xdcffff', '\xf1': '\x00\x18\x18~\x18\x18\x00~', 'r': '\x00\x00\x00\xdcv``\xf0', '\xf5': '\x18\x18\x18\x18\x18\xd8\xd8p', 'v': '\x00\x00\x00\xc6\xc6\xc6l8', '\xf9': '\x00\x00\x00\x00\x18\x18\x00\x00', 'z': '\x00\x00\x00~\x0c\x180~', '\xfd': '\x00x\x0c\x180|\x00\x00', '~': 'v\xdc\x00\x00\x00\x00\x00\x00', '\x01': '~\x81\xa5\x81\xbd\x99\x81~', '\x82': '\x0c\x18\x00|\xc6\xfe\xc0|', '\x05': '8|8\xfe\xfe\xd6\x108', '\x86': '8l8x\x0c|\xccv', '\t': '\x00<fBBf<\x00', '\x8a': '0\x18\x00|\xc6\xfe\xc0|', '\r': '?3?00p\xf0\xe0', '\x8e': '\xc6\x108l\xc6\xfe\xc6\xc6', '\x11': '\x02\x0e>\xfe>\x0e\x02\x00', '\x92': '\x00>l\xcc\xfe\xcc\xcc\xce', '\x15': '>a<ff<\x86|', '\x96': 'x\xcc\x00\xcc\xcc\xcc\xccv', '\x19': '\x18\x18\x18\x18~<\x18\x00', '\x9a': '\xc6\x00\xc6\xc6\xc6\xc6\xc6|', '\x1d': '\x00$f\xfff$\x00\x00', '\x9e': '\xf8\xcc\xcc\xfa\xc6\xcf\xc6\xc7', '!': '\x00\x18<<\x18\x18\x00\x18', '\xa2': '\x0c\x18\x00|\xc6\xc6\xc6|', '%': '\x00\x00\xc6\xcc\x180f\xc6', '\xa6': '\x00<ll6\x00~\x00', ')': '\x000\x18\x0c\x0c\x0c\x180', '\xaa': '\x00\x00\x00\xfe\x06\x06\x00\x00', '-': '\x00\x00\x00\x00~\x00\x00\x00', '\xae': '\x00\x00\x003f\xccf3', '1': '\x00\x188\x18\x18\x18\x18~', '\xb2': 'w\xddw\xddw\xddw\xdd', '5': '\x00\xfe\xc0\xc0\xfc\x06\xc6|', '\xb6': '6666\xf6666', '9': '\x00|\xc6\xc6~\x06\x0cx', '\xba': '66666666', '=': '\x00\x00\x00~\x00\x00~\x00', '\xbe': '\x18\x18\xf8\x18\xf8\x00\x00\x00', 'A': '\x008l\xc6\xfe\xc6\xc6\xc6', '\xc2': '\x00\x00\x00\x00\xff\x18\x18\x18', 'E': '\x00\xfebhxhb\xfe', '\xc6': '\x18\x18\x1f\x18\x1f\x18\x18\x18', 'I': '\x00<\x18\x18\x18\x18\x18<', '\xca': '66\xf7\x00\xff\x00\x00\x00', 'M': '\x00\xc6\xee\xfe\xfe\xd6\xc6\xc6', '\xce': '66\xf7\x00\xf7666', 'Q': '\x00|\xc6\xc6\xc6\xce|\x0e', '\xd2': '\x00\x00\x00\x00\xff666', 'U': '\x00\xc6\xc6\xc6\xc6\xc6\xc6|', '\xd6': '\x00\x00\x00\x00?666', 'Y': '\x00fff<\x18\x18<', '\xda': '\x00\x00\x00\x00\x1f\x18\x18\x18', ']': '\x00<\x0c\x0c\x0c\x0c\x0c<', '\xde': '\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f', 'a': '\x00\x00\x00x\x0c|\xccv', '\xe2': '\x00\xfeb````\xf0', 'e': '\x00\x00\x00|\xc6\xfe\xc0|', '\xe6': '\x00\x00\x00fff|\xc0', 'i': '\x00\x18\x008\x18\x18\x18<', '\xea': '\x008l\xc6\xc6l(\xee', 'm': '\x00\x00\x00\xec\xfe\xd6\xd6\xd6', '\xee': '\x00\x00\x00|\xc6p\xc6|', 'q': '\x00\x00\x00v\xcc|\x0c\x1e', '\xf2': '\x000\x18\x0c\x180\x00~', 'u': '\x00\x00\x00\xcc\xcc\xcc\xccv', '\xf6': '\x00\x00\x18\x00~\x00\x18\x00', 'y': '\x00\x00\x00\xc6\xc6~\x06\xfc', '\xfa': '\x00\x00\x00\x00\x18\x00\x00\x00', '}': '\x00p\x18\x18\x0e\x18\x18p', '\xfe': '\x00\x00<<<<\x00\x00'
}


class Font(object):
    """Single-height bitfont."""

    def __init__(self, height, fontdict={}):
        """Initialise the font."""
        self._height = height
        if height == 8 and not fontdict:
            fontdict = DEFAULT_FONT
        self._fontdict = fontdict

    def get_bytes(self, charvalue):
        """Get byte sequency for character."""
        return self._fontdict[chr(charvalue)]

    def set_bytes(self, charvalue, byte_sequence):
        """Set byte sequency for character."""
        self._fontdict[chr(charvalue)] = byte_sequence

    def build_glyph(self, c, req_width, req_height, carry_col_9, carry_row_9):
        """Build a glyph for the given codepage character."""
        try:
            face = bytearray(self._fontdict[c])
        except KeyError:
            logging.debug(
                    u'%s [%s] not represented in font, replacing with blank glyph.',
                    c, repr(c))
            face = bytearray(int(self._height))
        # shape of encoded mask (8 or 16 wide; usually 8, 14 or 16 tall)
        code_height = 8 if req_height == 9 else req_height
        code_width = (8 * len(face)) // code_height
        force_double = req_width >= code_width * 2
        force_single = code_width >= (req_width-1) * 2
        if force_double or force_single:
            # i.e. we need a double-width char but got single or v.v.
            logging.debug(
                    u'Incorrect glyph width for %s [%s]: %d-pixel requested, %d-pixel found.',
                    c, repr(c), req_width, code_width)
        return _unpack_glyph(
                face, code_height, code_width, req_height, req_width,
                force_double, force_single, carry_col_9, carry_row_9)

if numpy:

    def _unpack_glyph(
            face, code_height, code_width, req_height, req_width,
            force_double, force_single, carry_col_9, carry_row_9):
        """Convert byte list to glyph pixels, numpy implementation."""
        glyph = numpy.unpackbits(face, axis=0).reshape((code_height, code_width)).astype(bool)
        # repeat last rows (e.g. for 9-bit high chars)
        if req_height > glyph.shape[0]:
            if carry_row_9:
                repeat_row = glyph[-1]
            else:
                repeat_row = numpy.zeros((1, code_width), dtype=numpy.uint8)
            while req_height > glyph.shape[0]:
                glyph = numpy.vstack((glyph, repeat_row))
        if force_double:
            glyph = glyph.repeat(2, axis=1)
        elif force_single:
            glyph = glyph[:, ::2]
        # repeat last cols (e.g. for 9-bit wide chars)
        if req_width > glyph.shape[1]:
            if carry_col_9:
                repeat_col = numpy.atleast_2d(glyph[:,-1]).T
            else:
                repeat_col = numpy.zeros((code_height, 1), dtype=numpy.uint8)
            while req_width > glyph.shape[1]:
                glyph = numpy.hstack((glyph, repeat_col))
        return glyph

else:

    def _unpack_glyph(
            face, code_height, code_width, req_height, req_width,
            force_double, force_single, carry_col_9, carry_row_9):
        """Convert byte list to glyph pixels, non-numpy implementation."""
        # req_width can be 8, 9 (SBCS), 16, 18 (DBCS) only
        req_width_base = req_width if req_width <= 9 else req_width // 2
        # if our code glyph is too wide for request, we need to make space
        start_width = req_width*2 if force_single else req_width
        glyph = [ [False]*start_width for _ in range(req_height) ]
        for yy in range(code_height):
            for half in range(code_width//8):
                line = face[yy*(code_width//8)+half]
                for xx in range(8):
                    if (line >> (7-xx)) & 1 == 1:
                        glyph[yy][half*8 + xx] = True
            # halve the width if code width incorrect
            if force_single:
                glyph[yy] = glyph[yy][::2]
            # MDA/VGA 9-bit characters
            # carry_col_9 will be ignored for double-width glyphs
            if carry_col_9 and req_width == 9:
                glyph[yy][8] = glyph[yy][7]
        # tandy 9-bit high characters
        if carry_row_9 and req_height == 9:
            for xx in range(8):
                glyph[8][xx] = glyph[7][xx]
        # double the width if code width incorrect
        if force_double:
            for yy in range(code_height):
                for xx in range(req_width_base, -1, -1):
                    glyph[yy][2*xx+1] = glyph[yy][xx]
                    glyph[yy][2*xx] = glyph[yy][xx]
        return glyph
