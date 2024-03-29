<center>
<a href = "/">
<img src="../wiki-images/Logo - Pic Only.png" alt = "BiomationScripter Logo" width = "300"/>
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

!!! warning "Warning"

    **Information on this page may be outdated**

# BiomationScripter - OTProto Templates
---
## Overview

BiomationScripter Templates can be used to help quickly and easily generate automation protocols for common experiments or procedures. Protocols generated using the same Template will all follow the same basic instructions, but will differ depending on user inputs. For example, the heat shock transformation Template accepts user inputs for aspects such as the length of the heat shock, the final volume of the transformations, and the DNA to use in each transformation.

If you can't find a Template for a specific protocol, you can try [raising an issue](https://github.com/intbio-ncl/BiomationScripterLib/issues) on the GitHub to see if anyone can help, or create your own Template [following the walkthrough found here](#creating-custom-otprototemplates).

Below you can find documentation for Opentrons Templates included with BiomationScripter.

---

## OTProto Templates

Any Template can be imported using the statement below:

```python
from BiomationScripter.OTProto.Templates import <TEMPLATE_NAME>
```

Replace `<TEMPLATE_NAME>` in the code above with one of the template names below:

[`Heat_Shock_Transformation`](#template-heat_shock_transformation) | [`DNA_fmol_Dilution`](#template-dna_fmol_dilution) | [`Primer_Mixing`](#template-primer_mixing) | [`Protocol_From_Layouts`](#template-protocol_from_layouts) | [`Spot_Plating`](#template-spot_plating) | [`Standard_iGEM_Calibration`](#template-standard_igem_calibration)

---

### Template: [`Heat_Shock_Transformation`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/Templates.py)

#### Overview

This template can be used to set up heat shock based transformations on the OT2.

#### Generic Protocol Steps

The basic protocol is described below.

1. **Distribute competent cells from aliquots to the transformation labware**
    * The amounts of cells per transformation (in uL) is defined by the user
2. **Add DNA from DNA source labware to the transformation labware**
    * The amount of DNA per transformation (in uL) is defined by the user
3. **Wait for an amount of time (determined by the user in seconds)**
4. **Perform the heat shock**
    * The heat shock temperature (in celcius) is determined by the user
    * The heat shock time (in seconds) is determined by the user
5. **The protocol pauses and prompts the user to supply the media**
6. **The media is distributed to each transformation**
    * The volume of media added is determined by the total volume of the transformation, as defined by the user

The transformations can then be removed from the Opentrons for the incubation step and subsequent plating.

#### Usage

!!! example

    See an example protocol using this template [here](protocol_examples/OTProto/Templates/Heat-Shock-Transformation.ipynb).


The `Template` object is created using the following code:

```python
from BiomationScripter.OTProto.Templates import Heat_Shock_Transformation

Protocol_Template = Heat_Shock_Transformation.Template(
  DNA_Source_Layouts: List[_BMS.Labware_Layout],
  Competent_Cells_Source_Type: str,
  Transformation_Destination_Type: str,
  Media_Source_Type: str,
  DNA_Volume_Per_Transformation: float,
  Competent_Cell_Volume_Per_Transformation: float,
  Transformation_Final_Volume: float,
  Heat_Shock_Time: int,
  Heat_Shock_Temp: int,
  Media_Aliquot_Volume: float,
  Competent_Cells_Aliquot_Volume: float,
  Wait_Before_Shock: int,
  Replicates: int,
  Heat_Shock_Modules: List[str] = ["temperature module gen2"],
  Cooled_Cells_Modules: List[str] = [],
  Shuffle: Union[Tuple[str, str] , None] = None,
  Patience: int = 1200,
  Cells_Mix_Before = (5,"transfer_volume"),
  Cells_Mix_After = None,
  DNA_Mix_Before = None,
  DNA_Mix_After = (10,"transfer_volume"),
  Protocol: opentrons.protocol_api,
  Name: str,
  Metadata,
  Starting_20uL_Tip: str = "A1",
  Starting_300uL_Tip: str = "A1",
  Starting_1000uL_Tip: str = "A1"
)
```


#### Full Documentation

**`__init__` Arguments:**

* `DNA_Source_Layouts` | `List[_BMS.Labware_Layout]`: [`Labware_Layout`]() objects which define the locations for the DNA to be transformed
* `Competent_Cells_Source_Type` | `str`: The type of labware in which the competent cells will be stored - must be an [opentrons API name](../OTProto/#opentrons-api-names)
* `Transformation_Destination_Type` | `str`: The type of labware to prepare the transformations in - must be an [opentrons API name](../OTProto/#opentrons-api-names)
* `Media_Source_Type` | `str`: The type of labware in which the media will be stored - must be an [opentrons API name](../OTProto/#opentrons-api-names)
* `DNA_Volume_Per_Transformation` | `float`: The volume of DNA (in uL) to add per transformation
* `Competent_Cell_Volume_Per_Transformation` | `float`: The volume of competent cells (in uL) to add per transformation
* `Transformation_Final_Volume` | `float`: The final volume (in uL) of each transformation
* `Heat_Shock_Time` | `int`: The time (in seconds) to heat shock
* `Heat_Shock_Temp` | `int`: The temperature (in celcius) to heat shock
* `Media_Aliquot_Volume` | `float`: The volume (in uL) for each media aliquot
* `Competent_Cells_Aliquot_Volume` | `float`: The volume (in uL) for each competent cells aliquot
* `Wait_Before_Shock` | `int`: The time to wait (in seconds) before heat shocking
* `Replicates` | `int`: The number of replicates for each transformation
* `Heat_Shock_Modules` | `List[str] = ["temperature module gen2"]`: The Opentrons module to use for heat shocking - supports use of either the Temperature Modules or the Opentrons Thermocycler
* `Cooled_Cells_Modules` | `List[str] = []`: The Opentrons module to use for cooling competent cells
* `Shuffle` | `Union[Tuple[str, str] , None] = None`: Determines whether the locations of each transformation in the destination will be randomly shuffled
* `Patience` | `int = 1200`: The time to wait (in seconds) for a temperature module to cool to 4C - the protocol will continue after this point even if it hasn't fully cooled
* `Cells_Mix_Before` | `Union[Tuple[int, Union[float , Literal["transfer_volume"]]] , None] = (5,"transfer_volume")`: Mixing parameters for competent cells before aspiration - `(Mixing_Repeats, Mixing_Volume)`
* `Cells_Mix_After` | `Union[Tuple[int, Union[float , Literal["transfer_volume"]]] , None] = None`: Mixing parameters after competent cells are dispensed - `(Mixing_Repeats, Mixing_Volume)`
* `DNA_Mix_Before` | `Union[Tuple[int, Union[float , Literal["transfer_volume"]]] , None] = None`: Mixing parameters for DNA before aspiration - `(Mixing_Repeats, Mixing_Volume)`
* `DNA_Mix_After` | `Union[Tuple[int, Union[float , Literal["transfer_volume"]]] , None] = (10,"transfer_volume")`: Mixing parameters after DNA has been dispensed - `(Mixing_Repeats, Mixing_Volume)`
* [`**kwargs` from `OTProto_Template`](#__init__-arguments)

**Attributes:**

* `dna_per_transformation` | `float`
* `cells_per_transformation` | `float`
* `final_volume` | `float`
* `heat_shock_time` | `int`
* `heat_shock_temp` | `int`
* `wait_before_shock` | `int`
* `replicates` | `int`
* `shuffle` | `Tuple[str, str]` OR `None`
* `patience` | `int`
* `cells_mix_before` | `Tuple[int, float OR "transfer_volume"]` OR `None`
* `cells_mix_after` | `Tuple[int, float OR "transfer_volume"]` OR `None`
* `dna_mix_before` | `Tuple[int, float OR "transfer_volume"]` OR `None`
* `dna_mix_after` | `Tuple[int, float OR "transfer_volume"]` OR `None`
* `heat_shock_modules` | `List[str]`
* `cooled_cells_modules` | `List[str]`
* `dna_source_layouts` | `List[Labware_Layout]`
* `comp_cells_source_type` | `str`
* `comp_cells_aliquot_volume` | `float`
* `media_source_type` | `str`
* `media_aliquot_volume` | `float`
* `destination_type` | `str`
* [All attributes from `OTProto_Template`](#superclass-otproto_template)

**Methods:**

* `run(self)` returns `None`
    * Generates Opentrons liquid handling commands

---

### Template: [`DNA_fmol_Dilution`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/EchoProto/Templates.py)

#### Overview

This protocol can be used to dilute DNA stocks to a specified fmol/uL. Can either dilute stocks in their source labware, or prepare diluted stocks in a new labware.

#### Generic Protocol Steps

The basic protocol is described below.

**If keeping DNA in source labware:**

1. Add the required amount of water to DNA samples and mix

**If moving DNA to new labware:**

1. Add the required amount of water to the destination wells
2. Add the required amount of DNA to the destination wells and mix

#### Usage

!!! example

    See an example protocol using this template [here]().

The `Template` object is created using the following code:

```python
from BiomationScripter.OTProto.Templates import DNA_fmol_Dilution

Protocol_Template = DNA_fmol_Dilution.Template(
  Final_fmol: float,
  DNA: List[str],
  DNA_Concentration: List[float],
  DNA_Length: List[int],
  DNA_Source_Type: str,
  Keep_In_Current_Wells: bool,
  Water_Source_Labware_Type: str,
  Water_Aliquot_Volume: float,
  DNA_Source_Wells: list[str] = None,
  Final_Volume: float = None,
  Current_Volume: List[float] = None,
  Destination_Labware_Type: str = None,
  Destination_Labware_Wells: List[str] = None,
  Protocol: opentrons.protocol_api,
  Name: str,
  Metadata,
  Starting_20uL_Tip: str = "A1",
  Starting_300uL_Tip: str = "A1",
  Starting_1000uL_Tip: str = "A1"
)
```

#### Full Documentation

**`__init__` Arguments:**

* `Final_fmol` | `float`: The final fmol/uL concentration to dilute DNA samples to
* `DNA` | `List[str]`: The names of the DNA to dilute
* `DNA_Concentration` | `List[float]`: The current stock concentrations (in ng/uL)
* `DNA_Length` | `List[int]`: The lengths (in bp) for each DNA sample
* `DNA_Source_Type` | `str`: The type of labware in which the DNA samples are stored - must be an [opentrons API name](../OTProto/#opentrons-api-names)
* `Keep_In_Current_Wells` | `bool`: Whether to dilute the samples in their current labware, or to move them to a new labware
* `Water_Source_Labware_Type` | `str`: The labware in which the water aliquots are kept - must be an [opentrons API name](../OTProto/#opentrons-api-names)
* `Water_Aliquot_Volume` | `float`: The volume (in uL) for the water aliquots
* `DNA_Source_Wells` | `list[str] = None`: The source wells for each DNA sample - if `None`, the source wells are automatically assigned
* `Final_Volume` | `float = None`: The final volume (in uL) for the diluted samples - ignored if `Keep_In_Current_Wells` is `True`
* `Current_Volume` | `List[float] = None`: The current volumes of each DNA sample - ignored if `Keep_In_Current_Wells` is `False`
* `Destination_Labware_Type` | `str = None`: The type of labware to transfer DNA samples to - ignored if `Keep_In_Current_Wells` is `True` - must be an [opentrons API name](../OTProto/#opentrons-api-names)
* `Destination_Labware_Wells` | `List[str] = None`: The destination wells into which the DNA samples should be diluted - if `None` then wells are automatically assigned - ignored if `Keep_In_Current_Wells` is `True`
* [`**kwargs` from `OTProto_Template`](#__init__-arguments)

**Attributes:**

* `final_fmol` | `float`
* `_keep_in_current_wells` | `bool`
* `final_volume` | `float` OR `None`
* `dna` | `List[str]`
* `dna_source_wells` | `List[str]` OR `None`
* `dna_source_type` | `str`
* `dna_starting_volume` | `List[float]` OR `None`
* `dna_starting_concentration` | `List[float]`
* `dna_length` | `list[float]`
* `water_source_labware_type` | `str`
* `water_aliquot_volume` | `float`
* `_destination_labware_type` | `str` OR `None`
* `_destination_labware_wells` | `List[str]` OR `None`

**Methods:**

* `run(self)` returns `None`
    * Generates Opentrons liquid handling commands


### Template: [`Standard_iGEM_Calibration`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/Templates.py)

#### Overview

This template can be used to generate an automation protocol to prepare a 96 well plate for calibrating plate reader fluorescence and absorbance measurements.

For more information about the iGEM calibration protocol, read the following resources:

* https://doi.org/10.1093/synbio/ysac010
* https://technology.igem.org/engineering/test

Briefly, this templates allows for automated transfer of specificed calibrated from stock labware (tubes or plates) into a 96-well measurement plate. A 12-step serial dilution is performed for each calibrant within the measurement plate. The measurement plate can then be used to calibrate a plate reader as described in the resources above.

#### Generic Protocol Steps

The basic protocol is described below for a single calibrant with no repeats

1. Transfer solvent into the appropriate wells A1-A12 of a 96 well measurement plate as required
  * Note that if the calibrant is supplied at the concentration required for the most concentrated point of the serial dilution, no solvent is added to A1

2. Add calibrant to well A1 of the measurement plate

3. Perform a 2-fold serial dilution of the calibrant from well A1 to well A11 (Such that well A12 contains only solvent)

4. Remove excess volume from well A11 so that all wells in the measurement plate have the same volume

#### Usage

!!! example

    See an example protocol using this template [here](protocol_examples/OTProto/Templates/iGEM-Calibration-Plate_Setup.ipynb).

The `Template` object is created using the following code:

```python
from BiomationScripter.OTProto.Templates import Standard_iGEM_Calibration

Protocol_Template = Standard_iGEM_Calibration.Template(
  Calibrants: List[Calibrant],
  Calibrants_Stock_Concs: List[float],
  Calibrants_Initial_Concs: List[float],
  Calibrants_Solvents: List[str],
  Calibrant_Aliquot_Volumes: List[float],
  Solvent_Aliquot_Volumes: List[float],
  Volume_Per_Well: float,
  Repeats: int,
  Calibrant_Labware_Type: str,
  Solvent_Labware_Type: str,
  Destination_Labware_Type: str,
  Trash_Labware_Type: str,
  Solvent_Mix_Before = None,
  Solvent_Mix_After = None,
  Solvent_Source_Touch_Tip: bool = True,
  Solvent_Destination_Touch_Tip: bool = True,
  Solvent_Move_After_Dispense = "well_bottom",
  Solvent_Blowout = "destination well",
  First_Dilution_Mix_Before = (10, "transfer_volume"),
  First_Dilution_Mix_After = (10, "transfer_volume"),
  First_Dilution_Source_Touch_Tip: bool = True,
  First_Dilution_Destination_Touch_Tip: bool = True,
  First_Dilution_Move_After_Dispense = None,
  First_Dilution_Blowout = "destination well",
  Dilution_Mix_Before = (10, "transfer_volume"),
  Dilution_Mix_After = (10, "transfer_volume"),
  Dilution_Source_Touch_Tip: bool = True,
  Dilution_Destination_Touch_Tip: bool = True,
  Dilution_Move_After_Dispense = None,
  Dilution_Blowout = "destination well",
  Mix_Speed_Multipler: float = 2,
  Aspirate_Speed_Multipler: float = 1,
  Dispense_Speed_Multipler: float = 1,
  Blowout_Speed_Multiplier: float = 1,
  Dead_Volume_Proportion: float = 0.95,
  Protocol: opentrons.protocol_api,
  Name: str,
  Metadata,
  Starting_20uL_Tip: str = "A1",
  Starting_300uL_Tip: str = "A1",
  Starting_1000uL_Tip: str = "A1"
)
```

#### Full Documentation



**Attributes:**



**Methods:**

* `run(self)` returns `None`
    * Generates Opentrons liquid handling commands


## Superclass: [`OTProto_Template`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/Templates.py)

This class is used as a superclass for all OTProto templates. It contains attributes and methods which are common to a wide range of Opentrons protocols, and therefore allows for a certain amount of standardisation across the templates.

### Usage

The `OTProto_Template` class shouldn't be used alone. Instead, it should be used to extend OTProto templates, e.g.:

```python
from BiomationScripter import OTProto

class My_New_Template(OTProto.OTProto_Template):
    def __init__(self, My_Arg1, My_Arg2, **kwargs):

        self.my_arg1 = My_Arg1
        self.my_arg2 = May_Arg2

        super().__init__(**kwargs)

    def run(self):
      pass
```

In the above code, the `run` method should contain code to execute the protocol. A full walkthrough for creating an OTProto template can be found [here]().

### `__init__` Arguments

The `OTProto_Template` superclass' `__init__` function accepts the following arguments:

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Name` | `str`: A readable name for the protocol to be created by the template
* `Metadata` | `dict{str: str}`: This is metadata about the protocol - it should follow the best practices described [here](#)
* `Custom_Labware_Dir` | `str`: Directory location pointing to where any custom labware definitions are stored
* `Starting_20uL_Tip` | `str = "A1"`: The position of the starting tip in the first p20 tip box
* `Starting_300uL_Tip` | `str = "A1"`: The position of the starting tip in the first p300 tip box
* `Starting_1000uL_Tip` | `str = "A1"`: The position of the starting tip in the first p1000 tip box

### Attributes

* `_protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `name` | `str`: A readable name for the protocol created by the template
* `metadata` | `dict{str: str}`: This is metadata about the protocol - it should follow the best practices described [here](#)
* `custom_labware_dir` | `str`: Directory location pointing to where any custom labware definitions are stored
* `tip_types` | `dict{str: str}`: A dictionary recording the pipette tip labware to be used by each of the supported pipette types. The dictionary keys are `"P20", "p300", "P1000"`, which refer to the three gen2 single channel pipette types available. The default values for each of these keys are `"opentrons_96_tiprack_20ul", "opentrons_96_tiprack_300ul", "opentrons_96_tiprack_1000ul"` respectively
* `starting_tips` | `dict{str: str}`: A dictionary recording the starting well location for each supported pipette type. The starting tip is assumed to be located in the first tip box loaded onto the deck which is associated with that pipette. The dictionary keys are `"P20", "p300", "P1000"`, which refer to the three gen2 single channel pipette types available.
* `tips_needed` | `dict{str: int}`: A dictionary which records how many of each tip type is required to complete the protocol generated by the template. The dictionary keys are `"P20", "p300", "P1000"`, which refer to the three gen2 single channel pipette types available.
* `_pipettes` | `dict{str: str}`: A dictionary which records the type of pipette mounted in each position of the Opentrons' pipette mount. The keys are `"left", "right"`. The default values for each of these keys are `"p20_single_gen2", "p300_single_gen2"` respectively.
* `__pipettes_loaded` | `bool = False`: Records whether the pipettes have been loaded to the protocol.

### Methods

* `pipettes_loaded(self)` returns `bool`
    * Returns the load state of the pipettes (i.e. `True` if the pipettes have been loaded, `False` if they have not)
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
* `calculate_and_add_tips(self, Transfer_Volumes: List[float], New_Tip: bool)` returns `None`
    * Determines how many tips of each tip type is required based on the currently loaded pipette types and a list of transfer volumes
    * For each transfer volume, the most appropriate pipettea and tip type is selected
    * If `New_Tip` is `True`, then a new tip will be used for every transfer (including situations where a transfer needs to be split into multiple steps)
    * If `New_Tip` is `False`, then the same tip is used for all transfers which share that tip type
    * The number of tips needed are stored in `self.tips_needed`
    * This method can be called multiple times during a protocol, but these must occur after `load_pipettes` and before `add_tip_boxes_to_pipettes`
* `tip_racks_prompt(self)` returns `None`
    * Pauses the protocol at run time and informs the user of how many tip boxes of each type is required
    * Should be called after `add_tip_boxes_to_pipettes`
* `run(self)` returns `None`
    * This should be extended by an OTProto template
    * Calls `self.load_pipettes()`
* `run_as_module(self, Parent)` returns `None`

    !!! warning "Warning"

        * `run_as_module` is experimental and should be used with caution
        * This method may disappear or be changed in a way which is not backward compatible without notice

<!--

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

    This code can be copied to a text file and saved as a python file (.py), which can then be uploaded to the OT-2 either via the app, or run via SSH (See the Opentrons documentation for valid ways of running OT-2 protocols) -->
