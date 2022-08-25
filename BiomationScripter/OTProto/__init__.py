from fileinput import filename
import json
import BiomationScripter as _BMS
import math
from opentrons import protocol_api
import warnings
from random import shuffle
import datetime
from typing import Union

BiomationScripter_Install_Dir = "/var/lib/jupyter/notebooks/Packages/BiomationScripterLib/BiomationScripter/OTProto/"
Pre_Loaded_Custom_Labware_Dir = BiomationScripter_Install_Dir + "Opentrons_Custom_Labware_Definitions/"

########################

class OTProto_Template:
    def __init__(self,
        Protocol: protocol_api,
        Name: str,
        Metadata,
        Custom_Labware_Dir: str = "../Custom_Labware/",
        Starting_20uL_Tip: str = "A1",
        Starting_300uL_Tip: str = "A1",
        Starting_1000uL_Tip: str = "A1"
    ):
        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self.custom_labware_dir = Custom_Labware_Dir

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self.tip_types = {
            "p20": "opentrons_96_tiprack_20ul",
            "p300": "opentrons_96_tiprack_300ul",
            "p1000": "opentrons_96_tiprack_1000ul"
        }
        self.starting_tips = {
            "p20": Starting_20uL_Tip,
            "p300": Starting_300uL_Tip,
            "p1000": Starting_1000uL_Tip
        }

        self.tips_needed = {
            "p20": 0,
            "p300": 0,
            "p1000": 0
        }

        ###############
        # Robot Setup #
        ###############
        self._pipettes = {
            "left": "p20_single_gen2",
            "right": "p300_single_gen2"
        }
        self.__pipettes_loaded = False

    def pipettes_loaded(self):
        return(self.__pipettes_loaded)

    def custom_labware_directory(self, Directory):
        self.custom_labware_dir = Directory

    def pipette_config(self, Pipette_Type, Position):
        if self.__pipettes_loaded:
            raise _BMS.BMSTemplateError("Pipettes have already been loaded. Please modify pipette configuration before loading pipettes. Changes to configuration have NOT been saved.")

        if not Position.lower() in ["left", "right"]:
            raise _BMS.RobotConfigurationError("{} is an invalid pipette positon. Please specify either 'right' or 'left'".format(Position))

        self._pipettes[Position.lower()] = Pipette_Type


    def load_pipettes(self):
        for pipette_position in self._pipettes.keys():
            if pipette_position in self._protocol.loaded_instruments.keys():
                warnings.warn("Pipette already loaded in {} position so loading was skipped".format(pipette_position))
                continue
            pipette = self._pipettes[pipette_position]
            self._protocol.load_instrument(pipette, pipette_position)
        self.__pipettes_loaded = True

    def tip_type(self, Pipette, Tip_Type):
        try:
            self.tip_types[Pipette] = Tip_Type
        except KeyError:
            raise _BMS.RobotConfigurationError("{} is not a known pipette class. Please specify either p20, p300, or p1000".format(Pipette))

    def starting_tip_position(self, Pipette, Tip_Position):
        try:
            self.starting_tips[Pipette] = Tip_Position
        except:
            raise _BMS.RobotConfigurationError("{} is not a known pipette class. Please specify either p20, p300, or p1000".format(Pipette))

    def add_tip_boxes_to_pipettes(self):
        for pipette_type in self.tips_needed.keys():
            # Get the current pipette
            pipette = get_pipette(self._protocol, pipette_type)
            # Get the amount of tips needed for this pipette
            tips_needed = self.tips_needed[pipette_type]
            if tips_needed == 0:
                continue
            elif pipette == None and not self.tips_needed[pipette_type] == 0:
                raise _BMS.RobotConfigurationError("Tips have been specifed for {}, however this pipette type has not been loaded. Please ensure pipettes have been loaded and check your protocol.".format(pipette_type))
            else:
                tip_boxes_needed = tip_racks_needed(tips_needed, self.starting_tips[pipette_type])
                tip_type = self.tip_types[pipette_type]
                for tip_box in range(0, tip_boxes_needed):
                    tip_box_deck_slot = next_empty_slot(self._protocol)
                    tip_box = load_labware(self._protocol, tip_type, tip_box_deck_slot)

                    pipette.tip_racks.append(tip_box)

                pipette.starting_tip = pipette.tip_racks[0].well(self.starting_tips[pipette_type])

    def calculate_and_add_tips(self, Transfer_Volumes, New_Tip):
        Tips_20uL, Tips_300uL, Tips_1000uL = calculate_tips_needed(self._protocol, Transfer_Volumes, new_tip = New_Tip)
        self.tips_needed["p20"] += Tips_20uL
        self.tips_needed["p300"] += Tips_300uL
        self.tips_needed["p1000"] += Tips_1000uL

    def tip_racks_prompt(self):
        if not get_p20(self._protocol) == None:
            self._protocol.pause("This protocol uses {} 20 uL tip boxes".format(tip_racks_needed(self.tips_needed["p20"], self.starting_tips["p20"])))
        if not get_p300(self._protocol) == None:
            self._protocol.pause("This protocol uses {} 300 uL tip boxes".format(tip_racks_needed(self.tips_needed["p300"], self.starting_tips["p300"])))
        if not get_p1000(self._protocol) == None:
            self._protocol.pause("This protocol uses {} 1000 uL tip boxes".format(tip_racks_needed(self.tips_needed["p1000"], self.starting_tips["p1000"])))

    def run(self):
        #################
        # Load pipettes #
        #################
        self.load_pipettes()

    def run_as_module(self, Parent):
        #############################
        # Duplicate parent settings #
        #############################
        self.custom_labware_dir = Parent.custom_labware_dir
        self.tip_types = Parent.tip_types
        self._pipettes = Parent._pipettes
        self.__pipettes_loaded = True

        #############################
        # Get updated starting tips #
        #############################
        for pipette_type in self.starting_tips:
            pipette = get_pipette(self._protocol, pipette_type)
            if pipette:
                last_tip_rack = pipette.tip_racks[-1]
                next_tip_in_rack = last_tip_rack.next_tip().well_name
                self.starting_tips[pipette_type] = next_tip_in_rack

        ############################
        # Clear deck and tip racks #
        ############################
        for position in self._protocol.deck:
            if position == 12:
                # This is needed to stop the OT2 from deleting the waste bin
                # If the waste bin is deleted, there is a chance the tip will crash into
                # the side of it...
                continue
            del self._protocol.deck[position]

        # Clear the tip racks stored on each loaded pipette
        # This stops tip racks from being duplicated
        # Duplicated tip racks can cause the OT2 to try and use now-empty racks
        for pipette_type in self.tip_types:
            pipette = get_pipette(self._protocol, pipette_type)
            if pipette:
                pipette.tip_racks = []

        self.run()

########################

def get_locations(Labware, Wells, Direction = "Horizontal", Box = False):
    # Argument Direction is ignored is Wells is a list of wells
    ## It is only used if Wells is a well range (e.g. A1:H4)
    if not type(Wells) == list:
        if not ":" in Wells:
            Wells = [Wells]
        else:
            Wells = _BMS.well_range(
                        Wells = Wells,
                        Labware_Format = [len(Labware.rows()), len(Labware.columns())],
                        Direction = Direction,
                        Box = Box
            )

    Locations = []
    for well in Wells:
        Locations.append(Labware.wells_by_name()[well])

    return(Locations)

def get_pipette(Protocol, Pipette):
    if Pipette == "p20":
        return(get_p20(Protocol))
    elif Pipette == "p300":
        return(get_p300(Protocol))
    elif Pipette == "p1000":
        return(get_p1000(Protocol))
    else:
        raise _BMS.RobotConfigurationError("{} is not a known pipette class. Please specify either p20, p300, or p1000".format(Pipette))

def select_pipette_by_volume(Protocol, Volume):

    # Check which pipettes are available - any unavailable will return None
    p20 = get_p20(Protocol)
    p300 = get_p300(Protocol)
    p1000 = get_p1000(Protocol)

    if Volume < 1:
        raise _BMS.RobotConfigurationError("A volume of {} was specified. Cannot transfer less than 1 uL.".format(Volume))
    elif Volume < 20 and p20:
        return(p20)
    elif Volume == 20 and p20:
        return(p20)
    elif Volume == 20 and not p20:
        return(p300)
    elif Volume > 20 and Volume <= 300 and p300:
        return(p300)
    elif Volume > 300 and p1000:
        return(p1000)
    elif Volume >= 100 and not p300 and p1000:
        return(p1000)
    elif Volume > 300 and not p1000 and p300:
        return(p300)
    elif p20 and not p300 and not p1000:
        return(p20)
    else:
        raise _BMS.RobotConfigurationError("A suitable pipette is not loaded to transfer {} uL.\n Currently loaded pipettes:\n{}".format(Volume, Protocol._instruments))

def set_location_offset_top(Locations, Offset):
    # Check if a list of locations is given. If only one location is provided in non-list format, put it into a list
    if not type(Locations) == list:
        Locations = [Locations]

    Offset_Locations = []
    # For each location provided, apply the offset and add to Offset_Locations
    for location in Locations:
        Offset_Locations.append(location.top(Offset))

    return(Offset_Locations)

def set_location_offset_bottom(Locations, Offset):
    # Check if a list of locations is given. If only one location is provided in non-list format, put it into a list
    if not type(Locations) == list:
        Locations = [Locations]

    Offset_Locations = []
    # For each location provided, apply the offset and add to Offset_Locations
    for location in Locations:
        Offset_Locations.append(location.bottom(Offset))

    return(Offset_Locations)

def transfer_liquids(Protocol, Transfer_Volumes, Source_Locations, Destination_Locations, new_tip = True, mix_after = None, mix_before = None, mix_speed_multiplier = 1, aspirate_speed_multiplier = 1, dispense_speed_multiplier = 1, blowout_speed_multiplier = 1, touch_tip_source = False, touch_tip_destination = False, blow_out = False, blowout_location = "destination well", move_after_dispense = None):

    if not type(Transfer_Volumes) == list:
        Transfer_Volumes = [Transfer_Volumes]
    if not type(Source_Locations) == list:
        Source_Locations = [Source_Locations]
    if not type(Destination_Locations) == list:
        Destination_Locations = [Destination_Locations]

    # if not len(Transfer_Volumes) == len(Source_Locations) or not len(Transfer_Volumes) == len(Destination_Locations):
    #     raise ValueError("The number of transfer volumes, source locations, and destination locations are not the same.")

    # Get the smallest non-zero volume to transfer
    if Transfer_Volumes.count(0) == 0:
        min_transfer = min(Transfer_Volumes)
    else:
        temp_Transfer_Volumes = [tv for tv in Transfer_Volumes if not tv == 0]
        min_transfer = min(temp_Transfer_Volumes)

    # Get the largest volume to transfer
    max_transfer = max(Transfer_Volumes)

    # Check that the correct pipettes are available #
    p20 = get_p20(Protocol)
    p300 = get_p300(Protocol)
    p1000 = get_p1000(Protocol)

    # Modify the blowout flow rate (if needed)
    for pipette in [p20, p300, p1000]:
        if pipette:
            pipette.flow_rate.blow_out *= blowout_speed_multiplier

    if not p20 and not p300 and not p1000:
        raise ValueError("No pipettes have been loaded")

    for transfer_volume in Transfer_Volumes:
        if transfer_volume == 0:
            continue
        if transfer_volume < 20 and not p20:
            raise ValueError("p20 pipette is required, but has not been loaded")
        if transfer_volume == 20 and (not p20 and not p300):
            raise ValueError("p20 or p300 pipette is required, but neither have been loaded")
        if (transfer_volume <= 100 and transfer_volume > 20) and not p300:
            raise ValueError("p300 pipette is required, but has not been loaded")
        if transfer_volume <=300 and (not p300 and not p1000):
            raise ValueError("p300 or p1000 pipette is required, but neither have been loaded")

    ################################
    # Liquid Handling Instructions #
    ################################

    # If the same tip will be used for all transfers, select it here
    if not new_tip:
        ## May need to load a tip on each pipette to transfer all liquid volumes
        ### Start by selecting for the smallest transfer volume
        select_pipette_by_volume(Protocol, min_transfer).pick_up_tip()

        ### Then get tip for the largest volume
        # Check that the most suitable pipette doesn't already have a tip loaded for the smallest transfer
        if not select_pipette_by_volume(Protocol, max_transfer).has_tip:
            select_pipette_by_volume(Protocol, max_transfer).pick_up_tip()

    # Begin iterating through the transfer volumes list
    for transfer_volume, source, destination in zip(Transfer_Volumes, Source_Locations, Destination_Locations):
        # Ignore any transfers of 0 uL
        if transfer_volume == 0:
            continue

        # Select the best pipette for this transfer
        pipette = select_pipette_by_volume(Protocol, transfer_volume)

        # Load the pipette tip if required
        ## This will be needed if a new tip is being used for each transfer, and will be ignore if the same tip will always be used
        if new_tip:
            if pipette.has_tip:
                # Logic check - this should never occur
                ## If new_tip is `True`, the tip should have have been dropped after the previous transfer step
                raise _BMS.TransferError("Logical error for `OTProto.transfer_liquids()`:\nThe tip should have been dropped in the previous step but is still loaded. Please submit this protocol as an issue on the Github.")
            else:
                pipette.pick_up_tip()

        # The while loop is used to deal with situations where the transfer volume needs to be split into multiple transfers
        ## This can happen when the transfer volume is more than the largest pipette's max volume
        volume_transfered = 0 # used to track how much liquid has been transfered
        while not volume_transfered == transfer_volume:

            # Check if the transfer needs to be split, and set the volume to be transfered in this event
            if (transfer_volume - volume_transfered) > pipette.max_volume:
                current_transfer_volume = pipette.max_volume
            else:
                current_transfer_volume = transfer_volume - volume_transfered


            # Convert the mix_before and mix_after arguments into a useable fomrat
            mix_before_reps = None
            mix_before_volume = None

            if mix_before:
                mix_before_reps = mix_before[0]
                if mix_before[1] == "transfer_volume":
                    # Set the mix volume to the transfer volume
                    mix_before_volume = current_transfer_volume
                else:
                    # Set the mix volume to that provided by the user
                    mix_before_volume = mix_before[1]

            mix_after_reps = None
            mix_after_volume = None

            if mix_after:
                mix_after_reps = mix_after[0]
                if mix_after[1] == "transfer_volume":
                    # Set the mix volume to the transfer volume
                    mix_after_volume = current_transfer_volume
                else:
                    # Set the mix volume to that provided by the user
                    mix_after_volume = mix_after[1]


            # Move to the source location
            pipette.move_to(source.top())

            # Mix the source liquid (if required) #
            if mix_before:
                # Set the mixing speed
                pipette.flow_rate.aspirate *= mix_speed_multiplier
                pipette.flow_rate.dispense *= mix_speed_multiplier

                # Perform the mixing
                pipette.mix(
                    repetitions = mix_before_reps,
                    volume = mix_before_volume,
                    location = source
                )

                # Reset the flow rate speeds
                pipette.flow_rate.aspirate /= mix_speed_multiplier
                pipette.flow_rate.dispense /= mix_speed_multiplier

            # Aspirate the liquid #
            pipette.aspirate(
                volume = current_transfer_volume,
                location = source,
                rate = aspirate_speed_multiplier
            )

            # Knock the tip against the sides of the current well (if required)
            if touch_tip_source:
                pipette.touch_tip()

            # Move to the destination well
            pipette.move_to(destination.top())

            # Dispense the liquid
            pipette.dispense(
                volume = current_transfer_volume,
                location = destination,
                rate = dispense_speed_multiplier
            )

            # Mix the destination liquid (if required) #
            if mix_after:
                # Set the mixing speed
                pipette.flow_rate.aspirate *= mix_speed_multiplier
                pipette.flow_rate.dispense *= mix_speed_multiplier

                # Perform the mixing
                pipette.mix(
                    repetitions = mix_after_reps,
                    volume = mix_after_volume,
                    location = destination
                )

                # Reset the flow rate speeds
                pipette.flow_rate.aspirate /= mix_speed_multiplier
                pipette.flow_rate.dispense /= mix_speed_multiplier

            # Move the tip if required
            if move_after_dispense == "well_top":
                pipette.move_to(destination.top())
            elif move_after_dispense == "well_bottom":
                pipette.move_to(destination.bottom())
            elif move_after_dispense:
                # Check if the argument is not understood
                raise _BMS.TransferError("The `move_after_dispense` argument for `transfer_liquids` and `dispense_from_aliquots` MUST be either 'well_bottom' or 'well_top'. See the documentation for more information.")

            # If blowout will be somewhere other than the destination, then do touch_tip first
            if blowout_location == "source_well" or blowout_location == "trash":
                # knock the tip against the sides of the current well (if required)
                if touch_tip_destination:
                    pipette.touch_tip()

            # perform blowout if needed
            if blow_out:
                if blowout_location == "destination well":
                    b_location = destination
                elif blowout_location == "source_well":
                    b_location = source
                elif blowout_location == "trash":
                    b_location = Protocol.fixed_trash["A1"]
                else:
                    b_location = "" # this is to use the OT API error handling
                pipette.blow_out(b_location)

            # If blowout was at the destination location, then do blowout now

            if blowout_location == "destination well":
                # knock the tip against the sides of the current well (if required)
                if touch_tip_destination:
                    pipette.touch_tip()


            # If new_tip is True, drop the tip now
            if new_tip:
                pipette.drop_tip()

            # Update the volume left to transfer
            volume_transfered += current_transfer_volume

    # If the same tip was used for all transfers, then drop it now
    if not new_tip:
        select_pipette_by_volume(Protocol, min_transfer).drop_tip()
        # Check if the tip used for largest transfers has already been dropped (i.e. when the same pipette was used for everything)
        if select_pipette_by_volume(Protocol, max_transfer).has_tip:
            select_pipette_by_volume(Protocol, max_transfer).drop_tip()

    # Reset the blowout flow rate (if needed)
    for pipette in [p20, p300, p1000]:
        if pipette:
            pipette.flow_rate.blow_out /= blowout_speed_multiplier

def dispense_from_aliquots(Protocol, Transfer_Volumes, Aliquot_Source_Locations, Destinations, Min_Transfer = None, Calculate_Only = False, Dead_Volume_Proportion = 0.95, Aliquot_Volumes = None, new_tip = True, mix_after = None, mix_before = None, mix_speed_multiplier = 1, aspirate_speed_multiplier = 1, dispense_speed_multiplier = 1, blowout_speed_multiplier = 1, touch_tip_source = False, touch_tip_destination = False, blow_out = False, blowout_location = "destination well", move_after_dispense = None):

    Initial_Source_Locations = Aliquot_Source_Locations.copy()

    # If no min transfer specified, then use the min volume of the smallest loaded pipette
    if not Min_Transfer:
        Min_Transfer = get_lowest_volume_pipette(Protocol).min_volume

    # Create list to store order of Aliquot Source Location usage
    Aliquot_Source_Order = []

    # Format aliquot volumes so it is useable
    if Aliquot_Volumes:
        if type(Aliquot_Volumes) == int or type(Aliquot_Volumes) == float:
            Aliquot_Volumes = [Aliquot_Volumes] * len(Aliquot_Source_Locations)

    # Modify aliquot volumes to account for dead volumes
    if Aliquot_Volumes:
        Aliquot_Volumes = [vol*Dead_Volume_Proportion for vol in Aliquot_Volumes.copy()]

    Aliquot_Index = 0
    event_index = 0
    for transfer_volume, destination in zip(Transfer_Volumes, Destinations):
        # Check if there is enough volume in the current aliquot
        if Aliquot_Volumes:

            if Aliquot_Volumes[Aliquot_Index] >= transfer_volume:
                # Check that the vol being left behind isn't below the min transfer (unless this is the last transfer event)
                if not event_index == len(Transfer_Volumes) - 1:
                    if Aliquot_Volumes[Aliquot_Index] - transfer_volume >= Min_Transfer or Aliquot_Volumes[Aliquot_Index] - transfer_volume == 0: # second condition ensures that an aliquot can still be depleted
                        # print("Check", Aliquot_Volumes[Aliquot_Index] - transfer_volume, ">=", Min_Transfer)
                        # If all is fine, then continue
                        Aliquot_Volumes[Aliquot_Index] -= transfer_volume
                    else:
                        # Otherwise, leave enough behind that the aliquot can still be taken from (split the transfer)
                        new_transfer_vol = transfer_volume - Min_Transfer
                        # print("new transfer vol", new_transfer_vol)
                        ## Add the current aliquot source location to the source order
                        Aliquot_Source_Order.append(Aliquot_Source_Locations[Aliquot_Index])
                        # update the amount of liquid left in the aliquot
                        Aliquot_Volumes[Aliquot_Index] -= new_transfer_vol
                        # Iterate to the next aliquot
                        Aliquot_Index += 1
                        if Aliquot_Index == len(Aliquot_Source_Locations):
                            Aliquot_Index = 0
                        ## Insert the transfer volume and destination
                        Transfer_Volumes.insert(event_index, new_transfer_vol)
                        Destinations.insert(event_index, destination)
                        # Update the next transfer vol (i.e. the one that has just been split)
                        Transfer_Volumes[event_index + 1] -= new_transfer_vol
                        # Then move onto the next transfer action
                        event_index += 1
                        continue

            # If not, then split the transfer action
            else:
                # Transfer the rest of the current aliquot
                transfer_rest_vol = Aliquot_Volumes[Aliquot_Index]
                # print("To Transfer:", transfer_rest_vol, "<",  "Transfer Total", transfer_volume)

                # Check if the remaining volume to transfer is below the min transfer volume
                if transfer_volume - transfer_rest_vol < Min_Transfer:
                    # Change how much is being transfered in this first event so that the next transfer is above the minimum transfer amount
                    new_transfer_vol = transfer_volume - Min_Transfer
                    # print("new transfer vol", new_transfer_vol)
                    ## Add the current aliquot source location to the source order
                    Aliquot_Source_Order.append(Aliquot_Source_Locations[Aliquot_Index])
                    # update the amount of liquid left in the aliquot
                    Aliquot_Volumes[Aliquot_Index] -= new_transfer_vol
                    # Iterate to the next aliquot
                    Aliquot_Index += 1
                    if Aliquot_Index == len(Aliquot_Source_Locations):
                        Aliquot_Index = 0
                    ## Insert the transfer volume and destination
                    Transfer_Volumes.insert(event_index, new_transfer_vol)
                    Destinations.insert(event_index, destination)
                    # Update the next transfer vol (i.e. the one that has just been split)
                    Transfer_Volumes[event_index + 1] -= new_transfer_vol
                    # Then move onto the next transfer action
                    event_index += 1
                    continue

                # print("Left to transfer:", transfer_volume - transfer_rest_vol)
                ## Add the current aliquot source location to the source order
                Aliquot_Source_Order.append(Aliquot_Source_Locations[Aliquot_Index])
                ## And then remove it from the available list
                Aliquot_Volumes.remove(Aliquot_Volumes[Aliquot_Index])
                Aliquot_Source_Locations.remove(Aliquot_Source_Locations[Aliquot_Index])
                # If the aliquot removed was the last in the list, move back to the first aliquot
                if Aliquot_Index == len(Aliquot_Source_Locations):
                    Aliquot_Index = 0
                # If there aren't any aliquots left, raise an error
                if len(Aliquot_Source_Locations) == 0:
                    raise _BMS.OutOFSourceMaterial("Ran out of source material when aliquoting into {}.\nSource Locations:\n{}".format(destination, "\n".join(str(sl) for sl in Initial_Source_Locations)))

                ## Insert the transfer volume and destination
                Transfer_Volumes.insert(event_index, transfer_rest_vol)
                Destinations.insert(event_index, destination)
                # Update the next transfer vol (i.e. the one that has just been split)
                Transfer_Volumes[event_index + 1] -= transfer_rest_vol
                # print(Aliquot_Source_Locations[Aliquot_Index], destination, Transfer_Volumes[event_index + 1])
                # Then move onto the next transfer action
                event_index += 1
                continue

        Aliquot_Source_Order.append(Aliquot_Source_Locations[Aliquot_Index])
        Aliquot_Index += 1
        if Aliquot_Index == len(Aliquot_Source_Locations):
            Aliquot_Index = 0

        event_index += 1

    # Sanity check
    if not len(Transfer_Volumes) == len(Aliquot_Source_Order) and len(Transfer_Volumes) == len(Destinations):
        raise _BMS.TransferError("Internal error calculating dispense from aliquot transfer actions. Please report as an issue")

    if Calculate_Only:
        return(Transfer_Volumes, Aliquot_Source_Order, Destinations)
    else:
        transfer_liquids(
            Protocol = Protocol,
            Transfer_Volumes = Transfer_Volumes,
            Source_Locations = Aliquot_Source_Order,
            Destination_Locations = Destinations,
            new_tip = new_tip,
            mix_after = mix_after,
            mix_before = mix_before,
            mix_speed_multiplier = mix_speed_multiplier,
            aspirate_speed_multiplier = aspirate_speed_multiplier,
            dispense_speed_multiplier = dispense_speed_multiplier,
            blowout_speed_multiplier = blowout_speed_multiplier,
            touch_tip_source = touch_tip_source,
            touch_tip_destination = touch_tip_destination,
            blow_out = blow_out,
            blowout_location = blowout_location,
            move_after_dispense = move_after_dispense
        )

def next_empty_slot(protocol):
    # temporary workaround if Thermocycler is loaded
    if str(protocol.deck[7]) == "Thermocycler Module on 7":
        for slot in [1,2,3,4,5,6,9]:
            labware = protocol.deck[slot]
            if labware is None: # if no labware loaded into slot
                return(slot)
    else:
        for slot in protocol.deck:
            labware = protocol.deck[slot]
            if labware is None: # if no labware loaded into slot
                return(slot)
    raise IndexError('No Deck Slots Remaining')

def get_labware_format(labware_api_name, custom_labware_dir = None):
    # If try code block fails, labware may be custom, so treat it as such
    try:
        labware_definition = protocol_api.labware.get_labware_definition(labware_api_name)
        n_cols = len(labware_definition["ordering"])
        n_rows = len(labware_definition["ordering"][0])
        return(n_rows, n_cols)

    except FileNotFoundError:
        try:
            definition_file_location = "{}/{}.json".format(custom_labware_dir, labware_api_name)
            with open(definition_file_location) as labware_definition:
                data = json.load(labware_definition)
                n_cols = len(data["ordering"])
                n_rows = len(data["ordering"][0])
                return(n_rows, n_cols)
        except FileNotFoundError:
            definition_file_location = "{}/{}.json".format(Pre_Loaded_Custom_Labware_Dir, labware_api_name)
            with open(definition_file_location) as labware_definition:
                data = json.load(labware_definition)
                n_cols = len(data["ordering"])
                n_rows = len(data["ordering"][0])
                return(n_rows, n_cols)

def get_labware_well_capacity(labware_api_name, custom_labware_dir = None):
    # If try code block fails, labware may be custom, so treat it as such
    try:
        labware_definition = protocol_api.labware.get_labware_definition(labware_api_name)
        # Check the capacity of all wells in the labware and add to a set
        capacities = set()
        for well in labware_definition["wells"]:
            capacities.add(labware_definition["wells"][well]["totalLiquidVolume"])
        # Check if the capacities set has more than one volume
        ## If it does, raise an error becuase I can't think of an easy way to deal with that atm
        if not len(capacities) == 1:
            raise _BMS.LabwareError("Labware {} has slots/wells with different volume capacities; BMS cannot currently deal with this.")
        capacity = capacities.pop()
        return(capacity)

    except FileNotFoundError:
        try:
            definition_file_location = "{}/{}.json".format(custom_labware_dir, labware_api_name)
            with open(definition_file_location) as labware_definition:
                data = json.load(labware_definition)
                # Check the capacity of all wells in the labware and add to a set
                capacities = set()
                for well in data["wells"]:
                    capacities.add(data["wells"][well]["totalLiquidVolume"])
                # Check if the capacities set has more than one volume
                ## If it does, raise an error becuase I can't think of an easy way to deal with that atm
                if not len(capacities) == 1:
                    raise _BMS.LabwareError("Labware {} has slots/wells with different volume capacities; BMS cannot currently deal with this.")
                capacity = capacities.pop()
                return(capacity)
        except FileNotFoundError:
            definition_file_location = "{}/{}.json".format(Pre_Loaded_Custom_Labware_Dir, labware_api_name)
            with open(definition_file_location) as labware_definition:
                data = json.load(labware_definition)
                # Check the capacity of all wells in the labware and add to a set
                capacities = set()
                for well in data["wells"]:
                    capacities.add(data["wells"][well]["totalLiquidVolume"])
                # Check if the capacities set has more than one volume
                ## If it does, raise an error becuase I can't think of an easy way to deal with that atm
                if not len(capacities) == 1:
                    raise _BMS.LabwareError("Labware {} has slots/wells with different volume capacities; BMS cannot currently deal with this.")
                capacity = capacities.pop()
                return(capacity)

def load_labware(parent, labware_api_name, deck_position = None, custom_labware_dir = None, label = None):
    labware = None

    # Try and load not as custom
    try:
        # Check if `parent` is the deck or a hardware module, and treat it acordingly
        if parent.__class__ == protocol_api.protocol_context.ProtocolContext:
            # If no deck position, get the next empty slot
            if not deck_position:
                deck_position = next_empty_slot(parent)
            labware = parent.load_labware(labware_api_name, deck_position, label)
        else:
            labware = parent.load_labware(labware_api_name, label)
    except:
        if not custom_labware_dir:
            raise ValueError("{} appears to be custom labware; use `custom_labware_dir` to provide the directory location for this labware file".format(labware_api_name))
        labware = load_custom_labware(parent, custom_labware_dir + "/" + labware_api_name + ".json", deck_position, label)

    if labware == None:
        raise ValueError("Labware not loaded for unknown reasons.")

    return(labware)

def calculate_and_load_labware(protocol, labware_api_name, wells_required, wells_available = "all", modules=None, custom_labware_dir = None, label = None):
    # Determine amount of labware required #
    labware = []
    ## Load first labware to get format - assume always at least one required
    # load directly onto modules if available
    if modules is None:
        labware_slot = next_empty_slot(protocol)
        loaded_labware = load_labware(protocol, labware_api_name, labware_slot, custom_labware_dir = custom_labware_dir, label = label)
    else:
        if type(modules) is not list:
            modules = [modules]
        loaded_labware = load_labware(modules[0], labware_api_name, custom_labware_dir = custom_labware_dir, label = label)
    labware.append(loaded_labware)
    ## Determine space in labware
    if wells_available == "all":
        wells_in_labware = len(labware[0].wells())
    else:
        wells_in_labware = wells_available
    ## Determine total amount of dilution labware required
    n_labware = math.ceil(wells_required/wells_in_labware)
    ## Load more labware if required
    for lw in range(0, n_labware - 1):
        # load directly onto modules if available
        if modules is not None and len(modules) > lw+1:
            loaded_labware = load_labware(modules[lw+1], labware_api_name, custom_labware_dir = custom_labware_dir, label = label)
            labware.append(loaded_labware)
        else:
            labware_slot = next_empty_slot(protocol)
            loaded_labware = load_labware(protocol, labware_api_name, labware_slot, custom_labware_dir = custom_labware_dir, label = label)
            labware.append(loaded_labware)

    well_locations = []
    labware_index = 0
    location_in_labware_index = 0
    for well in range(0,wells_required):
        current_labware_wells = labware[labware_index].wells()
        well_locations.append(current_labware_wells[location_in_labware_index])
        location_in_labware_index += 1
        if location_in_labware_index == len(current_labware_wells):
            labware_index += 1
            location_in_labware_index = 0

    # Return the list of loaded labware
    return(labware, well_locations)

def load_labware_from_layout(Protocol, Labware_Layout, deck_position = None, custom_labware_dir = None):
    labware_type = Labware_Layout.type
    labware_name = Labware_Layout.name
    labware = load_labware(Protocol, labware_type, deck_position = deck_position, custom_labware_dir = custom_labware_dir, label = labware_name)

    return(labware)

def calculate_tips_needed(protocol, transfers, template = None, new_tip = True):
    if not type(transfers) == list:
        transfers = [transfers]

    tips_needed = {
        "20uL": 0,
        "300uL": 0,
        "1000uL": 0
    }

    for transfer in transfers:
        # If transfer volume is 0 uL, skip it
        if transfer == 0:
            continue
        # Get the most appropriate pipette from those which are loaded
        pipette = select_pipette_by_volume(protocol, transfer)
        # Check how many trasfers will be needed to transfer the entire volume (e.g. if p300 is chosen for 400 uL, two transfers needed)
        ## This can be ignored if new_tip == False (i.e. one tip will be used no matter hwhat)
        if new_tip:
            transfers_needed = math.ceil(transfer/pipette.max_volume)
            # For each transfer that is needed, add to the appropriate tips_needed counter
            for n in range(0, transfers_needed):
                tips_needed["{}uL".format(pipette.max_volume)] += 1
        else:
            # Check if a new tip needs to be added
            ## A new tip won't be needed if an appropriate sized tip has already been added and new_tip is False
            if tips_needed["{}uL".format(pipette.max_volume)] > 0:
                continue
            else:
                tips_needed["{}uL".format(pipette.max_volume)] += 1


    # If a template is specified, add the tips needed to the tips_needed attributes
    if template:
        template.tips_needed["p20"] += tips_needed["20uL"]
        template.tips_needed["p300"] += tips_needed["300uL"]
        template.tips_needed["p1000"] += tips_needed["1000uL"]

    # Return a list of all tips needed
    return(tips_needed["20uL"], tips_needed["300uL"], tips_needed["1000uL"])

def tip_racks_needed(tips_needed, starting_tip_position = "A1"):
    if tips_needed == 0:
        return(0)
    tips_in_first_rack = len(_BMS.well_range("{}:H12".format(starting_tip_position), [8,12], "Vertical"))
    if tips_needed > tips_in_first_rack:
        extra_racks_required = math.ceil((tips_needed - tips_in_first_rack)/96)
    else:
        extra_racks_required = 0
    racks_required = 1 + extra_racks_required
    return(racks_required)

def load_pipettes_and_tips(Protocol, Pipette_Type, Pipette_Position, Tip_Type, Number_Tips_Required = None, Starting_Tip = "A1"):
    ## When Number_Tips_Required is False, just one tip box is created and asigned to the pipette
    tip_racks = []

    if Number_Tips_Required:
        n_tip_racks = tip_racks_needed(Number_Tips_Required, Starting_Tip)
    else:
        n_tip_racks = 1

    for tip_rack in range(0, n_tip_racks):
        tip_rack_deck_slot = next_empty_slot(Protocol)
        tip_rack = load_labware(Protocol, Tip_Type, tip_rack_deck_slot)
        tip_racks.append(tip_rack)

    # Check if pipette is already loaded
    # if something is loaded but it isn't the same type as the one being loaded raise an error
    # if something is loaded and it is the same type as the one beign loaded, pass
    # if something isn't loaded, then load it
    if Pipette_Position in Protocol.loaded_instruments.keys():
        if Protocol.loaded_instruments[Pipette_Position].name == Pipette_Type:
            pipette = Protocol.loaded_instruments[Pipette_Position]
            for tip_rack in tip_racks:
                pipette.tip_racks.append(tip_rack)
        else:
            raise _BMS.RobotConfigurationError("A pipette is already loaded, check the protocol for errors.")
    else:
        pipette = Protocol.load_instrument(Pipette_Type, Pipette_Position, tip_racks)

    pipette.starting_tip = tip_racks[0].well(Starting_Tip)

    return(pipette, tip_racks)

def add_tip_boxes_to_pipettes(Protocol, Pipette_Type, Tip_Type, Tips_Needed, Starting_Tip = "A1"):
    if Tips_Needed == 0:
        return(None)
    pipette = get_pipette(Protocol, Pipette_Type)
    if pipette == None:
        raise _BMS.RobotConfigurationError("The specified pipette type, {}, has not been loaded.".format(Pipette_Type))
    tip_boxes_needed = tip_racks_needed(Tips_Needed, Starting_Tip)
    for tip_box in range(0, tip_boxes_needed):
        tip_box_deck_slot = next_empty_slot(Protocol)
        tip_box = load_labware(Protocol, Tip_Type, tip_box_deck_slot)

        pipette.tip_racks.append(tip_box)
    pipette.starting_tip = pipette.tip_racks[0].well(Starting_Tip)



# Functions less likely to be useful to users

def get_p20(protocol):
    pipettes = protocol.loaded_instruments
    for position in pipettes.keys():
        min_volume = pipettes[position].min_volume
        max_volume = pipettes[position].max_volume
        channels = pipettes[position].channels
        if (min_volume == 1) and (max_volume == 20) and (channels == 1):
            return(pipettes[position])
    return(None)

def get_p300(protocol):
    pipettes = protocol.loaded_instruments
    for position in pipettes.keys():
        min_volume = pipettes[position].min_volume
        max_volume = pipettes[position].max_volume
        channels = pipettes[position].channels
        if (min_volume == 20) and (max_volume == 300) and (channels == 1):
            return(pipettes[position])
    return(None)

def get_p1000(protocol):
    pipettes = protocol.loaded_instruments
    for position in pipettes.keys():
        min_volume = pipettes[position].min_volume
        max_volume = pipettes[position].max_volume
        channels = pipettes[position].channels
        if (min_volume == 100) and (max_volume == 1000) and (channels == 1):
            return(pipettes[position])
    return(None)

def get_lowest_volume_pipette(protocol):
    if get_pipette(protocol, "p20"):
        return(get_pipette(protocol, "p20"))
    elif get_pipette(protocol, "p300"):
        return(get_pipette(protocol, "p300"))
    elif get_pipette(protocol, "p1000"):
        return(get_pipette(protocol, "p1000"))

    return(None)

def load_custom_labware(parent, file, deck_position = None, label = None):
    # Open the labware json file
    with open(file) as labware_file:
        labware_file = json.load(labware_file)

    # Check if `parent` is the deck or a hardware module, and treat it acordingly
    if parent.__class__ == protocol_api.protocol_context.ProtocolContext:
        # If no deck position, get the next empty slot
        if not deck_position:
            deck_position = next_empty_slot(parent)
        labware = parent.load_labware_from_definition(labware_file, deck_position, label)
    else:
        labware = parent.load_labware_from_definition(labware_file, label)

    return(labware)

def shuffle_locations(protocol, Locations, outdir=None, outfile="Locations"):
    old_locations = Locations.copy()
    # shuffle the locations
    shuffle(Locations)
    new_locations = Locations
    # add the locations to the robot command line to be logged and seen by the user
    protocol.comment(f"Locations given were {old_locations}")
    protocol.comment(f"Shuffled locations are {new_locations}")
    # export to file (if outdir provided)
    # recommend user to provide outdir="/data/user_storage/<USER_DIR>"
    # this function will overwrite any existing file with the same path
    if outdir is not None:
        fw = open(outdir+outfile+".csv", "w")
        dt = datetime.datetime.now()
        fw.write(dt.strftime("%c"))
        fw.write("\nOld Location,New Location,\n")
        for o,n in zip(old_locations,new_locations):
            fw.write(f"{o},{n},\n")
        fw.close()
    return new_locations
