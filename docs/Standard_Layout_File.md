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



# BiomationScripter - Standard Layout File

    
---

## Overview

The standard layout file is an Excel file that can be used for storing information about plates used in protocols. This should be used for recording the location of  liquids within a given plate. Information contained within this file can be imported into a protocol using the ImportPlate or ImportLabware functions.

---

## Specification

The standard layout file consists of two sheets:
* **Plate Summary** is for attributes of the plate
* **Well lookup** is for the well contents

### Plate Summary
Plate Summary utilises 8 rows in the current version
* `Plate Name` | `str`: Name given to the plate by the user (_required_)
* `Plate Type` | `str`: Type of the plate e.g., 96-well, 384PP (_required_)
* `Total Wells` | `int`: Number of wells for the plate type (_optional_)
* `Rows` | `int`: Number of rows for the plate type (_optional_)
* `Columns` | `int`: Number of columns for the plate type (_optional_)
* `Minimum working volume` | `float`: Least volume that the wells can contain for operation (_optional_)
* `Maximum working volume` | `float`: Greatest volume that the wells can contain for operation (_optional_)
* `Description` | `str`: Field available for the user to write a summary of the plate's intended usage (_optional_)

### Well Lookup
Well lookup utilises 10 columns in the current version. The number of rows is dependent on the number of wells of the plate; each well should have its own row.
* `Well` | `str`: Name given to the well e.g., A1
* `Row` | `str`: Name given to the row e.g., A
* `Column` | `str`: Name given to the column e.g., 1
* `Name` | `str`: Content of the well e.g., T4 Ligase Buffer
* `Volume (uL) - Initial` | `float`: Volume of the liquid originally contained in the well
* `Concentration (ng/uL)` | `float`: Concentration of the liquid in ng/uL
* `Concentration (uM)` | `float`: Concentration of the liquid in uM
* `Volume (uL) - Current` | `float`: Volume of the liquid currently contained in the well i.e., after the last protocol
* `Calibration Type` | `str`: Calibration Type of the liquid or labware. Should be specified for when using EchoProto. e.g., AQ_BP
* `Notes` | `str`: Field available for the user to leave any comments regarding the well such as the source of the stock, expiry date of reagent, etc.

---

## Example Usage

Included for these docs is an example of this layout file for a plate used to store primers

<a href = "/">
<img src="../wiki-images/PlateSummary.png" alt = "Plate Summary sheet for \"Primers\" plate" width = "300"/>
   </a>
<a href = "/">
<img src="../wiki-images/WellLookup.png" alt = "Well lookup sheet for \"Primers\" plate" width = "800"/>
   </a>
   
---

## Resources

The example sheets can be found here: <a href = "../protocol_examples/standard_layout_file">Standard Layout File</a>
Each sheet has been separated into a `.csv` file for compliance with github

---
