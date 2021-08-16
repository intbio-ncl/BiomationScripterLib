import BiomationScripter as _BMS
import math

#### PROTOCOL TEMPLATES ####

class Loop_Assembly: # Volume is uL, assumes parts are at 10 fmol
    """Protocol template for setting up Loop assembly reactions using the Echo 525.

    Attributes:
    name (str): A name for the protocol.\n
    volume (float): The final volume for the Loop assembly reactions in micorlitres.
        Default: 5\n
    ratios (list[str]): A list of Backbone:Part ratios
        Example: ["1:1", "1:2", "2:1"]
        Default: ["1:1"]\n
    splates (list[BiomationScripter.PlateLayout]): A list of source plates which contain the required reagents.\n
    dplate_format (list[list[BiomationScripter.PlateLayout, list[str]]]): A list of two-element lists, where the first element is an empty PlateLayout object with a defined format to be used as the destination plate, and the second element is a list of available wells.
        Example: [[BiomationScripter.PlateLayout, ["A1","A2","A3"]],...]\n
    assemblies (list[str,list[str]]): A list of assemblies specified using two-element lists, where the first element is the backbone, and the second element is a list of parts
        Example: [["Backbone", ["Part1","Part2"]],...]\n
    repeats (int): The number of reactions to be prepared for each assembly specified.
        Default: 1\n
    _enzyme_amount (float): The amount of enzyme, in microliters, to add per 5 microlitres of reaction.
        Default: 0.125\n
    _ligase_buffer_amount (float): The amount of ligase buffer, in microliters, to add per 5 microlitres of reaction.
        Default: 0.5\n
    _ligase_amount (float): The amount of ligase, in microliters, to add per 5 microlitres of reaction.
        Default: 0.125\n
    _backbone_amount (float): Amount of DNA backbone, in microlitres, to add per 5 microlitre reaction, assuming 1:1 backbone:part ratio, and 10 fmol stock concentration.
        Default: 0.25\n
    _part_amount (float): Amount of each DNA part, in microlitres, to add per 5 microlitre reaction, assuming 1:1 backbone:part ratio, and 10 fmol stock concentration.
        Default: 0.25\n
    enzyme (str): Enzyme name. This should match the name given in the BiomationScripter.PlateLayout source plate(s).\n
    ligase_buffer (str): Ligase Buffer name. This should match the name given in the BiomationScripter.PlateLayout source plate(s).
        Default: "T4 Ligase Buffer")\n
    ligase (str): Ligase name. This should match the name given in the BiomationScripter.PlateLayout source plate(s).
        Default: "T4 Ligase"\n
    water (str): Water name. This should match the name given in the BiomationScripter.PlateLayout source plate(s).
        Default: "Water"\n

    """

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

    def define_destination_plate(self, Plate_Layout, Well_Range=None, UseOuterWells=True):
        self.dplate_format = [Plate_Layout, Plate_Layout.get_well_range(Well_Range, UseOuterWells)]

    def make_picklist(self,Directory):
        dplates = []
        n_assemblies = (len(self.assemblies) * len(self.ratios)) * self.repeats
        wells_per_dplate = len(self.dplate_format[1])
        n_dplates = math.ceil(n_assemblies/wells_per_dplate)
        dplate_well_range = self.dplate_format[1]

        for d in range(0,n_dplates):
            Name = self.dplate_format[0].name+"_"+str(d)
            dplates.append(self.dplate_format[0].clone_format(Name))

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

        # Create protocol and generate picklists
        Protocol = _BMS.EchoProto.Protocol(self.name)
        Protocol.add_source_plates(self.splates)
        Protocol.add_destination_plates(dplates)
        _BMS.EchoProto.Generate_Actions(Protocol)
        _BMS.EchoProto.Write_Picklists(Protocol,Directory)


class Q5PCR:
    def __init__(self, Name, Volume, Repeats = 1, Master_Mix = False):
        self.name = Name
        self.volume = Volume
        self.repeats = Repeats
        self.splates = []
        self.dplate_format = None
        self.samples = []
        self._master_mix = Master_Mix
        # Default volume for reagent amounts
        self.__default_volume = 5
        self.__volume_factor = self.volume/self.__default_volume
        # Default reagent amounts (in uL) for 5 uL reactions
        self._dNTPs_amount = 0.1
        self._Q5_buffer_amount = 1
        self._Q5_polymerase_amount = 0.05
        self._master_mix_amount = 2.5
        # Default DNA amounts in uL for 5 uL reactions, and 1 - 1000 ng/uL stock concentration
        self._dna_amount = 1
        # Default primer amounts in uL for 5 uL reactions, and 10 μM stock concentration
        self._primer_amount = 0.25
        # Default names
        self.dNTPs = "dNTPs"
        self.Q5_buffer = "Q5 Buffer"
        self.Q5_polymerase = "Q5 Polymerase"
        self.master_mix = "Q5 Master Mix"
        self.water = "Water"

    def add_sample(self,Template,Primer1,Primer2):
        self.samples.append([Template,Primer1,Primer2])

    def add_source_plate(self,SPlate):
        self.splates.append(SPlate)

    def define_destination_plate(self, Plate_Layout, Well_Range=None, Use_Outer_Wells=True):
        self.dplate_format = [Plate_Layout, Plate_Layout.get_well_range(Well_Range, Use_Outer_Wells)]

    def make_picklist(self, Directory):
        n_samples = len(self.samples) * self.repeats
        wells_per_dplate = len(self.dplate_format[1])
        dplates = _BMS.Create_Plates_Needed(self.dplate_format[0], n_samples, wells_per_dplate)

        dna_amount = self._dNTPs_amount*self.__volume_factor
        primer_amount = self._primer_amount*self.__volume_factor

        if self._master_mix:
            master_mix_amount = self._master_mix_amount*self.__volume_factor
            reagent_amount = master_mix_amount + dna_amount + (2 * primer_amount)
        else:
            dNTPs_amount = self._dNTPs_amount*self.__volume_factor
            Q5_buffer_amount = self._Q5_buffer_amount*self.__volume_factor
            Q5_polymerase_amount = self._Q5_polymerase_amount*self.__volume_factor
            reagent_amount = dNTPs_amount + Q5_buffer_amount + Q5_polymerase_amount + dna_amount + (2 * primer_amount)

        water_amount = self.volume - reagent_amount
        # If need to add less than 0.025 uL water, just add none (too small for echo to transfer)
        if water_amount < 0.025:
            water_amount = 0

        dplate_id = 0
        dplate_current_well = 0
        dplate_well_range = self.dplate_format[1]

        for sample in self.samples:
            for rep in range(0, self.repeats):
                dplate = dplates[dplate_id]

                dplate.add_content(dplate_well_range[dplate_current_well], sample[0], dna_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], sample[1], primer_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], sample[2], primer_amount)
                dplate.add_content(dplate_well_range[dplate_current_well], self.water, water_amount)

                if self._master_mix:
                    dplate.add_content(dplate_well_range[dplate_current_well], self.master_mix, master_mix_amount)
                else:
                    dplate.add_content(dplate_well_range[dplate_current_well], self.dNTPs, dNTPs_amount)
                    dplate.add_content(dplate_well_range[dplate_current_well], self.Q5_buffer, Q5_buffer_amount)
                    dplate.add_content(dplate_well_range[dplate_current_well], self.Q5_polymerase, Q5_polymerase_amount)

                dplate_current_well += 1
                # Check if the current destination plate is full, and if so move on to the next plate
                if dplate_current_well - 1 == len(dplate_well_range):
                    dplate_id += 1
                    dplate_current_well = 0

        # Create protocol and generate picklists
        Protocol = _BMS.EchoProto.Protocol(self.name)
        Protocol.add_source_plates(self.splates)
        Protocol.add_destination_plates(dplates)
        _BMS.EchoProto.Generate_Actions(Protocol)
        _BMS.EchoProto.Write_Picklists(Protocol,Directory)






        #
        #
        # # Note that DestinationWellRange overrides UseOuterWells
        # # DestinationWellRange can be a list of wells, or a continous range in the format "R1C1:R2C2"
        # # Gap refers to gaps between well range given, so a well range of A2:A6 with a gap of 1 would give A2, A4, A6, and a gap of 0 would give A2, A3, A4, A5, A6
        # if Name == None:
        #     Name = self.name + "_Destination_Plate"
        # self.dplate = _BMS.PlateLayout(Name, Type)
        # self.dplate.define_format(Rows, Columns)
        # if DestinationWellRange:
        #     if isinstance(DestinationWellRange, list):
        #         for w in DestinationWellRange:
        #             if not self.dplate.check_well(w):
        #                 raise ValueError("Destination Well {} does not exist in plate {}".format(w,self.dplate.name))
        #         g = 0
        #         for w in DestinationWellRange:
        #             if g == 0:
        #                 self.dwellrange.append(w)
        #             if g == gap:
        #                 g = 0
        #             else:
        #                 g += 1
        #     elif isinstance(DestinationWellRange, str):
        #         start,end = DestinationWellRange.split(":")
        #         wells = []
        #         startrow = start[0]
        #         endrow = end[0]
        #         rows = _BMS.Lrange(startrow,endrow)
        #         c = int(start[1:])
        #         for r in rows:
        #             if r == endrow:
        #                 endc = int(end[1:])
        #             else:
        #                 endc = self.dplate.columns
        #             for c in range(c,endc+1):
        #                 if not UseOuterWells and (r == "A" or r >= chr(64 + self.dplate.rows) or c == 1 or c >= self.dplate.columns):
        #                     continue
        #                 else:
        #                     if not self.dplate.check_well("{}{}".format(r,c)):
        #                         raise ValueError("Destination Well {} does not exist in plate {}".format("{}{}".format(r,c),self.dplate.name))
        #                     wells.append("{}{}".format(r,c))
        #             c = 1
        #         g = 0
        #         for w in wells:
        #             if g == 0:
        #                 self.dwellrange.append(w)
        #             if g == gap:
        #                 g = 0
        #             else:
        #                 g += 1
        # else:
        #     start,end = "{}{}:{}{}".format("A","1",chr(64 + self.dplate.rows), self.dplate.columns).split(":")
        #     wells = []
        #     startrow = start[0]
        #     endrow = end[0]
        #     rows = _BMS.Lrange(startrow,endrow)
        #     c = int(start[1:])
        #     for r in rows:
        #         if r == endrow:
        #             endc = int(end[1:])
        #         else:
        #             endc = self.dplate.columns
        #         for c in range(c,endc+1):
        #             if not UseOuterWells and (r == "A" or r >= chr(64 + self.dplate.rows) or c == 1 or c >= self.dplate.columns):
        #                 continue
        #             else:
        #                 if not self.dplate.check_well("{}{}".format(r,c)):
        #                     raise ValueError("Destination Well {} does not exist in plate {}".format("{}{}".format(r,c),self.dplate.name))
        #                 wells.append("{}{}".format(r,c))
        #         c = 1
        #     g = 0
        #     for w in wells:
        #         if g == 0:
        #             self.dwellrange.append(w)
        #         if g == gap:
        #             g = 0
        #         else:
        #             g += 1
