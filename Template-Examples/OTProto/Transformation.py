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
    'protocolName': 'OT-2_Example_Transformation_Protocol',
    'author': 'Bradley Brown',
    'author-email': 'b.bradley2@newcastle.ac.uk',
    'user': '',
    'user-email': '',
    'source': 'Custom Protocol inspired by 10.1093/synbio/ysaa010',
    'apiLevel': '2.10',
    'robotName': 'Robo' # This is the name of the OT2 you plan to run the protocol on
}

##############################################################
# Use this code to call the Transformation protocol template #
##############################################################

def run(protocol):

    #################################################
    # Add information needed for the protocol here: #
    #################################################

    DNA = [
    "DNA1",
    "DNA2",
    "DNA3",
    "DNA4",
    "DNA5",
    "DNA6",
    "DNA7",
    "DNA8",
    ]

    DNA_Source_Plate_Type = "3dprinted_24_tuberack_1500ul"

    DNA_Wells = BMS.well_range("A1:A4") + BMS.well_range("B1:B4")

    DNA_Per_Transformation = 2 #uL

    Simulate = False

    #################################################
    #################################################
    #################################################

    ##############################################################
    # The code below creates the protocol to be ran or simulated #
    ##############################################################

    Transformation = BMS.OTProto.Templates.Transformation(
        Protocol=protocol,
        Name=metadata["protocolName"],
        Metadata=metadata,
        DNA=DNA,
        DNA_Source_Wells=DNA_Wells,
        DNA_Source_Type=DNA_Source_Plate_Type,
        DNA_Volume_Per_Transformation=DNA_Per_Transformation,
        Simulate = Simulate
    )
    Transformation.run()


# ######################################################################
# # Use this code if simulating the protocol, otherwise comment it out #
# ######################################################################

# ##########################################################################################################
# # IMPORTANT - the protocol will not upload to the opentrons if this cell is not commented out or removed #
# ##########################################################################################################

# from opentrons import simulate as OT2 # This line simulates the protocol
# # Get the correct api version
# protocol = OT2.get_protocol_api('2.10')
# # Home the pipetting head
# protocol.home()
# # Call the 'run' function to run the protocol
# run(protocol)
# for line in protocol.commands():
#     print(line)
