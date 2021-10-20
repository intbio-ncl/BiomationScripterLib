from BiomationScripter import EchoProto
from BiomationScripter import OTProto
# from BiomationScripter import FelixProto
import math
import pandas as pd

# Exception classes #

class NegativeVolumeError(Exception):
    pass

class UnknownLabware(Exception):
    pass

class UnknownHardware(Exception):
    pass

class RobotConfigurationError(Exception):
    pass

class BMSTemplateError(Exception):
    pass

#####################

class PlateLayout:
    def __init__(self, Name, Type):
        self.name = Name
        self.type = Type
        self.rows = None
        self.columns = None
        self.content = {}
        self.well_range = None

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

    def define_format(self, Rows, Columns):
        self.rows = Rows
        self.columns = Columns

    def update_volume_in_well(self, Volume, Reagent, Well):
        if not Well in self.get_content().keys():
            raise ValueError("{} has not been previously defined. Add content to this well using the `add_content` method.".format(Well))
        well_content = self.get_content()[Well]
        for content in well_content:
            if content[0] == Reagent:
                content[1] = float(Volume)

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

    def get_content(self):
        return(self.content)

    def clear_content(self):
        self.content = {}

    def clear_content_from_well(self, Well):
        del self.content[Well]

    def get_occupied_wells(self):
        return(self.get_content().keys())

    def get_wells_containing_liquid(self, Liquid_Name):
        wells_to_return = []
        content = self.get_content()
        wells = self.get_occupied_wells()
        for well in wells:
            for liquid in content[well]:
                if liquid[0] == Liquid_Name:
                    wells_to_return.append(well)

        return(wells_to_return)

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
            sheet1 = pd.read_excel(path+filename, sheet_name=0, header=None)
            # look at Sheet2 (the Well lookup)
            sheet2 = pd.read_excel(path+filename, sheet_name=1)
        else:
            # add extension (default = ".xlsx") to arg1
            sheet1 = pd.read_excel(path+filename+ext, sheet_name=0, header=None)
            sheet2 = pd.read_excel(path+filename+ext, sheet_name=1)

        # get plate name and plate type from Sheet 1
        self.name = sheet1[1].iloc[0] # column 2, row 1
        self.type = sheet1[1].iloc[1] # column 2, row 2

        # if Current Volume column is empty (NaN), replace with Initial Volume
        sheet2["Volume (uL) - Current"].fillna(sheet2["Volume (uL) - Initial"], inplace=True)
        # select subset of columns as "content"
        content = sheet2[["Well", "Name", "Volume (uL) - Current", "Calibration Type"]]
        # delete rows where the Name is blank
        content = content.dropna(subset=["Name"])
        # iterate over rows
        for row in content.itertuples(index=False):
            # add contents to PlateLayout object
            self.add_content(row[0], row[1], row[2], row[3])
        return(self)

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


# def well_range_for_plate(Plate_Layout, Well_Range=None, UseOuterWells=True):
#     n_rows = Plate_Layout.rows
#     n_cols = Plate_Layout.columns
#     if Well_Range == None:
#         Well_Range = "A1:{}{}".format(chr(64+n_rows),n_cols)
#
#     plate_first_row = "A"
#     plate_last_row = chr(64+n_rows)
#     plate_first_col = 1
#     plate_last_col = n_cols
#
#     wells = well_range(Well_Range)
#
#     if UseOuterWells == False:
#         temp_wells = []
#         for w in wells:
#             if (plate_first_row in w) or (plate_last_row in w) or (str(plate_first_col) == w[1:]) or (str(plate_last_col) == w[1:]):
#                 continue
#             else:
#                 temp_wells.append(w)
#         wells = temp_wells
#
#     return(wells)

def Create_Plates_Needed(Plate_Format, N_Wells_Needed, N_Wells_Available):
    N_Plates_Needed = math.ceil(N_Wells_Needed/N_Wells_Available)
    Plates = []
    for plate_n in range(0, N_Plates_Needed):
        Plate_Name = Plate_Format.name + str(plate_n)
        Plates.append(Plate_Format.clone_format(Plate_Name))
    return(Plates)

def Lrange(L1,L2): # Between L1 and L2 INCLUSIVE of L1 and L2
    L1 = ord(L1.upper())
    L2 = ord(L2.upper())
    for L in range(L1,L2+1):
        yield(chr(L))

def Labware_Row_To_Index(row):
    return(ord(row.upper()) - ord("A"))

def well_range(Wells, Labware_Format = None, Direction = "Horizontal"):

    if not Labware_Format:
        Well = Wells
        first, last = Well.split(":")
        firstL = first[0]
        lastL = last[0]
        firstN = int(first[1:len(first)])
        lastN = int(last[1:len(last)])
        rows = []
        cols = []
        wells = []
        for L in Lrange(firstL,lastL):
            for N in range(firstN,lastN+1):
                wells.append(L+str(N))
        return(wells)

    else:
        # Labware_Format = [n_rows,n_columns]
        end_row, end_col = Labware_Format

        first_well, last_well = Wells.split(":")

        first_row = first_well[0]
        last_row = last_well[0]
        first_col = int(first_well[1:])
        last_col = int(last_well[1:])

        # Check if first and last wells are in range
        if (Labware_Row_To_Index(first_row) > end_row - 1) or (Labware_Row_To_Index(last_row) > end_row - 1) or (first_col > end_col) or (last_col > end_col):
            raise ValueError("Wells are not in range of specified format")

        wells = []

        if Direction == "Horizontal":
            rows = []
            for r in Lrange(first_row, last_row):
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
            for r in Lrange("A", chr(64 + end_row)):
                rows.append(r)

            first_row_of_col_index = Labware_Row_To_Index(first_row)

            for col in range(first_col, last_col + 1):
                for row in rows[first_row_of_col_index:]:
                    well = "{}{}".format(row,col)
                    wells.append(well)
                    if row == rows[-1]:
                        first_row_of_col_index = 0
                    if well == last_well:
                        return(wells)

def aliquot_calculator(Volume_Required, Volume_Per_Aliquot, Dead_Volume = 0):
    return(math.ceil(Volume_Required/(Volume_Per_Aliquot + Dead_Volume)))
