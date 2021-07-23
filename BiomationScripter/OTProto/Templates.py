import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
import math
import smtplib, ssl

class Monarch_Miniprep:
    def __init__(self, Protocol, Name, Metadata, Cultures, Culture_Source_Wells, Culture_Source_Type, Destination_Rack_Type_Tubes, Destination_Rack_Type_Spin_Columns, Destination_Rack_Type_Tube_Insert, Starting_300uL_Tip = "A1", API = "2.10", Simulate = False):
        """
        Cultures should be a list of names, and Culture_Source_Wells should be a list of wells in the same order as DNA.
        Cultures should be presented to the OT2 as cell pellets.
        """
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.cultures = Cultures
        self.culture_source_wells = Culture_Source_Wells
        self.culture_source_type = Culture_Source_Type
        self.starting_300uL_tip = Starting_300uL_Tip
        self.destination_rack_type_tubes = Destination_Rack_Type_Tubes
        self.destination_rack_type_spin_columns = Destination_Rack_Type_Spin_Columns
        self.destination_rack_tube_insert = Destination_Rack_Type_Tube_Insert
        self._reagents_sorce_type = "opentrons_24_aluminumblock_nest_2ml_snapcap"
        self._B1_source_wells = None
        self.B1_volume_per_source_well = 1500 # uL
        self._B2_source_wells = None
        self.B2_volume_per_source_well = 1500 # uL
        self._B3_source_wells = None
        self.B3_volume_per_source_well = 1500 # uL
        self._W1_source_wells = None
        self.W1_volume_per_source_well = 1500 # uL
        self._W2_source_wells = None
        self.W2_volume_per_source_well = 1500 # uL
        self._water_source_wells = None
        self.water_volume_per_source_well = 1500 # uL
        self._protocol = Protocol
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"
        self._custom_labware_dir = "../Custom_Labware/"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.__available_deck_positions = [1,2,3,4,5,6,7,8,9,10,11]

    def use_next_deck_position(self):
        deck_pos = self.__available_deck_positions[0]
        self.__available_deck_positions.remove(self.__available_deck_positions[0]) # record that this deck position has been used
        return(deck_pos)

    def load_labware(self, parent, labware_api_name):
        labware = None
        if self._simulate:
            try:
                labware = parent.load_labware(labware_api_name, self.use_next_deck_position())
            except:
                labware = _OTProto.load_custom_labware(parent, self._custom_labware_dir + "/" + labware_api_name + ".json", self.use_next_deck_position())
        else:
            labware = parent.load_labware(labware_api_name, self.use_next_deck_position())
        return(labware)

    def run(self):
        # Determine how many tips will be needed
        # 1 tip per sample for B1 resuspension
        # 1 tip for all for adding B2
        # 1 tip for all for adding B3
        # 1 tip for all for adding wash buffer 1
        # 1 tip for all for adding wash buffer 2
        # 1 tip for all for adding water
        tips_needed_300uL = len(self.cultures) + 5
        racks_needed_300uL  = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            tip_racks_300uL.append(self._protocol.load_labware(self._300uL_tip_type, self.use_next_deck_position()))

        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        # Determine how many destination racks are required (should always be an even number)
        n_samples = len(self.cultures)
        n_wells_per_destination_rack = len(self.destination_rack_type_tubes.wells())
        n_destination_racks_required = math.ceil((n_samples/2)/n_wells_per_destination_rack)*2

        # Load Culture Plate
        culture_labware = self.load_labware(self._protocol, self.culture_source_type)
        # Load Reagents Source Labware
        reagents_labware = self.load_labware(self._protocol, self._reagents_sorce_type)
        # Load intial destination labware(s)
        destination_rack_tubes = []
        for racks_required in range(0,n_destination_racks_required):
            destination_rack_tubes.append(self.load_labware(self._protocol, self.destination_rack_type_tubes))

        # Store culture locations
        Cultures = _BMS.Liquids()
        for c, w in zip(self.cultures, self.culture_source_wells):
            Cultures.add_liquid(c, w)

        # Store miniprep locations
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_destinations_wells = []
        counter = 0
        for rack in destination_rack_tubes:
            for s in range(0,n_samples):
                miniprep_destinations_wells += rack.wells()[0:n_miniprep_wells_per_rack]
                counter += 1
                if counter == n_samples:
                    break
        Minipreps_Tubes = _BMS.Liquids()
        for m, w in zip(self.cultures, miniprep_destinations_wells):
            Minipreps_Tubes.add_liquid(m, w)

        # Calculate number of B1 aliquots required
        B1_volume_required = len(self.cultures) * 200 # uL
        B1_aliquots_required = math.ceil(B1_volume_required/self.B1_volume_per_source_well)
        # Specify B1 source location(s)
        B1_source = reagents_labware.wells()[0:B1_aliquots_required]

        # Calculate number of B2 aliquots required
        B2_volume_required = len(self.cultures) * 200 # uL
        B2_aliquots_required = math.ceil(B2_volume_required/self.B2_volume_per_source_well)
        # Specify B2 source location(s)
        B2_source = reagents_labware.wells()[B1_aliquots_required:B1_aliquots_required+B2_aliquots_required]

        # Calculate number of B3 aliquots required
        B3_volume_required = len(self.cultures) * 400 # uL
        B3_aliquots_required = math.ceil(B3_volume_required/self.B3_volume_per_source_well)
        # Specify B3 source location(s)
        B3_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required]

        # Calculate number of W1 aliquots required
        W1_volume_required = len(self.cultures) * 200 # uL
        W1_aliquots_required = math.ceil(W1_volume_required/self.W1_volume_per_source_well)
        # Specify W1 source location(s)
        W1_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required]

        # Calculate number of W2 aliquots required
        W2_volume_required = len(self.cultures) * 200 # uL
        W2_aliquots_required = math.ceil(W2_volume_required/self.W2_volume_per_source_well)
        # Specify W2 source location(s)
        W2_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required]

        # Calculate number of Water aliquots required
        Water_volume_required = len(self.cultures) * 200 # uL
        Water_aliquots_required = math.ceil(Water_volume_required/self.Water_volume_per_source_well)
        # Specify Water source location(s)
        Water_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required+Water_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of B1 required".format(len(B1_source)))
        self._protocol.pause("{} aliquot(s) of B2 required".format(len(B2_source)))
        self._protocol.pause("{} aliquot(s) of B3 required".format(len(B3_source)))
        self._protocol.pause("{} aliquot(s) of W1 required".format(len(W1_source)))
        self._protocol.pause("{} aliquot(s) of W2 required".format(len(W2_source)))
        self._protocol.pause("{} aliquot(s) of Water required".format(len(Water_source)))


        # Add 200 uL B1 to each sample, re-suspend, and transfer to destination rack tubes


        # Add 200 uL B2 to each sample

        # Pause and get user to rock plate until all solutions dark pink and transparent

        # Add 400 uL B3 to each sample

        # Pause and get user to rock plate until all solutions are uniformly yellow

        # Pause and prompt user to centrifuge the racks for 5 min at 45000 RPM

        # Pause and prompt user to transfer the samples into spin columns, replace the tubes with the spin columns, centrifuge the racks for 1 min, and discard the flow through

        # Delete the tube racks and load the spin column racks

        # Add 200 uL of W1 to each sample

        # Pause and get the user to centrifuge the racks as above

        # Add 400 uL of W2 to each sample

        # Pause and get the user to centrifuge the rack as above, discard the flow through, and re-centrifuge

        # Get the user to insert the spin column insert into a clean eppendorf and replace on the rack

        # Delete the spin column racks and load the tube_insert racks

        # Add <VOLUME> of water to each tube

        # Pause and prompt the user to centrifuge for 1 min as above

        # Delete the tube_insert racks and load the tube racks (this is to make sure the correct labware shows up in the calibration pane on the app)

        # Pause and prompt the user to remove and dsicard the insert

        # Protocol ends

class Spot_Plating:
    def __init__(self, Protocol, Name, Metadata, Cells, Cell_Source_Wells, Cell_Source_Type, Petri_Dish_Type ="nuncomnitray40mlagar_96_wellplate_15ul", Dilution_Plate_Type = "nunclondeltasurface163320_96_wellplate_250ul", Plating_Volume = 10, Dilution_Factors = [1, 10, 100, 1000, 2000], Starting_20uL_Tip = "A1", Starting_300uL_Tip = "A1", API = "2.10", Simulate = False):
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.cells = Cells
        self.cell_source_wells = Cell_Source_Wells
        self.plating_volume = Plating_Volume
        self.dilution_factors = Dilution_Factors
        self.cell_source_type = Cell_Source_Type
        self.petri_dish_type = Petri_Dish_Type
        self.dilution_plate_type = Dilution_Plate_Type
        self.starting_20uL_tip = Starting_20uL_Tip
        self.starting_300uL_tip = Starting_300uL_Tip
        self._protocol = Protocol
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"
        self._custom_labware_dir = "../Custom_Labware/"
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self._LB_source_type = "3dprinted_15_tuberack_15000ul"
        self._LB_source_volume_per_well = 5000 # uL # No more than 6000 uL for 15 mL tubes
        self.__available_deck_positions = [1,2,3,4,5,6,7,8,9,10,11]
        self.__email_before_plating = False
        self.__email_when_complete = False
        self.__sender_email = None
        self.__receiver_email = None
        self.__password = None
        self.__port = None
        self.__before_plating_message = None
        self.__when_complete_message = None

    def email(self, Sender_Email, Receiver_Email, Password, Before_Plating = False, When_Complete = False, Port = 465, Before_Plating_Message = None, When_Complete_Message = None):
        self.__email_before_plating = Before_Plating
        self.__email_when_complete = When_Complete
        self.__sender_email = Sender_Email
        self.__receiver_email = Receiver_Email
        self.__password = Password
        self.__port = Port
        self.__before_plating_message = Before_Plating_Message
        self.__when_complete_message = When_Complete_Message

    def use_next_deck_position(self):
        deck_pos = self.__available_deck_positions[0]
        self.__available_deck_positions.remove(self.__available_deck_positions[0]) # record that this deck position has been used
        return(deck_pos)

    def load_labware(self, parent, labware_api_name):
        if self._simulate:
            return(_OTProto.load_custom_labware(parent, self._custom_labware_dir + "/" + labware_api_name + ".json", self.use_next_deck_position()))
        else:
            return(parent.load_labware(labware_api_name, self.use_next_deck_position()))

    def run(self):
        # Calculate LB per dilution
        total_LB_required = 0
        total_dilution_volume = 200 # uL
        dilution_LB_volumes = []
        dilution_cell_volumes = [] # This is the volume required from the previous dilution
        self.dilution_factors.sort()
        previous = 1
        LB_tips_300 = False
        LB_tips_20 = False
        cell_tips_300 = False
        cell_tips_20 = False
        first_transfer = True
        for df in self.dilution_factors:
            dilution_cell_volumes.append(total_dilution_volume*(previous/df))
            dilution_LB_volumes.append(total_dilution_volume - (total_dilution_volume*(previous/df)))
            total_LB_required += total_dilution_volume - (total_dilution_volume*(previous/df))
            if total_dilution_volume - (total_dilution_volume*(previous/df)) > 20:
                LB_tips_300 = True
            else:
                LB_tips_20 = True
            if first_transfer:
                first_transfer = False
                continue
            if total_dilution_volume*(previous/df) > 20:
                cell_tips_300 = True
            else:
                cell_tips_20 = True
            previous = df

        first_cell_tips_20 = False
        first_cell_tips_300 = False
        if dilution_cell_volumes[0] > 20:
            first_cell_tips_300 = True
        else:
            first_cell_tips_20 = True

        # Determine how many tips will be needed
        tips_needed_20uL = 0
        tips_needed_300uL = 0
        # Add tips for adding LB into the dilution plate
        if LB_tips_300:
            tips_needed_300uL += 1
        if LB_tips_20:
            tips_needed_20uL += 1
        # Add tips for adding culture into the dilution plate (first row)
        if first_cell_tips_20:
            tips_needed_20uL += len(self.cells)
        else:
            tips_needed_300uL += len(self.cells)
        # Add tips for performing serial dilutions
        serial_dilution_pipette = ""
        if cell_tips_20:
            tips_needed_20uL += len(self.cells)
        if cell_tips_300:
            tips_needed_300uL += len(self.cells)
        if cell_tips_20 and cell_tips_300:
            serial_dilution_pipette = "both"
        elif cell_tips_20 and not cell_tips_300:
            serial_dilution_pipette = "p20"
        elif not cell_tips_20 and cell_tips_300:
            serial_dilution_pipette = "p300"
        # Add tips for spot plating
        tips_needed_20uL += len(self.cells)

        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
        racks_needed_300uL = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            tip_racks_20uL.append(self._protocol.load_labware(self._20uL_tip_type, self.use_next_deck_position()))

        for rack300 in range(0, racks_needed_300uL):
            tip_racks_300uL = [self._protocol.load_labware(self._300uL_tip_type, self.use_next_deck_position())]

        # Set up pipettes
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        # Load labware
        LB_labware = self.load_labware(self._protocol, self._LB_source_type)
        cells_labware = self.load_labware(self._protocol, self.cell_source_type)

        # Determine number of dilution plates and petri dishes needed
        spots_needed = len(self.cells) * len(self.dilution_factors)
        # Load one of each plate type, and then calculate how many extra are needed
        dilution_labware = []
        dilution_labware.append(self.load_labware(self._protocol, self.dilution_plate_type))
        n_dilution_labware = math.ceil(spots_needed/len(dilution_labware[0].wells()))
        n_dilution_labware_extra = n_dilution_labware - 1
        for dl in range(0,n_dilution_labware_extra):
            dilution_labware.append(self.load_labware(self._protocol, self.dilution_plate_type))

        petri_dishes = []
        petri_dishes.append(self.load_labware(self._protocol, self.petri_dish_type))
        n_petri_dishes = math.ceil(spots_needed/len(petri_dishes[0].wells()))
        n_petri_dishes_extra = n_petri_dishes - 1
        for pd in range(0,n_petri_dishes_extra):
            petri_dishes.append(self.load_labware(self._protocol, self.petri_dish_type))

        # Calculate number of LB aliquots required
        LB_aliquots_required = math.ceil((total_LB_required*(len(self.cells)))/self._LB_source_volume_per_well)
        # Specify LB location
        LB_source = LB_labware.wells()[0:LB_aliquots_required]

        # Specify dilution labware well range
        dilution_well_range = [] # grouped by dilution factor
        spots_accounted_for = 0

        dilution_well_ranges = []
        plating_well_ranges = []
        dilution_labware_n = 0
        dilution_well_pos = 0
        plating_labware_n = 0
        plating_well_pos = 0
        for cell_n in range(0,len(self.cells)):
            dilution_cell_range = []
            plating_cell_range = []
            for df in self.dilution_factors:
                if dilution_well_pos > (len(dilution_labware[dilution_labware_n].wells()) - 1):
                    dilution_labware_n += 1
                    dilution_well_pos = 0
                if plating_well_pos > (len(petri_dishes[plating_labware_n].wells()) - 1):
                    plating_labware_n += 1
                    plating_well_pos = 0
                dilution_cell_range.append(dilution_labware[dilution_labware_n].wells()[dilution_well_pos])
                plating_cell_range.append(petri_dishes[plating_labware_n].wells()[plating_well_pos])
                dilution_well_pos += 1
                plating_well_pos += 1
            dilution_well_ranges.append(dilution_cell_range)
            plating_well_ranges.append(plating_cell_range)

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of LB required".format(len(LB_source)))
        self._protocol.pause("LB Location: {}".format(LB_source))
        self._protocol.pause("{} dilution labware required".format(len(dilution_labware)))
        self._protocol.pause("{} petri dishes required".format(len(petri_dishes)))
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(len(tip_racks_20uL)))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(len(tip_racks_300uL)))

        # Liquid handling begins
        # LB_used = 0
        # LB_tube_n = 0
        # # Add LB to each well
        # if LB_tips_20:
        #     p20.pick_up_tip()
        # if LB_tips_300:
        #     p300.pick_up_tip()
        # pipette = None
        # for cell in dilution_well_ranges:
        #     for destination, LB_vol in zip(cell, dilution_LB_volumes):
        #         source = LB_source[LB_tube_n]
        #         if LB_vol > 20:
        #             pipette = p300
        #         else:
        #             pipette = p20
        #         pipette.transfer(LB_vol, source, destination, new_tip = "never")
        #         LB_used += LB_vol
        #         if LB_used > self._LB_source_volume_per_well:
        #             LB_tube_n += 1
        #             LB_used = 0
        # if LB_tips_20:
        #     p20.drop_tip()
        # if LB_tips_300:
        #     p300.drop_tip()
        #
        # # Add initial cells to first dilution factor
        # pipette = None
        # if first_cell_tips_20:
        #     pipette = p20
        # else:
        #     pipette = p300
        # for cell_ranges, cell_source_well in zip(dilution_well_ranges, self.cell_source_wells):
        #     cell_vol = dilution_cell_volumes[0]
        #     source = cells_labware.wells_by_name()[cell_source_well]
        #     destination = cell_ranges[0]
        #     pipette.transfer(cell_vol, source, destination, mix_after = (10, cell_vol))
        #
        # # Perform serial dilutions
        # pipette = None
        # for cell_ranges in dilution_well_ranges: # SOMETHING IS WRONG HERE OR ABOVE
        #     if serial_dilution_pipette == "both":
        #         p20.pick_up_tip()
        #         p300.pick_up_tip()
        #     elif serial_dilution_pipette == "p20":
        #         p20.pick_up_tip()
        #     elif serial_dilution_pipette == "p300":
        #         p300.pick_up_tip()
        #     source_index = 0
        #     for destination, cell_vol in zip(cell_ranges[1:], dilution_cell_volumes[1:]):
        #         if cell_vol > 20:
        #             pipette = p300
        #         else:
        #             pipette = p20
        #         pipette.transfer(cell_vol, cell_ranges[source_index], destination, mix_after = (10, cell_vol), new_tip = "never")
        #         source_index += 1
        #     if serial_dilution_pipette == "both":
        #         p20.drop_tip()
        #         p300.drop_tip()
        #     elif serial_dilution_pipette == "p20":
        #         p20.drop_tip()
        #     elif serial_dilution_pipette == "p300":
        #         p300.drop_tip()
        #
        # # Liquid handling for cell plating
        # if self.__email_before_plating:
        #     metadata_string = ""
        #     for i in self.metadata:
        #         metadata_string += "{}: {}\n".format(i,self.metadata[i])
        #     if self.__before_plating_message == None:
        #         Plating_Message = """
        #         Subject: Update from {}\n\n
        #         The protocol '{}' is ready to begin spot plating. Please uncover the petri dish and resume the protocol.\n\n
        #         Metadata:\n
        #         {}
        #         \n
        #         From {}
        #         """.format(self.metadata['robotName'], self.metadata['protocolName'], metadata_string, self.metadata['robotName'])
        #     context = ssl.create_default_context()
        #     with smtplib.SMTP_SSL("smtp.gmail.com", self.__port, context=context) as server:
        #         server.login(self.__sender_email, self.__password)
        #         server.sendmail(self.__sender_email, self.__receiver_email, Plating_Message)

        self._protocol.pause("Uncover agar plate")
        for cell_range_source, cell_range_destination in zip(dilution_well_ranges, plating_well_ranges): # SOMETHING IS WRONG HERE OR ABOVE
            p20.pick_up_tip()
            for source, destination in zip(cell_range_source, cell_range_destination):
                p20.transfer(self.plating_volume, source, destination, blow_out = True, blowout_location = "destination well", new_tip = "never")
            p20.drop_tip()


class Transformation:
    def __init__(self, Protocol, Name, Metadata, DNA, DNA_Source_Wells, DNA_Volume_Per_Transformation = 2, DNA_Source_Type = "3dprinted_24_tuberack_1500ul", Starting_20uL_Tip = "A1", Starting_300uL_Tip = "A1", API = "2.10", Simulate = False):
        """DNA should be a list of names, and DNA_Source_Wells should be a list of wells in the same order as DNA."""
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.dna = DNA
        self.dna_source_wells = DNA_Source_Wells
        self.dna_volume_per_transformation = DNA_Volume_Per_Transformation
        self.dna_source_type = DNA_Source_Type
        self.starting_20uL_tip = Starting_20uL_Tip
        self.starting_300uL_tip = Starting_300uL_Tip
        self._protocol = Protocol
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"
        self._custom_labware_dir = "../Custom_Labware/"
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self._temperature_module = "temperature module gen2"
        self._transformation_volume = 200 #uL
        self._competent_cells_source_type = "3dprinted_24_tuberack_1500ul"
        self._competent_cells_source_volume_per_well  = 45 # uL
        self._competent_cell_volume_per_transformation = 10 # uL
        self._transformation_destination_type = "greiner650161ushape_96_wellplate_200ul"
        self._LB_source_type = "3dprinted_15_tuberack_15000ul"
        self._LB_source_volume_per_well = 5000 # uL # No more than 6000 uL for 15 mL tubes
        self._heat_shock_time = 90 # Seconds
        self._heat_shock_temp = 42 # celsius
        self.__available_deck_positions = [1,2,3,5,6,7,8,9,10,11] # deck position 4 will always be taken by the temperature module

    # def modify_robot_setup(self, p20_type, p20_position, p300_type, p300_position):
    #

    def use_next_deck_position(self):
        deck_pos = self.__available_deck_positions[0]
        self.__available_deck_positions.remove(self.__available_deck_positions[0]) # record that this deck position has been used
        return(deck_pos)

    def load_labware(self, parent, labware_api_name):
        labware = None
        if self._simulate:
            try:
                labware = parent.load_labware(labware_api_name, self.use_next_deck_position())
            except:
                labware = _OTProto.load_custom_labware(parent, self._custom_labware_dir + "/" + labware_api_name + ".json", self.use_next_deck_position())
        else:
            labware = parent.load_labware(labware_api_name, self.use_next_deck_position())
        return(labware)

    def run(self):
        # Determine how many tips will be needed
        tips_needed_20uL = 0
        # Add 1 tip for adding competent cells
        tips_needed_20uL += 1
        # Add tips for adding DNA - one per sample
        tips_needed_20uL += len(self.dna)
        # Add tips for adding LB - one per sample
        tips_needed_300uL = len(self.dna)
        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
        racks_needed_300uL  = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            tip_racks_20uL.append(self._protocol.load_labware(self._20uL_tip_type, self.use_next_deck_position()))
        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            tip_racks_300uL.append(self._protocol.load_labware(self._300uL_tip_type, self.use_next_deck_position()))
        # Set up pipettes
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        # Load temperature_module
        temperature_module = self._protocol.load_module(self._temperature_module, 4)
        #Load transfomration plate onto temp module
        transformation_plate = self.load_labware(temperature_module, self._transformation_destination_type)

        # Load all other labware
        LB_labware = self.load_labware(self._protocol, self._LB_source_type)
        dna_labware = self.load_labware(self._protocol, self.dna_source_type)
        competent_cells_labware = self.load_labware(self._protocol, self._competent_cells_source_type)

        # Store DNA locations
        DNA = _BMS.Liquids()
        for d,w in zip(self.dna, self.dna_source_wells):
            DNA.add_liquid(d, dna_labware, w)

        # Calculate number of cell aliquots required
        cc_volume_required = len(self.dna) * self._competent_cell_volume_per_transformation # uL
        cc_aliquots_required = math.ceil(cc_volume_required/self._competent_cells_source_volume_per_well)
        # Specify competent cells location
        competent_cells_source = competent_cells_labware.wells()[0:cc_aliquots_required]

        # Calculate number of LB aliquots required
        LB_volume_per_transformation = self._transformation_volume - (self.dna_volume_per_transformation + self._competent_cell_volume_per_transformation)
        LB_Volume_required = len(self.dna) * LB_volume_per_transformation
        LB_aliquots_required = math.ceil(LB_Volume_required/self._LB_source_volume_per_well)
        # Specify LB location
        LB_source = LB_labware.wells()[0:LB_aliquots_required]

        # specify wells to be used for transformations
        transformation_plate_wells_by_row = []
        for r in transformation_plate.rows():
            for w in r:
                transformation_plate_wells_by_row.append(w)
        transformation_destination_range = transformation_plate_wells_by_row[0:len(self.dna)]

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of LB required".format(len(LB_source)))
        self._protocol.pause("LB Location: {}".format(LB_source))
        self._protocol.pause("{} aliquot(s) of cells required".format(len(competent_cells_source)))
        self._protocol.pause("Competent cells location: {}".format(competent_cells_source))
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(len(tip_racks_20uL)))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(len(tip_racks_300uL)))

        for l in DNA.get_all_liquids():
            liquid_name = l
            liquid_labware = DNA.get_liquid_labware(liquid_name)
            liquid_well = DNA.get_liquid_well(liquid_name)
            self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))



        ##################################
        # Start of protocol instructions #
        ##################################

        # Set temperature to 4C and wait until temp is reached
        temperature_module.set_temperature(4)

        # Add competent cells to plate
        cells_used = 0
        tube_n = 0
        p20.pick_up_tip()
        for destination in transformation_destination_range:
            p20.transfer(self._competent_cell_volume_per_transformation, competent_cells_source[tube_n], destination, new_tip = "never", mix_before = (5, 10))
            cells_used += self._competent_cell_volume_per_transformation
            if cells_used >= self._competent_cells_source_volume_per_well:
                tube_n += 1
                cells_used = 0
        p20.drop_tip()

        # Add DNA to competent cells and mix
        for dna, destination in zip(DNA.get_all_liquids(), transformation_destination_range):
            source_labware = DNA.get_liquid_labware(dna)
            source_well = DNA.get_liquid_well(dna)
            source = source_labware.wells_by_name()[source_well]
            p20.transfer(self.dna_volume_per_transformation, source, destination, mix_after = (10, 10))

        # Heat shock at 42C
        temperature_module.set_temperature(self._heat_shock_temp)
        self._protocol.delay(seconds = self._heat_shock_time)
        temperature_module.set_temperature(4)

        # Prompt user to open LB tubes
        self._protocol.pause("Open up LB tubes")

        # Add LB to transfomrations
        LB_used = 0
        tube_n = 0
        for destination in transformation_destination_range:
            p300.transfer(LB_volume_per_transformation, LB_source[tube_n], destination)
            LB_used += LB_volume_per_transformation
            if LB_used > self._LB_source_volume_per_well:
                tube_n += 1
                LB_used = 0
