import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple

class Template(_OTProto.OTProto_Template):
    def __init__(self,
        Cells: List[str],
        Cells_Source_Wells: List[str],
        Cells_Source_Type: str,
        Agar_Labware_Type: str,
        Plating_Volumes: List[float],
        Repeats: int,
        Media_Source_Type: Union[str, None] = None,
        Media_Aliquot_Volume: Union[float, None] = None,
        Dilution_Factors: List[int] = [1],
        Dilution_Volume: Union[float, None] = None,
        Dilution_Labware_Type: Union[str, None] = None,
        Pause_Before_Plating: bool = True,
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
