import BiomationScripter as _BMS
import BiomationScripter.EchoProto as _EchoProto
import math
from typing import List, NewType

#### PROTOCOL TEMPLATES ####

class Loop_Assembly(_EchoProto.EchoProto_Template):
    def __init__(self,
        Enzyme: str,
        Source_Plates: List[_BMS.Labware_Layout],
        Destination_Plate_Layout: _BMS.Labware_Layout,
        Volume: float,
        Assemblies: List[_BMS.Assembly],
        Backbone_to_Part: List[str] = ["1:1"],
        Repeats: int = 1,
        Merge: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)

        print([
            Enzyme,
            Source_Plates,
            Destination_Plate_Layout,
            Volume,
            Assemblies,
            Backbone_to_Part,
            Repeats,
            Merge,
        ])


        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.volume = Volume # uL
        self.ratios = Backbone_to_Part
        self.repeats = Repeats
        self.enzyme = Enzyme

        # Deal with assemblies as a list or a list of the new object
        self.assemblies = []
        for assembly in Assemblies:
            if type(Assemblies[0]) == _BMS.Assembly:
                self.assemblies.append([assembly.backbone, assembly.parts])
            else:
                self.assemblies.append(assembly)

        self.merge = Merge

        ###########
        # Labware #
        ###########
        # Add source layouts to self.source_plate_layouts
        for source in Source_Plates:
            self.add_source_layout(source)

        # Add the destination layout (more may be created later if needed)
        #NOTE - This might break some things or cause unexpected behaviour
        if not Destination_Plate_Layout.get_available_wells():
            Destination_Plate_Layout.set_available_wells()
        self.add_destination_layout(Destination_Plate_Layout)

        ##############################################
        # Default reagent amounts for 5 uL reactions #
        ##############################################
        self.__default_volume = 5
        self._enzyme_amount = 0.125
        self._buffer_amount = 0.5
        self._ligase_amount = 0.125

        ##########################################
        # Default DNA amounts for 5 uL reactions #
        ##########################################
        # For 1:1 ratio, and source concentration of 10 fmol/uL
        self._backbone_amount = 0.25
        self._part_amount = 0.25

        #########################
        # Default reagent names #
        #########################
        self.buffer = "T4 Ligase Buffer"
        self.ligase = "T4 Ligase"
        self.water = "Water"

        self.assembly_locations = []

    def run(self):

        ###################################################
        # Calculate number of destination plates required #
        ###################################################
        # Determine final number of assemblies, and hence number of destination wells required
        n_assemblies = (len(self.assemblies) * len(self.ratios)) * self.repeats

        # Create the number of destination plates needed as layout objects
        extra_destination_layouts = _BMS.Create_Plates_Needed(
            Plate_Format = self.destination_plate_layouts[0],
            N_Wells_Needed = n_assemblies,
            N_Wells_Available = len(self.destination_plate_layouts[0].get_available_wells()),
            Return_Original_Layout = False
        )

        # Add any extra destination plates needed
        for layout in extra_destination_layouts:
            self.add_destination_layout(layout)

        ######################################
        # Calculate reagent volumes required #
        ######################################
        # Volume factor is the difference between the default volume (5 uL) and the user-define final volume
        volume_factor = self.volume/self.__default_volume
        # Use the volume factor to calculate the reagent volumes
        enzyme_amount = self._enzyme_amount*volume_factor
        buffer_amount = self._buffer_amount*volume_factor
        ligase_amount = self._ligase_amount*volume_factor
        # Store the total amount of reagents per reaction for later use
        reagent_amount = enzyme_amount + buffer_amount + ligase_amount

        ########################################
        # Add liquids to destination layout(s) #
        ########################################
        # Counter to track which destination plate is in use
        destination_plate_index = 0
        # Counter to track which destination well is in use
        destination_well_index = 0

        # For every reaction
        for assembly in self.assemblies:
            for ratio in self.ratios:
                for rep in range(0, self.repeats):
                    backbone_amount = (self._backbone_amount*volume_factor)*float(ratio.split(":")[0])
                    part_amount = (self._part_amount*volume_factor)*float(ratio.split(":")[1])
                    water_amount = self.volume - (backbone_amount + (part_amount*len(assembly[1])) + reagent_amount)

                    # Get the current destination plate and well
                    current_destination_plate = self.destination_plate_layouts[destination_plate_index]
                    current_destination_well = current_destination_plate.available_wells[destination_well_index]

                    # Add the reagents, water, and DNA to the destinaton plate
                    try:
                        current_destination_plate.add_content(current_destination_well, self.water, water_amount)
                        if type(self.buffer) == list:
                            for buffer in self.buffer:
                                current_destination_plate.add_content(current_destination_well, buffer, buffer_amount/len(self.buffer))
                        else:
                            current_destination_plate.add_content(current_destination_well, self.buffer, buffer_amount)
                        current_destination_plate.add_content(current_destination_well, self.enzyme, enzyme_amount)
                        current_destination_plate.add_content(current_destination_well, self.ligase, ligase_amount)
                        backbone_name = assembly[0]
                        well_label = "{}: ".format(backbone_name)
                        current_destination_plate.add_content(current_destination_well, backbone_name, backbone_amount)
                        DNA_part_names = assembly[1]
                        for part_name in DNA_part_names:
                            current_destination_plate.add_content(current_destination_well, part_name, part_amount)
                            well_label += "{} + ".format(part_name)

                        well_label = "{}{}{}".format(well_label[:-2], ratio,rep)

                        current_destination_plate.add_well_label(current_destination_well, well_label)
                    # Raise a more relevant error message if NegativeVolumeError occurs
                    except _BMS.NegativeVolumeError:
                        raise _BMS.NegativeVolumeError("This assembly is above the reaction volume: {}, {}".format(assembly, ratio))

                    # Iterate to the next destination well
                    destination_well_index += 1
                    # Check if the current destinaton plate is full
                    if destination_well_index - 1 == len(current_destination_plate.available_wells):
                        # If so, iterate to the first well of the next destination plate
                        destination_plate_index += 1
                        destination_well_index = 0

        # Generate the picklists
        self.create_picklists(self.merge)

class PCR(_EchoProto.EchoProto_Template):
    def __init__(self,
        Polymerase: str,
        Polymerase_Buffer: str,
        Source_Plates: List[_BMS.Labware_Layout],
        Destination_Plate_Layout: _BMS.Labware_Layout,
        Volume: float,
        Reactions: List[str],
        Master_Mix: bool = False,
        Repeats: int = 1,
        Merge: bool = False,
        **kwargs
    ):

        super().__init__(**kwargs)

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.volume = Volume # uL
        self.repeats = Repeats
        self.reactions = Reactions
        self.polymerase = Polymerase
        self.buffer = Polymerase_Buffer
        self.master_mix = Master_Mix
        self.merge = Merge

        ###########
        # Labware #
        ###########
        # Add source layouts to self.source_plate_layouts
        for source in Source_Plates:
            self.add_source_layout(source)

        # Add the destination layout (more may be created later if needed)
        self.add_destination_layout(Destination_Plate_Layout)

        ###########################
        # Default reagent amounts #
        ###########################
        self.__default_volume = 5

        self._dNTPs_amount = 0.1
        self._buffer_amount = 1
        self._polymerase_amount = 0.05
        self._master_mix_amount = 2.5

        ##################################
        # Default DNA and primer amounts #
        ##################################
        # Default DNA amounts in uL for 5 uL reactions, and 1 - 1000 ng/uL stock concentration
        self._dna_amount = 1
        # Default primer amounts in uL for 5 uL reactions, and 10 μM stock concentration
        self._primer_amount = 0.25

        #########################
        # Default reagent names #
        #########################
        self.dNTPs = "dNTPs"
        self.water = "Water"

    def run(self):

        ###################################################
        # Calculate number of destination plates required #
        ###################################################
        # Determine final number of reactions, and hence number of destination wells required
        n_reactions = len(self.reactions) * self.repeats

        # Create the number of destination plates needed as layout objects
        extra_destination_layouts = _BMS.Create_Plates_Needed(
            Plate_Format = self.destination_plate_layouts[0],
            N_Wells_Needed = n_reactions,
            N_Wells_Available = len(self.destination_plate_layouts[0].get_available_wells()),
            Return_Original_Layout = False
        )

        # Add any extra destination plates needed
        for layout in extra_destination_layouts:
            self.add_destination_layout(layout)

        ######################################
        # Calculate reagent volumes required #
        ######################################
        # Volume factor is the difference between the default volume (5 uL) and the user-define final volume
        volume_factor = self.volume/self.__default_volume

        # Use the volume factor to calculate the reagent volumes
        dna_amount = self._dNTPs_amount * volume_factor
        primer_amount = self._primer_amount * volume_factor

        # Determine if a mastermix is being used
        if self.master_mix:
            master_mix_amount = self._master_mix_amount * volume_factor
            reagent_amount = master_mix_amount + dna_amount + (2 * primer_amount)
        else:
            dNTPs_amount = self._dNTPs_amount * volume_factor
            buffer_amount = self._buffer_amount * volume_factor
            polymerase_amount = self._polymerase_amount * volume_factor
            reagent_amount = dNTPs_amount + buffer_amount + polymerase_amount + dna_amount + (2 * primer_amount)

        water_amount = self.volume - reagent_amount

        ########################################
        # Add liquids to destination layout(s) #
        ########################################
        # Counter to track which destination plate is in use
        destination_plate_index = 0
        # Counter to track which destination well is in use
        destination_well_index = 0

        # For every reaction
        for reaction in self.reactions:
            for rep in range(0, self.repeats):
                # Get the current destination plate and well
                current_destination_plate = self.destination_plate_layouts[destination_plate_index]
                current_destination_well = current_destination_plate.available_wells[destination_well_index]

                # Add the reagents, water, and DNA to the destinaton plate
                try:
                    current_destination_plate.add_content(current_destination_well, self.water, water_amount)
                    current_destination_plate.add_content(current_destination_well, reaction[0], dna_amount)
                    current_destination_plate.add_content(current_destination_well, reaction[1], primer_amount)
                    current_destination_plate.add_content(current_destination_well, reaction[2], primer_amount)

                    if self.master_mix:
                        current_destination_plate.add_content(current_destination_well, self.master_mix, master_mix_amount)
                    else:
                        current_destination_plate.add_content(current_destination_well, self.dNTPs, dNTPs_amount)
                        current_destination_plate.add_content(current_destination_well, self.buffer, buffer_amount)
                        current_destination_plate.add_content(current_destination_well, self.polymerase, polymerase_amount)

                    # Label the well
                    current_destination_plate.add_well_label(current_destination_well, "{}-{}-{}-{}".format(reaction[0], reaction[1], reaction[2], rep))
                # Raise a more relevant error message if NegativeVolumeError occurs
                except _BMS.NegativeVolumeError:
                    raise _BMS.NegativeVolumeError("This assembly is above the reaction volume: {}, {}".format(assembly, ratio))

                # Iterate to the next destination well
                destination_well_index += 1
                # Check if the current destinaton plate is full
                if destination_well_index - 1 == len(current_destination_plate.available_wells):
                    # If so, iterate to the first well of the next destination plate
                    destination_plate_index += 1
                    destination_well_index = 0

        # Generate the picklists
        self.create_picklists(self.merge)
