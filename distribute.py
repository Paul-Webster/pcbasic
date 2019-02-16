#!/usr/bin/env python
"""
PC-BASIC packaging script
Python, Windows, MacOS and Linux packaging

(c) 2015--2019 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import sys

# get setup.py parameters
from setup import SETUP_OPTIONS

# we're not setup.py and not being called by the sdist installer
# so we can import from the package if we want
from pcbasic.metadata import AUTHOR
from pcbasic.basic import NAME, VERSION, COPYRIGHT

# setup commands
from packaging.common import COMMANDS, SHORT_VERSION


if set(sys.argv) & set(('bdist_msi', 'bdist_dmg', 'bdist_deb', 'build_rpm')):
    from packaging import package
    package(SETUP_OPTIONS, NAME, AUTHOR, VERSION, SHORT_VERSION, COPYRIGHT)

else:
    # sdist, bdist_wheel, build_docs, wash
    from setuptools import setup
    setup(cmdclass=COMMANDS, **SETUP_OPTIONS)
