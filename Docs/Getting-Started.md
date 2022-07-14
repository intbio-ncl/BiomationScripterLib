<center>
<a href = "Home.md">
<img src="../Resources/Logo - Full Name.png" alt = "BiomationScripter Logo" width = "300"/>
</a>



---
[Home](Home.md) |
[Getting Started](Getting-Started.md) |
[Generic Tools](BiomationScripter.md) |
[EchoProto](EchoProto.md) |
[EchoProto Templates](EchoProto_Templates.md) |
[OTProto](OTProto.md) |
[OTProto Templates](OTProto_Templates.md)
---
</center>

# BiomationScripter - Getting Started
---
[Overview](Getting-Started.md#feature-overview) |
[Where To Start](Getting-Started.md#where-to-start) |
[Installation](Getting-Started.md#installation)

---
## Feature Overview

The BiomationScripter python library contains a set of packages to help programmatically script protocols for bioautomation platforms. Currently supported automation equipment are listed below, along with their associated BiomationScripter module name. More information for how to use these packages can be found by following the relevant link. BiomationScripter also contains some generic functions and classes which can be used to help write protocols for any automation platform, and can be used in conjunction with the specialised packages listed below.

If you are unsure where to start, see the guidance [here](#where-to-start).

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

## Where To Start

### Using Templates

BiomationScripter contains Templates for certain protocols, such as PCR or transformation. These Templates can be supplied with user inputs to generate a protocol for the chosen automation equipment. For example, if you wished to use the Echo liquid handler to prepare a set of PCR reactions, you could use the EchoProto PCR Template. This Template can be supplied with information specific to your experiment, such as the type of polymerase and buffer to use, the template DNA and primers, and the final volume of the PCR reactions. The Template will then use the information provided to generate an automation protocol for the Echo.

See the options below for more information about how BiomationScripter Templates work.

**For Echo Liquid Handler**

The [EchoProto Templates documentation page](EchoProto_Templates.md) has explanations of the existing EchoProto Templates, along with links to walkthroughs showing how each Template can be used. If you're not sure where to start, try [this walkthough](Protocol%20Examples/EchoProto/Templates/EchoProto-Templates-Loop_Assembly.ipynb).

**For Opentrons Liquid Handler**

*Coming Soon*

### Making Templates

Whilst BiomationScripter contains ready-made Templates for common protocols, there may be an experiment you wish to automate for which no Template exists. If this automated experiment is something which you are likely to run many times, but with different parameters or inputs, you may wish to create your own Template. To learn how to do this, see the information below.

**For Echo Liquid Handler**

Check out the example walkthrough [here](Example_Code_Snippets/EchoProto/EchoProto-EchoProto_Template-Superclass.ipynb), and the full documentation [here](EchoProto_Templates.md#superclass-echoproto_template).

**For Opentrons Liquid Handler**

*Coming soon*

### Writing protocols without Templates

There are some experiments/protocols you may wish to automate which will not be ran often, or if they are the inputs will always remain the same. In this case, it may be better to write the protocol without the use of a Template. In this case, you can use the helper functions and classes included in the `BMS` generic tools package, along with tools in the package related to the automation equipment you wish to use. To find out more, see below.

**For Echo Liquid Handler**

Full documentation can be found [here](EchoProto.md).

**For Opentrons Liquid Handler**

Full documentation can be found [here](OTProto.md).

---
