import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import smtplib, ssl

class Primer_Mixing_LightRun:
    def __init__(self, Protocol, Name, Metadata, DNA, DNA_Source_Wells, Primers, Primer_Source_Wells,
    Destination_Contents, primer_plate_is_DNA_plate = False,
    DNA_Source_Type = "labcyte384pp_384_wellplate_65ul", Primer_Source_Type = "labcyte384pp_384_wellplate_65ul", Destination_Type = "3dprinted_24_tuberack_1500ul",
    Starting_20uL_Tip = "A1", API = "2.10", Simulate = False):
        # DNA should be a list of names, and DNA_Source_Wells should be a list of wells in the same order as DNA.
        self.Name = Name
        self.Metadata = Metadata
        self._simulate = Simulate
        self.dna = DNA
        self.dna_source_wells = DNA_Source_Wells
        self.dna_source_type = DNA_Source_Type
        self.primers = Primers
        self.primer_source_wells = Primer_Source_Wells
        self.primer_source_type = Primer_Source_Type
        self.starting_20uL_tip = Starting_20uL_Tip
        self._protocol = Protocol
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._custom_labware_dir = "../Custom_Labware/"
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self.destination_type = Destination_Type
        self.destination_contents = Destination_Contents
        self.primer_plate_is_dna_plate = primer_plate_is_DNA_plate
        self._custom_labware_dir = "../Custom_Labware/"

    def load_labware(self, parent, labware_api_name, deck_pos = None, label = None):
            if deck_pos == None:
                Deck_Pos = _OTProto.next_empty_slot(self._protocol)
            else:
                Deck_Pos = deck_pos
            labware = _OTProto.load_labware(parent, labware_api_name, Deck_Pos, self._custom_labware_dir, label)
            return(labware)

    def run(self):
        # Determine how many tips will be needed
        # this will be twice the length of destination contents
        # one tip for DNA, one tip for primer - per destination
        tips_needed_20uL = 2 * len(self.destination_contents)
        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            tip_racks_20uL.append(self._protocol.load_labware(self._20uL_tip_type, _OTProto.next_empty_slot(self._protocol)))
        # Set up pipettes
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)

        # User prompts for number of tip boxes required, and locations of the tip boxes
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(racks_needed_20uL))
        for tip_box_index in range(0, len(tip_racks_20uL)):
            self._protocol.pause("Place 20 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_20uL[tip_box_index].parent))

        # Load all other labware
        dna_labware = self.load_labware(self._protocol, self.dna_source_type, label = "DNA Plate")
        if not self.primer_plate_is_dna_plate:
            primer_labware = self.load_labware(self._protocol, self.primer_source_type, label = "Primer Plate")
        else:
            primer_labware = dna_labware
        destination_labware = self.load_labware(self._protocol, self.destination_type, label = "Tube Rack")

        # Store DNA locations
        DNA = _BMS.Liquids()
        for d,w in zip(self.dna, self.dna_source_wells):
            DNA.add_liquid(d, dna_labware, w)
        # Store primer locations
        Primers = _BMS.Liquids()
        for p,w in zip(self.primers, self.primer_source_wells):
            Primers.add_liquid(p, primer_labware, w)

        # specify wells to be used for LightRun tubes
        destination_plate_wells_by_row = []
        for r in destination_labware.rows():
            for w in r:
                destination_plate_wells_by_row.append(w)
        destination_range = destination_plate_wells_by_row[0:len(self.destination_contents)]

        # User prompts for number of tip boxes required, and locations of the tip boxes
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(racks_needed_20uL))
        for tip_box_index in range(0, len(tip_racks_20uL)):
            self._protocol.pause("Place 20 uL tip rack {} at deck position {}".format((tip_box_index + 1), tip_racks_20uL[tip_box_index].parent))

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("This protocol needs {} 1.5mL tubes".format(len(destination_range)))
        # one tube rack has been loaded for the destination plate, maximum number of samples is 24
        if len(destination_range) > 24:
            self._protocol.pause("This protocol requires more than 24 tubes. Please limit the protocol to 24 tubes only.")

        # Prompt user to load DNA
        for l in DNA.get_all_liquids():
            liquid_name = l
            liquid_labware = DNA.get_liquid_labware(liquid_name)
            liquid_well = DNA.get_liquid_well(liquid_name)
            self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))
        # Prompt user to load Primers
        for l in Primers.get_all_liquids():
            liquid_name = l
            liquid_labware = Primers.get_liquid_labware(liquid_name)
            liquid_well = Primers.get_liquid_well(liquid_name)
            self._protocol.pause('Place {} in well {} at deck position {}'.format(liquid_name, liquid_well, liquid_labware.parent))

        ##################################
        # Start of protocol instructions #
        ##################################

        # Add DNA to destination tubes
        for i in range(len(destination_range)):
            # extract liquid contents from list
            contents = self.destination_contents[i]
            contents_dna = contents[0] # DNA
            contents_primer = contents[1] # primer
            # get dna source well
            dna_labware = DNA.get_liquid_labware(contents_dna)
            dna_well = DNA.get_liquid_well(contents_dna)
            dna_source = dna_labware.wells_by_name()[dna_well]
            # get forward primer well
            primer_labware = Primers.get_liquid_labware(contents_primer)
            primer_well = Primers.get_liquid_well(contents_primer)
            primer_source = primer_labware.wells_by_name()[primer_well]
            # get destination well
            destination = destination_range[i]

            # transfer 5uL of DNA to each tube
            p20.transfer(5, dna_source, destination)
            # transfer 5uL of primer to each tube
            p20.transfer(5, primer_source, destination, mix_after = (5, 5)) # mix after 5 times with 5uL

class Monarch_Miniprep:
    def __init__(self, Protocol, Name, Metadata, Cultures, Culture_Source_Wells, Culture_Source_Type, Destination_Rack_Type_Tubes, Destination_Rack_Type_Spin_Columns, Destination_Rack_Type_Tube_Insert, Elution_Volume = 50, Starting_300uL_Tip = "A1", API = "2.10", Simulate = "deprecated"):
        """
        Cultures should be a list of names, and Culture_Source_Wells should be a list of wells in the same order as DNA.
        Cultures should be presented to the OT2 as cell pellets.
        """
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self.cultures = Cultures
        self.culture_source_wells = Culture_Source_Wells
        self.culture_source_type = Culture_Source_Type
        self.elution_volume = Elution_Volume
        self.starting_300uL_tip = Starting_300uL_Tip
        self.destination_rack_type_tubes = Destination_Rack_Type_Tubes
        self.destination_rack_type_spin_columns = Destination_Rack_Type_Spin_Columns
        self.destination_rack_tube_insert = Destination_Rack_Type_Tube_Insert
        self._reagents_sorce_type = "opentrons_24_aluminumblock_nest_2ml_snapcap"
        self._B1_source_wells = None # Resuspension Buffer
        self.B1_volume_per_source_well = 1500 # uL
        self._B2_source_wells = None # Lysis Buffer
        self.B2_volume_per_source_well = 1500 # uL
        self._B3_source_wells = None # Neutralisation Buffer
        self.B3_volume_per_source_well = 1500 # uL
        self._W1_source_wells = None # Wash Buffer 1
        self.W1_volume_per_source_well = 1500 # uL
        self._W2_source_wells = None # Wash Buffer 2
        self.W2_volume_per_source_well = 1500 # uL
        self._water_source_wells = None # water / Elution Buffer
        self.water_volume_per_source_well = 1500 # uL
        self._protocol = Protocol
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"
        self._custom_labware_dir = "../Custom_Labware/"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

    def load_labware(self, parent, labware_api_name, deck_pos = None):
        if deck_pos == None:
            Deck_Pos = _OTProto.next_empty_slot(self._protocol)
        else:
            Deck_Pos = deck_pos
        labware = _OTProto.load_labware(parent, labware_api_name, Deck_Pos, self._custom_labware_dir)
        return(labware)


    def run(self):
        # Determine how many tips will be needed
        # 1 tip per sample for B1 resuspension
        # 1 tip for all for adding B2
        # 1 tip for all for adding B3
        # 1 tip for all for adding wash buffer 1
        # 1 tip for all for adding wash buffer 2
        # 1 tip for all for adding water
        tips_needed_300uL = len(self.cultures) + 5
        racks_needed_300uL = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            tip_racks_300uL.append(self._protocol.load_labware(self._300uL_tip_type, _OTProto.next_empty_slot(self._protocol)))

        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        # Determine how many destination racks are required (should always be an even number)
        # Load first two racks and then calculate how many extra are required
        destination_racks_tubes = []
        destination_racks_tubes.append(self.load_labware(self._protocol, self.destination_rack_type_tubes))
        destination_racks_tubes.append(self.load_labware(self._protocol, self.destination_rack_type_tubes))

        n_samples = len(self.cultures)
        n_wells_per_destination_rack = len(destination_racks_tubes[0].wells())
        n_destination_racks_required = math.ceil((n_samples/2)/n_wells_per_destination_rack)*2
        for extra_rack in range(0,n_destination_racks_required - 2):
            destination_racks_tubes.append(self.load_labware(self._protocol, self.destination_rack_type_tubes))

        # Load Culture Plate
        culture_labware = self.load_labware(self._protocol, self.culture_source_type)
        # Load Reagents Source Labware
        reagents_labware = self.load_labware(self._protocol, self._reagents_sorce_type)

        # Store culture locations
        Cultures = _BMS.Liquids()
        for c, w in zip(self.cultures, self.culture_source_wells):
            Cultures.add_liquid(c, culture_labware, w)


        # Store miniprep locations for tube rack
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_tube_locations = []
        minipreps_located = 0
        for i_rack in range(0, n_destination_racks_required):
            row_n = 0
            well_n = 0
            i_well_in_row = 0
            wells = destination_racks_tubes[i_rack].rows() # wells grouped by row
            for i_miniprep_in_rack in range(0, n_miniprep_wells_per_rack):
                if minipreps_located == len(self.cultures):
                    break
                well = wells[row_n][i_well_in_row]
                miniprep_tube_locations.append(well)
                i_well_in_row += 1
                minipreps_located += 1
                if i_well_in_row == len(wells[row_n]):
                    row_n += 1
                    i_well_in_row = 0

        # for mpl in miniprep_tube_locations:
        #     print(mpl)

        # Calculate number of B1 aliquots required
        B1_volume_required = len(self.cultures) * 200 # uL
        B1_aliquots_required = math.ceil(B1_volume_required/self.B1_volume_per_source_well) + 1
        # Specify B1 source location(s)
        B1_source = reagents_labware.wells()[0:B1_aliquots_required]

        # Calculate number of B2 aliquots required
        B2_volume_required = len(self.cultures) * 200 # uL
        B2_aliquots_required = math.ceil(B2_volume_required/self.B2_volume_per_source_well) + 1
        # Specify B2 source location(s)
        B2_source = reagents_labware.wells()[B1_aliquots_required:B1_aliquots_required+B2_aliquots_required]

        # Calculate number of B3 aliquots required
        B3_volume_required = len(self.cultures) * 400 # uL
        B3_aliquots_required = math.ceil(B3_volume_required/self.B3_volume_per_source_well) + 1
        # Specify B3 source location(s)
        B3_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required]

        # Calculate number of W1 aliquots required
        W1_volume_required = len(self.cultures) * 200 # uL
        W1_aliquots_required = math.ceil(W1_volume_required/self.W1_volume_per_source_well) + 1
        # Specify W1 source location(s)
        W1_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required]

        # Calculate number of W2 aliquots required
        W2_volume_required = len(self.cultures) * 200 # uL
        W2_aliquots_required = math.ceil(W2_volume_required/self.W2_volume_per_source_well) + 1
        # Specify W2 source location(s)
        W2_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required]

        # Calculate number of Water aliquots required
        Water_volume_required = len(self.cultures) * 50 # uL
        Water_aliquots_required = math.ceil(Water_volume_required/self.water_volume_per_source_well) + 1
        # Specify Water source location(s)
        Water_source = reagents_labware.wells()[B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required:B1_aliquots_required+B2_aliquots_required+B3_aliquots_required+W1_aliquots_required+W2_aliquots_required+Water_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        B1_Wells = []
        for location in B1_source:
            B1_Wells.append(str(location).split(" ")[0])
        B2_Wells = []
        for location in B2_source:
            B2_Wells.append(str(location).split(" ")[0])
        B3_Wells = []
        for location in B3_source:
            B3_Wells.append(str(location).split(" ")[0])
        W1_Wells = []
        for location in W1_source:
            W1_Wells.append(str(location).split(" ")[0])
        W2_Wells = []
        for location in W2_source:
            W2_Wells.append(str(location).split(" ")[0])
        Water_Wells = []
        for location in Water_source:
            Water_Wells.append(str(location).split(" ")[0])

        self._protocol.pause("Place reagents rack on deck position {}".format(reagents_labware.parent))
        self._protocol.pause("{} aliquot(s) of B1 required ({} uL per tube/well. Place in positions {})".format(len(B1_source), self.B1_volume_per_source_well, B1_Wells))
        self._protocol.pause("{} aliquot(s) of B2 required ({} uL per tube/well. Place in positions {})".format(len(B2_source), self.B2_volume_per_source_well, B2_Wells))
        self._protocol.pause("{} aliquot(s) of B3 required ({} uL per tube/well. Place in positions {})".format(len(B3_source), self.B3_volume_per_source_well, B3_Wells))
        self._protocol.pause("{} aliquot(s) of W1 required ({} uL per tube/well. Place in positions {})".format(len(W1_source), self.W1_volume_per_source_well, W1_Wells))
        self._protocol.pause("{} aliquot(s) of W2 required ({} uL per tube/well. Place in positions {})".format(len(W2_source), self.W2_volume_per_source_well, W2_Wells))
        self._protocol.pause("{} aliquot(s) of Water required ({} uL per tube/well. Place in positions {})".format(len(Water_source), self.water_volume_per_source_well, Water_Wells))
        self._protocol.pause("{} destination racks required".format(len(destination_racks_tubes)))
        self._protocol.pause("{} tubes per rack".format(n_miniprep_wells_per_rack))

        # Add 200 uL B1 to each sample, re-suspend, and transfer to destination rack tubes
        B1_used = 0
        B1_tube_n = 0
        for culture in Cultures.get_all_liquids():
            source = B1_source[B1_tube_n]
            destination_labware = Cultures.get_liquid_labware(culture)
            destination_well = Cultures.get_liquid_well(culture)
            destination = destination_labware.wells_by_name()[destination_well]
            p300.transfer(200, source, destination, mix_after = (40, 150), blow_out = True, blowout_location = "destination well")
            B1_used += 200
            if B1_used + 200 >= self.B1_volume_per_source_well:
                B1_tube_n += 1
                B1_used = 0

        # Transfer to tubes
        for sample, destination in zip(Cultures.get_all_liquids(), miniprep_tube_locations):
            source_labware = Cultures.get_liquid_labware(sample)
            source_well = Cultures.get_liquid_well(sample)
            source = source_labware.wells_by_name()[source_well]
            p300.transfer(200, source, destination, mix_before = (5, 150))


        # Add 200 uL B2 to each sample
        B2_used = 0
        B2_tube_n = 0
        for destination in miniprep_tube_locations:
            source = B2_source[B2_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")
            B2_used += 200
            if B2_used + 200 >= self.B2_volume_per_source_well:
                B2_tube_n += 1
                B2_used = 0
        self._protocol.pause("Invert the tube racks until all solutions are dark pink and transparent, then replace the racks.")

        # Add 400 uL B3 to each sample
        B3_used = 0
        B3_tube_n = 0
        for destination in miniprep_tube_locations:
            source = B3_source[B3_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")
            B3_used += 400
            if B3_used + 400 >= self.B3_volume_per_source_well:
                B3_tube_n += 1
                B3_used = 0
        self._protocol.pause("Invert the tube racks until all solutions are uniformly yellow, then centrifuge the racks for 5 mins at 4500 RPM.")

        self._protocol.pause("Replace the tubes with clean spin columns and carefully tip the supernatant from the tubes into the columns, then centrifuge for 1 min and discard the flow through.")

        # Delete the tube racks and load the spin column racks
        destination_racks_spin_columns = []
        for tube_rack in destination_racks_tubes:
            tube_rack_deck_pos = tube_rack.parent
            del self._protocol.deck[str(tube_rack_deck_pos)]
            destination_racks_spin_columns.append(self.load_labware(self._protocol, self.destination_rack_type_spin_columns, deck_pos = tube_rack_deck_pos))

        # Store miniprep locations for spin columns rack
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_spin_column_locations = []
        minipreps_located = 0
        for i_rack in range(0, n_destination_racks_required):
            row_n = 0
            well_n = 0
            i_well_in_row = 0
            wells = destination_racks_spin_columns[i_rack].rows() # wells grouped by row
            for i_miniprep_in_rack in range(0, n_miniprep_wells_per_rack):
                if minipreps_located == len(self.cultures):
                    break
                well = wells[row_n][i_well_in_row]
                miniprep_spin_column_locations.append(well)
                i_well_in_row += 1
                minipreps_located += 1
                if i_well_in_row == len(wells[row_n]):
                    row_n += 1
                    i_well_in_row = 0

        # Add 200 uL of W1 to each sample
        W1_used = 0
        W1_tube_n = 0
        for destination in miniprep_spin_column_locations:
            source = W1_source[W1_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")
            W1_used += 200
            if W1_used + 200 >= self.W1_volume_per_source_well:
                W1_tube_n += 1
                W1_used = 0

        # Pause and get the user to centrifuge the racks as above
        self._protocol.pause("Centrifuge the racks for 5 mins at 4500 RPM.")

        # Add 400 uL of W2 to each sample
        W2_used = 0
        W2_tube_n = 0
        for destination in miniprep_spin_column_locations:
            source = W2_source[W2_tube_n]
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")
            p300.transfer(200, source, destination, blow_out = True, blowout_location = "destination well")
            W2_used += 400
            if W2_used + 400 >= self.W2_volume_per_source_well:
                W2_tube_n += 1
                W2_used = 0

        # Pause and get the user to centrifuge the rack as above, discard the flow through, and re-centrifuge
        self._protocol.pause("Centrifuge the racks for 5 mins at 4500 RPM, discard the flow through, and then re-centrifuge.")

        # Get the user to insert the spin column insert into a clean eppendorf and replace on the rack
        self._protocol.pause("Replace the spin columns with clean 1.5 mL tubes, and insert the inner spin column into the tube.")

        # Delete the spin column racks and load the tube_insert racks
        destination_racks_insert_tubes = []
        for spin_column_rack in destination_racks_spin_columns:
            spin_column_rack_deck_pos = spin_column_rack.parent
            del self._protocol.deck[str(spin_column_rack_deck_pos)]
            destination_racks_insert_tubes.append(self.load_labware(self._protocol, self.destination_rack_tube_insert, deck_pos = spin_column_rack_deck_pos))

        # Store miniprep locations for tube_insert racks
        n_miniprep_wells_per_rack = math.ceil(n_samples/n_destination_racks_required)
        miniprep_insert_tube_locations = []
        minipreps_located = 0
        for i_rack in range(0, n_destination_racks_required):
            row_n = 0
            well_n = 0
            i_well_in_row = 0
            wells = destination_racks_insert_tubes[i_rack].rows() # wells grouped by row
            for i_miniprep_in_rack in range(0, n_miniprep_wells_per_rack):
                if minipreps_located == len(self.cultures):
                    break
                well = wells[row_n][i_well_in_row]
                miniprep_insert_tube_locations.append(well)
                i_well_in_row += 1
                minipreps_located += 1
                if i_well_in_row == len(wells[row_n]):
                    row_n += 1
                    i_well_in_row = 0

        # Add <VOLUME> of water to each tube
        Water_used = 0
        Water_tube_n = 0
        for destination in miniprep_insert_tube_locations:
            source = Water_source[Water_tube_n]
            p300.transfer(self.elution_volume, source, destination, blow_out = True, blowout_location = "destination well")
            Water_used += self.elution_volume
            if Water_used + self.elution_volume >= self.water_volume_per_source_well:
                Water_tube_n += 1
                Water_used = 0

        # Pause and prompt the user to centrifuge for 1 min as above
        self._protocol.pause("Centrifuge the racks for 5 mins at 4500 RPM, then remove and discard the inserts.")

        # Delete the tube_insert racks and load the tube racks (this is to make sure the correct labware shows up in the calibration pane on the app)

        for tube_rack in destination_racks_insert_tubes:
            tube_rack_deck_pos = tube_rack.parent
            del self._protocol.deck[str(tube_rack_deck_pos)]
            self.load_labware(self._protocol, self.destination_rack_type_tubes, deck_pos = tube_rack_deck_pos)

class Spot_Plating:
    def __init__(self,
        Protocol,
        Name,
        Metadata,
        Cells,
        Cell_Source_Wells,
        Cell_Source_Type,
        Dilution_Plate_Type,
        Petri_Dish_Type ="nuncomnitray40mlagar_96_wellplate_15ul",
        Plating_Volume = 10,
        Dilution_Factors = [1, 10, 100, 1000, 2000],
        Dilution_Volume = 200,
        Starting_20uL_Tip = "A1",
        Starting_300uL_Tip = "A1",
        API = "2.10",
        Simulate = "deprecated"
    ):

        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self._custom_labware_dir = "../Custom_Labware/"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.plating_volume = Plating_Volume
        self.dilution_factors = Dilution_Factors
        self.dilution_volume = Dilution_Volume

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.starting_20uL_tip = Starting_20uL_Tip
        self.starting_300uL_tip = Starting_300uL_Tip
        ## Cells to be plated ##
        self.cells = Cells
        self.cell_source_type = Cell_Source_Type
        self.cell_source_wells = Cell_Source_Wells
        ## LB media ##
        self._LB_source_type = "3dprinted_15_tuberack_15000ul"
        self._LB_source_volume_per_well = 5000 # uL # No more than 6000 uL for 15 mL tubes

        #######################
        # Destination Labware #
        #######################
        self.petri_dish_type = Petri_Dish_Type
        self.dilution_plate_type = Dilution_Plate_Type

        ###############
        # Robot Setup #
        ###############
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"

    def serial_dilution_volumes(self, dilution_factors, total_volume):
        # Note that total volume is the amount the dilution will be made up to
        ## The total volume of all dilutions other than the final will be lower than this
        substance_volumes = []
        solution_volumes = []

        # This the the dilution factor of the source material for the first serial dilution
        ## This is always 1, as the initial substance is assumed to be undiluted
        source_dilution_factor = 1

        for df in dilution_factors:
            # Get the dilution factor of the current serial dilution being performed
            destination_dilution_factor = df

            # Calculate the volume, in uL, of substance and solution required for each dilution factor
            substance_volume = total_volume * (source_dilution_factor/destination_dilution_factor)
            solution_volume = total_volume - substance_volume

            # Store the volumes required for later use
            substance_volumes.append(substance_volume)
            solution_volumes.append(solution_volume)

            # Set the current dilution as the source for the next serial dilution
            source_dilution_factor = df

        return(substance_volumes, solution_volumes)

    ####################################
    # Function to be called by the OT2 #
    ####################################
    def run(self):

        #################################################################
        # Calculate amount of cells and LB media required for dilutions #
        #################################################################

        # Ensure dilution factors are in ascending order
        self.dilution_factors.sort()

        # Call the serial_dilution_volumes method to get a list of cell and LB volumes for each dilution factor
        ## These lists retain the order of self.dilution_factors (after sort)
        cell_dilution_volumes, LB_dilution_volumes = self.serial_dilution_volumes(self.dilution_factors, self.dilution_volume)

        ## Create copies of the cell and LB volume lists without volume 0 - helps calculate number of tips required ###
        cell_dilution_volumes_no_0 = cell_dilution_volumes.copy()
        try:
            cell_dilution_volumes_no_0.remove(0)
        except:
            pass
        LB_dilution_volumes_no_0 = LB_dilution_volumes.copy()
        try:
            LB_dilution_volumes_no_0.remove(0)
        except:
            pass
        ###############################################################################################################

        #########################################################################
        # Calculate the number of 20 and 300 uL tips required for this protocol #
        #########################################################################
        tips_required_20uL = 0
        tips_required_300uL = 0

        # Tips required for dilution stage #

        ## Adding LB to dilution labware - don't need to change tip per transfer
        ### Determine the min and max LB volumes which need to be transferred, and determine if a 20uL or 300uL tip, or both, are required
        max_LB_volume = max(LB_dilution_volumes_no_0)
        min_LB_volume = min(LB_dilution_volumes_no_0)
        if max_LB_volume > 20:
            # If there are any LB transfer events larger than 20 uL, a 300 uL tip will be required
            tips_required_300uL += 1
        if min_LB_volume <= 20:
            # If there are any LB transfer events fewer than or equal to 20 uL, a 20 uL tip will be required:
            tips_required_20uL += 1

        ## Transferring cells to and between wells of the dilution labware - clean tip per transformation
        for Cell in self.cells:
            ### Determine the min and max cell volumes which need to be transferred, and determine if a 20uL or 300uL tip, or both, are required
            max_cell_volume = max(cell_dilution_volumes_no_0)
            min_cell_volume = min(cell_dilution_volumes_no_0)

            if max_cell_volume > 20:
                # If there are any cell transfer events larger than 20 uL, a 300 uL tip will be required
                tips_required_300uL += 1
            if min_cell_volume <= 20:
                # If there are any cell transfer events fewer than or equal to 20 uL, a 20 uL tip will be required:
                tips_required_20uL += 1

        # Tips required for spot plating - clean tip for each dilution #
        if self.plating_volume > 20:
            tips_required_300uL += len(self.cells) * len(self.dilution_factors)
        else:
            tips_required_20uL += len(self.cells) * len(self.dilution_factors)

        ##############################################################################
        # Calculate the number of 20 and 300 uL tip racks required for this protocol #
        ##############################################################################
        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_required_20uL, self.starting_20uL_tip)
        racks_needed_300uL = _OTProto.tip_racks_needed(tips_required_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._20uL_tip_type, rack_deck_slot, self._custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_20uL.append(rack)

        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._300uL_tip_type, rack_deck_slot, self._custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_300uL.append(rack)

        ###################
        # Set up pipettes #
        ###################
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        ################
        # Load labware #
        ################

        # Determine amount of dilution labware required #
        ## Determine number of wells required
        wells_needed = len(self.cells) * len(self.dilution_factors)
        ## Load and store all required dilution labware
        dilution_labware = _OTProto.calculate_and_load_labware(self._protocol, self.dilution_plate_type, wells_needed, custom_labware_dir = self._custom_labware_dir)

        # Determine amount of agar plates required #
        wells_needed = len(self.cells) * len(self.dilution_factors)
        petri_dishes = _OTProto.calculate_and_load_labware(self._protocol, self.petri_dish_type, wells_needed, custom_labware_dir = self._custom_labware_dir)

        # Load source labware #
        cell_labware_deck_slot = _OTProto.next_empty_slot(self._protocol)
        cells_labware = _OTProto.load_labware(self._protocol, self.cell_source_type, cell_labware_deck_slot, self._custom_labware_dir)
        LB_labware_deck_slot = _OTProto.next_empty_slot(self._protocol)
        LB_labware = _OTProto.load_labware(self._protocol, self._LB_source_type, LB_labware_deck_slot, self._custom_labware_dir)

        ## Calculate number of LB aliquots required
        total_LB_required = len(self.cells) * sum(LB_dilution_volumes) # Calculate total amount of LB required
        LB_aliquots_required = math.ceil(total_LB_required/self._LB_source_volume_per_well)
        ## Specify LB location
        LB_source = LB_labware.wells()[0:LB_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of LB required".format(len(LB_source)))
        self._protocol.pause("LB Location: {}".format(LB_source))
        self._protocol.pause("{} dilution labware required".format(len(dilution_labware)))
        self._protocol.pause("{} petri dishes required".format(len(petri_dishes)))
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(len(tip_racks_20uL)))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(len(tip_racks_300uL)))

        ##########################
        # Liquid handling begins #
        ##########################

        ##############################
        # Add LB to dilution labware #
        ##############################
        # This is to switch which LB aliquot is being used as the source
        LB_tube_index = 0

        # Determine which tip(s) are required and get it/them
        if min_LB_volume <= 20:
            p20.pick_up_tip()
        if max_LB_volume > 20:
            p300.pick_up_tip()

        # Create a list of LB volumes which need to be transfered to the destination labware
        LB_transfers = LB_dilution_volumes * len(self.cells)
        for destination_labware_index in range(0, len(dilution_labware)):
            # Get the current destination laware
            destination_labware = dilution_labware[destination_labware_index]
            # Get all available wells in the destination labware
            wells_in_labware = len(destination_labware.wells())
            # Get the subset of LB volumes which will be transferred to this destination labware
            ## Note that if there is only one destination labware, LB_volumes == LB_transfers
            LB_volumes = LB_transfers[0+(wells_in_labware*destination_labware_index):wells_in_labware+(wells_in_labware*destination_labware_index)]
            for volume, destination in zip(LB_volumes, destination_labware.wells()):
                # if volume is 0, skip the transfer
                if volume == 0:
                    continue
                # Determine which pipette is needed
                if volume > 20:
                    pipette = p300
                elif volume <= 20:
                    pipette = p20
                # Determine which LB aliquot to take from
                source = LB_source[LB_tube_index]
                # Perform the transfer
                pipette.transfer(volume, source, destination, new_tip = "never")
                # Iterate to the next LB aliquot, and check if need to go back to first aliquot
                if LB_tube_index == len(LB_source) - 1:
                    LB_tube_index = 0
                else:
                    LB_tube_index += 1

        # Drop tips which have been in use
        if min_LB_volume <= 20:
            p20.drop_tip()
        if max_LB_volume > 20:
            p300.drop_tip()

        ############################
        # Perform serial dilutions #
        ############################

        # Set up a list to store locations of all dilutions - will be used for plating later
        dilution_locations = []

        transfer_index = 0
        destination_labware_index = 0
        for cell_index in range(0, len(self.cells)):
            # Determine which tip(s) are required and get it/them
            if min_cell_volume <= 20:
                p20.pick_up_tip()
            if max_cell_volume > 20:
                p300.pick_up_tip()

            # Transfer cells to the first well in the dilution labware
            # Determine which pipette is needed
            transfer_volume = cell_dilution_volumes[0]
            if transfer_volume > 20:
                pipette = p300
            elif transfer_volume <= 20:
                pipette = p20
            # get the destination location
            destination_labware = dilution_labware[destination_labware_index]
            destination = destination_labware.wells()[transfer_index]
            dilution_locations.append(destination)
            # get the source location
            source = cells_labware.wells_by_name()[self.cell_source_wells[cell_index]]
            # Perfrom the transfer
            pipette.transfer(transfer_volume, source, destination, new_tip = "never", mix_after = (5,transfer_volume))
            # Add to the transfer counter
            transfer_index += 1
            # Check if the current destination labware is full
            if len(destination_labware.wells()) == transfer_index:
                destination_labware_index += 1
                transfer_index = 0


            # Perform the remianing serial dilutions for this cell type
            for transfer_volume in cell_dilution_volumes[1:]:
                # if volume is 0, skip the transfer
                if transfer_volume == 0:
                    continue
                # Determine which pipette is needed
                if transfer_volume > 20:
                    pipette = p300
                elif transfer_volume <= 20:
                    pipette = p20
                # set the source as the previous dilution
                if transfer_index == 0: # If the next dilution is in a new destination labware...
                    # Set the source labware as the previous labware
                    source_labware = dilution_labware[destination_labware_index - 1]
                    source = source_labware.wells()[-1]
                else:
                    source_labware = dilution_labware[destination_labware_index]
                    source = source_labware.wells()[transfer_index - 1]

                # Set the destination location
                destination_labware = dilution_labware[destination_labware_index]
                destination = destination_labware.wells()[transfer_index]
                dilution_locations.append(destination)

                # Perform the transfer
                pipette.transfer(transfer_volume, source, destination, new_tip = "never", mix_before = (5,transfer_volume), mix_after = (5,transfer_volume))
                # Add to the transfer counter
                transfer_index += 1
                # Check if the current destination labware is full
                if len(destination_labware.wells()) == transfer_index:
                    destination_labware_index += 1
                    transfer_index = 0

            # Drop tips which have been in use
            if min_cell_volume <= 20:
                p20.drop_tip()
            if max_cell_volume > 20:
                p300.drop_tip()


        self._protocol.pause("Uncover agar plate on position {}".format(petri_dishes[0].parent))

        # Determine which pipette is needed
        if self.plating_volume > 20:
            pipette = p300
        elif self.plating_volume <= 20:
            pipette = p20

        destination_labware_index = 0
        plating_index = 0
        for source in dilution_locations:
            destination_labware = petri_dishes[destination_labware_index]
            destination = destination_labware.wells()[plating_index]
            pipette.transfer(self.plating_volume, source, destination, blow_out = True, blowout_location = "destination well")
            # Add to the plating counter
            plating_index += 1
            # Check if the current destination labware is full
            if len(destination_labware.wells()) == plating_index:
                destination_labware_index += 1
                plating_index = 0
                self._protocol.pause("Uncover agar plate on position {}".format(petri_dishes[destination_labware_index].parent))


class Transformation:
    def __init__(self,
        Protocol,
        Name,
        Metadata,
        DNA,
        DNA_Source_Wells,
        Competent_Cells_Source_Type,
        Transformation_Destination_Type,
        DNA_Source_Type,
        DNA_Volume_Per_Transformation,
        Starting_20uL_Tip = "A1",
        Starting_300uL_Tip = "A1",
        API = "2.10",
        Simulate = "deprecated"
    ):
        # DNA should be a list of names, and DNA_Source_Wells should be a list of wells in the same order as DNA.

        #####################
        # Protocol Metadata #
        #####################
        self._protocol = Protocol
        self.name = Name
        self.metadata = Metadata
        self._simulate = Simulate
        self._custom_labware_dir = "../Custom_Labware/"

        if not Simulate == "deprecated":
            print("Simulate no longer needs to be specified and will soon be removed.")

        ########################################
        # User defined aspects of the protocol #
        ########################################
        # Running parameters
        self.dna_volume_per_transformation = DNA_Volume_Per_Transformation # uL
        self._competent_cell_volume_per_transformation = 10 # uL
        self._transformation_volume = 200 #uL
        self._heat_shock_time = 90 # Seconds
        self._heat_shock_temp = 42 # celsius

        ####################
        # Source materials #
        ####################
        ## Pipette Tips ##
        self._20uL_tip_type = "opentrons_96_tiprack_20ul"
        self._300uL_tip_type = "opentrons_96_tiprack_300ul"
        self.starting_20uL_tip = Starting_20uL_Tip
        self.starting_300uL_tip = Starting_300uL_Tip
        ## DNA to be transformed ##
        self.dna = DNA
        self.dna_source_wells = DNA_Source_Wells
        self.dna_source_type = DNA_Source_Type
        ## Competent cells ##
        self._competent_cells_source_type = Competent_Cells_Source_Type
        self._competent_cells_source_volume_per_well  = 45 # uL
        ## Media ##
        self._LB_source_type = "3dprinted_15_tuberack_15000ul"
        self._LB_source_volume_per_well = 5000 # uL # No more than 6000 uL for 15 mL tubes

        #######################
        # Destination Labware #
        #######################
        self._transformation_destination_type = Transformation_Destination_Type

        ###############
        # Robot Setup #
        ###############
        self._p20_type = "p20_single_gen2"
        self._p20_position = "left"
        self._p300_type = "p300_single_gen2"
        self._p300_position = "right"
        self._temperature_module = "temperature module gen2"

    def run(self):
        ###########################
        # Load temperature_module #
        ###########################
        temperature_module = self._protocol.load_module(self._temperature_module, 4)

        #########################################################################
        # Calculate the number of 20 and 300 uL tips required for this protocol #
        #########################################################################
        tips_needed_20uL = 0
        tips_needed_300uL = 0

        # Adding competent cells #
        if self._competent_cell_volume_per_transformation > 20:
            tips_needed_300uL += 1
        else:
            tips_needed_20uL += 1

        # Add tips for adding DNA - one per sample #
        tips_needed_20uL += len(self.dna)

        # Add tips for adding LB - one per sample #
        media_per_transformation = self._transformation_volume - (self._competent_cell_volume_per_transformation + self.dna_volume_per_transformation)
        if media_per_transformation > 20:
            tips_needed_300uL += len(self.dna)
        else:
            tips_needed_20uL += len(self.dna)

        ##############################################################################
        # Calculate the number of 20 and 300 uL tip racks required for this protocol #
        ##############################################################################
        # Calculate number of racks needed - account for the first rack missing some tips
        racks_needed_20uL = _OTProto.tip_racks_needed(tips_needed_20uL, self.starting_20uL_tip)
        racks_needed_300uL  = _OTProto.tip_racks_needed(tips_needed_300uL, self.starting_300uL_tip)
        # Load tip racks
        tip_racks_20uL = []
        for rack20 in range(0, racks_needed_20uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._20uL_tip_type, rack_deck_slot, self._custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_20uL.append(rack)

        tip_racks_300uL = []
        for rack300 in range(0, racks_needed_300uL):
            # Find the next empty deck slot for the tip rack
            rack_deck_slot = _OTProto.next_empty_slot(self._protocol)
            # Load the tip rack
            rack = _OTProto.load_labware(self._protocol, self._300uL_tip_type, rack_deck_slot, self._custom_labware_dir)
            # Store the tip rack for future usage
            tip_racks_300uL.append(rack)

        ###################
        # Set up pipettes #
        ###################
        p20 = self._protocol.load_instrument(self._p20_type, self._p20_position, tip_racks = tip_racks_20uL)
        p20.starting_tip = tip_racks_20uL[0].well(self.starting_20uL_tip)
        p300 = self._protocol.load_instrument(self._p300_type, self._p300_position, tip_racks = tip_racks_300uL)
        p300.starting_tip = tip_racks_300uL[0].well(self.starting_300uL_tip)

        ################
        # Load labware #
        ################
        # Load transfomration plate onto temp module #
        transformation_plate = _OTProto.load_labware(temperature_module, self._transformation_destination_type, custom_labware_dir = self._custom_labware_dir)

        # Load all other labware #
        LB_labware_slot = _OTProto.next_empty_slot(self._protocol)
        LB_labware = _OTProto.load_labware(self._protocol, self._LB_source_type, LB_labware_slot, self._custom_labware_dir)

        dna_labware_slot = _OTProto.next_empty_slot(self._protocol)
        dna_labware = _OTProto.load_labware(self._protocol, self.dna_source_type, dna_labware_slot, self._custom_labware_dir)

        competent_cells_labware_slot = _OTProto.next_empty_slot(self._protocol)
        competent_cells_labware = _OTProto.load_labware(self._protocol, self._competent_cells_source_type, competent_cells_labware_slot, self._custom_labware_dir)


        # Calculate number of cell aliquots required #
        cc_volume_required = len(self.dna) * self._competent_cell_volume_per_transformation # uL
        cc_aliquots_required = math.ceil(cc_volume_required/self._competent_cells_source_volume_per_well)
        # Specify competent cells location
        competent_cells_source = competent_cells_labware.wells()[0:cc_aliquots_required]

        # Calculate number of LB aliquots required #
        LB_volume_per_transformation = self._transformation_volume - (self.dna_volume_per_transformation + self._competent_cell_volume_per_transformation)
        LB_Volume_required = len(self.dna) * LB_volume_per_transformation
        LB_aliquots_required = math.ceil(LB_Volume_required/self._LB_source_volume_per_well)
        # Specify LB location
        LB_source = LB_labware.wells()[0:LB_aliquots_required]

        # Prompt user to check all liquids are correctly placed
        self._protocol.pause("{} aliquot(s) of LB required".format(len(LB_source)))
        self._protocol.pause("LB Location: {}".format(LB_source))
        self._protocol.pause("{} aliquot(s) of cells required".format(len(competent_cells_source)))
        self._protocol.pause("Competent cells location: {}".format(competent_cells_source))
        self._protocol.pause("This protocol needs {} 20 uL tip racks".format(len(tip_racks_20uL)))
        self._protocol.pause("This protocol needs {} 300 uL tip racks".format(len(tip_racks_300uL)))

        for dna, source_well in zip(self.dna, self.dna_source_wells):
            self._protocol.pause('Place {} in well {} at deck position {}'.format(dna, source_well, dna_labware_slot))

        ##########################
        # Liquid handling begins #
        ##########################

        ########################################################
        # Set temperature to 4C and wait until temp is reached #
        ########################################################
        temperature_module.set_temperature(4)

        ################################
        # Add competent cells to plate #
        ################################
        # This is to switch which competent cells aliquot is being used as the source
        cc_tube_index = 0

        # Determine which tip is required and get it
        if self._competent_cell_volume_per_transformation <= 20:
            pipette = p20
            pipette.pick_up_tip()
        else:
            pipette = p300
            pipette.pick_up_tip()

        for transformation_index in range(0, len(self.dna)):
            # Determine which competent cell aliquot to take from
            source = competent_cells_source[cc_tube_index]
            # Set the next empty well in the transformation labware as the destination
            destination = transformation_plate.wells()[transformation_index]
            # Perform the transfer
            pipette.transfer(self._competent_cell_volume_per_transformation, source, destination, new_tip = "never", mix_before = (5, self._competent_cell_volume_per_transformation))
            # Iterate to the next competent cell aliquot, and check if need to go back to first aliquot
            if cc_tube_index == len(competent_cells_source) - 1:
                cc_tube_index = 0
            else:
                cc_tube_index += 1

        # Drop tips which have been in use
        if self._competent_cell_volume_per_transformation <= 20:
            pipette = p20
            pipette.drop_tip()
        else:
            pipette = p300
            pipette.drop_tip()

        ######################################
        # Add DNA to competent cells and mix #
        ######################################
        # Determine which pipette should be used
        if self.dna_volume_per_transformation <= 20:
            pipette = p20
        else:
            pipette = p300

        for transformation_index in range(0, len(self.dna)):
            # Get the location of the dna to be added
            source = dna_labware.wells()[transformation_index]
            # Get the 'well' to which the DNA should be added
            destination = transformation_plate.wells()[transformation_index]
            # Perform the transfer
            pipette.transfer(self.dna_volume_per_transformation, source, destination, mix_after = (10, 10))

        #####################
        # Heat shock at 42C #
        #####################
        # Set the temp to heat shock
        temperature_module.set_temperature(self._heat_shock_temp)
        # Wait for a bit
        self._protocol.delay(seconds = self._heat_shock_time)
        # Cool back to 4 - protocol won't continue until this is back at 4...
        temperature_module.set_temperature(4)

        #############################
        # Add LB to transfomrations #
        #############################
        # Prompt user to open LB tubes
        self._protocol.pause("Open up LB tubes")

        # This is to switch which LB aliquot is being used as the source
        LB_tube_index = 0

        # Determine which pipette will be used
        if media_per_transformation <= 20:
            pipette = p20
        else:
            pipette = p300

        for transformation_index in range(0, len(self.dna)):
            # Determine which media aliquot to take from
            source = LB_source[LB_tube_index]
            # Set the next empty well in the transformation labware as the destination
            destination = transformation_plate.wells()[transformation_index]
            # Perform the transfer
            pipette.transfer(media_per_transformation, source, destination)
            # Iterate to the next media aliquot, and check if need to go back to first aliquot
            if LB_tube_index == len(LB_source) - 1:
                LB_tube_index = 0
            else:
                LB_tube_index += 1
