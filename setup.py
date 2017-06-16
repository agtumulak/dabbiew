from  __future__ import division, absolute_import, print_function, unicode_literals

from dabbiew.version import get_git_version
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
  name='dabbiew',
  version=get_git_version(),
  description='A curses-based DataFrame viewer inspired by TabView.',
  long_description=readme(),
  classifiers=[
      'Environment :: Console :: Curses',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 2.7',
      'Topic :: Database :: Front-Ends',
  ],
  keywords='curses dataframe viewer',
  url='https://github.com/agtumulak/dabbiew',
  author='Aaron G. Tumulak',
  author_email='agtumulak@gmail.com',
  license='MIT',
  packages=['dabbiew'],
  scripts=['bin/dabbiew'],
  install_requires=[
      'numpy',
      'pandas',
      'xlrd'
  ]
 )
