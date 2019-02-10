"""
PC-BASIC - text.py
Text-buffer operations

(c) 2013--2019 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import logging

from ...compat import zip, int2byte


class TextRow(object):
    """Buffer for a single row of the screen."""

    def __init__(self, attr, width, conv, dbcs_enabled):
        """Set up screen row empty and unwrapped."""
        self._width = width
        # screen buffer, initialised to spaces
        self.buf = [(b' ', attr)] * width
        # character is part of double width char; 0 = no; 1 = lead, 2 = trail
        self.double = [0] * width
        # last non-whitespace column [0--width], zero means all whitespace
        self.end = 0
        # line continues on next row (either LF or word wrap happened)
        self.wrap = False
        self._dbcs_enabled = dbcs_enabled
        self._conv = conv

    def copy_from(self, src_row):
        """Copy contents from another row."""
        assert self._width == src_row._width
        self.buf[:] = src_row.buf[:]
        self.double[:] = src_row.double[:]
        self.end = src_row.end
        self.wrap = src_row.wrap

    def clear(self, attr, from_col=1, to_col=None, adjust_end=True, clear_wrap=False):
        """Clear the screen row between given columns (inclusive; base-1 index)."""
        if to_col is None:
            to_col = self._width
        width = to_col - from_col + 1
        start, stop = from_col - 1, to_col
        self.buf[start:stop] = [(b' ', attr)] * width
        self.double[start:stop] = [0] * width
        if adjust_end and self.end <= to_col:
            self.end = min(self.end, start)
        if clear_wrap:
            self.wrap = False
        return self._rebuild_char_widths_from(from_col)

    def put_char_attr(self, col, char, attr, adjust_end=False):
        """Put a byte to the screen."""
        assert isinstance(char, bytes), type(char)
        # update the screen buffer
        self.buf[col-1] = (char, attr)
        self.double[col-1] = 0
        if adjust_end:
            self.end = max(self.end, col)
        return self._rebuild_char_widths_from(col)

    def _rebuild_char_widths_from(self, col):
        """Rebuild DBCS character width buffers."""
        # nothing to do for sbcs codepages
        if not self._dbcs_enabled:
            return col, col
        # mark out replaced char and changed following dbcs characters to be redrawn
        text = self.get_text_raw()
        sequences = self._conv.mark(text, flush=True)
        flags = ((0,) if len(seq) == 1 else (1, 2) for seq in sequences)
        old_double = self.double
        self.double = [entry for flag in flags for entry in flag]
        # find the first and last changed columns, to be able to redraw
        diff = [old != new for old, new in zip(old_double, self.double)]
        if True in diff:
            start_col, stop_col = diff.index(True) + 1, len(diff) - diff[::-1].index(True)
        else:
            start_col, stop_col = col, col
        # if the tail byte has changed, the lead byte needs to be redrawn as well
        if self.double[start_col-1] == 2:
            start_col -= 1
        return min(col, start_col), max(col, stop_col)

    def insert_char_attr(self, col, c, attr):
        """
        Insert a halfwidth character,
        NOTE: This sets the attribute of *everything that has moved* to attr.
        Return the character dropping off at the end.
        """
        self.buf.insert(col-1, (c, attr))
        pop_char, pop_attr = self.buf.pop()
        self.double.insert(col-1, 0)
        self.double.pop()
        if self.end >= col:
            self.end = min(self.end + 1, self._width)
        else:
            self.end = col
        # reset the attribute of all moved chars
        self.buf[col-1:max(self.end, col)] = [
            (_c, attr) for _c, _ in self.buf[col-1:max(self.end, col)]
        ]
        start_col, stop_col = self._rebuild_char_widths_from(col)
        # attrs change only up to logical end of row but dbcs can change up to row width
        stop_col = max(self.end, stop_col)
        return pop_char, pop_attr, start_col, stop_col

    def delete_char_attr(self, col, attr, fill_char_attr):
        """
        Delete a halfwidth character, filling with space(s) at the logical end.
        NOTE: This sets the attribute of *everything that has moved* to attr.
        """
        # do nothing beyond logical end of row
        if self.end < col:
            return 0, 0
        index = col-1
        adjust_end = fill_char_attr is None
        if adjust_end:
            fill_char_attr = (b' ', attr)
        # before we delete it, what is the dbcs type of this char?
        dbcs = self.double[index]
        self.buf[:self.end] = self.buf[:index] + self.buf[index+1:self.end] + [fill_char_attr]
        self.double[:self.end] = self.double[:index] + self.double[index+1:self.end] + [0]
        # clear trail byte if lead deleted and vice versa
        if dbcs == 2:
            logging.debug('Trail byte delete')
            self.buf[index-1] = (b' ', attr)
            self.double[index-1] = 0
        elif dbcs == 1:
            self.buf[index] = (b' ', attr)
            self.double[index] = 0
        # reset the attribute of all moved chars
        self.buf[col-1:max(self.end, col)] = [
            (_c, attr) for _c, _ in self.buf[col-1:max(self.end, col)]
        ]
        start_col, stop_col = self._rebuild_char_widths_from(col)
        # attrs change only up to old logical end of row but dbcs can change up to row width
        stop_col = max(self.end, stop_col)
        # change the logical end
        if adjust_end:
            self.end = max(self.end - 1, 0)
        return start_col, stop_col

    def get_text_raw(self, from_col=1, to_col=None):
        """Get the raw text between given columns (inclusive)."""
        if to_col is None:
            to_col = self._width
        # slice bounds
        start, stop = from_col - 1, to_col
        # include lead byte if start on trail
        if self.double[start] == 2:
            start -= 1
        # include trail byte if end on lead
        if self.double[stop-1] == 1:
            stop += 1
        return b''.join(_c for _c, _ in self.buf[start:stop])


class TextPage(object):
    """Buffer for a screen page."""

    def __init__(self, attr, width, height, conv, dbcs_enabled):
        """Initialise the screen buffer to given dimensions."""
        self.row = [TextRow(attr, width, conv, dbcs_enabled) for _ in range(height)]


class TextBuffer(object):
    """Buffer for text on all screen pages."""

    def __init__(self, attr, width, height, num_pages, codepage, do_fullwidth):
        """Initialise the screen buffer to given pages and dimensions."""
        self._dbcs_enabled = codepage.dbcs and do_fullwidth
        self._conv = codepage.get_converter(preserve=b'')
        self.pages = [
            TextPage(attr, width, height, self._conv, self._dbcs_enabled)
            for _ in range(num_pages)
        ]
        self._width = width
        self._height = height

    def __repr__(self):
        """Return an ascii representation of the screen buffer (for debugging)."""
        horiz_bar = ('   +' + '-' * self._width + '+')
        row_strs = []
        for num, page in enumerate(self.pages):
            lastwrap = False
            row_strs.append(horiz_bar)
            for i, row in enumerate(page.row):
                # convert non-ascii bytes to \x81 etc
                # dbcs is encoded as double char in left column, '' in right
                rowbytes = (_pair[0] for _pair in row.buf)
                # replace non-ascii with ? - this is not ideal but
                # for python2 we need to stick to ascii-128 so implicit conversion to bytes works
                # and for python3 we must use unicode
                # and backslashreplace messes up the output width...
                rowstr = ''.join(
                    _char.decode('ascii', 'replace').replace(u'\ufffd', u'?')
                    for _char in rowbytes
                )
                left = '\\' if lastwrap else '|'
                right = '\\' if row.wrap else '|'
                row_strs.append('{0:2} {1}{2}{3} {4:2}'.format(
                    i, left, rowstr, right, row.end,
                ))
                lastwrap = row.wrap
            row_strs.append(horiz_bar)
        return '\n'.join(row_strs)

    def set_wrap(self, pagenum, row, wrap):
        """Connect/disconnect rows on active page by line wrap."""
        self.pages[pagenum].row[row-1].wrap = wrap

    def wraps(self, pagenum, row):
        """The given row is connected by line wrap."""
        return self.pages[pagenum].row[row-1].wrap

    def set_row_length(self, pagenum, row, length):
        """Return logical length of row."""
        self.pages[pagenum].row[row-1].end = length

    def row_length(self, pagenum, row):
        """Return logical length of row."""
        return self.pages[pagenum].row[row-1].end

    def copy_page(self, src, dst):
        """Copy source to destination page."""
        for dst_row, src_row in zip(self.pages[dst].row, self.pages[src].row):
            dst_row.copy_from(src_row)

    def clear_area(self, pagenum, from_row, from_col, to_row, to_col, attr, clear_wrap):
        """Clear a rectangular area of the screen (inclusive bounds; 1-based indexing)."""
        for row in self.pages[pagenum].row[from_row-1:to_row]:
            row.clear(attr, from_col=from_col, to_col=to_col, clear_wrap=clear_wrap)

    def put_char_attr(self, pagenum, row, col, c, attr, adjust_end=False):
        """Put a byte to the screen, reinterpreting SBCS and DBCS as necessary."""
        return self.pages[pagenum].row[row-1].put_char_attr(col, c, attr, adjust_end=adjust_end)

    def insert_char_attr(self, pagenum, row, col, c, attr):
        """
        Insert a halfwidth character,
        NOTE: This sets the attribute of *everything that has moved* to attr.
        Return the character dropping off at the end.
        """
        return self.pages[pagenum].row[row-1].insert_char_attr(col, c, attr)

    def delete_char_attr(self, pagenum, row, col, attr, fill_char_attr=None):
        """
        Delete a halfwidth character, filling with space(s) at the logical end.
        NOTE: This sets the attribute of *everything that has moved* to attr.
        """
        return self.pages[pagenum].row[row-1].delete_char_attr(col, attr, fill_char_attr)

    def scroll_up(self, pagenum, from_line, bottom, attr):
        """Scroll up."""
        new_row = TextRow(attr, self._width, self._conv, self._dbcs_enabled)
        self.pages[pagenum].row.insert(bottom, new_row)
        # remove any wrap above/into deleted row, unless the deleted row wrapped into the next
        if self.wraps(pagenum, from_line-1):
            self.set_wrap(pagenum, from_line-1, self.wraps(pagenum, from_line))
        # delete row # from_line
        del self.pages[pagenum].row[from_line-1]

    def scroll_down(self, pagenum, from_line, bottom, attr):
        """Scroll down."""
        new_row = TextRow(attr, self._width, self._conv, self._dbcs_enabled)
        # insert at row # from_line
        self.pages[pagenum].row.insert(from_line - 1, new_row)
        # delete row # bottom
        del self.pages[pagenum].row[bottom-1]
        # if we inserted below a wrapping row, make sure the new empty row wraps
        # so as not to break line continuation
        if self.wraps(pagenum, from_line-1):
            self.set_wrap(pagenum, from_line, True)

    def get_char(self, pagenum, row, col):
        """Retrieve a byte from the screen (SBCS or DBCS half-char)."""
        return ord(self.pages[pagenum].row[row-1].buf[col-1][0])

    def get_attr(self, pagenum, row, col):
        """Retrieve attribute from the screen."""
        return self.pages[pagenum].row[row-1].buf[col-1][1]

    def get_charwidth(self, pagenum, row, col):
        """Retrieve DBCS character width in bytes."""
        dbcs = self.pages[pagenum].row[row-1].double[col-1]
        if dbcs == 0:
            # halfwidth
            return 1
        elif dbcs == 1:
            # fullwidth
            return 2
        # trail byte
        return 0

    def step_right(self, pagenum, row, col):
        """Get the distance in columns to the next position, accounting for character width."""
        width = self.get_charwidth(pagenum, row, col)
        # on a trail byte: just go one to the right
        return width or 1

    def step_left(self, pagenum, row, col):
        """Get the distance in columns to the previous position, accounting for character width."""
        # previous is trail byte: go two to the left
        # lead byte: go three to the left
        width = self.get_charwidth(pagenum, row, col-1)
        if width == 0:
            skip = 2
        elif width == 2:
            skip = 3
        else:
            skip = 1
        return skip

    def get_fullchar_attr(self, pagenum, row, col):
        """Retrieve SBCS or DBCS character."""
        charwidth = self.get_charwidth(pagenum, row, col)
        if charwidth == 2:
            lead = int2byte(self.get_char(pagenum, row, col))
            trail = int2byte(self.get_char(pagenum, row, col + 1))
            return lead + trail, self.get_attr(pagenum, row, col + 1)
        elif charwidth == 1:
            char = int2byte(self.get_char(pagenum, row, col))
            attr = self.get_attr(pagenum, row, col)
            return char, attr
        else:
            logging.debug(
                'DBCS trail byte access at %d, %d (%d)',
                row, col, self.get_charwidth(pagenum, row, col)
            )
            return b'\0', 0

    def get_text_raw(self, pagenum):
        """Retrieve all raw text on a page."""
        return tuple(row.get_text_raw() for row in range(self.pages[pagenum].row))

    ###########################################################################
    # logical lines

    def get_text_logical(self, pagenum, start_row, start_col, stop_row, stop_col):
        """Retrieve section of logical text for copying."""
        if start_row == stop_row:
            return self._get_row_logical(pagenum, start_row, start_col, stop_col)
        text = [
            self._get_row_logical(pagenum, start_row, from_col=start_col)
        ]
        text.extend(
            self._get_row_logical(pagenum, _row)
            for _row in range(start_row, stop_row-1)
        )
        text.append(self._get_row_logical(pagenum, stop_row, to_col=stop_col))
        return b''.join(text)

    def _get_row_logical(self, pagenum, row, from_col=1, to_col=None):
        """Get the text between given columns (inclusive), don't go beyond end."""
        therow = self.pages[pagenum].row[row-1]
        if to_col is None:
            to_col = self._width
        text = therow.get_text_raw(from_col, min(to_col, self.row_length(pagenum, row)))
        # wrap on line that is not full means LF
        if self.row_length(pagenum, row) < self._width or not self.wraps(pagenum, row):
            text += b'\n'
        return text

    def find_start_of_line(self, pagenum, srow):
        """Find the start of the logical line that includes our current position."""
        # move up as long as previous line wraps
        while srow > 1 and self.wraps(pagenum, srow-1):
            srow -= 1
        return srow

    def find_end_of_line(self, pagenum, srow):
        """Find the end of the logical line that includes our current position."""
        # move down as long as this line wraps
        while srow <= self._height and self.wraps(pagenum, srow):
            srow += 1
        return srow

    def get_logical_line(self, pagenum, from_row, from_column=None):
        """Get the contents of the logical line."""
        # find start and end of logical line
        if from_column is None:
            start_row, start_col = self.find_start_of_line(pagenum, from_row), 1
        else:
            start_row, start_col = from_row, from_column
        stop_row = self.find_end_of_line(pagenum, from_row)
        return self.get_text_logical(pagenum, start_row, start_col, stop_row, stop_col=None)

    def get_logical_line_from(self, pagenum, srow, prompt_row, left, right):
        """Get bytearray of the contents of the logical line, adapted for INPUT."""
        # INPUT: the prompt starts at the beginning of a logical line
        # but the row may have moved up: this happens on line 24
        # in this case we need to move up to the start of the logical line
        prompt_row = self.find_start_of_line(pagenum, prompt_row)
        # find start of logical line
        srow = self.find_start_of_line(pagenum, srow)
        # INPUT returns empty string if enter pressed below prompt row
        if srow > prompt_row:
            return b''
        text = []
        # add all rows of the logical line
        for row in range(srow, self._height+1):
            # exclude prompt, if any; only go from furthest_left to furthest_right
            if row == prompt_row:
                text.append(self._get_row_logical(pagenum, row, from_col=left, to_col=right))
            else:
                text.append(self._get_row_logical(pagenum, row,))
            if not self.wraps(pagenum, row):
                break
        return b''.join(text)
