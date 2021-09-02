import json
import BiomationScripter as _BMS
import math

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

def load_custom_labware(protocol, file, deck_position = None):
    with open(file) as labware_file:
        labware = json.load(labware_file)

    if deck_position == None: # This is for where Protocol is actually a hardware module, i.e. when loading labware onto hardware with a pre-defined slot position
        return(protocol.load_labware_from_definition(labware))
    else:
        return(protocol.load_labware_from_definition(labware, deck_position))

def load_labware(parent, labware_api_name, deck_pos, custom_labware_dir = None):
    labware = None

    try:
        labware = parent.load_labware(labware_api_name, deck_pos)
    except:
        labware = load_custom_labware(parent, custom_labware_dir + "/" + labware_api_name + ".json", deck_pos)

    return(labware)

def tip_racks_needed(tips_needed, starting_tip_position = "A1"):
    tips_in_first_rack = len(_BMS.well_range("{}:H12".format(starting_tip_position)))
    if tips_needed > tips_in_first_rack:
        extra_racks_required = math.ceil((tips_needed - tips_in_first_rack)/96)
    else:
        extra_racks_required = 0
    racks_required = 1 + extra_racks_required
    return(racks_required)
