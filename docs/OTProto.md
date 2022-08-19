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

# BiomationScripter - OTProto
---
[Overview](#feature-overview) | [Setting up the OT-2](#setting-up-the-ot-2-to-work-with-biomationscripter) | [Using OTProto](#using-otproto) | [Functions](#functions) | [Simulating Protocols](#simulating-protocols) | [OTProto Templates](#using-otprototemplates)

---
## Feature Overview
OTProto is a module within the BiomationScripter package which contains tools specifically aimed at assisting with scripting protocols for the Opentrons-2. This module makes use of the [OT2 API V2](https://docs.opentrons.com/v2/index.html) python protocol.

OTProto contains two submodules:

* [**OTProto:**](#using-otproto) A set of functions and classes which abstract out some parts of the protocol writing, such as determining how many tips are required, and switching loading custom labware
* [**OTProto.Templates:**](#templates) A set of classes which generate OT-2 instructions for common protocols, such as plasmid purification and transformation, based on user inputs

If you are planning on using the Opentrons to automate common protocols, such as transformation, there may be a pre-written OTProto template available. A list of currently available templates can be found [here](OTProto_Templates.md).

If you are planning on automating a protocol which you will use many times, but with slightly different variations/inputs, it may be helpful to create your own OTProto template. A walkthrough explaining how this can be done can be found [here](Example_Code_Snippets/OTProto/OTProto-OTProto_Template-Superclass.ipynb).

If you are planning to automate a protocol for which there are no existing templates, and that protocol will only be repeated identically (or not at all), it may be best to not write a template. In this case, the [general BiomationScripter tools](BiomationScripter.md) and [OTProto tools](#using-otproto) can be used to help write the protocol.

---

## Setting up the OT-2 to work with BiomationScripter
Due to large amounts of the OT-2's onboard computer being read only, the BiomationScripter package can not be installed as usual. Instead, follow the instructions below to get set up.

1. Create a new directory called `Packages` in the writable section of the OT-2's onboard computer
     * `/var/lib/jupyter/notebooks/` is an example of a writable directory
2. Clone the [BiomationScripter repo](https://github.com/intbio-ncl/BiomationScripter) into this new directory
3. The following code will need to be added to start of every protocol you wish to use BiomationScripter in:
     ```python
     import sys
     sys.path.insert(0, "<Directory>")
     ```
     Replace `<Directory>` with the path you cloned BiomationScripter into (e.g. `/var/lib/jupyter/notebooks/Packages/BiomationScripterLib`)

NOTE: Version 6.0.0 of the Opentrons app added in a new analysis function. In order to make use of this function, BiomationScripter must also be installed in a specific location on the controlling PC. Instructions for doing this can be found [here](https://support.opentrons.com/s/article/Using-Python-packages-in-Python-API-protocols#modulenotfounderror). If these instructions are not followed, you will see a 'Protocol anlysis failure' popup box, with a message similar to 'No module named BiomationScripter'. Note that you can also choose to ignore this error and proceed to running the protocol.

---

## Using OTProto
Begin by importing the OTProto module:
```python
import BiomationScripter.OTProto as OTProto
```

### Functions

[`add_tip_boxes_to_pipettes`](#function-add_tip_boxes_to_pipettes) |
[`calculate_and_load_labware`](#function-calculate_and_load_labware) |
[`calculate_tips_needed`](#function-calculate_tips_needed) |
[`dispense_from_aliquots`](#function-dispense_from_aliquots) |
[`get_labware_format`](#function-get_labware_format) |
[`get_labware_well_capacity`](#function-get_labware_well_capacity) |
[`get_locations`](#function-get_locations) |
[`get_p1000`](#function-get_p1000) |
[`get_p20`](#function-get_p20) |
[`get_p300`](#function-get_p300) |
[`get_pipette`](#function-get_pipette) |
[`load_custom_labware`](#function-load_custom_labware) |
[`load_labware_from_layout`](#function-load_labware_from_layout) |
[`load_labware`](#function-load_labware) |
[`load_pipettes_and_tips`](#function-load_pipettes_and_tips) |
[`next_empty_slot`](#function-next_empty_slot) |
[`select_pipette_by_volume`](#function-select_pipette_by_volume) |
[`shuffle_locations`](#function-shuffle_locations) |
[`tip_racks_needed`](#function-tip_racks_needed) |
[`transfer_liquids`](#function-transfer_liquids)

<br>
<br>

### Function: [`add_tip_boxes_to_pipettes`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This functions calculates how many tip boxes of a specific tip type are required, and then loads that many boxes to the Opentrons deck.

**Usage**

`OTProto.add_tip_boxes_to_pipettes(protocol: opentrons.protocol_api.contexts.ProtocolContext, Pipette_Type: str, Tip_Type: str, Tips_Needed: int, Starting_Tip: str)` returns `float`

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Pipette_Type` | `str`: The type of pipette which will use the tips being loaded (either `"p20"`, `"p300"`, or `"p1000"`)
* `Tip_Type` | `str`: The labware api name for the type of tip to load (e.g. `"opentrons_96_tiprack_20ul"`)
* `Tips_Needed` | `int`: Number of tips needed for the entire protocol of the specific tip type
* `Starting_Tip` | `str = "A1"`: The starting tip position in the first tip box, will default to the first position ("A1")

**Behaviour:**

This function will calculate the number of boxes of the specified tip type needed based on the number of tips needed. The boxes will then be loaded to the Opentrons deck, and associated with the specified pipette type.

### Function: [`calculate_and_load_labware`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function calculates how many of a certain labware type is required for a protocol, and then loads the labware to the deck

**Usage:**

`OTProto.calculate_and_load_labware(protocol: opentrons.protocol_api.contexts.ProtocolContext, labware_api_name: str, wells_required: int, custom_labware_dir: str = None, label: str = None)` returns `list[opentrons.protocol_api.labware.Labware]` and `list[opentrons.protocol_api.labware.Well]`

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `labware_api_name` | `str`: The Opentrons API name for the labware to be loaded
* `wells_required` | `int`: The number of wells which need to be available for use
* `custom_labware_dir` | `str = None`: Location of a directory where any custom labware definition files are stored
* `label` | `str = None`: A human readable label for the loaded labware

**Behaviour:**

This function loads a set of labware, where the type is defined by `labware_api_name`, and the amount of labware loaded is defined by the number of wells required (as supplied by the `wells_required` argument).

This function first calls [`BiomationScripter.OTProto.load_labware`](#function-load_labware) to load a single copy of the labware, as it is assumed that at least one of the labware will always be required. The labware is loaded into the next empty slot on the deck. If not slots remain, an error is raised. This first loaded labware is then used to determine how many wells the labware contains, and therefore how many copies of the labware is required based on the number of wells needed (`wells_required`). If more than one labware is required, these extra copies are then also loaded onto the next empty slot(s). If at any point there are no more free slots, an error is raised.

Once all required labware has been loaded, a list of well locations ([`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) is generated. This list of wells locations is equal in length to the number of `wells_required`, and can be used to determine which wells can be used in each of the loaded labware.

The function then returns two variables: the list of loaded labware, and the list of well locations.

The `custom_labware_dir` and `labware_api_name` arguments are passed directly to [`BiomationScripter.OTProto.load_labware`](#function-load_labware).

### Function: [`calculate_tips_needed`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function determines how many tips of each size (20uL, 300uL, and 1000uL) are required for a set of liquid transfer actions, based on the pipette types present and whether a new tip should be used for each transfer or not

**Usage:**

`OTProto.calculate_tips_needed(Protocol: opentrons.protocol_api.contexts.ProtocolContext, transfers: list[float], template: BMS.OTProto.Template = None, new_tip: bool = True)` returns `float` and `float` and `float`

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `transfers` | `list[float]`: List of volumes to be transferred by the Opentrons
* `template` | `BMS.OTProto.template = None`: This argument must refer to an OTProto template object - the tips needed will be added to the template's `tips_needed` attribute as well as returned
* `new_tip` | `bool = True`: A boolean which determines whether a new tip is used for every transfer specified (`True`), or if one tip is used for all transfers (`False`)

**Behaviour:**

For each volume in the list passed to `transfers`, the [`select_pipette_by_volume`](#function-select_pipette_by_volume) function is used to determine which pipette size should be used to perform that transfer, based on the pipette type(s) loaded. It is then determined whether that transfer can be completed in one step (e.g. a p300 transferring 100 uL), or two steps (e.g. a p300 transfering 400 uL in 2*200 uL steps). From this information, along with the `new_tip` argument, it is determined how many tips are needed for that transfer, and what tip size is required.

Once all transfer volumes have been iterated through, the function returns the number of each tip type needed as an `int` in the order of 20uL, 300uL, and 1000uL.


### Function: [`dispense_from_aliquots`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function can be used to dispense varying amounts of liquid from a set of aliquots to a list of destination locations

**Usage:**

`
OTProto.dispense_from_aliquots(
  protocol: opentrons.protocol_api.contexts.ProtocolContext,
  Transfer_Volumes: list[float],
  Aliquot_Source_Locations: list[opentrons.protocol_api.labware.Well],
  Destinations: list[opentrons.protocol_api.labware.Well],
  Min_Tranfer: float = None,
  Calculate_Only: bool = False,
  Dead_Volume_Proportion: float = 0.95,
  Aliquot_Volumes: list[float]/float = None,
  new_tip: bool = True,
  mix_after: tuple(int, float/int/str) = None,
  mix_before: tuple(int, float/int/str) = None,
  mix_speed_multiplier: float = 1,
  aspirate_speed_multiplier: float = 1,
  dispense_speed_multiplier: float = 1,
  blowout_speed_multiplier: float = 1,
  touch_tip_source: bool = False,
  touch_tip_destination: bool = False,
  blow_out: bool = False,
  blowout_location: str = "destination well",
  move_after_dispense: str = None
)
` returns `None`

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Transfer_Volumes` | `list[float]`: A list of transfer volumes (in microlitres)
* `Aliquot_Source_Locations` | `list[opentrons.protocol_api.labware.Well]`: A list of locations for each of the aliquots - to be used as the potential source locations
* `Destinations` | `list[opentrons.protocol_api.labware.Well]`: A list of locations which liquid will be transferred to
* `Min_Transfer` | `float = None`: The minimal transfer volume to allow - this prevents transfer splits across aliquots from falling below this threshold
* `Calculate_Only` | `bool = False`: The function will only calculate the transfers and return them, rather than perform the liquid handling
* `Dead_Volume_Proportion` | `float = 0.95`: Defines the dead volume proportion of the aliquots - e.g. 0.95 means than 5% of the total well capacity is the dead volume
* `Aliquot_Volumes` | `list[float]/float = None`: A list of volumes relating to the amount of liquid in each aliquot specified by `Aliquot_Source_Locations` - if a single float is specified this volume will be used for all aliquots
* `new_tip` | `bool = True`: A boolean which determines whether a new tip is used for every transfer specified (`True`), or if one tip is used for all transfers (`False`)
* `mix_after` | `tuple(int, int/float/str) = None`: Specifies mixing event after dispensing into the destination location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)
* `mix_before` | `tuple(int, int/float/str) = None`: Specifies mixing event before aspirating from the source location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)
* `mix_speed_multiplier` | `float = 1`: Speed multiplier for mixing steps
* `aspirate_speed_multiplier` | `float = 1`: Speed multiplier for aspirate steps
* `dispense_speed_multiplier` | `float = 1`: Speed multiplier for dispense steps
* `blowout_speed_multiplier` | `float = 1`: Speed multiplier for blowout steps
* `touch_tip_source` | `bool = False`: When true the pipette tip will touch the top, inner sides of the source labware after aspiration
* `touch_tip_destination` | `bool = False`: When true the pipette tip will touch the top, inner sides of the destination labware after dispensing
* `blow_out` | `bool = False`: Defines whether a blowout step will occur
* `blowout_location` | `str = "destination_well"`: Defines where the blowout should occur - ignored if `blow_out` is `False`
* `move_after_dispense` | `str = None`: Defines if the pipette should move to the `"well_top"` or `"well_bottom"` after dispensing, but before any blowout occurs - if `None` then no movement occurs


**Behaviour:**

This function determines which aliquots should be used as the source location for the liquid transfer events specified by `transfer_liquids` and `destinations`. This information is then passed on to [`BiomationScripter.transfer_liquids`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-transfer_liquids) to perform the liquid handling actions.

If `Aliquot_Volumes` isn't `None`, then volume checking will occur and an error will be raised if there is not enough volume across all aliquots to perform all liquid handling actions. If `Aliquot_Volumes` is a single float, this volume will be used for all aliquots. If `Aliquot_Volumes` is a list of floats with a length equal to the number of aliquots, each volumes specified will be used as the amount of liquid in the corresponding aliquot specified by `Aliquot_Locations`

If `Aliquot_Volumes` is left as `None`, then each aliquot will take turns at being the source location, and no volume checking will occur.

The `new_tip`, `mix_after`, and `mix_before` arguments are passed directly to the [`BiomationScripter.transfer_liquids`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-transfer_liquids) function.

### Function: [`get_labware_format`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function can be used to get the labware format (i.e. number of rows and columns) from an opentrons labware API name.

**Usage:**

`OTProto.get_labware_format(labware_api_name: str, custom_labware_dir = None)` returns `(n_rows: int, n_cols: int)`

**Arguments:**

* `labware_api_name` | `str`: Opentrons API name for the labware
* `custom_labware_dir` | `str`: Location of any custom labware - only required if simulating away from the OT2

**Behaviour:**

The function searches through the specified labware's definition file to determine the number of rows and columns, and then returns them. The return order is number or rows first, and then number of columns.

### Function: [`get_labware_well_capacity`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function can be used to get a labware's maximum well capacity from an opentrons labware API name.

**Usage:**

`OTProto.get_labware_well_capacity(labware_api_name: str, custom_labware_dir = None)` returns `float`

**Arguments:**
* `labware_api_name` | `str`: Opentrons API name for the labware
* `custom_labware_dir` | `str`: Location of any custom labware - only required if simulating away from the OT2

**Behaviour:**

The function searches through the specified labware's definition file to determine the maximum well capacity of the labware, and then returns it. Note that this function may yield unexpected results if the labware has wells with different capacities.

### Function: [`get_locations`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Converts well positions in a specified labware to [`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well) objects, which can be used to specify a source or destination location in Opentrons or OTProto liquid handling functions.

**Usage:**

`OTProto.get_locations(Labware: opentrons.protocol_api.labware.Labware, Wells: list[str]/str, Direction: str = None)` returns `list[opentrons.protocol_api.labware.Well]`

**Arguments:**

* `Labware` | [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware): Labware to generate locations for
* `Wells` | `list[str]/str`: The wells in the specified labware to convert to locations - this can either be a list of wells (`["A1", "D5", "E7"]`), or a well range (`"C2:E4"`)
* `Direction` | `str = None`: Used to specify the direction ("Horizontal" or "Vertical") to generate locations when a well range is specified - required when `Wells` is a well range, ignored when `Wells` is a list of wells - see [`BiomationScripter.well_range`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/BiomationScripter#function-well_range) for more information about how directionality works with well ranges

**Behaviour:**

This function converts a list of wells (or a range of wells) in a specified labware to a list of [`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well) objects (also called locations here). These locations can be used as the source or destination arguments in liquid handling functions such as the opentrons [`transfer`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext.transfer) function, or the OTProto [`transfer_liquids`]() and [`dispense_from_aliquots`]() functions.

If the specified wells are not present in the labware defined by the `Labware` argument, an error will raised. Also, if `Direction` is not specified when `Wells` is a well range, an error will be raised.

### Function: [`get_p1000`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the p1000 pipette from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object if that pipette has been loaded

**Usage:**

`OTProto.get_p1000(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**

Searches the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `protocol` argument for a p1000 pipette. If a p1000 single channel pipette has been loaded, it is returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object. If the pipette has not been loaded, `None` is returned.

### Function: [`get_p20`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the p20 pipette from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object if that pipette has been loaded

**Usage:**

`OTProto.get_p20(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**

Searches the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `protocol` argument for a p20 pipette. If a p20 single channel pipette has been loaded, it is returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object. If the pipette has not been loaded, `None` is returned.

### Function: [`get_p300`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the p300 pipette from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object if that pipette has been loaded

**Usage:**

`OTProto.get_p300(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**

Searches the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `protocol` argument for a p300 pipette. If a p300 single channel pipette has been loaded, it is returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object. If the pipette has not been loaded, `None` is returned.

### Function: [`get_pipette`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the specified Opentrons pipette as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object if that pipette has been loaded.

**Usage:**

`OTProto.get_pipette(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Pipette: str)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Pipette` | `str`: The pipette type to return - must be either `"p20"`, `"p300"`, or `"p1000"`

**Behaviour:**

This function calls the [`get_p20`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p20), [`get_p300`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p300), or [`get_p1000`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p1000) function depending on the argument supplied to `Pipette`, and returns the output.

The pipette will only be returned if that pipette type has been loaded to the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `Protocol` argument. If the pipette type is not present, `None` will be returned and no error will be raised.

If `Pipette` is not `"p20"`, `"p300"`, or `"p1000"`, then an error will be raised.

### Function: [`load_custom_labware`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function loads a custom labware from a specified `.json` labware file created using the [Opentrons Labware Creator](https://labware.opentrons.com/create/)

**Usage:**

`OTProto.load_custom_labware(parent: opentrons.protocol_api.contexts.ProtocolContext/opentrons.protocol_api.contexts.TemperatureModuleContext/opentrons.protocol_api.contexts.ThermocyclerContext/https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext, file: str, deck_position: int = None, label: str = None)` returns [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Arguments:**

* `parent` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext)/[`opentrons.protocol_api.contexts.TemperatureModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.TemperatureModuleContext)/[`opentrons.protocol_api.contexts.ThermocyclerContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ThermocyclerContext)/[`opentrons.protocol_api.contexts.MagneticModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext): Specifies onto what the labware should be loaded - `ProtocolContext` is used to load onto the Opentrons deck, and a `ModuleContext` is used to load the labware onto a hardware module (e.g. temperature module), rather than the deck
* `file` | `str`: The location of the `.json` labware file (should be the full path to the file, including the file name and file extension)
* `deck_position` | `int = None`: The deck position to load the labware to
* `label` | `str = None`: A human-readable name for the labware

**Behaviour:**

Labware defined by the labware file supplied by the `file` argument is loaded and returned as a [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) object. If the labware file cannot be found at the location specified by the `file` argument, an error will occur.

The object type supplied to `parent` determines whether the labware is loaded to the Opentrons deck (when `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object), or to one of the hardware modules (when `parent` is one of [`opentrons.protocol_api.contexts.TemperatureModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.TemperatureModuleContext)/[`opentrons.protocol_api.contexts.ThermocyclerContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ThermocyclerContext)/[`opentrons.protocol_api.contexts.MagneticModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext) object).

If `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object and `deck_position` is `None`, the next empty slot is used (retrieved using [`OTProto.next_empty_slot`](#function-next_empty_slot)). If `parent` is not a `ProtocolContext` object, then `deck_position` is ignored.

### Function: [`load_labware_from_layout`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Generates an [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) object from a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) object

**Usage:**

`OTProto.load_labware_from_layout(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Labware_Layout: BiomationScripter.Labware_Layout, deck_position: int = None, custom_labware_dir: str = None)` returns [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Labware_Layout` | [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout): The Layout object to be used as the template for generating the [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) object
* `deck_position` | `int = None`: An integer (from 1-11) stating which deck position the labware should be loaded on to - if no value is specified, the labware will be loaded onto the next available deck slot
* `custom_labware_dir` | `str = None`: Location of a directory where any custom labware definition files are stored - if not specified then `../custom_labware` will be used if custom labware is being used

**Behaviour:**

This function generates and loads an [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware), which can be used in Opentrons protocols, using a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) as the template. Any content stored in the `Labware_Layout.content` attribute will not be carried over to the `Labware` object.

For this function to work correctly, the `Labware_Layout` `type` attribute (`Labware_Layout.type`) MUST be the API name of the labware to be loaded. If the `type` attribute can not be found as a labware API name, an error will occur.

The `Labware_Layout.name` attribute is used as the label for the `Labware` object.

### Function: [`load_labware`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Loads labware (either custom or default) based on an API name

**Usage:**

`OTProto.load_labware(parent: opentrons.protocol_api.contexts.ProtocolContext/opentrons.protocol_api.contexts.TemperatureModuleContext/opentrons.protocol_api.contexts.ThermocyclerContext/https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext, labware_api_name: str, deck_position: int = None, custom_labware_dir label: str = None)` returns [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

See the [code snippet examples](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/docs/Example_Code_Snippets/OTProto/OTProto-load_labware-Function.ipynb) for example usage.

**Behaviour:**

The `load_labware` function firstly determines whether the labware type specified by `labware_api_name` is in the default list of labware, or if it is custom labware. If it is custom, then the [`load_custom_labware`](#function-load_custom_labware) function is called and used to load the labware. The `custom_labware_dir` argument is used to find the custom file location, and if it isn't specified then an error will be raised.


The object type supplied to `parent` determines whether the labware is loaded to the Opentrons deck (when `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object), or to one of the hardware modules (when `parent` is one of [`opentrons.protocol_api.contexts.TemperatureModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.TemperatureModuleContext)/[`opentrons.protocol_api.contexts.ThermocyclerContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ThermocyclerContext)/[`opentrons.protocol_api.contexts.MagneticModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext) object).

If `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object and `deck_position` is `None`, the next empty slot is used (retrieved using [`OTProto.next_empty_slot`](#function-next_empty_slot)). If `parent` is not a `ProtocolContext` object, then `deck_position` is ignored.

### Function: [`load_pipettes_and_tips`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Loads a specified pipette, and creates tip racks which are assigned to that pipette and loads to the deck

**Usage:**

`OTProto.load_pipettes_and_tips(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Pipette_Type: str, Pipette_Position: str, Tip_Type: str, Number_Tips_Required: int = None, Starting_Tip: str = "A1")` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) and [`list[opentrons.protocol_api.labware.Labware]`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Pipette_Type` | `str`: The API name for the pipette type to load (see [here](https://docs.opentrons.com/v2/new_pipette.html#pipette-models) for pipette types)
* `Pipette_Position` | `str`: The position in which the pipette is loaded (either `"left"` or `"right"`)
* `Tip_Type` | `str`: The API name for the tip type to load
* `Number_Tips_Required` | `int = None`: The number of `Tip_Type` tips required in the protocol
* `starting_tip_position` | `str = "A1"`: The first available tip in the first tip rack

**Behaviour:**

This function will load a pipette of type `pipette_type` into position `Pipette_Position` on the Opentrons. Tip racks of type `Tip_Type` are then loaded to the next empty slot of the Opentrons deck (uses [`OTProto.next_empty_slot`](#function-next_empty_slot)) and assigns the tip rack to be used by the pipette just loaded.

If `Number_Tips_Required = None`, then a single tip rack is loaded. If a number is supplied to `Number_Tips_Required`, the [`OTProto.tip_racks_needed`](#function-tip_racks_needed) function is used to determine the number of tip racks to load (`Number_Tips_Required` and `starting_tip_position` are passed directly to the [`OTProto.tip_racks_needed`](#function-tip_racks_needed) function).

The `starting_tip_position` is used to allow the pipette to know where to begin taking tips from.

This function returns two variables: an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object which stores information about the pipette and can be used to call liquid handling methods from, and a list of the loaded tip racks as [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) objects.

### Function: [`next_empty_slot`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function gets the next empty slot on the Opentrons deck for the current protocol.

**Usage:**

`OTProto.next_empty_slot(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns `int`

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**

This function gets the `deck` attribute from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object and iterates through each slot on the deck. If there is no labware loaded onto a slot, that slot number is returned as an `int`. If no empty slots are left, and error is returned.

### Function: [`select_pipette_by_volume`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Selects the most appropriate loaded pipette for a specified transfer volume.

**Usage:**

`OTProto.select_pipette_by_volume(protocol: opentrons.protocol_api.contexts.ProtocolContext, Volume: float)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Volume` | `float`: The transfer volume (in microlitres)

**Behaviour:**

This function uses the [`get_p20`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p20), [`get_p300`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p300), or [`get_p1000`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p1000) functions to determine which pipettes have been loaded to the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) supplied to the `Protocol` argument. From the loaded pipettes, the most appropriate pipette to perform the transfer volume specified by `Volume` will be returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object.

Note that this function only returns the selected pipette; the transfer action is NOT performed.

Pipettes are selected based on whether or not the transfer volume lies within that pipette's volume range. In the case of overlapping volume ranges, the pipette with a lower volume range will be selected to ensure the highest accuracy level (e.g. if both a p20 and p300 are loaded and `Volume = 20`, the p20 will be returned even though the p300 can transfer 20 uL).

If `Volume` is above the volume range of the largest pipette, the pipette with the largest volume range will be selected (e.g. if a p20 and p300 are loaded and `Volume = 400`, the p300 will be selected). Note that using a pipette to transfer a volume of liquid higher than its maximum volume range will result in the transfer action being split.

If `Volume` is below 1 uL, an error will be raised as the Opentrons cannot pipette below this volume.

If not pipettes are loaded which are suitable for the specified volume, an error will be raised.

### Function: [`shuffle_locations`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Takes a list and shuffles the elements within. This generates a message to the robot showing the previous order of the list and the new order of the list. If an output directory is specified, this function will write the lists to a .csv file.

**Usage:**

`OTProto.shuffle_locations(Locations: list[], outdir: str = None, outfile: str = "Locations")` returns `list[]`

**Arguments:**

* `Locations` | `list[]`: A list containing any elements. Typically, this should contain [`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well) objects. May also be invoked upon a list of Wells as strings.
* `outdir` | `str = None`: The path to the output directory where the .csv file will be written. Recommended location is "/data/user_storage/<USER_DIRECTORY>". If this is not specified, the .csv file will not be created.
* `outfile` | `str = "Locations"`: The name that will be used for the .csv file. If this is not specified, the .csv file will be named "Locations" by default.

**Behaviour:**

This function takes a list and shuffles any elements contained within. The new locations will be logged by the robot and shown to the user via the application command line. If an output directory is specified, this information will be written to a .csv file.

### Function: [`tip_racks_needed`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Determines the number of tip racks needed based on the number of tips needed, and the first tip available for partially used tip racks

**Usage:**

`OTProto.tip_racks_needed(tips_needed: int, starting_tip_position: str = "A1")` returns `int`

**Arguments:**

* `tips_needed` | `int`: Number of tips needed
* `starting_tip_position` | `str = "A1"`: The first available tip in the first tip rack

**Behaviour:**

`tip_racks_needed` returns how many tip racks are needed based on the number of tips needed (`tips_needed` argument). Only one type of tip should be specified. If two or more tip types are to be used, call this function for each tip type.

The `starting_tip_position` refers to the next available tip position in partially-used racks. All subsequent tip racks following the first rack are assumed to be full. If the tip position doesn't exist in the tip rack, and error is raised.

Note that this function doesn't load the tip racks, it just returns the number of tip racks required.

### Function: [`transfer_liquids`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Transfers liquids from source locations to destination locations

**Usage:**

`
OTProto.transfer_liquids(
  protocol: opentrons.protocol_api.contexts.ProtocolContext,
  Transfer_Volumes: list[float]/float,
  Source_Locations: list[opentrons.protocol_api.labware.Well]/opentrons.protocol_api.labware.Well,
  Destination_Locations: list[opentrons.protocol_api.labware.Well]/opentrons.protocol_api.labware.Well,
  new_tip: bool = True,
  mix_after: tuple(int, float/int/str) = None,
  mix_before: tuple(int, float/int/str) = None,
  mix_speed_multiplier: float = 1,
  aspirate_speed_multiplier: float = 1,
  dispense_speed_multiplier: float = 1,
  blowout_speed_multiplier: float = 1,
  touch_tip_source: bool = False,
  touch_tip_destination: bool = False,
  blow_out: bool = False,
  blowout_location: str = "destination well",
  move_after_dispense: str = None
)
`
returns `None`


**Arguments:**

* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Transfer_Volumes` | `list[float]/float`: A list of transfer volumes (in microlitres), or a single transfer volume
* `Source_Locations` | `list[opentrons.protocol_api.labware.Well]`/[`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well): A list of locations which liquid will be transferred from (can also be a single location)
* `Destination_Locations` | `list[opentrons.protocol_api.labware.Well]`/[`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well): A list of locations which liquid will be transferred to (can also be a single location)
* `new_tip` | `bool = True`: A boolean which determines whether a new tip is used for every transfer specified (`True`), or if one tip is used for all transfers (`False`)
* `mix_after` | `tuple(int, int/float/str) = None`: Specifies mixing event after dispensing into the destination location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)
* `mix_before` | `tuple(int, int/float/str) = None`: Specifies mixing event before aspirating from the source location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)
* `mix_speed_multiplier` | `float = 1`: Speed multiplier for mixing steps
* `aspirate_speed_multiplier` | `float = 1`: Speed multiplier for aspirate steps
* `dispense_speed_multiplier` | `float = 1`: Speed multiplier for dispense steps
* `blowout_speed_multiplier` | `float = 1`: Speed multiplier for blowout steps
* `touch_tip_source` | `bool = False`: When true the pipette tip will touch the top, inner sides of the source labware after aspiration
* `touch_tip_destination` | `bool = False`: When true the pipette tip will touch the top, inner sides of the destination labware after dispensing
* `blow_out` | `bool = False`: Defines whether a blowout step will occur
* `blowout_location` | `str = "destination_well"`: Defines where the blowout should occur - ignored if `blow_out` is `False`
* `move_after_dispense` | `str = None`: Defines if the pipette should move to the `"well_top"` or `"well_bottom"` after dispensing, but before any blowout occurs - if `None` then no movement occurs

**Behaviour:**

The `transfer_liquids` function is intended to generate liquid transfer actions for the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied by `Protocol`. A liquid transfer action is generated for each element in the list of volumes specified by the `Transfer_Volumes` argument. The source for the transfer is determined by using the element in `Source_Locations` with the same index as the volume specified in `Transfer_Volumes`, and the destination is determined in the same way, but using `Destination_Locations`. So for example, if `Transfer_Volumes = [20, 100, 400]`, `Source_Locations = [Source_1, Source_1, Source_2]`, and `Destination_Locations = [Dest_1, Dest_2, Dest_3]`, then the following three transfer actions will be generated:
* Transfer 20 uL from `Source_1` to `Dest_1`
* Transfer 100 uL from `Source_1` to `Dest_2`
* Transfer 400 uL from `Source_2` to `Dest_3`

The `new_tip` argument determines whether a new tip is used for each transfer action, or if the same tip is used for all transfers. The `new_tip`, `mix_before`, and `mix_after` arguments apply to all transfer actions. If different transfers require different behaviours, it is recommended to split the transfers and call the `transfer_liquids` function for each scenario.

For each transfer action, [`select_pipette_by_volume`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-select_pipette_by_volume) is used to determine the best pipette to use from those which have been loaded. If no suitable pipettes are present, an error will be raised. If the transfer volume is larger than the volume range of the largest pipette loaded, the transfer action is split into two. For example, if a p20 and p300 are loaded, and a transfer volume of 400 uL is specified, two transfer actions of 200uL will occur. If `new_tip = True`, a new tip will be used for both transfer actions. If `new_tip = False`, the same tip will be used.

If the length of `Transfer_Volumes`, `Source_Locations`, and `Destination_Locations` are not all identical, an error will be rasied.

It is possible to supply a single transfer volume, source location, and destination location without making them into a list (e.g. `Transfer_Volumes = 20`, `Source_Locations = source_1`, and `Destination_Locations = dest_1`.


---

# Using OTProto.Templates

See the full documentation [here](OTProto_Templates.md)


---
# Simulating Protocols
Protocols can be simulated on any computer which has the [Opentrons API installed](https://docs.opentrons.com/v2/writing.html#installing). There are two methods of simulating protocols written using BiomationScripter.

## Within the python script:
This method of simulating the protocol requires a slight addition to the python script, and may be useful when writing protocols using Jupyter Notebook or in an interactive environment.

1. Add the following lines to the end of your python script:

    ```python
    from opentrons import simulate as OT2 # Import the simulation module from the API
    protocol = OT2.get_protocol_api('2.10') # Create the protocol object with the correct API version
    protocol.home() # Simulating homing the pipetting head
    run(protocol) # Call your 'run' function to run the protocol
    # Print out each action that the opentrons will perform when running your protocol
    for line in protocol.commands():
        print(line)
    ```

2. Save and run this modified script.

**IMPORTANT** Make sure that these changes are reverted before uploading to the Opentrons, otherwise you will get errors.

## From the command line:
This method of simulating the protocol does not require the python script to be modified.

1. Follow the instructions from the [Opentrons API documentation](https://docs.opentrons.com/v2/writing.html#simulating-your-scripts).

**Note** For protocols which use template classes, give the `Simulate` variable as `False`, or simply don't declare it, when simulating using this method.
