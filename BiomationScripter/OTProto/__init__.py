import json
import BiomationScripter as _BMS
import math
from opentrons import simulate as OT2
import warnings

########################

class OTProto_Template:
    def __init__(self,
        Protocol,
        Name,
        Metadata,
        Starting_20uL_Tip = "A1",
        Starting_300uL_Tip = "A1",
        Starting_1000uL_Tip = "A1"
    ):
        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self.custom_labware_dir = "../Custom_Labware/"

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

    def custom_labware_directory(self, Directory):
        self.custom_labware_dir = Directory

    def pipette_config(self, Pipette_Type, Position):
        if self.__pipettes_loaded:
            raise _BMS.BMSTemplateError("Pipettes have already been loaded. Please modify pipette configuration before loading pipettes. Changes to configuration have NOT been saved.")
        try:
            self._pipettes[Position.lower()] = Pipette_Type
        except KeyError:
            raise _BMS.RobotConfigurationError("{} is an invalid pipette positon. Please specify either 'right' or 'left'".format(Position))

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
                self.starting_tip_position(pipette_type, next_tip_in_rack)

        ############################
        # Clear deck and tip racks #
        ############################
        for position in self._protocol.deck:
            del self._protocol.deck[position]


        self.run()


########################

def get_locations(Labware, Wells, Direction = None):
    # Argument Direction is ignored is Wells is a list of wells
    ## It is only used if Wells is a well range (e.g. A1:H4)
    if not type(Wells) == list:
        if not Direction == "Horizontal" and not Direction == "Vertical":
            raise ValueError("When using OTProto.get_locations with a well range, `Direction` must be either 'Horizontal' or 'Vertical'.")
        n_labware_rows = len(Labware.rows())
        n_labware_cols = len(Labware.columns())
        Wells = _BMS.well_range(Wells, [n_labware_rows, n_labware_cols], Direction = Direction)

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

def select_pipette_by_volume(Protocol, Volume):

    # Check which pipettes are available - any unavailable will return None
    p20 = get_p20(Protocol)
    p300 = get_p300(Protocol)
    p1000 = get_p1000(Protocol)

    if Volume < 1:
        raise _BMS.RobotConfigurationError("Cannot transfer less than 1 uL.")
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

def transfer_liquids(
                Protocol,
                Transfer_Volumes,
                Source_Locations,
                Destination_Locations,
                new_tip = True,
                mix_after = None,
                mix_before = None
):



    if not type(Transfer_Volumes) == list:
        Transfer_Volumes = [Transfer_Volumes]
    if not type(Source_Locations) == list:
        Source_Locations = [Source_Locations]
    if not type(Destination_Locations) == list:
        Destination_Locations = [Destination_Locations]

    if not len(Transfer_Volumes) == len(Source_Locations) or not len(Transfer_Volumes) == len(Destination_Locations):
        raise ValueError("The number of transfer volumes, source locations, and destination locations are not the same.")

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

            # Choose best pipette to use
            pipette = select_pipette_by_volume(Protocol, transfer_volume)

            # Deal with mix_before and mix_after
            if mix_before and mix_before[1] == "transfer_volume":
                mix_before = (mix_before[0], transfer_volume)
            if mix_after and mix_after[1] == "transfer_volume":
                mix_after = (mix_after[0], transfer_volume)

            # If trying to mix with a volume larger than the pipette and deal with, set mix volume to the max
            if mix_before and mix_before[1] > pipette.max_volume:
                mix_before[1] = pipette.max_volume
            if mix_after and mix_after[1] > pipette.max_volume:
                mix_after[1] = pipette.max_volume

            pipette.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = mix_before, mix_after = mix_after)

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
            pipette = select_pipette_by_volume(Protocol, transfer_volume)

            # Deal with mix_before and mix_after
            if mix_before and mix_before[1] == "transfer_volume":
                mix_before = (mix_before[0], transfer_volume)
            if mix_after and mix_after[1] == "transfer_volume":
                mix_after = (mix_after[0], transfer_volume)

            # If trying to mix with a volume larger than the pipette and deal with, set mix volume to the max
            if mix_before and mix_before[1] > pipette.max_volume:
                mix_before = (mix_before[0], pipette.max_volume)
            if mix_after and mix_after[1] > pipette.max_volume:
                mix_after = (mix_after[0], pipette.max_volume)

            pipette.transfer(transfer_volume, source, destination, mix_before = mix_before, mix_after = mix_after, new_tip = "always")

def dispense_from_aliquots(Protocol, Transfer_Volumes, Aliquot_Source_Locations, Destinations, Aliquot_Volumes = None, new_tip = True, mix_after = None, mix_before = None):

    Initial_Source_Locations = Aliquot_Source_Locations.copy()

    # Create list to store order of Aliquot Source Location usage
    Aliquot_Source_Order = []

    # Format aliquot volumes so it is useable
    if Aliquot_Volumes:
        if type(Aliquot_Volumes) == int or type(Aliquot_Volumes) == float:
            Aliquot_Volumes = [Aliquot_Volumes] * len(Aliquot_Source_Locations)


    Aliquot_Index = 0
    for transfer_volume, destination in zip(Transfer_Volumes, Destinations):
        # Check if there is enough volume in the current aliquot
        if Aliquot_Volumes:
            # If there is, then continue
            if Aliquot_Volumes[Aliquot_Index] >= transfer_volume:
                Aliquot_Volumes[Aliquot_Index] -= transfer_volume
            # If not, then remove the current aliquot from the list of those available
            else:
                Aliquot_Volumes.remove(Aliquot_Volumes[Aliquot_Index])
                Aliquot_Source_Locations.remove(Aliquot_Source_Locations[Aliquot_Index])
                # If the aliquot removed was the last in the list, move back to the first aliquot
                if Aliquot_Index == len(Aliquot_Source_Locations):
                    Aliquot_Index = 0
                # If there aren't any aliquots left, raise an error
                if len(Aliquot_Source_Locations) == 0:
                    raise _BMS.OutOFSourceMaterial("Ran out of source material when aliquoting into {}.\nSource Locations:\n{}".format(destination, Initial_Source_Locations))

        Aliquot_Source_Order.append(Aliquot_Source_Locations[Aliquot_Index])
        Aliquot_Index += 1
        if Aliquot_Index == len(Aliquot_Source_Locations):
            Aliquot_Index = 0
    transfer_liquids(Protocol, Transfer_Volumes, Aliquot_Source_Order, Destinations, new_tip = new_tip, mix_before = mix_before, mix_after = mix_after)

def next_empty_slot(protocol):
    for slot in protocol.deck:
        labware = protocol.deck[slot]
        if not labware: # if no labware loaded into slot
            return(slot)
    raise IndexError('No Deck Slots Remaining')

def get_labware_format(labware_api_name, custom_labware_dir = None):
    # If try code block fails, labware may be custom, so treat it as such
    try:
        labware_definition = OT2.protocol_api.labware.get_labware_definition(labware_api_name)
        n_cols = len(labware_definition["ordering"])
        n_rows = len(labware_definition["ordering"][0])
        return(n_rows, n_cols)

    except FileNotFoundError:
        definition_file_location = "{}/{}.json".format(custom_labware_dir, labware_api_name)
        with open(definition_file_location) as labware_definition:
            data = json.load(labware_definition)
            n_cols = len(data["ordering"])
            n_rows = len(data["ordering"][0])
            return(n_rows, n_cols)

def get_labware_well_capacity(labware_api_name, custom_labware_dir = None):
    # If try code block fails, labware may be custom, so treat it as such
    try:
        labware_definition = OT2.protocol_api.labware.get_labware_definition(labware_api_name)
        # Check the capacity of all wells in the labware and add to a set
        capacities = set()
        for well in labware_definition["wells"]:
            capacities.add(labware_definition["wells"][well]["totalLiquidVolume"])
        # Check if the capacities set has more than one volume
        ## If it does, raise an error becuase I can't think of an easy way to deal with that atm
        if not len(capacities) == 1:
            raise BMS.LabwareError("Labware {} has slots/wells with different volume capacities; BMS cannot currently deal with this.")
        capacity = capacities.pop()
        return(capacity)

    except FileNotFoundError:
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
                raise BMS.LabwareError("Labware {} has slots/wells with different volume capacities; BMS cannot currently deal with this.")
            capacity = capacities.pop()
            return(capacity)

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
        if not custom_labware_dir:
            raise ValueError("{} appears to be custom labware; use `custom_labware_dir` to provide the directory location for this labware file".format(labware_api_name))
        labware = load_custom_labware(parent, custom_labware_dir + "/" + labware_api_name + ".json", deck_position, label)

    if labware == None:
        raise ValueError("Labware not loaded for unknown reasons.")

    return(labware)

def calculate_and_load_labware(protocol, labware_api_name, wells_required, wells_available = "all", custom_labware_dir = None):
    # Determine amount of labware required #
    labware = []
    ## Load first labware to get format - assume always at least one required
    labware_slot = next_empty_slot(protocol)
    loaded_labware = load_labware(protocol, labware_api_name, labware_slot, custom_labware_dir = custom_labware_dir)
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

def load_labware_from_layout(Protocol, Plate_Layout, deck_position = None, custom_labware_dir = None):
    labware_type = Plate_Layout.type
    labware_name = Plate_Layout.name
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
        else:
            transfers_needed = 1
        # For each transfer that is needed, add to the appropriate tips_needed counter
        for n in range(0, transfers_needed):
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

    pipette = Protocol.load_instrument(Pipette_Type, Pipette_Position, tip_racks)
    pipette.starting_tip = tip_racks[0].well(Starting_Tip)

    return(pipette, tip_racks)
