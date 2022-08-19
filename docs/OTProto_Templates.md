<center>
<a href = "/">
<img src="../wiki-images/Logo - Full Name.png" alt = "BiomationScripter Logo" width = "300"/>
</a>



---
[Home](index.md) |
[Getting Started](Getting-Started.md) |
[Generic Tools](BiomationScripter.md) |
[EchoProto](EchoProto.md) |
[EchoProto Templates](EchoProto_Templates.md) |
[OTProto](OTProto.md) |
[OTProto Templates](OTProto_Templates.md)
---
</center>

# BiomationScripter - OTProto - Templates
---

[Overview](#overview) | [Using OTProto Templates](#using-otproto-templates) | [Creating Templates](#creating-custom-otprototemplates) | [All Templates](#ot2-templates) | [OTProto Template Superclass](#superclass-otproto_template)

---

## Overview

BiomationScripter Templates can be used to help quickly and easily generate automation protocols for common experiments or procedures. Protocols generated using the same Template will all follow the same basic instructions, but will differ depending on user inputs. For example, the heat shock transformation Template accepts user inputs for aspects such as the length of the heat shock, the final volume of the transformations, and the DNA to use in each transformation.

If you can't find a Template for a specific protocol, you can try [raising an issue](https://github.com/intbio-ncl/BiomationScripterLib/issues) on the GitHub to see if anyone can help, or create your own Template [following the walkthrough found here](#creating-custom-otprototemplates).

Below you can find documentation for Opentrons Templates included with BiomationScripter.

---

## Using OTProto.Templates

## Import Statement
`import BiomationScripter.OTProto.Templates as Templates`

## Using OTProto Templates
Described here are the generic best practices for creating Opentrons protocols using OTProto templates.

### Walkthrough
Begin by creating a python file in any text editor or IDE. Then, set up the content of the python file following the guidelines below.

**Header:**

The header of the python file can be split up into three sections:
1. **Point the Opentrons to the location of the BMS library:** This adds the BMS library to the Opentrons python path. Make sure that the directory specified is the same as the directory BMS was installed in during [installation](#setting-up-the-ot-2-to-work-with-biomationscripter).
2. **Import the BiomationScripter library and OTProto.Templates module:** This makes the required functions and classes available for use
3. **Record the protocol metadata:** Record metadata for the protocol - follow the format given in the code below; this is required by the templates and the protocol will not run without it

```python
####################################################
# Import BiomationScripter to help write protocols #
####################################################
# This code block will be used by the Opentrons to find the pre-installed BMS library
import sys
sys.path.insert(0, "/var/lib/jupyter/notebooks/Packages/BiomationScripterLib") # This should be the directory in which BMS was installed

# This code block imports the BMS library and the OTProto.Templates module
import BiomationScripter as BMS
import BiomationScripter.OTProto.Templates as Templates

##################################
# Record the protocol's metadata #
##################################
metadata = {
    'protocolName': 'Protocol Name',
    'author': 'Author',
    'author-email': 'author@email.com',
    'user': 'User',
    'user-email': 'user@email.com',
    'source': 'Generated using BiomationScripter',
    'apiLevel': '2.10',
    'robotName': 'Robo' # This is the name/ID of the OT2 you plan to run the protocol on
}

```

**Body:**

This section of code is where the user-defined aspects of the protocol are specified, and where the OTProto template class is called. See the [`OTProto Template Documentation`]() for the list of user-defined arguments required, and the format they must be supplied in.

Changes to the robot configuration can also be specified here. See the [`OTProto Template Superclass documentation`](#superclass-otproto_template) for more information.

```python
# All user-defined information about the protocol is stored within a function...
# ..called 'run', which can be called by the Opentrons at runtime (or during simulation)

def run(protocol):
   #################################################
   # Add information needed for the protocol here: #
   #################################################

   Argument_1 = "Cello"
   Argument_2 = "World"
   Argument_3 = 12

   #########################################################################################
   # The code below calls the template class and passes along the user-defined information #
   #########################################################################################

   # Create the template object and pass the required user-defined variables
   Example_Protocol = Templates.Example_Template(
      Protocol = protocol, # Takes the protocol object supplied to the run function
      Name = metadata["protocolName"],
      Metadata = metadata,
      Argument_1 = Argument_1,
      Argument_2 = Argument_2,
      Argument_3 = Argument_3
   )

   # Call the template's run method
   Example_Protocol.run()
```

**Simulation:**

For loading to the Opentrons, just the code above is required. There are two methods for simulating the protocol:

**Option one:**

Follow the instructions [here](https://support.opentrons.com/en/articles/2741869-simulating-ot-2-protocols-on-your-computer).

**Option two:**

Append the code below to the end of the protocol file and run the file (either on the command line, in an IDE, or in Jupyter Notebook):

```python
# #####################################################################
# Use this cell if simulating the protocol, otherwise comment it out #
# #####################################################################

# #########################################################################################################
# IMPORTANT - the protocol will not upload to the opentrons if this cell is not commented out or removed #
# #########################################################################################################

from opentrons import simulate as OT2 # This line simulates the protocol
# Get the correct api version
protocol = OT2.get_protocol_api(metadata["apiLevel"])
# Home the pipetting head
protocol.home()
# Call the 'run' function to run the protocol
run(protocol)
for line in protocol.commands():
    print(line)
```

**NOTE: this code block MUST be removed or commented out before loading the protocol file to the opentrons, otherwise an error will occur during load**

### Example
The code below shows an example for using the [`DNA_fmol_Dilution`]() OTProto template to create an Opentrons protocol.

The protocol takes 10 DNA samples and dilutes them to 10 fmol/μL in new tubes.

```python
####################################################
# Import BiomationScripter to help write protocols #
####################################################
import sys
sys.path.insert(0, "/var/lib/jupyter/notebooks/Packages/BiomationScripterLib/")
import BiomationScripter as BMS
import BiomationScripter.OTProto.Templates as Templates

##################################
# Record the protocol's metadata #
##################################
metadata = {
    'protocolName': 'Dilute level 0 Phytobrick parts to 10 fmol per uL',
    'author': 'Bradley Brown',
    'author-email': 'b.bradley2@newcastle.ac.uk',
    'user': 'Bradley Brown',
    'user-email': 'b.bradley2@newcastle.ac.uk',
    'source': 'Generated using BiomationScripter',
    'apiLevel': '2.10',
    'robotName': 'ICOT2S' # This is the name of the OT2 you plan to run the protocol on
}

##############################################################
# Use this cell to call the Spot Plating protocol template #
##############################################################

def run(protocol):

    #################################################
    # Add information needed for the protocol here: #
    #################################################

    Final_Fmol = 10
    DNA = [
        "EiraCFP_CE", #1 *
        "JuniperGFP_CE", #2 *
        "BlazeYFP_CE", #3 *
        "B0015_EF", #4 *
        "EL222_CE", #6 *
        "pBLInd100-B0034_AC", #7 *
        "J23100-B0034_AC", #8 *
        "mCherry_CE", #11 *
        "pOdd_AF_ab", #9
        "pOdd_AF_bg" #10
    ]

    DNA_Concentration = [ # ng/uL
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100
    ]

    DNA_Length = [ # bp
        2000,
        3000,
        3000,
        3000,
        3000,
        3000,
        3000,
        3000,
        3000,
        3000
    ]

    DNA_Source_Type = "3dprinted_24_tuberack_1500ul"

    DNA_Source_Wells = [
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "B1",
        "B2",
        "B3",
        "B4",
        "B5"
    ]

    Keep_In_Current_Wells = False

    Final_Volume = 10 # uL
    Destination_Labware_Type = "labcyte384pp_384_wellplate_65ul"
    Destination_Labware_Range = BMS.well_range("A1:A10")

    Water_Source_Labware_Type = "3dprinted_24_tuberack_1500ul"
    Water_Per_Well = 1000 #uL

    Starting_20uL_Tip = "A1"
    Starting_300uL_Tip = "A1"


    #################################################
    #################################################
    #################################################

    ##############################################################
    # The code below creates the protocol to be ran or simulated #
    ##############################################################

    fmol_dilution = Templates.DNA_fmol_Dilution(
        Protocol=protocol,
        Name=metadata["protocolName"],
        Metadata=metadata,
        Final_fmol = Final_Fmol,
        DNA = DNA,
        DNA_Concentration = DNA_Concentration,
        DNA_Length = DNA_Length,
        DNA_Source_Type = DNA_Source_Type,
        DNA_Source_Wells = DNA_Source_Wells,
        Keep_In_Current_Wells = Keep_In_Current_Wells,
        Water_Source_Labware_Type = Water_Source_Labware_Type,
        Water_Per_Well = Water_Per_Well,
        Final_Volume = Final_Volume,
        Destination_Labware_Type = Destination_Labware_Type,
        Destination_Labware_Range = Destination_Labware_Range,
        Starting_20uL_Tip = Starting_20uL_Tip,
        Starting_300uL_Tip = Starting_300uL_Tip
    )
    fmol_dilution.custom_labware_dir = "PATH_TO_CUSTOM_LABWARE"
    fmol_dilution.run()
```

This code can be copied to a text file and saved as a python file (.py), which can then be uploaded to the OT-2 either via the app, or run via SSH (See the Opentrons documentation for valid ways of running OT-2 protocols)

## Creating custom OTProto.Templates
It is possible to create custom OTProto templates by appending to the [`BiomationScripter/OTProto/Templates.py`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/Templates.py) file.

In BiomationScripter, templates are stored as python classes which extend the [`BiomationScripter.OTProto.OTProto_Template`](#superclass-otproto_template) superclass, which defines methods and attributes common to all OTProto templates. Full documentation relating to these attributes and methods can be found [here](#superclass-otproto_template).

The [`BiomationScripter.OTProto.OTProto_Template`](#superclass-otproto_template) superclass has the following `__init__` arguments:
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Name` | `str`: The name of the protocol (this is the name of the protocol, NOT the protocol template)
* `Metadata` | `dict{str: str}`: This is metadata about the protocol - it should follow the best practices described [here]()
* `Starting_20uL_Tip` | `str = "A1"`: Optional argument which specifies the position of the first 20uL tip to use in the first tip rack
* `Starting_300uL_Tip` | `str = "A1"`: Optional argument which specifies the position of the first 300uL tip to use in the first tip rack
* `Starting_1000uL_Tip` | `str = "A1"`: Optional argument which specifies the position of the first 1000uL tip to use in the first tip rack

For information about methods which are available to use with OTProto template classes, check out the [template superclass documentation](#superclass-otproto_template).

OTProto templates all follow a similar structure, as shown below:

```python
class Your_Template(_OTProto.OTProto_Template):
   def __init__(self,
      # These are arguments which are specific to the protocol template being created
      Argument_1,
      Argument_2,
      ...
      Argument_n,
      # `**kwargs` is used to pass keyword arguments to the `_OTProto.OTProto_Template` superclass
      **kwargs
   ):

      # The code below stores information specific to the protocol template as attributes
      # The attribute values may come from the arguments above, or have default values defined
      ########################################
      # User defined aspects of the protocol #
      ########################################
      self.argument_1 = Argument_1
      self.argument_2 = Argument_2
      ...
      self.argument_n = Argument_n
      self.attribute = "Cello"

      # This code must always be included as it passes keyword arguments to the superclass
      # (Required arguments: Protocol, Name, Metadata)
      # (Arguments with default values: Starting_20uL_Tip="A1", Starting_300uL_Tip="A1", Starting_1000uL_Tip="A1")
      ##################################################
      # Protocol Metadata and Instrument Configuration #
      ##################################################
      super().__init__(**kwargs)

   # The `run` method stores all actions related to setting up the protocol and the liquid handling actions
   # When called by the OT2, it will run the protocol
   def run(self):

      # Always begin by calling the `load_pipettes` method (which is defined by the superclass)
      # This locks in which pipette types will be available for the duration of the protocol
      #################
      # Load pipettes #
      #################
      self.load_pipettes()

      # The rest of the code will be dependent on the specific protocol template...
      # ...but will largely follow the fomrat of loading tip racks (and determining how many are required),...
      # ...loading other labware, and generating the liquid transfer actions to be performed
```


---

## OT2 Templates

[`DNA_fmol_Dilution`](#template-dna_fmol_dilution) |
[`Heat_Shock_Transformation`](#template-heat_shock_transformation) |
[`Primer_Mixing`](#template-primer_mixing) |
[`Protocol_From_Layouts`](#template-protocol_from_layouts) |
[`Spot_Plating`](#template-spot_plating) |
[`Standard_iGEM_Calibration`](#template-standard_igem_calibration)


### Template: [`DNA_fmol_Dilution`](../BiomationScripter/EchoProto/Templates.py)

#### Overview:
asdf

#### Generic Protocol Steps:

The basic protocol is described below. Volumes stated below are for 5 uL final reaction volumes. These amounts will be scaled based on the user-defined final volume. DNA parts are assumed to be at 10 fmol/uL.

1. **Add 0.5 uL of buffer**
    * The buffer type is determined by the user
    * A list of buffers can be supplied - in this case each buffer is added in equal amounts such that the total buffer volume is 0.5 uL
2. **Add 0.125 uL of enzyme**
    * The enzyme type is determined by the user, although the protocol is intended for use with SapI (even level assemblies) or BsaI (odd level assemblies)
3. **Add 0.125 uL of T4 ligase**
    * The ligase type can be modified by the user, but T4 Ligase is the intended reagent
4. **Add DNA backbone as supplied by the user**
    * The volume is 0.25 uL adjusted by the backbone to part ratio supplied by the user
5. **Add the DNA part(s) supplied by the user**
    * The volume is 0.25 uL per part, adjusted by the backbone to part ratio supplied by the user
6. **Add nuclease free water so that the final volume is 5 uL**

Following set up by the Echo, the destination plate(s) should be vortexed and briefly span down to ensure all liquid is at the bottom of the wells.

#### Usage

See an example protocol using this template [here](Protocol%20Examples/EchoProto/Templates/EchoProto-Templates-Loop_Assembly.ipynb).

The Template object is created using the following code:

```python
BiomationScripter.EchoProto.Templates.Loop_Assembly(

)
```

#### Full Documentation

**Attributes:**

* `name` | `str`: A name for the protocol (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `metadata` | `dict[str]`: A dictionary describing the metadata for the protocol (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)

**Methods:**

*





## Superclass: [`OTProto_Template`](../BiomationScripter/OTProto/Templates.py)

This class is used as a superclass for all OTProto templates. It contains attributes and methods which are common to any Opentrons protocol, and therefore allows for a certain amount of standardisation across the templates.

**Usage:**

The `OTProto_Template` class should only be used to extend OTProto templates, and shouldn't be called by itself. Below is an example of how a new protocol template can be created using this class. For a complete walkthrough describing how OTProto templates can be created, see [here](#).

```python
class New_Template(BiomationScripter.OTProto.OTProto_Template):
   def __init__(self, **kwargs):
      super().__init__(**kwargs)
```

**Attributes:**

* `_protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `name` | `str`: A readable name for the protocol created by the template
* `metadata` | `dict{str: str}`: This is metadata about the protocol - it should follow the best practices described [here](#)
* `custom_labware_dir` | `str`: Directory location pointing to where any custom labware definitions are stored
* `tip_types` | `dict{str: str}`: A dictionary recording the pipette tip labware to be used by each of the supported pipette types. The dictionary keys are `"P20", "p300", "P1000"`, which refer to the three gen2 single channel pipette types available. The default values for each of these keys are `"opentrons_96_tiprack_20ul", "opentrons_96_tiprack_300ul", "opentrons_96_tiprack_1000ul"` respectively
* `starting_tips` | `dict{str: str}`: A dictionary recording the starting well location for each supported pipette type. The starting tip is assumed to be located in the first tip box loaded onto the deck which is associated with that pipette. The dictionary keys are `"P20", "p300", "P1000"`, which refer to the three gen2 single channel pipette types available.
* `tips_needed` | `dict{str: int}`: A dictionary which records how many of each tip type is required to complete the protocol generated by the template. The dictionary keys are `"P20", "p300", "P1000"`, which refer to the three gen2 single channel pipette types available.
* `_pipettes` | `dict{str: str}`: A dictionary which records the type of pipette mounted in each position of the Opentrons' pipette mount. The keys are `"left", "right"`. The default values for each of these keys are `"p20_single_gen2", "p300_single_gen2"` respectively.
* `__pipettes_loaded` | `bool = False`: Records whether the pipettes have been loaded to the protocol.

**Methods:**

* `__init__(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Name: str, Metadata: dict{str: str}, Starting_20uL_Tip: str = "A1", Starting_300uL_Tip: str = "A1", Starting_1000uL_Tip: str = "A1")` returns `BiomationScripter.OTProto.OTProto_Template`
  * Should only be called within the `__init__` of an OTProto Template class as `super().__init__(**kwargs)`
  * `Protocol` is stored as `self._protocol`
  * `Name` is stored as `self.name`
  * `Metadata` is stored as `self.metadata`
  * `Starting_20uL_Tip`, `Starting_300uL_Tip`, and `Starting_1000uL_Tip` are stored as the values in the `self.starting_tips` attribute. The keys for these values are `"P20", "p300", "P1000"` respectively, which refer to the three gen2 single channel pipette types available.
* `custom_labware_directory(self, Directory: str)` returns `None`
  * Changes `self.custom_labware_dir` to `Directory`
* `pipette_config(self, Pipette_Type: str, Position: str)` returns `None`:
  * Changes the pipette type to be loaded in position `Position` to `Pipette_Type`
  * Looks for `Position` as a key in the `self._pipettes` dictionary and changes its value to `Pipette_Type`
  * If `Position` is not either "left" or "right" (not case sensitive), an error is raised
  * If the pipettes have already been loaded, an error is raised
  * An error will *not* be raised at this stage if `Pipette_Type` is not a valid pipette type
* `load_pipettes(self)` returns `None`
  * Loads the pipettes using information stored in `self._pipettes` to the `opentrons.protocol_api.contexts.ProtocolContext` object stored in `self._protocol`
  * If the pipette type stored in `self._pipettes` is not a valid pipette type, an error will be raised
  * If the pipettes have already been loaded, a warning is raised and the pipettes are not re-loaded
  * The `self.__pipettes_loaded` flag is changed to `True` if the pipettes are successfully loaded
* `tip_type(self, Pipette: str, Tip_Type: str)` returns `None`
  * Changes the tip type labware associated with the pipette type `Pipette` in the `self.tip_types` dictionary
  * An error is raised if `Pipette` is not a key in `self.tip_types`
  * An error is not raised at this stage if `Tip_Type` is not a valid tip type labware
* `starting_tip_position(self, Pipette: str, Tip_Position: str)` returns `None`
  * Changes the position in the first tip box labware loaded from which the pipette with a type of `Pipette` should take its first tip
  * An error is raised if `Pipette` is not a key in `self.starting_tips`
  * `Tip_Position` should be a well position which exists in tip box labware (e.g. B1, C5, D12), but an error will not be raised at this stage
* `add_tip_boxes_to_pipettes(self)` returns `None`
  * Determines how of each type of tip box is required, loads these boxes to the deck, and associates them to the correct pipette
  * `self.tips_needed` is used to determine how many tip boxes are required
  * `self.tip_types` is used to get the labware type for the tip boxes, and to determine which pipette should be assigned which tip box
  * If a pipette type is required but has not been loaded, an error will be raised
* `run(self)` returns `None`
  * This should be extended by an OTProto template
  * Calls `self.load_pipettes()`
* `run_as_module(self, Parent)` returns `None`
  * This is experimental and should only be used with caution
  * This method may disappear or be changed in a way which is not backward compatible
