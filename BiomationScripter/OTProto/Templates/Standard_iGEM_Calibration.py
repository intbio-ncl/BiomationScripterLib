import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple


class Calibrant:
    def __init__(self, Name, Stock_Conc, Initial_Conc, Solvent):
        self.name = Name
        self.stock_conc = Stock_Conc
        self.initial_conc = Initial_Conc
        self.solvent = Solvent

class Template(_OTProto.OTProto_Template):
    # Always do microspheres
    # Any amount of other calibrants
    def __init__(self,
        Calibrants: List[Calibrant],
        Calibrants_Stock_Concs: List[float],
        Calibrants_Initial_Concs: List[float],
        Calibrants_Solvents: List[str],
        Calibrant_Aliquot_Volumes: List[float],
        Solvent_Aliquot_Volumes: List[float],
        Volume_Per_Well: float,
        Repeats: int,
        Calibrant_Labware_Type: str,
        Solvent_Labware_Type: str,
        Destination_Labware_Type: str,
        Trash_Labware_Type: str,
        Solvent_Mix_Before = None,
        Solvent_Mix_After = None,
        Solvent_Source_Touch_Tip: bool = True,
        Solvent_Destination_Touch_Tip: bool = True,
        Solvent_Move_After_Dispense = "well_bottom",
        Solvent_Blowout = "destination well",
        First_Dilution_Mix_Before = (10, "transfer_volume"),
        First_Dilution_Mix_After = (10, "transfer_volume"),
        First_Dilution_Source_Touch_Tip: bool = True,
        First_Dilution_Destination_Touch_Tip: bool = True,
        First_Dilution_Move_After_Dispense = None,
        First_Dilution_Blowout = "destination well",
        Dilution_Mix_Before = (10, "transfer_volume"),
        Dilution_Mix_After = (10, "transfer_volume"),
        Dilution_Source_Touch_Tip: bool = True,
        Dilution_Destination_Touch_Tip: bool = True,
        Dilution_Move_After_Dispense = None,
        Dilution_Blowout = "destination well",
        Mix_Speed_Multipler: float = 2,
        Aspirate_Speed_Multipler: float = 1,
        Dispense_Speed_Multipler: float = 1,
        Blowout_Speed_Multiplier: float = 1,
        Dead_Volume_Proportion: float = 0.95,
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
                    source_layout_type = labware_type
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
