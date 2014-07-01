#!/usr/bin/env python
import sys
import re

from setuptools import setup
from npm2spec import __version__

description = "Small library to help you generate spec file for npm project."

long_description = """
npm2spec makes you life easier at packaging npm project for Fedora.
"""

download_url = "http://pypi.python.org/packages/source/p/npm2spec/npm2spec-%s.tar.gz" % __version__

requirements = [
    'requests',
    'jinja2',
    'pkgwat.api',
]

try:
    import argparse
except ImportError:
    requirements.append('argparse')

setup(
    name='npm2spec',
    version=__version__,
    description=description,
    author="Ralph Bean",
    author_email="rbean@redhat.com",
    maintainer="Ralph Bean",
    maintainer_email="rbean@redhat.com",
    url="http://github.com/ralphbean/npm2spec",
    license="GPLv3+",
    long_description=long_description,
    download_url=download_url,
    packages=['npm2spec'],
    include_package_data=True,
    install_requires=requirements,
    entry_points="""
    [console_scripts]
    npm2spec = npm2spec:main
    """,
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Environment :: Console",
        ],

)
