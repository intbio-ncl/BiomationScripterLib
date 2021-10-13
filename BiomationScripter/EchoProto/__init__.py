import BiomationScripter as _BMS
import math

Source_Plate_Types = {
#   "type": [dead volume, max transfer volume, max storage volume], (volumes in uL)
    "384PP": [15, 2, 65],
    "384LDV": [3, 0.5, 12],
    "6RES": [250, 2800, 2800]
}



def Write_Picklists(Protocol, Save_Location): # Writes a Picklist to a csv pick list - argument is a Picklist Class
    for tl in Protocol.transfer_lists:
        TL = tl[0]
        Title = TL.title
        SPType = TL.source_plate.type

        PickList = open(Save_Location+"/"+Protocol.title + "-" + Title + ".csv", "w")
        PickList.write("UID,Source Plate Name,Source Plate Type,Source Well,Destination Plate Name,Destination Plate Type,Destination Well,Transfer Volume,Reagent\n")
        for action in TL.get_actions():
            UID, Rea, SPN, Cali, SW, DPN, DPT, DW, Vol = action.get_all()
            SPT = SPType + "_" + Cali
            line = str(UID) + "," + SPN + "," + SPT + "," + SW + "," + DPN + "," + DPT + "," + DW + "," + str(Vol) + "," + Rea + "\n" # Make less stupid (#DougKnows)
            PickList.write(line)
        PickList.close()
        print(Save_Location+"/"+Protocol.title + "-" + Title + ".csv")

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
        raise ValueError("Cannot find the following reagents in a source plate: {}".format(Missing_Reagents))

    # Check if there is enough volume for each of the required reagents present in the source plates
    ## Also check that the storage volume is not above the maximum amount
    Exceptions = []
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
                print("Can't find source plate type for {} so dead volume set to 0, and no max transfer volume or max storage volume specified.".format(plate.name))

            available_volume += total_source_volume - dead_volume

        if available_volume < required_volume:
            Exceptions.append([required_reagent, required_volume-available_volume])

    if len(Exceptions) > 0:
        error_text = ""
        for e in Exceptions:
            error_text += "Source plates do not contain enough volume of {}. {} uL more is required.\n".format(e[0], e[1])
        raise ValueError(error_text)

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
                        if total_volume_to_transfer <= max_transfer_volume and total_volume_to_transfer <= available_volume:
                            transfer_list.add_action(reagent,
                                liquid_class,
                                source_well,
                                destination_plate.name,
                                destination_plate.type,
                                destination_well,
                                int(total_volume_to_transfer * 1000)
                            )
                            total_volume_to_transfer = 0
                            source_plate.update_volume_in_well(Protocol.get_reagent_volume(reagent, source_plate, source_well) - total_volume_to_transfer, reagent, source_well)
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
                            total_volume_to_transfer -= max_transfer_volume
                            source_plate.update_volume_in_well(Protocol.get_reagent_volume(reagent, source_plate, source_well) - max_transfer_volume, reagent, source_well)
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
                        # If the current source well is empty
                        elif available_volume < 0.025:
                            source_index += 1
                        else:
                            raise ValueError("Internal transfer error: unhandled transfer situation for {}. Please raise this protocol as an issue on GitHub.".format(reagent))
                        if source_index == len(source_wells):
                            raise ValueError("Internal calculation error: ran out of {} to transfer. Please raise this protocol as an issue on GitHub.".format(reagent))



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
        self.destination_plates.append(D_Plate)

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
                reagents_in_well = set( [reagent_info[0] for reagent_info in plate.get_content()[well]] )
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
                reagents_in_well = set( [reagent_info[0] for reagent_info in plate.get_content()[well]] )
                Available_Reagents = Available_Reagents.union(reagents_in_well)

        return(Available_Reagents)

    def get_reagent_volume(self, Reagent_Name, Plate, Well):
        try:
            Reagents = Plate.get_content()[Well]
        except KeyError:
            raise KeyError("Well {} not found when searching for {} in plate {}.\nPlate Content:\n{}".format(Well, Reagent_Name, Plate.name, Plate.get_content()))
        for reagent_info in Reagents:
            if reagent_info[0] == Reagent_Name:
                return(reagent_info[1])

        return(None)

    def get_reagent_info(self, Reagent_Name, Plate, Well):
        Reagents = Plate.get_content()[Well]
        for reagent_info in Reagents:
            if reagent_info[0] == Reagent_Name:
                return(reagent_info[1:])

        return(None)

    def get_reagent_source_locations(self, Reagent_Name):
        Source_Plates = self.get_source_plates()
        Locations = []
        for plate in Source_Plates:
            occupied_wells = plate.get_occupied_wells()
            for well in occupied_wells:
                for reagent in plate.get_content()[well]:
                    if reagent[0] == Reagent_Name:
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
                    if reagent[0] == Reagent_Name:
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
            raise ValueError("Cannot transfer {} at {} nL; Transfer Volume must be more than 25 nL for Echo 525".format(self.reagent,Volume))
        elif source_plate_type == "384PP" and int(Volume) > 2000:
            raise ValueError("Cannot transfer {} at {} nL; Maximum transfer volume from 384PP plates is 2000 nL".format(self.reagent,Volume))
        elif source_plate_type == "384LDV" and int(Volume) > 500:
            raise ValueError("Cannot transfer {} at {} nL; Maximum transfer volume from 384LDV plates is 500 nL".format(self.reagent,Volume))
        self._volume = int(Volume)

    def get_volume(self):
        return(self._volume)

    ## Getter for uid
    def get_uid(self):
        return(self.__uid)

    ## Getter for all values as a list
    def get_all(self):
        return([self.__uid, self.reagent, self.source_plate.name, self.calibration, self.source_well, self.destination_plate_name, self.destination_plate_type, self.destination_well, self._volume])
