#!/usr/bin/env python
# -*- coding: utf-8 -*-

from  __future__ import division, absolute_import, print_function, unicode_literals

import curses
import locale
import numpy as np
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


def screen(start, end, cum_extents, offset):
    """Generate column widths or row heights from screen start to end positions.

    Indexing for start and end is analogous to python ranges. Start is first 
    screen position that gets drawn. End does not get drawn. Returned tuples 
    correspond to elements that are inside screen box.

    >>> args = (5, 10, [0, 3, 6, 9, 12, 15], 0)
    >>> [(col, width, cursor) for col, width, cursor in screen(*args)]
    [(1, 1, 0), (2, 3, 1), (3, 1, 4)]
    >>> args = (5, 10, [0, 3, 6, 9, 12, 15], 2)
    >>> [(col, width, cursor) for col, width, cursor in screen(*args)]
    [(1, 1, 2), (2, 3, 3), (3, 1, 6)]

    :param start: screen position start
    :type start: int
    :param end: screen position end
    :type end: int
    :param cum_extents: cumulative sum of column widths or row heights
    :type cum_extents: numpy.ndarray
    :param offset: shifts cursor position returned by fixed amount
    :type offset: int
    :returns: index of element, extent of element, position of element on screen
    :rtype: int, int, int
    """
    cum_extents = cum_extents[1:] # Initial zero useless
    ind = np.searchsorted(cum_extents, start)
    yield ind, cum_extents[ind] - start, offset
    for ind, cum_extent in enumerate(cum_extents[ind+1:], start=ind+1):
        if cum_extent >= end:
            yield (ind,
                  end - cum_extents[ind-1],
                  offset + cum_extents[ind-1] - start)
            raise StopIteration
        else:
            yield (ind,
                  cum_extents[ind] - cum_extents[ind-1],
                  offset + cum_extents[ind-1] - start)


def origin(current, start, end, cum_extents, screen, moving):
    """Determine new origin for screen view if necessary.

    The part of the DataFrame displayed on screen is conceptually a box which 
    has the same dimensions as the screen and hovers over the contents of the 
    DataFrame. The origin of the relative coordinate system of the box is 
    calculated here.

    >>> origin(0, 0, 0, [0, 4, 8, 12], 7, True)
    0
    >>> origin(4, 0, 2, [0, 4, 8, 12], 7, True)
    5
    >>> origin(5, 1, 1, [0, 4, 8, 12], 7, False)
    4

    :param current: current origin of a given axis
    :type current: int
    :param start: leftmost column index or topmost row index selected
    :type start: int
    :param end: rightmost column index or bottommost row index selected
    :type end: int
    :param cum_extents: cumulative sum of column widths or row heights
    :type cum_extents: numpy.ndarray
    :param screen: total extent of a given axis
    :type screen: int
    :param moving: flag if current action is advancing
    :type: bool
    :returns: new origin
    :rtype: int
    """
    # Convert indices to coordinates of boundaries
    start = cum_extents[start]
    end = cum_extents[end+1]
    if end > current + screen and moving:
        return end - screen
    elif start < current and not moving:
        return start
    else:
        return current


def draw(stdscr, df, frozen_y, frozen_x, unfrozen_y, unfrozen_x,
         origin_y, origin_x, left, right, top, bottom, cum_widths, cum_heights):
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
    :param cum_widths: cumulative sum of column widths
    :type cum_widths: numpy.ndarray
    :param cum_heights: cumulative sum of row heights
    :type cum_heights: numpy.ndarray
    """
    for col, width, x_cursor in screen(origin_x, origin_x + unfrozen_x, cum_widths, frozen_x):
        # Draw persistent header row
        col_selected = left <= col <= right
        col_attribute = curses.A_REVERSE if col_selected else curses.A_NORMAL
        text = format_line(str(df.columns[col]), width).encode('utf-8')
        stdscr.addstr(0, x_cursor, text, col_attribute)
        for row, height, y_cursor in screen(origin_y, origin_y + unfrozen_y, cum_heights, frozen_y):
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

    >>> advance(0, 0, True, 3, 1)
    (0, 1, True)
    >>> advance(0, 1, False, 3, 1)
    (1, 2, True)
    >>> advance(1, 2, True, 3, 1)
    (1, 2, True)
    >>> advance(1, 2, True, 3, 1)
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
    
    >>> retreat(1, 2, True, 1)
    (1, 1, False)
    >>> retreat(1, 1, True, 1)
    (1, 1, False)
    >>> retreat(1, 1, False, 1)
    (0, 0, False)
    >>> retreat(0, 0, False, 1)
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
    """Returns number previous keystrokes have a number.

    >>> number_in(deque(['s', 'p', 'a', 'm']))
    1
    >>> number_in(deque(['8', 's', 'p', 'a', 'm']))
    1
    >>> number_in(deque(['8', 's', 'p', 'a', 'm', '9']))
    9
    >>> number_in(deque(['8', 's', 'p', 'a', 'm', '9', '0']))
    90

    :param keystroke_history: contains the last few keystrokes
    :type keystroke_history: collections.deque
    :returns: number inferred from keystroke history
    :rtype: int
    """
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


def expand_cumsum(start, end, cum_extents, amount):
    """Increase each extent by a given amount and update cumulative extents.

    >>> expand_cumsum(1, 2, np.array([0, 4, 8, 12, 16, 20]), 2)
    array([ 0,  4, 10, 16, 20, 24])

    :param start: leftmost column or topmost row of range to expand
    :type start: int
    :param end: rightmost column or bottommost row of range to expand
    :type end: int
    :param cum_extents: cumulative sum of column widths or row heights
    :type cum_extents: numpy.ndarray
    :param amount: amount to increment each row or column in range
    :type amount: int
    """
    extent_increase = np.append(np.array([0]), np.full(cum_extents.size - 1, 0))
    extent_increase[start+1:end+2] = amount
    return cum_extents + extent_increase.cumsum()


def contract_cumsum(start, end, cum_extents, amount, minimum_extent=2):
    """Decrease each extent by a given amount and update cumulative extents.

    >>> contract_cumsum(1, 2, np.array([0, 4, 8, 12, 16, 20]), 2)
    array([ 0,  4,  6,  8, 12, 16])
    >>> contract_cumsum(1, 2, np.array([0, 3, 6, 9, 12, 15]), 2)
    array([ 0,  3,  6,  9, 12, 15])

    :param start: leftmost column or topmost row of range to contract
    :type start: int
    :param end: rightmost column or bottommost row of range to contract
    :type end: int
    :param cum_extents: cumulative sum of column widths or row heights
    :type cum_extents: numpy.ndarray
    :param amount: amount to decrement each row or column in range
    :type amount: int
    """
    extents = np.diff(cum_extents[start:end+2])
    extent_decrease = np.append(np.array([0]), np.full(cum_extents.size - 1, 0))
    # Only decrase extents if it stays above minimum extent
    extent_decrease[start+1:end+2][extents - amount >= minimum_extent] = amount
    return cum_extents - extent_decrease.cumsum()


def run(stdscr, df):
    curses.curs_set(0) # invisible cursor
    stdscr.scrollok(False)
    screen_y, screen_x = stdscr.getmaxyx()
    screen_y -= 1 # Avoid writing to last line
    frozen_y, frozen_x = 1, 8
    unfrozen_y, unfrozen_x = screen_y - frozen_y, screen_x - frozen_x
    rows, cols = df.shape
    left, right, top, bottom = 0, 0, 0, 0
    cum_heights = np.append(np.array([0]), np.full(rows, 1).cumsum())
    cum_widths = np.append(np.array([0]), np.full(cols, 10).cumsum())
    origin_y, origin_x = 0, 0
    moving_down, moving_right = True, True
    resizing = False
    max_history = 10
    keystroke_history = deque([], max_history)

    while True:
        origin_x = origin(origin_x, left, right, cum_widths, unfrozen_x, moving_right)
        origin_y = origin(origin_y, top, bottom, cum_heights, unfrozen_y, moving_down)
        draw(stdscr, df, frozen_y, frozen_x, unfrozen_y, unfrozen_x,
             origin_y, origin_x, left, right, top, bottom, cum_widths, cum_heights)
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
            cum_widths = expand_cumsum(left, right, cum_widths, 1)
        if keypress in [ord(',')]:
            cum_widths = contract_cumsum(left, right, cum_widths, 1)
        if keypress in [ord('<')]:
            cum_widths = contract_cumsum(0, cols-1, cum_widths, 1)
        if keypress in [ord('>')]:
            moving_right = True
            cum_widths = expand_cumsum(0, cols-1, cum_widths, 1)
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
