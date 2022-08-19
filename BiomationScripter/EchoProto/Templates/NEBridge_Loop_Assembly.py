import BiomationScripter as _BMS
import BiomationScripter.EchoProto as _EchoProto
import math
from typing import List, NewType, Dict, Tuple, Union
from decimal import Decimal


class Template(_EchoProto.EchoProto_Template):
    def __init__(self,
        Enzyme: str,
        # Buffer: str,
        Volume: float,
        Assemblies: List[_BMS.Assembly],
        Backbone_to_Part: List[str] = ["1:1"],
        Repeats: int = 1,
        DNA_Source_Concentration = 10, # fmol
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

        # Deal with assemblies as a list or a list of the new object
        self.assemblies = []
        for assembly in Assemblies:
            if type(Assemblies[0]) == _BMS.Assembly:
                self.assemblies.append([assembly.backbone, assembly.parts])
            else:
                self.assemblies.append(assembly)

        ##############################################
        # Default reagent amounts for 5 uL reactions #
        ##############################################
        self.__default_volume = 5
        self._enzyme_amount = 0.35
        self._nebridge_amount = 1.65

        ##########################################
        # Default DNA amounts for 5 uL reactions #
        ##########################################
        # For 1:1 ratio, and source concentration of 20 fmol/uL
        self._backbone_amount = (0.25 * (20/DNA_Source_Concentration))
        self._part_amount = (0.25 * (20/DNA_Source_Concentration))

        #########################
        # Default reagent names #
        #########################
        self.nebridge = "NEBridge"
        self.water = "Water"

    def run(self):

        ###################################################
        # Calculate number of destination plates required #
        ###################################################
        # Determine final number of assemblies, and hence number of destination wells required
        n_assemblies = (len(self.assemblies) * len(self.ratios)) * self.repeats

        # Create the number of destination plates needed as layout objects
        extra_destination_layouts = _BMS.Create_Labware_Needed(
            Labware_Format = self.destination_plate_layouts[0],
            N_Wells_Needed = n_assemblies,
            N_Wells_Available = len(self.destination_plate_layouts[0].get_available_wells()),
            Return_Original_Layout = False
        )

        # Add any extra destination plates needed
        for layout in extra_destination_layouts:
            layout.set_available_wells()
            self.add_destination_layout(layout)

        ######################################
        # Calculate reagent volumes required #
        ######################################
        # Volume factor is the difference between the default volume (5 uL) and the user-define final volume
        volume_factor = self.volume/self.__default_volume
        # Use the volume factor to calculate the reagent volumes
        enzyme_amount = self._enzyme_amount*volume_factor
        nebridge_amount = self._nebridge_amount*volume_factor
        # Store the total amount of reagents per reaction for later use
        reagent_amount = enzyme_amount + nebridge_amount

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
                        current_destination_plate.add_content(current_destination_well, self.enzyme, enzyme_amount)
                        current_destination_plate.add_content(current_destination_well, self.nebridge, nebridge_amount)
                        backbone_name = assembly[0]
                        well_label = "{}: ".format(backbone_name)
                        current_destination_plate.add_content(current_destination_well, backbone_name, backbone_amount)
                        DNA_part_names = assembly[1]
                        for part_name in DNA_part_names:
                            current_destination_plate.add_content(current_destination_well, part_name, part_amount)
                            well_label += "{} + ".format(part_name)

                        well_label = "{}{}{}".format(well_label[:-2], ratio,rep)

                        current_destination_plate.add_well_label(current_destination_well, well_label)
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
