#!/usr/bin/env python

####################################################
# Import BiomationScripter to help write protocols #
####################################################
import sys
sys.path.insert(0, "/var/lib/jupyter/notebooks/Packages/")
import BiomationScripter as BMS
import BiomationScripter.OTProto.Templates as Templates

##################################
# Record the protocol's metadata #
##################################
metadata = {
    'protocolName': 'OT-2_Example_Spot_Plating_Protocol',
    'author': 'Bradley Brown',
    'author-email': 'b.bradley2@newcastle.ac.uk',
    'user': '',
    'user-email': '',
    'source': 'Custom Protocol inspired by 10.1093/synbio/ysaa010',
    'apiLevel': '2.10',
    'robotName': 'Robo' # This is the name of the OT2 you plan to run the protocol on
}

##############################################################
# Use this code to call the Spot Plating protocol template #
##############################################################

def run(protocol):

    #################################################
    # Add information needed for the protocol here: #
    #################################################

    Cells = [
    "DNA1",
    "DNA2",
    "DNA3",
    "DNA4",
    "DNA5",
    "DNA6",
    "DNA7",
    "DNA8"
    ]

    Cell_Source_Plate_Type = "nunclondeltasurface163320_96_wellplate_250ul"

    Dilution_Plate_Type = "nunclondeltasurface163320_96_wellplate_250ul"

    Cell_Wells = BMS.well_range("A1:A8")

    Plating_Volume = 10 #uL

    Dilution_Factors = [1, 10, 100, 1000, 2000, 5000, 8000, 10000]

    Starting_tip_position_20uL = "A1"

    Starting_tip_position_300uL = "A1"

    Simulate = False

    #################################################
    #################################################
    #################################################

    ##############################################################
    # The code below creates the protocol to be ran or simulated #
    ##############################################################

    Spot_Plating  = BMS.OTProto.Templates.Spot_Plating (
        Protocol=protocol,
        Name=metadata["protocolName"],
        Metadata=metadata,
        Cells=Cells,
        Cell_Source_Wells=Cell_Wells,
        Cell_Source_Type=Cell_Source_Plate_Type,
        Dilution_Plate_Type=Dilution_Plate_Type,
        Plating_Volume=Plating_Volume,
        Dilution_Factors=Dilution_Factors,
        Starting_20uL_Tip=Starting_tip_position_20uL,
        Starting_300uL_Tip=Starting_tip_position_300uL,
        Simulate = Simulate
    )
    Spot_Plating.run()


######################################################################
# Use this code if simulating the protocol, otherwise comment it out #
######################################################################

##########################################################################################################
# IMPORTANT - the protocol will not upload to the opentrons if this cell is not commented out or removed #
##########################################################################################################

# from opentrons import simulate as OT2 # This line simulates the protocol
# # Get the correct api version
# protocol = OT2.get_protocol_api('2.10')
# # Home the pipetting head
# protocol.home()
# # Call the 'run' function to run the protocol
# run(protocol)
# for line in protocol.commands():
#     print(line)
