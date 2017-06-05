#!/usr/bin/env python
# -*- coding: utf-8 -*-

from  __future__ import division, absolute_import, print_function, unicode_literals

import curses
import locale
import pandas as pd
from collections import deque
from sys import argv


def format_line(text, width):
    """Pad or truncate text to fit width.

    Text is left justified if there is sufficient room. Otherwise, text is 
    truncated and ellipsis (\\\\u2026) is appended.

    >>> format_line('lorem ipsum', 16)
    u'lorem ipsum     '
    >>> format_line('lorem ipsum', 6)
    u'lore\\u2026 '
    >>> format_line('lorem ipsum', 2)
    u'\\u2026 '
    >>> format_line('lorem ipsum', 1)
    u' '

    :param text: contents of cell
    :type text: str
    :param width: width of cell
    :type width: int
    :returns: string formatted to fit in width
    :rtype: str
    """
    if len(text) < width:
        return text.ljust(width)
    elif width > 2:
        return text[:width-2] + '… '
    elif width == 2:
        return '… '
    else:
        return ' ' * width


def screen(start, end, extents, offset):
    """Generate column widths or row heights from screen start to end positions.

    Indexing for start and end is analogous to python ranges. Start is first 
    screen position that gets drawn. End does not get drawn. Returned tuples 
    correspond to elements that are inside screen box.

    >>> args = (5, 10, [3, 3, 3, 3, 3], 0)
    >>> [(col, width, cursor) for col, width, cursor in screen(*args)]
    [(1, 1, 0), (2, 3, 1), (3, 1, 4)]
    >>> args = (5, 10, [3, 3, 3, 3, 3], 2)
    >>> [(col, width, cursor) for col, width, cursor in screen(*args)]
    [(1, 1, 2), (2, 3, 3), (3, 1, 6)]

    :param start: screen position start
    :type start: int
    :param end: screen position end
    :type end: int
    :param extents: column widths or row heights
    :type extents: list
    :param offset: shifts cursor position returned by fixed amount
    :type offset: int
    :returns: index of element, extent of element, position of element on screen
    :rtype: int, int, int
    """
    accumulated = 0
    for ind, extent in enumerate(extents):
        accumulated += extent
        if accumulated > start:
            break
    yield ind, accumulated - start, offset
    for ind, extent in enumerate(extents[ind+1:], start=ind+1):
        if accumulated + extent >= end:
            yield ind, end - accumulated, offset + accumulated - start
            raise StopIteration
        else:
            yield ind, extent, offset + accumulated - start
            accumulated += extent


def origin(current, start, end, extents, screen, moving):
    """Determine new origin for screen view if necessary.

    The part of the DataFrame displayed on screen is conceptually a box which 
    has the same dimensions as the screen and hovers over the contents of the 
    DataFrame. The origin of the relative coordinate system of the box is 
    calculated here.

    >>> origin(0, 0, 0, [4, 4, 4], 7, True)
    0
    >>> origin(4, 0, 2, [4, 4, 4], 7, True)
    5
    >>> origin(5, 1, 1, [4, 4, 4], 7, False)
    4

    :param current: current origin of a given axis
    :type current: int
    :param start: leftmost column index or topmost row index selected
    :type start: int
    :param end: rightmost column index or bottommost row index selected
    :type end: int
    :param extents: widths of each column or heights of each row
    :type extents: list
    :param screen: total extent of a given axis
    :type screen: int
    :param moving: flag if current action is advancing
    :type: bool
    :returns: new origin
    :rtype: int
    """
    # Convert indices to coordinates of boundaries
    start = sum(extents[:start])
    end = sum(extents[:end+1])
    if end > current + screen and moving:
        return end - screen
    elif start < current and not moving:
        return start
    else:
        return current


def draw(stdscr, df, frozen_y, frozen_x, unfrozen_y, unfrozen_x,
         origin_y, origin_x, left, right, top, bottom, widths, heights):
    """Refresh display with updated view.

    Running line profiler shows this is the slowest part. Will optimize later. 
    Also figure out how to test this.

    :param stdscr: window object to update
    :type stdscr: curses.window
    :param df: underlying data to present
    :type df: pandas.DataFrame
    :param frozen_y: initial row offset before view box contents are shown
    :type frozen_y: int
    :param frozen_x: initial column offset before view box contents are shown
    :type frozen_x: int
    :param unfrozen_y: number of rows dedicated to contents of view box
    :type unfrozen_y: int
    :param unfrozen_x: number of columns dedicated to contents of view box
    :type unfrozen_x: int
    :param origin_y: y coordinate of bottommost part of view box
    :type origin_y: int
    :param origin_x: x coordinate of leftmost part of view box
    :type origin_x: int
    :param left: leftmost column of selection
    :type left: int
    :param right: rightmost column of selection
    :type left: int
    :param top: topmost row of selection
    :type top: int
    :param bottom: bottommost row of selection
    :type bottom: int
    :param widths: horizontal extent of each column
    :type widths: list
    :param heights: vertical extent of each row
    :type heights: list
    """
    for col, width, x_cursor in screen(origin_x, origin_x + unfrozen_x, widths, frozen_x):
        # Draw persistent header row
        col_selected = left <= col <= right
        col_attribute = curses.A_REVERSE if col_selected else curses.A_NORMAL
        text = format_line(str(df.columns[col]), width).encode('utf-8')
        stdscr.addstr(0, x_cursor, text, col_attribute)
        for row, height, y_cursor in screen(origin_y, origin_y + unfrozen_y, heights, frozen_y):
            # Draw persistent index column
            row_selected = top <= row <= bottom
            row_attribute = curses.A_REVERSE if row_selected else curses.A_NORMAL
            text = format_line(str(df.index[row]), frozen_x).encode('utf-8')
            stdscr.addstr(y_cursor, 0, text, row_attribute)
            # Draw DataFrame contents
            selected = col_selected and row_selected
            attribute = curses.A_REVERSE if selected else curses.A_NORMAL
            text = format_line(str(df.iat[row,col]), width).encode('utf-8')
            stdscr.addstr(y_cursor, x_cursor, text, attribute)
    # Clear right margin if theres unused space on the right
    margin = frozen_x + unfrozen_x - (x_cursor + width)
    if margin > 0:
        for y_cursor in range(frozen_y + unfrozen_y):
            stdscr.addstr(y_cursor, x_cursor + width, ' ' * margin, curses.A_NORMAL)
    # Clear frozen topleft corner
    for x_cursor in range(frozen_x):
        for y_cursor in range(frozen_y):
            stdscr.addstr(y_cursor, x_cursor, ' ', curses.A_NORMAL)
    stdscr.refresh()


def advance(start, end, resizing, boundary, amount):
    """Move down or right.

    >>> advance(0, 0, True, 3)
    (0, 1, True)
    >>> advance(0, 1, False, 3)
    (1, 2, True)
    >>> advance(1, 2, True, 3)
    (1, 2, True)
    >>> advance(1, 2, True, 3)
    (1, 2, True)

    :param start: leftmost column or topmost row
    :type start: int
    :param end: rightmost column or bottommost row
    :type end: int
    :param resizing: flag if the selection is currently being resized
    :type resizing: bool
    :param boundary: total number of columns or rows
    :type boundary: int
    :param amount: number of columns or rows to advance
    :type amount: int
    """
    #TODO: Implement tests for amount
    moving = True
    amount = amount if end + amount < boundary else boundary - 1 - end
    end += amount
    if not resizing:
        start += amount
    return start, end, moving


def retreat(start, end, resizing, amount):
    """Move up or left.
    
    >>> retreat(1, 2, True)
    (1, 1, False)
    >>> retreat(1, 1, True)
    (1, 1, False)
    >>> retreat(1, 1, False)
    (0, 0, False)
    >>> retreat(0, 0, False)
    (0, 0, False)

    :param start: leftmost column or topmost row
    :type start: int
    :param end: rightmost column or bottommost row
    :type end: int
    :param resizing: flag if the selection is currently being resized
    :type resizing: bool
    :param amount: number of columns or rows to retreat
    :type amount: int
    """
    #TODO: Implement tests for amount
    moving = False
    max_amount = end - start if resizing else start
    amount = min(amount, max_amount)
    end -= amount
    if not resizing:
        start -= amount
    return start, end, moving


def number_in(keystroke_history):
    """Returns number previous keystrokes have a number."""
    number = ''
    keystroke_history.reverse() # most recent keystroke first
    for keystroke in keystroke_history:
        if keystroke.isdigit():
            number = keystroke + number
        else:
            break
    keystroke_history.clear()
    if not number:
        return 1
    else:
        return int(number)


def run(stdscr, df):
    curses.curs_set(0) # invisible cursor
    stdscr.scrollok(False)
    screen_y, screen_x = stdscr.getmaxyx()
    screen_y -= 1 # Avoid writing to last line
    frozen_y, frozen_x = 1, 8
    unfrozen_y, unfrozen_x = screen_y - frozen_y, screen_x - frozen_x
    rows, cols = df.shape
    left, right, top, bottom = 0, 0, 0, 0
    heights, widths = [1] * rows, [8] * cols
    origin_y, origin_x = 0, 0
    moving_down, moving_right = True, True
    resizing = False
    max_history = 10
    keystroke_history = deque([], max_history)

    while True:
        origin_x = origin(origin_x, left, right, widths, unfrozen_x, moving_right)
        origin_y = origin(origin_y, top, bottom, heights, unfrozen_y, moving_down)
        draw(stdscr, df, frozen_y, frozen_x, unfrozen_y, unfrozen_x,
             origin_y, origin_x, left, right, top, bottom, widths, heights)
        keypress = stdscr.getch()
        if keypress in [ord('q')]:
            break
        if keypress in [ord('v')]:
            resizing = not resizing
        if keypress in [ord('\x1b')]: # escape key
            resizing = False
            right = left
            bottom = top
        if keypress in [ord('l'), curses.KEY_RIGHT]:
            amount = number_in(keystroke_history)
            left, right, moving_right = advance(left, right, resizing, cols, amount)
        if keypress in [ord('j'), curses.KEY_DOWN]:
            amount = number_in(keystroke_history)
            top, bottom, moving_down = advance(top, bottom, resizing, rows, amount)
        if keypress in [ord('h'), curses.KEY_LEFT]:
            amount = number_in(keystroke_history)
            left, right, moving_right = retreat(left, right, resizing, amount)
        if keypress in [ord('k'), curses.KEY_UP]:
            amount = number_in(keystroke_history)
            top, bottom, moving_down = retreat(top, bottom, resizing, amount)
        if keypress in [ord('.')]:
            moving_right = True
            for col in range(left, right+1):
                widths[col] += 1
        if keypress in [ord(',')]:
            for col in range(left, right+1):
                widths[col] -= 0 if widths[col] == 2 else 1
        if keypress in [ord('t')]:
            toggle = {0 : 1, 1 : 0}
            frozen_y = toggle[frozen_y]
            unfrozen_y = screen_y - frozen_y
        if keypress in [ord('y')]:
            toggle = {0 : 8, 8 : 0}
            frozen_x = toggle[frozen_x]
            unfrozen_x = screen_x - frozen_x
        # Store keystroke in history
        try:
            keystroke_history.append(chr(keypress))
        except ValueError:
            pass


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    df = pd.DataFrame.from_csv(argv[1], index_col=None)
    curses.wrapper(run, df)
