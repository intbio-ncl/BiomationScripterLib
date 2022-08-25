import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple

class Template(_OTProto.OTProto_Template):
    def __init__(self,
        Sources: List[ Union[_BMS.Labware_Layout, str] ],
        Destinations: List[ Union[_BMS.Labware_Layout, str] ],
        **kwargs
    ):
        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.source_layouts = []
        self.destination_layouts = []

        for source in Sources:
            if type(source) is str:
                self.source_layouts.append(_BMS.Import_Labware_Layout(source))
            else:
                self.source_layouts.append(source)

        for destination in Destinations:
            if type(destination) is str:
                self.destination_layouts.append(_BMS.Import_Labware_Layout(destination))
            else:
                self.destination_layouts.append(destination)

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

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
