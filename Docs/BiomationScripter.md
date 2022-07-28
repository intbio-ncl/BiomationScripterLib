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

# BiomationScripter - Generic Tools

For version 0.2.0.dev

---
[Overview](#feature-overview) |
[Using BiomationScripter Tools](#using-biomationscripter) |
[Classes](#classes) |
[Functions](#functions) |
[Exceptions](#exceptions)

---

## Feature Overview
The BiomationScripter package contains a set of generic tools which can be used to help write protocols for any supported automation platform. These tools take the form of classes and functions and aid in the creation of automation protocols by providing common formats and abstracting-out commonly required functions. These include classes which can store information about the format and content of plates or other labware, and functions which return valid well ranges.

---
## Using BiomationScripter
Begin by importing the BiomatonScripter package:\
`import BiomationScripter as BMS`

---

### Classes

[`Labware_Content`](#class-labware_content) |
[`LabwareLayout`](#class-labware_layout) |
[`Assembly`](#class-assembly) |
[`Liquids`](#class-liquids) |
[`Mastermix`](#class-mastermix)

### Class [`Assembly`](../BiomationScripter/__init__.py)

This class is used to store basic information about a DNA assembly

**Usage:**

`BMS.Assembly(Name: str, Backbone: str, Parts: list[str])` returns `BiomatonScripter.Assembly` object

**Attributes:**

* `name` | `str`: The assembly name
* `backbone` | `str`: The name of the plasmid backbone
* `parts` | `list[str]`: A list of parts to be assembled into the plasmid backbone

**Methods:**

* `__init__(self, Name: str, Backbone: str, Parts: list[str])` returns `BiomatonScripter.Assembly` object
  * Creates the `BiomatonScripter.Assembly` object


### Class [`Labware_Content`](../BiomationScripter/__init__.py)

This class is used by [`Labware_Layout`](#class-labware_layout) to store content information.

**Usage:**

`BMS.Labware_Content(Name: str, Volume: float|int, Liquid_Class: str = None)` returns `BiomationScripter.Labware_Content` object

**Attributes:**
* `name` | `str`: The name of the liquid/reagent
* `volume` | `float|int`: The amount of the liquid/reagent (in microlitres)
* `liquid_class` | `str`: The liquid class or calibration for the reagent/liquid
  * Defaults to `None`

**Methods:**
* `__init__(self, Name: str, Volume: float|int, Liquid_Class: str = None)` returns `BiomationScripter.Labware_Content`
  * Creates the `BiomationScripter.Labware_Content` object
* `get_info(self)` returns `List[self.name, self.volume, self.liquid_class]`
  * Returns as a list `self.name`, `self.volume`, and `self.liquid_class`

### Class: [`Labware_Layout`](../BiomationScripter/__init__.py)

This class is used to store information, such as number of wells and content, about plates or other labware which can later be retrieved. The `BMS.Labware_Layout` class is also intended to be universal within BiomationScripter, and not specific to any particular automation equipment.

 `Labware_Layout` objects are separate from, but sometimes related to, any object which is meant to represent a physical instance of a piece of labware. The `Labware_Layout` class captures information about a piece of labware, such as its content. Within BiomationScripter you may come across other classes which are used to represent labware, such as ['opentrons.protocol_api.labware.Labware'](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) from the [Opentrons Python API](https://docs.opentrons.com/v2/index.html). The ['opentrons.protocol_api.labware.Labware'](https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.labware.Labware) class is distinct from the `BMS.Labware_Layout` class as the Opentrons class represents the physical instance of the labware and is specific to the Opentrons liquid handling system, whereas `BMS.Labware_Layout` can capture additional metadata and can be utilised by multiple automation equipment within the BiomationScripter context.

**Usage:**

`BMS.Labware_Layout(name: str, type: str)` returns `BiomationScripter.Labware_Layout` object

[See examples of this class in use here.](https://github.com/intbio-ncl/BiomationScripterLib/blob/main/Docs/Example_Code_Snippets/BMS/BMS-Labware_Layout-Class.ipynb)

**Attributes:**
* `name` | `str`: A readable name for the plate/labware.
* `type` | `str`: The type for the plate/labware.
* `rows` | `int`: Number of rows.
* `columns` | `int`: Number of columns.
* `content` | `dict{str: list[BiomationScripter.Labware_Content]}`: Dictionary storing content of the plate.
  * Dictionary key is the well ID (e.g. "A1")
  * Value is a list of [`Labware_Content`](#class-labware_content) objects
* `available_wells` | `list[str] = None`: List of wells in the plate which are available for use
    * If `None`, this means that no available wells have been specified, and is distinct from `[]`, which means there are no available wells
* `empty_wells` | `list[str] = None`: List of wells in the plate which are available and empty
  * If `None`, this means that no empty wells have been specified, and is distinct from `[]`, which means there are no empty wells
  * This is generated automatically when `available_wells` are specified, and it automatically updated when content is added and removed
* `well_labels` | `dict{str: str} = {}`: A dictionary of well labels
  * The well position is used as the key
  * The label is used as the value

**Methods:**
* `__init__(self, Name: str, Type: str)` returns `BiomationScripter.Labware_Layout`
  * Creates a `BiomationScripter.Labware_Layout` object with a name and labware type.
  * `Name` is stored as `self.name` and is required with no default value.
  * `Type` is stored as `self.type` and is required with no default value.
  * `self.rows` is instantiated as `None`
  * `self.columns` is instantiated as `None`
  * `self.content` is instantiated as an empty `dict{}`
  * `self.available_wells` is instantiated as `None`
  * `self.empty_wells` is instantiated as `None`
  * `self.well_labels` is instantiated as an empty `dict{}`
* `define_format(self, Rows: int, Columns: int)` returns `None`
  * Defines the number of rows, columns, and wells for the labware.
  * `Rows` is stored as `self.rows` and is required with no default value.
  * `Columns` is stored as `self.columns` and is required with no default value.
* `get_format(self)` returns `list[str]`
  * Returns the number of rows and columns for the labware
    * Returns `[self.rows, self.columns]`
* `set_available_wells(self, Well_Range: str = None, Use_Outer_Wells: bool = True, Direction: str = "Horizontal", Box: bool = False)` returns `None`
  * Adds the specified wells to `self.available_wells` and `self.empty_wells`
  * When no arguments are specified, all wells are specified as available for use
  * `Well_Range` can be a range of wells specified as First_Well:Last_Well (e.g. `"A1:B4"`), or a single well (e.g. `"C6"`)
  * When `Use_Outer_Wells = False`, wells from the first and last rows, and the first and last columns, are not included, even if the well range specifies them
  * The `Direction` argument determines the order in which wells are counted. If `Direction = "Horizontal"`, wells are added to the list starting with those on the same row, before moving to the next row. For example, the well range A2:B4 would begin by adding wells in row 'A' (A2, A3, A4,...), and then move on to row 'B'. If `Direction = "Vertical"`, wells will instead be added to the list starting with those in the same column (A1, B1, C1,...), and then move on to subsequent columns (A2, B2, C2,...)
  * The `Box` argument determines whether the well range has a box-like shape. For example, if `Box = True`, the well range A2:C4 would returns the wells A2, A3, A4, B2, B3, B4, C2, C3, C4. If `Box = False`, then the well range A2:C4 would instead include all wells between A2 and C4 up to the boundary of the plate.
* `get_available_wells(self)` returns `list[str]`
  * Returns a list of available wells
  * If `None` is returned, then no available well range has been specified
* `get_well_range(self, Well_Range: str = None, Use_Outer_Wells: bool = True, Direction: str = "Horizontal", Box: bool = False)` returns `List[str]`
  * Returns a list of wells (e.g. `["A1", "A2", "A3"]`)
  * `Well_Range` can be a range of wells specified as First_Well:Last_Well (e.g. `"A1:B4"`), or a single well (e.g. `"C6"`)
  * When `Use_Outer_Wells = False`, wells from the first and last rows, and the first and last columns, are not included, even if the well range specifies them
  * The `Direction` argument determines the order in which wells are counted. If `Direction = "Horizontal"`, wells are added to the list starting with those on the same row, before moving to the next row. For example, the well range A2:B4 would begin by adding wells in row 'A' (A2, A3, A4,...), and then move on to row 'B'. If `Direction = "Vertical"`, wells will instead be added to the list starting with those in the same column (A1, B1, C1,...), and then move on to subsequent columns (A2, B2, C2,...)
  * The `Box` argument determines whether the well range has a box-like shape. For example, if `Box = True`, the well range A2:C4 would returns the wells A2, A3, A4, B2, B3, B4, C2, C3, C4. If `Box = False`, then the well range A2:C4 would instead include all wells between A2 and C4 up to the boundary of the plate.
* `check_well(self, Well: str)` returns `bool`
  * Checks whether `Well` (e.g. "A1") is a valid well in the current plate
  * Returns `True` if the well is present, and `False` if it is not
  * Can be used to check if a well is out of range
* `clone_format(self, Name: str)` returns `BiomationScripter.Labware_Layout`
  * Creates a new `BiomationScripter.Labware_Layout` object with the same format
  * `Name` is used as the new name
  * Content in the current plate is not copied, only the format (`self.type`, `self.rows`, and `self.columns`)
* `add_content(self, Well: str, Reagent: str, Volume: float, Liquid_Class: str/boolean = False)` returns `None`
  * Creates a [`Labware_Content`](#class-labware_content) object and adds to `self.content` in the form `{Well: [ [BiomationScripter.Labware_Content] ]}`
  * Will not overwrite any currently stored content in the well, and will instead append the new content to any current content
  * `Well` is a required value with no default which can have two forms: either a single well (e.g. `"A1"`), or a well range, where the first well is separated from the last well by a colon (e.g. `"A1:A5"`)
    * If `Well` specifies a well range, the specified content will be added to all wells.
  * `Reagent` is a required value with no default.
  * `Volume` is a required value which should be specified in microlitres, and has no default.
  * `Liquid_Class` is an optional value, with a default of `False`.
* `get_content(self)` returns `self.content: dict{str: [BiomationScripter.Labware_Content]}`
  * Returns all stored content in the `BiomationScripter.Labware_Layout` object as a dictionary
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
* `get_total_volume_of_liquid(self, Liquid: str)` returns `float`
  * Returns the total volume of the specified liquid across all wells of the labware
* `print(self)` returns `str`
  * Pretty prints all content stored in `self.content`
  * Returns a `str` with the same content which is printed
* `import_labware(self, filename: str, path: str = "~", ext: str = ".xlsx")` returns `None`
  * Used by the [`BiomationScripter.Import_Labware_Layout`](#Function-Import_Labware_Layout) function.
* `add_well_label(self, Well: str, Label: str)` returns `None`
  * Assigns the label specified by `Label` to the well specified by `Well`
  * Well labels must be unique or an error will be raised
  * Adds the label to `self.well_labels`
* `get_well_content_by_label(self, Label: str)` returns [`Labware_Content`](#class-labware_content) object
  * Returns the [`Labware_Content`](#class-labware_content) object in the well with a label of `Label`
* `get_well_location_by_label(self, Label: str)` returns `str`
  * Retuns the well position as a `str` which has label of `Label`
* `get_next_empty_well(self)` returns `str`
  * Returns the next well positon as `str` which is specified as being empty
  * Returns in the order specified by `self.available_wells`, and checks `self.empty_wells` to see if the next available well is empty

### Class: [`Liquids`](../BiomationScripter/__init__.py)
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

### Class [`Mastermix`](../BiomationScripter/__init__.py)

This class is used by [`BMS.Mastermix_Maker`](#function-mastermix_maker) to store information about a mastermix. It is not intended for use outside of this function. Even though the [`BMS.Mastermix_Maker`](#function-mastermix_maker) returns this class, it shouldn't ever need to be used or understood.

**Usage:**

`BMS.Mastermix(Name: str, Reagents: list[str], Wells: list[str])` returns `BiomatonScripter.Mastermix` object

**Attributes:**

* `name` | `str`: The name of the mastermix
* `reagents` | `str`: A list of reagents in the mastermix and their volumes - the reagent and its volume is stored as a list in the format `"Reagent_vol_Volume"`, where `"_vol_"` is always in the string to separate the reagent name and the volume - the volume must be written in numerical form (i.e. `"5"` rather than `"five"`)
* `wells` | `list[str]`: A list of destination wells serviced by the mastermix, given in the format `"index_well"`, where the index is the index of the destination labware

**Methods:**

* `__init__(self, Name: str, Reagents: list[str], Wells: list[str])` returns `BiomatonScripter.Mastermix` object
 * Creates the `BiomatonScripter.Mastermix` object

---

### Functions

[`Create_Labware_Needed`](#function-create_labware_needed) |
[`fmol_calculator`](#function-fmol_calculator) |
[`Import_Labware_Layout`](#function-import_labware_layout) |
[`Mastermix_Maker`](#function-mastermix_maker) |
[`Reagent_Finder`](#function-reagent_finder) |
[`well_range`](#function-well_range)


### Function: [`Create_Labware_Needed`](../BiomationScripter/__init__.py)
This function calculates how many plates of a certain type are required for a protocol and returns a list of [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) objects.

**Usage:**\
`BMS.Create_Labware_Needed(Plate_Format: BiomationScripterLabware_Layout, N_Wells_Needed: int, N_Wells_Available: int/str = "All", Return_Original_Layout: bool = True)` returns `list[BiomationScripterLabware_Layout]`

**Arguments:**
* `Labware_Format` | [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout): `Labware_Layout` object to be used as the template
* `N_Wells_Needed` | `int`: Total number of wells or slots required by the protocol
* `N_Wells_Available` | `int/str = "All"`: Either the number of wells/slots available per plate/labware (`int`), or `"All"`, which specifies that all wells/slots in the labware are available (`str`)
* `Return_Original_Layout` | `bool = True`: Specifies whether the layout given in `Labware_Format` should be returned or not

**Behaviour:**\
[`Create_Labware_Needed`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#function-Create_Labware_Needed) calculates how many plates or other type of labware are needed for a protocol based on the number of wells/slots required (`N_Wells_Needed`) and the number of wells/slots available per plate/labware (`N_Wells_Available`). That number of [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) objects will then be created using the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) specified by the `Labware_Format` argument as a template. These objects are then returned as a list. NOTE: if the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object specified by `Labware_Fomrat` has content specified, this content will not be added to the [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) objects which are returned. The original [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object is returned as the first element in the returned list.


### Function: [`fmol_calculator`](../BiomationScripter/__init__.py)
Calculates the number of fmols of a dsDNA molecule based on the mass (ng) and length (bp).

**Usage:**

`BMS.fmol_calculator(mass_ng: float, length_bp: int)` returns `float`

**Arguments:**
* `mass_ng` | `float`: The mass of the dsDNA sample in nanograms
* `length_bp` | `int`: The length of the dsDNA molecule in base pairs

**Behaviour:**\
Calculates fmols of dsDNA molecules in a sample. Uses the following equation:

![((mass_ng * 1e^-9)/((length_bp * 617.96) + 36.04)) * 1e^15](https://latex.codecogs.com/svg.latex?fmol=\frac{mass\\_ng\times1e^-^9}{(length\\_bp\times617.96)+36.04}\times1e^1^5)


### Function: [`Import_Labware_Layout`](../BiomationScripter/__init__.py)
This function imports an Excel file with a standard layout and converts it to a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object.

**Usage:**\
`BMS.Import_Labware_Layout(Filename: str, path: str = "~", ext: str = ".xlsx")` returns [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout)

**Arguments:**
* `Filename` | `str`: Location of an Excel file (relative to home directory) specifying the desired labware layout
* `path` | `str = "~"`: The path to prepend to the file location passed to `Filename`, default is the home directoy (`"~"`)
* `ext` | `str = ".xlsx"`: The file extension for the file passed to `Filename`, default is an excel file (`".xlsx"`)

**Behaviour:**\
This function will import a layout specified by an excel file as a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout) object. The excel file should follow the standard described [here](Standard_Layout_File.md)


### Function: [`Mastermix_Maker`](../BiomationScripter/__init__.py)
This function can be used to automatedly generate mastermixes based on source materials in a list of destination labware layout objects, and user-defined parameters.

**Usage:**

`BMS.Mastermix_Maker(Destination_Layouts: List[BMS.Labware_Layout], Mastermix_Layout = BMS.Labware_Layout, Maximum_Mastermix_Volume: float, Min_Transfer_Volume: float, Extra_Reactions: float, Excluded_Reagents: List[str] = [], Excluded_Combinations: List[List[str]] = [], Preferential_Reagents: List[str] = [], Seed: int = None)` returns `(Mastermixes: List[BMS.Mastermix], Seed: int, Destination_Layouts: List[BMS.Labware_Layout], Mastermix_Layouts: List[BMS.Labware_Layout])`

**Arguments:**
* `Destination_Layouts` | `List[BMS.Labware_Layout]`: List of [`BMS.Labware_Layout`](#class-labware_layout) objects representing the final state of the destination labware to prepare mastermixes for - must be fully populated with all source material required in each well
* `Mastermix_Layout` | `BMS.Labware_Layout`: A [`BMS.Labware_Layout`](#class-labware_layout) object representing the labware for the mastermixes - should be empty (i.e. not content specified), but the labware format should be given
* `Maximum_Mastermix_Volume` | `float`: Maximum volume (in microlitres) for each mastermix - should not be more than the maximum well capacity for the mastermix labware
* `Min_Transfer_Volume` | `float`: The minimum transfer volume (in microlitres) for any liquids into or from the mastermixes
* `Extra_Reactions` | `float`: The number of extra reactions each mastermix should be prepared for - can be used to account for pipetting inaccuracy or well dead volumes - can be a proportion of a reaction (e.g. prepare for 1.5 extra reactions)
* `Excluded_Reagents` | `List[str] = []`: A list of reagents which should not be included in any mastermixes - this will remain as source materials in the destination labware layout(s)
* `Excluded_Combinations` | `List[List[str]] = []`: A list of lists, where each sub-list contains reagents names which should not be combined within the same mastermix
* `Preferential_Reagents` | `List[str] = []`: A list of reagents which should be considered first as components of a mastermix
* `Seed` | `int = None`: A seed can be supplied for the random generated sections of the function, to ensure repeatability - if no seed is specified then different seeds will be tried until a solution is found (or after there has been too many attempts)

**Behaviour:**

This function can be used to automatically generate mastermixes for a given list of destination labware layouts. The mastermixes are generated by finding common source reagents across destination wells, and grouping them together in the minimal amount of mastermixes. The mastermixes generated are stored in `BMS.labware_layout` objects and also returned as a list of `BMS.Mastermix` objects.

The exact composition of the mastermixes generated can be influenced by through the use of arguments listed above. In some cases, these arguments may provide too many constraints and result in an impossible situation where mastermixes cannot be generated. To help ensure all possible combinations are attempted, there is some randomness within the function. This randomness can be removed by supplying a specific seed, and ensure that the same mastermixes are generated each time.


### Function: [`Reagent_Finder`](../BiomationScripter/__init__.py)
Searches a directory containing labware layout files for a specified reagent.

**Usage:**\
`BMS.Reagent_Finder(Reagents: List[str], Directories: List[str])` returns `None`

**Arguments:**
* `Reagents` | `List[str]`: A list of reagent names to search for
* `Directories` | `List[str]`: A list of directories containing labware layout files

**Behaviour:**\
This function will search in the directories listed for files which appear to be BMS labware layout files. Any labware layout files found will then be searched for the specified reagents. The name of all reagents are then printed to OUT, along with the name of the labware layout they appear in and the well(s) they occupy.



### Function: [`well_range`](../BiomationScripter/__init__.py)
This function returns a list of wells based on a specified well range and direction. Wells are always in the format of row followed by column, where row is a letter and column is an integer (e.g. A1, D6, C12, B7, etc.).

**Usage:**
`BMS.well_range(Wells: str, Labware_Format: BiomationScripterLabware_Layout = None, Direction: str = "Horizontal", Box = True)` returns `list[str]`

**Arguments:**
* `Wells` | `str`: A string specifying the range of wells to return - must always have the following format: `"{}{}:{}{}".format(Starting Well Row, Starting Well Column, End Well Row, End Well Column)`, e.g. `"A1:B4"`
* `Labware_Format` | [`BiomationScripterLabware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-labware_layout)/list[`str`] = `None`: Plate/labware type to give context to the well range being returned, or a list specifying the number of rows and columns in the labware (e.g. [8, 12])
* `Direction` | `str = "Horizontal"`: Direction to use when calculating wells in the specified well range - must be either `"Horizontal"` or `"Vertical"`
* `Box` | `bool = True`: Determines the well range 'shape' - can only be `False` if `Labware_Format` is specified

**Behaviour:**
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
* **TransferError**: Used to indicate a general problem with a transfer event
