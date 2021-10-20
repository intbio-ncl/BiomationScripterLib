import BiomationScripter as _BMS

Source_Plate_Types = {
#   "type": [dead volume, max transfer volume, max storage volume], (volumes in uL)
    "384PP": [15, 2, 65],
    "384LDV": [3, 0.5, 12],
    "6RES": [250, 2800, 2800]
}

def Write_Picklists(Protocol, Save_Location): # Writes a Picklist to a csv pick list - argument is a Picklist Class
    for tl in Protocol.transferlists:
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

    S_Plates = Protocol.source_plates # Get all source plates

    # Get all destination plates
    D_Plates = []
    for dp in Protocol.destination_plates:
        D_Plates.append(dp[0])

    ## Check that all reagents in the destination plates are in a source plate
    # Find required reagents
    Required_Reagents = set()
    for d in D_Plates:
        for w in d.get_content().keys():
            Required_Reagents = Required_Reagents.union( set( [r[0] for r in d.get_content()[w]] ) )
    # Check that reagents are in a source plate # Will need to add in volume checking and account for dead volume
    Available_Reagents = set()
    for sp in S_Plates:
        S_Wells = list(sp.get_content().keys())
        Available_Reagents = Available_Reagents.union( set([sp.get_content()[w][0][0] for w in S_Wells]) )
    # Compare required reagents with Available_Reagents
    if len(Required_Reagents.difference(Available_Reagents)) == 0:
        pass
    else:
        raise ValueError("Cannot find the following reagents in a source plate: {}".format(Required_Reagents.difference(Available_Reagents)))
        # Add in ability to input different name without exiting the script???


    for sp in S_Plates: # For each TransferList/source plate
        # Define dead volume, max transfer volume, and max storage volume for this source plate
        if sp.type in Source_Plate_Types.keys():
            dead_volume = Source_Plate_Types[sp.type][0]
            max_transfer_volume = Source_Plate_Types[sp.type][1]
            max_storage_volume = Source_Plate_Types[sp.type][2]
        else:
            dead_volume = 0
            max_transfer_volume = None
            max_storage_volume = None
            print("Can't find source plate type, dead volume set to 0, and no max transfer volume or max storage volume specified.")
        # Check if any source plate wells contain too much volume
        if max_storage_volume:
            for source_well in sp.get_content():
                source_reagent_name = sp.get_content()[source_well][0][0]
                source_well_volume = sp.get_content()[source_well][0][1]
                if source_well_volume > max_storage_volume:
                    raise ValueError("Too much volume of {} in well {}, plate {} (current: {}, max: {}).".format(source_reagent_name,source_well,sp.name, source_well_volume, max_storage_volume))

        proto = Protocol.make_transfer_list(sp)
        for dp in D_Plates: # loop through all destination plates
            # print(dp.name)
            for destination_well in dp.get_content(): # Get each well and each required reagent
                for d_reagent_info in dp.get_content()[destination_well]:
                    d_reagent_name = d_reagent_info[0]
                    d_reagent_volume = d_reagent_info[1]
                    # Get a list of source wells which contain the required reagent
                    source_wells = []
                    for source_well in sp.get_content(): # Iterate through all specified wells in the current source plate
                        if d_reagent_name in sp.get_content()[source_well][0][0]: # If the reagent is in the source well
                            source_wells.append([source_well, sp.get_content()[source_well][0]]) # Add that source well and its contents to the source_wells list

                    n_source_well = 0 # counter for reagents in multiple source wells, formerly swn
                    for source_well in source_wells: # formerly sw
                        n_source_well += 1
                        # Check enough volume in source well
                        sw_volume = source_well[1][1]
                        available_sw_volume = sw_volume - dead_volume
                        sw_liquid_class = source_well[1][2]
                        # required_volume = reagent[1] Now d_reagent_volume

                        if available_sw_volume < d_reagent_volume: # If the current source well doesn't have enough volume
                            if n_source_well == len(source_wells): # Check if there are more source wells with the same reagent (true if there aren't any more)
                                Exceptions.append([d_reagent_name,source_well[0],sp.name,d_reagent_volume,available_sw_volume])
                                # raise ValueError("Not enough volume in source plate for {} (well {}, plate {})).".format(reagent[0],source_well[0],sp.name))
                            else: # If there are more, continue on to the next source well and try again
                                continue
                        else: # If the current source well does have enough volume
                            if max_transfer_volume and (d_reagent_volume > max_transfer_volume):
                                while d_reagent_volume >= max_transfer_volume:
                                    # Add liquid transfer action for the max transfer volume
                                    proto.add_action(d_reagent_name, sw_liquid_class, source_well[0], dp.name, dp.type, destination_well, int(max_transfer_volume*1000))
                                    # Record that liquid has transfered
                                    source_well[1][1] = source_well[1][1] - max_transfer_volume
                                    d_reagent_volume -= max_transfer_volume

                                if d_reagent_volume != 0:
                                    # Add liquid transfer action for remaining liquid to transfer
                                    proto.add_action(d_reagent_name, sw_liquid_class, source_well[0], dp.name, dp.type, destination_well, int(d_reagent_volume*1000))
                                    # Record that liquid has transfered
                                    source_well[1][1] = source_well[1][1] - d_reagent_volume
                                    d_reagent_volume -= d_reagent_volume
                            else:
                                # Add liquid transfer action for remaining liquid to transfer
                                proto.add_action(d_reagent_name, sw_liquid_class, source_well[0], dp.name, dp.type, destination_well, int(d_reagent_volume*1000))
                                # Record that liquid has transfered
                                source_well[1][1] = source_well[1][1] - d_reagent_volume
                                d_reagent_volume -= d_reagent_volume
                            break
    if len(Exceptions) > 0:
        Exception_Text = "\n"
        reagent_exceptions = set()
        for e in Exceptions:
            reagent_exceptions.add(e[0])

        for reagent in reagent_exceptions:
            volume_lacking = 0
            for e in Exceptions:
                if reagent == e[0]:
                    volume_lacking += e[3]
                    available = e[4]
            Exception_Text += "Lacking at least {} uL of {}\n".format(volume_lacking - available, reagent)
        raise ValueError(Exception_Text)


                            # if sp.type == "384PP" and int(float(required_volume)*1000) > 2000:
                            #     transfer_volume = int(float(required_volume)*1000)
                            #     while transfer_volume >= 2000:
                            #         proto.add_action(reagent[0], sw[1][0][2], sw[0], dp.name, dp.type, well, 2000) # Add action (volume in nL)
                            #         sp.get_content()[sw[0]][0][1] -= 2000/1000 # Remove volume from source plate
                            #         transfer_volume -= 2000
                            #     if transfer_volume != 0:
                            #         # print(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, transfer_volume)
                            #         proto.add_action(reagent[0], sw[1][0][2], sw[0], dp.name, dp.type, well, transfer_volume) # Add action (volume in nL)
                            #
                            #         sp.get_content()[sw[0]][0][1] -= transfer_volume/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                            #         break
                            #     else:
                            #         break
                            # elif sp.type == "384LDV" and int(float(required_volume)*1000) > 500:
                            #     transfer_volume = int(float(required_volume)*1000)
                            #     while transfer_volume >= 500:
                            #         proto.add_action(reagent[0], sw[1][0][2], sw[0], dp.name, dp.type, well, 500) # Add action (volume in nL)
                            #         sp.get_content()[sw[0]][0][1] -= 500/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                            #         transfer_volume -= 500
                            #     if transfer_volume != 0:
                            #         proto.add_action(reagent[0], sw[1][0][2], sw[0], dp.name, dp.type, well, transfer_volume) # Add action (volume in nL)
                            #         sp.get_content()[sw[0]][0][1] -= transfer_volume/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                            #         break
                            #     else:
                            #         break
                            # else:
                            #     proto.add_action(reagent[0], sw[1][0][2], sw[0], dp.name, dp.type, well, int(float(required_volume)*1000)) # Add action (volume in nL)
                            #     sp.get_content()[sw[0]][0][1] -= required_volume # Remove volume from source plate (but DON'T save changes to plate file)
                            #     break


class Protocol:
    def __init__(self,Title):
        self.title = Title
        self.source_plates = []
        self.destination_plates = []
        self.transferlists = []

    def add_source_plate(self,Plate):
        self.source_plates.append(Plate)

    def add_source_plates(self, Plates):
        for p in Plates:
            self.add_source_plate(p)

    def make_transfer_list(self,Source_Plate):
        TL = TransferList(Source_Plate)
        self.transferlists.append([TL])
        return(TL)

    def get_transfer_list(self,Source_Plate):
        for tl in self.transferlists:
            if Source_Plate == tl.source_plate:
                return(tl)
                break

    def add_destination_plate(self,Plate,Use_Outer_Wells = True):
        D_Plate = Plate
        self.destination_plates.append([D_Plate, Use_Outer_Wells])

    def add_destination_plates(self, Plates, Use_Outer_Wells = True):
        for D_Plate in Plates:
            self.add_destination_plate(D_Plate, Use_Outer_Wells)

    def get_destination_plates(self):
        return(self.destination_plates)

    def get_source_plates(self):
        return(self.source_plates)


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
