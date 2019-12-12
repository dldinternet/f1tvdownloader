#!/usr/bin/env python
import os
from codecs import open

from setuptools import find_packages, setup

from f1tvdl import __version__

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst'), 'r', 'utf-8') as handle:
    readme = handle.read()


setup(
    name='f1tvdl',
    version=__version__,
    description='A F1TV video downloader for subscribers and legal usage.',
    long_description=readme,
    author='DLDInternet',
    url='http://github.com/dldinternet/f1tvdownloader',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[
        "path.py>=6.2",
        "pyyaml>=5.1",
        "requests>=1.2.0",
        "six>=1.9.0",
        "tabulate>=0.8.3",
        "splinter"
    ],
    extras_require={
        'dev': [
            "pip",
            "mock>=1.2",
            "astroid>=2.2.5",
            "coverage>=4.5.1",
            "flake8>=3.3.0",
            "isort>=4.2.15",
            "mccabe>=0.6.1",
            "pycodestyle>=2.3.1",
            "pyflakes>=1.5.0",
            "pylint>=2.3.1",
            "pytest>=4.3.1",
            "pytest-cov>=2.5.1",
            "pytest-timeout>=1.3.3",
            "requests>=2.19.1",
            "urllib3>=1.23",
            "websocket-client>=0.48.0",
            "tox>=3.14.0",
            "bump2version",
        ],
    },
    entry_points={
        'console_scripts': [
            'f1tvdl=f1tvdl.cli.main:main',
        ],
    },
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
