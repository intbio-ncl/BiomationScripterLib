import json
import BiomationScripter as _BMS
import math

def next_empty_slot(protocol):
    for slot in protocol.deck:
        labware = protocol.deck[slot]
        if not labware: # if no labware loaded into slot
            return(slot)
    raise IndexError('No Deck Slots Remaining')

def load_custom_labware(protocol, file, deck_position = None):
    with open(file) as labware_file:
        labware = json.load(labware_file)

    if deck_position == None: # This is for where Protocol is actual a hardware module
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
