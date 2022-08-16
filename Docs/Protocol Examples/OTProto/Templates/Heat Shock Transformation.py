#!/usr/bin/env python
# coding: utf-8

# In[1]:


####################################################
# Import BiomationScripter to help write protocols #
####################################################
import sys
sys.path.insert(0, "/var/lib/jupyter/notebooks/Packages/BiomationScripterLib")
import BiomationScripter as BMS
import BiomationScripter.OTProto.Templates as Templates


# In[2]:


##################################
# Record the protocol's metadata #
##################################
metadata = {
    'protocolName': 'Transformation Example',
    'author': 'Bradley Brown',
    'author-email': 'b.bradley2@newcastle.ac.uk',
    'user': '',
    'user-email': '',
    'source': 'Generated using BiomationScripter',
    'apiLevel': '2.11',
    'robotName': 'RobOT2' # This is the name of the OT2 you plan to run the protocol on
}


# In[5]:


##############################################################
# Use this cell to call the Transformation protocol template #
##############################################################

def run(protocol):
    
    #################################################
    # Add information needed for the protocol here: #
    #################################################
    
    Custom_Labware_Dir = "../../../../Resources/For Docs/custom_labware"
    
    # DNA Plate Info #
    
    DNA_Plate_Wells = [
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B9",
        "B10",
        "B11",
        "B12",
    ]
    
    DNA_Plate_Content = [
        "Assembly 1",
        "Assembly 2",
        "Assembly 3",
        "Assembly 4",
        "Assembly 5",
        "Assembly 6",
        "Assembly 7",
        "Assembly 8",
        "Assembly 9",
        "Assembly 10",
        "Assembly 11",
    ]
    
    DNA_Plate = BMS.Labware_Layout("DNA Plate", "appliedbiosystemsmicroampoptical_384_wellplate_20ul")
    
    DNA_Plate.bulk_add_content(
        Wells = DNA_Plate_Wells,
        Reagents = DNA_Plate_Content,
        Volumes = 20
    )
    
    # DNA Tubes Info #
    
    DNA_Tubes_Wells = [
        "A1",
        "A2"
    ]
    
    DNA_Tubes_Content = [
        "Positive",
        "Negative"
    ]
    
    DNA_Tubes = BMS.Labware_Layout("DNA Tubes", "3dprinted_24_tuberack_1500ul")
    
    DNA_Tubes.bulk_add_content(
        Wells = DNA_Tubes_Wells,
        Reagents = DNA_Tubes_Content,
        Volumes = 20
    )
    
    DNA_Source_Layouts = [DNA_Plate, DNA_Tubes]
    
    # Other labware and material info #
    
    Competent_Cells_Source_Type = "3dprinted_24_tuberack_1500ul"
    Media_Source_Type = "3dprinted_15_tuberack_15000ul"
    Transformation_Destination_Type = "nunclondeltasurface163320_96_wellplate_250ul"
    
    Competent_Cells_Aliquot_Vol = 40 # uL
    Media_Aliquot_Vol = 5000 # uL
    
    # Protocol Parameters #
    
    DNA_Per_Transformation = 3 # uL
    Competent_Cells_Volume = 20 # uL
    Final_Volume = 100 # uL
    Heat_Shock_Time = 30 # Seconds
    Heat_Shock_Temp = 42 # celcius
    Wait_Before_Shock = 300 # seconds
    Reps = 1

    # Available Modules #

    Modules = ["temperature module gen2", "Thermocycler Module"]

    # Shuffle Function Parameters #

    # Shuffle = ["/data/user_storage/Bradle/TransfomrationExample/","DNA_Locations"]
    
    # Starting Tips #
    
    Starting_20uL_Tip = "A8"
    Starting_300uL_Tip = "A1"
    
    #################################################
    #################################################
    #################################################
    
    ##############################################################
    # The code below creates the protocol to be ran or simulated #
    ##############################################################
    
    Transformation = BMS.OTProto.Templates.Heat_Shock_Transformation(
        Protocol=protocol,
        Name=metadata["protocolName"],
        Metadata=metadata,
        DNA_Source_Layouts=DNA_Source_Layouts,
        Competent_Cells_Source_Type=Competent_Cells_Source_Type,
        Transformation_Destination_Type=Transformation_Destination_Type,
        Media_Source_Type=Media_Source_Type,
        DNA_Volume_Per_Transformation=DNA_Per_Transformation,
        Competent_Cell_Volume_Per_Transformation=Competent_Cells_Volume,
        Transformation_Final_Volume=Final_Volume,
        Heat_Shock_Time=Heat_Shock_Time,
        Heat_Shock_Temp=Heat_Shock_Temp,
        Media_Aliquot_Volume=Media_Aliquot_Vol,
        Competent_Cells_Aliquot_Volume=Competent_Cells_Aliquot_Vol,
        Wait_Before_Shock=Wait_Before_Shock,
        Replicates=Reps,
        Modules=Modules,
        Starting_20uL_Tip = Starting_20uL_Tip,
        Starting_300uL_Tip = Starting_300uL_Tip,
        # Shuffle=Shuffle,
        # Cells_Mix_Before = None,
        # DNA_Mix_After = None
    )
    Transformation.custom_labware_dir = Custom_Labware_Dir
    Transformation.run()
