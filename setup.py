#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import find_packages, setup

setup(
    name='ds_store_parser',
    version='0.1.0',
    description='A .DS_Store Parser',
    author = 'G-C Partners, LLC',
    author_email = 'nibrahim@g-cpartners.com',
    url='https://github.com/gcpartners/ds_store_tool',
    # download_url = 'https://github.com/gcpartners/ds_store_tool/archive/0.0.1.tar.gz',
    license="Apache Software License v2",
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'ds_store'
    ],
    packages=find_packages(
        '.'
    ),
    scripts=[
        u'scripts/DsStoreParser.py',
    ],
    classifiers=[
        'Programming Language :: Python',
    ]
)
