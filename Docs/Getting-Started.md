# BiomationScripter - Getting Started
---
[Overview](https://github.com/intbio-ncl/BiomationScripter/wiki/Getting-Started#feature-overview) | [Installation](https://github.com/intbio-ncl/BiomationScripter/wiki/Getting-Started#installation)

---
## Feature Overview

The BiomationScripter python library contains a set of packages to help programmatically script protocols for bioautomation platforms. Currently supported automation equipment are listed below, along with their associated BiomationScripter module name. More information for how to use these packages can be found by following the relevant link. BiomationScripter also contains some generic functions and classes which can be used to help write protocols for any automation platform, and can be used in conjunction with the specialised packages listed below.

* [Generic tools](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/__init__.py) - [BiomationScripter](https://github.com/intbio-ncl/BiomationScripterLib/wiki/BiomationScripter)
* [OpenTrons-2](https://www.opentrons.com/ot-2/) - [OTProto](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto)
* [Echo 525](https://www.mybeckman.uk/liquid-handlers/echo-525) - [EchoProto](https://github.com/intbio-ncl/BiomationScripterLib/wiki/EchoProto)
* [CyBioFelix](https://www.analytik-jena.com/products/liquid-handling-automation/liquid-handling/flexible-benchtop-liquid-handling/cybio-felix-series/) - FelixProto - **Coming Soon**

---

## Installation

Clone [the repository](https://github.com/intbio-ncl/BiomationScripter) on to your working area, and then choose one of the options below:

A. Run the following command to install the python package on your machine:

   `pip install git+https://github.com/intbio-ncl/BiomationScripter.git`

B. `cd` into the directory you just cloned, and run the following command to install the python package on your machine:

    `python setup.py install`

---
