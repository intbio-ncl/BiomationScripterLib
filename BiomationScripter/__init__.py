from BiomationScripter import EchoProto
from BiomationScripter import OTProto
# from BiomationScripter import FeliXProto
# from BiomationScripter import PIXLProto
# from BiomationScripter import AttuneProto
# from BiomationScripter import ClarioProto

import math
import pandas as pd

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

#####################
# Classes

class DoE_Experiment:
    def __init__(self, Name, DoE_File):
        self.name = Name
        self.doe_file = DoE_File

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

class DoE_Run_Data:
    def __init__(self, ID, Factors, Values):
        self.id = ID
        self.run_data = {}
        for factor, value in zip(Factors, Values):
            self.run_data[factor] = value

    def get_factor_value(self, Factor):
        return(self.run_data[Factor])

class Labware_Layout:
    def __init__(self, Name, Type):
        self.name = Name
        self.type = Type
        self.rows = None
        self.columns = None
        self.content = {}
        self.well_range = None

    def define_format(self, Rows, Columns):
        self.rows = Rows
        self.columns = Columns

    def get_format(self):
        return(self.rows, self.columns)

    def get_well_range(self, Well_Range=None, Use_Outer_Wells = True):
        n_rows = self.rows
        n_cols = self.columns
        if Well_Range == None:
            Well_Range = "A1:{}{}".format(chr(64+n_rows),n_cols)

        plate_first_row = "A"
        plate_last_row = chr(64+n_rows)
        plate_first_col = 1
        plate_last_col = n_cols

        wells = well_range(Well_Range)

        if not Use_Outer_Wells:
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

    def add_content(self, Well, Reagent, Volume, Liquid_Class = False):
        # TODO: * Check if Well exists in the plate
        #       * Allow well ranges to span multiple columns
        #       * Don't overwrite current content if a well range is specified
        if Volume < 0:
            raise NegativeVolumeError

        # Volume should always be uL
        if Liquid_Class == False:
            Liquid_Class = "Unknown"
        if ":" in Well:
            for w in well_range(Well):
                self.add_content(w, Reagent, Volume, Liquid_Class)
        elif Well in self.content:
            self.content[Well].append([Reagent,float(Volume), Liquid_Class])
        else:
            self.content[Well] = [ [Reagent,float(Volume), Liquid_Class] ]

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

    def clear_content_from_well(self, Well):
        del self.content[Well]

    def get_volume_of_liquid_in_well(self, Liquid, Well):
        if not Well in self.get_occupied_wells():
            raise LabwareError("Well {} in labware {} contains no liquids.".format(Well, self.name))
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


    # create a dummy PlateLayout object before running this method
    def import_plate(self, filename, path="~", ext=".xlsx"):
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

def Combine_DoE_Factors(DoE_Experiment, Factor_Names):
    # Create an empty list to store each of the specified factor combinations
    Combined_Factors = []
    # For each run in the DoE
    for run in DoE_Experiment.runs:
        # Get the values of all the specified factors
        combined_factor = []
        for component_factor in Factor_Names:
            component_factor_value = run.get_factor_value(component_factor)
            # Store the factor name-value combination as a string in a list
            combined_factor.append("{}({})".format(component_factor, component_factor_value))
        # Convert the list of factor name-value combinations to a string and add to the previously created list
        Combined_Factors.append("-".join(combined_factor))

    return(Combined_Factors)

def Import_Plate_Layout(Filename):
    plate_layout = PlateLayout("name", "type")
    plate_layout.import_plate(Filename)
    return(plate_layout)

def Create_Plates_Needed(Plate_Format, N_Wells_Needed, N_Wells_Available = "All"):
    if not type(N_Wells_Available) is int:
        if N_Wells_Available == "All":
            N_Wells_Available = Plate_Format.rows * Plate_Format.columns
        else:
            raise ValueError("`N_Wells_Available` should either be an integer, or 'All'.")

    N_Plates_Needed = math.ceil(N_Wells_Needed/N_Wells_Available)
    Plates = [Plate_Format]
    for plate_n in range(1, N_Plates_Needed):
        Plate_Name = Plate_Format.name + str(plate_n)
        Plates.append(Plate_Format.clone_format(Plate_Name))
    return(Plates)

def well_range(Wells, Labware_Format = None, Direction = "Horizontal", Box = True):
    if not Direction == "Horizontal" and not Direction == "Vertical":
        raise ValueError("`Direction` must be either 'Horizontal' or 'Vertical'")

    if not Labware_Format and not Box:
        raise LabwareError("`Box` can only be `False` when `Labware_Format` is specified")

    if not Labware_Format:
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
