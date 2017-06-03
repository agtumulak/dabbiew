#!/usr/bin/env python
# -*- coding: utf-8 -*-

from  __future__ import division, absolute_import, print_function, unicode_literals

import curses
import locale
import pandas as pd
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


def screen(start, end, extents):
    """Generate column widths or row heights from screen start to end positions.

    Indexing for start and end is analogous to python ranges. Start is first 
    screen position that gets drawn. End does not get drawn. Returned tuples 
    correspond to elements that are inside screen box.

    >>> args = (5, 10, [3, 3, 3, 3, 3])
    >>> [(col, width, cursor) for col, width, cursor in screen(*args)]
    [(1, 1, 0), (2, 3, 1), (3, 1, 4)]

    :param start: screen position start
    :type start: int
    :param end: screen position end
    :type end: int
    :param extents: column widths or row heights
    :type extents: list
    :returns: index of element, extent of element, position of element on screen
    :rtype: int, int, int
    """
    accumulated = 0
    for ind, extent in enumerate(extents):
        accumulated += extent
        if accumulated > start:
            break
    yield ind, accumulated - start, 0
    for ind, extent in enumerate(extents[ind+1:], start=ind+1):
        if accumulated + extent >= end:
            yield ind, end - accumulated, accumulated - start
            raise StopIteration
        else:
            yield ind, extent, accumulated - start
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


def draw(stdscr, df, x_origin, y_origin, left, right, top, bottom, widths, heights):
    """Refresh display with updated view.

    Running line profiler shows this is the slowest part. Will optimize later. 
    Also figure out how to test this.

    :param stdscr: window object to update
    :type stdscr: curses.window
    :param df: underlying data to present
    :type df: pandas.DataFrame
    :param x_origin: x coordinate of leftmost part of view box
    :type x_origin: int
    :param y_origin: y coordinate of bottommost part of view box
    :type y_origin: int
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
    screen_y, screen_x = stdscr.getmaxyx()
    screen_y -= 1 # Avoid cursor going off screen
    for col, width, x_cursor in screen(x_origin, x_origin + screen_x, widths):
        series = df.iloc[:,col]
        for row, height, y_cursor in screen(y_origin, y_origin + screen_y, heights):
            selected = left <= col <= right and top <= row <= bottom
            attribute = curses.A_REVERSE if selected else curses.A_NORMAL
            cell = series.iloc[row]
            text = format_line(str(cell), width).encode('utf-8')
            stdscr.addstr(y_cursor, x_cursor, text, attribute)
    # Clear right margin if theres unused space on the right
    margin = screen_x - (x_cursor + width)
    if margin > 0:
        for row in range(screen_y):
            stdscr.addstr(row, x_cursor + width, ' ' * margin, curses.A_NORMAL)
    stdscr.refresh()


def advance(start, end, resizing, boundary):
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
    """
    moving = True
    if end + 1 < boundary:
        end += 1
        if not resizing:
            start += 1
    return start, end, moving


def retreat(start, end, resizing):
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
    """
    moving = False
    if not resizing and start - 1 >= 0:
        start -= 1
        end -= 1
    elif resizing and end > start:
        end -= 1
    return start, end, moving


def run(stdscr, df):
    curses.curs_set(0) # invisible cursor
    stdscr.scrollok(False)
    screen_y, screen_x = stdscr.getmaxyx()
    rows, cols = df.shape
    left, right, top, bottom = 0, 0, 0, 0
    heights, widths = [1] * rows, [8] * cols
    y_origin, x_origin = 0, 0
    moving_down, moving_right = True, True
    resizing = False

    while True:
        x_origin = origin(x_origin, left, right, widths, screen_x, moving_right)
        y_origin = origin(y_origin, top, bottom, heights, screen_y, moving_down)
        draw(stdscr, df, x_origin, y_origin, left, right, top, bottom, widths, heights)
        keypress = stdscr.getch()
        if keypress == ord('q'):
            break
        if keypress == ord('v'):
            resizing = not resizing
        if keypress == ord('l'):
            left, right, moving_right = advance(left, right, resizing, cols)
        if keypress == ord('j'):
            top, bottom, moving_down = advance(top, bottom, resizing, rows)
        if keypress == ord('h'):
            left, right, moving_right = retreat(left, right, resizing)
        if keypress == ord('k'):
            top, bottom, moving_down = retreat(top, bottom, resizing)
        if keypress == ord('.'):
            moving_right = True
            for col in range(left, right+1):
                widths[col] += 1
        if keypress == ord(','):
            for col in range(left, right+1):
                widths[col] -= 0 if widths[col] == 2 else 1


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    df = pd.DataFrame.from_csv(argv[1], index_col=None)
    curses.wrapper(run, df)
