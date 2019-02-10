"""
PC-BASIC - display.buffers
Text and pixel buffer operations

(c) 2013--2019 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import logging

from ...compat import zip, int2byte, iterchar
from ..base import signals

from ..base.bytematrix import ByteMatrix


class _TextRow(object):
    """Buffer for a single row of the screen."""

    def __init__(self, attr, width):
        """Set up screen row empty and unwrapped."""
        # halfwidth character buffer, initialised to spaces
        self.chars = [b' '] * width
        # attribute buffer
        self.attrs = [attr] * width
        # last non-whitespace column [0--width], zero means all whitespace
        self.length = 0
        # line continues on next row (either LF or word wrap happened)
        self.wrap = False


class _PixelAccess(object):
    """
    Wrapper class to enable pixel indexing.
    Usage example: VideoBuffer.pixels[y0:y1, x0:x1] = sprite
    """

    def __init__(self, video_buffer):
        """Wrap the VideoBuffer."""
        self._video_buffer = video_buffer
        self._pixels = video_buffer._pixels

    def __getitem__(self, index, data):
        """Retrieve a copy of a pixel range."""
        return self._pixels[index]

    def __setitem__(self, index, data):
        """Set a pixel range, clear affected text buffers and submit to interface."""
        self._pixels[index] = data
        # make sure the indices are slices so that __getattr__ returns a matrix
        yslice, xslice = index
        if not isinstance(yslice, slice):
            yslice = slice(yslice, yslice+1)
        if not isinstance(xslice, slice):
            xslice = slice(xslice, xslice+1)
        # single-attribute fill; ensure we have a complete matrix to submit
        if not instance(data, ByteMatrix):
            data = self._pixels[yslice, xslice]
        self._submit_rect(xslice.start, yslice.start, data)

    def _submit_rect(self, x, y, rect):
        """Clear the text under the rect and submit to interface."""
        row0, col0, row1, col1 = self.pixel_to_text_area(x, y, x+rect.width, y+rect.height)
        # clear text area
        # we can't see or query the attribute in graphics mode - might as well set to zero
        self._video_buffer._clear_text_area(
            row0, col0, row1, col1, 0, adjust_end=False, clear_wrap=False
        )
        #FIXME: dbcs buffer doesn't know screen reality has changed
        for row in range(row0, row1+1):
            self._queues.video.put(signals.Event(
                signals.VIDEO_PUT_TEXT,
                (self._pagenum, row, col0, [u' ']*(col1-col0+1), 0, None)
            ))
        self._queues.video.put(signals.Event(
            signals.VIDEO_PUT_RECT, (self._pagenum, x, y, rect)
        ))

#FIXME: unused
class _CharAccess(object):
    """
    Wrapper class to enable character indexing.
    Usage example: VideoBuffer.chars.set_attr(7)[0, :] = b' '
    """

    def __init__(self, video_buffer):
        """Wrap the VideoBuffer."""
        self._video_buffer = video_buffer
        self._attr = 0

    def set_attr(attr):
        """Set attribute for next access."""
        self._attr = attr
        return self


class VideoBuffer(object):
    """Buffer for a screen page."""

    def __init__(
            self, queues, pixel_height, pixel_width, height, width,
            colourmap, attr, font, codepage, do_fullwidth, pagenum
        ):
        """Initialise the screen buffer to given dimensions."""
        self._rows = [_TextRow(attr, width) for _ in range(height)]
        self._width = width
        self._height = height
        self._font = font
        self._colourmap = colourmap
        # DBCS support
        self._codepage = codepage
        self._dbcs_enabled = codepage.dbcs and do_fullwidth
        self._dbcs_text = [tuple(iterchar(b' ')) * width for _ in range(height)]
        # initialise pixel buffers
        self._pixels = ByteMatrix(pixel_height, pixel_width)
        # with set_attr that calls submit_rect
        self._pixel_access = _PixelAccess(self)
        self._char_access = _CharAccess(self)
        # needed for signals only
        self._pagenum = pagenum
        self._queues = queues

    @property
    def pixels(self):
        """Pixel-buffer access."""
        return self._pixel_access

    @property
    def chars(self):
        """Pixel-buffer access."""
        return self._char_access

    def __repr__(self):
        """Return an ascii representation of the screen buffer (for debugging)."""
        horiz_bar = ('   +' + '-' * self._width + '+')
        row_strs = []
        lastwrap = False
        row_strs.append(horiz_bar)
        for i, row in enumerate(self._rows):
            # replace non-ascii with ? - this is not ideal but
            # for python2 we need to stick to ascii-128 so implicit conversion to bytes works
            # and for python3 we must use unicode
            # and backslashreplace messes up the output width...
            rowstr = ''.join(
                _char.decode('ascii', 'replace').replace(u'\ufffd', u'?')
                for _char in row.chars
            )
            left = '\\' if lastwrap else '|'
            right = '\\' if row.wrap else '|'
            row_strs.append('{0:2} {1}{2}{3} {4:2}'.format(
                i, left, rowstr, right, row.length,
            ))
            lastwrap = row.wrap
        row_strs.append(horiz_bar)
        return '\n'.join(row_strs)

    def rebuild(self):
        """Completely resubmit the text and graphics screen to the interface."""
        # resubmit the text buffer without changing the pixel buffer
        # redraw graphics
        for row in range(self._height):
            self._refresh_range(row+1, 1, self._width, text_only=True)


    ##########################################################################
    # query buffers

    def get_char(self, row, col):
        """Retrieve a (halfwidth) character from the screen (as bytes)."""
        return self._rows[row-1].chars[col-1]

    def get_byte(self, row, col):
        """Retrieve a byte from the character buffer (as int)."""
        return ord(self._rows[row-1].chars[col-1])

    def get_attr(self, row, col):
        """Retrieve attribute from the screen."""
        return self._rows[row-1].attrs[col-1]

    def get_charwidth(self, row, col):
        """Get DBCS width of cell on active page."""
        return len(self._dbcs_text[row-1][col-1])

    #FIXME: sanitise the below

    def pixelrow_until(self, *args, **kwargs):
        return self._pixels.row_until(*args, **kwargs)

    def get_row(self, row):
        """Retrieve characters on a row, as bytes."""
        return b''.join(self._rows[row-1].chars)

    def get_chars(self):
        """Retrieve all characters on this page, as tuple of bytes."""
        return tuple(self.get_row(_row) for _row in range(self._height))

    def get_text(self, start_row, stop_row):
        """Retrieve all logical text on this page, as tuple of list of unicode."""
        return tuple(
            self._dbcs_to_unicode(self._dbcs_text[row-1][:self._length[row-1]])
            for _row in range(start_row, stop_row+1)
        )

    ##########################################################################
    # logical lines

    def find_start_of_line(self, srow):
        """Find the start of the logical line that includes our current position."""
        # move up as long as previous line wraps
        while srow > 1 and self.wraps(srow-1):
            srow -= 1
        return srow

    def find_end_of_line(self, srow):
        """Find the end of the logical line that includes our current position."""
        # move down as long as this line wraps
        while srow <= self._height and self.wraps(srow):
            srow += 1
        return srow

    def set_wrap(self, row, wrap):
        """Connect/disconnect rows on active page by line wrap."""
        self._rows[row-1].wrap = wrap

    def wraps(self, row):
        """The given row is connected by line wrap."""
        return self._rows[row-1].wrap

    def set_row_length(self, row, length):
        """Return logical length of row."""
        self._rows[row-1].length = length

    def row_length(self, row):
        """Return logical length of row."""
        return self._rows[row-1].length


    ##########################################################################
    # convert between text and pixel positions

    def pixel_to_text_pos(self, x, y):
        """Convert pixel position to text position."""
        return 1 + y // self._font.height, 1 + x // self._font.width

    def pixel_to_text_area(self, x0, y0, x1, y1):
        """Convert from pixel area to text area."""
        col0 = min(self.width, max(1, 1 + x0 // self._font.width))
        row0 = min(self.height, max(1, 1 + y0 // self._font.height))
        col1 = min(self.width, max(1, 1 + x1 // self._font.width))
        row1 = min(self.height, max(1, 1 + y1 // self._font.height))
        return row0, col0, row1, col1

    def text_to_pixel_pos(self, row, col):
        """Convert text position to pixel position."""
        # area bounds are all inclusive
        return (
            (col-1) * self._font.width, (row-1) * self._font.height,
        )

    def text_to_pixel_area(self, row0, col0, row1, col1):
        """Convert text area to pixel area."""
        # area bounds are all inclusive
        return (
            (col0-1) * self._font.width, (row0-1) * self._font.height,
            col1 * self._font.width - 1, row1 * self._font.height - 1
        )

    ##########################################################################
    # page copy

    def copy_from(self, src):
        """Copy source into this page."""
        for dst_row, src_row in zip(self._rows, src._rows):
            assert len(dst_row.chars) == len(src_row.chars)
            assert len(dst_row.attrs) == len(src_row.attrs)
            dst_row.chars[:] = src_row.chars
            dst_row.attrs[:] = src_row.attrs
            dst_row.length = src_row.length
            dst_row.wrap = src_row.wrap
        self._dbcs_text[:] = src._dbcs_text
        self._pixels[:, :] = src._pixels
        self._pixel_access = _PixelAccess(self)
        self._char_access = _CharAccess(self)
        self._queues.video.put(signals.Event(
            signals.VIDEO_COPY_PAGE, (src._pagenum, self._pagenum)
        ))


    ##########################################################################
    # modify text

    def put_char_attr(self, row, col, char, attr, adjust_end=False):
        """Put a byte to the screen, reinterpreting SBCS and DBCS as necessary."""
        assert isinstance(char, bytes), type(char)
        # update the screen buffer
        self._rows[row-1].chars[col-1] = char
        self._rows[row-1].attrs[col-1] = attr
        if adjust_end:
            self._rows[row-1].length = max(self._rows[row-1].length, col)
        self._refresh_range(row, col, col)

    def insert_char_attr(self, row, col, char, attr):
        """
        Insert a halfwidth character,
        NOTE: This sets the attribute of *everything that has moved* to attr.
        Return the character dropping off at the end.
        """
        therow = self._rows[row-1]
        therow.chars.insert(col-1, char)
        therow.attrs.insert(col-1, attr)
        pop_char = therow.chars.pop()
        pop_attr = therow.attrs.pop()
        if therow.length >= col:
            therow.length = min(therow.length + 1, self._width)
        else:
            therow.length = col
        # reset the attribute of all moved chars
        stop_col = max(therow.length, col)
        therow.attrs[col-1:stop_col] = [attr] * (stop_col - col + 1)
        # attrs change only up to logical end of row but dbcs can change up to row width
        self._refresh_range(row, col, stop_col)
        return pop_char

    def delete_char_attr(self, row, col, attr, fill_char_attr=None):
        """
        Delete a halfwidth character, filling with space(s) at the logical end.
        NOTE: This sets the attribute of *everything that has moved* to attr.
        """
        therow = self._rows[row-1]
        # do nothing beyond logical end of row
        if therow.length < col:
            return 0, 0
        if fill_char_attr is None:
            fill_char, fill_attr = b' ', attr
            adjust_end = True
        else:
            fill_char, fill_attr = fill_char_attr
        adjust_end = fill_char_attr is None
        therow.chars[:therow.length] = (
            therow.chars[:col-1] + therow.chars[col:therow.length] + [fill_char]
        )
        therow.attrs[:therow.length] = (
            therow.attrs[:col-1] + therow.attrs[col:therow.length] + [fill_attr]
        )
        # reset the attribute of all moved chars
        stop_col = max(therow.length, col)
        therow.attrs[col-1:stop_col] = [attr] * (stop_col - col + 1)
        # change the logical end
        if adjust_end:
            therow.length = max(therow.length - 1, 0)
        self._refresh_range(row, col, stop_col)
        return col, stop_col


    ###########################################################################
    # update pixel buffer and interface

    def _update_dbcs(self, row):
        """Update the DBCS buffer."""
        raw = self.get_row(row)
        if self._dbcs_enabled:
            # get a new converter each time so we don't share state between calls
            conv = self._codepage.get_converter(preserve=b'')
            marks = conv.mark(raw, flush=True)
            tuples = ((_seq,) if len(_seq) == 1 else (_seq, b'') for _seq in marks)
            sequences = [_seq for _tup in tuples for _seq in _tup]
        else:
            sequences = tuple(iterchar(raw))
        updated = [old != new for old, new in zip(self._dbcs_text[row-1], sequences)]
        self._dbcs_text[row-1] = sequences
        try:
            start = updated.index(True) + 1
            stop = len(updated) - updated[::-1].index(True)
        except ValueError:
            # no change to text in buffer
            # however, in graphics mode we need to plot at least the updated range
            # as the dbcs buffer is not updated when overdrawn
            # and in text mode the attribute may have changed
            start, stop = len(updated), 0
        return start, stop

    def _refresh_range(self, row, start, stop, text_only=False):
        """Draw a section of a screen row to pixels and interface."""
        dbcs_start, dbcs_stop = self._update_dbcs(row)
        start, stop = min(start, dbcs_start), max(stop, dbcs_stop)
        col, last_col = start, start
        last_attr = None
        chars = []
        chunks = []
        # collect chars in chunks with the same attribute
        while col <= stop:
            char = self._dbcs_text[row-1][col-1]
            attr = self.get_attr(row, col)
            if attr != last_attr:
                if last_attr is not None:
                    chunks.append((last_col, chars, last_attr))
                last_col, last_attr = col, attr
                chars = []
            chars.append(char)
            col += len(char)
        if chars:
            chunks.append((last_col, chars, attr))
        for col, chars, attr in chunks:
            self._draw_text(row, col, chars, attr, text_only)

    def _dbcs_to_unicode(self, chars):
        """Convert list of dbcs chars to list of unicode; fullwidth trailed by empty u''."""
        text = [[_c, u''] if len(_c) > 1 else [_c] for _c in chars]
        return [self._codepage.to_unicode(_c, u'\0') for _list in text for _c in _list]

    def _draw_text(self, row, col, chars, attr, text_only):
        """Draw a chunk of text in a single attribute to pixels and interface."""
        if row < 1 or col < 1 or row > self._height or col > self._width:
            logging.debug('Ignoring out-of-range text rendering request: row %d col %d', row, col)
            return
        _, back, _, underline = self._colourmap.split_attr(attr)
        # update pixel buffer
        left, top = self.text_to_pixel_pos(row, col)
        sprite = self._font.render_text(chars, attr, back, underline)
        if not text_only:
            self._pixels[top:top+sprite.height, left:left+sprite.width] = sprite
        else:
            sprite = self._pixels[top:top+sprite.height, left:left+sprite.width]
        # mark full-width chars by a trailing empty string to preserve column counts
        text = self._dbcs_to_unicode(chars)
        self._queues.video.put(signals.Event(
            signals.VIDEO_PUT_TEXT, (self._pagenum, row, col, text, attr, sprite)
        ))

    ###########################################################################
    # clearing

    def clear_rows(self, start, stop, attr):
        """Clear text and graphics on given (inclusive) text row range."""
        self._clear_text_area(
            start, 1, stop, self._width, attr, adjust_end=True, clear_wrap=True
        )
        self._dbcs_text[start-1:stop] = [
            tuple(iterchar(b' ')) * self._width for _ in range(stop-start+1)
        ]
        # clear pixels
        x0, y0, x1, y1 = self.text_to_pixel_area(start, 1, stop, self._width)
        _, back, _, _ = self._colourmap.split_attr(attr)
        self._pixels[y0:y1+1, x0:x1+1] = back
        # this should only be called on the active page
        self._queues.video.put(signals.Event(signals.VIDEO_CLEAR_ROWS, (back, start, stop)))

    def clear_row_from(self, srow, scol, attr):
        """Clear from given position to end of logical line (CTRL+END)."""
        if scol == 1:
            self.clear_rows(srow, srow, attr)
        else:
            # clear the first row of the logical line
            self._clear_text_area(
                srow, scol, srow, self._width, attr, adjust_end=True, clear_wrap=True
            )
            # redraw the last char before the clear too, as it may have been changed by dbcs logic
            self._refresh_range(srow, scol-1, self._width)

    def _clear_text_area(self, from_row, from_col, to_row, to_col, attr, clear_wrap, adjust_end):
        """Clear a rectangular area of the screen (inclusive bounds; 1-based indexing)."""
        for row in self._rows[from_row-1:to_row]:
            row.chars[from_col-1:to_col] = [b' '] * (to_col - from_col + 1)
            row.attrs[from_col-1:to_col] = [attr] * (to_col - from_col + 1)
            if adjust_end and row.length <= to_col:
                row.length = min(row.length, from_col-1)
            if clear_wrap:
                row.wrap = False
        #FIXME: update DBCS buffer

    ###########################################################################
    # scrolling

    def _text_scroll_up(self, from_line, bottom, attr):
        """Scroll up."""
        new_row = _TextRow(attr, self._width)
        self._rows.insert(bottom, new_row)
        # remove any wrap above/into deleted row, unless the deleted row wrapped into the next
        if self.wraps(from_line-1):
            self.set_wrap(from_line-1, self.wraps(from_line))
        # delete row # from_line
        del self._rows[from_line-1]

    def scroll_up(self, from_line=None):
        """Scroll the scroll region up by one line, starting at from_line."""
        if from_line is None:
            from_line = self.scroll_area.top
        _, back, _, _ = self._colourmap.split_attr(self._attr)
        self._queues.video.put(signals.Event(
            signals.VIDEO_SCROLL, (-1, from_line, self.scroll_area.bottom, back)
        ))
        if self.current_row > from_line:
            self._move_cursor(self.current_row - 1, self.current_col)
        # update text buffer
        self._text_scroll_up(from_line, self.scroll_area.bottom, self._attr)
        # update dbcs buffer
        self._dbcs_text[from_line-1:self.scroll_area.bottom-1] = (
            self._dbcs_text[from_line:self.scroll_area.bottom]
        )
        self._dbcs_text[self.scroll_area.bottom-1] = (tuple(iterchar(b' ')) * self._width)
        # update pixel buffer
        sx0, sy0, sx1, sy1 = self.text_to_pixel_area(
            from_line+1, 1, self.scroll_area.bottom, self._width
        )
        tx0, ty0 = self.text_to_pixel_pos(from_line, 1)
        self._pixels.move(sy0, sy1+1, sx0, sx1+1, ty0, tx0)

    def _text_scroll_down(self, from_line, bottom, attr):
        """Scroll down."""
        new_row = _TextRow(attr, self._width)
        # insert at row # from_line
        self._rows.insert(from_line - 1, new_row)
        # delete row # bottom
        del self._rows[bottom-1]
        # if we inserted below a wrapping row, make sure the new empty row wraps
        # so as not to break line continuation
        if self.wraps(from_line-1):
            self.set_wrap(from_line, True)

    def scroll_down(self, from_line):
        """Scroll the scroll region down by one line, starting at from_line."""
        _, back, _, _ = self._colourmap.split_attr(self._attr)
        self._queues.video.put(signals.Event(
            signals.VIDEO_SCROLL, (1, from_line, self.scroll_area.bottom, back)
        ))
        if self.current_row >= from_line:
            self._move_cursor(self.current_row + 1, self.current_col)
        # update text buffer
        self._apage._text_scroll_down(from_line, self.scroll_area.bottom, self._attr)
        # update dbcs buffer
        self._dbcs_text[from_line:self.scroll_area.bottom] = (
            self._dbcs_text[from_line-1:self.scroll_area.bottom-1]
        )
        self._dbcs_text[from_line-1] = tuple(iterchar(b' ')) * self._width
        # update pixel buffer
        sx0, sy0, sx1, sy1 = self.text_to_pixel_area(
            from_line, 1, self.scroll_area.bottom-1, self._width
        )
        tx0, ty0 = self.text_to_pixel_pos(from_line+1, 1)
        self._pixels.move(sy0, sy1+1, sx0, sx1+1, ty0, tx0)
