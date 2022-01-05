import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
# import smtplib, ssl

class Example_Template(_OTProto.OTProto_Template):
    def __init__(self,
        # insert custom arguments here, e.g.:
#       arg_1,
#       arg_2,
        **kwargs # this accepts default keyword arguments from OTProto_Template, i.e. Protocol, Name, and Metadata
    ):
        # Instantiate custom attributes here, e.g.:
#       self.att1 = arg_1
#       self.att2 = arg_2
#       self.att3 = "Cello"
        super().__init__(**kwargs) # This passes the Protocol, Name, Metadata, and various starting tip kw args

    def run(self):

        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        # The rest of your code goes here #

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

class DNA_fmol_Dilution(_OTProto.OTProto_Template):
    def __init__(self,
        Final_fmol,
        DNA,
        DNA_Concentration,
        DNA_Length,
        DNA_Source_Type,
        DNA_Source_Wells,
        Keep_In_Current_Wells,
        Water_Source_Labware_Type,
        Water_Per_Well,
        Final_Volume = None,
        Current_Volume = None,
        Destination_Labware_Type = None,
        Destination_Labware_Range = None,
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
        self._destination_labware_range = Destination_Labware_Range

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
        for dna_starting_concentration, dna_length in zip(self.dna_starting_concentration, self.dna_length):
            mass_g = dna_starting_concentration * 1e-9
            length = dna_length
            fmol = (mass_g/((length * 617.96) + 36.04)) * 1e15
            dna_current_fmol.append(fmol)
            dilution_factor = self.final_fmol/fmol
            dna_dilution_factor.append(dilution_factor)

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
            for dna_well in self.dna_source_wells:
                DNA_Locations.append(DNA_labware.wells_by_name()[dna_well])

            # Load destination labware #
            destination_labware = _OTProto.load_labware(self._protocol, self._destination_labware_type, custom_labware_dir = self.custom_labware_dir, label = "Destination Labware")
            destination_locations = []
            for destination_well in self._destination_labware_range:
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

class OT2_Picklist:
    def __init__(self, Protocol, Name, Metadata, Source_1, Source_Wells_1, Source_Plate_Type_1, Source_Label_1,
    Destination_Plate_Type_1, Destination_Label_1, Transfer_Steps, Source_Plates, Destination_Plates,
    Source_2 = None, Source_Wells_2 = None, Source_Plate_Type_2 = None, Source_Label_2 = None,
    Source_3 = None, Source_Wells_3 = None, Source_Plate_Type_3 = None, Source_Label_3 = None,
    Source_4 = None, Source_Wells_4 = None, Source_Plate_Type_4 = None, Source_Label_4 = None,
    Source_5 = None, Source_Wells_5 = None, Source_Plate_Type_5 = None, Source_Label_5 = None,
    Source_6 = None, Source_Wells_6 = None, Source_Plate_Type_6 = None, Source_Label_6 = None,
    Source_7 = None, Source_Wells_7 = None, Source_Plate_Type_7 = None, Source_Label_7 = None,
    Source_8 = None, Source_Wells_8 = None, Source_Plate_Type_8 = None, Source_Label_8 = None,
    Source_9 = None, Source_Wells_9 = None, Source_Plate_Type_9 = None, Source_Label_9 = None,
    Destination_Plate_Type_2 = None, Destination_Label_2 = None,
    Destination_Plate_Type_3 = None, Destination_Label_3 = None,
    Destination_Plate_Type_4 = None, Destination_Label_4 = None,
    Destination_Plate_Type_5 = None, Destination_Label_5 = None,
    Destination_Plate_Type_6 = None, Destination_Label_6 = None,
    Destination_Plate_Type_7 = None, Destination_Label_7 = None,
    Destination_Plate_Type_8 = None, Destination_Label_8 = None,
    Destination_Plate_Type_9 = None, Destination_Label_9 = None,
    Starting_20uL_Tip = "A1", Starting_300uL_Tip = "A1", API = "2.10", Simulate = "deprecated"):

        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.Name = Name
        self.Metadata = Metadata
        self._simulate = Simulate
        self._custom_labware_dir = "../Custom_Labware/"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self.starting_20uL_tip = Starting_20uL_Tip
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.starting_300uL_tip = Starting_300uL_Tip
        ## Source Plate 1 ##
        self.source_plate_1 = Source_1
        self.source_wells_1 = Source_Wells_1
        self.source_plate_type_1 = Source_Plate_Type_1
        self.source_label_1 = Source_Label_1
        ## Other Source Plates ##
        self.source_plates = Source_Plates
        # There are 12 spaces on the deck
        # 12 is taken by the waste tray
        # at least 1 space is needed for a tip rack
        # at least 1 space is needed for a destination plate
        # This leaves a maximum of 9 possible free spaces
        self.source_plate_2 = Source_2
        self.source_wells_2 = Source_Wells_2
        self.source_plate_type_2 = Source_Plate_Type_2
        self.source_label_2 = Source_Label_2
        self.source_plate_3 = Source_3
        self.source_wells_3 = Source_Wells_3
        self.source_plate_type_3 = Source_Plate_Type_3
        self.source_label_3 = Source_Label_3
        self.source_plate_4 = Source_4
        self.source_wells_4 = Source_Wells_4
        self.source_plate_type_4 = Source_Plate_Type_4
        self.source_label_4 = Source_Label_4
        self.source_plate_5 = Source_5
        self.source_wells_5 = Source_Wells_5
        self.source_plate_type_5 = Source_Plate_Type_5
        self.source_label_5 = Source_Label_5
        self.source_plate_6 = Source_6
        self.source_wells_6 = Source_Wells_6
        self.source_plate_type_6 = Source_Plate_Type_6
        self.source_label_6 = Source_Label_6
        self.source_plate_7 = Source_7
        self.source_wells_7 = Source_Wells_7
        self.source_plate_type_7 = Source_Plate_Type_7
        self.source_label_7 = Source_Label_7
        self.source_plate_8 = Source_8
        self.source_wells_8 = Source_Wells_8
        self.source_plate_type_8 = Source_Plate_Type_8
        self.source_label_8 = Source_Label_8
        self.source_plate_9 = Source_9
        self.source_wells_9 = Source_Wells_9
        self.source_plate_type_9 = Source_Plate_Type_9
        self.source_label_9 = Source_Label_9

        #######################
        # Destination Labware #
        #######################
        self.destination_plate_type_1 = Destination_Plate_Type_1
        self.destination_label_1 = Destination_Label_1
        ## Other Destination Plates
        self.destination_plates = Destination_Plates
        # Maximum of 9 other destination plates
        self.destination_plate_type_2 = Destination_Plate_Type_2
        self.destination_label_2 = Destination_Label_2
        self.destination_plate_type_3 = Destination_Plate_Type_3
        self.destination_label_3 = Destination_Label_3
        self.destination_plate_type_4 = Destination_Plate_Type_4
        self.destination_label_4 = Destination_Label_4
        self.destination_plate_type_5 = Destination_Plate_Type_5
        self.destination_label_5 = Destination_Label_5
        self.destination_plate_type_6 = Destination_Plate_Type_6
        self.destination_label_6 = Destination_Label_6
        self.destination_plate_type_7 = Destination_Plate_Type_7
        self.destination_label_7 = Destination_Label_7
        self.destination_plate_type_8 = Destination_Plate_Type_8
        self.destination_label_8 = Destination_Label_8
        self.destination_plate_type_9 = Destination_Plate_Type_9
        self.destination_label_9 = Destination_Label_9
        ## Information on transfers
        self.transfer_steps = Transfer_Steps

        ###############
        # Robot Setup #
        ###############
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"

    def run(self):
        # Determine how many tips will be needed of each size
        tips_needed_20uL = 0
        tips_needed_300uL = 0
        for t in self.transfer_steps:
            if t[4] < 20:
                tips_needed_20uL += 1
            elif t[4] >= 20 and t[4] <= 300:
                tips_needed_300uL += 1
            elif t[4] > 300:
                if t[4] % 300:
                    tips_needed_300uL += round(t[4]/300) + 1
                else:
                    tips_needed_300uL += t[4] / 300

        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
        racks_needed_300uL = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            tip_racks_20uL.append(self._protocol.load_labware(self._20uL_tip_type, _OTProto.next_empty_slot(self._protocol)))
        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            tip_racks_300uL.append(self._protocol.load_labware(self._300uL_tip_type, _OTProto.next_empty_slot(self._protocol)))
        # Set up pipettes
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        # User prompts for number of tip boxes required, and locations of the tip boxes
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(racks_needed_20uL))
        for tip_box_index in range(0, len(tip_racks_20uL)):
            self._protocol.pause("Place 20 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_20uL[tip_box_index].parent))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(racks_needed_300uL))
        for tip_box_index in range(0, len(tip_racks_300uL)):
            self._protocol.pause("Place 300 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_300uL[tip_box_index].parent))

        # Load all other labware
        source_labware_1 = None
        source_labware_2 = None
        source_labware_3 = None
        source_labware_4 = None
        source_labware_5 = None
        source_labware_6 = None
        source_labware_7 = None
        source_labware_8 = None
        source_labware_9 = None
        # Create dictionaries for source plate data
        source_dict_1 = {
            "plate": self.source_plate_1,
            "type": self.source_plate_type_1,
            "label": self.source_label_1,
            "wells": self.source_wells_1,
            "labware": source_labware_1,
            "liquid": _BMS.Liquids()
        }
        source_dict_2 = {
            "plate": self.source_plate_2,
            "type": self.source_plate_type_2,
            "label": self.source_label_2,
            "wells": self.source_wells_2,
            "labware": source_labware_2,
            "liquid": _BMS.Liquids()
        }
        source_dict_3 = {
            "plate": self.source_plate_3,
            "type": self.source_plate_type_3,
            "label": self.source_label_3,
            "wells": self.source_wells_3,
            "labware": source_labware_3,
            "liquid": _BMS.Liquids()
        }
        source_dict_4 = {
            "plate": self.source_plate_4,
            "type": self.source_plate_type_4,
            "label": self.source_label_4,
            "wells": self.source_wells_4,
            "labware": source_labware_4,
            "liquid": _BMS.Liquids()
        }
        source_dict_5 = {
            "plate": self.source_plate_5,
            "type": self.source_plate_type_5,
            "label": self.source_label_5,
            "wells": self.source_wells_5,
            "labware": source_labware_5,
            "liquid": _BMS.Liquids()
        }
        source_dict_6 = {
            "plate": self.source_plate_6,
            "type": self.source_plate_type_6,
            "label": self.source_label_6,
            "wells": self.source_wells_6,
            "labware": source_labware_6,
            "liquid": _BMS.Liquids()
        }
        source_dict_7 = {
            "plate": self.source_plate_7,
            "type": self.source_plate_type_7,
            "label": self.source_label_7,
            "wells": self.source_wells_7,
            "labware": source_labware_7,
            "liquid": _BMS.Liquids()
        }
        source_dict_8 = {
            "plate": self.source_plate_8,
            "type": self.source_plate_type_8,
            "label": self.source_label_8,
            "wells": self.source_wells_8,
            "labware": source_labware_8,
            "liquid": _BMS.Liquids()
        }
        source_dict_9 = {
            "plate": self.source_plate_9,
            "type": self.source_plate_type_9,
            "label": self.source_label_9,
            "wells": self.source_wells_9,
            "labware": source_labware_9,
            "liquid": _BMS.Liquids()
        }
        # Create a list to store the dictionaries
        source_list = [source_dict_1,source_dict_2,source_dict_3,source_dict_4,source_dict_5,source_dict_6,source_dict_7,source_dict_8,source_dict_9]
        # remove entries for source plates that do not exist
        for p in range(0,(9-self.source_plates)):
            source_list.pop()

        # Load all other labware
        destination_labware_1 = None
        destination_labware_2 = None
        destination_labware_3 = None
        destination_labware_4 = None
        destination_labware_5 = None
        destination_labware_6 = None
        destination_labware_7 = None
        destination_labware_8 = None
        destination_labware_9 = None
        # Create dictionaries for source plate data
        destination_dict_1 = {
            "type": self.destination_plate_type_1,
            "label": self.destination_label_1,
            "labware": destination_labware_1,
        }
        destination_dict_2 = {
            "type": self.destination_plate_type_2,
            "label": self.destination_label_2,
            "labware": destination_labware_2,
        }
        destination_dict_3 = {
            "type": self.destination_plate_type_3,
            "label": self.destination_label_3,
            "labware": destination_labware_3,
        }
        destination_dict_4 = {
            "type": self.destination_plate_type_4,
            "label": self.destination_label_4,
            "labware": destination_labware_4,
        }
        destination_dict_5 = {
            "type": self.destination_plate_type_5,
            "label": self.destination_label_5,
            "labware": destination_labware_5,
        }
        destination_dict_6 = {
            "type": self.destination_plate_type_6,
            "label": self.destination_label_6,
            "labware": destination_labware_6,
        }
        destination_dict_7 = {
            "type": self.destination_plate_type_7,
            "label": self.destination_label_7,
            "labware": destination_labware_7,
        }
        destination_dict_8 = {
            "type": self.destination_plate_type_8,
            "label": self.destination_label_8,
            "labware": destination_labware_8,
        }
        destination_dict_9 = {
            "type": self.destination_plate_type_9,
            "label": self.destination_label_9,
            "labware": destination_labware_9,
        }
        # Create a list to store the dictionaries
        destination_list = [destination_dict_1,destination_dict_2,destination_dict_3,destination_dict_4,destination_dict_5,destination_dict_6,destination_dict_7,destination_dict_8,destination_dict_9]
        # remove entries for destination plates that do not exist
        for p in range(0,(9-self.destination_plates)):
            destination_list.pop()

        # Load labware and store liquid for Source
        for dict in source_list:
            ## Find the next empty deck slot
            labware_slot = _OTProto.next_empty_slot(self._protocol)
            ## Load the labware
            dict["labware"] = _OTProto.load_labware(self._protocol, dict["type"], labware_slot, self._custom_labware_dir, dict["label"])
            # Store liquid locations
            for l,w in zip(dict["plate"], dict["wells"]):
                dict["liquid"].add_liquid(l, dict["labware"], w)
            # dev note: if these functions do not work with None types, use the number of source plates as a break criteria

        # Load labware for Destination
        for dict in destination_list:
            ## Find the next empty deck slot
            labware_slot = _OTProto.next_empty_slot(self._protocol)
            ## Load the labware
            dict["labware"] = _OTProto.load_labware(self._protocol, dict["type"], labware_slot, self._custom_labware_dir, dict["label"])

        # User prompts for number of tip boxes required, and locations of the tip boxes
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(racks_needed_20uL))
        for tip_box_index in range(0, len(tip_racks_20uL)):
            self._protocol.pause("Place 20 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_20uL[tip_box_index].parent))

        # # Prompt user to check all liquids are correctly placed
        # self._protocol.pause("This protocol needs {} 1.5mL tubes".format(len(destination_range)))
        # # one tube rack has been loaded for the destination plate, maximum number of samples is 24
        # if len(destination_range) > 24:
        #     self._protocol.pause("This protocol requires more than 24 tubes. Please limit the protocol to 24 tubes only.")

        # # Prompt user to load DNA
        # for l in DNA.get_all_liquids():
        #     liquid_name = l
        #     liquid_labware = DNA.get_liquid_labware(liquid_name)
        #     liquid_well = DNA.get_liquid_well(liquid_name)
        #     self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))
        # # Prompt user to load Primers
        # for l in Primers.get_all_liquids():
        #     liquid_name = l
        #     liquid_labware = Primers.get_liquid_labware(liquid_name)
        #     liquid_well = Primers.get_liquid_well(liquid_name)
        #     self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))

        ##################################
        # Start of protocol instructions #
        ##################################

        # Complete transfer steps
        for i in range(len(self.transfer_steps)):
            # extract liquid contents from list
            transfer = self.transfer_steps[i]
            source_label = transfer[0]
            source_well = transfer[1]
            destination_label = transfer[2]
            destination_well = transfer[3]
            transfer_volume = transfer[4]
            liquid = transfer[5]
            # reverse lookup source plate based on source_label
            for dict in source_list:
                if dict["label"] == source_label:
                    source_plate = dict["liquid"]
            # reverse lookup destination plate based on destination_label
            for dict in destination_list:
                if dict["label"] == destination_label:
                    destination_labware = dict["labware"]

            # get source well
            source_labware = source_plate.get_liquid_labware(liquid)
            source_well = source_plate.get_liquid_well(liquid)
            source = source_labware.wells_by_name()[source_well]
            # get destination well
            destination = destination_labware.wells_by_name()[destination_well]

            # transfer
            if transfer_volume > 5 and transfer_volume < 20:
                p20.transfer(transfer_volume, source, destination)
            elif transfer_volume >= 20 and transfer_volume < 300:
                p300.transfer(transfer_volume, source, destination)
            else:
                self._protocol.pause("Transfer volume > 300 uL. This will be split into two transfers. Continue?")

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

class Monarch_Miniprep:
    def __init__(self,
        Protocol,
        Name,
        Metadata,
        Cultures,
        Culture_Source_Wells,
        Culture_Source_Type,
        Destination_Rack_Type_Tubes,
        Destination_Rack_Type_Spin_Columns,
        Destination_Rack_Type_Tube_Insert,
        Elution_Volume = 50,
        Starting_300uL_Tip = "A1",
        API = "2.10",
        Simulate = "deprecated"
        ):

        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.custom_labware_dir = "../Custom_Labware/"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.elution_volume = Elution_Volume
        # Reagent volume per sample (uL)
        self.B1_volume_per_sample = 200
        self.B2_volume_per_sample = 200
        self.B3_volume_per_sample = 400
        self.W1_volume_per_sample = 200
        self.W2_volume_per_sample = 400

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.starting_300uL_tip = Starting_300uL_Tip
        ## Cultures ##
        self.cultures = Cultures
        self.culture_source_type = Culture_Source_Type
        self.culture_source_wells = Culture_Source_Wells
        ## Reagents ##
        self.reagents_source_type = "opentrons_24_aluminumblock_nest_2ml_snapcap"
        self._B1_source_wells = None # Resuspension Buffer
        self.B1_volume_per_source_well = 1500 # uL
        self._B2_source_wells = None # Lysis Buffer
        self.B2_volume_per_source_well = 1500 # uL
        self._B3_source_wells = None # Neutralisation Buffer
        self.B3_volume_per_source_well = 1500 # uL
        self._W1_source_wells = None # Wash Buffer 1
        self.W1_volume_per_source_well = 1500 # uL
        self._W2_source_wells = None # Wash Buffer 2
        self.W2_volume_per_source_well = 1500 # uL
        self._water_source_wells = None # water / Elution Buffer
        self.water_volume_per_source_well = 1500 # uL

        #######################
        # Destination Labware #
        #######################
        self.destination_rack_type_tubes = Destination_Rack_Type_Tubes
        self.destination_rack_type_spin_columns = Destination_Rack_Type_Spin_Columns
        self.destination_rack_tube_insert = Destination_Rack_Type_Tube_Insert

        ###############
        # Robot Setup #
        ###############
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"

    def run(self):

        ##################################################################
        # Calculate the number of 300 uL tips required for this protocol #
        ##################################################################
        tips_required_300uL = 0

        # Use a new tip for each culture and step
        ## Some transfer steps may exceed the max transfer size of the pipette and require two or more tips per transfer
        for culture in self.cultures:
            # B1 Resuspension
            tips_required_300uL += math.ceil(self.B1_volume_per_sample/300)
            # Transfer resuspended cultures
            tips_required_300uL += math.ceil(self.B1_volume_per_sample/300)
            # Adding B2
            tips_required_300uL += math.ceil(self.B2_volume_per_sample/300)
            # Adding B3
            tips_required_300uL += math.ceil(self.B3_volume_per_sample/300)
            # Adding W1
            tips_required_300uL += math.ceil(self.W1_volume_per_sample/300)
            # Adding W2
            tips_required_300uL += math.ceil(self.W2_volume_per_sample/300)
            # Elution
            tips_required_300uL += math.ceil(self.elution_volume/300)


        racks_needed_300uL = _OTProto.tip_racks_needed(tips_required_300uL, starting_tip_position = self.starting_300uL_tip)
        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            tip_racks_300uL.append(self._protocol.load_labware(self._300uL_tip_type, _OTProto.next_empty_slot(self._protocol)))

        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        # Determine how many destination racks are required (should always be an even number)
        # Load first two racks and then calculate how many extra are required
        destination_racks_tubes = []

        destination_racks_tubes_slot = _OTProto.next_empty_slot(self._protocol)
        destination_racks_tubes.append(_OTProto.load_labware(self._protocol, self.destination_rack_type_tubes, destination_racks_tubes_slot, self.custom_labware_dir))

        destination_racks_tubes_slot = _OTProto.next_empty_slot(self._protocol)
        destination_racks_tubes.append(_OTProto.load_labware(self._protocol, self.destination_rack_type_tubes, destination_racks_tubes_slot, self.custom_labware_dir))

        n_samples = len(self.cultures)
        n_wells_per_destination_rack = len(destination_racks_tubes[0].wells())
        n_destination_racks_required = math.ceil((n_samples/2)/n_wells_per_destination_rack)*2
        for extra_rack in range(0,n_destination_racks_required - 2):
            destination_racks_tubes_slot = _OTProto.next_empty_slot(self._protocol)
            destination_racks_tubes.append(_OTProto.load_labware(self._protocol, self.destination_rack_type_tubes, destination_racks_tubes_slot, self.custom_labware_dir))


        # Load Culture Plate
        culture_labware_slot = _OTProto.next_empty_slot(self._protocol)
        culture_labware = _OTProto.load_labware(self._protocol, self.culture_source_type, culture_labware_slot, self.custom_labware_dir)

        # Load Reagents Source Labware
        reagents_labware_slot = _OTProto.next_empty_slot(self._protocol)
        reagents_labware = _OTProto.load_labware(self._protocol, self.reagents_source_type, reagents_labware_slot, self.custom_labware_dir)



        # Store culture locations
        Cultures = _BMS.Liquids()
        for c, w in zip(self.cultures, self.culture_source_wells):
            Cultures.add_liquid(c, culture_labware, w)


        # Store miniprep locations for tube rack
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_tube_locations = []
        minipreps_located = 0
        for i_rack in range(0, n_destination_racks_required):
            row_n = 0
            well_n = 0
            i_well_in_row = 0
            wells = destination_racks_tubes[i_rack].rows() # wells grouped by row
            for i_miniprep_in_rack in range(0, n_miniprep_wells_per_rack):
                if minipreps_located == len(self.cultures):
                    break
                well = wells[row_n][i_well_in_row]
                miniprep_tube_locations.append(well)
                i_well_in_row += 1
                minipreps_located += 1
                if i_well_in_row == len(wells[row_n]):
                    row_n += 1
                    i_well_in_row = 0

        # for mpl in miniprep_tube_locations:
        #     print(mpl)

        # Calculate number of B1 aliquots required
        B1_volume_required = len(self.cultures) * 200 # uL
        B1_aliquots_required = math.ceil(B1_volume_required/self.B1_volume_per_source_well) + 1
        # Specify B1 source location(s)
        B1_source = reagents_labware.wells()[0:B1_aliquots_required]

        # Calculate number of B2 aliquots required
        B2_volume_required = len(self.cultures) * 200 # uL
        B2_aliquots_required = math.ceil(B2_volume_required/self.B2_volume_per_source_well) + 1
        # Specify B2 source location(s)
        B2_source = reagents_labware.wells()[B1_aliquots_required:B1_aliquots_required+B2_aliquots_required]

        # Calculate number of B3 aliquots required
        B3_volume_required = len(self.cultures) * 400 # uL
        B3_aliquots_required = math.ceil(B3_volume_required/self.B3_volume_per_source_well) + 1
        # Specify B3 source location(s)
        B3_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required]

        # Calculate number of W1 aliquots required
        W1_volume_required = len(self.cultures) * 200 # uL
        W1_aliquots_required = math.ceil(W1_volume_required/self.W1_volume_per_source_well) + 1
        # Specify W1 source location(s)
        W1_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required]

        # Calculate number of W2 aliquots required
        W2_volume_required = len(self.cultures) * 400 # uL
        W2_aliquots_required = math.ceil(W2_volume_required/self.W2_volume_per_source_well) + 1
        # Specify W2 source location(s)
        W2_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required]

        # Calculate number of Water aliquots required
        Water_volume_required = len(self.cultures) * 50 # uL
        Water_aliquots_required = math.ceil(Water_volume_required/self.water_volume_per_source_well) + 1
        # Specify Water source location(s)
        Water_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required+Water_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        B1_Wells = []
        for location in B1_source:
            B1_Wells.append(str(location).split(" ")[0])
        B2_Wells = []
        for location in B2_source:
            B2_Wells.append(str(location).split(" ")[0])
        B3_Wells = []
        for location in B3_source:
            B3_Wells.append(str(location).split(" ")[0])
        W1_Wells = []
        for location in W1_source:
            W1_Wells.append(str(location).split(" ")[0])
        W2_Wells = []
        for location in W2_source:
            W2_Wells.append(str(location).split(" ")[0])
        Water_Wells = []
        for location in Water_source:
            Water_Wells.append(str(location).split(" ")[0])

        self._protocol.pause("Place reagents rack on deck position {}".format(reagents_labware.parent))
        self._protocol.pause("{} aliquot(s) of B1 required ({} uL per tube/well. Place in positions {})".format(len(B1_source), self.B1_volume_per_source_well, B1_Wells))
        self._protocol.pause("{} aliquot(s) of B2 required ({} uL per tube/well. Place in positions {})".format(len(B2_source), self.B2_volume_per_source_well, B2_Wells))
        self._protocol.pause("{} aliquot(s) of B3 required ({} uL per tube/well. Place in positions {})".format(len(B3_source), self.B3_volume_per_source_well, B3_Wells))
        self._protocol.pause("{} aliquot(s) of W1 required ({} uL per tube/well. Place in positions {})".format(len(W1_source), self.W1_volume_per_source_well, W1_Wells))
        self._protocol.pause("{} aliquot(s) of W2 required ({} uL per tube/well. Place in positions {})".format(len(W2_source), self.W2_volume_per_source_well, W2_Wells))
        self._protocol.pause("{} aliquot(s) of Water required ({} uL per tube/well. Place in positions {})".format(len(Water_source), self.water_volume_per_source_well, Water_Wells))
        self._protocol.pause("{} destination racks required".format(len(destination_racks_tubes)))
        self._protocol.pause("{} tubes per rack".format(n_miniprep_wells_per_rack))

        # Add 200 uL B1 to each sample, re-suspend, and transfer to destination rack tubes
        B1_used = 0
        B1_tube_n = 0
        for culture in Cultures.get_all_liquids():
            source = B1_source[B1_tube_n]
            destination_labware = Cultures.get_liquid_labware(culture)
            destination_well = Cultures.get_liquid_well(culture)
            destination = destination_labware.wells_by_name()[destination_well]
            p300.transfer(200, source, destination, mix_after = (40, 150), blow_out = True, blowout_location = "destination well")

            B1_used += 200
            if B1_used + 200 >= self.B1_volume_per_source_well:
                B1_tube_n += 1
                B1_used = 0

        # Transfer to tubes
        for sample, destination in zip(Cultures.get_all_liquids(), miniprep_tube_locations):
            source_labware = Cultures.get_liquid_labware(sample)
            source_well = Cultures.get_liquid_well(sample)
            source = source_labware.wells_by_name()[source_well]
            p300.transfer(200, source, destination, mix_before = (5, 150))



        # Add 200 uL B2 to each sample
        B2_used = 0
        B2_tube_n = 0
        for destination in miniprep_tube_locations:
            source = B2_source[B2_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")

            B2_used += 200
            if B2_used + 200 >= self.B2_volume_per_source_well:
                B2_tube_n += 1
                B2_used = 0
        self._protocol.pause("Invert the tube racks until all solutions are dark pink and transparent, then replace the racks.")

        # Add 400 uL B3 to each sample
        B3_used = 0
        B3_tube_n = 0
        for destination in miniprep_tube_locations:
            source = B3_source[B3_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")

            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")

            B3_used += 400
            if B3_used + 400 >= self.B3_volume_per_source_well:
                B3_tube_n += 1
                B3_used = 0
        self._protocol.pause("Invert the tube racks until all solutions are uniformly yellow, then centrifuge the racks for 5 mins at 4500 RPM.")

        self._protocol.pause("Replace the tubes with clean spin columns and carefully tip the supernatant from the tubes into the columns, then centrifuge for 1 min and discard the flow through.")

        # Delete the tube racks and load the spin column racks
        destination_racks_spin_columns = []
        for tube_rack in destination_racks_tubes:
            tube_rack_deck_pos = tube_rack.parent
            del self._protocol.deck[str(tube_rack_deck_pos)]
            destination_racks_spin_columns.append(_OTProto.load_labware(self._protocol, self.destination_rack_type_spin_columns, tube_rack_deck_pos, self.custom_labware_dir))


        # Store miniprep locations for spin columns rack
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_spin_column_locations = []
        minipreps_located = 0
        for i_rack in range(0, n_destination_racks_required):
            row_n = 0
            well_n = 0
            i_well_in_row = 0
            wells = destination_racks_spin_columns[i_rack].rows() # wells grouped by row
            for i_miniprep_in_rack in range(0, n_miniprep_wells_per_rack):
                if minipreps_located == len(self.cultures):
                    break
                well = wells[row_n][i_well_in_row]
                miniprep_spin_column_locations.append(well)
                i_well_in_row += 1
                minipreps_located += 1
                if i_well_in_row == len(wells[row_n]):
                    row_n += 1
                    i_well_in_row = 0

        # Add 200 uL of W1 to each sample
        W1_used = 0
        W1_tube_n = 0
        for destination in miniprep_spin_column_locations:
            source = W1_source[W1_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")

            W1_used += 200
            if W1_used + 200 >= self.W1_volume_per_source_well:
                W1_tube_n += 1
                W1_used = 0

        # Pause and get the user to centrifuge the racks as above
        self._protocol.pause("Centrifuge the racks for 5 mins at 4500 RPM.")

        # Add 400 uL of W2 to each sample
        W2_used = 0
        W2_tube_n = 0
        for destination in miniprep_spin_column_locations:
            source = W2_source[W2_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")

            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")

            W2_used += 400
            if W2_used + 400 >= self.W2_volume_per_source_well:
                W2_tube_n += 1
                W2_used = 0

        # Pause and get the user to centrifuge the rack as above, discard the flow through, and re-centrifuge
        self._protocol.pause("Centrifuge the racks for 5 mins at 4500 RPM, discard the flow through, and then re-centrifuge.")

        # Get the user to insert the spin column insert into a clean eppendorf and replace on the rack
        self._protocol.pause("Replace the spin columns with clean 1.5 mL tubes, and insert the inner spin column into the tube.")

        # Delete the spin column racks and load the tube_insert racks
        destination_racks_insert_tubes = []
        for spin_column_rack in destination_racks_spin_columns:
            spin_column_rack_deck_pos = spin_column_rack.parent
            del self._protocol.deck[str(spin_column_rack_deck_pos)]
            destination_racks_insert_tubes.append(_OTProto.load_labware(self._protocol, self.destination_rack_tube_insert, spin_column_rack_deck_pos, self.custom_labware_dir))

        # Store miniprep locations for tube_insert racks
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_insert_tube_locations = []
        minipreps_located = 0
        for i_rack in range(0, n_destination_racks_required):
            row_n = 0
            well_n = 0
            i_well_in_row = 0
            wells = destination_racks_insert_tubes[i_rack].rows() # wells grouped by row
            for i_miniprep_in_rack in range(0, n_miniprep_wells_per_rack):
                if minipreps_located == len(self.cultures):
                    break
                well = wells[row_n][i_well_in_row]
                miniprep_insert_tube_locations.append(well)
                i_well_in_row += 1
                minipreps_located += 1
                if i_well_in_row == len(wells[row_n]):
                    row_n += 1
                    i_well_in_row = 0

        # Add <VOLUME> of water to each tube
        Water_used = 0
        Water_tube_n = 0
        for destination in miniprep_insert_tube_locations:
            source = Water_source[Water_tube_n]
            p300.transfer(self.elution_volume, source, destination, blow_out = True, blowout_location = "destination well")

            Water_used += self.elution_volume
            if Water_used + self.elution_volume >= self.water_volume_per_source_well:
                Water_tube_n += 1
                Water_used = 0

        # Pause and prompt the user to centrifuge for 1 min as above
        self._protocol.pause("Centrifuge the racks for 5 mins at 4500 RPM, then remove and discard the inserts.")

        # Delete the tube_insert racks and load the tube racks (this is to make sure the correct labware shows up in the calibration pane on the app)

        for tube_rack in destination_racks_insert_tubes:
            tube_rack_deck_pos = tube_rack.parent
            del self._protocol.deck[str(tube_rack_deck_pos)]
            destination_racks_tubes.append(_OTProto.load_labware(self._protocol, self.destination_rack_type_tubes, tube_rack_deck_pos, self.custom_labware_dir))

class Spot_Plating:
    def __init__(self,
        Protocol,
        Name,
        Metadata,
        Cells,
        Cell_Source_Wells,
        Cell_Source_Type,
        Dilution_Plate_Type,
        Petri_Dish_Type ="nuncomnitray40mlagar_96_wellplate_15ul",
        Plating_Volume = 10,
        Dilution_Factors = [1, 10, 100, 1000, 2000],
        Dilution_Volume = 200,
        Starting_20uL_Tip = "A1",
        Starting_300uL_Tip = "A1",
        API = "2.10",
        Simulate = "deprecated"
    ):

        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.custom_labware_dir = "../Custom_Labware/"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.plating_volume = Plating_Volume
        self.dilution_factors = Dilution_Factors
        self.dilution_volume = Dilution_Volume

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.starting_20uL_tip = Starting_20uL_Tip
        self.starting_300uL_tip = Starting_300uL_Tip
        ## Cells to be plated ##
        self.cells = Cells
        self.cell_source_type = Cell_Source_Type
        self.cell_source_wells = Cell_Source_Wells
        ## LB media ##
        self.LB_source_type = "3dprinted_15_tuberack_15000ul"
        self.LB_source_volume_per_well = 5000 # uL # No more than 6000 uL for 15 mL tubes

        #######################
        # Destination Labware #
        #######################
        self.petri_dish_type = Petri_Dish_Type
        self.dilution_plate_type = Dilution_Plate_Type

        ###############
        # Robot Setup #
        ###############
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"

    def serial_dilution_volumes(self, dilution_factors, total_volume):
        # Note that total volume is the amount the dilution will be made up to
        ## The total volume of all dilutions other than the final will be lower than this
        substance_volumes = []
        solution_volumes = []

        # This the the dilution factor of the source material for the first serial dilution
        ## This is always 1, as the initial substance is assumed to be undiluted
        source_dilution_factor = 1

        for df in dilution_factors:
            # Get the dilution factor of the current serial dilution being performed
            destination_dilution_factor = df

            # Calculate the volume, in uL, of substance and solution required for each dilution factor
            substance_volume = total_volume * (source_dilution_factor/destination_dilution_factor)
            solution_volume = total_volume - substance_volume

            # Store the volumes required for later use
            substance_volumes.append(substance_volume)
            solution_volumes.append(solution_volume)

            # Set the current dilution as the source for the next serial dilution
            source_dilution_factor = df

        return(substance_volumes, solution_volumes)

    ####################################
    # Function to be called by the OT2 #
    ####################################
    def run(self):

        #################################################################
        # Calculate amount of cells and LB media required for dilutions #
        #################################################################

        # Ensure dilution factors are in ascending order
        self.dilution_factors.sort()

        # Call the serial_dilution_volumes method to get a list of cell and LB volumes for each dilution factor
        ## These lists retain the order of self.dilution_factors (after sort)
        cell_dilution_volumes, LB_dilution_volumes = self.serial_dilution_volumes(self.dilution_factors, self.dilution_volume)

        ## Create copies of the cell and LB volume lists without volume 0 - helps calculate number of tips required ###
        cell_dilution_volumes_no_0 = cell_dilution_volumes.copy()
        try:
            cell_dilution_volumes_no_0.remove(0)
        except:
            pass
        LB_dilution_volumes_no_0 = LB_dilution_volumes.copy()
        try:
            LB_dilution_volumes_no_0.remove(0)
        except:
            pass
        ###############################################################################################################

        #########################################################################
        # Calculate the number of 20 and 300 uL tips required for this protocol #
        #########################################################################
        tips_required_20uL = 0
        tips_required_300uL = 0

        # Tips required for dilution stage #

        ## Adding LB to dilution labware - don't need to change tip per transfer
        ### Determine the min and max LB volumes which need to be transferred, and determine if a 20uL or 300uL tip, or both, are required
        max_LB_volume = max(LB_dilution_volumes_no_0)
        min_LB_volume = min(LB_dilution_volumes_no_0)
        if max_LB_volume > 20:
            # If there are any LB transfer events larger than 20 uL, a 300 uL tip will be required
            tips_required_300uL += 1
        if min_LB_volume <= 20:
            # If there are any LB transfer events fewer than or equal to 20 uL, a 20 uL tip will be required:
            tips_required_20uL += 1

        ## Transferring cells to and between wells of the dilution labware - clean tip per transformation
        for Cell in self.cells:
            ### Determine the min and max cell volumes which need to be transferred, and determine if a 20uL or 300uL tip, or both, are required
            max_cell_volume = max(cell_dilution_volumes_no_0)
            min_cell_volume = min(cell_dilution_volumes_no_0)

            if max_cell_volume > 20:
                # If there are any cell transfer events larger than 20 uL, a 300 uL tip will be required
                tips_required_300uL += 1
            if min_cell_volume <= 20:
                # If there are any cell transfer events fewer than or equal to 20 uL, a 20 uL tip will be required:
                tips_required_20uL += 1

        # Tips required for spot plating - clean tip for each dilution #
        if self.plating_volume > 20:
            tips_required_300uL += len(self.cells) * len(self.dilution_factors)
        else:
            tips_required_20uL += len(self.cells) * len(self.dilution_factors)

        ##############################################################################
        # Calculate the number of 20 and 300 uL tip racks required for this protocol #
        ##############################################################################
        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_required_20uL, self.starting_20uL_tip)
        racks_needed_300uL = _OTProto.tip_racks_needed(tips_required_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._20uL_tip_type, rack_deck_slot, self.custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_20uL.append(rack)

        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._300uL_tip_type, rack_deck_slot, self.custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_300uL.append(rack)

        ###################
        # Set up pipettes #
        ###################
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        ################
        # Load labware #
        ################

        # Determine amount of dilution labware required #
        ## Determine number of wells required
        wells_needed = len(self.cells) * len(self.dilution_factors)
        ## Load and store all required dilution labware
        dilution_labware, dilution_locations = _OTProto.calculate_and_load_labware(self._protocol, self.dilution_plate_type, wells_needed, custom_labware_dir = self.custom_labware_dir)

        # Determine amount of agar plates required #
        wells_needed = len(self.cells) * len(self.dilution_factors)
        petri_dishes, colony_locations = _OTProto.calculate_and_load_labware(self._protocol, self.petri_dish_type, wells_needed, custom_labware_dir = self.custom_labware_dir)

        # Load source labware #
        cell_labware_deck_slot = _OTProto.next_empty_slot(self._protocol)
        cells_labware = _OTProto.load_labware(self._protocol, self.cell_source_type, cell_labware_deck_slot, self.custom_labware_dir)
        LB_labware_deck_slot = _OTProto.next_empty_slot(self._protocol)
        LB_labware = _OTProto.load_labware(self._protocol, self.LB_source_type, LB_labware_deck_slot, self.custom_labware_dir)

        ## Calculate number of LB aliquots required
        total_LB_required = len(self.cells) * sum(LB_dilution_volumes) # Calculate total amount of LB required
        LB_aliquots_required = math.ceil(total_LB_required/self.LB_source_volume_per_well)
        ## Specify LB location
        LB_source = LB_labware.wells()[0:LB_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of LB required".format(len(LB_source)))
        self._protocol.pause("LB Location: {}".format(LB_source))
        self._protocol.pause("{} dilution labware required".format(len(dilution_labware)))
        self._protocol.pause("{} petri dishes required".format(len(petri_dishes)))
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(len(tip_racks_20uL)))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(len(tip_racks_300uL)))

        ##########################
        # Liquid handling begins #
        ##########################

        ##############################
        # Add LB to dilution labware #
        ##############################

        # Create a list of LB volumes which need to be transfered to the destination labware
        LB_transfers = LB_dilution_volumes * len(self.cells)
        for destination_labware_index in range(0, len(dilution_labware)):
            # Get the current destination laware
            destination_labware = dilution_labware[destination_labware_index]
            # Get all available wells in the destination labware
            wells_in_labware = len(destination_labware.wells())
            # Get the subset of LB volumes which will be transferred to this destination labware
            ## Note that if there is only one destination labware, LB_volumes == LB_transfers
            LB_volumes = LB_transfers[0+(wells_in_labware*destination_labware_index):wells_in_labware+(wells_in_labware*destination_labware_index)]
            _OTProto.dispense_from_aliquots(self._protocol, LB_volumes, LB_source, destination_labware.wells(), new_tip = False, Aliquot_Volumes = self.LB_source_volume_per_well)

#### Code below is replaced with code above, but is left for now incase of unexpected behaviour
        # # This is to switch which LB aliquot is being used as the source
        # LB_tube_index = 0
        #
        # # Determine which tip(s) are required and get it/them
        # if min_LB_volume <= 20:
        #     p20.pick_up_tip()
        # if max_LB_volume > 20:
        #     p300.pick_up_tip()
        #
        # # Create a list of LB volumes which need to be transfered to the destination labware
        # LB_transfers = LB_dilution_volumes * len(self.cells)
        # for destination_labware_index in range(0, len(dilution_labware)):
        #     # Get the current destination laware
        #     destination_labware = dilution_labware[destination_labware_index]
        #     # Get all available wells in the destination labware
        #     wells_in_labware = len(destination_labware.wells())
        #     # Get the subset of LB volumes which will be transferred to this destination labware
        #     ## Note that if there is only one destination labware, LB_volumes == LB_transfers
        #     LB_volumes = LB_transfers[0+(wells_in_labware*destination_labware_index):wells_in_labware+(wells_in_labware*destination_labware_index)]
        #     for volume, destination in zip(LB_volumes, destination_labware.wells()):
        #         # if volume is 0, skip the transfer
        #         if volume == 0:
        #             continue
        #         # Determine which pipette is needed
        #         if volume > 20:
        #             pipette = p300
        #         elif volume <= 20:
        #             pipette = p20
        #         # Determine which LB aliquot to take from
        #         source = LB_source[LB_tube_index]
        #         # Perform the transfer
        #         pipette.transfer(volume, source, destination, new_tip = "never")
        #         # Iterate to the next LB aliquot, and check if need to go back to first aliquot
        #         if LB_tube_index == len(LB_source) - 1:
        #             LB_tube_index = 0
        #         else:
        #             LB_tube_index += 1
        #
        # # Drop tips which have been in use
        # if min_LB_volume <= 20:
        #     p20.drop_tip()
        # if max_LB_volume > 20:
        #     p300.drop_tip()

        ############################
        # Perform serial dilutions #
        ############################

        # Set up a list to store locations of all dilutions - will be used for plating later
        dilution_locations = []

        transfer_index = 0
        destination_labware_index = 0
        for cell_index in range(0, len(self.cells)):
            # Determine which tip(s) are required and get it/them
            if min_cell_volume <= 20:
                p20.pick_up_tip()
            if max_cell_volume > 20:
                p300.pick_up_tip()

            # Transfer cells to the first well in the dilution labware
            # Determine which pipette is needed
            transfer_volume = cell_dilution_volumes[0]
            if transfer_volume > 20:
                pipette = p300
            elif transfer_volume <= 20:
                pipette = p20
            # get the destination location
            destination_labware = dilution_labware[destination_labware_index]
            destination = destination_labware.wells()[transfer_index]
            dilution_locations.append(destination)
            # get the source location
            source = cells_labware.wells_by_name()[self.cell_source_wells[cell_index]]
            # Perfrom the transfer
            pipette.transfer(transfer_volume, source, destination, new_tip = "never", mix_after = (5,transfer_volume))
            # Add to the transfer counter
            transfer_index += 1
            # Check if the current destination labware is full
            if len(destination_labware.wells()) == transfer_index:
                destination_labware_index += 1
                transfer_index = 0


            # Perform the remianing serial dilutions for this cell type
            for transfer_volume in cell_dilution_volumes[1:]:
                # if volume is 0, skip the transfer
                if transfer_volume == 0:
                    continue
                # Determine which pipette is needed
                if transfer_volume > 20:
                    pipette = p300
                elif transfer_volume <= 20:
                    pipette = p20
                # set the source as the previous dilution
                if transfer_index == 0: # If the next dilution is in a new destination labware...
                    # Set the source labware as the previous labware
                    source_labware = dilution_labware[destination_labware_index - 1]
                    source = source_labware.wells()[-1]
                else:
                    source_labware = dilution_labware[destination_labware_index]
                    source = source_labware.wells()[transfer_index - 1]

                # Set the destination location
                destination_labware = dilution_labware[destination_labware_index]
                destination = destination_labware.wells()[transfer_index]
                dilution_locations.append(destination)

                # Perform the transfer
                pipette.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = (5,transfer_volume), mix_after = (5,transfer_volume))
                # Add to the transfer counter
                transfer_index += 1
                # Check if the current destination labware is full
                if len(destination_labware.wells()) == transfer_index:
                    destination_labware_index += 1
                    transfer_index = 0

            # Drop tips which have been in use
            if min_cell_volume <= 20:
                p20.drop_tip()
            if max_cell_volume > 20:
                p300.drop_tip()


        self._protocol.pause("Uncover agar plate on position {}".format(petri_dishes[0].parent))

        # Determine which pipette is needed
        if self.plating_volume > 20:
            pipette = p300
        elif self.plating_volume <= 20:
            pipette = p20

        destination_labware_index = 0
        plating_index = 0
        for source in dilution_locations:
            destination_labware = petri_dishes[destination_labware_index]
            destination = destination_labware.wells()[plating_index]
            pipette.transfer(self.plating_volume, source, destination, blow_out = True, blowout_location = "destination well")
            # Add to the plating counter
            plating_index += 1
            # Check if the current destination labware is full
            if len(destination_labware.wells()) == plating_index:
                destination_labware_index += 1
                plating_index = 0
                self._protocol.pause("Uncover agar plate on position {}".format(petri_dishes[destination_labware_index].parent))

class Transformation:
    def __init__(self,
        Protocol,
        Name,
        Metadata,
        DNA,
        DNA_Source_Wells,
        Competent_Cells_Source_Type,
        Transformation_Destination_Type,
        DNA_Source_Type,
        DNA_Volume_Per_Transformation,
        Starting_20uL_Tip = "A1",
        Starting_300uL_Tip = "A1",
        API = "2.10",
        Simulate = "deprecated"
    ):
        # DNA should be a list of names, and DNA_Source_Wells should be a list of wells in the same order as DNA.

        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.custom_labware_dir = "../Custom_Labware/"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

        ########################################
        # User defined aspects of the protocol #
        ########################################
        # Running parameters
        self.dna_volume_per_transformation = DNA_Volume_Per_Transformation # uL
        self._competent_cell_volume_per_transformation = 10 # uL
        self._transformation_volume = 200 #uL
        self._heat_shock_time = 90 # Seconds
        self._heat_shock_temp = 42 # celsius

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.starting_20uL_tip = Starting_20uL_Tip
        self.starting_300uL_tip = Starting_300uL_Tip
        ## DNA to be transformed ##
        self.dna = DNA
        self.dna_source_wells = DNA_Source_Wells
        self.dna_source_type = DNA_Source_Type
        ## Competent cells ##
        self._competent_cells_source_type = Competent_Cells_Source_Type
        self.competent_cells_source_volume_per_well  = 45 # uL
        ## Media ##
        self.LB_source_type = "3dprinted_15_tuberack_15000ul"
        self.LB_source_volume_per_well = 5000 # uL # No more than 6000 uL for 15 mL tubes

        #######################
        # Destination Labware #
        #######################
        self._transformation_destination_type = Transformation_Destination_Type
        self.transformation_locations = []

        ###############
        # Robot Setup #
        ###############
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"
        self._temperature_module = "temperature module gen2"

    def run(self):
        ###########################
        # Load temperature_module #
        ###########################
        temperature_module = self._protocol.load_module(self._temperature_module, 4)

        #########################################################################
        # Calculate the number of 20 and 300 uL tips required for this protocol #
        #########################################################################
        tips_needed_20uL = 0
        tips_needed_300uL = 0

        # Adding competent cells #
        if self._competent_cell_volume_per_transformation > 20:
            tips_needed_300uL += 1
        else:
            tips_needed_20uL += 1

        # Add tips for adding DNA - one per sample #
        tips_needed_20uL += len(self.dna)

        # Add tips for adding LB - one per sample #
        media_per_transformation = self._transformation_volume - (self._competent_cell_volume_per_transformation + self.dna_volume_per_transformation)
        if media_per_transformation > 20:
            tips_needed_300uL += len(self.dna)
        else:
            tips_needed_20uL += len(self.dna)

        ##############################################################################
        # Calculate the number of 20 and 300 uL tip racks required for this protocol #
        ##############################################################################
        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
        racks_needed_300uL  = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._20uL_tip_type, rack_deck_slot, self.custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_20uL.append(rack)

        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._300uL_tip_type, rack_deck_slot, self.custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_300uL.append(rack)

        ###################
        # Set up pipettes #
        ###################
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        ################
        # Load labware #
        ################
        # Load transfomration plate onto temp module #
        transformation_plate = _OTProto.load_labware(temperature_module, self._transformation_destination_type, custom_labware_dir = self.custom_labware_dir)

        # Load all other labware #
        LB_labware_slot = _OTProto.next_empty_slot(self._protocol)
        LB_labware = _OTProto.load_labware(self._protocol, self.LB_source_type, LB_labware_slot, self.custom_labware_dir)

        dna_labware_slot = _OTProto.next_empty_slot(self._protocol)
        dna_labware = _OTProto.load_labware(self._protocol, self.dna_source_type, dna_labware_slot, self.custom_labware_dir)

        competent_cells_labware_slot = _OTProto.next_empty_slot(self._protocol)
        competent_cells_labware = _OTProto.load_labware(self._protocol, self._competent_cells_source_type, competent_cells_labware_slot, self.custom_labware_dir)

        # Calculate number of cell aliquots required #
        cc_volume_required = len(self.dna) * self._competent_cell_volume_per_transformation # uL
        cc_aliquots_required = _BMS.aliquot_calculator(cc_volume_required, self.competent_cells_source_volume_per_well)

        # Specify competent cells location
        competent_cells_source = competent_cells_labware.wells()[0:cc_aliquots_required]

        # Calculate number of LB aliquots required #
        LB_volume_per_transformation = self._transformation_volume - (self.dna_volume_per_transformation + self._competent_cell_volume_per_transformation)
        LB_Volume_required = len(self.dna) * LB_volume_per_transformation
        LB_aliquots_required = _BMS.aliquot_calculator(LB_Volume_required, self.LB_source_volume_per_well)

        # Specify LB location
        LB_source = LB_labware.wells()[0:LB_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of LB required".format(len(LB_source)))
        self._protocol.pause("LB Location: {}".format(LB_source))
        self._protocol.pause("{} aliquot(s) of cells required".format(len(competent_cells_source)))
        self._protocol.pause("Competent cells location: {}".format(competent_cells_source))
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(len(tip_racks_20uL)))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(len(tip_racks_300uL)))

        for dna, source_well in zip(self.dna, self.dna_source_wells):
            self._protocol.pause('Place {} in well {} at deck position {}'.format(dna, source_well, dna_labware_slot))

        ##########################
        # Liquid handling begins #
        ##########################

        ########################################################
        # Set temperature to 4C and wait until temp is reached #
        ########################################################
        temperature_module.set_temperature(4)

        ################################
        # Add competent cells to plate #
        ################################
        # This is to switch which competent cells aliquot is being used as the source
        cc_tube_index = 0

        # Determine which tip is required and get it
        if self._competent_cell_volume_per_transformation <= 20:
            pipette = p20
            pipette.pick_up_tip()
        else:
            pipette = p300
            pipette.pick_up_tip()

        for transformation_index in range(0, len(self.dna)):
            # Determine which competent cell aliquot to take from
            source = competent_cells_source[cc_tube_index]
            # Set the next empty well in the transformation labware as the destination
            destination = transformation_plate.wells()[transformation_index]
            # Perform the transfer
            pipette.transfer(self._competent_cell_volume_per_transformation, source, destination, new_tip = "never", mix_before = (5, self._competent_cell_volume_per_transformation), touch_tip = True, blow_out = True, blowout_location = "destination well")
            # Iterate to the next competent cell aliquot, and check if need to go back to first aliquot
            if cc_tube_index == len(competent_cells_source) - 1:
                cc_tube_index = 0
            else:
                cc_tube_index += 1

        # Drop tips which have been in use
        if self._competent_cell_volume_per_transformation <= 20:
            pipette = p20
            pipette.drop_tip()
        else:
            pipette = p300
            pipette.drop_tip()

        ######################################
        # Add DNA to competent cells and mix #
        ######################################
        # Determine which pipette should be used
        if self.dna_volume_per_transformation <= 20:
            pipette = p20
        else:
            pipette = p300

        for transformation_index in range(0, len(self.dna)):
            # Get the location of the dna to be added
            source = dna_labware.wells_by_name()[self.dna_source_wells[transformation_index]]
            # Get the 'well' to which the DNA should be added
            destination = transformation_plate.wells()[transformation_index]
            # Perform the transfer
            pipette.transfer(self.dna_volume_per_transformation, source, destination, mix_after = (10, 10), touch_tip = True, blow_out = True, blowout_location = "destination well")

        #####################
        # Heat shock at 42C #
        #####################
        self._protocol.pause("Check that cells and DNA are collected at the bottom of the plate.")
        # Set the temp to heat shock
        temperature_module.set_temperature(self._heat_shock_temp)
        # Wait for a bit
        self._protocol.delay(seconds = self._heat_shock_time)
        # Cool back to 4 - protocol won't continue until this is back at 4...
        temperature_module.set_temperature(4)

        #############################
        # Add LB to transfomrations #
        #############################
        # Prompt user to open LB tubes
        self._protocol.pause("Open up LB tubes")

        # This is to switch which LB aliquot is being used as the source
        LB_tube_index = 0

        # Determine which pipette will be used
        if media_per_transformation <= 20:
            pipette = p20
        else:
            pipette = p300

        for transformation_index in range(0, len(self.dna)):
            # Determine which media aliquot to take from
            source = LB_source[LB_tube_index]
            # Set the next empty well in the transformation labware as the destination
            destination = transformation_plate.wells()[transformation_index]
            # Perform the transfer
            pipette.transfer(media_per_transformation, source, destination)
            # Iterate to the next media aliquot, and check if need to go back to first aliquot
            if LB_tube_index == len(LB_source) - 1:
                LB_tube_index = 0
            else:
                LB_tube_index += 1

        for dna, well in zip(self.dna, transformation_plate.wells()):
            self.transformation_locations.append([well, dna])

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



# class Primer_Mixing_LightRun:
#     def __init__(self, Protocol, Name, Metadata, DNA, DNA_Source_Wells, Primers, Primer_Source_Wells,
#     Destination_Contents, primer_plate_is_DNA_plate = False,
#     DNA_Source_Type = "labcyte384pp_384_wellplate_65ul", Primer_Source_Type = "labcyte384pp_384_wellplate_65ul", Destination_Type = "3dprinted_24_tuberack_1500ul",
#     Starting_20uL_Tip = "A1", API = "2.10", Simulate = False):
#
#         #####################
#         # Protocol Metadata #
#         #####################
#         self._protocol = Protocol
#         self.Name = Name
#         self.Metadata = Metadata
#         self._simulate = Simulate
#         self.custom_labware_dir = "../Custom_Labware/"
#
#         if not Simulate == "deprecated":
#             print("Simulate no longer needs to be specified and will soon be removed.")
#
#         ########################################
#         # User defined aspects of the protocol #
#         ########################################
#         self.primer_plate_is_dna_plate = primer_plate_is_DNA_plate
#
#         ####################
#         # Source materials #
#         ####################
#         ## Pipette Tips ##
#         self._20uL_tip_type = "opentrons_96_tiprack_20ul"
#         self.starting_20uL_tip = Starting_20uL_Tip
#         ## DNA samples ##
#         self.dna = DNA
#         self.dna_source_wells = DNA_Source_Wells
#         self.dna_source_type = DNA_Source_Type
#         ## Primer samples ##
#         self.primers = Primers
#         self.primer_source_wells = Primer_Source_Wells
#         self.primer_source_type = Primer_Source_Type
#
#         #######################
#         # Destination Labware #
#         #######################
#         self.destination_type = Destination_Type
#         self.destination_contents = Destination_Contents
#
#         ###############
#         # Robot Setup #
#         ###############
#         self._p20_type = "p20_single_gen2"
#         self._p20_position = "left"
#
#     def run(self):
#         # Determine how many tips will be needed
#         # this will be twice the length of destination contents
#         # one tip for DNA, one tip for primer - per destination
#         tips_needed_20uL = 2 * len(self.destination_contents)
#         # Calculate number of racks needed - account for the first rack missing some tips
#         racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
#         # Load tip racks
#         tip_racks_20uL = []
#         for rack20 in range(0, racks_needed_20uL):
#             tip_racks_20uL.append(self._protocol.load_labware(self._20uL_tip_type, _OTProto.next_empty_slot(self._protocol)))
#         # Set up pipettes
#         p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
#         p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
#
#         # User prompts for number of tip boxes required, and locations of the tip boxes
#         self._protocol.pause("This protocol needs {} 20 uL tip racks".format(racks_needed_20uL))
#         for tip_box_index in range(0, len(tip_racks_20uL)):
#             self._protocol.pause("Place 20 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_20uL[tip_box_index].parent))
#
#         # Load all other labware
#         if not self.primer_plate_is_dna_plate:
#             ## Find the next empty deck slot
#             dna_labware_slot = _OTProto.next_empty_slot(self._protocol)
#             ## Load the DNA labware
#             dna_labware = _OTProto.load_labware(self._protocol, self.dna_source_type, dna_labware_slot, self.custom_labware_dir, label = "DNA Plate")
#
#             ## Find the next empty deck slot
#             primer_labware_slot = _OTProto.next_empty_slot(self._protocol)
#             ## Load the primer labware
#             primer_labware = _OTProto.load_labware(self._protocol, self.primer_source_type, primer_labware_slot, self.custom_labware_dir, label = "Primer Plate")
#         else:
#             ## Find the next empty deck slot
#             dna_labware_slot = _OTProto.next_empty_slot(self._protocol)
#             ## Load the DNA labware
#             dna_labware = _OTProto.load_labware(self._protocol, self.dna_source_type, dna_labware_slot, self.custom_labware_dir, label = "DNA and Primer Plate")
#             primer_labware = dna_labware
#
#         destination_labware_slot = _OTProto.next_empty_slot(self._protocol)
#         destination_labware = _OTProto.load_labware(self._protocol, self.destination_type, destination_labware_slot, self.custom_labware_dir, label = "Tube Rack")
#
#         # Store DNA locations
#         DNA = _BMS.Liquids()
#         for d,w in zip(self.dna, self.dna_source_wells):
#             DNA.add_liquid(d, dna_labware, w)
#         # Store primer locations
#         Primers = _BMS.Liquids()
#         for p,w in zip(self.primers, self.primer_source_wells):
#             Primers.add_liquid(p, primer_labware, w)
#
#         # specify wells to be used for LightRun tubes
#         destination_plate_wells_by_row = []
#         for r in destination_labware.rows():
#             for w in r:
#                 destination_plate_wells_by_row.append(w)
#         destination_range = destination_plate_wells_by_row[0:len(self.destination_contents)]
#
#         # User prompts for number of tip boxes required, and locations of the tip boxes
#         self._protocol.pause("This protocol needs {} 20 uL tip racks".format(racks_needed_20uL))
#         for tip_box_index in range(0, len(tip_racks_20uL)):
#             self._protocol.pause("Place 20 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_20uL[tip_box_index].parent))
#
#         # Prompt user to check all liquids are correctly placed
#         self._protocol.pause("This protocol needs {} 1.5mL tubes".format(len(destination_range)))
#         # one tube rack has been loaded for the destination plate, maximum number of samples is 24
#         if len(destination_range) > 24:
#             self._protocol.pause("This protocol requires more than 24 tubes. Please limit the protocol to 24 tubes only.")
#
#         # Prompt user to load DNA
#         for l in DNA.get_all_liquids():
#             liquid_name = l
#             liquid_labware = DNA.get_liquid_labware(liquid_name)
#             liquid_well = DNA.get_liquid_well(liquid_name)
#             self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))
#         # Prompt user to load Primers
#         for l in Primers.get_all_liquids():
#             liquid_name = l
#             liquid_labware = Primers.get_liquid_labware(liquid_name)
#             liquid_well = Primers.get_liquid_well(liquid_name)
#             self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))
#
#         ##################################
#         # Start of protocol instructions #
#         ##################################
#
#         # Add DNA to destination tubes
#         for i in range(len(destination_range)):
#             # extract liquid contents from list
#             contents = self.destination_contents[i]
#             contents_dna = contents[0] # DNA
#             contents_primer = contents[1] # primer
#             # get dna source well
#             dna_labware = DNA.get_liquid_labware(contents_dna)
#             dna_well = DNA.get_liquid_well(contents_dna)
#             dna_source = dna_labware.wells_by_name()[dna_well]
#             # get forward primer well
#             primer_labware = Primers.get_liquid_labware(contents_primer)
#             primer_well = Primers.get_liquid_well(contents_primer)
#             primer_source = primer_labware.wells_by_name()[primer_well]
#             # get destination well
#             destination = destination_range[i]
#
#             # transfer 5uL of DNA to each tube
#             p20.transfer(5, dna_source, destination)
#             # transfer 5uL of primer to each tube
#             # p20.transfer(5, primer_source, destination, mix_after = (5, 5)) # mix after 5 times with 5uL
