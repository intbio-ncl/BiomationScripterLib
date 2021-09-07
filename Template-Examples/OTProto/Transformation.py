#!/usr/bin/env python
# coding: utf-8

# In[ ]:


####################################################
# Import BiomationScripter to help write protocols #
####################################################
import sys
sys.path.insert(0, "/var/lib/jupyter/notebooks/Packages/")
import BiomationScripter as BMS
import BiomationScripter.OTProto.Templates as Templates


# In[ ]:


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


# In[ ]:


##############################################################
# Use this cell to call the Transformation protocol template #
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
    
    DNA_Source_Plate_Type = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
    
    Competent_Cells_Source_Type = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
    
    Transformation_Destination_Type = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
    
    DNA_Wells = BMS.well_range("A1:A4") + BMS.well_range("B1:B4")
    
    DNA_Per_Transformation = 2 #uL
    
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
        Competent_Cells_Source_Type = Competent_Cells_Source_Type,
        Transformation_Destination_Type = Transformation_Destination_Type,
        DNA_Source_Type=DNA_Source_Plate_Type,
        DNA_Volume_Per_Transformation=DNA_Per_Transformation,
    )
    Transformation._custom_labware_dir = "C:/Users/bradl/Nextcloud/Private/Automation/Opentrons_Labware_Definitions"
    Transformation.run()


# In[ ]:


# ######################################################################
# # Use this cell if simulating the protocol, otherwise comment it out #
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


# In[ ]:




