import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple

class Template(_OTProto.OTProto_Template):
    def __init__(self,
        DNA: List[str],
        DNA_Source_Type: str,
        DNA_Source_Wells: List[str],
        Primers: List[str],
        Primer_Source_Wells: List[str],
        Primer_Source_Type: str,
        DNA_Primer_Mixtures: List[ List[str] ],
        Destination_Type: str,
        DNA_Volume: float,
        Primer_Volume: float,
        Final_Volume: float,
        Water_Source_Type: Union[str, None],
        Water_Aliquot_Volume: float,
        DNA_Primers_Same_Source: bool = False,
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
            number_water_aliquots = math.ceil(sum(Water_Transfers) / (self.water_aliquot_volume - self.water_aliquot_volume * 0.01))

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
