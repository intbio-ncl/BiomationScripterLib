import BiomationScripter as _BMS
import math
from typing import List, Dict

from pathlib import Path

########################

Source_Plate_Types = {
#   "type": [dead volume, max transfer volume, max storage volume], (volumes in uL)
    "384PP": [15, 2, 65],
    "384LDV": [3, 0.5, 12],
    "6RES": [250, 2800, 2800]
}

########################

class EchoProto_Template:
    def __init__(self,
        Name: str,
        Source_Plates: List[_BMS.Labware_Layout],
        Destination_Plate_Layout: _BMS.Labware_Layout,
        Picklist_Save_Directory: str = ".",
        Metadata: dict = None,
        Merge: bool = False
    ):

        #####################
        # Protocol Metadata #
        #####################
        self.name = Name
        self.metadata = Metadata
        self.save_dir = Picklist_Save_Directory
        self._protocol = _BMS.EchoProto.Protocol(Name)
        self.merge = Merge

        #################
        # Plate Layouts #
        #################
        self.source_plate_layouts = []
        self.destination_plate_layouts = []

        # Add source layouts to self.source_plate_layouts
        for source in Source_Plates:
            self.add_source_layout(source)

        # Add the destination layout (more may be created later if needed)
        #NOTE - This might break some things or cause unexpected behaviour
        if not Destination_Plate_Layout.get_available_wells():
            Destination_Plate_Layout.set_available_wells()
        Destination_Plate_Layout.clear_content()
        self.add_destination_layout(Destination_Plate_Layout)

    def create_picklists(self):
        _BMS.EchoProto.Generate_Actions(self._protocol)
        _BMS.EchoProto.Write_Picklists(self._protocol, self.save_dir, Merge = self.merge)

    def add_source_layout(self, Layout):
        # Check if Layout is a Labware_Layout object; if not, attempt to use it as a file location
        if type(Layout) is _BMS.Labware_Layout:
            pass
        elif type(Layout) is str:
            # Import file as a Labware_Layout object
            Layout = _BMS.Import_Labware_Layout(Layout)

        self.source_plate_layouts.append(Layout)
        self._protocol.add_source_plates([Layout])

    def add_destination_layout(self, Layout):
        # Check if Layout is a Labware_Layout object; if not, attempt to use it as a file location
        if type(Layout) is _BMS.Labware_Layout:
            pass
        elif type(Layout) is str:
            # Import file as a Labware_Layout object
            Layout = _BMS.Import_Labware_Layout(Layout)


        self.destination_plate_layouts.append(Layout)
        self._protocol.add_destination_plates([Layout])


# This is redundant (BMS.Create_Plates_Needed seems to do the same thing)
# def Calculate_And_Create_Plates(Plate_Format, Wells_Required, Wells_Available):
#     plates_required = math.ceil(Wells_Required/Wells_Available)
#     plates = []
#     for plate_index in range(0, plates_required):
#         name = "{}_{}".format(Plate_Format.name, plate_index)
#         plates.append(Plate_Format.clone_format(name))
#
#     return(plates)

def Write_Picklists(Protocol, Save_Location = ".", Merge = False): # Writes a Picklist to a csv pick list - argument is a Picklist Class
    if Merge:
        # Group transfer lists by source plate type
        Transfer_Lists = []
        for source_plate_type in Source_Plate_Types.keys():
            Transfer_Lists.append([TL[0] for TL in Protocol.transfer_lists if TL[0].source_plate.type == source_plate_type])

        while [] in Transfer_Lists:
            Transfer_Lists.remove([])
    else:
        Transfer_Lists = [[TL[0]] for TL in Protocol.transfer_lists]

    for transfer_lists_for_picklist in Transfer_Lists:

        if len(transfer_lists_for_picklist) > 1:
            Source_Plate_Names_Str = ""
        else:
            Source_Plate_Names_Str = f"-({transfer_lists_for_picklist[0].title})"


        Picklist_Title = f"{transfer_lists_for_picklist[0].source_plate.type}{Source_Plate_Names_Str}"

        filepath = Path(f"{Save_Location}/{Protocol.title}-{Picklist_Title}.csv")

        PickList = open(filepath, "w")
        PickList.write("UID,Source Plate Name,Source Plate Type,Source Well,Destination Plate Name,Destination Plate Type,Destination Well,Transfer Volume,Reagent\n")
        for transfer_list in transfer_lists_for_picklist:
            for action in transfer_list.get_actions():
                UID, Rea, SPN, Cali, SW, DPN, DPT, DW, Vol = action.get_all()
                SPT = transfer_list.source_plate.type + "_" + Cali
                line = f"{UID},{SPN},{SPT},{SW},{DPN},{DPT},{DW},{Vol},{Rea}\n"
                PickList.write(line)
        PickList.close()
        print(filepath)

def Generate_Actions(Protocol):
    Exceptions = []

    # Get all source plates
    Source_Plates = Protocol.source_plates

    # Get all destination plates
    Destination_Plates = Protocol.destination_plates

    ## Check that all reagents in the destination plates are in a source plate
    # get required reagents
    Required_Reagents = Protocol.get_required_reagents()
    # get available source reagents
    Available_Reagents = Protocol.get_available_reagents()
    # Check if there are any required reagents which are not present in a source plate
    Missing_Reagents = Required_Reagents.difference(Available_Reagents)

    if len(Missing_Reagents) > 0:
        raise _BMS.OutOFSourceMaterial("Cannot find the following reagents in a source plate: {}".format(Missing_Reagents))

    # Check if there is enough volume for each of the required reagents present in the source plates
    ## Also check that the storage volume is not above the maximum amount
    Exceptions = []
    Wells_Below_Dead_Volume = {}
    for required_reagent in Required_Reagents:
        required_volume = 0
        required_reagent_locations = Protocol.get_reagent_destination_locations(required_reagent)
        for location in required_reagent_locations:
            plate = location[0]
            well = location[1]
            required_volume += Protocol.get_reagent_volume(required_reagent, plate, well)

        available_volume = 0
        source_reagent_locations = Protocol.get_reagent_source_locations(required_reagent)
        for location in source_reagent_locations:
            plate = location[0]
            well = location[1]
            total_source_volume = Protocol.get_reagent_volume(required_reagent, plate, well)
            if plate.type in Source_Plate_Types.keys():
                dead_volume = Source_Plate_Types[plate.type][0]
                max_storage_volume = Source_Plate_Types[plate.type][2]
                if total_source_volume > max_storage_volume:
                    print("Volume of {} in {}, well {}, is {} uL above the maximum storage volume. This well will be ignored.".format(required_reagent, plate.name, well, total_source_volume - max_storage_volume))
                    plate.clear_content_from_well(well)
                    continue
            else:
                dead_volume = 0
                print("Can't seem to find source plate type for {} so dead volume set to 0, and no max transfer volume or max storage volume specified.".format(plate.name))

            if total_source_volume - dead_volume < 0:
                # If the available volume is below the dead volume, add nothing rather than adding a negative volume
                Wells_Below_Dead_Volume[well] = [plate.name, required_reagent, dead_volume-total_source_volume]
            else:
                available_volume += total_source_volume - dead_volume
        if available_volume < required_volume:
            extra_reagent_volume = required_volume-available_volume
            Exceptions.append([required_reagent, extra_reagent_volume, well, plate.name])

    for well in Wells_Below_Dead_Volume:
        plate_name = Wells_Below_Dead_Volume[well][0]
        reagent_name = Wells_Below_Dead_Volume[well][1]
        volume_below_dead = Wells_Below_Dead_Volume[well][2]
        print("Well {} of plate {} containing {} is {} uL below the dead volume.".format(well, plate_name, reagent_name, volume_below_dead))

    if len(Exceptions) > 0:
        error_text = "\n"
        error_csv_text = "\nName,Well,Plate,Volume Needed\n"
        for e in Exceptions:
            extra_volume_to_add = e[1]
            below_dead_volume_text = ".\n"
            if e[2] in Wells_Below_Dead_Volume.keys():
                if e[3] == Wells_Below_Dead_Volume[e[2]][0]:
                    below_dead_volume_text = ". This well is also {} uL below the dead volume.\n".format(Wells_Below_Dead_Volume[e[2]][2])
                    extra_volume_to_add = e[1] + Wells_Below_Dead_Volume[e[2]][2]
            error_text += "Not enough volume of {}. {} uL more is required. Last well checked was {} of {}{}\n".format(e[0], e[1], e[2], e[3], below_dead_volume_text)
            error_csv_text += "{},{},{},{}\n".format(e[0], e[2], e[3], extra_volume_to_add)
        raise _BMS.OutOFSourceMaterial(error_text + error_csv_text)

    ###########################
    # Generate transfer lists #
    ###########################

    # Generate a transfer list for each source plate
    for source_plate in Source_Plates:
        # Define dead volume, max transfer volume, and max storage volume for this source plate
        if source_plate.type in Source_Plate_Types.keys():
            dead_volume = Source_Plate_Types[source_plate.type][0]
            max_transfer_volume = Source_Plate_Types[source_plate.type][1]
            max_storage_volume = Source_Plate_Types[source_plate.type][2]
        else:
            dead_volume = 0
            max_transfer_volume = 10000
            max_storage_volume = 10000

        # Create the transfer list
        transfer_list = Protocol.make_transfer_list(source_plate)
        # Add transfer actions from the source plate based on required reagents in the destination plate(s)
        for destination_plate in Destination_Plates:
            # Get the required reagents in the current destination plate which are present in the current source plate
            required_reagents = Protocol.get_required_reagents(destination_plate)
            available_source_reagents = Protocol.get_available_reagents(source_plate)
            reagents_to_transfer = required_reagents.intersection(available_source_reagents)

            # For each reagent which will be transferred form this source plate
            for reagent in reagents_to_transfer:
                source_wells = source_plate.get_wells_containing_liquid(reagent)
                destination_locations = Protocol.get_reagent_destination_locations(reagent)

                # Iterate through the destination locations for the current reagent
                for destination in destination_locations:
                    destination_plate = destination[0]
                    destination_well = destination[1]
                    total_volume_to_transfer = Protocol.get_reagent_info(reagent, destination_plate, destination_well)[0]

                    # Transfer liquid from source well(s) to destination well until the total volume has been transferred
                    ## This may take multiple actions if the volume to transfer is above the max transfer volume, or multiple source wells are required
                    source_index = 0
                    while total_volume_to_transfer > 0:
                        # get current source location
                        source_well = source_wells[source_index]
                        liquid_class = Protocol.get_reagent_info(reagent, source_plate, source_well)[1]
                        # Check how much volume is available to transfer from the current source well
                        available_volume = Protocol.get_reagent_volume(reagent, source_plate, source_well) - dead_volume
                        # If the volume to transfer is below both the available volume and the max transfer volume, add the action to the transfer list
                        # If the current source well is empty
                        if available_volume < 0.025:
                            source_index += 1
                        elif total_volume_to_transfer <= max_transfer_volume and total_volume_to_transfer <= available_volume:
                            transfer_list.add_action(reagent,
                                liquid_class,
                                source_well,
                                destination_plate.name,
                                destination_plate.type,
                                destination_well,
                                int(total_volume_to_transfer * 1000)
                            )
                            source_plate.update_volume_in_well(Protocol.get_reagent_volume(reagent, source_plate, source_well) - total_volume_to_transfer, reagent, source_well)
                            total_volume_to_transfer = 0

                        # If the total volume to transfer is above the max transfer limit, but there is enough to transfer the max transfer from the current source well
                        elif total_volume_to_transfer > max_transfer_volume and available_volume >= max_transfer_volume:
                            transfer_list.add_action(reagent,
                                liquid_class,
                                source_well,
                                destination_plate.name,
                                destination_plate.type,
                                destination_well,
                                int(max_transfer_volume * 1000)
                            )
                            source_plate.update_volume_in_well(Protocol.get_reagent_volume(reagent, source_plate, source_well) - max_transfer_volume, reagent, source_well)
                            total_volume_to_transfer -= max_transfer_volume

                        # If the total volume to transfer is above the max transfer limit, and there isn't enough to transfer the max transfer from the current source well...
                        # ..., transfer the entire content of the current source well and iterate to the next source well
                        # Also if the total volume to transfer is below the max transfer limit, but there isn't enough to transfer the entire amount, do the same
                        elif (total_volume_to_transfer > max_transfer_volume and available_volume < max_transfer_volume) or (total_volume_to_transfer <= max_transfer_volume and available_volume < total_volume_to_transfer):
                            transfer_list.add_action(reagent,
                                liquid_class,
                                source_well,
                                destination_plate.name,
                                destination_plate.type,
                                destination_well,
                                int(available_volume * 1000)
                            )
                            total_volume_to_transfer -= available_volume
                            source_plate.update_volume_in_well(Protocol.get_reagent_volume(reagent, source_plate, source_well) - available_volume, reagent, source_well)
                            source_index += 1
                        else:
                            raise _BMS.OutOFSourceMaterial("Internal transfer error: unhandled transfer situation for {}. Please raise this protocol as an issue on GitHub.".format(reagent))
                        if source_index == len(source_wells):
                            raise _BMS.OutOFSourceMaterial("Internal calculation error: ran out of {} to transfer. Please raise this protocol as an issue on GitHub.".format(reagent))

#################################

class Protocol:
    def __init__(self,Title):
        self.title = Title
        self.source_plates = []
        self.destination_plates = []
        self.transfer_lists = []

    def add_source_plate(self,Plate):
        self.source_plates.append(Plate)

    def add_source_plates(self, Plates):
        for p in Plates:
            self.add_source_plate(p)

    def make_transfer_list(self, Source_Plate):
        TL = TransferList(Source_Plate)
        self.transfer_lists.append([TL])
        return(TL)

    def get_transfer_list(self,Source_Plate):
        for tl in self.transfer_lists:
            if Source_Plate == tl.source_plate:
                return(tl)

    def add_destination_plate(self, Destination_Plate):
        self.destination_plates.append(Destination_Plate)

    def add_destination_plates(self, Destination_Plates):
        for Destination_Plate in Destination_Plates:
            self.destination_plates.append(Destination_Plate)

    def get_destination_plates(self):
        return(self.destination_plates)

    def get_source_plates(self):
        return(self.source_plates)

    def get_required_reagents(self, Destination_Plate = None):
        if Destination_Plate:
            Destination_Plates = [Destination_Plate]
        else:
            Destination_Plates = self.get_destination_plates()

        Required_Reagents = set()
        for plate in Destination_Plates:
            occupied_wells = plate.get_content().keys()
            for well in occupied_wells:
                reagents_in_well = set( [reagent_info.name for reagent_info in plate.get_content()[well]] )
                Required_Reagents = Required_Reagents.union(reagents_in_well)

        return(Required_Reagents)

    def get_available_reagents(self, Source_Plate = None):
        if Source_Plate:
            Source_Plates = [Source_Plate]
        else:
            Source_Plates = self.get_source_plates()

        Available_Reagents = set()
        for plate in Source_Plates:
            occupied_wells = plate.get_content().keys()
            for well in occupied_wells:
                reagents_in_well = set( [reagent_info.name for reagent_info in plate.get_content()[well]] )
                Available_Reagents = Available_Reagents.union(reagents_in_well)

        return(Available_Reagents)

    def get_reagent_volume(self, Reagent_Name, Plate, Well):
        try:
            Reagents = Plate.get_content()[Well]
        except KeyError:
            raise KeyError("Well {} not found when searching for {} in plate {}.\nPlate Content:\n{}".format(Well, Reagent_Name, Plate.name, Plate.get_content()))
        for reagent_info in Reagents:
            if reagent_info.name == Reagent_Name:
                return(reagent_info.volume)

        return(None)

    def get_reagent_info(self, Reagent_Name, Plate, Well):
        Reagents = Plate.get_content()[Well]
        for reagent_info in Reagents:
            if reagent_info.name == Reagent_Name:
                return(reagent_info.get_info()[1:])

        return(None)

    def get_reagent_source_locations(self, Reagent_Name):
        Source_Plates = self.get_source_plates()
        Locations = []
        for plate in Source_Plates:
            occupied_wells = plate.get_occupied_wells()
            for well in occupied_wells:
                for reagent in plate.get_content()[well]:
                    if reagent.name == Reagent_Name:
                        Locations.append([plate, well])

        if len(Locations) > 0:
            return(Locations)
        else:
            return(None)

    def get_reagent_destination_locations(self, Reagent_Name):
        Destination_Plates = self.get_destination_plates()
        Locations = []
        for plate in Destination_Plates:
            occupied_wells = plate.get_occupied_wells()
            for well in occupied_wells:
                for reagent in plate.get_content()[well]:
                    if reagent.name == Reagent_Name:
                        Locations.append([plate, well])

        if len(Locations) > 0:
            return(Locations)
        else:
            return(None)

class TransferList:
    ## Class for storing the TransferList
    def __init__(self,Source_Plate):
        ## Initialise TransferList with the TransferList's title
        self.title = Source_Plate.name
        self.source_plate = Source_Plate
        ## Create properties to store actions and source plate type
        self._actions = [] # When populated has form [ Action Class, Action Class, ..., Action Class]
        self.__actionUIDs = []
        self._source_plate_type = Source_Plate.type
        # list of allowed source plate types
        self.__source_plate_types = {"384PP", "384LDV", "6RES"}

    ## Getter and Setter for source plate type
    def get_source_plate_type(self):
        return(self._source_plate_type)

    ## Getter and Setter for actions
    def get_actions(self):
        return(self._actions)
    def get_action_by_uid(self, UID):
        return(next((x for x in self._actions if x.get_uid() == UID),None))

    def add_action(self, Reagent, Calibration, Source_Well, Destination_Plate_Name, Destination_Plate_Type, Destination_Well, Volume):

        # Generate UID for the action
        if len(self._actions) == 0:
            UID = 0
        else:
            UID = max(self.__actionUIDs) + 1
        self.__actionUIDs.append(UID)
        ## Create action class and append to self._actions
        self._actions.append(Action(UID, Reagent, self.source_plate, Calibration, Source_Well, Destination_Plate_Name, Destination_Plate_Type, Destination_Well))
        ## Add transfer volume to newly created action
        self.get_action_by_uid(UID).set_volume(Volume)

class Action:
    ## Class for storing information about a liquid transfer action
    def __init__(self, UID, Reagent, Source_Plate, Calibration, Source_Well, Destination_Plate_Name, Destination_Plate_Type, Destination_Well):
        self.__uid = UID
        self.reagent = Reagent
        self.source_plate = Source_Plate
        self.calibration = Calibration
        self.source_well = Source_Well
        self.destination_plate_name = Destination_Plate_Name
        self.destination_plate_type = Destination_Plate_Type
        self.destination_well = Destination_Well
        self._volume = None

    ## Setter and Getter for volume
    def set_volume(self, Volume): #Volume in nL
        source_plate_type = self.source_plate.type
        if isinstance(Volume, float):
            raise TypeError("Transfer Volume must be an integer")
        elif int(Volume) < 25:
            raise _BMS.TransferError("Cannot transfer {} at {} nL; Transfer Volume must be more than 25 nL for Echo 525".format(self.reagent,Volume))
        elif source_plate_type == "384PP" and int(Volume) > 2000:
            raise _BMS.TransferError("Cannot transfer {} at {} nL; Maximum transfer volume from 384PP plates is 2000 nL".format(self.reagent,Volume))
        elif source_plate_type == "384LDV" and int(Volume) > 500:
            raise _BMS.TransferError("Cannot transfer {} at {} nL; Maximum transfer volume from 384LDV plates is 500 nL".format(self.reagent,Volume))
        self._volume = int(Volume)

    def get_volume(self):
        return(self._volume)

    ## Getter for uid
    def get_uid(self):
        return(self.__uid)

    ## Getter for all values as a list
    def get_all(self):
        return([self.__uid, self.reagent, self.source_plate.name, self.calibration, self.source_well, self.destination_plate_name, self.destination_plate_type, self.destination_well, self._volume])
