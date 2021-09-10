<!-- markdownlint-disable -->

# <kbd>module</kbd> `BiomationScripter.EchoProto.Templates`






---

## <kbd>class</kbd> `Loop_Assembly`
Protocol template for setting up Loop assembly reactions using the Echo 525. 



**Attributes:**
 name (str): A name for the protocol. 

volume (float): The final volume for the Loop assembly reactions in micorlitres. 
 - <b>`Default`</b>:  5 

ratios (list[str]): A list of Backbone:Part ratios 
 - <b>`Example`</b>:  ["1:1", "1:2", "2:1"] 
 - <b>`Default`</b>:  ["1:1"] 

splates (list[BiomationScripter.PlateLayout]): A list of source plates which contain the required reagents. 

dplate_format (list[list[BiomationScripter.PlateLayout, list[str]]]): A list of two-element lists, where the first element is an empty PlateLayout object with a defined format to be used as the destination plate, and the second element is a list of available wells. 
 - <b>`Example`</b>:  [[BiomationScripter.PlateLayout, ["A1","A2","A3"]],...] 

assemblies (list[str,list[str]]): A list of assemblies specified using two-element lists, where the first element is the backbone, and the second element is a list of parts 
 - <b>`Example`</b>:  [["Backbone", ["Part1","Part2"]],...] 

repeats (int): The number of reactions to be prepared for each assembly specified. 
 - <b>`Default`</b>:  1 

_enzyme_amount (float): The amount of enzyme, in microliters, to add per 5 microlitres of reaction. 
 - <b>`Default`</b>:  0.125 

_ligase_buffer_amount (float): The amount of ligase buffer, in microliters, to add per 5 microlitres of reaction. 
 - <b>`Default`</b>:  0.5 

_ligase_amount (float): The amount of ligase, in microliters, to add per 5 microlitres of reaction. 
 - <b>`Default`</b>:  0.125 

_backbone_amount (float): Amount of DNA backbone, in microlitres, to add per 5 microlitre reaction, assuming 1:1 backbone:part ratio, and 10 fmol stock concentration. 
 - <b>`Default`</b>:  0.25 

_part_amount (float): Amount of each DNA part, in microlitres, to add per 5 microlitre reaction, assuming 1:1 backbone:part ratio, and 10 fmol stock concentration. 
 - <b>`Default`</b>:  0.25 

enzyme (str): Enzyme name. This should match the name given in the BiomationScripter.PlateLayout source plate(s). 

ligase_buffer (str): Ligase Buffer name. This should match the name given in the BiomationScripter.PlateLayout source plate(s). 
 - <b>`Default`</b>:  "T4 Ligase Buffer") 

ligase (str): Ligase name. This should match the name given in the BiomationScripter.PlateLayout source plate(s). 
 - <b>`Default`</b>:  "T4 Ligase" 

water (str): Water name. This should match the name given in the BiomationScripter.PlateLayout source plate(s). 
 - <b>`Default`</b>:  "Water" 

### <kbd>method</kbd> `__init__`

```python
__init__(Name, Enzyme, Volume=5, Backbone_to_Part=['1:1'], repeats=1)
```








---

### <kbd>method</kbd> `add_assembly`

```python
add_assembly(Backbone, Parts)
```





---

### <kbd>method</kbd> `add_source_plate`

```python
add_source_plate(SPlate)
```





---

### <kbd>method</kbd> `define_destination_plate`

```python
define_destination_plate(Plate_Layout, Well_Range=None, UseOuterWells=True)
```





---

### <kbd>method</kbd> `make_picklist`

```python
make_picklist(Directory)
```






---

## <kbd>class</kbd> `Q5PCR`




### <kbd>method</kbd> `__init__`

```python
__init__(Name, Volume, Master_Mix=False)
```








---

### <kbd>method</kbd> `add_sample`

```python
add_sample(Template, Primer1, Primer2)
```





---

### <kbd>method</kbd> `add_source_plate`

```python
add_source_plate(SPlate)
```





---

### <kbd>method</kbd> `define_destination_plate`

```python
define_destination_plate(
    Type,
    Rows,
    Columns,
    Name=None,
    UseOuterWells=True,
    DestinationWellRange=None,
    gap=0
)
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
