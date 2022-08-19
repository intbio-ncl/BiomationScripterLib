import BiomationScripter as _BMS
import BiomationScripter.EchoProto as _EchoProto
import math
from typing import List, NewType, Dict, Tuple, Union
from decimal import Decimal


class Template(_EchoProto.EchoProto_Template):
    def __init__(self,
        Volume: float,
        Reactions: Tuple[str, str, str],
        Polymerase: str = None,
        Polymerase_Buffer: str = None,
        Polymerase_Buffer_Stock_Conc: float = None,
        Master_Mix: str = None,
        Master_Mix_Stock_Conc = None,
        Repeats: int = 1,
        DNA_Amounts = None,
        **kwargs
    ):

        super().__init__(**kwargs)

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.volume = Volume # uL
        self.repeats = Repeats
        self.reactions = Reactions
        self.polymerase = Polymerase
        self.buffer = Polymerase_Buffer
        self.master_mix = Master_Mix
        self.master_mix_stock_conc = Master_Mix_Stock_Conc
        self.buffer_stock_conc = Polymerase_Buffer_Stock_Conc

        if not self.master_mix:
            if not self.polymerase or not self.buffer:
                raise _BMS.BMSTemplateError("If mastermix is not specified, then the polymerase and buffer to use must be given.")

        ###########################
        # Default reagent amounts #
        ###########################
        self.__default_volume = 5

        self._dNTPs_amount = 0.1
        self._polymerase_amount = 0.05
        if self.master_mix:
            if not self.master_mix_stock_conc:
                raise _BMS.BMSTemplateError("If master mix is specified, a stock concentration (e.g. 2x) must also be given.")
            else:
                self._master_mix_amount = self.__default_volume / self.master_mix_stock_conc
        else:
            self._master_mix_amount = None
            self._buffer_amount = self.__default_volume / self.buffer_stock_conc

        ##################################
        # Default DNA and primer amounts #
        ##################################
        # Default DNA amounts in uL for 5 uL reactions, and 1 - 1000 ng/uL stock concentration
        self._default_dna_amount = 1 # uL
        if not DNA_Amounts:
            self.dna_amounts = [self._default_dna_amount * (self.volume/self.__default_volume)]
        else:
            self.dna_amounts = DNA_Amounts

        # Default primer amounts in uL for 5 uL reactions, and 10 μM stock concentration
        self.primer_amount = 0.25

        #########################
        # Default reagent names #
        #########################
        self.dNTPs = "dNTPs"
        self.water = "Water"

    def run(self):

        ###################################################
        # Calculate number of destination plates required #
        ###################################################
        # Determine final number of reactions, and hence number of destination wells required
        n_reactions = len(self.reactions) * self.repeats * len(self.dna_amounts)

        # Create the number of destination plates needed as layout objects
        extra_destination_layouts = _BMS.Create_Labware_Needed(
            Labware_Format = self.destination_plate_layouts[0],
            N_Wells_Needed = n_reactions,
            N_Wells_Available = len(self.destination_plate_layouts[0].get_available_wells()),
            Return_Original_Layout = False
        )

        # Add any extra destination plates needed
        for layout in extra_destination_layouts:
            self.add_destination_layout(layout)

        ######################################
        # Calculate reagent volumes required #
        ######################################
        # Volume factor is the difference between the default volume (5 uL) and the user-define final volume
        volume_factor = self.volume/self.__default_volume

        # Use the volume factor to calculate the reagent volumes
        primer_amount = self.primer_amount * volume_factor



        ########################################
        # Add liquids to destination layout(s) #
        ########################################
        # Counter to track which destination plate is in use
        destination_plate_index = 0
        # Counter to track which destination well is in use
        destination_well_index = 0

        # For every reaction
        for reaction in self.reactions:
            for dna_amount in self.dna_amounts:
                # Determine if a mastermix is being used
                if self.master_mix:
                    master_mix_amount = self._master_mix_amount * volume_factor
                    reagent_amount = master_mix_amount + dna_amount + (2 * primer_amount)
                else:
                    dNTPs_amount = self._dNTPs_amount * volume_factor
                    buffer_amount = self._buffer_amount * volume_factor
                    polymerase_amount = self._polymerase_amount * volume_factor
                    reagent_amount = float(Decimal(str(dNTPs_amount)) + Decimal(str(buffer_amount)) + Decimal(str(polymerase_amount)) + Decimal(str(dna_amount)) + (2 * Decimal(str(primer_amount))))

                water_amount = self.volume - reagent_amount

                for rep in range(0, self.repeats):
                    # Get the current destination plate and well
                    current_destination_plate = self.destination_plate_layouts[destination_plate_index]
                    current_destination_well = current_destination_plate.available_wells[destination_well_index]

                    # Add the reagents, water, and DNA to the destinaton plate
                    try:
                        current_destination_plate.add_content(current_destination_well, self.water, water_amount)
                        current_destination_plate.add_content(current_destination_well, reaction[0], dna_amount)
                        current_destination_plate.add_content(current_destination_well, reaction[1], primer_amount)
                        current_destination_plate.add_content(current_destination_well, reaction[2], primer_amount)

                        if self.master_mix:
                            current_destination_plate.add_content(current_destination_well, self.master_mix, master_mix_amount)
                        else:
                            current_destination_plate.add_content(current_destination_well, self.dNTPs, dNTPs_amount)
                            current_destination_plate.add_content(current_destination_well, self.buffer, buffer_amount)
                            current_destination_plate.add_content(current_destination_well, self.polymerase, polymerase_amount)

                        # Label the well
                        current_destination_plate.add_well_label(current_destination_well, "{}-{}-{}-DNA_Vol({})-{}".format(reaction[0], reaction[1], reaction[2], dna_amount, rep))
                    # Raise a more relevant error message if NegativeVolumeError occurs
                    except _BMS.NegativeVolumeError:
                        raise _BMS.NegativeVolumeError("This reaction is above the reaction volume: {}".format(reaction))

                    # Iterate to the next destination well
                    destination_well_index += 1
                    # Check if the current destinaton plate is full
                    if destination_well_index - 1 == len(current_destination_plate.available_wells):
                        # If so, iterate to the first well of the next destination plate
                        destination_plate_index += 1
                        destination_well_index = 0

        # Sanity check
        for dest in self.destination_plate_layouts:
            for well in dest.get_occupied_wells():
                reagents = dest.get_liquids_in_well(well)
                if not sum([dest.get_volume_of_liquid_in_well(reagent, well) for reagent in reagents]) == self.volume:
                    raise _BMS.BMSTemplateError("Internal Calculation Error. Please raise as an issue on the GitHub.")

        # Generate the picklists
        self.create_picklists()
