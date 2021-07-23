from BiomationScripter import EchoProto
from BiomationScripter import OTProto
# from BiomationScripter import FelixProto

def WellInRange(Plate, Well):
    Row = Well[0]
    Column = int(Well[1:])
    InRange = None
    if Row > chr(64 + Plate.rows):
        InRange = False
    elif Column > Plate.columns:
        InRange = False
    else:
        InRange = True
    return(InRange)

def copy_plate_format(Plate_Layout, New_Name):
    """Does not copy content"""
    name = Plate_Layout.name
    type = Plate_Layout.type
    rows = Plate_Layout.rows
    columns = Plate_Layout.columns
    plate_copy = PlateLayout(name, type)
    plate_copy.define_format(rows, columns)
    return(plate_copy)

class PlateLayout:
    def __init__(self, Name, Type):
        self.name = Name
        self.type = Type
        self.rows = None
        self.columns = None
        self.content = {}

    def define_format(self, rows, columns):
        self.rows = rows
        self.columns = columns

    def add_content(self, Well, Reagent, Volume, Liquid_Class = False):
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

    def print(self):
        print("Information for " + self.name)
        print("Plate Type: " + self.type)
        content = self.get_content()
        print("Well\tVolume(uL)\tLiquid Class\tReagent")
        for well in content:
            for c in content[well]:
                print(well+"\t"+str(c[1])+"\t\t"+c[2]+"\t\t"+c[0])

    def clear_content(self):
        self.content = {}

def well_range_for_plate(Plate_Layout, Well_Range=None, UseOuterWells=True):
    n_rows = Plate_Layout.rows
    n_cols = Plate_Layout.columns
    if Well_Range == None:
        Well_Range = "A1:{}{}".format(chr(64+n_rows),n_cols)

    plate_first_row = "A"
    plate_last_row = chr(64+n_rows)
    plate_first_col = 1
    plate_last_col = n_cols

    wells = well_range(Well_Range)

    if UseOuterWells == False:
        temp_wells = []
        for w in wells:
            if (plate_first_row in w) or (plate_last_row in w) or (str(plate_first_col) == w[1:]) or (str(plate_last_col) == w[1:]):
                continue
            else:
                temp_wells.append(w)
        wells = temp_wells

    return(wells)

def Lrange(L1,L2): # Between L1 and L2 INCLUSIVE of L1 and L2
    L1 = ord(L1.upper())
    L2 = ord(L2.upper())
    for L in range(L1,L2+1):
        yield(chr(L))

def well_range(Well):
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

class Liquids:
    def __init__(self):
        self.liquids = {}

    def add_liquid(self, liquid, labware, source_well):
        self.liquids[liquid] = [labware, source_well]

    def get_liquid_labware(self, liquid):
        return(self.liquids[liquid][0])

    def get_liquid_well(self, liquid):
        return(self.liquids[liquid][1])

    def add_liquids_to_labware(self, liquids, labware, blocked_wells = False):
        wells = list(labware.wells_by_name().keys())
        if blocked_wells:
            for bw in blocked_wells:
                wells.remove(bw)
        for l in liquids:
            self.liquids[l] = [labware, wells[0]]
            wells.remove(wells[0])

    def get_all_liquids(self):
        return(list(self.liquids.keys()))
