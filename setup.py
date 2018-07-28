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
    version='0.1.2',
    description='A .DS_Store Parser',
    author = 'G-C Partners, LLC',
    author_email = 'nibrahim@g-cpartners.com',
    url='https://github.com/gcpartners/ds_store_tool',
    license="Apache Software License v2",
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'mac_alias'
    ],
    packages=find_packages(
        '.'
    ),
    scripts=[
        u'./ds_store_tool.py',
    ],
    classifiers=[
        'Programming Language :: Python',
    ]
)
