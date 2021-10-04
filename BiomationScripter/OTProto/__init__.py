import json
import BiomationScripter as _BMS
import math
from opentrons import simulate as OT2

########################

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

def transfer_liquids(Protocol, Transfer_Volumes, Source_Locations, Destination_Locations, new_tip = True, mix_after = None, mix_before = None):
    min_transfer = min(Transfer_Volumes)
    max_transfer = max(Transfer_Volumes)

    # Check that the correct pipettes are available #
    p20 = get_p20(Protocol)
    p300 = get_p300(Protocol)
    p1000 = get_p1000(Protocol)

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

    if not new_tip:
        # Select tip for smallest transfers
        if min_transfer == 0:
            pass
        elif min_transfer <= 20 and p20:
            p20.pick_up_tip()
        elif min_transfer == 20 and p300 and not p20:
            p300.pick_up_tip()
        elif min_transfer <= 300 and p300:
            p300.pick_up_tip()
        else:
            p1000.pick_up_tip()

        # Select tip for largest transfers (if not already selected)
        if (max_transfer > 20 and max_transfer <= 300) and p300:
            if not p300.has_tip:
                p300.pick_up_tip()
        elif max_transfer >= 100 and not p300 and p1000:
            if not p1000.has_tip:
                p1000.pick_up_tip()

        for transfer_volume, source, destination in zip(Transfer_Volumes, Source_Locations, Destination_Locations):
            if transfer_volume == 0:
                continue
            # Deal with mix_before and mix_after
            if mix_before and mix_before[1] == "transfer_volume":
                mix_before = (mix_before[0], transfer_volume)
            if mix_after and mix_after[1] == "transfer_volume":
                mix_after = (mix_after[0], transfer_volume)

            # Choose best pipette to use
            if transfer_volume < 20 and p20:
                p20.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and p20:
                p20.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and not p20:
                p300.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 20 and transfer_volume <= 300 and p300:
                p300.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and p1000:
                p1000.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume >= 100 and not p300 and p1000:
                p1000.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and not p1000 and p300:
                p300.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif not p300 and not p1000:
                p20.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)

        if p20:
            if p20.has_tip:
                p20.drop_tip()
        if p300:
            if p300.has_tip:
                p300.drop_tip()
        if p1000:
            if p1000.has_tip:
                p1000.drop_tip()

    else:
        for transfer_volume, source, destination in zip(Transfer_Volumes, Source_Locations, Destination_Locations):
            if transfer_volume == 0:
                continue
            # Deal with mix_before and mix_after
            if mix_before and mix_before[1] == "transfer_volume":
                mix_before = (mix_before[0], transfer_volume)
            if mix_after and mix_after[1] == "transfer_volume":
                mix_after = (mix_after[0], transfer_volume)

            # Choose best pipette to use
            if transfer_volume < 20 and p20:
                p20.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and p20:
                p20.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and not p20:
                p300.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 20 and transfer_volume <= 300 and p300:
                p300.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and p1000:
                p1000.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume >= 100 and not p300 and p1000:
                p1000.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and not p1000 and p300:
                p300.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif not p300 and not p1000:
                p20.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)



def dispense_from_aliquots(Protocol, Transfer_Volumes, Aliquot_Source_Locations, Destinations, new_tip = True, mix_after = None, mix_before = None):
    min_transfer = min(Transfer_Volumes)
    max_transfer = max(Transfer_Volumes)

    # Check that the correct pipettes are available #
    p20 = get_p20(Protocol)
    p300 = get_p300(Protocol)
    p1000 = get_p1000(Protocol)

    if not p20 and not p300 and not p1000:
        raise ValueError("No pipettes have been loaded")

    for volume in Transfer_Volumes:
        if volume == 0:
            continue
        if volume < 20 and not p20:
            raise ValueError("p20 pipette is required, but has not been loaded")
        if volume == 20 and (not p20 and not p300):
            raise ValueError("p20 or p300 pipette is required, but neither have been loaded")
        if (volume <= 100 and volume > 20) and not p300:
            raise ValueError("p300 pipette is required, but has not been loaded")
        if volume <=300 and (not p300 and not p1000):
            raise ValueError("p300 or p1000 pipette is required, but neither have been loaded")

    if not new_tip:
        # Select tip for smallest transfers
        if min_transfer == 0:
            pass
        elif min_transfer <= 20 and p20:
            p20.pick_up_tip()
        elif min_transfer == 20 and p300 and not p20:
            p300.pick_up_tip()
        elif min_transfer <= 300 and p300:
            p300.pick_up_tip()
        else:
            p1000.pick_up_tip()

        # Select tip for largest transfers (if not already selected)
        if (max_transfer > 20 and max_transfer <= 300) and p300:
            if not p300.has_tip:
                p300.pick_up_tip()
        elif max_transfer >= 100 and not p300 and p1000:
            if not p1000.has_tip:
                p1000.pick_up_tip()

        Aliquot_Index = 0
        for transfer_volume, destination in zip(Transfer_Volumes, Destinations):
            if transfer_volume == 0:
                continue
            # Deal with mix_before and mix_after
            if mix_before and mix_before[1] == "transfer_volume":
                mix_before = (mix_before[0], transfer_volume)
            if mix_after and mix_after[1] == "transfer_volume":
                mix_after = (mix_after[0], transfer_volume)
            source = Aliquot_Source_Locations[Aliquot_Index]
            # Choose best pipette to use
            if transfer_volume < 20 and p20:
                p20.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and p20:
                p20.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and not p20:
                p300.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 20 and transfer_volume <= 300 and p300:
                p300.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and p1000:
                p1000.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume >= 100 and not p300 and p1000:
                p1000.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and not p1000 and p300:
                p300.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            elif not p300 and not p1000:
                p20.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)
            Aliquot_Index += 1
            if Aliquot_Index == len(Aliquot_Source_Locations):
                Aliquot_Index = 0

        if p20:
            if p20.has_tip:
                p20.drop_tip()
        if p300:
            if p300.has_tip:
                p300.drop_tip()
        if p1000:
            if p1000.has_tip:
                p1000.drop_tip()

    else:
        Aliquot_Index = 0
        for transfer_volume, destination in zip(Transfer_Volumes, Destinations):
            if transfer_volume == 0:
                continue
            source = Aliquot_Source_Locations[Aliquot_Index]
            # Deal with mix_before and mix_after
            if mix_before and mix_before[1] == "transfer_volume":
                mix_before = (mix_before[0], transfer_volume)
            if mix_after and mix_after[1] == "transfer_volume":
                mix_after = (mix_after[0], transfer_volume)
            # Choose best pipette to use
            if transfer_volume < 20 and p20:
                p20.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and p20:
                p20.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume == 20 and not p20:
                p300.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 20 and transfer_volume <= 300 and p300:
                p300.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and p1000:
                p1000.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume >= 100 and not p300 and p1000:
                p1000.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif transfer_volume > 300 and not p1000 and p300:
                p300.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            elif not p300 and not p1000:
                p20.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after)
            Aliquot_Index += 1
            if Aliquot_Index == len(Aliquot_Source_Locations):
                Aliquot_Index = 0


# def calculate_aliquots_required(Transfers, Aliquot_Volume):
#     aliquots_required = 1
#     volume_left_in_aliquot = Aliquot_Volume
#     for transfer in Transfers:
#         if transfer <= volume_left_in_aliquot:
#             volume_left_in_aliquot -= transfer
#         else:
#             aliquots_required += 1
#             volume_left_in_aliquot = Aliquot_Volume


def calculate_and_load_labware(protocol, labware_api_name, wells_required, custom_labware_dir = None):
    # Determine amount of labware required #
    labware = []
    ## Load first labware to get format - assume always at least one required
    labware_slot = next_empty_slot(protocol)
    loaded_labware = load_labware(protocol, labware_api_name, labware_slot, custom_labware_dir = custom_labware_dir)
    labware.append(loaded_labware)
    ## Determine space in labware
    wells_in_labware = len(labware[0].wells())
    ## Determine total amount of dilution labware required
    n_labware = math.ceil(wells_required/wells_in_labware)
    ## Load more labware if required
    for lw in range(0, n_labware - 1):
        labware_slot = next_empty_slot(protocol)
        loaded_labware = load_labware(protocol, labware_api_name, labware_slot, custom_labware_dir = custom_labware_dir)
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


def next_empty_slot(protocol):
    for slot in protocol.deck:
        labware = protocol.deck[slot]
        if not labware: # if no labware loaded into slot
            return(slot)
    raise IndexError('No Deck Slots Remaining')

def load_custom_labware(parent, file, deck_position = None, label = None):
    # Open the labware json file
    with open(file) as labware_file:
        labware_file = json.load(labware_file)

    # Check if `parent` is the deck or a hardware module, and treat it acordingly
    if parent.__class__ == OT2.protocol_api.protocol_context.ProtocolContext:
        # If no deck position, get the next empty slot
        if not deck_position:
            deck_position = next_empty_slot(parent)
        labware = parent.load_labware_from_definition(labware_file, deck_position, label)
    else:
        labware = parent.load_labware_from_definition(labware_file, label)

    return(labware)

def load_labware(parent, labware_api_name, deck_position = None, custom_labware_dir = None, label = None):
    labware = None

    # Try and load not as custom
    try:
        # Check if `parent` is the deck or a hardware module, and treat it acordingly
        if parent.__class__ == OT2.protocol_api.protocol_context.ProtocolContext:
            # If no deck position, get the next empty slot
            if not deck_position:
                deck_position = next_empty_slot(parent)
            labware = parent.load_labware(labware_api_name, deck_position, label)
        else:
            labware = parent.load_labware(labware_api_name, label)
    except:
        labware = load_custom_labware(parent, custom_labware_dir + "/" + labware_api_name + ".json", deck_position, label)

    if labware == None:
        raise ValueError("Labware not loaded for unknown reasons.")

    return(labware)

def load_pipettes_and_tips(Protocol, Pipette_Type, Pipette_Position, Tip_Type, Number_Tips_Required = False, Starting_Tip = "A1"):
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

    pipette = Protocol.load_instrument(Pipette_Type, Pipette_Position, tip_racks)
    pipette.starting_tip = tip_racks[0].well(Starting_Tip)

    return(pipette, tip_racks)

def tip_racks_needed(tips_needed, starting_tip_position = "A1"):
    tips_in_first_rack = len(_BMS.well_range("{}:H12".format(starting_tip_position), [8,12], "Vertical"))
    if tips_needed > tips_in_first_rack:
        extra_racks_required = math.ceil((tips_needed - tips_in_first_rack)/96)
    else:
        extra_racks_required = 0
    racks_required = 1 + extra_racks_required
    return(racks_required)
