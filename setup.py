#!/usr/bin/env python

from distutils.core import setup

setup(name='BiomationScripter',
      version='0.2.dev',
      description='Tools for scripting bio-automation protocols',
      author='Bradley Brown',
      author_email='bradley.brown4@hotmail.co.uk',
      packages=['BiomationScripter', 'BiomationScripter.EchoProto', 'BiomationScripter.OTProto'],
     )
