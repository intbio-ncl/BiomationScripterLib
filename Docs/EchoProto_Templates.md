<center>
<a href = "Home.md">
<img src="../Resources/.wiki-images/Logo - Full Name.png" alt = "BiomationScripter Logo" width = "300"/>
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

# BiomationScripter - EchoProto - Templates
---

[Overview](#overview) | [All Templates](#echo-templates) | [EchoProto Template Superclass](#superclass-echoproto_template)

---

## Overview

BiomationScripter Templates can be used to help quickly and easily generate automation protocols for common experiments or procedures. Protocols generated using the same Template will all follow the same basic instructions, but will differ depending on user inputs. For example, the PCR Template accepts user inputs for aspects such as the type of polyemrase and buffer, the final volume of the reactions, and the DNA templates and primers to use in each reaction.

If you can't find a Template for a specific protocol, you can try [raising an issue](https://github.com/intbio-ncl/BiomationScripterLib/issues) on the GitHub to see if anyone can help, or create your own Template [following the walkthrough found here](Example_Code_Snippets/EchoProto/EchoProto-EchoProto_Template-Superclass.ipynb).

Below you can find documentation for Echo Templates included with BiomationScripter.

---

## Echo Templates

[`Loop_Assembly`](#template-loop_assembly) | [`PCR`](#template-pcr)

### Template: [`Loop_Assembly`](../BiomationScripter/EchoProto/Templates.py)

#### Overview:

This Template is used to generate an Echo protocol for preparing Loop assembly reactions. The protocol is based on the methods described by [Pollak *et al.* 2018](https://doi.org/10.1111/nph.15625).

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
                                        Enzyme: str,
                                        Buffer: str/List[str],
                                        Volume: float,
                                        Assemblies: List[BiomationScripter.Assembly],
                                        Backbone_to_Part: List[str] = ["1:1"],
                                        Repeats: int = 1,
                                        Name: str,
                                        Source_Plates: List[BiomationScripter.Labware_Layout],
                                        Destination_Plate_Layout: BiomationScripter.Labware_Layout,
                                        Picklist_Save_Directory: str = ".",
                                        Metadata: dict[str, str],
                                        Merge: bool = False
)
```

#### Full Documentation

**Attributes:**

* `name` | `str`: A name for the protocol (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `metadata` | `dict[str]`: A dictionary describing the metadata for the protocol (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `save_dir` | `str`: The directory where the picklist files should be saved (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `_protocol` | [`BiomationScripter.EchoProto.Protocol`](EchoProto.md#class-protocol): A [`BiomationScripter.EchoProto.Protocol`](EchoProto.md#class-protocol) object (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `merge` | `bool`: Defines whether source plates of the same type should be merged into one picklist (`True`) or if each source plate should have a different picklist (`False`) (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `source_plate_layouts` | `list[BiomationScripter.Labware_Layout]`: A list of [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects describing the source plates available for use (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `destination_plate_layouts` | `list[BiomationScripter.Labware_Layout]`: A list of [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects which define the destination plates, including their intended content once the transfer has completed (from [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass)
* `volume` | `float`: Final volume of each reaction in microlitres
* `ratios` | `list[str]`: A list of backbone:part ratios, e.g. `["1:1", "2:1"]`
* `repeats` | `int`: The number of repeats for each unique assembly reaction
* `enzyme` | `str`: The name of the enzyme to be used
* `buffer` | `str/List[str]`: The name of the buffer (or buffers) to be used
* `assemblies` | `List[BMS.Assembly]`: A list of [`BiomationScripter.Assembly`](BiomationScripter.md#class-assembly) objects which describe the assembly reactions to be prepared
* `ligase` | `str`: The name of the ligase to use
* `water` | `str`: The name of the water to be added

**Methods:**

* `__init__(self, Enzyme: str, Buffer: str/List[str], Volume: float, Assemblies: List[BiomationScripter.Assembly], Backbone_to_Part: List[str] = ["1:1"], Repeats: int = 1, Name: str, Source_Plates: List[BiomationScripter.Labware_Layout], Destination_Plate_Layout: BiomationScripter.Labware_Layout, Picklist_Save_Directory: str = ".", Metadata: dict[str, str], Merge: bool = False)` returns [`BMS.EchoProto.Templates.Loop_Assembly`](#template-loop_assembly) object
    * Creates a [`BMS.EchoProto.Templates.Loop_Assembly`](#template-loop_assembly) object
    * Initiates the default reaction volumes (see above)
* `run(self)` returns `None`
    * Creates the Echo picklists for the protocol


### Template: [`PCR`](../BiomationScripter/EchoProto/Templates.py)

#### Overview:

This Template is used to generate an Echo protocol for preparing PCR reactions. It is based upon the protocol described [here]().


---

## Superclass: [`EchoProto_Template`](../BiomationScripter/EchoProto/__init__.py)

**Usage:**

This class should ONLY be used as an extension of an Echo Template class, e.g.:

```Python
class My_New_Template(BMS.EchoProto.EchoProto_Template):
  def __init__(self, My_Arg1, My_Arg2, **kwargs):

    super().__init__(**kwargs)

    self.my_arg1 = My_Arg1
    self.my_arg2 = My_Arg2

  def run(self):
    pass
```

[See the walkthrough here](Example_Code_Snippets/EchoProto/EchoProto-EchoProto_Template-Superclass.ipynb).

**Attributes:**

* `name` | `str`: A name for the protocol
* `metadata` | `dict[str]`: A dictionary describing the metadata for the protocol
* `save_dir` | `str`: The directory where the picklist files should be saved
* `_protocol` | [`BiomationScripter.EchoProto.Protocol`](EchoProto.md#class-protocol): A [`BiomationScripter.EchoProto.Protocol`](EchoProto.md#class-protocol) object
* `merge` | `bool`: Defines whether source plates of the same type should be merged into one picklist (`True`) or if each source plate should have a different picklist (`False`)
* `source_plate_layouts` | `list[BiomationScripter.Labware_Layout]`: A list of [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects describing the source plates available for use
* `destination_plate_layouts` | `list[BiomationScripter.Labware_Layout]`: A list of [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects which define the destination plates, including their intended content once the transfer has completed


**Methods:**

* `__init__(self, Name: str, Source_Plates: List[BiomationScripter.Labware_Layout], Destination_Plate_Layout: BiomationScripter.Labware_Layout, Picklist_Save_Directory: str = ".", Metadata: dict[str, str], Merge: bool = False)` returns [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass
    * This method is inherently called when an Echo Template class extends the [`BMS.EchoProto.EchoProto_Template`](#superclass-echoproto_template) superclass
    * The [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) objects used for `Source_Plates` must contain content representing the source material available
    * The [`BiomationScripter.Labware_Layout`](https://github.com/intbio-ncl/BiomationScripter/wiki/BiomationScripter#class-Labware_Layout) object used for `Destination_Plate_Layout` should have no content specified; this is generated by the Template class
    * The `Destination_Plate_Layout` will be assumed to have all wells available if its `available_wells` attribute has not been specified
* `add_source_layout(self, Layout: BiomationScripter.Labware_Layout)` returns `None`
    * This method is used to add a source plate layout
    * This is called within the `__init__` function when a Template object is generated, and so users should not need to call it manually
    * If source plate layouts are added after object creation, they should only be added using this method; if they are added by simply appending to `self.source_plate_layouts` unexpected behaviour will occur
* `add_destination_layout(self, Layout: BiomationScripter.Labware_Layout)` returns `None`
    * This method is used to add a destination plate layout
    * The first destination layout is added when `__init__` is called
    * Users may need to call this during the `run` method of their template if additional destination plates are required
    * If destination plate layouts are added after object creation, they should only be added using this method; if they are added by simply appending to `self.destination_plate_layouts` unexpected behaviour will occur
* `create_picklists(self)` returns `None`
    * This method should be called at the end of a Template `run` method to generate the Echo picklists
