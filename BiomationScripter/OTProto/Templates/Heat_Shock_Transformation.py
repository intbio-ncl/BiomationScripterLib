import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple


class Template(_OTProto.OTProto_Template):
    def __init__(self,
        DNA_Source_Layouts: List[_BMS.Labware_Layout],
        Competent_Cells_Source_Type: str,
        Transformation_Destination_Type: str,
        Media_Source_Type: str,
        DNA_Volume_Per_Transformation: float,
        Competent_Cell_Volume_Per_Transformation: float,
        Transformation_Final_Volume: float,
        Heat_Shock_Time: int,
        Heat_Shock_Temp: int,
        Media_Aliquot_Volume: float,
        Competent_Cells_Aliquot_Volume: float,
        Wait_Before_Shock: int,
        Replicates: int,
        Heat_Shock_Modules: List[str] = ["temperature module gen2"],
        Cooled_Cells_Modules: List[str] = [],
        Shuffle: Union[Tuple[str, str] , None] = None,
        Patience: int = 1200,
        Cells_Mix_Before = (5,"transfer_volume"),
        Cells_Mix_After = None,
        DNA_Mix_Before = None,
        DNA_Mix_After = (10,"transfer_volume"),
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
        self.shuffle = Shuffle
        self.patience = Patience
        self.cells_mix_before = Cells_Mix_Before
        self.cells_mix_after = Cells_Mix_After
        self.dna_mix_before = DNA_Mix_Before
        self.dna_mix_after = DNA_Mix_After

        self.heat_shock_modules = Heat_Shock_Modules
        self.cooled_cells_modules = Cooled_Cells_Modules

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
        self._tc_module = "Thermocycler Module"

        self._module_positions = [1, 3, 4, 6, 7, 9, 10]

        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

        ################
        # Load Modules #
        ################

        # Load the destination modules
        destination_modules = []

        # Check if the thermocycler will be used - load it first if it will be
        if self._tc_module in self.heat_shock_modules:
            destination_modules.append(self._protocol.load_module(self._tc_module))
            self._module_positions = [1, 3, 4, 6, 10]

        # Then load any remaining destination (heat shock) modules
        for hs_mod in self.heat_shock_modules:
            # Check that it isn't the thermocyler (if applicable)
            if not self._tc_module == hs_mod:
                # Get a suitable deck position
                deck_slot = _OTProto.next_empty_slot(self._protocol)
                while not deck_slot in self._module_positions and not deck_slot in self._module_positions:
                    deck_slot += 1
                    if deck_slot >= 12:
                        raise _BMS.LabwareError("Not enough deck positions on the robot.")
                # Load the module
                destination_modules.append(self._protocol.load_module(hs_mod, deck_slot))

        # Load the source modules
        source_modules = []
        for cc_mod in self.cooled_cells_modules:
            # Get a suitable deck position
            deck_slot = _OTProto.next_empty_slot(self._protocol)
            labware = self._protocol.deck[deck_slot]
            while not deck_slot in self._module_positions:
                deck_slot += 1
                if deck_slot >= 12:
                    raise _BMS.LabwareError("Not enough deck positions on the robot.")
                labware = self._protocol.deck[deck_slot]
                # check that the deck slot is empty
                while labware is not None:
                    deck_slot += 1
                    if deck_slot >= 12:
                        raise _BMS.LabwareError("Not enough deck positions on the robot.")
                    labware = self._protocol.deck[deck_slot]
            # Load the module
            source_modules.append(self._protocol.load_module(cc_mod, deck_slot))

        if len(source_modules) == 0:
            source_modules = None


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
        Cell_Source_Labware, Cell_Source_Locations = _OTProto.calculate_and_load_labware(self._protocol, self.comp_cells_source_type, Cell_Aliquots_Required, modules=source_modules, custom_labware_dir = self.custom_labware_dir)

        # DNA
        DNA_Source_Labware = [
            _OTProto.load_labware_from_layout(
                Protocol = self._protocol,
                Labware_Layout = dl,
                custom_labware_dir = self.custom_labware_dir
            )
            for dl in self.dna_source_layouts
        ]

        layout_labware_mapping = {}

        for layout, labware in zip(self.dna_source_layouts, DNA_Source_Labware):
            layout_labware_mapping[labware] = layout

        DNA_Source_Locations = []

        for layout, labware in zip(self.dna_source_layouts, DNA_Source_Labware):
            DNA_Source_Locations += _OTProto.get_locations(
                Labware = labware,
                Wells = layout.get_occupied_wells()
            )

        # Shuffle DNA locations
        if self.shuffle is not None:
            outD = self.shuffle[0]
            outF = self.shuffle[1]
            DNA_Source_Locations = _OTProto.shuffle_locations(self._protocol, DNA_Source_Locations, outdir=outD, outfile=outF)

        # Media
        # if media arguments are set to None, the media transfer steps are skipped
        if self.media_aliquot_volume is not None:
            Media_Aliquots_Required = math.ceil(sum(Media_Transfer_Volumes)/self.media_aliquot_volume)
            Media_Source_Labware, Media_Source_Locations = _OTProto.calculate_and_load_labware(self._protocol, self.media_source_type, Media_Aliquots_Required, custom_labware_dir = self.custom_labware_dir)

        ############################
        # Load Destination Labware #
        ############################
        Destination_Labware, Destination_Locations = _OTProto.calculate_and_load_labware(self._protocol, self.destination_type, Num_Transformations, modules=destination_modules, custom_labware_dir = self.custom_labware_dir)

        print("Transformation Mapping")
        for dna, destination in zip([f"{layout_labware_mapping[location.parent].get_liquids_in_well(location.well_name)[0]} ({location})" for location in DNA_Source_Locations], Destination_Locations):
            print(f"{dna} -> {destination}")

        ######################
        # User Setup Prompts #
        ######################
        self.tip_racks_prompt()

        for dna_name, location in  zip([layout.get_liquids_in_well(well)[0] for layout in self.dna_source_layouts for well in layout.get_occupied_wells()], DNA_Source_Locations):
            self._protocol.pause("Place DNA Sample {} at {}".format(dna_name, location))

        if self.media_aliquot_volume is not None:
            self._protocol.pause("This protocol uses {} aliquots of {} uL media, located at {}".format(Media_Aliquots_Required, self.media_aliquot_volume, Media_Source_Locations))
        else:
            self._protocol.pause("Media Aliquot Volume was set to None, media transfer steps shall be skipped")
        self._protocol.pause("This protocol uses {} aliquots of {} uL competent cells, located at {}".format(Cell_Aliquots_Required, self.comp_cells_aliquot_volume, Cell_Source_Locations))

        ##########################
        # Liquid handling begins #
        ##########################

        # Set temperature to 4C
        for hs_mod in destination_modules:
            if hs_mod._module.model() == "thermocyclerModuleV1":
                hs_mod.set_block_temperature(4)
                hs_mod.open_lid()
            else:
                hs_mod.start_set_temperature(4)

        if source_modules:
            for cc_mod in source_modules:
                cc_mod.start_set_temperature(4)

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
            mix_after = self.cells_mix_after,
            mix_before = self.cells_mix_before,
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
            mix_after = self.dna_mix_after,
            mix_before = self.dna_mix_before,
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

        for hs_mod in destination_modules:
            if hs_mod._module.model() == "thermocyclerModuleV1":
                # close thermocycler lid
                hs_mod.close_lid()
                # heat shock as user specified
                hs_mod.set_block_temperature(self.heat_shock_temp, hold_time_seconds=self.heat_shock_time)
                # hold at 4 for 2 minutes
                hs_mod.set_block_temperature(4, 120)
                # open the lid
                hs_mod.open_lid()
            else:
                hs_mod.set_temperature(self.heat_shock_temp)
                # Wait for a bit
                self._protocol.delay(seconds = self.heat_shock_time)
                # Cool back to 4
                hs_mod.start_set_temperature(4)

        # Ensure all modules get held at 4c for 2 mins
        for hs_mod in destination_modules:
            if hs_mod._module.model() != "thermocyclerModuleV1":
                timer = 0
                while hs_mod._module.status == "cooling" and timer < self.patience:
                    self._protocol.delay(seconds = 5)
                    timer += 5
        self._protocol.delay(seconds = 120)


        # # Set the temp to heat shock
        # if tc_module is not None:
        #     # close thermocycler lid
        #     tc_module.close_lid()
        #     # heat shock as user specified
        #     tc_module.set_block_temperature(self.heat_shock_temp, hold_time_seconds=self.heat_shock_time)
        #     # hold at 4 for 2 minutes
        #     tc_module.set_block_temperature(4, hold_time_seconds=120)
        #     # open the lid
        #     tc_module.open_lid()
        # else:
        #     destination_module.set_temperature(self.heat_shock_temp)
        #     # Wait for a bit
        #     self._protocol.delay(seconds = self.heat_shock_time)
        #     # Cool back to 4 - protocol won't continue until this is back at 4...
        #     destination_module.set_temperature(4)

        # Add media
        if self.media_aliquot_volume is not None:
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
