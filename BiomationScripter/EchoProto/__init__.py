import BiomationScripter as _BMS

def writePickLists(Protocol, SaveLocation): # Writes a Picklist to a csv pick list - argument is a Picklist Class
    for tl in Protocol.transferlists:
        TL = tl[0]
        Title = TL.title
        SPType = TL.source_plate.type

        PickList = open(SaveLocation+"/"+Protocol.title + "-" + Title + ".csv", "w")
        PickList.write("UID,Source Plate Name,Source Plate Type,Source Well,Destination Plate Name,Destination Plate Type,Destination Well,Transfer Volume,Reagent\n")
        for action in TL.get_actions():
            UID, Rea, SPN, Cali, SW, DPN, DPT, DW, Vol = action.get_all()
            SPT = SPType + "_" + Cali
            line = str(UID) + "," + SPN + "," + SPT + "," + SW + "," + DPN + "," + DPT + "," + DW + "," + str(Vol) + "," + Rea + "\n" # Make less stupid (#DougKnows)
            PickList.write(line)
        PickList.close()
        print(SaveLocation+"/"+Protocol.title + "-" + Title + ".csv")

def Generate_Actions(Protocol):
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
        # print(sp.name)
        proto = Protocol.make_transfer_list(sp)
        for dp in D_Plates: # loop through all destination plates
            # print(dp.name)
            for well in dp.get_content(): # Get each well and each required reagent
                for reagent in dp.get_content()[well]:
                    source_wells = [ [w,sp.get_content()[w]] for w in sp.get_content() if reagent[0] in sp.get_content()[w][0] ] # Get source well(s) with required reagent
                    swn = 0 # counter for reagents in multiple source wells
                    # print(source_wells)
                    for sw in source_wells:
                        swn += 1
                        # Check enough volume in source well
                        # print(sw)
                        deadVolume = 0
                        if sp.type == "384PP":
                            deadVolume = 15
                        elif sp.type == "384LDV":
                            deadvolume = 3
                        elif sp.type == "6RES":
                            deadvolume = 250
                        else:
                            print("Can't find source plate type, dead volume set to 0.")
                        sw_volume = sw[1][0][1] - deadVolume
                        required_volume = reagent[1]
                        if sw_volume < required_volume:
                            if swn == len(source_wells): # Check if there are more source wells with the same reagent (true if there aren't any more)
                                raise ValueError("Not enough volume in source plate for {} (well {}, plate {}); requires {} uL more (total volume required = {} uL).".format(reagent[0],sw[0],sp.name,(required_volume + deadVolume)-sw_volume, required_volume))
                            else:
                                continue
                        else:
                            if sp.type == "384PP" and int(float(required_volume)*1000) > 2000:
                                transfer_volume = int(float(required_volume)*1000)
                                while transfer_volume >= 2000:
                                    proto.add_action(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, 2000) # Add action (volume in nL)
                                    sp.get_content()[sw[0]][0][1] -= 2000/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                                    transfer_volume -= 2000
                                if transfer_volume != 0:
                                    # print(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, transfer_volume)
                                    proto.add_action(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, transfer_volume) # Add action (volume in nL)

                                    sp.get_content()[sw[0]][0][1] -= transfer_volume/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                                    break
                                else:
                                    break
                            elif sp.type == "384LDV" and int(float(required_volume)*1000) > 500:
                                transfer_volume = int(float(required_volume)*1000)
                                while transfer_volume >= 500:
                                    proto.add_action(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, 500) # Add action (volume in nL)
                                    sp.get_content()[sw[0]][0][1] -= 500/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                                    transfer_volume -= 500
                                if transfer_volume != 0:
                                    proto.add_action(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, transfer_volume) # Add action (volume in nL)
                                    sp.get_content()[sw[0]][0][1] -= transfer_volume/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                                    break
                                else:
                                    break
                            else:
                                proto.add_action(reagent[0], sp.name, sw[1][0][2], sw[0], dp.name, dp.type, well, int(float(required_volume)*1000)) # Add action (volume in nL)
                                sp.get_content()[sw[0]][0][1] -= required_volume/1000 # Remove volume from source plate (but DON'T save changes to plate file)
                                break
                    # print(proto.get_actions())


# class TransferList:
#     ## Class for storing the TransferList
#     def __init__(self,Title):
#         ## Initialise TransferList with the TransferList's title and list of allowed source plate types
#         self.title = Title
#         self.__source_plate_types = {"384PP", "384LDV", "6RES"}
#         ## Create properties to store actions and source plate type
#         self._actions = [] #When populated has form [ [Action Class], [Action Class], ..., [Action Class]]
#         self.__actionUIDs = []
#         self._source_plate_type = None
#
#     ## Getter and Setter for source plate type
#     def get_source_plate_type(self):
#         return(self._source_plate_type)
#     def set_source_plate_type(self, source_plate_type):
#         if not source_plate_type in self.__source_plate_types:
#             raise ValueError("Supported source plate types are: 384PP, 384LDV, and 6RES")
#         self._source_plate_type = source_plate_type
#
#     ## Getter and Setter for actions
#     def get_actions(self):
#         return(self._actions)
#     def get_actionByUID(self, UID):
#         return(next((x for x in self._actions if x.get_uid() == UID),None))
#     def add_action(self, Reagent, SourcePlateName, Calibration, SourceWell, DestinationPlateName, DestinationPlateType, DestinationWell, Volume):
#         ## Generate UID for the action
#         if len(self._actions) == 0:
#             UID = 0
#         else:
#             UID = max(self.__actionUIDs) + 1
#         self.__actionUIDs.append(UID)
#         ## Create action class and append to self._actions
#         self._actions.append(Action(UID, Reagent, SourcePlateName, Calibration, SourceWell, DestinationPlateName, DestinationPlateType, DestinationWell))
#         ## Add transfer volume to newly created action
#         self.get_actionByUID(UID).set_volume(Volume, self.get_source_plate_type())
#
# class Action:
#     ## Class for storing information about a liquid transfer action
#     def __init__(self, UID, Reagent, SourcePlateName, Calibration, SourceWell, DestinationPlateName, DestinationPlateType, DestinationWell):
#         self.__uid = UID
#         self.reagent = Reagent
#         self.sourcePlateName = SourcePlateName
#         self.calibration = Calibration
#         self.sourceWell = SourceWell
#         self.destinationPlateName = DestinationPlateName
#         self.destinationPlateType = DestinationPlateType
#         self.destinationWell = DestinationWell
#         self._volume = None
#
#     ## Getter for uid
#     def get_uid(self):
#         return(self.__uid)
#
#     ## Setter and Getter for volume
#     def get_volume(self):
#         return(self._volume)
#     def set_volume(self, Volume, source_plate_type): #Volume in nL
#         if isinstance(Volume, float):
#             raise TypeError("Transfer Volume must be an integer")
#         elif int(Volume) < 25:
#             raise ValueError("Cannot transfer {} at {} nL; Transfer Volume must be more than 25 nL for Echo 525".format(self.reagent,Volume))
#         elif source_plate_type == "384PP" and int(Volume) > 2000:
#             raise ValueError("Cannot transfer {} at {} nL; Maximum transfer volume from 384PP plates is 2000 nL".format(self.reagent,Volume))
#         elif source_plate_type == "384LDV" and int(Volume) > 500:
#             raise ValueError("Cannot transfer {} at {} nL; Maximum transfer volume from 384LDV plates is 500 nL".format(self.reagent,Volume))
#         self._volume = int(Volume)
#
#     ## Getter for all values as a list
#     def get_all(self):
#         return([self.__uid, self.reagent, self.sourcePlateName, self.calibration, self.sourceWell, self.destinationPlateName, self.destinationPlateType, self.destinationWell, self._volume])



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

    # def add_sourcePlate(self,Source_Plate):
    #     proto_found = False
    #     for p in range(0,len(self.transferlists)):
    #         if TransferList_Title == self.transferlists[p][0].title: # Find TransferList with specified title
    #             proto_found = True
    #             plate_found = False
    #             for plate in self.plates:
    #                 # print(Source_Plate_Title,plate.name)
    #                 if Source_Plate_Title == plate.name: # Find plate with specified title
    #                     plate_found = True
    #                     Plate = plate
    #                     break
    #             if not plate_found:
    #                 raise FileNotFoundError("No Such Plate '{}' Exists".format(Source_Plate_Title))
    #             if len(self.transferlists[p]) == 1: # Check if a sourceplate is already associated (True if no plate associated)
    #                 self.transferlists[p].append(Plate)
    #                 self.transferlists[p][0].set_source_plate_type(Plate.get_source_plate_type()) # Add source plate type to TransferList object
    #             else:
    #                 replace = ""
    #                 while replace != "N":
    #                     replace = input("Replace current source plate (" + self.transferlists[p][1].name + ")? (Y or N): ")
    #                     if replace == "Y":
    #                         break
    #                 if replace == "Y":
    #                     self.transferlists[p][1] = Plate
    #                     self.transferlists[p][0].set_source_plate_type(Plate.get_source_plate_type()) # Add source plate type to TransferList object
    #                 elif replace == "N":
    #                     print("Plate not replaced")
    #     if not proto_found:
    #         raise FileNotFoundError("No Such TransferList '{}' Exists".format(TransferList_Title))

class TransferList:
    ## Class for storing the TransferList
    def __init__(self,Source_Plate):
        ## Initialise TransferList with the TransferList's title and list of allowed source plate types
        self.title = Source_Plate.name
        self.source_plate = Source_Plate
        self.__source_plate_types = {"384PP", "384LDV", "6RES"}
        ## Create properties to store actions and source plate type
        self._actions = [] # When populated has form [ [Action Class], [Action Class], ..., [Action Class]]
        self.__actionUIDs = []
        self._source_plate_type = Source_Plate.type

    ## Getter and Setter for source plate type
    def get_source_plate_type(self):
        return(self._source_plate_type)

    ## Getter and Setter for actions
    def get_actions(self):
        return(self._actions)
    def get_actionByUID(self, UID):
        return(next((x for x in self._actions if x.get_uid() == UID),None))
    def add_action(self, Reagent, SourcePlateName, Calibration, SourceWell, DestinationPlateName, DestinationPlateType, DestinationWell, Volume):
        # print("Add action for " + Reagent)
        ## Generate UID for the action
        if len(self._actions) == 0:
            UID = 0
        else:
            UID = max(self.__actionUIDs) + 1
        self.__actionUIDs.append(UID)
        ## Create action class and append to self._actions
        self._actions.append(Action(UID, Reagent, SourcePlateName, Calibration, SourceWell, DestinationPlateName, DestinationPlateType, DestinationWell))
        ## Add transfer volume to newly created action
        self.get_actionByUID(UID).set_volume(Volume, self.get_source_plate_type())

class Action:
    ## Class for storing information about a liquid transfer action
    def __init__(self, UID, Reagent, SourcePlateName, Calibration, SourceWell, DestinationPlateName, DestinationPlateType, DestinationWell):
        self.__uid = UID
        self.reagent = Reagent
        self.sourcePlateName = SourcePlateName
        self.calibration = Calibration
        self.sourceWell = SourceWell
        self.destinationPlateName = DestinationPlateName
        self.destinationPlateType = DestinationPlateType
        self.destinationWell = DestinationWell
        self._volume = None

    ## Getter for uid
    def get_uid(self):
        return(self.__uid)

    ## Setter and Getter for volume
    def get_volume(self):
        return(self._volume)
    def set_volume(self, Volume, source_plate_type): #Volume in nL
        if isinstance(Volume, float):
            raise TypeError("Transfer Volume must be an integer")
        elif int(Volume) < 25:
            raise ValueError("Cannot transfer {} at {} nL; Transfer Volume must be more than 25 nL for Echo 525".format(self.reagent,Volume))
        elif source_plate_type == "384PP" and int(Volume) > 2000:
            raise ValueError("Cannot transfer {} at {} nL; Maximum transfer volume from 384PP plates is 2000 nL".format(self.reagent,Volume))
        elif source_plate_type == "384LDV" and int(Volume) > 500:
            raise ValueError("Cannot transfer {} at {} nL; Maximum transfer volume from 384LDV plates is 500 nL".format(self.reagent,Volume))
        self._volume = int(Volume)

    ## Getter for all values as a list
    def get_all(self):
        return([self.__uid, self.reagent, self.sourcePlateName, self.calibration, self.sourceWell, self.destinationPlateName, self.destinationPlateType, self.destinationWell, self._volume])
