# BiomationScripter - OTProto
---
[Overview](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto#feature-overview) | [Setting up the OT-2](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto#setting-up-the-ot-2-to-work-with-biomationscripter) | [Using OTProto](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto#using-otproto) | [Functions](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#functions) | [Using OTProto Templates](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto#otprototemplates) | [All Templates](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto#templates) | [Simulating Protocols](https://github.com/intbio-ncl/BiomationScripter/wiki/OTProto#simulating-protocols)

---
## Feature Overview
OTProto is a module within the BiomationScripter package which contains tools specifically aimed at assisting with scripting protocols for the Opentrons-2. This module makes use of the [OT2 API V2](https://docs.opentrons.com/v2/index.html) python protocol.

OTProto contains two submodules:
* [**OTProto:**](#using-otproto) A set of functions and classes which abstract out some parts of the protocol writing, such as determining how many tips are required, and switching loading custom labware
* [**OTProto.Templates:**](#using-otprototemplates) A set of classes which generate OT-2 instructions for common protocols, such as plasmid purification and transformation, based on user inputs

If you are planning on using the Opentrons to automate common protocols, such as transformation, there may be a pre-written OTProto template available. A list of currently available templates can be found [here](#template-classes).

If you are planning on automating a protocol which you will use many times, but with slightly different variations/inputs, it may be helpful to create your own OTProto template. A walkthrough explaining how this can be done can be found [here](#creating-custom-otprototemplates).

If you are planning to automate a protocol for which there are no existing templates, and that protocol will only be repeated identically (or not at all), it may be best to not write a template. In this case, the [general BiomationScripter tools](https://github.com/intbio-ncl/BiomationScripterLib/wiki/BiomationScripter) and [OTProto tools](#using-otproto) can be used to help write the protocol.

---

## Setting up the OT-2 to work with BiomationScripter
Due to large amounts of the OT-2's onboard computer being read only, the BiomationScripter package can not be installed as usual. Instead follow the instructions below to get set up.

1. Create a new directory called `Packages` in the writable section of the OT-2's onboard computer
     * `/var/lib/jupyter/notebooks/` is suggested for convenience in the case of using Jupyter Notebook to run the OT2
2. Clone the [BiomationScripter repo](https://github.com/intbio-ncl/BiomationScripter) into this new directory
3. The following code will need to be added to start of every protocol you wish to use BiomationScripter in:
     ```python
     import sys
     sys.path.insert(0, "<Directory>")
     ```
     Replace `<Directory>` with the path you cloned BiomationScripter into (e.g. `/var/lib/jupyter/notebooks/Packages/BiomationScripterLib`)

---

## Using OTProto
Begin by importing the OTProto module:
```python
import BiomationScripter.OTProto as OTProto
```


### Functions

[`get_locations`](#function-get_locations)
[`get_pipette`](#function-get_pipette)
[`get_p20`](#function-get_p20)
[`get_p300`](#function-get_p300)
[`get_p1000`](#function-get_p1000)
[`select_pipette_by_volume`](#function-select_pipette_by_volume)
[`transfer_liquids`](#function-transfer_liquids)
[`dispense_from_aliquots`](#function-dispense_from_aliquots)
[`next_empty_slot`](#function-next_empty_slot)
[`load_custom_labware`](#function-load_custom_labware)
[`load_labware`](#function-load_labware)
[`calculate_and_load_labware`](#function-calculate_and_load_labware)
[`load_labware_from_layout`](#function-load_labware_from_layout)
[`calculate_tips_needed`](#function-calculate_tips_needed)
[`tip_racks_needed`](#function-tip_racks_needed)
[`load_pipettes_and_tips`](#function-load_pipettes_and_tips)

<br>
<br>

### Function: [`get_locations`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Converts well positions in a specified labware to [`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well) objects, which can be used to specify a source or destination location in Opentrons or OTProto liquid handling functions.

**Usage:**\
`OTProto.get_locations(Labware: opentrons.protocol_api.labware.Labware, Wells: list[str]/str, Direction: str = None)` returns `list[opentrons.protocol_api.labware.Well]`

**Arguments:**
* `Labware` | [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware): Labware to generate locations for
* `Wells` | `list[str]/str`: The wells in the specified labware to convert to locations - this can either be a list of wells (`["A1", "D5", "E7"]`), or a well range (`"C2:E4"`)
* `Direction` | `str = None`: Used to specify the direction ("Horizontal" or "Vertical") to generate locations when a well range is specified - required when `Wells` is a well range, ignored when `Wells` is a list of wells - see [`BiomationScripter.well_range`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/BiomationScripter#function-well_range) for more information about how directionality works with well ranges

**Behaviour:**\
This function converts a list of wells (or a range of wells) in a specified labware to a list of [`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well) objects (also called locations here). These locations can be used as the source or destination arguments in liquid handling functions such as the opentrons [`transfer`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext.transfer) function, or the OTProto [`transfer_liquids`]() and [`dispense_from_aliquots`]() functions.

If the specified wells are not present in the labware defined by the `Labware` argument, an error will raised. Also, if `Direction` is not specified when `Wells` is a well range, an error will be raised.



### Function: [`get_pipette`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the specified Opentrons pipette as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object if that pipette has been loaded.

**Usage:**\
`OTProto.get_pipette(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Pipette: str)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Pipette` | `str`: The pipette type to return - must be either `"p20"`, `"p300"`, or `"p1000"`

**Behaviour:**\
This function calls the [`get_p20`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p20), [`get_p300`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p300), or [`get_p1000`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p1000) function depending on the argument supplied to `Pipette`, and returns the output.

The pipette will only be returned if that pipette type has been loaded to the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `Protocol` argument. If the pipette type is not present, `None` will be returned and no error will be raised.

If `Pipette` is not `"p20"`, `"p300"`, or `"p1000"`, then an error will be raised.


### Function: [`get_p20`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the p20 pipette from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object if that pipette has been loaded

**Usage:**\
`OTProto.get_p20(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**\
Searches the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `protocol` argument for a p20 pipette. If a p20 single channel pipette has been loaded, it is returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object. If the pipette has not been loaded, `None` is returned.

### Function: [`get_p300`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the p300 pipette from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object if that pipette has been loaded

**Usage:**\
`OTProto.get_p300(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**\
Searches the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `protocol` argument for a p300 pipette. If a p300 single channel pipette has been loaded, it is returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object. If the pipette has not been loaded, `None` is returned.

### Function: [`get_p1000`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Returns the p1000 pipette from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object if that pipette has been loaded

**Usage:**\
`OTProto.get_p1000(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**\
Searches the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied to the `protocol` argument for a p1000 pipette. If a p1000 single channel pipette has been loaded, it is returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object. If the pipette has not been loaded, `None` is returned.


### Function: [`select_pipette_by_volume`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Selects the most appropriate loaded pipette for a specified transfer volume.

**Usage:**\
`OTProto.select_pipette_by_volume(protocol: opentrons.protocol_api.contexts.ProtocolContext, Volume: float)` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Volume` | `float`: The transfer volume (in microlitres)

**Behaviour:**\
This function uses the [`get_p20`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p20), [`get_p300`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p300), or [`get_p1000`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-get_p1000) functions to determine which pipettes have been loaded to the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) supplied to the `Protocol` argument. From the loaded pipettes, the most appropriate pipette to perform the transfer volume specified by `Volume` will be returned as an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object.

Note that this function only returns the selected pipette; the transfer action is NOT performed.

Pipettes are selected based on whether or not the transfer volume lies within that pipette's volume range. In the case of overlapping volume ranges, the pipette with a lower volume range will be selected to ensure the highest accuracy level (e.g. if both a p20 and p300 are loaded and `Volume = 20`, the p20 will be returned even though the p300 can transfer 20 uL).

If `Volume` is above the volume range of the largest pipette, the pipette with the largest volume range will be selected (e.g. if a p20 and p300 are loaded and `Volume = 400`, the p300 will be selected). Note that using a pipette to transfer a volume of liquid higher than its maximum volume range will result in the transfer action being split.

If `Volume` is below 1 uL, an error will be raised as the Opentrons cannot pipette below this volume.

If not pipettes are loaded which are suitable for the specified volume, an error will be raised.


### Function: [`transfer_liquids`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Transfers liquids from source locations to destination locations

**Usage:**\
`OTProto.transfer_liquids(protocol: opentrons.protocol_api.contexts.ProtocolContext, Transfer_Volumes: list[float]/float, Source_Locations: list[opentrons.protocol_api.labware.Well]/opentrons.protocol_api.labware.Well, Destination_Locations: list[opentrons.protocol_api.labware.Well]/opentrons.protocol_api.labware.Well, new_tip: bool = True, mix_after: tuple(int, float/int/str) = None, mix_before: tuple(int, float/int/str) = None)` returns `None`


**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Transfer_Volumes` | `list[float]/float`: A list of transfer volumes (in microlitres), or a single transfer volume
* `Source_Locations` | `list[opentrons.protocol_api.labware.Well]`/[`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well): A list of locations which liquid will be transferred from (can also be a single location)
* `Destination_Locations` | `list[opentrons.protocol_api.labware.Well]`/[`opentrons.protocol_api.labware.Well`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Well): A list of locations which liquid will be transferred to (can also be a single location)
* `new_tip` | `bool = True`: A boolean which determines whether a new tip is used for every transfer specified (`True`), or if one tip is used for all transfers (`False`)
* `mix_after` | `tuple(int, int/float/str) = None`: Specifies mixing event after dispensing into the destination location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)
* `mix_before` | `tuple(int, int/float/str) = None`: Specifies mixing event before aspirating from the source location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)


**Behaviour:**\
The `transfer_liquids` function is intended to generate liquid transfer actions for the [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object supplied by `Protocol`. A liquid transfer action is generated for each element in the list of volumes specified by the `Transfer_Volumes` argument. The source for the transfer is determined by using the element in `Source_Locations` with the same index as the volume specified in `Transfer_Volumes`, and the destination is determined in the same way, but using `Destination_Locations`. So for example, if `Transfer_Volumes = [20, 100, 400]`, `Source_Locations = [Source_1, Source_1, Source_2]`, and `Destination_Locations = [Dest_1, Dest_2, Dest_3]`, then the following three transfer actions will be generated:
* Transfer 20 uL from `Source_1` to `Dest_1`
* Transfer 100 uL from `Source_1` to `Dest_2`
* Transfer 400 uL from `Source_2` to `Dest_3`

The `new_tip` argument determines whether a new tip is used for each transfer action, or if the same tip is used for all transfers. The `new_tip`, `mix_before`, and `mix_after` arguments apply to all transfer actions. If different transfers require different behaviours, it is recommended to split the transfers and call the `transfer_liquids` function for each scenario.

For each transfer action, [`select_pipette_by_volume`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-select_pipette_by_volume) is used to determine the best pipette to use from those which have been loaded. If no suitable pipettes are present, an error will be raised. If the transfer volume is larger than the volume range of the largest pipette loaded, the transfer action is split into two. For example, if a p20 and p300 are loaded, and a transfer volume of 400 uL is specified, two transfer actions of 200uL will occur. If `new_tip = True`, a new tip will be used for both transfer actions. If `new_tip = False`, the same tip will be used.

If the length of `Transfer_Volumes`, `Source_Locations`, and `Destination_Locations` are not all identical, an error will be rasied.

It is possible to supply a single transfer volume, source location, and destination location without making them into a list (e.g. `Transfer_Volumes = 20`, `Source_Locations = source_1`, and `Destination_Locations = dest_1`.


### Function: [`dispense_from_aliquots`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function can be used to dispense varying amounts of liquid from a set of aliquots to a list of destination locations

**Usage:**\
`OTProto.dispense_from_aliquots(protocol: opentrons.protocol_api.contexts.ProtocolContext, Transfer_Volumes: list[float], Aliquot_Source_Locations: list[opentrons.protocol_api.labware.Well], Destinations: list[opentrons.protocol_api.labware.Well], Aliquot_Volumes: list[float]/float = None, new_tip: bool = True, mix_after: tuple(int, float/int/str) = None, mix_before: tuple(int, float/int/str) = None)` returns `None`

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Transfer_Volumes` | `list[float]: A list of transfer volumes (in microlitres)
* `Aliquot_Source_Locations` | `list[opentrons.protocol_api.labware.Well]: A list of locations for each of the aliquots - to be used as the potential source locations
* `Destinations` | `list[opentrons.protocol_api.labware.Well]: A list of locations which liquid will be transferred to
* `Aliquot_Volumes` | `list[float]/float = None`: A list of volumes relating to the amount of liquid in each aliquot specified by `Aliquot_Source_Locations` - if a single float is specified this volume will be used for all aliquots
* `new_tip` | `bool = True`: A boolean which determines whether a new tip is used for every transfer specified (`True`), or if one tip is used for all transfers (`False`)
* `mix_after` | `tuple(int, int/float/str) = None`: Specifies mixing event after dispensing into the destination location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)
* `mix_before` | `tuple(int, int/float/str) = None`: Specifies mixing event before aspirating from the source location - if `None`, no mixing occurs - first element in the tuple specifies the number of mixing iterations (aspirate up and down) to occur, and the second element specifies the volume to use in the mixing event (either a volume in microlitres, or the keyword `"transfer_volume"`, which uses the transfer volume as the mixing volume)

**Behaviour:**\
This function determines which aliquots should be used as the source location for the liquid transfer events specified by `transfer_liquids` and `destinations`. This information is then passed on to [`BiomationScripter.transfer_liquids`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-transfer_liquids) to perform the liquid handling actions.

If `Aliquot_Volumes` isn't `None`, then volume checking will occur and an error will be raised if there is not enough volume across all aliquots to perform all liquid handling actions. If `Aliquot_Volumes` is a single float, this volume will be used for all aliquots. If `Aliquot_Volumes` is a list of floats with a length equal to the number of aliquots, each volumes specified will be used as the amount of liquid in the corresponding aliquot specified by `Aliquot_Locations`

If `Aliquot_Volumes` is left as `None`, then each aliquot will take turns at being the source location, and no volume checking will occur.

The `new_tip`, `mix_after`, and `mix_before` arguments are passed directly to the [`BiomationScripter.transfer_liquids`](https://github.com/intbio-ncl/BiomationScripterLib/wiki/OTProto#function-transfer_liquids) function.

### Function: [`next_empty_slot`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function gets the next empty slot on the Opentrons deck for the current protocol.

**Usage:**\
`OTProto.next_empty_slot(protocol: opentrons.protocol_api.contexts.ProtocolContext)` returns `int`

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol

**Behaviour:**\
This function gets the `deck` attribute from the supplied [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object and iterates through each slot on the deck. If there is no labware loaded onto a slot, that slot number is returned as an `int`. If no empty slots are left, and error is returned.


### Function: [`load_custom_labware`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function loads a custom labware from a specified `.json` labware file created using the [Opentrons Labware Creator](https://labware.opentrons.com/create/)

**Usage:**\
`OTProto.load_custom_labware(parent: opentrons.protocol_api.contexts.ProtocolContext/opentrons.protocol_api.contexts.TemperatureModuleContext/opentrons.protocol_api.contexts.ThermocyclerContext/https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext, file: str, deck_position: int = None, label: str = None)` returns [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Arguments:**
* `parent` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext)/[`opentrons.protocol_api.contexts.TemperatureModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.TemperatureModuleContext)/[`opentrons.protocol_api.contexts.ThermocyclerContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ThermocyclerContext)/[`opentrons.protocol_api.contexts.MagneticModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext): Specifies onto what the labware should be loaded - `ProtocolContext` is used to load onto the Opentrons deck, and a `ModuleContext` is used to load the labware onto a hardware module (e.g. temperature module), rather than the deck
* `file` | `str`: The location of the `.json` labware file (should be the full path to the file, including the file name and file extension)
* `deck_position` | `int = None`: The deck position to load the labware to
* `label` | `str = None`: A human-readable name for the labware

**Behaviour:**\
Labware defined by the labware file supplied by the `file` argument is loaded and returned as a [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) object. If the labware file cannot be found at the location specified by the `file` argument, an error will occur.

The object type supplied to `parent` determines whether the labware is loaded to the Opentrons deck (when `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object), or to one of the hardware modules (when `parent` is one of [`opentrons.protocol_api.contexts.TemperatureModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.TemperatureModuleContext)/[`opentrons.protocol_api.contexts.ThermocyclerContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ThermocyclerContext)/[`opentrons.protocol_api.contexts.MagneticModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext) object).

If `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object and `deck_position` is `None`, the next empty slot is used (retrieved using [`OTProto.next_empty_slot`](#function-next_empty_slot)). If `parent` is not a `ProtocolContext` object, then `deck_position` is ignored.


### Function: [`load_labware`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Loads labware (either custom or default) based on an API name

**Usage:**\
`OTProto.load_labware(parent: opentrons.protocol_api.contexts.ProtocolContext/opentrons.protocol_api.contexts.TemperatureModuleContext/opentrons.protocol_api.contexts.ThermocyclerContext/https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext, labware_api_name: str, deck_position: int = None, custom_labware_dir label: str = None)` returns [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Behaviour:**\
The `load_labware` function firstly determines whether the labware type specified by `labware_api_name` is in the default list of labware, or if it is custom labware. If it is custom, then the [`load_custom_labware`](#function-load_custom_labware) function is called and used to load the labware. The `custom_labware_dir` argument is used to find the custom file location, and if it isn't specified then an error will be raised.


The object type supplied to `parent` determines whether the labware is loaded to the Opentrons deck (when `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object), or to one of the hardware modules (when `parent` is one of [`opentrons.protocol_api.contexts.TemperatureModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.TemperatureModuleContext)/[`opentrons.protocol_api.contexts.ThermocyclerContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ThermocyclerContext)/[`opentrons.protocol_api.contexts.MagneticModuleContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.MagneticModuleContext) object).

If `parent` is an [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext) object and `deck_position` is `None`, the next empty slot is used (retrieved using [`OTProto.next_empty_slot`](#function-next_empty_slot)). If `parent` is not a `ProtocolContext` object, then `deck_position` is ignored.

### Function: [`calculate_and_load_labware`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function calculates how many of a certain labware type is required for a protocol, and then loads the labware to the deck

**Usage:**\
`OTProto.calculate_and_load_labware(protocol: opentrons.protocol_api.contexts.ProtocolContext, labware_api_name: str, wells_required: int, custom_labware_dir: str = None)` returns `list[opentrons.protocol_api.labware.Labware]` and `list[opentrons.protocol_api.labware.Well]`

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `labware_api_name` | `str`: The Opentrons API name for the labware to be loaded
* `wells_required` | `int`: The number of wells which need to be available for use
* `custom_labware_dir` | `str = None`: Location of a directory where any custom labware definition files are stored

**Behaviour:**\
This function loads a set of labware, where the type is defined by `labware_api_name`, and the amount of labware loaded is defined by the number of wells required (as supplied by the `wells_required` argument).

This function first calls [`BiomationScripter.OTProto.load_labware`](#function-load_labware) to load a single copy of the labware, as it is assumed that at least one of the labware will always be required. The labware is loaded into the next empty slot on the deck. If not slots remain, an error is raised. This first loaded labware is then used to determine how many wells the labware contains, and therefore how many copies of the labware is required based on the number of wells needed (`wells_required`). If more than one labware is required, these extra copies are then also loaded onto the next empty slot(s). If at any point there are no more free slots, an error is raised.

Once all required labware has been loaded, a list of well locations ([`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) is generated. This list of wells locations is equal in length to the number of `wells_required`, and can be used to determine which wells can be used in each of the loaded labware.

The function then returns two variables: the list of loaded labware, and the list of well locations.

The `custom_labware_dir` and `labware_api_name` arguments are passed directly to [`BiomationScripter.OTProto.load_labware`](#function-load_labware).



### Function: [`load_labware_from_layout`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Generates an [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) object from a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) object

**Usage:**\
`OTProto.load_labware_from_layout(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Plate_Layout: BiomationScripter.Labware_Layout, deck_position: int = None, custom_labware_dir: str = None)` returns [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Plate_Layout` | [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout): The Layout object to be used as the template for generating the [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) object
* `deck_position` | `int = None`: An integer (from 1-11) stating which deck position the labware should be loaded on to - if no value is specified, the labware will be loaded onto the next available deck slot
* `custom_labware_dir` | `str = None`: Location of a directory where any custom labware definition files are stored - if not specified then `../custom_labware` will be used if custom labware is being used

**Behaviour:**\
This function generates and loads an [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware), which can be used in Opentrons protocols, using a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) as the template. Any content stored in the `Labware_Layout.content` attribute will not be carried over to the `Labware` object.

For this function to work correctly, the `Labware_Layout` `type` attribute (`Labware_Layout.type`) MUST be the API name of the labware to be loaded. If the `type` attribute can not be found as a labware API name, an error will occur.

The `Labware_Layout.name` attribute is used as the label for the `Labware` object.


### Function: [`calculate_tips_needed`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
This function determines how many tips of each size (20uL, 300uL, and 1000uL) are required for a set of liquid transfer actions, based on the pipette types present and whether a new tip should be used for each transfer or not

**Usage:**\
`OTProto.calculate_tips_needed(Protocol: opentrons.protocol_api.contexts.ProtocolContext, transfers: list[float], new_tip: bool = True)` returns `float` and `float` and `float`

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `transfers` | `list[float]`: List of volumes to be transferred by the Opentrons
* `new_tip` | `bool = True`: A boolean which determines whether a new tip is used for every transfer specified (`True`), or if one tip is used for all transfers (`False`)

**Behaviour:**\
For each volume in the list passed to `transfers`, the [`select_pipette_by_volume`](#function-select_pipette_by_volume) function is used to determine which pipette size should be used to perform that transfer, based on the pipette type(s) loaded. It is then determined whether that transfer can be completed in one step (e.g. a p300 transferring 100 uL), or two steps (e.g. a p300 transfering 400 uL in 2*200 uL steps). From this information, along with the `new_tip` argument, it is determined how many tips are needed for that transfer, and what tip size is required.

Once all transfer volumes have been iterated through, the function returns the number of each tip type needed as an `int` in the order of 20uL, 300uL, and 1000uL.


### Function: [`tip_racks_needed`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Determines the number of tip racks needed based on the number of tips needed, and the first tip available for partially used tip racks

**Usage:**\
`OTProto.tip_racks_needed(tips_needed: int, starting_tip_position: str = "A1")` returns `int`

**Arguments:**
* `tips_needed` | `int`: Number of tips needed
* `starting_tip_position` | `str = "A1"`: The first available tip in the first tip rack

**Behaviour:**\
`tip_racks_needed` returns how many tip racks are needed based on the number of tips needed (`tips_needed` argument). Only one type of tip should be specified. If two or more tip types are to be used, call this function for each tip type.

The `starting_tip_position` refers to the next available tip position in partially-used racks. All subsequent tip racks following the first rack are assumed to be full. If the tip position doesn't exist in the tip rack, and error is raised.

Note that this function doesn't load the tip racks, it just returns the number of tip racks required.

### Function: [`load_pipettes_and_tips`](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/__init__.py)
Loads a specified pipette, and creates tip racks which are assigned to that pipette and loads to the deck

**Usage:**\
`OTProto.load_pipettes_and_tips(Protocol: opentrons.protocol_api.contexts.ProtocolContext, Pipette_Type: str, Pipette_Position: str, Tip_Type: str, Number_Tips_Required: int = None, Starting_Tip: str = "A1")` returns [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) and [`list[opentrons.protocol_api.labware.Labware]`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware)

**Arguments:**
* `Protocol` | [`opentrons.protocol_api.contexts.ProtocolContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.ProtocolContext): The protocol object which is used by the Opentrons API to encapsulate all information relating to the current protocol
* `Pipette_Type` | `str`: The API name for the pipette type to load (see [here](https://docs.opentrons.com/v2/new_pipette.html#pipette-models) for pipette types)
* `Pipette_Position` | `str`: The position in which the pipette is loaded (either `"left"` or `"right"`)
* `Tip_Type` | `str`: The API name for the tip type to load
* `Number_Tips_Required` | `int = None`: The number of `Tip_Type` tips required in the protocol
* `starting_tip_position` | `str = "A1"`: The first available tip in the first tip rack

**Behaviour:**\
This function will load a pipette of type `pipette_type` into position `Pipette_Position` on the Opentrons. Tip racks of type `Tip_Type` are then loaded to the next empty slot of the Opentrons deck (uses [`OTProto.next_empty_slot`](#function-next_empty_slot)) and assigns the tip rack to be used by the pipette just loaded.

If `Number_Tips_Required = None`, then a single tip rack is loaded. If a number is supplied to `Number_Tips_Required`, the [`OTProto.tip_racks_needed`](#function-tip_racks_needed) function is used to determine the number of tip racks to load (`Number_Tips_Required` and `starting_tip_position` are passed directly to the [`OTProto.tip_racks_needed`](#function-tip_racks_needed) function).

The `starting_tip_position` is used to allow the pipette to know where to begin taking tips from.

This function returns two variables: an [`opentrons.protocol_api.contexts.InstrumentContext`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.contexts.InstrumentContext) object which stores information about the pipette and can be used to call liquid handling methods from, and a list of the loaded tip racks as [`opentrons.protocol_api.labware.Labware`](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) objects.


---
# OTProto.Templates

[Importing Template Module](#import-statement) | [Using Templates](#using-otproto-templates) | [Creating Templates](#creating-custom-otprototemplates) | [OTProto Template Superclass](#superclass-otproto_template)

## Import Statement
`import BiomationScripter.OTProto.Templates as Templates`

## Using OTProto Templates
Described here are the generic best practices for creating Opentrons protocols using OTProto templates.

### Walkthrough
Begin by creating a python file in any text editor or IDE. Then, set up the content of the python file following the guidelines below.

**Header:**\
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

**Body:**\

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

**Simulation:**\
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

See the [`OTProto.Templates` module file](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/BiomationScripter/OTProto/Templates.py) for examples.

## Templates

### Class: [`Transformation`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/OTProto/Templates.py)
This class is used to generate a transformation protocol for the OT-2.



## Superclass: [`OTProto_Template`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/OTProto/Templates.py)

This class is used as a superclass for all OTProto templates. It contains attributes and methods which are common to any Opentrons protocol, and therefore allows for a certain amount of standardisation across the templates.

**Usage:**
The [`OTProto_Template`](#OTProto_Template) class should only be used to extend OTProto templates, and shouldn't be called by itself. Below is an example of how a new protocol template can be created using this class. For a complete walkthrough describing how OTProto templates can be created, see [here](#).

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
