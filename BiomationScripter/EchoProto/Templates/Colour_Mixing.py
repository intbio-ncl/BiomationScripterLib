import BiomationScripter as _BMS
import BiomationScripter.EchoProto as _EchoProto
import math
from typing import List, NewType, Dict, Tuple, Union
from decimal import Decimal


class Template(_EchoProto.EchoProto_Template):
    def __init__(
        self,
        Source_Colours: List[str],
        Final_Volume: float,
        Mixing_Ratios: List[str],
        Permutations: bool = False,
        Merge: bool = True,
        **kwargs # This will make the superclass arguments available to `Colour_Mixing` as keyword arguments
    ):
        super().__init__(**kwargs) # This passes the keyword arguments to the superclass

        #######################
        # User Defined Values #
        #######################
        self.source_colours = Source_Colours
        self.final_volume = Final_Volume # uL
        self.mixing_ratios = Mixing_Ratios
        self.permutations = Permutations
        self.merge = Merge

    def run(self):

        # Set up an empty list in which the colour mixtures required will be added
        Colour_Mixtures = []

        # Iterate through the list of source colours provided to create the list of mixtures.
        for colour_1 in self.source_colours:
            for colour_2 in self.source_colours:
                # Ignore situations where colour_1 and colour_2 are the same
                if colour_1 == colour_2:
                    continue
                # Unless permutations has been set to `True`, ignore situations where...
                # ...the same colours have already been mixed, just in a different order
                elif not self.permutations and [colour_2, colour_1] in Colour_Mixtures:
                    continue
                else:
                    # Add the two colours to the list of mixtures to prepare
                    Colour_Mixtures.append([colour_1, colour_2])

        # Here, we'll print to OUT all of the mixtures which will be prepared
        for c in Colour_Mixtures:
            print(c)

        # Determine how may different mixtures will be prepared
        Number_Of_Mixtures = len(Colour_Mixtures) * len(self.mixing_ratios)

        # Use BMS.Create_Labware_Needed to ensure enough destination plates are available
        Extra_Destination_Plates_Required = _BMS.Create_Labware_Needed(
            Labware_Format = self.destination_plate_layouts[0],
            N_Wells_Needed = Number_Of_Mixtures,
            N_Wells_Available = "All",
            Return_Original_Layout = False
        )

        # If any extra plates were created, add them using the `add_destination_layout` method defined by the superclass
        for plate_layout in Extra_Destination_Plates_Required:
            self.add_destination_layout(plate_layout)

        # Add content to the destination plate(s)

        # A counter is used to iterate through the destination plates (if more than one)
        Destination_Plate_Index = 0

        for mixture in Colour_Mixtures:
            # Get the current destination plate
            Destination_Plate = self.destination_plate_layouts[Destination_Plate_Index]

            # Get the colours
            colour_1 = mixture[0]
            colour_2 = mixture[1]

            # For every ratio defined by the user
            for ratio in self.mixing_ratios:
                # Get the ratio for each colour
                colour_1_ratio = float(ratio.split(":")[0])
                colour_2_ratio = float(ratio.split(":")[1])

                # Get the volumes to add for each colour
                colour_1_volume = (colour_1_ratio/(colour_1_ratio + colour_2_ratio)) * self.final_volume
                colour_2_volume = (colour_2_ratio/(colour_1_ratio + colour_2_ratio)) * self.final_volume

                # Get the next empty well in the destination plate
                well = Destination_Plate.get_next_empty_well()
                # If there are no empty wells left, iterate to the next plate and try again
                if not well:
                    Destination_Plate_Index += 1
                    Destination_Plate = self.destination_plate_layouts[Destination_Plate_Index]
                    well = Destination_Plate.get_next_empty_well()

                # Add content to the plate
                Destination_Plate.add_content(
                    Well = well,
                    Reagent = colour_1,
                    Volume = colour_1_volume
                )
                Destination_Plate.add_content(
                    Well = well,
                    Reagent = colour_2,
                    Volume = colour_2_volume
                )

        self.create_picklists()
