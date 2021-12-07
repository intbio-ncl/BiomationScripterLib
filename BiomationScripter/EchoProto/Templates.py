import BiomationScripter as _BMS
import BiomationScripter.EchoProto as _EchoProto
import math

#### PROTOCOL TEMPLATES ####

class Loop_Assembly(_EchoProto.EchoProto_Template):
    def __init__(self,
        Enzyme,
        Source_Plates,
        Destination_Plate_Layout,
        Volume,
        Assemblies,
        Backbone_to_Part = ["1:1"],
        Repeats = 1,
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
        self.assemblies = Assemblies # [ [Backbone, [Part1, ... Partn]] ]

        ###########
        # Labware #
        ###########
        # Add source layouts to self.source_plate_layouts
        for source in Source_Plates:
            self.add_source_layout(source)

        # Add the destination layout (more may be created later if needed)
        self.add_destination_layout(Destination_Plate_Layout)

        ##############################################
        # Default reagent amounts for 5 uL reactions #
        ##############################################
        self.__default_volume = 5
        self._enzyme_amount = 0.125
        self._ligase_buffer_amount = 0.5
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
        self.ligase_buffer = "T4 Ligase Buffer"
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
        ligase_buffer_amount = self._ligase_buffer_amount*volume_factor
        ligase_amount = self._ligase_amount*volume_factor
        # Store the total amount of reagents per reaction for later use
        reagent_amount = enzyme_amount + ligase_buffer_amount + ligase_amount

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
                        current_destination_plate.add_content(current_destination_well, self.ligase_buffer, ligase_buffer_amount)
                        current_destination_plate.add_content(current_destination_well, self.enzyme, enzyme_amount)
                        backbone_name = assembly[0]
                        current_destination_plate.add_content(current_destination_well, backbone_name, backbone_amount)
                        DNA_part_names = assembly[1]
                        for part_name in DNA_part_names:
                            current_destination_plate.add_content(current_destination_well, part_name, part_amount)
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
        Polymerase,
        Polymerase_Buffer,
        Source_Plates,
        Destination_Plate_Layout,
        Volume,
        Reactions,
        Master_Mix = False,
        Repeats = 1,
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

# class PCR:
#     def __init__(self,
#         Name,
#         Volume,
#         Polymerase,
#         Polymerase_Buffer,
#         Repeats = 1,
#         Master_Mix = False,
#         Colony = False
#     ):
#
#         #####################
#         # Protocol Metadata #
#         #####################
#         self.name = Name
#
#         ########################################
#         # User defined aspects of the protocol #
#         ########################################
#         self.samples = []
#         self.volume = Volume
#         self.repeats = Repeats
#         self.buffer = Polymerase_Buffer
#         self.polymerase = Polymerase
#         self._master_mix = Master_Mix
#         self.colony_pcr = Colony
#
#         ###########
#         # Labware #
#         ###########
#         self.source_plates = []
#         self.destination_plate_format = None
#
#
#         ###########################
#         # Default reagent amounts #
#         ###########################
#         self.__default_volume = 5
#         self.__volume_factor = self.volume/self.__default_volume
#
#         self._dNTPs_amount = 0.1
#         self._buffer_amount = 1
#         self._polymerase_amount = 0.05
#         self._master_mix_amount = 2.5
#
#         ##################################
#         # Default DNA and primer amounts #
#         ##################################
#         # Default DNA amounts in uL for 5 uL reactions, and 1 - 1000 ng/uL stock concentration
#         self._dna_amount = 1
#         # Default primer amounts in uL for 5 uL reactions, and 10 μM stock concentration
#         self._primer_amount = 0.25
#
#         #########################
#         # Default reagent names #
#         #########################
#         self.dNTPs = "dNTPs"
#         self.master_mix = "Master Mix"
#         self.water = "Water"
#
#     def add_sample(self,Template,Primer1,Primer2):
#         self.samples.append([Template,Primer1,Primer2])
#
#     def add_source_plate(self,SPlate):
#         self.source_plates.append(SPlate)
#
#     def define_destination_plate(self, Plate_Layout, Well_Range=None, Use_Outer_Wells=True):
#         self.destination_plate_format = [Plate_Layout, Plate_Layout.get_well_range(Well_Range, Use_Outer_Wells)]
#
#     def make_picklist(self, Directory):
#         n_samples = len(self.samples) * self.repeats
#         wells_per_dplate = len(self.destination_plate_format[1])
#         dplates = _BMS.Create_Plates_Needed(self.destination_plate_format[0], n_samples, wells_per_dplate)
#
#         dna_amount = self._dNTPs_amount*self.__volume_factor
#         primer_amount = self._primer_amount*self.__volume_factor
#
#         if self._master_mix:
#             master_mix_amount = self._master_mix_amount*self.__volume_factor
#             reagent_amount = master_mix_amount + dna_amount + (2 * primer_amount)
#         else:
#             dNTPs_amount = self._dNTPs_amount*self.__volume_factor
#             buffer_amount = self._buffer_amount*self.__volume_factor
#             polymerase_amount = self._polymerase_amount*self.__volume_factor
#             reagent_amount = dNTPs_amount + buffer_amount + polymerase_amount + dna_amount + (2 * primer_amount)
#
#         water_amount = self.volume - reagent_amount
#         # If need to add less than 0.025 uL water, just add none (too small for echo to transfer)
#         if water_amount < 0.025:
#             water_amount = 0
#
#         dplate_id = 0
#         dplate_current_well = 0
#         dplate_well_range = self.destination_plate_format[1]
#
#         for sample in self.samples:
#             for rep in range(0, self.repeats):
#                 dplate = dplates[dplate_id]
#                 if not self.colony_pcr:
#                     dplate.add_content(dplate_well_range[dplate_current_well], sample[0], dna_amount)
#                 dplate.add_content(dplate_well_range[dplate_current_well], sample[1], primer_amount)
#                 dplate.add_content(dplate_well_range[dplate_current_well], sample[2], primer_amount)
#                 dplate.add_content(dplate_well_range[dplate_current_well], self.water, water_amount)
#
#                 if self._master_mix:
#                     dplate.add_content(dplate_well_range[dplate_current_well], self.master_mix, master_mix_amount)
#                 else:
#                     dplate.add_content(dplate_well_range[dplate_current_well], self.dNTPs, dNTPs_amount)
#                     dplate.add_content(dplate_well_range[dplate_current_well], self.buffer, buffer_amount)
#                     dplate.add_content(dplate_well_range[dplate_current_well], self.polymerase, polymerase_amount)
#
#                 dplate_current_well += 1
#                 # Check if the current destination plate is full, and if so move on to the next plate
#                 if dplate_current_well - 1 == len(dplate_well_range):
#                     dplate_id += 1
#                     dplate_current_well = 0
#
#         # Create protocol and generate picklists
#         Protocol = _BMS.EchoProto.Protocol(self.name)
#         Protocol.add_source_plates(self.source_plates)
#         Protocol.add_destination_plates(dplates)
#         _BMS.EchoProto.Generate_Actions(Protocol)
#         _BMS.EchoProto.Write_Picklists(Protocol,Directory)

# class Loop_Assembly: # Volume is uL, assumes parts are at 10 fmol/uL
#
#     def __init__(self,
#         Name,
#         Enzyme,
#         Source_Plates,
#         Destination_Plate_Format,
#         Destination_Well_Range = None,
#         Use_Outer_Destination_Wells = True,
#         Volume = 5,
#         Backbone_to_Part = ["1:1"],
#         Repeats = 1
#     ):
#         #####################
#         # Protocol Metadata #
#         #####################
#         self.name = Name
#         # Create an empty Echo protocol
#         self._protocol = _BMS.EchoProto.Protocol(Name)
#
#         ########################################
#         # User defined aspects of the protocol #
#         ########################################
#         self.volume = Volume # uL
#         self.ratios = Backbone_to_Part
#         self.repeats = Repeats
#         self.assemblies = []
#         self.enzyme = Enzyme
#
#         ###########
#         # Labware #
#         ###########
#         self.source_plates = Source_Plates
#         self.destination_plate_format = Destination_Plate_Format # [Plate_Layout, Wells_For_Use]
#         self.destination_well_range = Destination_Plate_Format.get_well_range(Well_Range = Destination_Well_Range, Use_Outer_Wells = Use_Outer_Destination_Wells)
#
#         ##############################################
#         # Default reagent amounts for 5 uL reactions #
#         ##############################################
#         self._enzyme_amount = 0.125
#         self._ligase_buffer_amount = 0.5
#         self._ligase_amount = 0.125
#
#         ##########################################
#         # Default DNA amounts for 5 uL reactions #
#         ##########################################
#         # For 1:1 ratio, and source concentration of 10 fmol/uL
#         self._backbone_amount = 0.25
#         self._part_amount = 0.25
#
#         #########################
#         # Default reagent names #
#         #########################
#         self.ligase_buffer = "T4 Ligase Buffer"
#         self.ligase = "T4 Ligase"
#         self.water = "Water"
#
#         self.assembly_locations = []
#
#     ###############################
#     # Function to add an assembly #
#     ###############################
#     def add_assembly(self,Backbone,Parts):
#         # If a single string is given for Parts, convert it to a list
#         ## This keeps things consistent for downstream usage,
#         ## but allows user input flexiblility when assembling a single part
#         if isinstance(Parts, str):
#             Parts = list(Parts)
#         # Add the assembly to self.assemblies in the format list[Backbone: str, Parts: list[Part: str]]
#         self.assemblies.append([Backbone,Parts])
#
#     #####################################
#     # Function to generate the picklist #
#     #####################################
#     def make_picklist(self,Directory):
#
#         ###################################################
#         # Calculate number of destination plates required #
#         ###################################################
#         # Determine final number of assemblies, and hence number of destination wells required
#         n_assemblies = (len(self.assemblies) * len(self.ratios)) * self.repeats
#
#         ################################################
#         # Create required number of destination plates #
#         ################################################
#         destination_plates = _BMS.EchoProto.Calculate_And_Create_Plates(self.destination_plate_format, n_assemblies, len(self.destination_well_range))
#
#         ######################################
#         # Calculate reagent volumes required #
#         ######################################
#         # Volume factor is the difference between the default volume (5 uL) and the user-define final volume
#         volume_factor = self.volume/5
#         # Use the volume factor to calculate the reagent volumes
#         enzyme_amount = self._enzyme_amount*volume_factor
#         ligase_buffer_amount = self._ligase_buffer_amount*volume_factor
#         ligase_amount = self._ligase_amount*volume_factor
#         # Store the total amount of reagents per reaction for later use
#         reagent_amount = enzyme_amount + ligase_buffer_amount + ligase_amount
#
#         #########################################################
#         # Add DNA, water, and reagents to each destination well #
#         #########################################################
#         # Counter to define which destination plate is in use
#         destination_plate_index = 0
#         # Counter to define which destination well is in use
#         destination_well_index = 0
#
#         # For every reaction
#         for assembly in self.assemblies:
#             for ratio in self.ratios:
#                 for rep in range(0, self.repeats):
#                     backbone_amount = (self._backbone_amount*volume_factor)*float(ratio.split(":")[0])
#                     part_amount = (self._part_amount*volume_factor)*float(ratio.split(":")[1])
#                     water_amount = self.volume - (backbone_amount + (part_amount*len(assembly[1])) + reagent_amount)
#                     # If water amount is below the minimum amount which can be transfered by the Echo, set the water amount to 0
#                     ## This is to avoid errors
#                     if water_amount < 0.025 and water_amount > 0:
#                         water_amount = 0
#
#                     # Get the current destination plate
#                     destination_plate = destination_plates[destination_plate_index]
#                     # Get the current destination well
#                     destination_well = self.destination_well_range[destination_well_index]
#
#                     # Add the reagents, water, and DNA to the destinaton plate
#                     try:
#                         destination_plate.add_content(destination_well, self.enzyme, enzyme_amount)
#                         destination_plate.add_content(destination_well, self.ligase_buffer, ligase_buffer_amount)
#                         destination_plate.add_content(destination_well, self.ligase, ligase_amount)
#                         destination_plate.add_content(destination_well, self.water, water_amount)
#                         destination_plate.add_content(destination_well, assembly[0], backbone_amount)
#                         part_string = ""
#                         for part in assembly[1]:
#                             destination_plate.add_content(destination_well, part, part_amount)
#                             part_string += part + "+"
#                     except _BMS.NegativeVolumeError:
#                         raise _BMS.NegativeVolumeError("This assembly is above the reaction volume: {}, {}".format(assembly, ratio))
#
#                     assembly_name = "{}-{}-{}".format(assembly[0],part_string[0:-1],ratio)
#                     self.assembly_locations.append([destination_plate.name, destination_well, assembly_name])
#
#                     # Iterate to the next destination well
#                     destination_well_index += 1
#                     # Check if the current destinaton plate is full
#                     if destination_well_index - 1 == len(self.destination_well_range):
#                         # If so, iterate to the first well of the next destination plate
#                         destination_plate_index += 1
#                         destination_well_index = 0
#
#         # dplate_id = 0
#         # # Counter to define which destination well is in use
#         # dplate_current_well = 0
#         # # For every reaction
#         # for assembly in self.assemblies:
#         #     for ratio in self.ratios:
#         #         for rep in range(0, self.repeats):
#         #             backbone_amount = (self._backbone_amount*volume_factor)*float(ratio.split(":")[0])
#         #             part_amount = (self._part_amount*volume_factor)*float(ratio.split(":")[1])
#         #             # Calculate amount of water to be added
#         #             water_amount = self.volume - (backbone_amount + (part_amount*len(assembly[1])) + reagent_amount)
#         #             # If the amount of water required is less than 0, that means that the reaction is above the reaction volume
#         #             ## In this case, raise an error
#         #             if water_amount < 0:
#         #                 raise ValueError("This assembly is above the reaction volume: {}, {}".format(assembly, ratio))
#         #             # If water amount is below the minimum amount which can be transfered by the Echo, set the water amount to 0
#         #             ## This is to avoid errors
#         #             if water_amount < 0.025:
#         #                 water_amount = 0
#         #
#         #             # Get the current destination plate
#         #             dplate = dplates[dplate_id]
#         #             # Get the current destination well
#         #             d_well = dplate_well_range[dplate_current_well]
#         #
#         #             # Add the reagents, water, and DNA to the destinaton plate
#         #             dplate.add_content(d_well, self.enzyme, enzyme_amount)
#         #             dplate.add_content(d_well, self.ligase_buffer, ligase_buffer_amount)
#         #             dplate.add_content(d_well, self.ligase, ligase_amount)
#         #             dplate.add_content(d_well, self.water, water_amount)
#         #             dplate.add_content(d_well, assembly[0], backbone_amount)
#         #             part_string = ""
#         #             for part in assembly[1]:
#         #                 dplate.add_content(d_well, part, part_amount)
#         #                 part_string += part + "+"
#         #
#         #             assembly_name = "{}-{}-{}".format(assembly[0],part_string[0:-1],ratio)
#         #             self.assembly_locations.append([dplate.name, d_well, assembly_name])
#         #
#         #             # Iterate to the next destination well
#         #             dplate_current_well += 1
#         #             # Check if the current destinaton plate is full
#         #             if dplate_current_well - 1 == len(dplate_well_range):
#         #                 # If so, iterate to the first well of the next destination plate
#         #                 dplate_id += 1
#         #                 dplate_current_well = 0
#
#         # self.destination_plates = dplates
#
#         ##########################################
#         # Create protocol and generate picklists #
#         ##########################################
#         # Create an empty Echo protocol
#         Protocol = _BMS.EchoProto.Protocol(self.name)
#         # Add the source and destination plates to the protocol
#         Protocol.add_source_plates(self.source_plates)
#         Protocol.add_destination_plates(destination_plates)
#         # Generate the liquid transfer actions
#         _BMS.EchoProto.Generate_Actions(Protocol)
#         # Create and write the picklists
#         _BMS.EchoProto.Write_Picklists(Protocol,Directory)
