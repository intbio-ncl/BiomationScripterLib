import os
import math as _math
import random
import warnings
from typing import Dict, List, Union, Tuple

try:
    import pandas as pd
except ImportError:
    warnings.warn("No pandas, continue at your own zoological peril 🐼")

# Exception classes #
class BiomationError(Exception):
    """A general exception for BiomationScripter"""
    pass

class NegativeVolumeError(BiomationError):
    pass


class RobotConfigurationError(BiomationError):
    pass


class BMSTemplateError(BiomationError):
    pass


class LabwareError(BiomationError):
    pass


class OutOFSourceMaterial(BiomationError):
    pass


class DoEError(BiomationError):
    pass


class TransferError(BiomationError):
    pass


# Function to pass template modules
def get_template_module(module_name):
    if module_name == "OTProto":
        import BiomationScripter.OTProto.Templates as OTProto_Templates

        return OTProto_Templates

    elif module_name == "EchoProto":
        import BiomationScripter.EchoProto.Templates as EchoProto_Templates

        return EchoProto_Templates

    raise ValueError(f"invald module_name ({module_name!r}) passed to get_template_module")


#####################
# Classes


class DoE_Material:
    def __init__(self, ID, Material_Type, Factors=None, Factor_Values=None):
        if (Factors and not Factor_Values) or (not Factors and Factor_Values):
            raise DoEError(
                f"Error creating source type {Material_Type} {ID}"
                " - factor names or factor values were specified without the other."
            )

        self.id = ID
        self.material_type = Material_Type
        self.factors = {}

        if Factors:
            for factor, value in zip(Factors, Factor_Values):
                self.factors[factor] = value

    def get_factor_value(self, Factor):
        return self.factors[Factor]


class DoE_Intermediate:
    def __init__(
        self,
        ID,
        Intermediate_Type,
        Component_Types,
        Component_IDs,
        Component_Amount_Types,
        Component_Amount_Values,
    ):
        self.id = ID
        self.intermediate_type = Intermediate_Type
        self.components = {}

        for component_type, id, amount_type, amount_value in zip(
            Component_Types, Component_IDs, Component_Amount_Types, Component_Amount_Values
        ):
            self.components[component_type] = [id, amount_type, amount_value]

    def get_component_id(self, Component):
        return self.components[Component][0]

    def get_component_amount_info(self, Component):
        return self.components[Component][1:]


class DoE_Experiment:
    def __init__(self, Name, DoE_File):
        self.name = Name
        self.doe_file = DoE_File
        self.materials = {}
        self.intermediates = {}

        # Open the CSV file containing the DoE run data
        file = open(DoE_File, "r")
        # Store the DoE data from the file as a list
        data = []
        for row in file:
            data.append(row)

        # Close the file
        file.close()

        # Remove any empty lines imported
        if "" in data:
            data.remove("")

        # Get the factor names
        self.factors = data[0].replace("\n", "").split(",")

        # store run data using the DoE_Run_Data class
        self.runs = []
        ID = 0
        for run in data[1:]:
            # remove new line symbols if present, and convert string to a list
            run = run.replace("\n", "").split(",")
            if "" in run:
                raise ValueError(
                    f"Missing value found in run {ID} for factor {self.factors[run.index('')]}; "
                    "check that all values are present and objectives are not present in the file."
                )
            self.runs.append(DoE_Run_Data(ID, self.factors, run))
            ID += 1

    def add_material(self, Material):
        self.materials[Material.id] = Material

    def get_material(self, Material_Name):
        return self.materials[Material_Name]

    def add_intermediate(self, Intermediate):
        self.intermediates[Intermediate.id] = Intermediate

    def get_intermediate(self, Intermediate_Name):
        return self.intermediates[Intermediate_Name]

    def get_run(self, ID):
        for run in self.runs:
            if run.id == ID:
                return run

    def batch_by_factor_value(self, Factor, Value):
        batched_experiment = DoE_Experiment(
            "{}-Batched-{}-{}".format(self.name, Factor, Value), self.doe_file
        )
        runs = batched_experiment.runs.copy()
        for run in runs:
            if not run.get_factor_value(Factor) == Value:
                batched_experiment.runs.remove(run)
        return batched_experiment

    def get_all_values(self, Name):
        Values = []
        for run in self.runs:
            Values.append(run.get_value_by_name(Name))

        return Values


class DoE_Run_Data:
    def __init__(self, ID, Factors, Values):
        self.id = ID
        self.source_materials = {}
        self.intermediates = {}
        self.run_data = {}
        for factor, value in zip(Factors, Values):
            self.run_data[factor] = value

    def get_factor_value(self, Factor):
        return self.run_data[Factor]

    def add_factor(self, Factor, Value):
        self.run_data[Factor] = Value

    def specify_source_material(self, Material, Value):
        self.source_materials[Material] = Value

    def get_source_material_value(self, Source_Material):
        return self.source_materials[Source_Material]

    def specify_intermediate(self, Intermediate, Value):
        self.intermediates[Intermediate] = Value

    def get_intermediate_value(self, Intermediate):
        return self.intermediates[Intermediate]

    def get_value_by_name(self, Name):
        found = False
        Value = None
        if not found:
            try:
                Value = self.get_factor_value(Name)
                found = True
            except KeyError:
                pass
        if not found:
            try:
                Value = self.get_source_material_value(Name)
                found = True
            except KeyError:
                pass
        if not found:
            try:
                Value = self.get_intermediate_value(Name)
                found = True
            except KeyError:
                pass
        if not found:
            raise DoEError("Cannot find {}.".format(Name))
        else:
            return Value


class Labware_Content:
    """This class is used by `Labware_Layout` to store content information."""

    def __init__(self, Name: str, Volume: Union[float, int], Liquid_Class: Union[str, None] = None):
        self.name = Name
        self.volume = Volume
        self.liquid_class = Liquid_Class

    def get_info(self):
        return [self.name, self.volume, self.liquid_class]


class Assembly:
    """This class is used to store basic information about a DNA assembly."""

    def __init__(self, Name: str, Backbone: str, Parts: List[str]):
        self.name = Name
        self.backbone = Backbone
        self.parts = Parts


class Labware_Layout:
    """This class is used to store information, such as number of wells and content, about labware which can later be retrieved.

    The BMS.Labware_Layout class is intended to be universal within BiomationScripter, and not specific to any particular automation equipment.
    Labware_Layout objects are separate from, but sometimes related to, any object which is meant to represent a physical instance of a piece of labware.
    """

    def __init__(self, Name: str, Type: str):
        self.name: str = Name
        self.type: str = Type
        self.rows: int = None
        self.columns: int = None
        self.content: Dict[str, List[Labware_Content]] = {}
        self.available_wells: List[str] = None
        self.empty_wells: List[str] = None
        self.well_labels: Dict[str, str] = {}

    def get_total_volume_of_liquid(self, Liquid):
        wells = self.get_wells_containing_liquid(Liquid)
        total_volume = 0
        for well in wells:
            total_volume += self.get_volume_of_liquid_in_well(Liquid, well)

        return total_volume

    def define_format(self, Rows: int, Columns: int):
        self.rows = Rows
        self.columns = Columns

    def get_format(self):
        return (self.rows, self.columns)

    def set_available_wells(
        self, Well_Range=None, Use_Outer_Wells=True, Direction="Horizontal", Box=False
    ):
        self.available_wells = self.get_well_range(Well_Range, Use_Outer_Wells, Direction, Box)
        self.empty_wells = self.available_wells.copy()

    def get_available_wells(self):
        return self.available_wells

    def get_well_range(
        self, Well_Range=None, Use_Outer_Wells=True, Direction="Horizontal", Box=False
    ):
        if not Direction == "Horizontal" and not Direction == "Vertical":
            raise ValueError("`Direction` must be either 'Horizontal' or 'Vertical'")

        n_rows = self.rows
        n_cols = self.columns
        if Well_Range is None:
            Well_Range = "A1:{}{}".format(chr(64 + n_rows), n_cols)

        wells = well_range(Well_Range, Labware_Format=self, Direction=Direction, Box=Box)

        if not Use_Outer_Wells:
            plate_first_row = "A"
            plate_last_row = chr(64 + n_rows)
            plate_first_col = 1
            plate_last_col = n_cols

            temp_wells = []
            for w in wells:
                if (
                    (plate_first_row in w)
                    or (plate_last_row in w)
                    or (str(plate_first_col) == w[1:])
                    or (str(plate_last_col) == w[1:])
                ):
                    continue
                else:
                    temp_wells.append(w)
            wells = temp_wells

        return wells

    def check_well(self, Well):
        Row = Well[0]
        Column = int(Well[1:])
        InRange = None
        if Row > chr(64 + self.rows):
            InRange = False
        elif Column > self.columns:
            InRange = False
        else:
            InRange = True
        return InRange

    def clone_format(self, New_Name):
        # Does not copy content
        name = New_Name
        type = self.type
        rows = self.rows
        columns = self.columns
        plate_copy = Labware_Layout(name, type)
        plate_copy.define_format(rows, columns)
        return plate_copy

    def bulk_add_content(self, Wells, Reagents, Volumes, Liquid_Classes = None):
        if type(Volumes) is int or type(Volumes) is float:
            Volumes = [Volumes] * len(Wells)
        if Liquid_Classes is None:
            for well, reagent, volume in zip(Wells, Reagents, Volumes):
                self.add_content(well, reagent, volume)
        else:
            for well, reagent, volume, liquid_class in zip(Wells, Reagents, Volumes, Liquid_Classes):
                self.add_content(well, reagent, volume, liquid_class)

    def add_content(self, Well, Reagent, Volume, Liquid_Class=None):
        if Volume < 0:
            raise NegativeVolumeError

        if self.available_wells and ":" not in Well and not type(Well) == list:
            if Well not in self.available_wells:
                raise LabwareError(
                    f"Available wells are specified, but well {Well} is not defined as available. "
                    "Check that the correct well has been specified. "
                    f"Available wells are: {self.available_wells}\n"
                )

        # Volume should always be uL
        if Liquid_Class is None:
            Liquid_Class = "Unknown"
        if ":" in Well:
            for w in well_range(Well, Labware_Format=self):
                self.add_content(w, Reagent, Volume, Liquid_Class)
        elif type(Well) == list:
            for well in Well:
                self.add_content(well, Reagent, Volume, Liquid_Class)
        elif Well in self.content:
            self.content[Well].append(Labware_Content(Reagent, float(Volume), Liquid_Class))
        else:
            self.content[Well] = [Labware_Content(Reagent, float(Volume), Liquid_Class)]

        if self.empty_wells and Well in self.empty_wells:
            self.empty_wells.remove(Well)

    def add_well_label(self, Well: str, Label: str):
        for well in self.well_labels:
            if self.well_labels[well] == Label:
                raise LabwareError(
                    'Label "{}" is already used as a label in {}'.format(Label, well)
                )
        self.well_labels[Well] = Label

    def get_well_content_by_label(self, Label: str):
        for well in self.well_labels:
            if self.well_labels[well] == Label:
                return self.content[well]
        return None

    def get_well_location_by_label(self, Label: str):
        for well in self.well_labels:
            if self.well_labels[well] == Label:
                return well

        return None

    def get_content(self):
        return self.content

    def get_occupied_wells(self):
        return list(self.get_content().keys())

    def get_liquids_in_well(self, Well):
        if Well not in self.get_occupied_wells():
            raise LabwareError("Well {} in labware {} contains no liquids.".format(Well, self.name))

        liquids_in_well = []
        content_in_well = self.content[Well]
        for content in content_in_well:
            liquids_in_well.append(content.name)

        return liquids_in_well

    def get_wells_containing_liquid(self, Liquid_Name):
        wells_to_return = []
        content = self.get_content()
        wells = self.get_occupied_wells()
        for well in wells:
            for liquid in content[well]:
                if liquid.name == Liquid_Name:
                    wells_to_return.append(well)
        return wells_to_return

    def clear_content(self):
        self.content = {}
        if self.available_wells:
            self.empty_wells = self.available_wells.copy()

    def clear_content_from_well(self, Well):
        del self.content[Well]

        if self.empty_wells:
            self.empty_wells.append(Well)

    def clear_liquid_in_well(self, Well, Liquid):
        well_contents = self.content[Well].copy()
        for content in well_contents:
            if Liquid == content.name:
                self.content[Well].remove(content)

        # Check if the well is now empty
        if len(self.content[Well]) == 0:
            # Clean up
            self.clear_content_from_well(Well)

    def get_next_empty_well(self):
        if not self.available_wells:
            raise LabwareError(
                "Available wells must be specified to get the next empty well. "
                f"Specify the avilable wells for {self.name} using `.set_available_wells`."
            )
        if len(self.empty_wells) == 0:
            return None
        # Iterate through all available wells, and return the first one which also exists in the empty wells attribute
        for well in self.available_wells:
            if well in self.empty_wells:
                return well

    def get_volume_of_liquid_in_well(self, Liquid, Well):
        # if not Well in self.get_occupied_wells():
        #     raise LabwareError("Well {} in labware {} contains no liquids.".format(Well, self.name))
        well_content = self.get_content()[Well]
        for content in well_content:
            if content.name == Liquid:
                return content.volume

        return 0.0

    def update_volume_in_well(self, Volume, Reagent, Well):
        if Well not in self.get_content().keys():
            raise LabwareError(
                "{} has not been previously defined. Add content to this well using the `add_content` method.".format(
                    Well
                )
            )
        well_content = self.get_content()[Well]
        for content in well_content:
            if content.name == Reagent:
                content.volume = float(Volume)

    def print(self):
        print("\033[1mInformation for " + self.name + "\033[0m")
        print("Plate Type: " + self.type)
        content = self.get_content()
        print("Well\tVolume(uL)\tLiquid Class\tReagent")
        content_return = ""
        for well in content:
            for c in content[well]:
                content_return += (
                    well + "\t" + str(c.volume) + "\t\t" + c.liquid_class + "\t\t" + c.name + "\n"
                )
                print(well + "\t" + str(c.volume) + "\t\t" + c.liquid_class + "\t\t" + c.name)
        return content_return

    def import_labware(self, filename, path="~", ext=".xlsx"):
        return self.import_plate(filename, path, ext)

    # create a dummy PlateLayout object before running this method
    def import_plate(self, filename, path="~", ext=".xlsx"):
        # check if filename contains the extension
        # NOTE: this only checks for a "." so could easily throw errors if given atypical input
        if "." in filename:
            # look at Sheet1 (the Plate Metadata)
            sheet1 = pd.read_excel(path + filename, sheet_name=0, header=None, engine="openpyxl")
            # look at Sheet2 (the Well lookup)
            sheet2 = pd.read_excel(path + filename, sheet_name=1, engine="openpyxl")
        else:
            # add extension (default = ".xlsx") to arg1
            sheet1 = pd.read_excel(
                path + filename + ext, sheet_name=0, header=None, engine="openpyxl"
            )
            sheet2 = pd.read_excel(path + filename + ext, sheet_name=1, engine="openpyxl")

        # get plate name and plate type from Sheet 1
        # TODO: throw an error message if the name and/or type are blank
        self.name = sheet1[1].iloc[0]  # column 2, row 1
        self.type = sheet1[1].iloc[1]  # column 2, row 2

        # if Current Volume column is empty (NaN), replace with Initial Volume
        sheet2["Volume (uL) - Current"].fillna(sheet2["Volume (uL) - Initial"], inplace=True)
        # if both Volume columns are empty, replace with zeroes
        # TODO: add a warning to the user to say they are empty
        sheet2["Volume (uL) - Current"].fillna(0, inplace=True)
        # TODO: add a warning that liquid class has been set to a default value
        sheet2["Calibration Type"].fillna("AQ_BP", inplace=True)
        # select subset of columns as "content"
        content = sheet2[["Well", "Name", "Volume (uL) - Current", "Calibration Type"]]
        # delete rows where the Name is blank
        content = content.dropna(subset=["Name"])
        # iterate over rows
        for row in content.itertuples(index=False):
            # add contents to PlateLayout object
            self.add_content(row[0], row[1], row[2], row[3])
        return self


class Liquids:
    """This class is used to store information about liquids and where they are stored."""

    def __init__(self):
        self.liquids = {}

    def add_liquid(self, liquid: str, labware: Union[str, Labware_Layout], source_well: str):
        """Adds a liquid to self.liquids"""
        self.liquids[liquid] = [labware, source_well]

    def get_liquids_in_labware(self, labware: Union[str, Labware_Layout]):
        """Returns all liquids within a specified labware."""
        liquids_to_return = []
        for liquid in self.liquids:
            if labware == self.get_liquid_labware(liquid):
                liquids_to_return.append(liquid)

        return liquids_to_return

    def get_liquid_by_location(self, labware, well):
        liquid_to_return = None
        for liquid in self.liquids:
            if labware == self.get_liquid_labware(liquid) and well == self.get_liquid_well(liquid):
                liquid_to_return = liquid
                break
        if liquid_to_return is None:
            raise ValueError("No liquid found in labware {} at well {}".format(labware, well))
        else:
            return liquid_to_return

    def get_liquid(self, liquid):
        return self.liquids[liquid]

    def get_liquid_labware(self, liquid):
        return self.liquids[liquid][0]

    def get_liquid_well(self, liquid):
        return self.liquids[liquid][1]

    def add_liquids_to_labware(self, liquids, labware, blocked_wells=None, well_range=None):
        if well_range:
            wells = well_range
        else:
            wells = list(labware.wells_by_name().keys())

        if blocked_wells:
            for bw in blocked_wells:
                wells.remove(bw)
        for liquid in liquids:
            self.liquids[liquid] = [labware, wells[0]]
            wells.remove(wells[0])

    def get_all_liquids(self):
        return list(self.liquids.keys())


class Mastermix:
    """This class is used by BMS.Mastermix_Maker to store information about a mastermix. It is not intended for use outside of this function."""

    def __init__(self, Name: str, Reagents: str, Wells: List[str]):
        self.name = Name
        self.reagents = Reagents
        self.wells = Wells

##########################################
# Functions


def Aliquot_Calculator(Liquid, Destination_Layouts, Aliquot_Volume, Dead_Volume):
    # Calculate total volume of liquid in all destinations provided
    total_volume = 0
    for destination_layout in Destination_Layouts:
        total_volume += destination_layout.get_total_volume_of_liquid(Liquid)

    num_aliquots = _math.ceil(total_volume / (Aliquot_Volume - Dead_Volume))

    return(num_aliquots)

def Get_Transfers_Required(Liquid, Destination_Layouts):
    transfer_volumes = []
    destination_wells = []
    destination_layouts = []

    for destination_layout in Destination_Layouts:
        wells_with_liquid = destination_layout.get_wells_containing_liquid(Liquid)

        for well in wells_with_liquid:
            transfer_volumes.append(destination_layout.get_volume_of_liquid_in_well(Liquid, well))
            destination_wells.append(well)
            destination_layouts.append(destination_layout)

    return(transfer_volumes, destination_wells, destination_layouts)

def DoE_Get_Value_From_Combined_Factor(Factor_Name, Combined_Factor):
    Value = Combined_Factor.split(Factor_Name)[1].split("(")[1].split(")")[0]

    # Try and return as a float - if a ValueError is raised, assume the value is a string and just return as is
    try:
        Value = float(Value)
    except ValueError:
        pass

    return Value

def DoE_Create_Source_Material(
    DoE_Experiment, Source_Material_Name, Factor_Names, Add_To_Runs=True
):
    # Create an empty list to store each of source material types
    # Each source material type is formed from combinations of the same factors...
    # ... with different values as specified by the DoE
    Source_Material_Types = []

    Source_Material_Component_Info = {}  # ID: list(Factor Values)

    if Factor_Names:
        # For each run in the DoE
        for run in DoE_Experiment.runs:
            # Get the values of all the specified factors
            source_material_type = []
            component_factor_values = []
            for component_factor in Factor_Names:
                component_factor_value = run.get_factor_value(component_factor)
                component_factor_values.append(component_factor_value)
                # Store the factor name-value combination as a string in a list
                source_material_type.append(
                    "{}({})".format(component_factor, component_factor_value)
                )
            # Convert the list of factor name-value combinations to a string and add to the previously created list
            Source_Material_Types.append("-".join(source_material_type))
            Source_Material_Component_Info["-".join(source_material_type)] = component_factor_values
            if Add_To_Runs:
                run.specify_source_material(Source_Material_Name, "-".join(source_material_type))
        for material_id in set(Source_Material_Types):
            Material_Object = DoE_Material(
                material_id,
                Source_Material_Name,
                Factor_Names,
                Source_Material_Component_Info[material_id],
            )
            DoE_Experiment.add_material(Material_Object)
    else:
        Source_Material_Types = [Source_Material_Name]
        Source_Material_Component_Info = {Source_Material_Name: None}
        if Add_To_Runs:
            for run in DoE_Experiment.runs:
                run.specify_source_material(Source_Material_Name, Source_Material_Name)

        Material_Object = DoE_Material(Source_Material_Name, Source_Material_Name)
        DoE_Experiment.add_material(Material_Object)

    return Source_Material_Types


def DoE_Create_Intermediate(
    DoE_Experiment,
    Intermediate_Name,
    Source_Material_Names,
    Source_Materials_Amount_Types,
    Source_Materials_Amount_Values,
    Add_To_Runs=True,
):
    # Create an empty list to store each of intermediate types
    # Each intermediate type is formed from combinations of the same source materials...
    # ... with different values as specified by the DoE
    Intermediate_Types = []

    Intermediate_Component_Info = {}

    # For each run in the DoE
    for run in DoE_Experiment.runs:
        # Get the values of all the specified source_materials
        intermediate_type = []
        component_source_material_values = []
        for component_source_material, amount_type, amount_value in zip(
            Source_Material_Names, Source_Materials_Amount_Types, Source_Materials_Amount_Values
        ):
            component_source_material_value = run.get_source_material_value(
                component_source_material
            )

            # Check to see if any factors are specified as references for amounts of components to be added
            # Different amounts of a source material being added results in extra combinations
            # e.g. an intermediate type might be composed of a buffer and a chemical
            # But the amount of chemical is determined by Factor-1, which has two values in the DoE
            # Therefore, there will need to be two unique versions of the intermediate type to account for
            # these differences

            if amount_value in DoE_Experiment.factors:
                amount_value = run.get_factor_value(amount_value)
                component_source_material = "{}[{}]".format(component_source_material, amount_value)

            component_source_material_values.append([component_source_material_value, amount_value])
            # Store the source_material name-value combination as a string in a list
            intermediate_type.append(
                "{}({})".format(component_source_material, component_source_material_value)
            )

        # Convert the list of source_material name-value combinations to a string and add to the previously created list
        Intermediate_Types.append("-".join(intermediate_type))
        Intermediate_Component_Info["-".join(intermediate_type)] = component_source_material_values
        if Add_To_Runs:
            run.specify_intermediate(Intermediate_Name, "-".join(intermediate_type))

    for intermediate_id in set(Intermediate_Types):
        component_ids = [id[0] for id in Intermediate_Component_Info[intermediate_id]]
        component_amount_values = [id[1] for id in Intermediate_Component_Info[intermediate_id]]
        Intermediate_Object = DoE_Intermediate(
            intermediate_id,
            Intermediate_Name,
            Source_Material_Names,
            component_ids,
            Source_Materials_Amount_Types,
            component_amount_values,
        )
        DoE_Experiment.add_intermediate(Intermediate_Object)

    return Intermediate_Types


def Reagent_Finder(Reagents: List[str], Directories: List[str]):
    """Searches a list of directories containing labware layout files for a specified reagent.

    This function will search in the directories listed for files which appear to be BMS labware layout files.
    Any labware layout files found will then be searched for the specified reagents.
    The name of all reagents are then printed to OUT, along with the name of the labware layout they appear in and the well(s) they occupy.
    """

    # Get all labware layouts in the specified directories
    Files = []
    for directory in Directories:
        Files.append(
            [
                file
                for file in os.listdir(directory + "/")
                if os.path.isfile(os.path.join(directory + "/", file)) and "~$" not in file
            ]
        )

    Layouts = []
    for files, directory in zip(Files, Directories):
        for file in files:
            try:
                Layouts.append(Import_Labware_Layout(Filename=file, path=directory + "/"))
            except:
                continue

    # Check if each reagent is in a labware file
    for reagent in Reagents:
        print("\n{}:".format(reagent))
        for layout in Layouts:
            if len(layout.get_wells_containing_liquid(reagent)) > 0:
                print("> {}: {}".format(layout.name, layout.get_wells_containing_liquid(reagent)))


def Import_Labware_Layout(Filename: str, path: str = "~", ext: str = ".xlsx"):
    """Imports an Excel file with a standard layout and converts it to a BiomationScripter.Labware_Layout object."""


    labware_layout = Labware_Layout("name", "type")
    labware_layout.import_labware(Filename, path=path, ext=ext)
    return labware_layout


def Create_Labware_Needed(
    Labware_Format: Labware_Layout, N_Wells_Needed: int, N_Wells_Available = "All", Return_Original_Layout: bool = True
):
    """calculates how many labware of a certain type are required for a protocol and returns a list of Labware_Layout objects.

    Determines number of labware by the total number of wells required (N_Wells_Needed) and the number of wells available per labware (N_Wells_Available).
    The labware created is based on the Labware_Layout provided to Labware_Format.
    Any content already in the template Labware_Layout is not copied to new labware created.
    """

    if not type(N_Wells_Available) is int:
        if N_Wells_Available == "All":
            N_Wells_Available = Labware_Format.rows * Labware_Format.columns
        else:
            raise ValueError("`N_Wells_Available` should either be an integer, or 'All'.")

    N_Plates_Needed = _math.ceil(N_Wells_Needed / N_Wells_Available)
    if Return_Original_Layout is True:
        Plates = [Labware_Format]
    elif Return_Original_Layout is False:
        Plates = []
    for plate_n in range(1, N_Plates_Needed):
        Plate_Name = Labware_Format.name + str(plate_n)
        Plates.append(Labware_Format.clone_format(Plate_Name))
    return Plates


def well_range(Wells: str, Labware_Format: Union[Labware_Layout, Tuple[int, int]] = None, Direction = "Horizontal", Box: bool = False):
    """Returns a list of wells based on a specified well range and direction.

    Wells are always in the format of row followed by column, where row is a letter and column is an integer (e.g. A1, D6, C12, B7, etc.).
    The Direction argument determines the order in which wells are counted.
    The Box argument determines whether the well range has a box-like shape.
    If Box = False, then a Labware_Format must be specified
    """

    if not Direction == "Horizontal" and not Direction == "Vertical":
        raise ValueError("`Direction` must be either 'Horizontal' or 'Vertical'")

    if not Labware_Format and not Box:
        raise LabwareError("`Box` can only be `False` when `Labware_Format` is specified")

    if not Labware_Format or Box:
        Well = Wells
        first, last = Well.split(":")
        firstL = first[0]
        lastL = last[0]
        firstN = int(first[1 : len(first)])
        lastN = int(last[1 : len(last)])
        wells = []
        if Direction == "Horizontal":
            for L in _Lrange(firstL, lastL):
                for N in range(firstN, lastN + 1):
                    wells.append(L + str(N))
            return wells
        elif Direction == "Vertical":
            for N in range(firstN, lastN + 1):
                for L in _Lrange(firstL, lastL):
                    wells.append(L + str(N))
            return wells

    else:
        # Get the end row and end column number for the labware being used
        if type(Labware_Format) is list:
            if not len(Labware_Format) == 2:
                raise ValueError(
                    "Labware_Format argument MUST either be a BiomationScripter.Labware_Layout "
                    "object, or a list specifying number of rows and number of columns (e.g. "
                    "[8, 12])."
                )
            end_row, end_col = Labware_Format
        else:
            Labware_Format = [Labware_Format.rows, Labware_Format.columns]

        end_row, end_col = Labware_Format
        # Get the first and last wells in the specified well range
        first_well, last_well = Wells.split(":")

        # Split the first and last wells up into rows and columns
        first_row = first_well[0]
        last_row = last_well[0]
        first_col = int(first_well[1:])
        last_col = int(last_well[1:])

        # Check if first and last wells are in range
        if (
            (_Labware_Row_To_Index(first_row) > end_row - 1)
            or (_Labware_Row_To_Index(last_row) > end_row - 1)
            or (first_col > end_col)
            or (last_col > end_col)
        ):
            raise ValueError("Wells are not in range of specified format")

        wells = []

        if Direction == "Horizontal":
            rows = []
            for r in _Lrange(first_row, last_row):
                rows.append(r)

            first_col_of_row = first_col

            for row in rows:
                for col in range(first_col_of_row, end_col + 1):
                    well = "{}{}".format(row, col)
                    wells.append(well)
                    if col == end_col:
                        first_col_of_row = 1
                    if well == last_well:
                        return wells

        elif Direction == "Vertical":
            rows = []
            for r in _Lrange("A", chr(64 + end_row)):
                rows.append(r)

            first_row_of_col_index = _Labware_Row_To_Index(first_row)

            for col in range(first_col, last_col + 1):
                for row in rows[first_row_of_col_index:]:
                    well = "{}{}".format(row, col)
                    wells.append(well)
                    if row == rows[-1]:
                        first_row_of_col_index = 0
                    if well == last_well:
                        return wells


def Group_Locations(Locations, Group_Populations):
    Grouped_Locations = []
    start_index = 0
    end_index = 0
    for group_pop in Group_Populations:
        end_index += group_pop
        Grouped_Locations.append(Locations[start_index:end_index])
        start_index += group_pop
    return Grouped_Locations


def Mastermix_Maker(
    Destination_Layouts: List[Labware_Layout],
    Mastermix_Layout: Labware_Layout,
    Maximum_Mastermix_Volume: float,
    Min_Transfer_Volume: float,
    Extra_Reactions: float,
    Excluded_Reagents: List[str] = [],
    Excluded_Combinations: List[List[str]] = [],
    Preferential_Reagents: List[str] = [],
    Seed: Union[int, None] = None,
):

    """Generates mastermixes based on source materials in a list of destination Labware_Layout objects, and other user-defined parameters.

    Mastermixes are generated by finding common source reagents across destination wells and grouping them together in the minimal amount of mastermixes.
    Parameters supplied as arguments can be used to influence compositions of the mastermixes.
    To help ensure many combinations are attempted, there is some randomness within the function.
    This randomness can be removed by supplying a specific seed, which ensures that the same mastermixes are generated each time.
    """

    Solved = False  # Check whether a solution has been found

    First_Attempt = True  # Determine whether this is the first attempt to find a solution

    # Whilst there is no solution
    print("\nDetermining mastermixes, this may take a while...\n")
    while not Solved:

        try:

            # Get all unique reagents in the destination layout
            All_Reagents = set()

            for Destination_Layout in Destination_Layouts:
                for well in Destination_Layout.get_content():
                    for reagent in Destination_Layout.get_liquids_in_well(well):
                        All_Reagents.add(reagent)

            # For each reagent at each volume/well, get the wells it appears in
            # e.g., 20 uL water might be in wells A1, A2, A3 and 30 uL water might be in wells A4, A5, A6

            Wells_By_Reagent_ID = {}

            for reagent in All_Reagents:
                # get wells containing the current reagent (grouped by destination layout)
                wells_with_reagent_by_destination = [
                    Destination_Layout.get_wells_containing_liquid(reagent)
                    for Destination_Layout in Destination_Layouts
                ]

                # combine grouped wells into one list, and add the destination layout index to the
                # well designation (INDEX_WELL)
                wells_with_reagent = []
                for wells, dest_index in zip(
                    wells_with_reagent_by_destination,
                    range(0, len(wells_with_reagent_by_destination)),
                ):
                    wells_with_reagent += ["{}_{}".format(dest_index, well) for well in wells]

                # Group the identified wells based on the reagent's volume/well
                for well in wells_with_reagent:
                    # Get the volume in the well
                    well_volume = Destination_Layouts[
                        _get_well_layout_index(well)
                    ].get_volume_of_liquid_in_well(reagent, well.split("_")[1])
                    # Create a new reagent ID which includes the volume/well
                    reagent_id = "{}_vol_{}".format(reagent, well_volume)
                    # Add the well to the relevant reagent id (create the entry if needed)
                    if reagent_id in Wells_By_Reagent_ID.keys():
                        Wells_By_Reagent_ID[reagent_id].add(well)
                    else:
                        Wells_By_Reagent_ID[reagent_id] = set([well])

            # a set of all volume/well values
            vols_per_well = set()
            # Get the reagent id keys in alphabetical order - needed to ensure consistency when doing random shuffles
            reagent_id_keys = list(Wells_By_Reagent_ID.keys())
            reagent_id_keys.sort()

            for reagent_id in reagent_id_keys:
                vols_per_well.add(_get_vol_per_well(reagent_id))

            vols_per_well = list(vols_per_well)
            vols_per_well.sort()

            # Get a list of reagent IDs ordered by volume/well (ascending)
            Ordered_Reagent_IDs = []
            for volume in vols_per_well:
                for reagent_id in reagent_id_keys:
                    if _get_vol_per_well(reagent_id) == volume:
                        Ordered_Reagent_IDs.append(reagent_id)

            # Removed excluded reagents (i.e. those not to be used in mastermixes)

            for (
                reagent
            ) in Ordered_Reagent_IDs.copy():  # copy to make sure the iterating works as expected
                for excluded_reagent in Excluded_Reagents:
                    if excluded_reagent in reagent:
                        Ordered_Reagent_IDs.remove(reagent)

            #####################################

            # Check for linked reagents (where reagent ids share the same well set)

            reagents_checked = []  # Used to ensure combinations, NOT permutations
            Linked_Reagents = []

            for reagent_id in Ordered_Reagent_IDs:
                linked_reagents = [reagent_id]  # temp list for inside loop
                reagent_well_set = Wells_By_Reagent_ID[
                    reagent_id
                ]  # well set for the current reagent
                for candidate_reagent in Ordered_Reagent_IDs:
                    if candidate_reagent == reagent_id:
                        # Don't link a reagent with itself
                        continue
                    elif candidate_reagent in reagents_checked:
                        # Ignore already checked reagents - avoids permutations
                        continue
                    elif reagent_well_set == Wells_By_Reagent_ID[candidate_reagent]:
                        # If the reagent well sets are identical, then link the reagents
                        linked_reagents.append(candidate_reagent)
                        # Make sure that the linked reagents aren't excluded combinations
                        for excluded_combo in Excluded_Combinations:
                            if (
                                candidate_reagent.split("_vol_")[0] in excluded_combo
                                and reagent_id.split("_vol_")[0] in excluded_combo
                            ):
                                linked_reagents.remove(
                                    candidate_reagent
                                )  # remove it if it is an excluded combo

                # Reagent volumes will be scaled up to ensure that the mastermix can service the correct number of wells,
                ## and to also ensure that the lowest volume reagent can be added with a transfer volume above the min transfer vol
                # Check that this scale up will not put the total mastermix volume above the total well capacity if these linked reagents were used
                lowest_vol_reag = [
                    reag
                    for reag in linked_reagents
                    if _get_vol_per_well(reag)
                    == min([_get_vol_per_well(reag) for reag in linked_reagents])
                ][0]
                if (
                    _get_vol_per_well(lowest_vol_reag)
                    * (len(Wells_By_Reagent_ID[lowest_vol_reag]) + Extra_Reactions)
                    >= Min_Transfer_Volume
                ):
                    potential_mm_reaction_num = (
                        len(Wells_By_Reagent_ID[lowest_vol_reag]) + Extra_Reactions
                    )
                else:
                    potential_mm_reaction_num = Min_Transfer_Volume / _get_vol_per_well(
                        lowest_vol_reag
                    )
                # If the sum of all mm reagents multiplied by the number of required reagents would be more than the max mastermix vol allowed
                ## then remove the highest vol reagent until the vol is below the max volume allowed
                total_potential_mastermix_volume = sum(
                    [
                        _get_vol_per_well(reag) * potential_mm_reaction_num
                        for reag in linked_reagents
                    ]
                )
                while total_potential_mastermix_volume > Maximum_Mastermix_Volume:
                    linked_reagents.remove(
                        [
                            reag
                            for reag in linked_reagents
                            if _get_vol_per_well(reag)
                            == max([_get_vol_per_well(reag) for reag in linked_reagents])
                        ][0]
                    )
                    total_potential_mastermix_volume = sum(
                        [
                            _get_vol_per_well(reag) * potential_mm_reaction_num
                            for reag in linked_reagents
                        ]
                    )

                # Check if the current reagent was linked with any other reagent(s)
                if len(linked_reagents) == 1:
                    pass
                else:
                    Linked_Reagents.append(linked_reagents)

                # Mark that the reagent has been checked
                reagents_checked.append(reagent_id)

            # print(Linked_Reagents)

            ######################################

            # Create the mastermixes

            No_Solution = False

            if Seed:
                random.seed(Seed)
                random.shuffle(Ordered_Reagent_IDs)

            Mastermixes = []
            for reagent_id in Ordered_Reagent_IDs:

                # Check if the reagent's volume/well is below the trasfer threshold
                if _get_vol_per_well(reagent_id) < Min_Transfer_Volume:
                    # print("\n")
                    mastermix_reagents = [reagent_id]  # list to hold the mastermix components
                    mastermix_per_well = _get_vol_per_well(
                        reagent_id
                    )  # to track the volume of MM to add per well
                    current_reagent_well_set = Wells_By_Reagent_ID[
                        reagent_id
                    ].copy()  # set of wells which need to be statisifed by the MMs

                    # Check if the reagent's well set is empty
                    ## This can occur if the reagent has been satisified by other mastermixes
                    if len(current_reagent_well_set) == 0:
                        continue

                    # print("start", mastermix_reagents)

                    ##########################################
                    # Check if there are any linked reagents #
                    ##########################################
                    for linked_reagents in Linked_Reagents:
                        if reagent_id in linked_reagents:
                            # For any linked reagents found...
                            for linked_reagent in linked_reagents:
                                # Skip the current reagent in the list so it isn't added to itself
                                if linked_reagent == reagent_id:
                                    continue
                                # Check that the linked reagent hasn't already been used up in other mastermixes
                                elif len(Wells_By_Reagent_ID[linked_reagent]) == 0:
                                    continue
                                else:
                                    mastermix_reagents.append(linked_reagent)
                                    mastermix_per_well += _get_vol_per_well(linked_reagent)
                    # Check if the MM per well is above the threshold
                    if mastermix_per_well >= Min_Transfer_Volume:
                        # print("Reagent:", reagent_id)
                        # print("linked mm reag", mastermix_reagents)
                        # If it is, then create the mastermix
                        mastermix_name = ":".join(mastermix_reagents)
                        # Check if any linked reagents have already been used
                        if False in [
                            current_reagent_well_set == Wells_By_Reagent_ID[mm_reag]
                            for mm_reag in mastermix_reagents
                        ]:
                            # If the well sets are not equal, then just skip to the next code block (essentially means that the simple solution failed...)
                            # Reset the variables first...
                            mastermix_reagents = [
                                reagent_id
                            ]  # list to hold the mastermix components
                            mastermix_per_well = _get_vol_per_well(
                                reagent_id
                            )  # to track the volume of MM to add per well
                            current_reagent_well_set = Wells_By_Reagent_ID[
                                reagent_id
                            ].copy()  # set of wells which need to be statisifed by the MMs
                            pass
                        else:
                            mastermix_well_set = current_reagent_well_set.copy()
                            Mastermixes.append(
                                Mastermix(
                                    mastermix_name,
                                    mastermix_reagents.copy(),
                                    mastermix_well_set.copy(),
                                )
                            )
                            # Remove the used wells from the reagent IDs
                            for used_reagent in mastermix_reagents:
                                # print("Current {} well set: {}".format(used_reagent, Wells_By_Reagent_ID[used_reagent]))
                                Wells_By_Reagent_ID[used_reagent] -= mastermix_well_set
                                # print("Updated {} well set: {}".format(used_reagent, Wells_By_Reagent_ID[used_reagent]))
                            # print("---")

                            # Then continue to the next reagent in need of a mastermix
                            continue
                    else:
                        # If not, pass to the next code block to add some more components
                        pass

                    ###############################################################
                    # Add components until the MM per well is above the threshold #
                    ###############################################################
                    split = (
                        []
                    )  # This is used to keep track of things if multiple MMs are needed for a reagent
                    ## split is a list of sets: split = [ [wells: set, mm_reagents: set] ]
                    split_active = (
                        False  # True when there are still wells that need to be dealt with
                    )
                    ## split variables hold wells that are not currently active
                    ## mastermix_ variables hold currently active wells (actively trying to satisify)

                    # Keep looping until the MM per well is above the threshold and all wells have been satisified
                    while (
                        mastermix_per_well < Min_Transfer_Volume
                        or len(current_reagent_well_set) > 0
                        or split_active
                    ):
                        # Start by identifying the reagent with the most wells in common
                        ## (if there is a tie, the reagent with lowest vol/well is selected)
                        common_wells = set()
                        chosen_component = ""
                        chosen_components = []
                        preferential_selected = False
                        for candidate_reagent in Ordered_Reagent_IDs:
                            # Make sure that the linked reagents aren't excluded combinations
                            exclude = False
                            for excluded_combo in Excluded_Combinations:
                                if (
                                    candidate_reagent.split("_vol_")[0] in excluded_combo
                                    and reagent_id.split("_vol_")[0] in excluded_combo
                                ):
                                    exclude = True
                                    break
                            if exclude:
                                continue

                            # Make sure that adding the reagent wouldn't put the mastermix volume over the max allowed
                            # Reagent volumes will be scaled up to ensure that the mastermix can service the correct number of wells,
                            ## and to also ensure that the lowest volume reagent can be added with a transfer volume above the min transfer vol
                            # Check that this scale up will not put the total mastermix volume above the total well capacity if these linked reagents were used
                            # Only bother checking if the candidate reagent shares wells with the current reagent
                            if (
                                len(
                                    current_reagent_well_set.intersection(
                                        Wells_By_Reagent_ID[candidate_reagent]
                                    )
                                )
                                > 0
                            ):
                                lowest_vol_reag = [
                                    reag
                                    for reag in mastermix_reagents + [candidate_reagent]
                                    if _get_vol_per_well(reag)
                                    == min(
                                        [
                                            _get_vol_per_well(reag)
                                            for reag in mastermix_reagents + [candidate_reagent]
                                        ]
                                    )
                                ][0]
                                if (
                                    _get_vol_per_well(lowest_vol_reag)
                                    * (len(Wells_By_Reagent_ID[lowest_vol_reag]) + Extra_Reactions)
                                    >= Min_Transfer_Volume
                                ):
                                    potential_mm_reaction_num = (
                                        len(Wells_By_Reagent_ID[lowest_vol_reag]) + Extra_Reactions
                                    )
                                    # If the sum of all mm reagents multiplied by the number of required reagents would be more than the max mastermix vol allowed, then continue
                                    total_potential_mastermix_volume = sum(
                                        [
                                            _get_vol_per_well(reag) * potential_mm_reaction_num
                                            for reag in mastermix_reagents + [candidate_reagent]
                                        ]
                                    )
                                    if total_potential_mastermix_volume > Maximum_Mastermix_Volume:
                                        # print(total_potential_mastermix_volume, Maximum_Mastermix_Volume, reagent_id, candidate_reagent)
                                        continue
                                else:
                                    potential_mm_reaction_num = (
                                        Min_Transfer_Volume / _get_vol_per_well(lowest_vol_reag)
                                    )
                                    # before continuing, if the number of reactions required by the lowest vol reagent will always make the candidate reagent above the max
                                    ## vol allowed, then mark the reagents as excluded combos to ensure that they don't keep getting checked
                                    if (
                                        _get_vol_per_well(candidate_reagent)
                                        * potential_mm_reaction_num
                                        > Maximum_Mastermix_Volume
                                    ):
                                        Excluded_Combinations.append(
                                            [candidate_reagent, lowest_vol_reag]
                                        )
                                        continue
                                    # If the sum of all mm reagents multiplied by the number of required reagents would be more than the max mastermix vol allowed, then continue
                                    total_potential_mastermix_volume = sum(
                                        [
                                            _get_vol_per_well(reag) * potential_mm_reaction_num
                                            for reag in mastermix_reagents + [candidate_reagent]
                                        ]
                                    )
                                    if total_potential_mastermix_volume > Maximum_Mastermix_Volume:
                                        continue

                            if candidate_reagent == reagent_id:
                                # don't check reagents with theirselves
                                continue
                            elif candidate_reagent in mastermix_reagents:
                                # Don't add duplicate reagents
                                continue

                            elif candidate_reagent.split("_vol_")[0] in Preferential_Reagents:
                                preferential_selected = True
                                # If the candidate is a preferential reagent, choose it over non-preferential reagents
                                if len(
                                    current_reagent_well_set.intersection(
                                        Wells_By_Reagent_ID[candidate_reagent]
                                    )
                                ) > len(common_wells):
                                    # If so, store this as the current best option (may get overwritten later)
                                    common_wells = current_reagent_well_set.intersection(
                                        Wells_By_Reagent_ID[candidate_reagent]
                                    )
                                    chosen_component = candidate_reagent
                            # Check if the number of wells in common is higher than the currently recorded number
                            elif (
                                len(
                                    current_reagent_well_set.intersection(
                                        Wells_By_Reagent_ID[candidate_reagent]
                                    )
                                )
                                > len(common_wells)
                                and not preferential_selected
                            ):
                                # If so, store this as the current best option (may get overwritten later)
                                common_wells = current_reagent_well_set.intersection(
                                    Wells_By_Reagent_ID[candidate_reagent]
                                )
                                chosen_component = candidate_reagent
                        chosen_components = [
                            chosen_component
                        ]  # make a list to make downstreaming processing easier

                        # Check if there were any identified reagents
                        if not chosen_components == [""]:
                            # print("chosen comps", chosen_components)
                            # If there were, then check if it satisifies all wells or not
                            if not len(current_reagent_well_set) == len(common_wells):
                                ## If the chosen component only applies to a subset of wells, activate the split
                                split_active = True
                                # Store the non-common wells in the split, along with the current reagents
                                split_tracker_wells = current_reagent_well_set.symmetric_difference(
                                    common_wells
                                )
                                split_tracker_reagents = mastermix_reagents.copy()
                                split.append(
                                    [split_tracker_wells.copy(), split_tracker_reagents.copy()]
                                )
                                # Remove split wells from the active mastermix_wells
                                current_reagent_well_set -= split_tracker_wells
                            else:
                                # If applies to all wells, then just pass
                                pass

                        else:
                            # print("chosen comps", chosen_components)
                            # if no remaining reagent has any common wells, then start looking at breaking apart current MMs
                            common_wells = set()
                            chosen_mastermix = None
                            for mastermix in Mastermixes:
                                # print(current_reagent_well_set, mastermix.wells)
                                if len(
                                    current_reagent_well_set.intersection(mastermix.wells)
                                ) > len(common_wells):
                                    # check that none of the current reagents are in the identified mastermix
                                    if (
                                        len(
                                            current_reagent_well_set.intersection(
                                                mastermix.reagents
                                            )
                                        )
                                        > 0
                                    ):
                                        continue
                                    # Make sure that the linked reagents aren't excluded combinations
                                    exclude = False
                                    for excluded_combo in Excluded_Combinations:
                                        for reagent_in_candidate_mm in mastermix.reagents:
                                            if (
                                                reagent_in_candidate_mm.split("_vol_")[0]
                                                in excluded_combo
                                                and reagent_id.split("_vol_")[0] in excluded_combo
                                            ):
                                                exclude = True
                                                break
                                    if exclude:
                                        continue
                                    common_wells = current_reagent_well_set.intersection(
                                        mastermix.wells
                                    )
                                    chosen_mastermix = mastermix
                            # Check if a mastermix was found
                            if chosen_mastermix:
                                # print("chosen mm", chosen_mastermix.name)
                                # Remove the common wells from the chosen mastermix as they will be re-assigned to the new mastermix
                                chosen_mastermix.wells -= common_wells
                                # If the mastermix is now not servicing any wells, delete it
                                if len(chosen_mastermix.wells) == 0:
                                    Mastermixes.remove(chosen_mastermix)
                                # Store the components from the chosen mastermix
                                chosen_components = chosen_mastermix.reagents.copy()
                                # If there were, then check if it satisifies all wells or not
                                if not len(current_reagent_well_set) == len(common_wells):
                                    # If the chosen component only applies to a subset of wells, activate the split
                                    split_active = True
                                    # Store the non-common wells in the split, along with the current reagents
                                    split_tracker_wells = (
                                        current_reagent_well_set.symmetric_difference(common_wells)
                                    )
                                    split_tracker_reagents = mastermix_reagents.copy()
                                    split.append(
                                        [split_tracker_wells.copy(), split_tracker_reagents.copy()]
                                    )
                                    # Remove split wells from the active mastermix_wells
                                    current_reagent_well_set = common_wells.copy()
                                else:
                                    # If applies to all wells, then just pass
                                    pass

                            else:
                                # If no mastermixes could be found to split, then raise an error
                                No_Solution = True
                                break

                        # update mastermix components
                        for chosen_component in chosen_components:
                            # print("Add comp", chosen_component)
                            mastermix_reagents.append(chosen_component)
                            mastermix_per_well += _get_vol_per_well(chosen_component)
                        # Check if the mm per well is above the threshold
                        if mastermix_per_well >= Min_Transfer_Volume:
                            # print("mm_per_well_sanity_check", mastermix_per_well, Min_Transfer_Volume)
                            # print("Reagent:", reagent_id)
                            # print("mm reag", mastermix_reagents)
                            # if yes, then mark the active well set as satisified and create a mastermix
                            mastermix_name = ":".join(mastermix_reagents)
                            mastermix_well_set = current_reagent_well_set.copy()  # active well set
                            Mastermixes.append(
                                Mastermix(
                                    mastermix_name, mastermix_reagents.copy(), mastermix_well_set
                                )
                            )
                            # Remove the used wells from the reagent IDs
                            for used_reagent in mastermix_reagents:
                                # print("Current {} well set: {}".format(used_reagent, Wells_By_Reagent_ID[used_reagent]))
                                Wells_By_Reagent_ID[used_reagent] -= mastermix_well_set
                                # print("Updated {} well set: {}".format(used_reagent, Wells_By_Reagent_ID[used_reagent]))
                            # print("---")
                            # Mark the current wells as satisified
                            current_reagent_well_set.clear()

                            if split_active:
                                ## Apply the most recent split as active
                                current_reagent_well_set = split[-1][0]
                                mastermix_reagents = split[-1][1]
                                mastermix_per_well = sum(
                                    [_get_vol_per_well(r) for r in mastermix_reagents]
                                )
                                split.remove(split[-1])
                                if len(split) == 0:
                                    split_active = False
                                else:
                                    pass
                        else:
                            # if mm/well is not above the threshold, then keep looping
                            continue

                    if No_Solution:
                        break

                else:
                    # If the reagent vol/well is already above the threshold, then just skip
                    continue

            if No_Solution:
                raise MastermixError("No solution could be found with these constraints.")
            else:
                Solved = True  # break out of the while loop with a solution

        # If a solution is not possible
        except MastermixError:
            # If this was the first attempt
            if First_Attempt:
                # Check if a seed was given
                if Seed:
                    raise MastermixError(
                        "No solution could be found with these constraints and a seed of {}".format(
                            Seed
                        )
                    )
                # If a seed wasn't given, then try shuffling the order of the reagents with different seeds
                else:
                    Seed = 0
                    First_Attempt = False
            else:
                # Iterate the seed number
                Seed += 1
                # To stop infinte loops
                if not First_Attempt:
                    if Seed > 1000:
                        raise MastermixError(
                            """
No solution could be found with these constraints. Try one of the following options:
> Decrease the minimum transfer volume (if specified)
> Decrease the stock concentration of highly concentrated source material
> Use a mastermix labware with a higher well capacity (especially when there are a lot of samples)
"""
                        )

    # Remove any empty mastermixes
    ## These are MMs which were generated at some point, but then were split out into other mastermixes and no longer service any wells

    for mm in Mastermixes:
        if sum([_get_vol_per_well(reagent) for reagent in mm.reagents]) < Min_Transfer_Volume:
            raise ValueError(mm.name)
        if len(mm.wells) == 0:
            Mastermixes.remove(mm)

    # Set up the mastermix layout with the generated content
    Mastermix_Layouts = [Mastermix_Layout]
    Mastermix_Layout_Index = 0

    for mastermix in Mastermixes:

        # Check if a new mastermix layout is needed
        if Mastermix_Layouts[Mastermix_Layout_Index].get_next_empty_well() is None:

            new_mastermix_layout_name = "{}_{}".format(
                Mastermix_Layout.name, Mastermix_Layout_Index + 1
            )
            Mastermix_Layouts.append(Mastermix_Layout.clone_format(new_mastermix_layout_name))
            Mastermix_Layout_Index += 1

        well = Mastermix_Layouts[Mastermix_Layout_Index].get_next_empty_well()
        Mastermix_Layouts[Mastermix_Layout_Index].add_well_label(well, mastermix.name)

        # Make sure that the transfer volume TO the mastermix is above the threshold for all reagents
        ## If not, additional extra reactions will be added to that mastermix
        extra_reactions = Extra_Reactions
        for reagent in mastermix.reagents:
            volume = (len(mastermix.wells) + extra_reactions) * (_get_vol_per_well(reagent))
            # Make sure that the transfer volume TO the mastermix is above the threshold
            if volume < Min_Transfer_Volume:
                extra_vol_needed = Min_Transfer_Volume - volume
                extra_reactions_needed = extra_vol_needed / _get_vol_per_well(reagent)
                extra_reactions += extra_reactions_needed
        # Add reagents to the mastermix layout
        for reagent in mastermix.reagents:
            Mastermix_Layouts[Mastermix_Layout_Index].add_content(
                Well=well,
                Reagent=reagent.split("_vol_")[0],
                Volume=(len(mastermix.wells) + extra_reactions) * (_get_vol_per_well(reagent)),
            )

    # Modify the destination layout to now take mastermixes as reagents
    for Destination_Layout, Dest_Index in zip(
        Destination_Layouts, range(0, len(Destination_Layouts))
    ):

        for destination_well in Destination_Layout.content.copy():
            destination_location = "{}_{}".format(Dest_Index, destination_well)
            for mastermix in Mastermixes:
                # Find if any mastermixes satisfy the destination well
                if destination_location in mastermix.wells:
                    # Get the reagents that the mastermix covers
                    reagents = mastermix.reagents
                    # Calculate the volume of mastermix needed for this well
                    mastermix_volume = sum([_get_vol_per_well(reagent) for reagent in reagents])
                    # Sanity check
                    if not mastermix_volume == sum(
                        [
                            Destination_Layout.get_volume_of_liquid_in_well(
                                reagent.split("_vol_")[0], destination_well
                            )
                            for reagent in reagents
                        ]
                    ):
                        # print("destination well content:", [reagent.split("_vol_")[0] for reagent in reagents], Destination_Layout.get_liquids_in_well(destination_well))
                        raise LabwareError(
                            "Mastermix Maker encountered an error with well {} mastermix {}: vol1 = {}, vol2 = {}".format(
                                destination_well,
                                mastermix.name,
                                mastermix_volume,
                                sum(
                                    [
                                        Destination_Layout.get_volume_of_liquid_in_well(
                                            reagent.split("_vol_")[0], destination_well
                                        )
                                        for reagent in reagents
                                    ]
                                ),
                            )
                        )

                    # Remove the reagents in the mastermix from the destination well
                    for reagent in reagents:
                        # print("remove from destination {}: {}".format(Dest_Index, reagent))
                        Destination_Layout.clear_liquid_in_well(
                            destination_well, reagent.split("_vol_")[0]
                        )

                    # Add mastermix to the destination well
                    Destination_Layout.add_content(
                        Well=destination_well, Reagent=mastermix.name, Volume=mastermix_volume
                    )

    return (Mastermixes, Seed, Destination_Layouts, Mastermix_Layouts)


def fmol_calculator(mass_ng, length_bp):
    return ((mass_ng * 1e-9) / ((length_bp * 617.96) + 36.04)) * 1e15

def serial_dilution_volumes(dilution_factors, total_volume):
    # Note that total volume is the amount the dilution will be made up to
    ## The total volume of all dilutions other than the final will be lower than this
    sample_volumes = []
    solution_volumes = []

    # This the the dilution factor of the source material for the first serial dilution
    ## This is always 1, as the initial sample is assumed to be undiluted
    source_dilution_factor = 1

    for df in dilution_factors:
        # Get the dilution factor of the current serial dilution being performed
        destination_dilution_factor = df

        # Calculate the volume, in uL, of sample and solution required for each dilution factor
        sample_volume = total_volume * (source_dilution_factor/destination_dilution_factor)
        solution_volume = total_volume - sample_volume

        # Store the volumes required for later use
        sample_volumes.append(sample_volume)
        solution_volumes.append(solution_volume)

        # Set the current dilution as the source for the next serial dilution
        source_dilution_factor = df

    return(sample_volumes, solution_volumes)

## Private ##
def _get_well_layout_index(well):
    return int(well.split("_")[0])


def _Lrange(L1, L2):  # Between L1 and L2 INCLUSIVE of L1 and L2
    L1 = ord(L1.upper())
    L2 = ord(L2.upper())
    for L in range(L1, L2 + 1):
        yield (chr(L))


def _Labware_Row_To_Index(row):
    return ord(row.upper()) - ord("A")


def _get_vol_per_well(Reagent_ID):
    return float(Reagent_ID.split("_vol_")[1])


class MastermixError(Exception):
    pass
