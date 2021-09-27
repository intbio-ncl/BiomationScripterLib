import json
import BiomationScripter as _BMS
import math
from opentrons import simulate as OT2

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
    # Return the list of loaded labware
    return(labware)


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
    # labware = None

    # Check if labware is in the default list
    if labware_api_name in OT2.protocol_api.labware.get_all_labware_definitions():
        # Check if `parent` is the deck or a hardware module, and treat it acordingly
        if parent.__class__ == OT2.protocol_api.protocol_context.ProtocolContext:
            # If no deck position, get the next empty slot
            if not deck_position:
                deck_position = next_empty_slot(parent)
            labware = parent.load_labware(labware_api_name, deck_position, label)
        else:
            labware = parent.load_labware(labware_api_name, label)
    # If not in default list, treat as custom labware
    else:
        labware = load_custom_labware(parent, custom_labware_dir + "/" + labware_api_name + ".json", deck_position, label)

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
