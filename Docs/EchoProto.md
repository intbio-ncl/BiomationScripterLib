# BiomationScripter - EchoProto
---

[Overview](#feature-overview) | [Importing Picklists](#importing-picklists-via-plate-reformat) | [Using EchoProto](#using-echoproto) | [Using EchoProto Templates](#using-echoprototemplates) | [Simulating Protocols](#simulating-protocols) | [All Templates](#template-classes)

---

## Feature Overview
EchoProto is a module within the BiomationScripter package which contains tools specifically aimed at writing protocols for the Echo525. EchoProto enables users to write python scripts which can then generate a set of CSV picklists. The picklists contain a list of transfer actions for the Echo to perform. There is one picklist generated per source plate, and all of the picklists together form the entire protocol. Instructions for importing the picklists to the Echo can be found [here](#importing-picklists-via-plate-reformat).

EchoProto contains two submodules:
* **EchoProto:** A set of functions and classes which are used to capture information about an Echo protocol, and convert this information into a set of picklists
* **EchoProto.Templates:** A set of classes which generate picklists for common protocols, such as Loop assembly and Q5 PCR, based on user inputs

If you are planning on using the Echo to automate common protocols, such as PCR, there may be a pre-written EchoProto template available. A list of currently available templates can be found [here](#template-classes).

If you are planning on automating a protocol which you will use many times, but with slightly different variations/inputs, it may be helpful to create your own EchoProto template. A walkthrough explaining how this can be done can be found here.

If you are planning to automate a protocol for which there are no existing templates, and that protocol will only be repeated identically (or not at all), it may be best to not write a template. In this case, the general BiomationScripter tools and EchoProto tools can be used to help write the protocol.

---

## Importing picklists via Plate Reformat
Plate Refomrat is the proprietary of choice for importing custom picklists into the Echo 525 liquid handling robot. To get started simply launch the software "Labcyte Echo Plate Reformat". Please not that custom picklists should be correctly formatted and saved as a .csv file before continuing this process.

A dialog box should appear to Connect to an Instrument. The instrument can be connected to via its IP address or there is an option to Work Offline.

![](https://github.com/intbio-ncl/BiomationScripter/blob/main/Resources/.wiki-images/Picture1.png)

Working offline may be useful for testing out protocols for simple errors without the need of inserting plates into the machine. After the connection is established, the software GUI should open.

Set-up a new protocol by clicking the new protocol button, this will open the Protocol Setup wizard.

![](https://github.com/intbio-ncl/BiomationScripter/blob/main/Resources/.wiki-images/Picture2.png)

Select the source plate type, the destination plate type and set the mapping type to custom. Click Ok to confirm and generate a new protocol file.

![](https://github.com/intbio-ncl/BiomationScripter/blob/main/Resources/.wiki-images/Picture3.png)

Now, the custom picklist can be imported to the new protocol. This is done using the "Import region definitions" option from the file menu. Import the custom picklist using the wizard. The import wizard will assist in retrieving the correct attributes using the file headers. Ensure that the following have been selected for import and that they map to the correct columns in the csv file:
* Source Plate Name
* Source Plate Type
* Source Well
* Destination Plate Name
* Destination Well
* Transfer Volume

![](https://github.com/intbio-ncl/BiomationScripter/blob/main/Resources/.wiki-images/Picture4.png)

The wizard will show a preview of the custom picklist file being imported, this is useful for proof checking the file before importing. There is a check box to remove duplicate line entries - it is recommended to uncheck this. There is also an option to Preview the import before finalising this. Select Import to import the picklist.

Now that the file has been imported, there should be two of each source and destination plate. The first of each will be the original blank plate from creating the protocol - this should be deleted. The second will contain the transfer steps from the picklist.

![](https://github.com/intbio-ncl/BiomationScripter/blob/main/Resources/.wiki-images/Picture5.png)

The protocol can be simulated and ran from the same software. This is done using the run button, represented by a blue play button.

![](https://github.com/intbio-ncl/BiomationScripter/blob/main/Resources/.wiki-images/Picture6.png)


---

## Using EchoProto
Begin by importing the EchoProto module:

`import BiomationScripter.EchoProto as EchoProto`

The EchoProto module has the following architecture:
<img src="https://github.com/intbio-ncl/BiomationScripterLib/blob/main/Resources/.wiki-images/EchoProto_Architecture.png" alt = "EchoProto_Architecture: Protocol contains 1 to many Transfer Lists. Transfer List contains 1 to many Actions." width = "900"/>

The [BiomationScripter.EchoProto.Protocol](#class-protocol) object is populated with [BiomationScripter.EchoProto.TransferList](#class-transferlist)s and [BiomationScripter.EchoProto.Action](#class-action)s through the use of the [BiomationScripter.EchoProto.Generate_Actions](#function-generate_actions) function. A populated [Protocol](#class-protocol) is used to generate CSV picklists by calling the [BiomationScripter.EchoProto.write_picklists](#function-write_picklists) function.

---

### Classes
### Class: [`Protocol`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/EchoProto/__init__.py)
This class is used to store information about a protocol, and can be used to generate CSV picklist files.

**Usage:**

`BMS.EchoProto.Protocol(Title: str)` returns [`BiomationScripter.EchoProto.Protocol`](#class-protocol)

**Attributes:**

* `title` | `str`: A title for the protocol
* `source_plates` | `list[BiomationScripter.Labware_Layout]`: A list of [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects which represent the source plates
* `destination_plates` | `list[BiomationScripter.Labware_Layout]`: A list of [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects which represent the source plates objects which represent the destination plates
* `transferlists` | `list[BiomationScripter.EchoProto.TransferList]`: A list of [`TransferList`](#class-transferlist) objects, which each represent a picklist

**Methods:**

* `__init__(self, Title: str)` returns [`BiomationScripter.EchoProto.Protocol`](#class-protocol)
   * Creates a [`BiomationScripter.EchoProto.Protocol`](#class-protocol) object with a title
   * `Title` is stored as `self.title`
   * `self.source_plates` is initiated as an empty `list[]`
   * `self.destination_plates` is initiated as an empty `list[]`
   * `self.transferlists` is initiated as an empty `list[]`
* `add_source_plate(self, Plate: BiomationScripter.Labware_Layout)` returns `None`
   * Appends the specified `Plate` to `self.source_plates`
* `add_source_plates(self, Plates: list[BiomationScripter.Labware_Layout])` returns `None`
   * Appends each of the plates specified in `Plates` to `self.source_plates`
* `make_transfer_list(self, Source_Plate: BiomationScripter.Labware_Layout)` returns [`BiomationScripter.EchoProto.TransferList`](#class-transferlist)
   * Creates a [`BiomationScripter.EchoProto.TransferList`](#class-transferlist) object and assigns the plate specified in `Source_Plate` to it
   * Appends the [`TransferList`](#class-transferlist) to `self.transferlists` and returns the object
* `get_transfer_list(self, Source_Plate: BiomationScripter.Labware_Layout)` returns [`BiomationScripter.EchoProto.TransferList`](#class-transferlist)
   * Returns the [`TransferList`](#class-transferlist) associated with the source plate specified by `Source_Plate`
* `add_destination_plate(self, Plate: BiomationScripter.Labware_Layout, Use_Outer_Wells = True: bool)` returns `None`
   * Appends the specified `Plate` to `self.destination_plates`
   * `Use_Outer_Wells` specifies whether or not wells in the first row, last row, first column, and last column should be used
* `add_destination_plates(self, Plates: list[BiomationScripter.Labware_Layout], Use_Outer_Wells = True: bool)` returns `None`
   * Appends each of the plates specified in `Plates` to `self.destination_plates`
   * `Use_Outer_Wells` specifies whether or not wells in the first row, last row, first column, and last column should be used
* `get_destination_plates(self)` returns `list[BiomationScripter.Labware_Layout]`
   * Returns a list of all [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) stored in `self.destination_plates`
* `get_source_plates(self)` returns `list[BiomationScripter.Labware_Layout]`
   * Returns a list of all [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) stored in `self.source_plates`

### Class: [`TransferList`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/EchoProto/__init__.py)
This class is used to group and store liquid transfer actions based on source plate, and acts as the basis for generating CSV picklist files. Each `TransferList` is associated with just one source plate, represented by a `BiomationScripter.Labware_Layout` object.

**Usage:**

`BMS.EchoProto.TransferList(Source_Plate: BiomationScripter.Labware_Layout)` returns [`BiomationScripter.EchoProto.TransferList`](#class-transferlist)

**Attributes:**

* `title` | `str`: A title for the transfer list
* `source_plate` | [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout): The source plate associated with the transfer list
* `_actions` | `list[BiomationScripter.EchoProto.Action]`: A list of liquid transfer events, where each transfer event is represented by a [`BiomationScripter.EchoProto.Action`](#class-action) object
* `__actionUIDs` | `list[int]`: A list of unique ids for each [`BiomationScripter.EchoProto.Action`](#class-action) in `_actions`
* `_source_plate_type` | `str`: The plate type for the associated source plate
* `__source_plate_types` | `set(str)`: A set of allowed source plate types
   * This should only be modified after consulting the list of compatible Echo source plates

**Methods:**

* `__init__(self, Source_Plate: BiomationScripter.Labware_Layout)` returns [`BiomationScripter.EchoProto.TransferList`](#class-transferlist)
   * Creates a [`BiomationScripter.EchoProto.TransferList`](#class-transferlist) object, which is associated with the source plate specified by `Source_Plate`, which is a [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout)
   * `self.title` is initialised using the the name of the associated source plate (`Source_Plate.name`)
   * `self.source_plate` is initialised as `Source_Plate`
   * `self._actions` is initialised as an empty list (`list[]`)
   * `self.__actionUIDs` is initialised as an empty list (`list[]`)
   * `self._source_plate_type` is initialised as `Source_Plate.type`
   * `self.__source_plate_types` is initialised as the following set of strings: `set("384PP", "384LDV", "6RES")`
* `get_source_plate_type(self)` returns `str`
   * Returns the type of source plate associated with the transfer list (`self._source_plate_type`)
* `get_actions(self)` returns `list[BiomationScripter.EchoProto.Action]`
   * Returns all liquid transfer events as a list of [`BiomationScripter.EchoProto.Action`](#class-action) objects
* `get_action_by_uid(self, UID: int)` returns [`BiomationScripter.EchoProto.Action`](#class-action)
   * Returns the [`BiomationScripter.EchoProto.Action`](#class-action) associated with the specified `UID`
* `add_action(self, Reagent: str, Calibration: str, Source_Well: str, Destination_Plate_Name: str, Destination_Plate_Type: str, Destination_Well: str, Volume: int)` returns `None`
   * Creates a [`BiomationScripter.EchoProto.Action`](#class-action) from the supplied arguments and appends it to `self._actions`
   * `Reagent` is the name of the liquid to be transferred
   * `Calibration` is the acoustic calibration for the Echo525 to use in the liquid transfer event (e.g. "AQ_BP")
   * `Source_Well` is the well from which the reagent is transferred (e.g. "A1")
   * `Destination_Plate_Name` is the name of the plate to which the reagent will be transferred
   * `Destination_Plate_Type` is the type of the plate to which the reagent will be transferred
   * `Destination_Well` is the well to which the reagent is transferred (e.g. "B6")
   * `Volume` is the amount, in nanolitres, of reagent which will be transferred
   * The source plate is taken from `self.source_plate`


### Class: [`Action`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/EchoProto/__init__.py)
This class is used to store information about a single liquid transfer event. Multiple [`BiomationScripter.EchoProto.Action`](#class-action) objects make up a [`BiomationScripter.EchoProto.TransferList`](#class-transferlist)

**Usage:**

`BMS.EchoProto.Action(UID: int, Reagent: str, Source_Plate_Name: str, Calibration: str, Source_Well: str, Destination_Plate_Name: str, Destination_Plate_Type: str, Destination_Well: str)` returns [`BiomationScripter.EchoProto.Action`](#class-action)

**Attributes:**

* `__uid` | `int`: A unique identifier for the liquid transfer event
* `reagent` | `str`: Name of the liquid to be transferred
* `source_plate` | [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout): The source plate containing the reagent
* `calibration` | `str`: Acoustic calibration the Echo525 will use during the liquid transfer event (e.g. "AQ_BP")
* `source_well` | `str`: The well from which the reagent is transferred (e.g. "A1")
* `destination_plate_name` | `str`: The name of the plate to which the reagent will be transferred
* `destination_plate_type` | `str`: The type of the plate to which the reagent will be transferred
* `destination_well` | `str`: The well to which the reagent is transferred (e.g. "B6")
* `_volume` | `int`: The amount of reagent, in nanolitres, which will be transferred

**Methods:**
* `__init__(self, UID: int, Reagent: str, Source_Plate: BiomationScripter.Labware_Layout, Calibration: str, Source_Well: str, Destination_Plate_Name: str, Destination_Plate_Type: str, Destination_Well: str)` returns [`BiomationScripter.EchoProto.Action`](#class-action)
   * Creates a [`BiomationScripter.EchoProto.Action`](#class-action) object
   * `UID` is stored as `self.__uid`
   * `Reagent` is stored as `self.reagent`
   * `Source_Plate` is stored as `self.source_plate`
   * `Calibration` is stored as `self.calibration`
   * `Source_Well` is stored as `self.source_well`
   * `Destination_Plate_Name` is stored as `self.destination_plate_name`
   * `Destination_Plate_Type` is stored as `self.destination_plate_type`
   * `Destination_Well` is stored as `self.destination_well`
   * `self._volume` is initialised as `None`
* `set_volume(self, Volume: int)` returns `None`
   * Stores the volume of liquid, in nanolitres, to be transferred as `self._volume`
   * Checks that the volume specified is valid:
      * Checks that the volume is an `int`
      * Checks that the volume is not below the minimum transfer volume of the Echo525 (25 nL)
      * Checks that the volume is not above the maximum transfer volume for the specified source plate (2000 nL for 384PP plate, and 500 nL for 384 LDV plate)
* `get_volume(self)` returns `int`
   * Returns `self._volume`
* `get_uid(self)` returns `int`
   * Returns `self.__uid`
* `get_all(self)` returns `list[int, str, str, str, str, str, str, str, int]`
   * Returns all attributes of the transfer action as a list in the format: `list[self.__uid, self.reagent, self.source_plate.name, self.calibration, self.source_well, self.destination_plate_name, self.destination_plate_type, self.destination_well, self._volume]`

---

### Functions

### Function: [`Generate_Actions`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/EchoProto/__init__.py)
This function is used to automatically generate liquid transfer instructions for a [`BiomationScripter.EchoProto.Protocol`](#class-protocol) object.

**Usage:**

`BMS.EchoProto.Generate_Actions(Protocol: BiomationScripter.EchoProto.Protocol)` returns `None`

**Behaviour:**

The [`Generate_Actions`](#function-generate_actions) function first generates and stores a [`BiomationScripter.EchoProto.TransferList`](#class-transferlist) object for each attached source plate. Reagents in destination plates attached to the [`Protocol`](#class-protocol) object are then mapped to reagents in source plates attached to the same object, and [`BiomationScripter.EchoProto.Action`](#class-action) objects are generated and attached to the relevant [`TransferList`](#class-transferlist) to capture each liquid transfer event required.

This function can only be called if the [`Protocol`](#class-protocol) object has destination plate(s) which define the final output of the automation protocol, and source plate(s) which contain the required reagents.

### Function: [`Write_Picklists`](https://github.com/intbio-ncl/BiomationScripter/blob/main/BiomationScripter/EchoProto/__init__.py)
This function is used to generate picklists as CSV files from a [`BiomationScripter.EchoProto.Protocol`](#class-protocol) object. The [`Protocol`](#class-protocol) object must have defined source plates, destination plates, and transferlists. The transferlists must also be populated with liquid transfer events.

**Usage:**

`BMS.EchoProto.Write_Picklists(Protocol: BiomationScripter.EchoProto.Protocol, Save_Location: str)` returns `None`

**Behaviour:**

The [`Write_Picklists`](#function-write_picklists) function first gets all [`BiomationScripter.EchoProto.TransferList`](#class-transferlist) objects stored within the [`BiomationScripter.EchoProto.Protocol`](#class-protocol) object. From these [`TransferList`](#class-transferlist) objects, the attached [`BiomationScripter.EchoProto.Action`](#class-action) objects are retrieved and the information captured by each [`Action`](#class-action) object is converted into a string, which is written to a CSV file. The CSV file is stored in the directory specified by `Save_Location`, and can be uploaded to the Echo525 as described [here](#importing-picklists-via-plate-reformat).

---


## Using EchoProto.Templates


### Examples

#### Loop Assembly

This example shows how the Loop Assembly template class can be used to generate picklists for the Echo525.

1. Import the BiomationScripter package and the BiomationScripter.EchoProto.Templates submodule:
   ```python
   import BiomationScripter as BMS
   import BiomationScripter.EchoProto.Templates as Templates
   ```

2. Specify general information for the loop assembly protocol:
   ```python
   # Give the protocol a name
   Protocol_Name = "Example Loop Protocol"
   # What is the final reaction volume for the assemblies in microlitres?
   Final_Reaction_Volume = 5 #uL
   # What is the name of the restriction enzyme which will be used in the assembly?
   Enzyme = "SapI"
   # What ratios of backbone:part(s) should be used?
   Ratios = ["1:1", "1:2"] # Backbone:Part(s)
   # How many repeats should be set up for each assembly?
   Repeats = 1
   # Where should the picklists be saved?
   Picklist_save_directory = ""
   ```

3. Specify the assemblies to be prepared. These should be specified as a list, with a format of `list[Backbone: str, list[part: str]]`:
   ```python
   # Assemblies should be specified in the format of a list
   Assemblies = [
      ["Backbone1", ["Part1", "Part2"]],
      ["Backbone2", ["Part3"]],
      ["Backbone2", ["Part4"]],
   ]
   ```

4. Specify where the DNA parts are stored:
   ```python
   ###################################
   # Specify where the DNA is stored #
   ###################################

   # What is the name of the DNA plate?
   DNA_Plate_Name = "DNA_Plate"
   # What is the type of plate?
   DNA_Plate_Type = "384PP"
   # How many rows does the plate have?
   DNA_Plate_Rows = 16
   # How many columns does the plate have?
   DNA_Plate_Columns = 24

   # What is the volume for each DNA part? This can also be specified separately for each part
   DNA_Source_Volume = 16

   # What are the names of the DNA parts?
   DNA_Names = [
      "Backbone1",
      "Backbone2",
      "Part1",
      "Part2",
      "Part3",
      "Part4"
   ]

   # What is the well location for each part?
   DNA_Source_Wells = [
      "B1",
      "C1",
      "B3",
      "D5",
      "B5",
      "A1"
   ]
   ```

5. Repeat the above for the reagents and water:

   ```python
   #########################################
   # Specify where the reagents are stored #
   #########################################
   Reagent_Plate_Name = "Reagent_Plate"
   Reagent_Plate_Type = "384LDV"
   Reagent_Plate_Rows = 16
   Reagent_Plate_Columns = 24

   Reagent_Source_Volume = 7

   Reagent_Names = [
      "SapI",
      "T4 Ligase Buffer",
      "T4 Ligase"
   ]

   Reagent_Source_Wells = [
      "B1",
      "E1",
      "F1"
   ]

   #####################################
   # Specify where the water is stored #
   #####################################
   Water_Plate_Name = "Water_Plate"
   Water_Plate_Type = "6RES"
   Water_Plate_Rows = 2
   Water_Plate_Columns = 3

   Water_Source_Volume = 2000

   Water_Source_Wells = [
      "A1"
   ]
   ```

6. Define the destination plate:

   ```python
   # Give the destination plate a name
   Destination_Plate_Name = "Destination_Plate"
   # Specify the type of plate
   Destination_Plate_Type = "384 MicroAmp PCR Plate"
   # How many rows does the plate have?
   Destination_Plate_Rows = 16
   # How many columns does the plate have?
   Destination_Plate_Columns = 24
   # Option to provide a range of available wells to be used; if all wells can be used, specify None
   Destination_Plate_Well_Range = None
   # Should the outer wells be used? False means the first and last column and row will be left empty
   Destination_Plate_Use_Outer_Wells = False
   ```

7. Create the source plates:

   ```python
   DNA_Plate = BMS.Labware_Layout(DNA_Plate_Name, DNA_Plate_Type)
   DNA_Plate.define_format(DNA_Plate_Rows,DNA_Plate_Columns)

   content = []
   for Name, Well in zip(DNA_Names,DNA_Source_Wells):
      content.append([Well, Name, DNA_Source_Volume, "AQ_BP"])

   for c in content:
      DNA_Plate.add_content(c[0],c[1],c[2], c[3])


   ##############################################################################
   ##############################################################################

   Reagent_Plate = BMS.Labware_Layout(Reagent_Plate_Name, Reagent_Plate_Type)
   Reagent_Plate.define_format(Reagent_Plate_Rows, Reagent_Plate_Columns)

   content = []
   for Name, Well in zip(Reagent_Names,Reagent_Source_Wells):
      content.append([Well, Name, Reagent_Source_Volume, "AQ_SP"])

   for c in content:
      Reagent_Plate.add_content(c[0],c[1],c[2], c[3])

   ##############################################################################
   ##############################################################################

   Water_Plate = BMS.Labware_Layout(Water_Plate_Name, Water_Plate_Type)
   Water_Plate.define_format(Water_Plate_Rows,Water_Plate_Columns)

   content = []
   for Well in Water_Source_Wells:
      content.append([Well, "Water", Water_Source_Volume, "AQ_BP"])

   for c in content:
      Water_Plate.add_content(c[0],c[1],c[2], c[3])
   ```

8. Create the destination plate format. Note that if multiple destination plates are required, the `Loop_Assembly` class will create these; the destination plate format only needs to be defined once.

   ```python
   Destination_Plate = BMS.Labware_Layout(Destination_Plate_Name, Destination_Plate_Type)
   Destination_Plate.define_format(Destination_Plate_Rows, Destination_Plate_Columns)
   ```

9. Create the protocol:

   ```python
   Protocol = Templates.Loop_Assembly(
      Name = Protocol_Name,
      Enzyme = Enzyme,
      Volume = Final_Reaction_Volume,
      Backbone_to_Part = Ratios,
      repeats = Repeats
   )
   ```

10. Add the source plates and define the destination plate format:

   ```python
   Protocol.add_source_plate(DNA_Plate)
   Protocol.add_source_plate(Reagent_Plate)
   Protocol.add_source_plate(Water_Plate)

   Protocol.define_destination_plate(Destination_Plate, Well_Range = Destination_Plate_Well_Range, Use_Outer_Wells = Destination_Plate_Use_Outer_Wells)
   ```

11. Add the assemblies:

   ```python
   for Assembly in Assemblies:
      Protocol.add_assembly(Assembly[0], Assembly[1])
   ```

12. Create and save the picklists:

   ```python
   Protocol.make_picklist(Picklist_save_directory)
   ```

Full code below:

```python
import BiomationScripter as BMS
import BiomationScripter.EchoProto.Templates as Templates

############################################################
# Edit the code in this cell with details of your protocol #
############################################################

Protocol_Name = "Example Loop Protocol"
Final_Reaction_Volume = 5 #uL
Enzyme = "SapI"
Ratios = ["1:1", "1:2"] # Backbone:Part(s)
Repeats = 1
Picklist_save_directory = ""

##############################
# Specify Assembly Reactions #
##############################

Assemblies = [
    ["Backbone1", ["Part1", "Part2"]],
    ["Backbone2", ["Part3"]],
    ["Backbone2", ["Part4"]],
]

###################################
# Specify where the DNA is stored #
###################################

DNA_Plate_Name = "DNA_Plate"
DNA_Plate_Type = "384PP"
DNA_Plate_Rows = 16
DNA_Plate_Columns = 24

DNA_Source_Volume = 16

DNA_Names = [
    "Backbone1",
    "Backbone2",
    "Part1",
    "Part2",
    "Part3",
    "Part4"
]

DNA_Source_Wells = [
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6"
]

#########################################
# Specify where the reagents are stored #
#########################################
Reagent_Plate_Name = "Reagent_Plate"
Reagent_Plate_Type = "384LDV"
Reagent_Plate_Rows = 16
Reagent_Plate_Columns = 24

Reagent_Source_Volume = 7

Reagent_Names = [
    "SapI",
    "T4 Ligase Buffer",
    "T4 Ligase"
]

Reagent_Source_Wells = [
    "B1",
    "E1",
    "F1"
]

#####################################
# Specify where the water is stored #
#####################################
Water_Plate_Name = "Water_Plate"
Water_Plate_Type = "6RES"
Water_Plate_Rows = 2
Water_Plate_Columns = 3

Water_Source_Volume = 2000

Water_Source_Wells = [
    "A1"
]

#############################
# Specify destination plate #
#############################
Destination_Plate_Name = "Destination_Plate"
Destination_Plate_Type = "384 MicroAmp PCR Plate"
Destination_Plate_Rows = 16
Destination_Plate_Columns = 24
Destination_Plate_Well_Range = None # Specify a range of wells which are available for use, otherwise leave as `None`
Destination_Plate_Use_Outer_Wells = False

########################
# Create Source Plates #
########################
DNA_Plate = BMS.Labware_Layout(DNA_Plate_Name, DNA_Plate_Type)
DNA_Plate.define_format(DNA_Plate_Rows,DNA_Plate_Columns)

content = []
for Name, Well in zip(DNA_Names,DNA_Source_Wells):
    content.append([Well, Name, DNA_Source_Volume, "AQ_BP"])

for c in content:
    DNA_Plate.add_content(c[0],c[1],c[2], c[3])


##############################################################################
##############################################################################

Reagent_Plate = BMS.Labware_Layout(Reagent_Plate_Name, Reagent_Plate_Type)
Reagent_Plate.define_format(Reagent_Plate_Rows, Reagent_Plate_Columns)

content = []
for Name, Well in zip(Reagent_Names,Reagent_Source_Wells):
    content.append([Well, Name, Reagent_Source_Volume, "AQ_SP"])

for c in content:
    Reagent_Plate.add_content(c[0],c[1],c[2], c[3])

##############################################################################
##############################################################################

Water_Plate = BMS.Labware_Layout(Water_Plate_Name, Water_Plate_Type)
Water_Plate.define_format(Water_Plate_Rows,Water_Plate_Columns)

content = []
for Well in Water_Source_Wells:
    content.append([Well, "Water", Water_Source_Volume, "AQ_BP"])

for c in content:
    Water_Plate.add_content(c[0],c[1],c[2], c[3])

##############################################################################
##############################################################################

Destination_Plate = BMS.Labware_Layout(Destination_Plate_Name, Destination_Plate_Type)
Destination_Plate.define_format(Destination_Plate_Rows, Destination_Plate_Columns)

##############################################
# Create protocol and convert to picklist(s) #
##############################################

Protocol = Templates.Loop_Assembly(
    Name = Protocol_Name,
    Enzyme = Enzyme,
    Volume = Final_Reaction_Volume,
    Backbone_to_Part = Ratios,
    repeats = Repeats
)

Protocol.add_source_plate(DNA_Plate)
Protocol.add_source_plate(Reagent_Plate)
Protocol.add_source_plate(Water_Plate)

Protocol.define_destination_plate(Destination_Plate, Well_Range = Destination_Plate_Well_Range, Use_Outer_Wells = Destination_Plate_Use_Outer_Wells)

for Assembly in Assemblies:
    Protocol.add_assembly(Assembly[0], Assembly[1])

Protocol.make_picklist(Picklist_save_directory)
```

---

### Simulating Protocols



---


### Template Classes
