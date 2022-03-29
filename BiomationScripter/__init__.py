from BiomationScripter import EchoProto
from BiomationScripter import OTProto
# from BiomationScripter import FeliXProto
# from BiomationScripter import PIXLProto
# from BiomationScripter import AttuneProto
# from BiomationScripter import ClarioProto

import math

# Exception classes #

class NegativeVolumeError(Exception):
    pass

class RobotConfigurationError(Exception):
    pass

class BMSTemplateError(Exception):
    pass

class LabwareError(Exception):
    pass

class OutOFSourceMaterial(Exception):
    pass

class DoEError(Exception):
    pass

class TransferError(Exception):
    pass

#####################
# Classes

class DoE_Material:
    def __init__(self, ID, Material_Type, Factors = None, Factor_Values = None):
        if (Factors and not Factor_Values) or (not Factors and Factor_Values):
            raise DoEError("Error creating source type {} {} - factor names or factor values were specified without the other.".format(Material_Type, ID))

        self.id = ID
        self.material_type = Material_Type
        self.factors = {}

        if Factors:
            for factor, value in zip(Factors, Factor_Values):
                self.factors[factor] = value

    def get_factor_value(self, Factor):
        return(self.factors[Factor])

class DoE_Intermediate:
    def __init__(self, ID, Intermediate_Type, Component_Types, Component_IDs, Component_Amount_Types, Component_Amount_Values):
        self.id = ID
        self.intermediate_type = Intermediate_Type
        self.components = {}

        for component_type, id, amount_type, amount_value in zip(Component_Types, Component_IDs, Component_Amount_Types, Component_Amount_Values):
            self.components[component_type] = [id, amount_type, amount_value]

    def get_component_id(self, Component):
        return(self.components[Component][0])

    def get_component_amount_info(self, Component):
        return(self.components[Component][1:])

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
                raise ValueError("Missing value found in run {} for factor {}; check that all values are present and objectives are not present in the file.".format(ID, self.factors[run.index("")]))
            self.runs.append(DoE_Run_Data(ID, self.factors, run))
            ID += 1

    def add_material(self, Material):
        self.materials[Material.id] = Material

    def get_material(self, Material_Name):
        return(self.materials[Material_Name])

    def add_intermediate(self, Intermediate):
        self.intermediates[Intermediate.id] = Intermediate

    def get_intermediate(self, Intermediate_Name):
        return(self.intermediates[Intermediate_Name])

    def get_run(self, ID):
        for run in self.runs:
            if run.id == ID:
                return(run)

    def batch_by_factor_value(self, Factor, Value):
        batched_experiment = DoE_Experiment("{}-Batched-{}-{}".format(self.name, Factor, Value), self.doe_file)
        runs = batched_experiment.runs.copy()
        for run in runs:
            if not run.get_factor_value(Factor) == Value:
                batched_experiment.runs.remove(run)
        return(batched_experiment)

    def get_all_values(self, Name):
        Values = []
        for run in self.runs:
            Values.append(run.get_value_by_name(Name))

        return(Values)

class DoE_Run_Data:
    def __init__(self, ID, Factors, Values):
        self.id = ID
        self.source_materials = {}
        self.intermediates = {}
        self.run_data = {}
        for factor, value in zip(Factors, Values):
            self.run_data[factor] = value

    def get_factor_value(self, Factor):
        return(self.run_data[Factor])

    def add_factor(self, Factor, Value):
        self.run_data[Factor] = Value

    def specify_source_material(self, Material, Value):
        self.source_materials[Material] = Value

    def get_source_material_value(self, Source_Material):
        return(self.source_materials[Source_Material])

    def specify_intermediate(self, Intermediate, Value):
        self.intermediates[Intermediate] = Value

    def get_intermediate_value(self, Intermediate):
        return(self.intermediates[Intermediate])

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
            return(Value)



class Labware_Layout:
    def __init__(self, Name, Type):
        self.name = Name
        self.type = Type
        self.rows = None
        self.columns = None
        self.content = {}
        self.available_wells = None
        self.empty_wells = None
        self.well_labels = {}

    def define_format(self, Rows, Columns):
        self.rows = Rows
        self.columns = Columns

    def get_format(self):
        return(self.rows, self.columns)

    def set_available_wells(self, Well_Range = None, Use_Outer_Wells = True, Direction = "Horizontal", Box = False):
        self.available_wells = self.get_well_range(Well_Range, Use_Outer_Wells, Direction, Box)
        self.empty_wells = self.available_wells.copy()

    def get_available_wells(self):
        return(self.available_wells)

    def get_well_range(self, Well_Range=None, Use_Outer_Wells = True, Direction = "Horizontal", Box = False):
        if not Direction == "Horizontal" and not Direction == "Vertical":
            raise ValueError("`Direction` must be either 'Horizontal' or 'Vertical'")

        n_rows = self.rows
        n_cols = self.columns
        if Well_Range == None:
            Well_Range = "A1:{}{}".format(chr(64+n_rows),n_cols)

        wells = well_range(Well_Range, Labware_Format = self, Direction = Direction, Box = Box)

        if not Use_Outer_Wells:
            plate_first_row = "A"
            plate_last_row = chr(64+n_rows)
            plate_first_col = 1
            plate_last_col = n_cols

            temp_wells = []
            for w in wells:
                if (plate_first_row in w) or (plate_last_row in w) or (str(plate_first_col) == w[1:]) or (str(plate_last_col) == w[1:]):
                    continue
                else:
                    temp_wells.append(w)
            wells = temp_wells

        return(wells)

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
        return(InRange)

    def clone_format(self, New_Name):
        # Does not copy content
        name = New_Name
        type = self.type
        rows = self.rows
        columns = self.columns
        plate_copy = PlateLayout(name, type)
        plate_copy.define_format(rows, columns)
        return(plate_copy)

    def add_content(self, Well, Reagent, Volume, Liquid_Class = None):
        # TODO: * Check if Well exists in the plate
        #       * Allow well ranges to span multiple columns
        #       * Don't overwrite current content if a well range is specified
        if Volume < 0:
            raise NegativeVolumeError

        if self.available_wells and not ":" in Well:
            if not Well in self.available_wells:
                raise LabwareError("Available wells are specified, but well {} is not defined as available.\nCheck that the correct well has been specified. Available wells are:\n".format(Well, self.available_wells))

        # Volume should always be uL
        if Liquid_Class == None:
            Liquid_Class = "Unknown"
        if ":" in Well:
            for w in well_range(Well):
                self.add_content(w, Reagent, Volume, Liquid_Class)
        elif type(Well) == list:
            for well in Well:
                self.add_content(well, Reagent, Volume, Liquid_Class)
        elif Well in self.content:
            self.content[Well].append([Reagent,float(Volume), Liquid_Class])
        else:
            self.content[Well] = [ [Reagent,float(Volume), Liquid_Class] ]

        if self.empty_wells and Well in self.empty_wells:
            self.empty_wells.remove(Well)

    def add_well_label(self, Well: str, Label: str):
        for well in self.well_labels:
            if self.well_labels[well] == Label:
                raise ValueError('Label "{}" is already used as a label in {}'.format(Label, well))
        self.well_labels[Well] = Label

    def get_well_content_by_label(self, Label: str):
        for well in self.well_labels:
            if self.well_labels[well] == Label:
                return(self.content[well])

    def get_well_location_by_label(self, Label: str):
        for well in self.well_labels:
            if self.well_labels[well] == Label:
                return(well)

    def get_content(self):
        return(self.content)

    def get_occupied_wells(self):
        return(list(self.get_content().keys()))

    def get_liquids_in_well(self, Well):
        if not Well in self.get_occupied_wells():
            raise LabwareError("Well {} in labware {} contains no liquids.".format(Well, self.name))

        liquids_in_well = []
        content_in_well = self.content[Well]
        for content in content_in_well:
            liquids_in_well.append(content[0])

        return(liquids_in_well)

    def get_wells_containing_liquid(self, Liquid_Name):
        wells_to_return = []
        content = self.get_content()
        wells = self.get_occupied_wells()
        for well in wells:
            for liquid in content[well]:
                if liquid[0] == Liquid_Name:
                    wells_to_return.append(well)
        return(wells_to_return)

    def clear_content(self):
        self.content = {}
        if self.available_wells:
            self.empty_wells = self.available_wells.copy()

    def clear_content_from_well(self, Well):
        del self.content[Well]

        if self.empty_wells:
            self.empty_wells.append(Well)

    def get_next_empty_well(self):
        if not self.available_wells:
            raise LabwareError("Available wells must be specified to get the next empty well. Specify the avilable wells for {} using `.set_available_wells`.".format(self.name))
        if len(self.empty_wells) == 0:
            return(None)
        # Iterate through all available wells, and return the first one which also exists in the empty wells attribute
        for well in self.available_wells:
            if well in self.empty_wells:
                return(well)


    def get_volume_of_liquid_in_well(self, Liquid, Well):
        # if not Well in self.get_occupied_wells():
        #     raise LabwareError("Well {} in labware {} contains no liquids.".format(Well, self.name))
        well_content = self.get_content()[Well]
        for content in well_content:
            if content[0] == Liquid:
                return(content[1])

        return(0.0)

    def update_volume_in_well(self, Volume, Reagent, Well):
        if not Well in self.get_content().keys():
            raise LabwareError("{} has not been previously defined. Add content to this well using the `add_content` method.".format(Well))
        well_content = self.get_content()[Well]
        for content in well_content:
            if content[0] == Reagent:
                content[1] = float(Volume)

    def print(self):
        print("Information for " + self.name)
        print("Plate Type: " + self.type)
        content = self.get_content()
        print("Well\tVolume(uL)\tLiquid Class\tReagent")
        content_return = ""
        for well in content:
            for c in content[well]:
                content_return += (well+"\t"+str(c[1])+"\t\t"+c[2]+"\t\t"+c[0]+ "\n")
                print(well+"\t"+str(c[1])+"\t\t"+c[2]+"\t\t"+c[0])
        return(content_return)


    def import_labware(self, filename, path="~", ext=".xlsx"):
        return(self.import_plate(filename, path, ext))


    # create a dummy PlateLayout object before running this method
    def import_plate(self, filename, path="~", ext=".xlsx"):
        import pandas as pd
        # check if filename contains the extension
        # NOTE: this only checks for a "." so could easily throw errors if given atypical input
        if "." in filename:
            # look at Sheet1 (the Plate Metadata)
            sheet1 = pd.read_excel(path+filename, sheet_name=0, header=None, engine='openpyxl')
            # look at Sheet2 (the Well lookup)
            sheet2 = pd.read_excel(path+filename, sheet_name=1, engine='openpyxl')
        else:
            # add extension (default = ".xlsx") to arg1
            sheet1 = pd.read_excel(path+filename+ext, sheet_name=0, header=None, engine='openpyxl')
            sheet2 = pd.read_excel(path+filename+ext, sheet_name=1, engine='openpyxl')

        # get plate name and plate type from Sheet 1
        # TODO: throw an error message if the name and/or type are blank
        self.name = sheet1[1].iloc[0] # column 2, row 1
        self.type = sheet1[1].iloc[1] # column 2, row 2

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
        return(self)


class PlateLayout(Labware_Layout):
    pass


class Liquids:
    def __init__(self):
        self.liquids = {}

    def add_liquid(self, liquid, labware, source_well):
        self.liquids[liquid] = [labware, source_well]

    def get_liquids_in_labware(self, labware):
        liquids_to_return = []
        for liquid in self.liquids:
            if labware == self.get_liquid_labware(liquid):
                liquids_to_return.append(liquid)

        return(liquids_to_return)

    def get_liquid_by_location(self, labware, well):
        liquid_to_return = None
        for liquid in self.liquids:
            if labware == self.get_liquid_labware(liquid) and well == self.get_liquid_well(liquid):
                liquid_to_return = liquid
                break
        if liquid_to_return == None:
            raise ValueError("No liquid found in labware {} at well {}".format(labware, well))
        else:
            return(liquid_to_return)

    def get_liquid(self, liquid):
        return(self.liquids[liquid])

    def get_liquid_labware(self, liquid):
        return(self.liquids[liquid][0])

    def get_liquid_well(self, liquid):
        return(self.liquids[liquid][1])

    def add_liquids_to_labware(self, liquids, labware, blocked_wells = None, well_range = None):
        if well_range:
            wells = well_range
        else:
            wells = list(labware.wells_by_name().keys())

        if blocked_wells:
            for bw in blocked_wells:
                wells.remove(bw)
        for l in liquids:
            self.liquids[l] = [labware, wells[0]]
            wells.remove(wells[0])

    def get_all_liquids(self):
        return(list(self.liquids.keys()))

##########################################
# Functions

def DoE_Get_Value_From_Combined_Factor(Factor_Name, Combined_Factor):
    Value = Combined_Factor.split(Factor_Name)[1].split("(")[1].split(")")[0]

    # Try and return as a float - if a ValueError is raised, assume the value is a string and just return as is
    try:
        Value = float(Value)
    except ValueError:
        pass

    return(Value)

def DoE_Create_Source_Material(DoE_Experiment, Source_Material_Name, Factor_Names, Add_To_Runs = True):
    # Create an empty list to store each of source material types
    ## Each source material type is formed from combinations of the same factors...
    ## ... with different values as specified by the DoE
    Source_Material_Types = []

    Source_Material_Component_Info = {} # ID: list(Factor Values)

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
                source_material_type.append("{}({})".format(component_factor, component_factor_value))
            # Convert the list of factor name-value combinations to a string and add to the previously created list
            Source_Material_Types.append("-".join(source_material_type))
            Source_Material_Component_Info["-".join(source_material_type)] = component_factor_values
            if Add_To_Runs:
                run.specify_source_material(Source_Material_Name, "-".join(source_material_type))
        for material_id in set(Source_Material_Types):
            Material_Object = DoE_Material(material_id, Source_Material_Name, Factor_Names, Source_Material_Component_Info[material_id])
            DoE_Experiment.add_material(Material_Object)
    else:
        Source_Material_Types = [Source_Material_Name]
        Source_Material_Component_Info = {
            Source_Material_Name: None
        }
        if Add_To_Runs:
            for run in DoE_Experiment.runs:
                run.specify_source_material(Source_Material_Name, Source_Material_Name)

        Material_Object = DoE_Material(Source_Material_Name, Source_Material_Name)
        DoE_Experiment.add_material(Material_Object)

    return(Source_Material_Types)

def DoE_Create_Intermediate(DoE_Experiment, Intermediate_Name, Source_Material_Names, Source_Materials_Amount_Types, Source_Materials_Amount_Values, Add_To_Runs = True):
    # Create an empty list to store each of intermediate types
    ## Each intermediate type is formed from combinations of the same source materials...
    ## ... with different values as specified by the DoE
    Intermediate_Types = []

    Intermediate_Component_Info = {}

    # For each run in the DoE
    for run in DoE_Experiment.runs:
        # Get the values of all the specified source_materials
        intermediate_type = []
        component_source_material_values = []
        for component_source_material, amount_type, amount_value in zip(Source_Material_Names, Source_Materials_Amount_Types, Source_Materials_Amount_Values):
            component_source_material_value = run.get_source_material_value(component_source_material)

            # Check to see if any factors are specified as references for amounts of components to be added
            ## Different amounts of a source material being added results in extra combinations
            ### e.g. an intermediate type might be composed of a buffer and a chemical
            ### But the amount of chemical is determined by Factor-1, which has two values in the DoE
            ### Therefore, there will need to be two unique versions of the intermediate type to account for these differences

            if amount_value in DoE_Experiment.factors:
                amount_value = run.get_factor_value(amount_value)
                component_source_material = "{}[{}]".format(component_source_material, amount_value)


            component_source_material_values.append([component_source_material_value, amount_value])
            # Store the source_material name-value combination as a string in a list
            intermediate_type.append("{}({})".format(component_source_material, component_source_material_value))



        # Convert the list of source_material name-value combinations to a string and add to the previously created list
        Intermediate_Types.append("-".join(intermediate_type))
        Intermediate_Component_Info["-".join(intermediate_type)] = component_source_material_values
        if Add_To_Runs:
            run.specify_intermediate(Intermediate_Name, "-".join(intermediate_type))

    for intermediate_id in set(Intermediate_Types):
        component_ids = [id[0] for id in Intermediate_Component_Info[intermediate_id]]
        component_amount_values = [id[1] for id in Intermediate_Component_Info[intermediate_id]]
        Intermediate_Object = DoE_Intermediate(intermediate_id, Intermediate_Name, Source_Material_Names, component_ids, Source_Materials_Amount_Types, component_amount_values)
        DoE_Experiment.add_intermediate(Intermediate_Object)


    return(Intermediate_Types)

def Reagent_Finder(Reagents, Directories):
    import os
    # Get all labware layouts in the specified directories
    Files = []
    for directory in Directories:
        Files.append([file for file in os.listdir(directory+"/") if os.path.isfile(os.path.join(directory+"/", file)) and not "~$" in file])

    Layouts = []
    for files, directory in zip(Files, Directories):
        for file in files:
            try:
                Layouts.append(
                    Import_Labware_Layout(
                        Filename = file,
                        path = directory+"/"
                    )
                )
            except:
                continue

    # Check if each reagent is in a labware file
    for reagent in Reagents:
        print("\n{}:".format(reagent))
        for layout in Layouts:
            if len(layout.get_wells_containing_liquid(reagent)) > 0:
                print("> {}: {}".format(layout.name, layout.get_wells_containing_liquid(reagent)))

def Import_Labware_Layout(Filename, path = "~", ext = ".xlsx"):
    labware_layout = Labware_Layout("name", "type")
    labware_layout.import_labware(Filename, path = path, ext = ext)
    return(labware_layout)

def Import_Plate_Layout(Filename, path = "~", ext = ".xlsx"):
    return(Import_Labware_Layout(Filename, path = path, ext = ext))

def Create_Plates_Needed(Plate_Format, N_Wells_Needed, N_Wells_Available = "All", Return_Original_Layout = True):
    if not type(N_Wells_Available) is int:
        if N_Wells_Available == "All":
            N_Wells_Available = Plate_Format.rows * Plate_Format.columns
        else:
            raise ValueError("`N_Wells_Available` should either be an integer, or 'All'.")

    N_Plates_Needed = math.ceil(N_Wells_Needed/N_Wells_Available)
    if Return_Original_Layout == True:
        Plates = [Plate_Format]
    elif Return_Original_Layout == False:
        Plates = []
    for plate_n in range(1, N_Plates_Needed):
        Plate_Name = Plate_Format.name + str(plate_n)
        Plates.append(Plate_Format.clone_format(Plate_Name))
    return(Plates)


def well_range(Wells, Labware_Format = None, Direction = "Horizontal", Box = False):
    if not Direction == "Horizontal" and not Direction == "Vertical":
        raise ValueError("`Direction` must be either 'Horizontal' or 'Vertical'")

    if not Labware_Format and not Box:
        raise LabwareError("`Box` can only be `False` when `Labware_Format` is specified")

    if not Labware_Format or Box:
        Well = Wells
        first, last = Well.split(":")
        firstL = first[0]
        lastL = last[0]
        firstN = int(first[1:len(first)])
        lastN = int(last[1:len(last)])
        wells = []
        if Direction == "Horizontal":
            for L in _Lrange(firstL,lastL):
                for N in range(firstN,lastN+1):
                    wells.append(L+str(N))
            return(wells)
        elif Direction == "Vertical":
            for N in range(firstN,lastN+1):
                for L in _Lrange(firstL,lastL):
                    wells.append(L+str(N))
            return(wells)

    else:
        # Get the end row and end column number for the labware being used
        if type(Labware_Format) is list:
            if not len(Labware_Format) == 2:
                raise ValueError("Labware_Format argument MUST either be a BiomationScripter.PlateLayout object, or a list specifying number of rows and number of columns (e.g. [8, 12]).")
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
        if (_Labware_Row_To_Index(first_row) > end_row - 1) or (_Labware_Row_To_Index(last_row) > end_row - 1) or (first_col > end_col) or (last_col > end_col):
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
                        return(wells)

        elif Direction == "Vertical":
            rows = []
            for r in _Lrange("A", chr(64 + end_row)):
                rows.append(r)

            first_row_of_col_index = _Labware_Row_To_Index(first_row)

            for col in range(first_col, last_col + 1):
                for row in rows[first_row_of_col_index:]:
                    well = "{}{}".format(row,col)
                    wells.append(well)
                    if row == rows[-1]:
                        first_row_of_col_index = 0
                    if well == last_well:
                        return(wells)

def Group_Locations(Locations, Group_Populations):
    Grouped_Locations = []
    start_index = 0
    end_index = 0
    for group_pop in Group_Population:
        end_index += group_pop
        Grouped_Locations.append(Locations[start_index:end_index])
        start_index += group_pop
    return(Grouped_Locations)

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
def _Lrange(L1,L2): # Between L1 and L2 INCLUSIVE of L1 and L2
    L1 = ord(L1.upper())
    L2 = ord(L2.upper())
    for L in range(L1,L2+1):
        yield(chr(L))

def _Labware_Row_To_Index(row):
    return(ord(row.upper()) - ord("A"))

## To be deprecated ##

def aliquot_calculator(Volume_Required, Volume_Per_Aliquot, Dead_Volume = 0):
    print("This will soon be deprecated")
    return(math.ceil(Volume_Required/(Volume_Per_Aliquot + Dead_Volume)))
