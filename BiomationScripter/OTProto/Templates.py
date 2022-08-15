import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
# import smtplib, ssl






class DNA_fmol_Dilution(_OTProto.OTProto_Template):
    def __init__(self,
        Final_fmol,
        DNA,
        DNA_Concentration,
        DNA_Length,
        DNA_Source_Type,
        Keep_In_Current_Wells,
        Water_Source_Labware_Type,
        Water_Per_Well,
        DNA_Source_Wells = None,
        Final_Volume = None,
        Current_Volume = None,
        Destination_Labware_Type = None,
        Destination_Labware_Wells = None,
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.final_fmol = Final_fmol
        self._keep_in_current_wells = Keep_In_Current_Wells
        self._final_volume = Final_Volume

        ####################
        # Source materials #
        ####################
        ## DNA to be diluted ##
        self.dna = DNA
        self.dna_source_wells = DNA_Source_Wells
        self.dna_source_type = DNA_Source_Type
        self.dna_starting_volume = Current_Volume
        self.dna_starting_concentration = DNA_Concentration
        self.dna_length = DNA_Length
        ## Water ##
        self.water_source_labware_type = Water_Source_Labware_Type
        self.water_per_well = Water_Per_Well

        #######################
        # Destination Labware #
        #######################
        self._destination_labware_type = Destination_Labware_Type
        self._destination_labware_wells = Destination_Labware_Wells

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        #################################################
        # Calculate dilution factor for each DNA sample #
        #################################################
        dna_current_fmol = []
        dna_dilution_factor = []
        for dna_name, dna_starting_concentration, dna_length in zip(self.dna, self.dna_starting_concentration, self.dna_length):
            mass_g = dna_starting_concentration * 1e-9
            length = dna_length
            fmol = (mass_g/((length * 617.96) + 36.04)) * 1e15
            dna_current_fmol.append(fmol)
            dilution_factor = self.final_fmol/fmol
            dna_dilution_factor.append(dilution_factor)
            if dilution_factor > 1:
                raise _BMS.NegativeVolumeError("DNA sample {} is too dilute and is already below {} fmol/uL".format(dna_name, self.final_fmol))

        ####################################################################
        # Determine if DNA will be diluted in current wells or transferred #
        ####################################################################
        if self._keep_in_current_wells == True:
            # Calculate amount of water to add to each DNA sample #
            water_to_add = []
            for starting_volume, dilution_factor in zip(self.dna_starting_volume, dna_dilution_factor):
                water_to_add.append((starting_volume / dilution_factor) - starting_volume)

            # Calculate number of tips needed:
            self.tips_needed["p20"], self.tips_needed["p300"], self.tips_needed["p1000"] = _OTProto.calculate_tips_needed(self._protocol, water_to_add, new_tip = True)
            # Add required number of tip boxes to the loaded pipettes
            self.add_tip_boxes_to_pipettes()

            # Load source labware #
            DNA_labware = _OTProto.load_labware(self._protocol, self.dna_source_type, custom_labware_dir = self.custom_labware_dir, label = "DNA Source Labware")
            ## Calculate number of water aliquots required
            total_water_required = sum(water_to_add)
            aliquots_required = math.ceil(total_water_required/self.water_per_well)
            ## Load required water source labware
            water_source_labware, water_source_locations = _OTProto.calculate_and_load_labware(self._protocol, self.water_source_labware_type, aliquots_required, custom_labware_dir = self.custom_labware_dir)

            ## DNA source labware is also the destination labware in this case
            ## But get DNA locations
            DNA_Locations = []
            # If DNA source wells were not specified, then choose wells to use
            if self.dna_source_wells == None:
                if len(DNA_labware.wells_by_name()) < len(self.dna):
                    raise _BMS.BMSTemplateError("Cannot currently use two source labware.")
                self.dna_source_wells = []
                for dna, source_well in zip(self.dna, DNA_labware.wells_by_name()):
                    self.dna_source_wells.append(source_well)

            for dna_well in self.dna_source_wells:
                DNA_Locations.append(DNA_labware.wells_by_name()[dna_well])

            # Liquid handling begins #
            ## Dispense water into DNA source wells and mix
            _OTProto.dispense_from_aliquots(self._protocol, water_to_add, water_source_locations, DNA_Locations, new_tip = True, mix_after = (5,"transfer_volume"))

        else:
            # Calculate amount of water to add to each DNA sample #
            water_to_add = []
            dna_to_add = []
            for dilution_factor in dna_dilution_factor:
                final_volume = self._final_volume
                dna_volume = final_volume * dilution_factor
                water_volume = final_volume - dna_volume
                water_to_add.append(water_volume)
                dna_to_add.append(dna_volume)

            # Calculate number of tips needed:
            water_tips_needed_20uL, water_tips_needed_300uL, water_tips_needed_1000uL = _OTProto.calculate_tips_needed(self._protocol, water_to_add, new_tip = False)
            dna_tips_needed_20uL, dna_tips_needed_300uL, dna_tips_needed_1000uL = _OTProto.calculate_tips_needed(self._protocol, dna_to_add, new_tip = True)

            self.tips_needed["p20"] = water_tips_needed_20uL + dna_tips_needed_20uL
            self.tips_needed["p300"] = water_tips_needed_300uL + dna_tips_needed_300uL
            self.tips_needed["p1000"] = water_tips_needed_1000uL + dna_tips_needed_1000uL

            # Add required number of tip boxes to the loaded pipettes
            self.add_tip_boxes_to_pipettes()

            # Load source labware #
            ## Calculate number of water aliquots required
            total_water_required = sum(water_to_add)
            aliquots_required = math.ceil(total_water_required/self.water_per_well)
            ## Load required water source labware
            water_source_labware, water_source_locations = _OTProto.calculate_and_load_labware(self._protocol, self.water_source_labware_type, aliquots_required, custom_labware_dir = self.custom_labware_dir)

            ## Load DNA Source Labware and get locations
            DNA_labware = _OTProto.load_labware(self._protocol, self.dna_source_type, custom_labware_dir = self.custom_labware_dir, label = "DNA Source Labware")
            DNA_Locations = []
            # If DNA source wells were not specified, then choose wells to use
            if self.dna_source_wells == None:
                if len(DNA_labware.wells_by_name()) < len(self.dna):
                    raise _BMS.BMSTemplateError("Cannot currently use two source labware.")
                self.dna_source_wells = []
                for dna, source_well in zip(self.dna, DNA_labware.wells_by_name()):
                    self.dna_source_wells.append(source_well)

            for dna_well in self.dna_source_wells:
                DNA_Locations.append(DNA_labware.wells_by_name()[dna_well])

            # Load destination labware #
            destination_labware = _OTProto.load_labware(self._protocol, self._destination_labware_type, custom_labware_dir = self.custom_labware_dir, label = "Destination Labware")
            destination_locations = []
            for destination_well in self._destination_labware_wells:
                destination_locations.append(destination_labware.wells_by_name()[destination_well])

            if not _OTProto.get_p20 == None:
                self._protocol.pause("This protocol uses {} 20 uL tip boxes".format(_OTProto.tip_racks_needed(self.tips_needed["p20"], self.starting_tips["p20"])))
            if not _OTProto.get_p300 == None:
                self._protocol.pause("This protocol uses {} 300 uL tip boxes".format(_OTProto.tip_racks_needed(self.tips_needed["p300"], self.starting_tips["p300"])))
            if not _OTProto.get_p1000 == None:
                self._protocol.pause("This protocol uses {} 1000 uL tip boxes".format(_OTProto.tip_racks_needed(self.tips_needed["p1000"], self.starting_tips["p1000"])))

            self._protocol.pause("This protocol uses {} aliquots of {} uL water, located at {}".format(len(water_source_locations), self.water_per_well, water_source_locations))

            for dna, location, volume in zip(self.dna, DNA_Locations, dna_to_add):
                self._protocol.pause("Place DNA sample {} at {}. {} uL will be used".format(dna, location, volume))
            # Liquid handling begins #
            ## Dispense water into DNA source wells and mix
            _OTProto.dispense_from_aliquots(self._protocol, water_to_add, water_source_locations, destination_locations, new_tip = True)

            ## Add DNA to water
            _OTProto.transfer_liquids(self._protocol, dna_to_add, DNA_Locations, destination_locations, new_tip = True, mix_after = (5,"transfer_volume"))

class Heat_Shock_Transformation(_OTProto.OTProto_Template):
    def __init__(self,
        DNA_Source_Layouts,
        Competent_Cells_Source_Type,
        Transformation_Destination_Type,
        Media_Source_Type,
        DNA_Volume_Per_Transformation,
        Competent_Cell_Volume_Per_Transformation,
        Transformation_Final_Volume,
        Heat_Shock_Time,
        Heat_Shock_Temp,
        Media_Aliquot_Volume,
        Competent_Cells_Aliquot_Volume,
        Wait_Before_Shock,
        Replicates,
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.dna_per_transformation = DNA_Volume_Per_Transformation
        self.cells_per_transformation = Competent_Cell_Volume_Per_Transformation
        self.final_volume = Transformation_Final_Volume
        self.heat_shock_time = Heat_Shock_Time # seconds
        self.heat_shock_temp = Heat_Shock_Temp # celcius
        self.wait_before_shock = Wait_Before_Shock # seconds
        self.replicates = Replicates

        ####################
        # Source materials #
        ####################
        self.dna_source_layouts = DNA_Source_Layouts

        self.comp_cells_source_type = Competent_Cells_Source_Type
        self.comp_cells_aliquot_volume = Competent_Cells_Aliquot_Volume

        self.media_source_type = Media_Source_Type
        self.media_aliquot_volume = Media_Aliquot_Volume

        #######################
        # Destination Labware #
        #######################
        self.destination_type = Transformation_Destination_Type

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        self._temperature_module = "temperature module gen2"
        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        ###########################
        # Load temperature_module #
        ###########################
        temperature_module = self._protocol.load_module(self._temperature_module, 4)

        ################################
        # Create transfer volume lists #
        ################################
        Num_Transformations = sum([len(dl.get_occupied_wells()) for dl in self.dna_source_layouts]) * self.replicates

        Cell_Transfer_Volumes = [self.cells_per_transformation] * Num_Transformations
        DNA_Transfer_Volumes = [self.dna_per_transformation] * Num_Transformations
        Media_Transfer_Volumes = [self.final_volume - self.dna_per_transformation - self.cells_per_transformation] * Num_Transformations

        #########################################################################
        # Calculate the number of tips and tip racks required for this protocol #
        #########################################################################

        self.calculate_and_add_tips(Cell_Transfer_Volumes, New_Tip = False)
        self.calculate_and_add_tips(DNA_Transfer_Volumes, New_Tip = True)
        self.calculate_and_add_tips(Media_Transfer_Volumes, New_Tip = True)
        self.add_tip_boxes_to_pipettes() # Starting tip(s) are defined here as well

        #######################
        # Load Source Labware #
        #######################
        # Competent Cells
        Cell_Aliquots_Required = math.ceil(sum(Cell_Transfer_Volumes)/self.comp_cells_aliquot_volume)
        Cell_Source_Labware, Cell_Source_Locations = _OTProto.calculate_and_load_labware(self._protocol, self.comp_cells_source_type, Cell_Aliquots_Required, custom_labware_dir = self.custom_labware_dir)

        # DNA
        DNA_Source_Labware = [
            _OTProto.load_labware_from_layout(
                Protocol = self._protocol,
                Labware_Layout = dl,
                custom_labware_dir = self.custom_labware_dir
            )
            for dl in self.dna_source_layouts
        ]

        DNA_Source_Locations = []

        for layout, labware in zip(self.dna_source_layouts, DNA_Source_Labware):
            DNA_Source_Locations += _OTProto.get_locations(
                Labware = labware,
                Wells = layout.get_occupied_wells()
            )

        # Media
        Media_Aliquots_Required = math.ceil(sum(Media_Transfer_Volumes)/self.media_aliquot_volume)
        Media_Source_Labware, Media_Source_Locations = _OTProto.calculate_and_load_labware(self._protocol, self.media_source_type, Media_Aliquots_Required, custom_labware_dir = self.custom_labware_dir)

        ############################
        # Load Destination Labware #
        ############################
        Destination_Labware = _OTProto.load_labware(temperature_module, self.destination_type, custom_labware_dir = self.custom_labware_dir, label = "Destination Labware")
        Destination_Locations = Destination_Labware.wells()[:Num_Transformations]

        print("Transformation Mapping")
        for dna, destination in zip([f"{layout.name}: {layout.get_liquids_in_well(well)[0]} ({well})" for layout in self.dna_source_layouts for well in layout.get_occupied_wells()], Destination_Locations):
            print(f"{dna} -> {destination}")

        ######################
        # User Setup Prompts #
        ######################
        self.tip_racks_prompt()

        for dna_name, location in  zip([layout.get_liquids_in_well(well)[0] for layout in self.dna_source_layouts for well in layout.get_occupied_wells()], DNA_Source_Locations):
            self._protocol.pause("Place DNA Sample {} at {}".format(dna_name, location))

        self._protocol.pause("This protocol uses {} aliquots of {} uL media, located at {}".format(Media_Aliquots_Required, self.media_aliquot_volume, Media_Source_Locations))
        self._protocol.pause("This protocol uses {} aliquots of {} uL competent cells, located at {}".format(Cell_Aliquots_Required, self.comp_cells_aliquot_volume, Cell_Source_Locations))

        ##########################
        # Liquid handling begins #
        ##########################

        # Set temperature to 4C and wait until temp is reached
        temperature_module.set_temperature(4)

        # Add comp cells

        _OTProto.dispense_from_aliquots(
            self._protocol,
            Cell_Transfer_Volumes,
            Cell_Source_Locations,
            Destination_Locations,
            Min_Transfer = None,
            Calculate_Only = False,
            Dead_Volume_Proportion = 1,
            Aliquot_Volumes = self.comp_cells_aliquot_volume,
            new_tip = False,
            mix_after = None,
            mix_before = (5,"transfer_volume"),
            mix_speed_multiplier = 1.5,
            aspirate_speed_multiplier = 1,
            dispense_speed_multiplier = 1,
            blowout_speed_multiplier = 1,
            touch_tip_source = False,
            touch_tip_destination = True,
            blow_out = True,
            blowout_location = "destination well",
            move_after_dispense = "well_bottom"
        )

        # Add DNA
        _OTProto.transfer_liquids(
            self._protocol,
            DNA_Transfer_Volumes,
            DNA_Source_Locations,
            Destination_Locations,
            new_tip = True,
            mix_after = (10,"transfer_volume"),
            mix_before = None,
            mix_speed_multiplier = 2,
            aspirate_speed_multiplier = 1,
            dispense_speed_multiplier = 1,
            blowout_speed_multiplier = 1,
            touch_tip_source = False,
            touch_tip_destination = True,
            blow_out = True,
            blowout_location = "destination well",
            move_after_dispense = "well_bottom"
        )

        # Heat shock

        # Wait for a bit
        self._protocol.delay(seconds = self.wait_before_shock)
        # Set the temp to heat shock
        temperature_module.set_temperature(self.heat_shock_temp)
        # Wait for a bit
        self._protocol.delay(seconds = self.heat_shock_time)
        # Cool back to 4 - protocol won't continue until this is back at 4...
        temperature_module.set_temperature(4)

        # Add media
        # Prompt user to open LB tubes
        self._protocol.pause("Open up LB tubes")

        _OTProto.dispense_from_aliquots(
            self._protocol,
            Media_Transfer_Volumes,
            Media_Source_Locations,
            Destination_Locations,
            Min_Transfer = None,
            Calculate_Only = False,
            Dead_Volume_Proportion = 1,
            Aliquot_Volumes = self.media_aliquot_volume,
            new_tip = True,
            mix_after = None,
            mix_before = None,
            mix_speed_multiplier = 1,
            aspirate_speed_multiplier = 1,
            dispense_speed_multiplier = 1,
            blowout_speed_multiplier = 1,
            touch_tip_source = False,
            touch_tip_destination = True,
            blow_out = True,
            blowout_location = "destination well",
            move_after_dispense = None
        )

class Primer_Mixing(_OTProto.OTProto_Template):
    def __init__(self,
        DNA,
        DNA_Source_Type,
        DNA_Source_Wells,
        Primers,
        Primer_Source_Wells,
        Primer_Source_Type,
        DNA_Primer_Mixtures,
        Destination_Type,
        # Defaults for LightRun Tubes
        DNA_Volume = 5,
        Primer_Volume = 5,
        Final_Volume = 10,
        Water_Source_Type = None,
        Water_Aliquot_Volume = 0,
        DNA_Primers_Same_Source = False,
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.dna_primer_mixtures = DNA_Primer_Mixtures
        self.dna_volume = DNA_Volume
        self.primer_volume = Primer_Volume
        self.final_volume = Final_Volume

        ####################
        # Source materials #
        ####################
        self.dna = DNA
        self.primers = Primers

        self.dna_source_wells = DNA_Source_Wells
        self.primer_source_wells = Primer_Source_Wells

        self.dna_source_type = DNA_Source_Type
        self.primer_source_type = Primer_Source_Type
        self.water_source_type = Water_Source_Type

        self.water_aliquot_volume = Water_Aliquot_Volume

        self.dna_primers_same_source = DNA_Primers_Same_Source

        #######################
        # Destination Labware #
        #######################
        self.destination_type = Destination_Type

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):

        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        ################################
        # Calculate and load tip boxes #
        ################################
        # Number of tips needed is:
        # > One tip for the water total - volume = final - (DNA + Primer)
        # > One tip per DNA sample per destination
        # > One tip per primer per destination

        # Calculate and store all of the transfers which need to be performed by this protocol
        Water_Transfers = []
        DNA_Transfers = []
        Primer_Transfers = []
        for mixture in self.dna_primer_mixtures:
            dna = mixture[0]
            primers = mixture[1:]
            water_vol = self.final_volume - (self.dna_volume + len(primers) * self.primer_volume)
            DNA_Transfers.append(self.dna_volume)
            for primer in primers:
                Primer_Transfers.append(self.primer_volume)
            Water_Transfers.append(water_vol)

        # This calculates the number of each tip type needed, and adds them to the tips_needed attribute
        water_tips_needed = _OTProto.calculate_tips_needed(self._protocol, Water_Transfers, template = self, new_tip = False)
        dna_tips_needed = _OTProto.calculate_tips_needed(self._protocol, DNA_Transfers, template = self, new_tip = True)
        primer_tips_needed = _OTProto.calculate_tips_needed(self._protocol, Primer_Transfers, template = self, new_tip = True)

        # Add required number of tip boxes to the loaded pipettes
        self.add_tip_boxes_to_pipettes()

        #######################
        # Load source labware #
        #######################
        # Calculate how many water aliquots are required
        if self.water_aliquot_volume == 0:
            number_water_aliquots = 0
        else:
            number_water_aliquots = _BMS.aliquot_calculator(
                                                Volume_Required = sum(Water_Transfers),
                                                Volume_Per_Aliquot = self.water_aliquot_volume,
                                                Dead_Volume = self.water_aliquot_volume * 0.01
            )

            # Load the required number of water labware
            Water_Labware, Water_Locations = _OTProto.calculate_and_load_labware(
                                                        protocol = self._protocol,
                                                        labware_api_name = self.water_source_type,
                                                        wells_required = number_water_aliquots,
                                                        custom_labware_dir = self.custom_labware_dir
            )

        #########################################
        # Create labware layout for DNA labware #
        #########################################

        dna_layout = _BMS.Labware_Layout(
                                Name = "DNA",
                                Type = self.dna_source_type
        )
        n_dna_layout_rows, n_dna_layout_cols = _OTProto.get_labware_format(self.dna_source_type, self.custom_labware_dir)
        dna_layout.define_format(n_dna_layout_rows, n_dna_layout_cols)

        # Add content to the layout
        for dna, dna_well in zip(self.dna, self.dna_source_wells):
         dna_layout.add_content(
                        Well = dna_well,
                        Reagent = dna,
                        Volume = 30 # This refers to nothing important - should add in a calculator somewhere to let user know how much is needed
         )

        ###########################################################################################
        # Create labware layout for Primer labware (if primer and dna aren't in the same labware) #
        ###########################################################################################

        if not self.dna_primers_same_source:
            primer_layout = _BMS.Labware_Layout(
                                       Name = "Primers",
                                       Type = self.primer_source_type
            )
            n_primer_layout_rows, n_primer_layout_cols = _OTProto.get_labware_format(self.primer_source_type, self.custom_labware_dir)
            primer_layout.define_format(n_primer_layout_rows, n_primer_layout_cols)
        else:
            dna_layout.name = "DNA and Primers"
            primer_layout = dna_layout

        # Add content to the layout
        for primer, primer_well in zip(self.primers, self.primer_source_wells):
            primer_layout.add_content(
                           Well = primer_well,
                           Reagent = primer,
                           Volume = 30 # This refers to nothing important - should add in a calculator somewhere to let user know how much is needed
            )

        ###################################
        # Load labware from layout object #
        ###################################
        dna_labware = _OTProto.load_labware_from_layout(
                                Protocol = self._protocol,
                                Plate_Layout = dna_layout,
                                custom_labware_dir = self.custom_labware_dir
        )

        if not self.dna_primers_same_source:
            primer_labware = _OTProto.load_labware_from_layout(
                                    Protocol = self._protocol,
                                    Plate_Layout = primer_layout,
                                    custom_labware_dir = self.custom_labware_dir
            )
        else:
            primer_labware = dna_labware

        ############################
        # Load destination labware #
        ############################
        destination_labware, destination_locations = _OTProto.calculate_and_load_labware(
                                                       protocol = self._protocol,
                                                       labware_api_name = self.destination_type,
                                                       wells_required = len(self.dna_primer_mixtures),
                                                       custom_labware_dir = self.custom_labware_dir
        )

        ##################################
        # Start of protocol instructions #
        ##################################

        # User prompts to ensure deck is correctly set up
        if not _OTProto.get_p20 == None:
            self._protocol.pause("This protocol uses {} 20 uL tip boxes".format(_OTProto.tip_racks_needed(self.tips_needed["p20"], self.starting_tips["p20"])))
        if not _OTProto.get_p300 == None:
            self._protocol.pause("This protocol uses {} 300 uL tip boxes".format(_OTProto.tip_racks_needed(self.tips_needed["p300"], self.starting_tips["p300"])))
        if not _OTProto.get_p1000 == None:
            self._protocol.pause("This protocol uses {} 1000 uL tip boxes".format(_OTProto.tip_racks_needed(self.tips_needed["p1000"], self.starting_tips["p1000"])))

        for dna, dna_well in zip(self.dna, self.dna_source_wells):
            self._protocol.pause("Ensure DNA {} is loaded in slot {} of labware {} on slot {}".format(dna, dna_well, dna_labware.name, dna_labware.parent))

        for primer, primer_well in zip(self.primers, self.primer_source_wells):
            self._protocol.pause("Ensure Primer {} is loaded in slot {} of labware {} on slot {}".format(primer, primer_well, primer_labware.name, primer_labware.parent))

        if number_water_aliquots > 0:
            self._protocol.pause("This protocol uses {} aliquots of {} uL water, located at {}".format(len(Water_Locations), self.water_aliquot_volume, Water_Locations))

            ######################################
            # Transfer water into required wells #
            ######################################
            _OTProto.dispense_from_aliquots(
                                Protocol = self._protocol,
                                Transfer_Volumes = Water_Transfers,
                                Aliquot_Source_Locations = Water_Locations,
                                Destinations = destination_locations,
                                Aliquot_Volumes = self.water_aliquot_volume,
                                new_tip = False
            )

        ####################################
        # Transfer DNA into required wells #
        ####################################

        ## Get transfer locations for each of the DNA samples required
        dna_wells = []
        for mixture in self.dna_primer_mixtures:
            dna_name = mixture[0]
            dna_wells.append(dna_layout.get_wells_containing_liquid(dna_name)[0])

        DNA_Transfer_Source_Locations = _OTProto.get_locations(
                                                Labware = dna_labware,
                                                Wells = dna_wells
        )

        _OTProto.transfer_liquids(
                            Protocol = self._protocol,
                            Transfer_Volumes = DNA_Transfers,
                            Source_Locations = DNA_Transfer_Source_Locations,
                            Destination_Locations = destination_locations,
                            new_tip = True,
                            mix_before = (3, "transfer_volume"),
                            mix_after = (3, "transfer_volume")
        )

        ########################################
        # Transfer primers into required wells #
        ########################################

        ## Get transfer locations for each of the primers required
        primer_wells = []
        primer_destination_locations = [] # Multiple primers may go into the same destination, so need a new list to store these
        for mixture, destination_location in zip(self.dna_primer_mixtures, destination_locations):
            primers = mixture[1:]
            for primer_name in primers:
                primer_wells.append(primer_layout.get_wells_containing_liquid(primer_name)[0])
                primer_destination_locations.append(destination_location)

        Primer_Transfer_Source_Locations = _OTProto.get_locations(
                                                Labware = primer_labware,
                                                Wells = primer_wells
        )

        _OTProto.transfer_liquids(
                            Protocol = self._protocol,
                            Transfer_Volumes = Primer_Transfers,
                            Source_Locations = Primer_Transfer_Source_Locations,
                            Destination_Locations = primer_destination_locations,
                            new_tip = True,
                            mix_before = (3, "transfer_volume"),
                            mix_after = (3, "transfer_volume")
        )

        #END#

class Protocol_From_Layouts(_OTProto.OTProto_Template):
    def __init__(self,
        Source_Layouts,
        Destination_Layouts,
        Import_From_Files = False,
        **kwargs
    ):
        ########################################
        # User defined aspects of the protocol #
        ########################################
        self._import_from_files = Import_From_Files

        if self._import_from_files:
            self.source_files = Source_Layouts
            self.destination_files = Destination_Layouts
            self.source_layouts = []
            self.destination_layouts = []
        else:
            self.source_files = None
            self.destination_files = None
            self.source_layouts = Source_Layouts
            self.destination_layouts = Destination_Layouts

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        ###################################################
        # Load source labware type(s) and current content #
        ###################################################
        # If Import_From_Files is specified, import and create the layouts from file locations
        if self._import_from_files:
            for source_file in self.source_files:
                self.source_layouts.append(_BMS.Import_Plate_Layout(source_file))

        #########################################################
        # Load destination labware type(s) and intended content #
        #########################################################
        # If Import_From_Files is specified, import and create the layouts from file locations
        if self._import_from_files:
            for destination_file in self.destination_files:
                self.destination_layouts.append(_BMS.Import_Plate_Layout(destination_file))

        ###########################################
        # Create and load PlateLayouts as labware #
        ###########################################
        source_labware = []

        for source_layout in self.source_layouts:
            source_labware.append(
                _OTProto.load_labware_from_layout(
                                                    Protocol = self._protocol,
                                                    Plate_Layout = source_layout,
                                                    custom_labware_dir = self.custom_labware_dir)
            )

        destination_labware = []
        for destination_layout in self.destination_layouts:
            destination_labware.append(
                _OTProto.load_labware_from_layout(
                                                    Protocol = self._protocol,
                                                    Plate_Layout = destination_layout,
                                                    custom_labware_dir = self.custom_labware_dir)
            )

        ###########################################
        # Create a lists for the transfer actions #
        ###########################################
        transfer_volumes = []
        source_locations = []
        destination_locations = []
        # For every destination labware specified
        for current_destination_labware, destination_layout in zip(destination_labware, self.destination_layouts):
            occupied_wells = destination_layout.get_occupied_wells()
            # For every well in the destination labware which needs liquid transfered to it
            for well in occupied_wells:
                # Check which reagents are required in each destination well
                required_reagents = destination_layout.get_liquids_in_well(well)
                # For each reagent, find a source location for it
                for required_reagent in required_reagents:
                    source_material_found = False
                    reagent_volume_required = destination_layout.get_volume_of_liquid_in_well(required_reagent, well)
                    for current_source_labware, source_layout in zip(source_labware, self.source_layouts):
                        wells_with_reagent = source_layout.get_wells_containing_liquid(required_reagent)
                        if len(wells_with_reagent) == 0:
                            continue
                        else:
                            for source_well in wells_with_reagent:
                                reagent_volume_available = source_layout.get_volume_of_liquid_in_well(required_reagent, source_well)
                                if not reagent_volume_available >= reagent_volume_required:
                                    continue
                                else:
                                    source = current_source_labware.wells_by_name()[source_well]
                                    destination = current_destination_labware.wells_by_name()[well]
                                    transfer_volumes.append(reagent_volume_required)
                                    source_locations.append(source)
                                    destination_locations.append(destination)
                                    source_layout.update_volume_in_well(reagent_volume_available - reagent_volume_required, required_reagent, source_well)
                                    source_material_found = True
                                    break
                        if source_material_found:
                            break
                    if not source_material_found:
                        raise _BMS.OutOFSourceMaterial("Failed to find {} to transfer to labware {}, well {}".format(required_reagent, destination_layout.name, well))
                    else:
                        continue

        ###################################################
        # Determine number of tips and tip racks required #
        ###################################################
        # Calculate number of tips needed:
        self.tips_needed["p20"], self.tips_needed["p300"], self.tips_needed["p1000"] = _OTProto.calculate_tips_needed(self._protocol, transfer_volumes, new_tip = True)
        # Add required number of tip boxes to the loaded pipettes
        self.add_tip_boxes_to_pipettes()

        #########################
        # Begin liquid handling #
        #########################
        for slot in self._protocol.deck:
            if slot == 12:
                continue
            labware = self._protocol.deck[slot]
            if labware:
                self._protocol.pause("Place {} ({}) in slot {}".format(labware.get_name(), labware.load_name, slot))

        _OTProto.transfer_liquids(self._protocol, transfer_volumes, source_locations, destination_locations, new_tip = True, mix_before = (5,"transfer_volume"), mix_after = (5,"transfer_volume"))

class Spot_Plating(_OTProto.OTProto_Template):
    def __init__(self,
        Cells,
        Cells_Source_Wells,
        Cells_Source_Type,
        Agar_Labware_Type,
        Plating_Volumes,
        Repeats,
        Media_Source_Type = None,
        Media_Aliquot_Volume = None,
        Dilution_Factors = [1],
        Dilution_Volume = None,
        Dilution_Labware_Type = None,
        Pause_Before_Plating = True,
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.repeats = Repeats
        self.pause_before_plating = Pause_Before_Plating
        # If a single volume is given, convert it to a list
        if not type(Plating_Volumes) == list:
            Plating_Volumes = [Plating_Volumes]
        self.plating_volumes = Plating_Volumes
        self.dilution_factors = Dilution_Factors
        self.dilution_volume = Dilution_Volume

        ####################
        # Source materials #
        ####################
        self.cells = Cells
        self.cells_source_type = Cells_Source_Type
        self.cells_source_wells = Cells_Source_Wells

        self.media_source_type = Media_Source_Type
        self.media_aliquot_volume = Media_Aliquot_Volume

        #######################
        # Destination Labware #
        #######################
        self.agar_labware_type = Agar_Labware_Type
        self.dilution_labware_type = Dilution_Labware_Type

        self.mapping = {}

        #####################
        # Argument checking #
        #####################
        if not Dilution_Factors == [1]:
            if None in [Media_Source_Type, Media_Aliquot_Volume, Dilution_Factors, Dilution_Volume, Dilution_Labware_Type]:
                raise _BMS.BMSTemplateError("Media_Source_Type, Dilution_Factors, Diltuon_Volume, and Dilution_Labware_Type MUST be defined if dilution factors other than 1 are specified.")

        if Dilution_Factors == [1]:
            for dilution_argument, dilution_argument_name in zip([Media_Source_Type, Media_Aliquot_Volume, Dilution_Factors, Dilution_Volume, Dilution_Labware_Type], ["Media_Source_Type", "Media_Aliquot_Volume", "Dilution_Factors", "Dilution_Volume", "Dilution_Labware_Type"]):
                if dilution_argument:
                    warnings.warn("{} will be ignored as no dilutions are specified.".format(dilution_argument_name))
            if Pause_Before_Plating:
                warnings.warn("Will not pause before plating as there is no dilution step specified")

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        ######################
        # Load Cells Labware #
        ######################
        Cells_Source_Labware = _OTProto.load_labware(self._protocol, self.cells_source_type, custom_labware_dir = self.custom_labware_dir, label = "Cells Source Labware")
        Cells_Source_Locations = _OTProto.get_locations(
                        Labware = Cells_Source_Labware,
                        Wells = self.cells_source_wells
        )

        #####################################################
        # If dilutions need to happen, deal with that first #
        #####################################################
        # Check if dilutions are going to occur
        if not self.dilution_factors == [1]:

            ################################
            # Create transfer volume lists #
            ################################

            Cell_Volumes_Per_Dilution, Media_Volumes_Per_Dilution = _BMS.serial_dilution_volumes(self.dilution_factors, self.dilution_volume)

            # These lists will be split into lists for each cell type
            # e.g., if there is cell1 and cell2 to plate, and dilutions of 1 and 10 are specified, the transfer volume lists would be:
            # Media_Transfer_Volumes = [[cell1_media_1in1, cell1_media_1in10], [cell2_media_1in1, cell2_media_1in10]]
            # Cell_Dilution_Volumes = [[cell1_cells_1in1, cell1_cells_1in10], [cell2_cells_1in1, cell2_cells_1in10]]
            Grouped_Media_Transfer_Volumes = []
            Grouped_Cell_Dilution_Volumes = []

            for cell in self.cells:
                Grouped_Media_Transfer_Volumes.append([])
                Grouped_Cell_Dilution_Volumes.append([])
                for cell_volume, media_volume in zip(Cell_Volumes_Per_Dilution, Media_Volumes_Per_Dilution):
                    Grouped_Media_Transfer_Volumes[-1].append(media_volume)
                    Grouped_Cell_Dilution_Volumes[-1].append(cell_volume)

            # Will sometimes need the unpacked transfer volumes (i.e. as a single list, rather than nested by transformation)
            Unpacked_Media_Transfer_Volumes = [transformation[dilution_factor_index] for transformation in Grouped_Media_Transfer_Volumes for dilution_factor_index in range(0, len(transformation))]
            Unpacked_Cell_Dilution_Volumes = [transformation[dilution_factor_index] for transformation in Grouped_Cell_Dilution_Volumes for dilution_factor_index in range(0, len(transformation))]

            #########################################################################
            # Calculate the number of tips and tip racks required for this protocol #
            #########################################################################

            # Don't need a clean tip for the media
            # Unpack all media volumes to a single list
            self.calculate_and_add_tips(Unpacked_Media_Transfer_Volumes, New_Tip = False)
            # Will need a clean tip for each transvomation, but can use the same one for dilutions of each type
            for transformation_cell_volumes in Grouped_Cell_Dilution_Volumes:
                self.calculate_and_add_tips(transformation_cell_volumes, New_Tip = False)
            #######################
            # Load Source Labware #
            #######################
            # Media
            Media_Aliquots_Required = math.ceil(sum(Unpacked_Media_Transfer_Volumes)/self.media_aliquot_volume)
            Media_Source_Labware, Media_Source_Locations = _OTProto.calculate_and_load_labware(self._protocol, self.media_source_type, Media_Aliquots_Required, custom_labware_dir = self.custom_labware_dir)

            ############################
            # Load Destination Labware #
            ############################
            # Need to calculate no. labware to load

            Dilution_Labware, Dilution_Locations = _OTProto.calculate_and_load_labware(
                                self._protocol,
                                self.dilution_labware_type,
                                len(Unpacked_Cell_Dilution_Volumes),
                                custom_labware_dir = self.custom_labware_dir,
                                label = "Dilution Labware"
            )

        # Next deal with everything which is needed for after the dilution stage
        ###############################
        # Create transfer volume list #
        ###############################

        # This is also created nested like the serial dilution transfer volumes
        Grouped_Plating_Transfer_Volumes = []
        Plating_Labels = []
        for transformation in self.cells:
            Grouped_Plating_Transfer_Volumes.append([])
            for dilution in self.dilution_factors:
                for plating_volume in self.plating_volumes:
                    for repeat in range(1, self.repeats + 1):
                        Grouped_Plating_Transfer_Volumes[-1].append(plating_volume)
                        Plating_Labels.append("Cells({}) - Dilution({}) - Plating Volume({}) - Repeat({})".format(transformation, dilution, plating_volume, repeat))

        # Also create the unpacked transfer list
        Unpacked_Plating_Transfer_Volumes = [transformation[spot_index] for transformation in Grouped_Plating_Transfer_Volumes for spot_index in range(0, len(transformation))]

        #########################################################################
        # Calculate the number of tips and tip racks required for this protocol #
        #########################################################################
        # One tip for each transformation
        for transformation_spot_plating_volumes in Grouped_Plating_Transfer_Volumes:
            self.calculate_and_add_tips(transformation_spot_plating_volumes, New_Tip = False)
        #######################
        # Load Source Labware #
        #######################
        # The source for plating onto agar is different depending on whether or not dilutions will be used
        if not self.dilution_factors == [1]:
            Plating_Source_Labware = Dilution_Labware
            Plating_Source_Locations = Dilution_Locations
        else:
            Plating_Source_Labware = Cells_Source_Labware
            Plating_Source_Locations = Cells_Source_Locations

        ############################
        # Load Destination Labware #
        ############################
        # Load as many agar labware as needed and store the locations of everything
        Agar_Labware, Agar_Locations = _OTProto.calculate_and_load_labware(
                                    self._protocol,
                                    self.agar_labware_type,
                                    len(Unpacked_Plating_Transfer_Volumes),
                                    custom_labware_dir = self.custom_labware_dir
        )


        ######################
        # User Setup Prompts #
        ######################
        # Print a list of locations and labels for mapping back

        for location, label in zip(Agar_Locations, Plating_Labels):
            self.mapping[label] = location
            # print(location, label)


        self.add_tip_boxes_to_pipettes() # Starting tip(s) are defined here as well
        self.tip_racks_prompt()

        for cell_name, location in  zip(self.cells, Cells_Source_Locations):
            self._protocol.pause("Ensure cell type {} is at {}".format(cell_name, location))

        if not self.dilution_factors == [1]:
            self._protocol.pause("This protocol uses {} aliquots of {} uL media, located at {}".format(Media_Aliquots_Required, self.media_aliquot_volume, Media_Source_Locations))
            self._protocol.pause("This protocol uses {} dilution labware: {}".format(len(Dilution_Labware), ["{} on position {}".format(l.load_name, l.parent) for l in Dilution_Labware]))

        self._protocol.pause("This protocol uses {} agar plate(s): {}".format(len(Agar_Labware), ["{} on position {}".format(l.load_name, l.parent) for l in Agar_Labware]))

        ##########################
        # Liquid handling begins #
        ##########################

        # Perform serial dilutions if required


        if not self.dilution_factors == [1]:
            # Add LB to the required wells of the dilution labware
            _OTProto.dispense_from_aliquots(
                                Protocol = self._protocol,
                                Transfer_Volumes = Unpacked_Media_Transfer_Volumes,
                                Aliquot_Source_Locations = Media_Source_Locations,
                                Destinations = Dilution_Locations,
                                Aliquot_Volumes = self.media_aliquot_volume,
                                Min_Transfer = None,
                                Calculate_Only = False,
                                Dead_Volume_Proportion = 1,
                                new_tip = False,
                                mix_after = None,
                                mix_before = None,
                                mix_speed_multiplier = 1.5,
                                aspirate_speed_multiplier = 1.5,
                                dispense_speed_multiplier = 1.5,
                                blowout_speed_multiplier = 1.5,
                                touch_tip_source = False,
                                touch_tip_destination = True,
                                blow_out = True,
                                blowout_location = "destination well",
                                move_after_dispense = "well_bottom"
            )

            # Add cells and perform serial dilutions
            Cell_Source_Locations = _OTProto.get_locations(
                                                    Labware = Cells_Source_Labware,
                                                    Wells = self.cells_source_wells
            )

            # Group dilution destination locations based on cell type
            Grouped_Dilution_Destination_Locations = [Dilution_Locations[len(self.dilution_factors) * i : len(self.dilution_factors) + len(self.dilution_factors)*i] for i in range(0, len(self.cells))]

            for cell_dilution_volumes, cell_source_location, dilution_destinations in zip(Grouped_Cell_Dilution_Volumes, Cell_Source_Locations, Grouped_Dilution_Destination_Locations):
                Serial_Source_Locations = [cell_source_location] + dilution_destinations[:-1]
                _OTProto.transfer_liquids(
                                Protocol = self._protocol,
                                Transfer_Volumes = cell_dilution_volumes,
                                Source_Locations = Serial_Source_Locations,
                                Destination_Locations = dilution_destinations,
                                new_tip = False,
                                mix_after = (10,"transfer_volume"),
                                mix_before = None,
                                mix_speed_multiplier = 2.5,
                                aspirate_speed_multiplier = 1,
                                dispense_speed_multiplier = 2,
                                blowout_speed_multiplier = 1,
                                touch_tip_source = False,
                                touch_tip_destination = True,
                                blow_out = True,
                                blowout_location = "destination well",
                                move_after_dispense = "well_bottom"
                )


        # Plate cells (from either the cell source plate or the dilution plate)

        # Group plating destination locations based on cell type
        Spots_Per_Cell_Type = len(Grouped_Plating_Transfer_Volumes[0])
        Grouped_Agar_Locations = [Agar_Locations[Spots_Per_Cell_Type * i : Spots_Per_Cell_Type + Spots_Per_Cell_Type*i] for i in range(0, len(self.cells))]

        Grouped_Plating_Source_Locations = [Plating_Source_Locations[int(Spots_Per_Cell_Type/(self.repeats + len(self.plating_volumes))) * i : int(Spots_Per_Cell_Type/(self.repeats + len(self.plating_volumes))) + int(Spots_Per_Cell_Type/(self.repeats + len(self.plating_volumes)))*i] for i in range(0, len(self.cells))]

        for destination_locations, volumes, name, unique_source_locations in zip(Grouped_Agar_Locations, Grouped_Plating_Transfer_Volumes, self.cells, Grouped_Plating_Source_Locations):

            source_locations = []
            for location in unique_source_locations:
                for transfers_per_source in range(0, self.repeats * len(self.plating_volumes)):
                    source_locations.append(location)

            _OTProto.transfer_liquids(
                                self._protocol,
                                volumes,
                                source_locations,
                                destination_locations,
                                new_tip = False,
                                mix_after = None,
                                mix_before = None,
                                mix_speed_multiplier = 1,
                                aspirate_speed_multiplier = 1.5,
                                dispense_speed_multiplier = 0.8,
                                blowout_speed_multiplier = 0.8,
                                touch_tip_source = False,
                                touch_tip_destination = False,
                                blow_out = True,
                                blowout_location = "destination well",
                                move_after_dispense = "well_bottom"
            )


        # for plating_volumes, cell_source_locations, agar_destinations in zip(Grouped_Plating_Transfer_Volumes, Grouped_Plating_Source_Locations, Grouped_Agar_Locations):
        #
        #     _OTProto.transfer_liquids(
        #                     Protocol = self._protocol,
        #                     Transfer_Volumes = plating_volumes,
        #                     Source_Locations = cell_source_locations,
        #                     Destination_Locations = agar_destinations,
        #                     new_tip = False,
        #                     blow_out = True,
        #                     blowout_location = "destination well"
        #     )

class Calibrant:
    def __init__(self, Name, Stock_Conc, Initial_Conc, Solvent):
        self.name = Name
        self.stock_conc = Stock_Conc
        self.initial_conc = Initial_Conc
        self.solvent = Solvent

class Standard_iGEM_Calibration(_OTProto.OTProto_Template):
    # Always do microspheres
    # Any amount of other calibrants
    def __init__(self,
        Calibrants,
        Calibrants_Stock_Concs,
        Calibrants_Initial_Concs,
        Calibrants_Solvents,
        Calibrant_Aliquot_Volumes,
        Solvent_Aliquot_Volumes,
        Volume_Per_Well,
        Repeats,
        Calibrant_Labware_Type,
        Solvent_Labware_Type,
        Destination_Labware_Type,
        Trash_Labware_Type,
        Solvent_Mix_Before = None,
        Solvent_Mix_After = None,
        Solvent_Source_Touch_Tip = True,
        Solvent_Destination_Touch_Tip = True,
        Solvent_Move_After_Dispense = "well_bottom",
        Solvent_Blowout = "destination well",
        First_Dilution_Mix_Before = (10, "transfer_volume"),
        First_Dilution_Mix_After = (10, "transfer_volume"),
        First_Dilution_Source_Touch_Tip = True,
        First_Dilution_Destination_Touch_Tip = True,
        First_Dilution_Move_After_Dispense = False,
        First_Dilution_Blowout = "destination well",
        Dilution_Mix_Before = (10, "transfer_volume"),
        Dilution_Mix_After = (10, "transfer_volume"),
        Dilution_Source_Touch_Tip = True,
        Dilution_Destination_Touch_Tip = True,
        Dilution_Move_After_Dispense = False,
        Dilution_Blowout = "destination well",
        Mix_Speed_Multipler = 2,
        Aspirate_Speed_Multipler = 1,
        Dispense_Speed_Multipler = 1,
        Blowout_Speed_Multiplier = 1,
        Dead_Volume_Proportion = 0.95,
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.calibrant_names = set(Calibrants)
        self.solvent_names = set(Calibrants_Solvents)

        self.calibrants = {}
        for name, stock, initial, solvent in zip(Calibrants, Calibrants_Stock_Concs, Calibrants_Initial_Concs, Calibrants_Solvents):
            self.calibrants[name] = Calibrant(name, stock, initial, solvent)

        self.calibrant_aliquot_volumes = Calibrant_Aliquot_Volumes
        self.solvent_aliquot_volumes = Solvent_Aliquot_Volumes
        self.final_volume = Volume_Per_Well
        self.repeats = Repeats

        ##############################
        # Liquid Handling Parameters #
        ##############################
        self.solvent_mix_before = Solvent_Mix_Before
        self.solvent_mix_after = Solvent_Mix_After
        self.solvent_source_touch_tip = Solvent_Source_Touch_Tip
        self.solvent_destination_touch_tip = Solvent_Destination_Touch_Tip
        self.solvent_move_after_dispense = Solvent_Move_After_Dispense
        if Solvent_Blowout:
            self.solvent_blowout_location = Solvent_Blowout
            self.solvent_blowout = True
        else:
            self.solvent_blowout_location = None
            self.solvent_blowout = False
        self.first_dilution_mix_before = First_Dilution_Mix_Before
        self.first_dilution_mix_after = First_Dilution_Mix_After
        self.first_dilution_source_touch_tip = First_Dilution_Source_Touch_Tip
        self.first_dilution_destination_touch_tip = First_Dilution_Destination_Touch_Tip
        self.first_dilution_move_after_dispense = First_Dilution_Move_After_Dispense
        if First_Dilution_Blowout:
            self.first_dilution_blowout_location = First_Dilution_Blowout
            self.first_dilution_blowout = True
        else:
            self.first_dilution_blowout_location = None
            self.first_dilution_blowout = False
        self.dilution_mix_before = Dilution_Mix_Before
        self.dilution_mix_after = Dilution_Mix_After
        self.dilution_source_touch_tip = Dilution_Source_Touch_Tip
        self.dilution_destination_touch_tip = Dilution_Destination_Touch_Tip
        self.dilution_move_after_dispense = Dilution_Move_After_Dispense
        if Dilution_Blowout:
            self.dilution_blowout_location = Dilution_Blowout
            self.dilution_blowout = True
        else:
            self.dilution_blowout_location = None
            self.dilution_blowout = False
        self.mix_speed_multiplier = Mix_Speed_Multipler
        self.aspirate_speed_multiplier = Aspirate_Speed_Multipler
        self.dispense_speed_multiplier = Dispense_Speed_Multipler
        self.blowout_speed_multiplier = Blowout_Speed_Multiplier
        self.dead_volume_proportion = Dead_Volume_Proportion

        ###########
        # Labware #
        ###########
        self.calibrant_type = Calibrant_Labware_Type
        self.solvent_type = Solvent_Labware_Type
        self.destination_type = Destination_Labware_Type
        self.trash_type = Trash_Labware_Type

        ######################
        # Default Parameters #
        ######################
        self._serial_dilution = 0.5
        self._number_of_dilutions = 10 # Does not include undiluted and 0% samples
        self._dilution_factors = []

        previous_dilution = 1
        for dilution_index in range(0, self._number_of_dilutions):
            self._dilution_factors.append(previous_dilution * self._serial_dilution)
            previous_dilution = self._dilution_factors[-1]

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        self.destination_layouts = []
        self.source_layouts = []

        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        ##############################
        # Destination Labware Layout #
        ##############################

        # Determine number of destination plates required
        Number_Of_Wells_Needed = (len(self.calibrants.keys()) * 12) * self.repeats
        Number_Of_Destination_Labware_Needed = math.ceil(Number_Of_Wells_Needed / (_OTProto.get_labware_format(self.destination_type, self.custom_labware_dir)[0] * _OTProto.get_labware_format(self.destination_type, self.custom_labware_dir)[1]))

        # Create the required number of destination labware layouts

        for i in range(0, Number_Of_Destination_Labware_Needed):
            destination_labware = _BMS.Labware_Layout("Destination {}".format(i+1), self.destination_type)
            n_rows, n_cols = _OTProto.get_labware_format(self.destination_type, self.custom_labware_dir)
            destination_labware.define_format(n_rows, n_cols)
            destination_labware.set_available_wells()
            self.destination_layouts.append(destination_labware)

        # Populate the destination layouts - initial additions only - not what is in the plate after serial dilutions occur
        ## Serial dilutions are identified via the well labels

        d_plate_id = 0
        for calibrant in self.calibrants.keys():
            calibrant_obj = self.calibrants[calibrant]
            for rep in range(0, self.repeats):
                if not self.destination_layouts[d_plate_id].get_next_empty_well():
                    d_plate_id += 1

                # Add calibrant to first well - dilute if needed
                first_well = self.destination_layouts[d_plate_id].get_next_empty_well()
                vol = self.final_volume * 2
                initial_dilution_factor = calibrant_obj.initial_conc/calibrant_obj.stock_conc
                self.destination_layouts[d_plate_id].add_content(
                    Well = first_well,
                    Reagent = calibrant,
                    Volume = vol * initial_dilution_factor
                )

                if not initial_dilution_factor == 1:
                    self.destination_layouts[d_plate_id].add_content(
                        Well = first_well,
                        Reagent = calibrant_obj.solvent,
                        Volume = vol - vol * initial_dilution_factor
                    )

                self.destination_layouts[d_plate_id].add_well_label(
                    Well = first_well,
                    Label = "{} - {} - ({})".format(calibrant, 1, rep)
                )

                # Add dilutions to other wells
                current_dilution_factor = 1
                previous_dilution_factor = 1
                for dilution_id in range(0, self._number_of_dilutions):
                    previous_dilution_factor = current_dilution_factor
                    current_dilution_factor *= self._serial_dilution

                    if not self.destination_layouts[d_plate_id].get_next_empty_well():
                        d_plate_id += 1

                    well = self.destination_layouts[d_plate_id].get_next_empty_well()


                    self.destination_layouts[d_plate_id].add_content(
                        Well = well,
                        Reagent = calibrant_obj.solvent,
                        Volume = self.final_volume
                    )

                    self.destination_layouts[d_plate_id].add_well_label(
                        Well = well,
                        Label = "{} - {} - ({})".format(calibrant, current_dilution_factor, rep)
                    )

                # Add undiluted sample
                if not self.destination_layouts[d_plate_id].get_next_empty_well():
                    d_plate_id += 1

                well = self.destination_layouts[d_plate_id].get_next_empty_well()


                self.destination_layouts[d_plate_id].add_content(
                    Well = well,
                    Reagent = calibrant_obj.solvent,
                    Volume = self.final_volume
                )

                self.destination_layouts[d_plate_id].add_well_label(
                    Well = well,
                    Label = "{} - {} - ({})".format(calibrant, 0, rep)
                )

        ##########################
        # Prepare source labware #
        ##########################

        # Calculate total volume of all source material required
        Source_Material_Volumes = {} # dict of total source material required
        for layout in self.destination_layouts:
            for occupied_well in layout.get_occupied_wells():
                for reagent in layout.get_liquids_in_well(occupied_well):
                    # Check if the source material is already in the dictionary
                    if reagent in Source_Material_Volumes.keys():
                        # Add to the total volume
                        Source_Material_Volumes[reagent] += layout.get_volume_of_liquid_in_well(reagent, occupied_well)
                    else:
                        # create the entry if it doesn't already exist
                        Source_Material_Volumes[reagent] = layout.get_volume_of_liquid_in_well(reagent, occupied_well)

        # Then, figure out how many aliquots of each reagent are required
        Source_Material_Aliquot_Vols = {} # dict for the total volume of aliquots for each source material
        Source_Material_Aliquot_Nums = {} # dict for the number of aliquots needed for each source material

        for reagent in Source_Material_Volumes.keys():
            if reagent in self.calibrant_names:
                aliquot_vol = self.calibrant_aliquot_volumes
            elif reagent in self.solvent_names:
                aliquot_vol = self.solvent_aliquot_volumes

            Source_Material_Aliquot_Vols[reagent] = aliquot_vol * self.dead_volume_proportion
            Source_Material_Aliquot_Nums[reagent] = math.ceil(Source_Material_Volumes[reagent] / Source_Material_Aliquot_Vols[reagent])

        # Use this info to set up the source layouts
        ## Will merge source material into the same labware if the type is the same
        ## e.g. if both solvents and calibrants have types of 1.5 mL tube racks, then use one tube rack for both, rather than one each
        for source_material in Source_Material_Aliquot_Nums.keys():
            # Get the material type for the current source material
            if source_material in self.calibrant_names:
                labware_type = self.calibrant_type
            elif source_material in self.solvent_names:
                labware_type = self.solvent_type

            # Try to find a source layout with empty wells which matches the labware type of the current source material
            ## Uses the first labware with any empty wells
            source_layouts = [layout for layout in self.source_layouts if layout.type == labware_type and not len(layout.empty_wells) == 0]
            # Check if a source layout was found
            if source_layouts == []:
                # If there were none, then create the layout
                source_layout_name = "Source_Labware_{}_{}".format(labware_type, len([layout for layout in self.source_layouts if layout.type == labware_type]))
                source_layout_type = labware_type
                source_layout = _BMS.Labware_Layout(source_layout_name, source_layout_type)
                source_rows, source_cols = _OTProto.get_labware_format(
                    source_layout.type,
                    self.custom_labware_dir
                )
                source_layout.define_format(source_rows, source_cols)
                source_layout.set_available_wells()
                self.source_layouts.append(source_layout)
                pass
            else:
                # select first appropriate source layout
                source_layout = source_layouts[0]

            # Add the aliquots to the layout
            for aliquot_index in range(0, Source_Material_Aliquot_Nums[source_material]):

                # Check that the next empty well exists
                if source_layout.get_next_empty_well():
                    pass
                else:
                    # Otherwise, create a new source layout and select that as the current source layout
                    source_layout_name = "Source_Labware_{}_{}".format(labware_type, len([layout for layout in self.source_layouts if layout.type == labware_type]))
                    source_layout_type = self.source_labware_types[source_material_type]
                    source_layout = _BMS.Labware_Layout(source_layout_name, source_layout_type)
                    source_rows, source_cols = _OTProto.get_labware_format(
                        source_layout.type,
                        self.custom_labware_dir
                    )
                    source_layout.define_format(source_rows, source_cols)
                    source_layout.set_available_wells()
                    self.source_layouts.append(source_layout)


                # Add to the layout
                source_layout.add_content(
                    Well = source_layout.get_next_empty_well(),
                    Reagent = source_material,
                    Volume = Source_Material_Aliquot_Vols[source_material]
                )

        # Make the trash layout
        trash_layout_name = "Liquid Trash"
        trash_layout_type = self.trash_type
        Trash_Layout = _BMS.Labware_Layout(trash_layout_name, trash_layout_type)
        trash_rows, trash_cols = _OTProto.get_labware_format(
            Trash_Layout.type,
            self.custom_labware_dir
        )
        Trash_Layout.define_format(trash_rows, trash_cols)
        Trash_Layout.set_available_wells(Well_Range = "A1:A1")
        Trash_Layout.add_well_label("A1", "Trash")

        # Add to end of destination layouts
        self.destination_layouts.append(Trash_Layout)

        ################
        # Load Labware #
        ################
        Source_Labware = []
        Destination_Labware = []

        for layout_list, labware_list in zip([self.source_layouts, self.destination_layouts], [Source_Labware, Destination_Labware]):
            for layout in layout_list:
                labware_list.append(
                    _OTProto.load_labware_from_layout(
                        Protocol = self._protocol,
                        Plate_Layout = layout,
                        custom_labware_dir = self.custom_labware_dir
                    )
                )

        #########################
        # Create transfer lists #
        #########################
        # Initial Transfer (solvents)
        Solvent_Transfer_List = {}

        for solvent_name in self.solvent_names:
            Solvent_Transfer_List[solvent_name] = [[], []] # volumes, destination locations
            d_index = 0
            for destination_layout in self.destination_layouts:
                for well in destination_layout.get_occupied_wells():
                    solvent = [liquid for liquid in destination_layout.get_liquids_in_well(well) if liquid == solvent_name]
                    if len(solvent) == 1:
                        transfer_volume = destination_layout.get_volume_of_liquid_in_well(solvent_name, well)
                        Solvent_Transfer_List[solvent_name][0].append(transfer_volume)
                        Solvent_Transfer_List[solvent_name][1].append(_OTProto.get_locations(Destination_Labware[d_index], well)[0])

                d_index += 1

        # Adding to the 'undiluted' calibrant wells
        Calibrant_Transfer_List = {}

        for calibrant_name in self.calibrant_names:
            Calibrant_Transfer_List[calibrant_name] = [[], [], []] # volumes, destination_layout_index, destination_well
            d_index = 0
            for destination_layout in self.destination_layouts:
                for well in destination_layout.get_occupied_wells():
                    calibrant = [liquid for liquid in destination_layout.get_liquids_in_well(well) if liquid == calibrant_name]
                    for c in calibrant:
                        transfer_volume = destination_layout.get_volume_of_liquid_in_well(calibrant_name, well)
                        Calibrant_Transfer_List[calibrant_name][0].append(transfer_volume)
                        Calibrant_Transfer_List[calibrant_name][1].append(_OTProto.get_locations(Destination_Labware[d_index], well)[0])

                d_index += 1

        Dilution_Transfer_List = {}
        Waste_Transfer_List = {}

        # Calculate the serial dilution transfer volume
        transfer_volume = (self._serial_dilution * self.final_volume) / (1 - self._serial_dilution)

        # return(None)



        for calibrant_name in self.calibrant_names:
            Dilution_Transfer_List[calibrant_name] = [[], [], []] # volumes, source_locations, destination_locations
            Waste_Transfer_List[calibrant_name] = [[], [], []] # volumes, source_locations, destination_locations
            for rep in range(0, self.repeats):


                # Get destination plate index and well of undiluted calibrant
                source_plate_index = [dest_index for dest_index in range(0, len(self.destination_layouts) - 1) if self.destination_layouts[dest_index].get_well_location_by_label("{} - {} - ({})".format(calibrant_name, 1, rep))][0]
                source_well = [self.destination_layouts[dest_index].get_well_location_by_label("{} - {} - ({})".format(calibrant_name, 1, rep)) for dest_index in range(0, len(self.destination_layouts) - 1) if self.destination_layouts[dest_index].get_well_location_by_label("{} - {} - ({})".format(calibrant_name, 1, rep))][0]

                for dilution in self._dilution_factors:
                    # Get destination plate index and well of current dilution
                    dest_plate_index = [dest_index for dest_index in range(0, len(self.destination_layouts) - 1) if self.destination_layouts[dest_index].get_well_location_by_label("{} - {} - ({})".format(calibrant_name, dilution, rep))][0]
                    dest_well = [self.destination_layouts[dest_index].get_well_location_by_label("{} - {} - ({})".format(calibrant_name, dilution, rep)) for dest_index in range(0, len(self.destination_layouts) - 1) if self.destination_layouts[dest_index].get_well_location_by_label("{} - {} - ({})".format(calibrant_name, dilution, rep))][0]


                    Dilution_Transfer_List[calibrant_name][0].append(transfer_volume)
                    Dilution_Transfer_List[calibrant_name][1].append(_OTProto.get_locations(Destination_Labware[source_plate_index], source_well)[0])
                    Dilution_Transfer_List[calibrant_name][2].append(_OTProto.get_locations(Destination_Labware[dest_plate_index], dest_well)[0])


                    # Prepare for next dilution
                    source_plate_index = dest_plate_index
                    source_well = dest_well

                # Add a final transfer to waste
                Waste_Transfer_List[calibrant_name][0].append(transfer_volume)
                Waste_Transfer_List[calibrant_name][1].append(_OTProto.get_locations(Destination_Labware[source_plate_index], source_well)[0])
                Waste_Transfer_List[calibrant_name][2].append(_OTProto.get_locations(Destination_Labware[-1], "A1")[0])


        # Calculate number of tips and tipboxes needed
        for solvent in self.solvent_names:
            self.calculate_and_add_tips(Solvent_Transfer_List[solvent][0], New_Tip = False)

        for calibrant in self.calibrant_names:
            self.calculate_and_add_tips(Calibrant_Transfer_List[calibrant][0], New_Tip = False)
            self.calculate_and_add_tips(Dilution_Transfer_List[calibrant][0], New_Tip = False)
            self.calculate_and_add_tips(Waste_Transfer_List[calibrant][0], New_Tip = True)

        self.add_tip_boxes_to_pipettes()

        ######################
        # User Setup Prompts #
        ######################
        self.tip_racks_prompt()

        print("\n\033[1mNumber Of Tips Used:" + "\033[0m")
        for pipette_type in self.tips_needed:
            if self.tips_needed[pipette_type] > 0:
                print("{}: {}".format(self.tip_types[pipette_type], self.tips_needed[pipette_type]))


        print("\n\033[1mDeck Setup:" + "\033[0m")
        for dpos in self._protocol.deck:
            if dpos == 12:
                print("Slot {}: {}".format(dpos, self._protocol.deck[dpos]))
                break
            if self._protocol.deck[dpos]:
                print("Slot {}: {}".format(dpos, self._protocol.deck[dpos].get_name()))
            else:
                print("Slot {}: Empty".format(dpos))

        for source_layout, source_labware in zip(self.source_layouts, Source_Labware):
            for well in source_layout.get_occupied_wells():
                content = source_layout.get_liquids_in_well(well)[0]
                volume = source_layout.get_volume_of_liquid_in_well(content, well)
                print("Place {} uL of {} at {}".format(volume/self.dead_volume_proportion, content, source_labware.wells_by_name()[well]))


        ##########################
        # Liquid handling begins #
        ##########################

        # Add solvents to destination plates

        for solvent in self.solvent_names:
            # Get solvent aliquot location
            Solvent_Aliquot_Layout_Positions = []
            for source_index in range(0, len(self.source_layouts)):
                source_wells = self.source_layouts[source_index].get_wells_containing_liquid(solvent)
                for well in source_wells:
                    Solvent_Aliquot_Layout_Positions.append([source_index, well])

            Solvent_Locations = [_OTProto.get_locations(Source_Labware[pos[0]], pos[1])[0] for pos in Solvent_Aliquot_Layout_Positions]


            _OTProto.dispense_from_aliquots(
                Protocol = self._protocol,
                Transfer_Volumes = Solvent_Transfer_List[solvent][0],
                Aliquot_Source_Locations = Solvent_Locations,
                Destinations = Solvent_Transfer_List[solvent][1],
                Aliquot_Volumes = self.solvent_aliquot_volumes,
                Min_Transfer = 2,
                Calculate_Only = False,
                Dead_Volume_Proportion = 0.95,
                new_tip = False,
                mix_after = self.solvent_mix_after,
                mix_before = self.solvent_mix_before,
                mix_speed_multiplier = self.mix_speed_multiplier,
                aspirate_speed_multiplier = self.aspirate_speed_multiplier,
                dispense_speed_multiplier = self.dispense_speed_multiplier,
                blowout_speed_multiplier = self.blowout_speed_multiplier,
                touch_tip_source = self.solvent_source_touch_tip,
                touch_tip_destination = self.solvent_destination_touch_tip,
                blow_out = self.solvent_blowout,
                blowout_location = self.solvent_blowout_location,
                move_after_dispense = self.solvent_move_after_dispense
            )

        # Add calibrants to the first well(s)

        for calibrant in self.calibrant_names:
            # Get calibrant source locations
            Calibrant_Aliquot_Layout_Positions = []
            for source_index in range(0, len(self.source_layouts)):
                source_wells = self.source_layouts[source_index].get_wells_containing_liquid(calibrant)
                for well in source_wells:
                    Calibrant_Aliquot_Layout_Positions.append([source_index, well])

            Calibrant_Locations = [_OTProto.get_locations(Source_Labware[pos[0]], pos[1])[0] for pos in Calibrant_Aliquot_Layout_Positions]

            _OTProto.dispense_from_aliquots(
                Protocol = self._protocol,
                Transfer_Volumes = Calibrant_Transfer_List[calibrant][0],
                Aliquot_Source_Locations = Calibrant_Locations,
                Destinations = Calibrant_Transfer_List[calibrant][1],
                Aliquot_Volumes = self.calibrant_aliquot_volumes,
                Min_Transfer = 2,
                Calculate_Only = False,
                Dead_Volume_Proportion = 0.95,
                new_tip = False,
                mix_after = self.first_dilution_mix_after,
                mix_before = self.first_dilution_mix_before,
                mix_speed_multiplier = self.mix_speed_multiplier,
                aspirate_speed_multiplier = self.aspirate_speed_multiplier,
                dispense_speed_multiplier = self.dispense_speed_multiplier,
                blowout_speed_multiplier = self.blowout_speed_multiplier,
                touch_tip_source = self.first_dilution_source_touch_tip,
                touch_tip_destination = self.first_dilution_destination_touch_tip,
                blow_out = self.first_dilution_blowout,
                blowout_location = self.first_dilution_blowout_location,
                move_after_dispense = self.first_dilution_move_after_dispense
            )

        # Perform the serial dilutions
        for calibrant in self.calibrant_names:

            _OTProto.transfer_liquids(
                Protocol = self._protocol,
                Transfer_Volumes = Dilution_Transfer_List[calibrant][0],
                Source_Locations = Dilution_Transfer_List[calibrant][1],
                Destination_Locations = Dilution_Transfer_List[calibrant][2],
                new_tip = False,
                mix_after = self.dilution_mix_after,
                mix_before = self.dilution_mix_before,
                mix_speed_multiplier = self.mix_speed_multiplier,
                aspirate_speed_multiplier = self.aspirate_speed_multiplier,
                dispense_speed_multiplier = self.dispense_speed_multiplier,
                blowout_speed_multiplier = self.blowout_speed_multiplier,
                touch_tip_source = self.dilution_source_touch_tip,
                touch_tip_destination = self.dilution_destination_touch_tip,
                blow_out = self.dilution_blowout,
                blowout_location = self.dilution_blowout_location,
                move_after_dispense = self.dilution_move_after_dispense
            )

        # Remove excess from final dilution
        for calibrant in self.calibrant_names:

            _OTProto.transfer_liquids(
                Protocol = self._protocol,
                Transfer_Volumes = Waste_Transfer_List[calibrant][0],
                Source_Locations = Waste_Transfer_List[calibrant][1],
                Destination_Locations = Waste_Transfer_List[calibrant][2],
                new_tip = True,
                mix_after = False,
                mix_before = self.dilution_mix_before,
                mix_speed_multiplier = self.mix_speed_multiplier,
                aspirate_speed_multiplier = self.aspirate_speed_multiplier,
                dispense_speed_multiplier = self.dispense_speed_multiplier,
                blowout_speed_multiplier = self.blowout_speed_multiplier,
                touch_tip_source = self.dilution_source_touch_tip,
                touch_tip_destination = False,
                blow_out = self.dilution_blowout,
                blowout_location = self.dilution_blowout_location,
                move_after_dispense = None
            )









##############
# Incomplete #
##############

class Design_Of_Experiments(_OTProto.OTProto_Template):
    def __init__(self,
        DoE_File,
        Source_Materials,
        Destination_Content,
        Labware_APIs,
        Replicates_Per_Run = 1,
        Intermediates = {},
        Batch_Info = [None, None],
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.doe_file = DoE_File
        self.batch_factor = Batch_Info[0]
        self.batch_value = Batch_Info[1]
        self.run_replicates = Replicates_Per_Run

        #############
        # Materials #
        #############
        self.source_materials = Source_Materials
        self.intermediates = Intermediates

        ###########################
        # Destination Information #
        ###########################
        self.destination_content = Destination_Content
        self.destination_layout = None

        ###########
        # Labware #
        ###########
        self.labware_apis = Labware_APIs
        self.labware_layouts = {}

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):
        super().run()

        #################
        # Load DoE Data #
        #################
        if self.batch_factor and self.batch_value:
            DoE = _BMS.DoE_Experiment(self.metadata["protocolName"], self.doe_file).batch_by_factor_value(self.batch_factor, self.batch_value)
        else:
            DoE = _BMS.DoE_Experiment(self.metadata["protocolName"], self.doe_file)

        ###########################
        # Set up source materials #
        ###########################
        for source_material in self.source_materials:
        # If the source material has several variations based on factor values, deal with it
            if type(self.source_materials[source_material][0]) is list:
                factor_components = self.source_materials[source_material][0]
                materials_in_run_order = _BMS.DoE_Create_Source_Material(DoE, source_material, factor_components)
                unique_materials = set(materials_in_run_order)

                print("\nThe following combinations of {} are required:".format(source_material))
                for material in unique_materials:
                    print("{} * {}".format(material, materials_in_run_order.count(material)))



            # If source material is explicitly linked to a factor, deal with it differently to above (obvs)
            else:
                source_material_name = source_material
                source_material_factor = self.source_materials[source_material][0]


                _BMS.DoE_Create_Source_Material(DoE, source_material, source_material_factor)

                print("\n{} is required as a source material.".format(source_material_name))



        ########################
        # Set up intermediates #
        ########################

        for intermediate in self.intermediates:
            source_components = [component[0] for component in self.intermediates[intermediate]]
            source_components_amount_types = [component[1] for component in self.intermediates[intermediate]]
            source_components_amount_values = [component[2] for component in self.intermediates[intermediate]]


            intermediates_in_run_order = _BMS.DoE_Create_Intermediate(DoE, intermediate, source_components, source_components_amount_types, source_components_amount_values)
            unique_intermediates = set(intermediates_in_run_order)

            print("\nThe following combinations of {} are required:".format(intermediate))
            for unique_intermediate in unique_intermediates:
                print("{} * {}".format(unique_intermediate, intermediates_in_run_order.count(unique_intermediate)))

        #############################
        # Set up destination layout #
        #############################

        # Create destination labware layout and add content
        ## Content should be mastermix type and volume, and cell type and volume
        self.labware_layouts["Destination"] = _BMS.Labware_Layout("Destination Labware", self.labware_apis["Destination"])

        Destination_Layout = self.labware_layouts["Destination"]
        Destination_Labware_Format = _BMS.OTProto.get_labware_format(Destination_Layout.type, self.custom_labware_dir)
        Destination_Layout.define_format(Destination_Labware_Format[0], Destination_Labware_Format[1])
        Destination_Well_Range = Destination_Layout.get_well_range(Use_Outer_Wells=False)

        # Determine how many destination wells are required
        ## Calculation uses the number of runs, the number of controls per run, and the number of replicates required
        number_of_runs = len(DoE.runs)
        # len(Destination_Content.keys()) ensures that slots for controls are accounted for, as well as just the samples
        Destination_Slots_Required = (number_of_runs * len(self.destination_content.keys())) * self.run_replicates

        if not Destination_Slots_Required <= len(Destination_Well_Range):
            raise _BMS.LabwareError("Not enough wells in destination plate to set up this experiment ({} needed, {} available)".format(len(DoE.runs) * 6, len(Destination_Well_Range)))

        well_index = 0
        for run in DoE.runs:
            for sample_type in self.destination_content:
                for replicate in range(0, self.run_replicates):
                    content_to_add = []
                    destination_well = Destination_Well_Range[well_index]
                    for content_info in self.destination_content[sample_type]:
                        content = run.get_value_by_name(content_info[0])
                        content_volume = content_info[1]
                        Destination_Layout.add_content(destination_well, content, content_volume)
                    well_index += 1

        print("\n")
        Destination_Layout.print()
        self.destination_layout = Destination_Layout

        #################################
        # Set up intermediate layout(s) #
        #################################

        # Intermediate labware have two representations: intermediate as a destination and intermediate as a source
        ## The intermediate as destination lists the source materials required in each well
        ## The intermediate as a source lists the newly named intermediate materials

        for intermediate in self.intermediates:


            # Set up intermediate as source layout
            self.labware_layouts["{} as source".format(intermediate)] = _BMS.Labware_Layout("{} Labware".format(intermediate), self.labware_apis[intermediate])
            intermediate_as_source_layout = self.labware_layouts["{} as source".format(intermediate)]
            intermediate_as_source_labware_format = _BMS.OTProto.get_labware_format(intermediate_as_source_layout.type, self.custom_labware_dir)
            intermediate_as_source_layout.define_format(intermediate_as_source_labware_format[0], intermediate_as_source_labware_format[1])

            # Set up intermediate as destination layout
            self.labware_layouts["{} as destination".format(intermediate)] = _BMS.Labware_Layout("{} Labware".format(intermediate), self.labware_apis[intermediate])
            intermediate_as_destination_layout = self.labware_layouts["{} as destination".format(intermediate)]
            intermediate_as_destination_labware_format = _BMS.OTProto.get_labware_format(intermediate_as_destination_layout.type, self.custom_labware_dir)
            intermediate_as_destination_layout.define_format(intermediate_as_destination_labware_format[0], intermediate_as_destination_labware_format[1])

            # Get intermediate labware well range and capacity
            ## intermediate as source and intermediate as destination are the same thing,
            ## ...so these don't need to be got separately
            intermediate_well_range = intermediate_as_source_layout.get_well_range()
            intermediate_well_capacity = _BMS.OTProto.get_labware_well_capacity(intermediate_as_source_layout.type, self.custom_labware_dir)

            # Get the names of the intermediates; these will be added to the intermediate as source layout
            intermediates_in_run_order = DoE.get_all_values(intermediate)
            unique_intermediates = set(intermediates_in_run_order)

            # Add the intermediate names to the intermediate as source layout
            # Also add the intermediate components to the intermediate as destination layout
            well_index = 0

            # Get information about the components which make up the intermediates
            source_components_info = self.intermediates[intermediate]

            for unique_intermediate in unique_intermediates:
                # Get volume of intermediate required to fill the destination labware
                volume_required = 0

                intermediate_object = DoE.get_intermediate(unique_intermediate)

                for well in self.labware_layouts["Destination"].get_wells_containing_liquid(unique_intermediate):
                    volume_required += self.labware_layouts["Destination"].get_volume_of_liquid_in_well(unique_intermediate, well)

                # Add an additional 10% to account for pipetting errors, dead volume, etc.
                volume_required += volume_required*0.1

                slots_required = math.ceil(volume_required/intermediate_well_capacity)
                volume_per_slot = volume_required/slots_required

                for slot in range(0, slots_required):
                    intermediate_as_source_layout.add_content(intermediate_well_range[well_index], unique_intermediate, volume_per_slot)


                    # Calculate how much of each source material is required for this intermediate type
                    ## Create a variable to store the component which makes up the intermediate...
                    ## ... to a final volume, if applicable
                    make_up_to_final_volume = None

                    volume_in_slot = 0

                    for component_info in source_components_info:
                        # Convert each of the source component infos to a volume (in uL)
                        component_name, value_type, value_or_ref = component_info
                        component_volume = None

                        if value_type == "volume":
                            # Check if the value_or_ref is an int/float which specifies a constant volume
                            if type(value_or_ref) is int or type(value_or_ref) is float:
                                component_volume = value_or_ref
                            # Check if the value_or_ref specifies that this component should be used to...
                            # ... make up the intermediate to a final volume
                            elif value_or_ref == "make up to final volume":
                                component_volume = value_or_ref
                                make_up_to_final_volume = component_name
                                continue
                            # If neither of the above cases are true, assume that value_or_ref is a reference...
                            # ... to a DoE factor, which should be present in the intermediate name
                            else:
                                component_volume = float(unique_intermediate.split(value_or_ref)[1].split("(")[1].split(")")[0])

                        # Check if "concentration" is in value_type rather than is value_type == "concentration"...
                        # ... as concentration should be supplied "concentration-{}".format(stock concentration)
                        elif "concentration" in value_type:
                            # Get the stock concentration of the component
                            stock_concentration = float(value_type.split("-")[1])

                            # Check if the value_or_ref is an int/float which specifies a constant concentration
                            if type(value_or_ref) is int or type(value_or_ref) is float:
                                final_concentration = value_or_ref
                            # If not, assume that value_or_ref is a reference to a DoE factor, which should be...
                            # ... present in the intermediate name
                            else:

                                final_concentration = float(intermediate_object.components[component_name][2])


                            # Calculate what the concentration in the intermediate should be (as this will be diluted in the destination)
                            intermediate_dilution_in_destination = set()

                            # For each well in the destination which contains this intermediate
                            for well in self.labware_layouts["Destination"].get_wells_containing_liquid(unique_intermediate):
                                # Get the volume of the intermediate in the well
                                intermediate_volume_in_destination = self.labware_layouts["Destination"].get_volume_of_liquid_in_well(unique_intermediate, well)
                                # And the final volume of the destination well
                                final_destination_volume = 0
                                for component in self.labware_layouts["Destination"].get_liquids_in_well(well):
                                    final_destination_volume += self.labware_layouts["Destination"].get_volume_of_liquid_in_well(component, well)

                                # Calculate how much the intermediate is diluted in the destination well and add to the pre-prepared set
                                intermediate_dilution_in_destination.add(intermediate_volume_in_destination/final_destination_volume)

                            # Check that the dilution factor is the same across all wells for this unique intermediate
                            ## Raise an error if not because that would be difficult to handle
                            if not len(intermediate_dilution_in_destination) == 1:
                                raise _BMS.DoEError("Same amount of intermediate {} must be added to all destination wells as this is difficult to deal with at the moment.".format(unique_intermediate))

                            intermediate_dilution_in_destination = intermediate_dilution_in_destination.pop()
                            concentration_in_intermediate = final_concentration/intermediate_dilution_in_destination

                            # Calculate the volume which needs to be added to the intermediate from the stock solution
                            component_volume = round((concentration_in_intermediate*volume_per_slot)/stock_concentration, 1)

                            # Sanity check the volume being added
                            if component_volume <= 0:
                                raise _BMS.NegativeVolumeError("Volume of {} to be added to {} is too small".format(component_name, unique_intermediate))

                        else:
                            raise _BMS.DoEError("Value type for {} in {} must be either 'volume' or 'concentration-{stock_concentration}'".format(component_name, intermediate))

                        # Add the component and volume to the intermediate_as_destination layout



                        intermediate_as_destination_layout.add_content(intermediate_well_range[well_index], intermediate_object.components[component_name][0], component_volume)
                        volume_in_slot += component_volume


                    # If one of the components specified that it should be used to make up any remaining volume, deal with it now
                    if make_up_to_final_volume:
                        intermediate_as_destination_layout.add_content(intermediate_well_range[well_index], intermediate_object.components[make_up_to_final_volume][0], volume_per_slot - volume_in_slot)
                        volume_in_slot += volume_per_slot - volume_in_slot

                    # Sanity check:
                    if not volume_in_slot == volume_per_slot:
                        raise _BMS.DoEError("Calculation error for intermediate {} in well {}:\nVolume Added: {}\nVolume Expected: {}".format(unique_intermediate, intermediate_well_range[well_index], volume_in_slot, volume_per_slot))

                    well_index += 1



            print("\nAs Destination")
            intermediate_as_destination_layout.print()
            print("\nAs Source")
            intermediate_as_source_layout.print()

        ###########################
        # Set up source layout(s) #
        ###########################

        for source_material in self.source_materials:
            # Set up source material layout
            self.labware_layouts[source_material] = _BMS.Labware_Layout("{} Labware".format(source_material), self.labware_apis[source_material])
            source_material_layout = self.labware_layouts[source_material]
            source_material_labware_format = _BMS.OTProto.get_labware_format(source_material_layout.type, self.custom_labware_dir)
            source_material_layout.define_format(source_material_labware_format[0], source_material_labware_format[1])
            source_material_well_range = source_material_layout.get_well_range()

            well_index = 0

            unique_source_ids = set(DoE.get_all_values(source_material))

            for source_id in unique_source_ids:
                # iterate through all wells in intermediate as destination layout with current source_id...
                # ... to calculate the total volume required, then add 10% more to account for dead volumes etc.

                source_id_volume_required = 0

                # Check all "intermediate as destination" layouts for the source material id, and add the required volume to the total
                for intermediate in self.intermediates:
                    intermediate_layout = self.labware_layouts["{} as destination".format(intermediate)]
                    for well in intermediate_layout.get_wells_containing_liquid(source_id):
                        source_id_volume_required += intermediate_layout.get_volume_of_liquid_in_well(source_id, well)

                # Do the above with the destination layout
                destination_layout = self.labware_layouts["Destination"]
                for well in destination_layout.get_wells_containing_liquid(source_id):
                    source_id_volume_required += destination_layout.get_volume_of_liquid_in_well(source_id, well)

                source_id_volume_required += source_id_volume_required * 0.1 # Add 10% more required volume for pipetting accuracy


                aliquot_volume = self.source_materials[source_material][1]
                slots_required = math.ceil(source_id_volume_required/aliquot_volume)

                print("Requires {} uL of {} total - {} aliquots".format(source_id_volume_required, source_id, slots_required))

                for slot in range(0, slots_required):
                    source_material_layout.add_content(source_material_well_range[well_index], source_id, aliquot_volume)
                    well_index += 1

            print("\n")
            source_material_layout.print()

        ########################################
        # Convert layouts to opentrons labware #
        ########################################

        # Create protocol to generate intermediates from source layouts
        source_layouts = []
        destination_layouts = []

        for layout in self.labware_layouts:
            if layout in self.source_materials.keys():
                source_layouts.append(self.labware_layouts[layout])
            elif " as destination" in layout and layout.replace(" as destination", "") in self.intermediates.keys():
                destination_layouts.append(self.labware_layouts[layout])



        Intermediate_Prep_Protocol = _OTProto.Templates.Protocol_From_Layouts(
                                        Protocol = self._protocol,
                                        Name=self.metadata["protocolName"],
                                        Metadata=self.metadata,
                                        Source_Layouts = source_layouts,
                                        Destination_Layouts = destination_layouts
        )
        Intermediate_Prep_Protocol.custom_labware_dir = self.custom_labware_dir
        Intermediate_Prep_Protocol.run()

        self._protocol.pause("Re-load the deck as stated below, and then click continue")

        # Create protocol to generate destination plate
        source_layouts = []
        destination_layouts = []

        for layout in self.labware_layouts:
            if layout in self.source_materials.keys():
                source_layouts.append(self.labware_layouts[layout])
            elif " as source" in layout and layout.replace(" as source", "") in self.intermediates.keys():
                source_layouts.append(self.labware_layouts[layout])
            elif "Destination" in layout:
                destination_layouts.append(self.labware_layouts[layout])

        Destination_Prep_Protocol = _OTProto.Templates.Protocol_From_Layouts(
                                    Protocol = self._protocol,
                                    Name=self.metadata["protocolName"],
                                    Metadata=self.metadata,
                                    Source_Layouts = source_layouts,
                                    Destination_Layouts = destination_layouts
        )
        Destination_Prep_Protocol.custom_labware_dir = self.custom_labware_dir
        Destination_Prep_Protocol.run_as_module(self)

        # END #
