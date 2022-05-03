import BiomationScripter as _BMS
import BiomationScripter.EchoProto as _EchoProto
import math
from typing import List, NewType, Dict

#### PROTOCOL TEMPLATES ####

class Loop_Assembly(_EchoProto.EchoProto_Template):
    def __init__(self,
        Enzyme: str,
        Buffer: str,
        Volume: float,
        Assemblies: List[_BMS.Assembly],
        Backbone_to_Part: List[str] = ["1:1"],
        Repeats: int = 1,
        **kwargs
    ):
        super().__init__(**kwargs)


        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.volume = Volume # uL
        self.ratios = Backbone_to_Part
        self.repeats = Repeats
        self.enzyme = Enzyme
        self.buffer = Buffer

        # Deal with assemblies as a list or a list of the new object
        self.assemblies = []
        for assembly in Assemblies:
            if type(Assemblies[0]) == _BMS.Assembly:
                self.assemblies.append([assembly.backbone, assembly.parts])
            else:
                self.assemblies.append(assembly)

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
        self.ligase = "T4 Ligase"
        self.water = "Water"

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
            layout.set_available_wells()
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
        self.create_picklists()

class PCR(_EchoProto.EchoProto_Template):
    def __init__(self,
        Polymerase: str,
        Polymerase_Buffer: str,
        Polymerase_Buffer_Stock_Conc: float,
        Volume: float,
        Reactions: List[str],
        Master_Mix: str = None,
        Master_Mix_Stock_Conc = None,
        Repeats: int = 1,
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
        self.master_mix_stock_conc = Master_Mix_Stock_Conc
        self.merge = Merge
        self.buffer_stock_conc = Polymerase_Buffer_Stock_Conc

        if not self.master_mix:
            if not self.polymerase or not self.buffer:
                raise _BMS.BMSTemplateError("If mastermix is not specified, then the polymerase and buffer to use must be given.")

        ###########################
        # Default reagent amounts #
        ###########################
        self.__default_volume = 5

        self._dNTPs_amount = 0.1
        self._buffer_amount = self.__default_volume / self.buffer_stock_conc
        self._polymerase_amount = 0.05
        if self.master_mix:
            if not self.master_mix_stock_conc:
                raise _BMS.BMSTemplateError("If master mix is specified, a stock concentration (e.g. 2x) must also be given.")
            else:
                self._master_mix_amount = self.__default_volume / self.master_mix_stock_conc
        else:
            self._master_mix_amount = None

        ##################################
        # Default DNA and primer amounts #
        ##################################
        # Default DNA amounts in uL for 5 uL reactions, and 1 - 1000 ng/uL stock concentration
        self.dna_amount = 1
        # Default primer amounts in uL for 5 uL reactions, and 10 μM stock concentration
        self.primer_amount = 0.25

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
        dna_amount = self.dna_amount * volume_factor
        primer_amount = self.primer_amount * volume_factor

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
        self.create_picklists()

class Colour_Mixing(_EchoProto.EchoProto_Template):
    def __init__(
        self,
        Source_Colours: List[str],
        Final_Volume: float,
        Mixing_Ratios: List[str],
        Permutations: bool = False,
        Merge: bool = True,
        **kwargs # This will make the superclass arguments available to `Colour_Mixing` as keyword arguments
    ):
        super().__init__(**kwargs) # This passes the keyword arguments to the superclass

        #######################
        # User Defined Values #
        #######################
        self.source_colours = Source_Colours
        self.final_volume = Final_Volume # uL
        self.mixing_ratios = Mixing_Ratios
        self.permutations = Permutations
        self.merge = Merge

    def run(self):

        # Set up an empty list in which the colour mixtures required will be added
        Colour_Mixtures = []

        # Iterate through the list of source colours provided to create the list of mixtures.
        for colour_1 in self.source_colours:
            for colour_2 in self.source_colours:
                # Ignore situations where colour_1 and colour_2 are the same
                if colour_1 == colour_2:
                    continue
                # Unless permutations has been set to `True`, ignore situations where...
                # ...the same colours have already been mixed, just in a different order
                elif not self.permutations and [colour_2, colour_1] in Colour_Mixtures:
                    continue
                else:
                    # Add the two colours to the list of mixtures to prepare
                    Colour_Mixtures.append([colour_1, colour_2])

        # Here, we'll print to OUT all of the mixtures which will be prepared
        for c in Colour_Mixtures:
            print(c)

        # Determine how may different mixtures will be prepared
        Number_Of_Mixtures = len(Colour_Mixtures) * len(self.mixing_ratios)

        # Use BMS.Create_Labware_Needed to ensure enough destination plates are available
        Extra_Destination_Plates_Required = _BMS.Create_Labware_Needed(
            Labware_Format = self.destination_plate_layouts[0],
            N_Wells_Needed = Number_Of_Mixtures,
            N_Wells_Available = "All",
            Return_Original_Layout = False
        )

        # If any extra plates were created, add them using the `add_destination_layout` method defined by the superclass
        for plate_layout in Extra_Destination_Plates_Required:
            self.add_destination_layout(plate_layout)

        # Add content to the destination plate(s)

        # A counter is used to iterate through the destination plates (if more than one)
        Destination_Plate_Index = 0

        for mixture in Colour_Mixtures:
            # Get the current destination plate
            Destination_Plate = self.destination_plate_layouts[Destination_Plate_Index]

            # Get the colours
            colour_1 = mixture[0]
            colour_2 = mixture[1]

            # For every ratio defined by the user
            for ratio in self.mixing_ratios:
                # Get the ratio for each colour
                colour_1_ratio = float(ratio.split(":")[0])
                colour_2_ratio = float(ratio.split(":")[1])

                # Get the volumes to add for each colour
                colour_1_volume = (colour_1_ratio/(colour_1_ratio + colour_2_ratio)) * self.final_volume
                colour_2_volume = (colour_2_ratio/(colour_1_ratio + colour_2_ratio)) * self.final_volume

                # Get the next empty well in the destination plate
                well = Destination_Plate.get_next_empty_well()
                # If there are no empty wells left, iterate to the next plate and try again
                if not well:
                    Destination_Plate_Index += 1
                    Destination_Plate = self.destination_plate_layouts[Destination_Plate_Index]
                    well = Destination_Plate.get_next_empty_well()

                # Add content to the plate
                Destination_Plate.add_content(
                    Well = well,
                    Reagent = colour_1,
                    Volume = colour_1_volume
                )
                Destination_Plate.add_content(
                    Well = well,
                    Reagent = colour_2,
                    Volume = colour_2_volume
                )

        self.create_picklists()
