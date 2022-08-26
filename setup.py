from distutils.core import setup

long_description = """
# BiomationScripter

This is a python package containing a set of tool to help with writing automation protocols for various liquid handling robots. There are also a set of generic tools which may help with writing protocols for multiple automation equipment

[ReadTheDocs](https://biomationscripterlib.readthedocs.io/en/v0.2.1/) for version 0.2.1.

## Getting Started

* https://biomationscripterlib.readthedocs.io/en/v0.2.0/Getting-Started

## BiomationScripter - Generic Tools

* https://biomationscripterlib.readthedocs.io/en/v0.2.0/BiomationScripter

## EchoProto

* https://biomationscripterlib.readthedocs.io/en/v0.2.0/EchoProto
* https://biomationscripterlib.readthedocs.io/en/v0.2.0/EchoProto_Templates

## OTProto

* https://biomationscripterlib.readthedocs.io/en/v0.2.0/OTProto
* https://biomationscripterlib.readthedocs.io/en/v0.2.0/OTProto_Templates
"""

setup(
    name='BiomationScripter',
    version='0.2.2',
    description='Tools for scripting bio-automation protocols',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author='Bradley Brown',
    author_email='bradley.brown4@hotmail.co.uk',
    packages=[
        'BiomationScripter',
        'BiomationScripter.EchoProto',
        'BiomationScripter.OTProto',
        'BiomationScripter.EchoProto.Templates',
        'BiomationScripter.OTProto.Templates'
    ],
)
