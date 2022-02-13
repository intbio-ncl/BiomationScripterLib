# BiomationScripter - Generic Tools

---
[Overview](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#feature-overview) | [Using BiomationScripter Tools](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#using-biomationscripter) | [Classes](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#classes) | [Functions](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#functions) | [Exceptions](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#exceptions)

---

## Feature Overview
The BiomationScripter package contains a set of generic tools which can be used to help write protocols for any supported automation platform. These tools take the form of classes and functions and aid in the creation of automation protocols by providing common formats and abstracting-out commonly required functions. These include classes which can store information about the format and content of plates or other labware, and functions which return valid well ranges.

---
## Using BiomationScripter
Begin by importing the BiomatonScripter package:\
`import BiomationScripter as BMS`

---

### Classes
### Class: [`Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/__init__.py)

*NOTE: this class can also be called using `PlateLayout`. The name `PlateLayout` will be removed in version 0.2.0.dev, but can still be used for now.*

This class is used to store information, such as number of wells and content, about plates or other labware which can later be retrieved. The `BMS.Labware_Layout` class is also intended to be universal within BiomationScripter, and not specific to any particular automation equipment.

 `Labware_Layout` objects are separate from, but sometimes related to, any object which is meant to represent a physical instance of a piece of labware. The `Labware_Layout` class captures information about a piece of labware, such as its content. Within BiomationScripter you may come across other classes which are used to represent labware, such as ['opentrons.protocol_api.labware.Labware'](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) from the [Opentrons Python API](https://docs.opentrons.com/v2/index.html). The ['opentrons.protocol_api.labware.Labware'](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) class is distinct from the `BMS.Labware_Layout` class as the Opentrons class represents the physical instance of the labware and is specific to the Opentrons liquid handling system, whereas `BMS.Labware_Layout` can capture additional metadata and can be utilised by multiple automation equipment within the BiomationScripter context.

**Usage:**\
`BMSLabware_Layout(name: str, type: str)` returns `BiomationScripter.Labware_Layout` object

[See examples of this class in use here.](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/Docs/Example_Code_Snippets/BMS/BMS-Labware_Layout-Class.ipynb)

**Attributes:**
* `name` | `str`: A readable name for the plate/labware.
* `type` | `str`: The type for the plate/labware.
* `rows` | `int`: Number of rows.
* `columns` | `int`: Number of columns.
* `content` | `dict{str: list[ list[str, float, str/boolean] ]}`: Dictionary storing content of the plate.
  * Dictionary key is the well ID (e.g. "A1")
  * Value is a list containing lists which capture information in the form `[Reagent_Name, Volume, Liquid_Class]`
    * `Reagent_Name` is a string
    * `Volume` is a float in microlitres
    * `Liquid_class` is optional, and is either stored as `False` or a string
* `available_wells` | `list[str] = None`: List of wells in the plate which are available for use
    * If `None`, this means that no available wells have been specified, and is distinct from `[]`, which means there are no available wells

**Methods:**
* `__init__(self, Name: str, Type: str)` returns `BiomationScripter.Labware_Layout`
  * Creates a `BiomationScripter.Labware_Layout` object with a name and labware type.
  * `Name` is stored as `self.name` and is required with no default value.
  * `Type` is stored as `self.type` and is required with no default value.
  * `self.rows` is instantiated as `None`
  * `self.columns` is instantiated as `None`
  * `self.content` is instantiated as an empty `dict{}`
  * `self.well_range` is instantiated as `None` - Note that this attribute is currently not in use
* `define_format(self, Rows: int, Columns: int)` returns `None`
  * Defines the number of rows, columns, and wells for the labware.
  * `Rows` is stored as `self.rows` and is required with no default value.
  * `Columns` is stored as `self.columns` and is required with no default value.
* `get_format(self)` returns `list[str]`
  * Returns the number of rows and columns for the labware
    * Returns `[self.rows, self.columns]`
* `get_well_range(self, Well_Range = None: str, Use_Outer_Wells = True: bool)` returns `List[str]`
  * Returns a list of wells (e.g. `["A1", "A2", "A3"]`)
  * When `Well_Range = None` and `Use_Outer_Wells = True`, a list of all wells in the plate are returned
  * When `Well_Range` is specified (E.g. `"A1:C4"`), all wells present within the plate and within that range are returned
  * When `Use_Outer_Wells = False`, wells from the first and last rows, and the first and last columns, are not returned
  * `Use_Outer_Wells` overrides `Well_Range`, so, for example, if any wells specified in `Well_Range` are in the first row and `Use_Outer_Wells = False`, those wells are *not* returned.
* `set_available_wells(self, Well_Range: str = None, Use_Outer_Wells: bool = True)` returns `None`
  * Uses `self.get_well_range` and stores the returned list of wells as `self.available_wells`
* `get_available_wells(self)` returns `list[str]`
  * Returns a list of available wells
  * If `None` is returned, then no available well range has been specified
* `check_well(self, Well: str)` returns `bool`
  * Checks whether `Well` (e.g. "A1") is a valid well in the current plate
  * Returns `True` if the well is present, and `False` if it is not
  * Can be used to check if a well is out of range
* `clone_format(self, Name: str)` returns `BiomationScripter.Labware_Layout`
  * Creates a new `BiomationScripter.Labware_Layout` object with the same format
  * `Name` is used as the new name
  * Content in the current plate is not copied, only the format (`self.type`, `self.rows`, and `self.columns`)
* `add_content(self, Well: str, Reagent: str, Volume: float, Liquid_Class: str/boolean = False)` returns `None`
  * Adds content to `self.content` in the form `{Well: [ [Reagent, Volume, Liquid_Class] ]}`
  * Will not overwrite any currently stored content in the well, and will instead append the new content to any current content
  * `Well` is a required value with no default which can have two forms: either a single well (e.g. `"A1"`), or a well range, where the first well is separated from the last well by a colon (e.g. `"A1:A5"`)
    * If `Well` specifies a well range, the specified content will be added to all wells.
  * `Reagent` is a required value with no default.
  * `Volume` is a required value which should be specified in microlitres, and has no default.
  * `Liquid_Class` is an optional value, with a default of `False`.
* `get_content(self)` returns `self.content: dict`
  * Returns all stored content in the `BiomationScripter.Labware_Layout' object as a dictionary
* `get_occupied_wells(self)` returns `list[str]`
  * Returns a list of all wells which appear in `self.content` (i.e. wells which have content specified for them)
  * If `self.content` is empty, and empty list is returned
* `get_liquids_in_well(self, Well: str)` returns `list[str]`
  * Returns a list of liquid names which are present in the well specified by `Well`
  * If `Well` is not present in `self.content`, an error will be raised
* `get_wells_containing_liquid(self, Liquid_Name: str)` returns `list[str]`
  * Returns a list of wells which contain `Liquid_Name`
  * If no wells are present which containing `Liquid_Name`, an empty list is returned
* `clear_content(self)` returns `None`
  * Clears the entire dictionary stored as `self.content`
* `clear_content_from_well(self, Well: str)` returns `None`
  * Clears all content in one well by deleting the entry in `self.content` with a key of `Well`
* `get_volume_of_liquid_in_well(self, Liquid: str, Well: str)` returns `float`
  * Returns the volume of `Liquid` in `Well`
  * If `Well` is not present in `self.content` an error is raised
  * If `Liquid` is not present in `Well`, `0.0` is returned
* `update_volume_in_well(self, Volume: float/int, Reagent: str, Well: str)` returns `None`
  * Changes the current volume of `Reagent` in well `Well` to `Volume`
  * If `Well` does not exist in `self.content`, an error will be raised
* `print(self)` returns `str`
  * Pretty prints all content stored in `self.content`
  * Returns a `str` with the same content which is printed
* `import_plate(self, filename: str, path: str = "~", ext: str = ".xlsx")` returns `None`
  *


### Class: [`Liquids`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/__init__.py)
This class is used to store information about liquids and where they are stored.

**Usage:**\
`BMS.Liquids()` returns `BiomationScripter.Liquids` object

**Attributes:**
* `liquids` | `dict{str: list[str/obj, str]}`: dictionary storing information about the liquids
   * Dictionary key is the name of the liquid
   * Dictionary values take the form of a list, formatted as [`labware`, `source_well`]
   * `labware` may be either a string, which defines the name of the labware, or an object which represents the labware
   * 'source_well' is a string (e.g. "A1")

**Methods:**
* `__init__(self)` returns `BiomationScripter.Liquids`
   * Creates a 'BiomationScripter.Liquids' object
   * `self.liquids` is initiated as an empty dictionary
* `add_liquid(self, liquid: str, labware: str/obj, source_well: str)` returns `None`
   * Adds a liquid to `self.liquids`
   * `liquid` acts as the dictionary key
   * `labware` and `source_well` are added as dictionary values, in the format `list[labware, source_well]`
* `get_liquid_labware(self, liquid: str)` returns `str/obj`
   * Returns the labware stored for the specified `liquid`
* `get_liquid_well(self, liquid: str)` returns `str`
   * Returns the source well for the specified `liquid`
* `add_liquids_to_labware(self, liquids: list[str], labware: str/obj, blocked_wells = None: list[str], well_range = None: list[str])` returns `None`
   * Adds a list of liquids to a specified labware in order using any available wells
   * `blocked_wells` is, by default, `None`
   * `blocked_wells` can be a list of well names (e.g. ["A1", "B1", "C1"]) which should not be used when assigning liquids to wells
   * `well_range` is, by default, `None`
   * `well_range` can be a list of well names (e.g. ["A1", "B1", "C1"]) which should be used when assigning liquids to wells
   * If both `blocked_wells` and `well_range` are defined, any wells present in both lists will be removed from `well_range`
* `get_all_liquids(self)` returns `list[str]`
   * Returns a list of all keys in `self.liquids`

---

### Functions
### Function: [`Import_Plate_Layout`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/__init__.py)
This function imports an Excel file with a standard layout and converts it to a [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object.

**Usage:**\
`BMS.Import_Plate_Layout(Filename: str)` returns [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout)

**Arguments:**
* `Filename` | `str`: Location of an Excel file (relative to home directory) specifying the desired plate layout

**Behaviour:**\
<TBC>


### Function: [`Create_Plates_Needed`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/__init__.py)
This function calculates how many plates of a certain type are required for a protocol and returns a list of [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) objects.

**Usage:**\
`BMS.Create_Plates_Needed(Plate_Format: BiomationScripterLabware_Layout, N_Wells_Needed: int, N_Wells_Available: int/str = "All")` returns `list[BiomationScripterLabware_Layout]`

**Arguments:**
* `Plate_Format` | [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout): Plate or labware type to be used as the template
* `N_Wells_Needed` | `int`: Total number of wells or slots required by the protocol
* `N_Wells_Available` | `int/str = "All"`: Either the number of wells/slots available per plate/labware (`int`), or `"All"`, which specifies that all wells/slots in the labware are available (`str`)

**Behaviour:**\
[`Create_Plates_Needed`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#function-Create_Plates_Needed) calculates how many plates or other type of labware are needed for a protocol based on the number of wells/slots required (`N_Wells_Needed`) and the number of wells/slots available per plate/labware (`N_Wells_Available`). That number of [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) objects will then be created using the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) specified by the `Plate_Format` argument as a template. These objects are then returned as a list. NOTE: if the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object specified by `Plate_Fomrat` has content specified, this content will not be added to the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) objects which are returned. The original [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object is returned as the first element in the returned list.

### Function: [`well_range`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/__init__.py)
This function returns a list of wells based on a specified well range and direction. Wells are always in the format of row followed by column, where row is a letter and column is an integer (e.g. A1, D6, C12, B7, etc.).

**Usage:**\
`BMS.well_range(Wells: str, Labware_Format: BiomationScripterLabware_Layout = None, Direction: str = "Horizontal", Box = True)` returns `list[str]`

**Arguments:**
* `Wells` | `str`: A string specifying the range of wells to return - must always have the following format: `"{}{}:{}{}".format(Starting Well Row, Starting Well Column, End Well Row, End Well Column)`, e.g. `"A1:B4"`
* `Labware_Format` | [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout)/list[`str`] = `None`: Plate/labware type to give context to the well range being returned, or a list specifying the number of rows and columns in the labware (e.g. [8, 12])
* `Direction` | `str = "Horizontal"`: Direction to use when calculating wells in the specified well range - must be either `"Horizontal"` or `"Vertical"`
* `Box` | `bool = True`: Determines the well range 'shape' - can only be `False` if `Labware_Format` is specified

*NOTE: In BiomationScripter version 0.1.0.dev, `Labware_Format` can be either a [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object, or a list specifying the number of rows and columns of the desired labware. When version 0.2.0.dev releases, support for supplying the `Labware_Format` argument with a [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object will be removed, and it will only be possible to supply the argument with a list. The `get_format()` method can be used to get this list from the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object.*

**Behaviour:**\
[`BiomationScripter.well_range`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#function-well_range) returns a list of wells based on the well range specified by `Wells`. The exact wells which are returned, and the order they are placed in the list, is determined by the `Direction`, `Labware_Format`, and `Box` arguments.

The `Direction` argument determines the order in which wells are counted. If `Direction = "Horizontal"`, wells are added to the list starting with those on the same row, before moving to the next row. For example, the well range A2:B4 would begin by adding wells in row 'A' (A2, A3, A4,...), and then move on to row 'B'. If `Direction = "Vertical"`, wells will instead be added to the list starting with those in the same column (A1, B1, C1,...), and then move on to subsequent columns (A2, B2, C2,...).

The `Box` argument determines whether the well range has a box-like shape. For example, if `Box = True`, the well range A2:C4 would returns the wells A2, A3, A4, B2, B3, B4, C2, C3, C4. If `Box = False`, then the well range A2:C4 would instead include all wells between A2 and C4 up to the boundary of the plate. So for a standard 96 well plate, this would return wells A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12, C1, C2, C3, C4. The order of these wells in both examples would be dependent on the `Direction` argument.

If `Box = False`, then `Labware_Format` must be specified using a [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object, which defines the number of rows and columns in the plate, or a list specifying the number of rows and columns the labware has. If `Box = False` and `Labware_Format = None`, an error will occur.

The image below sums up this information:

<img src="https://github.com/intbio-ncl/BiomationScripterLib/blob/main/Resources/.wiki-images/well_range_function_graphic.jpg" alt = "Graphic showing how the Direction and Box arguments work in the well_range function. Discussed in main text." width = "500"/>

---

### Exceptions

* **NegativeVolumeError**: Used when a calculation error occurs and volume less than 0 is specified
* **RobotConfigurationError**: Used when automation equipment is not configured correctly, or when information about the equipment is missing
* **BMSTemplateError**: Used when an error specific to a template occurs
* **LabwareError**: Used for issues relating to missing, incorrect, or inappropriate labware
* **OutOfSourceMaterial**: Used when not enough source material is available for the intended transfer step/protocol
