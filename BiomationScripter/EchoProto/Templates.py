import BiomationScripter as _BMS
import math

#### PROTOCOL TEMPLATES ####

class Loop_Assembly: # Volume is uL, assumes parts are at 10 fmol
    def __init__(self, Name, Enzyme, Volume = 5, Backbone_to_Part = ["1:1"], repeats = 1):
        self.name = Name
        self.volume = Volume # uL
        self.ratios = Backbone_to_Part
        self.splates = []
        self.dplate_format = None # [Plate_Layout, Wells_For_Use]
        self.assemblies = []
        self.repeats = repeats
        # Default reagent amounts (in uL) for 5 uL reactions
        self._enzyme_amount = 0.125
        self._ligase_buffer_amount = 0.5
        self._ligase_amount = 0.125
        # Default DNA amounts (in uL) for 5 uL reactions, 1:1 ratio, and 10 fmol concentration
        self._backbone_amount = 0.25
        self._part_amount = 0.25
        # Default names
        self.enzyme = Enzyme
        self.ligase_buffer = "T4 Ligase Buffer"
        self.ligase = "T4 Ligase"
        self.water = "Water"

    def add_assembly(self,Backbone,Parts):
        if isinstance(Parts, str):
            Parts = list(Parts)
        self.assemblies.append([Backbone,Parts])

    def add_source_plate(self,SPlate):
        self.splates.append(SPlate)

    def define_destination_plate(self,Plate_Layout, Well_Range=None, UseOuterWells=True):
        self.dplate_format = [Plate_Layout, _BMS.well_range_for_plate(Plate_Layout, Well_Range, UseOuterWells)]

    def make_picklist(self,Directory):
        dplates = []
        n_assemblies = (len(self.assemblies) * len(self.ratios)) * self.repeats
        wells_per_dplate = len(self.dplate_format[1])
        n_dplates = math.ceil(n_assemblies/wells_per_dplate)
        dplate_well_range = self.dplate_format[1]

        for d in range(0,n_dplates):
            dplates.append(_BMS.copy_plate_format(self.dplate_format[0],self.dplate_format[0].name+"_"+str(d)))

        volume_factor = self.volume/5
        enzyme_amount = self._enzyme_amount*volume_factor
        ligase_buffer_amount = self._ligase_buffer_amount*volume_factor
        ligase_amount = self._ligase_amount*volume_factor
        reagent_amount = enzyme_amount + ligase_buffer_amount + ligase_amount

        dplate_id = 0
        dplate_current_well = 0
        for assembly in self.assemblies:
            for ratio in self.ratios:
                backbone_amount = (self._backbone_amount*volume_factor)*float(ratio.split(":")[0])
                part_amount = (self._part_amount*volume_factor)*float(ratio.split(":")[1])
                water_amount = self.volume - (backbone_amount + (part_amount*len(assembly[1])) + reagent_amount)
                if water_amount < 0.025:
                    water_amount = 0
                    print("This assembly is above the reaction volume") # Add in identifier for assembly
                dplate = dplates[dplate_id]

                dplate.add_content(dplate_well_range[dplate_current_well], self.enzyme, enzyme_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], self.ligase_buffer, ligase_buffer_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], self.ligase, ligase_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], self.water, water_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], assembly[0], backbone_amount)
                for part in assembly[1]:
                    dplate.add_content(dplate_well_range[dplate_current_well], part, part_amount)

                dplate_current_well += 1
                if dplate_current_well - 1 == len(dplate_well_range):
                    dplate_id += 1
                    dplate_current_well = 0

        Protocol = _BMS.EchoProto.Protocol(self.name)
        for splate in self.splates:
            Protocol.add_source_plate(splate)
        for dplate in dplates:
            Protocol.add_destinationPlate(dplate)
        _BMS.EchoProto.Generate_Actions(Protocol)
        _BMS.EchoProto.writePickLists(Protocol,Directory)
        for tl in Protocol.TransferLists:
            for action in tl[0].get_actions():
                UID, Rea, SPN, Cali, SW, DPN, DPT, DW, Vol = action.get_all()
                SPType = tl[0].sourcePlate.type
                SPT = SPType + "_" + Cali
                line = str(UID) + "," + SPN + "," + SPT + "," + SW + "," + DPN + "," + DPT + "," + DW + "," + str(Vol) + "," + Rea + "\n" # Make less stupid (#DougKnows)
                print(line)


class Q5PCR:
    def __init__(self, Name, Volume):
        self.name = Name
        self.volume = Volume
        self.splates = []
        self.dplate = None
        self.dwellrange = []
        self.samples = []

    def add_sample(self,Template,Primer1,Primer2):
        self.samples.append([Template,Primer1,Primer2])

    def add_source_plate(self,SPlate):
        self.splates.append(SPlate)

    ##### ADD IN CODE TO ACCOUNT FOR USEOUTERWELLS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~######
    def define_destination_plate(self, Type, Rows, Columns, Name = None, UseOuterWells = True, DestinationWellRange = None, gap = 0):
        # Note that DestinationWellRange overrides UseOuterWells
        # DestinationWellRange can be a list of wells, or a continous range in the format "R1C1:R2C2"
        # Gap refers to gaps between well range given, so a well range of A2:A6 with a gap of 1 would give A2, A4, A6, and a gap of 0 would give A2, A3, A4, A5, A6
        if Name == None:
            Name = self.name + "_Destination_Plate"
        self.dplate = _BMS.PlateLayout(Name, Type)
        self.dplate.define_format(Rows, Columns)
        if DestinationWellRange:
            if isinstance(DestinationWellRange, list):
                for w in DestinationWellRange:
                    if not _BMS.WellInRange(self.dplate,w):
                        raise ValueError("Destination Well {} does not exist in plate {}".format(w,self.dplate.name))
                g = 0
                for w in DestinationWellRange:
                    if g == 0:
                        self.dwellrange.append(w)
                    if g == gap:
                        g = 0
                    else:
                        g += 1
            elif isinstance(DestinationWellRange, str):
                start,end = DestinationWellRange.split(":")
                wells = []
                startrow = start[0]
                endrow = end[0]
                rows = _BMS.Lrange(startrow,endrow)
                c = int(start[1:])
                for r in rows:
                    if r == endrow:
                        endc = int(end[1:])
                    else:
                        endc = self.dplate.columns
                    for c in range(c,endc+1):
                        if not UseOuterWells and (r == "A" or r >= chr(64 + self.dplate.rows) or c == 1 or c >= self.dplate.columns):
                            continue
                        else:
                            if not _BMS.WellInRange(self.dplate,"{}{}".format(r,c)):
                                raise ValueError("Destination Well {} does not exist in plate {}".format("{}{}".format(r,c),self.dplate.name))
                            wells.append("{}{}".format(r,c))
                    c = 1
                g = 0
                for w in wells:
                    if g == 0:
                        self.dwellrange.append(w)
                    if g == gap:
                        g = 0
                    else:
                        g += 1
        else:
            start,end = "{}{}:{}{}".format("A","1",chr(64 + self.dplate.rows), self.dplate.columns).split(":")
            wells = []
            startrow = start[0]
            endrow = end[0]
            rows = _BMS.Lrange(startrow,endrow)
            c = int(start[1:])
            for r in rows:
                if r == endrow:
                    endc = int(end[1:])
                else:
                    endc = self.dplate.columns
                for c in range(c,endc+1):
                    if not UseOuterWells and (r == "A" or r >= chr(64 + self.dplate.rows) or c == 1 or c >= self.dplate.columns):
                        continue
                    else:
                        if not _BMS.WellInRange(self.dplate,"{}{}".format(r,c)):
                            raise ValueError("Destination Well {} does not exist in plate {}".format("{}{}".format(r,c),self.dplate.name))
                        wells.append("{}{}".format(r,c))
                c = 1
            g = 0
            for w in wells:
                if g == 0:
                    self.dwellrange.append(w)
                if g == gap:
                    g = 0
                else:
                    g += 1
