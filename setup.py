#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
===========
Foggy March
===========

:Authors:
    Moritz Emanuel Beber
:Date:
    2014-01-27
:Copyright:
    Copyright |c| 2013, Jacobs University Bremen gGmbH, all rights reserved.
:File:
    setup.py

.. |c| unicode:: U+A9
"""


from setuptools import setup


setup(
    name = "foggy",
    version = "0.3",
    description = "simulate and analyse random walks on graphs",
    author = "Moritz Emanuel Beber",
    author_email = "moritz (dot) beber (at) gmail (dot) com",
    url = "http://github.com/Midnighter/foggy-march",
    packages = ["foggy"],
)

