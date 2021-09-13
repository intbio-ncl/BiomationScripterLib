from BiomationScripter import EchoProto
from BiomationScripter import OTProto
# from BiomationScripter import FelixProto
import math

class PlateLayout:
    def __init__(self, Name, Type):
        self.name = Name
        self.type = Type
        self.rows = None
        self.columns = None
        self.content = {}

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

    def add_content(self, Well, Reagent, Volume, Liquid_Class = False):
        # TODO: * Check is Well exists in the plate
        #       * Allow well ranges to span multiple columns
        #       * Don't overwrite current content if a well range is specified

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

        if Use_Outer_Wells == False:
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

class Liquids:
    def __init__(self):
        self.liquids = {}

    def add_liquid(self, liquid, labware, source_well):
        self.liquids[liquid] = [labware, source_well]

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

def well_range(Wells, Labware_Format):
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

    rows = []
    for r in Lrange(first_row, last_row):
        rows.append(r)

    wells = []
    row_index = 0
    first_col_of_row = first_col

    for row in rows:
        for col in range(first_col_of_row, end_col + 1):
            well = "{}{}".format(row, col)
            wells.append(well)
            if col == end_col:
                first_col_of_row = 1
            if well == last_well:
                return(wells)

def aliquot_calculator(Volume_Required, Volume_Per_Aliquot, Dead_Volume = 0):
    return(math.ceil(Volume_Required/(Volume_Per_Aliquot + Dead_Volume)))
