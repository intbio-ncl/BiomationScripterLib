import json
import BiomationScripter as _BMS
import math

def load_custom_labware(protocol, file, deck_position = None):
    with open(file) as labware_file:
        labware = json.load(labware_file)

    if deck_position == None: # This is for where Protocol is actual a hardware module
        return(protocol.load_labware_from_definition(labware))
    else:
        return(protocol.load_labware_from_definition(labware, deck_position))

def tip_racks_needed(tips_needed, starting_tip_position = "A1"):
    tips_in_first_rack = len(_BMS.well_range("{}:H12".format(starting_tip_position)))
    if tips_needed > tips_in_first_rack:
        extra_racks_required = math.ceil((tips_needed - tips_in_first_rack)/96)
    else:
        extra_racks_required = 0
    racks_required = 1 + extra_racks_required
    return(racks_required)
