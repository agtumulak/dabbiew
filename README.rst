#######
dabbiew
#######
.. image:: https://travis-ci.org/agtumulak/dabbiew.svg?branch=master
    :target: https://travis-ci.org/agtumulak/dabbiew

.. image:: https://coveralls.io/repos/github/agtumulak/dabbiew/badge.svg?branch=master
    :target: https://coveralls.io/github/agtumulak/dabbiew?branch=master

.. image:: https://readthedocs.org/projects/dabbiew/badge/?version=latest
    :target: http://dabbiew.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

A curses-based DataFrame viewer inspired by TabView

.. image:: doc/images/dabbiew.gif
   :scale: 50 %
   :alt: alternate text
   :align: center

*****
About
*****
This is a side project for now. I work on it because I want more green squares 
on my GitHub profile.

The main difference between TabView and DabBiew is that underlying data 
structure is a pandas DataFrame instead of a list of lists. This has the 
advantage of potentially being able to take advantage of Dask, which supports 
"Big Data" collections for distributed environments.

************
Installation
************
::

  pip install dabbiew

*****
Usage
*****
Open any csv or Excel file::

  dabbiew file.csv
  dabbiew file.xlsx

************
Key Bindings
************
A move command can be repeated by typing the number of times to repeat before
issuing an action. For example, to move down 12 times, simply type ``12j`` (or
``12↓``). To perform a search, open the search bar with ``\``, enter a
substring to match, and hit return (``↵``).

================================================= ==================================
Key                                               Action
================================================= ==================================
``v``                                             toggle selection mode
``esc``                                           cancel selection
``h`` ``j`` ``k`` ``l`` ``←`` ``↓``  ``↑`` ``→``  movement keys
``gg``, ``GG``                                    jump to top, bottom of DataFrame
``^``, ``$``                                      jump to left, right of DataFrame
``,``, ``.``                                      decrease, increase selection width
``<``, ``>``                                      decrease, increase all widths
``t``, ``y``                                      toggle header, index
``[``, ``]``                                      decrease, increase index width
``:``                                             toggle command mode
``/``                                             toggle search bar
``n``, ``p``                                      next, previous match
``d``                                             enter ipdb debug mode
``q``                                             quit
================================================= ==================================

************
Command Mode
************
Entering command mode (``:``) allows the user to call *any DataFrame method
which returns a Series or DataFrame* on the current selection. For instance, the
user can call ``:sum()``, ``:where(df==42)``, or even ``:where(df==41).sum()``
on a selection. The resulting Series or DataFrame is rendered on screen. To go
back to the previous view, simply quit (``q``). Note the name of the current
DataFrame is always called ``df``.

*************
Documentation
*************
To generate the source code documentation do::

  cd doc
  make html

and open ``_build/html/index.html``
