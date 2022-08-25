import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple


class Template(_OTProto.OTProto_Template):
    def __init__(self,
        Final_fmol: float,
        DNA: List[str],
        DNA_Concentration: List[float],
        DNA_Length: List[int],
        DNA_Source_Type: str,
        Keep_In_Current_Wells: bool,
        Water_Source_Labware_Type: str,
        Water_Aliquot_Volume: float,
        DNA_Source_Wells: list[str] = None,
        Final_Volume: float = None,
        Current_Volume: List[float] = None,
        Destination_Labware_Type: str = None,
        Destination_Labware_Wells: List[str] = None,
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.final_fmol = Final_fmol
        self._keep_in_current_wells = Keep_In_Current_Wells
        self.final_volume = Final_Volume

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
        self.water_aliquot_volume = Water_Aliquot_Volume

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
            aliquots_required = math.ceil(total_water_required/self.water_aliquot_volume)
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
                final_volume = self.final_volume
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
            aliquots_required = math.ceil(total_water_required/self.water_aliquot_volume)
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

            self._protocol.pause("This protocol uses {} aliquots of {} uL water, located at {}".format(len(water_source_locations), self.water_aliquot_volume, water_source_locations))

            for dna, location, volume in zip(self.dna, DNA_Locations, dna_to_add):
                self._protocol.pause("Place DNA sample {} at {}. {} uL will be used".format(dna, location, volume))
            # Liquid handling begins #
            ## Dispense water into DNA source wells and mix
            _OTProto.dispense_from_aliquots(self._protocol, water_to_add, water_source_locations, destination_locations, new_tip = True)

            ## Add DNA to water
            _OTProto.transfer_liquids(self._protocol, dna_to_add, DNA_Locations, destination_locations, new_tip = True, mix_after = (5,"transfer_volume"))
