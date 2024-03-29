import os
from itertools import product
from copy import deepcopy
import tempfile

import pytest
from opentrons import simulate as OT2

import BiomationScripter as bms
from BiomationScripter import EchoProto as ep
from BiomationScripter import OTProto as otp

from BiomationScripter.EchoProto.Templates import Loop_Assembly, PCR
from BiomationScripter.OTProto.Templates import Heat_Shock_Transformation

def test_fmol_calculator():
    mass1 = 120 # ng
    length1 = 1222 # bp

    assert bms.fmol_calculator(mass1, length1) == 158.90184839397108

    mass2 = 500 # ng
    length2 = 32 # bp

    assert bms.fmol_calculator(mass2, length2) == 25238.809616592196

def test_mastermixes_by_min_volume_basic():
    Destination_Layout = bms.Labware_Layout("Destination", "greiner655087_96_wellplate_340ul")
    Destination_Layout.define_format(8, 12)

    well_set_1 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A12")
    well_set_2 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A6")
    well_set_3 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A7:A12")
    well_set_4 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A3")
    well_set_5 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A4:A6")
    well_set_6 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A7:A9")
    well_set_7 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A10:A12")

    for well in well_set_1:
        Destination_Layout.add_content(well, "LB", 80)

    for well in well_set_2:
        Destination_Layout.add_content(well, "Cells 1", 19)

    for well in well_set_3:
        Destination_Layout.add_content(well, "Cells 2", 19)

    for well in well_set_4 + well_set_6:
        Destination_Layout.add_content(well, "Water", 1)

    for well in well_set_5 + well_set_7:
        Destination_Layout.add_content(well, "Inducer", 1)

    Mastermix_Layout = bms.Labware_Layout("Mastermix", "3dprinted_24_tuberack_1500ul")
    Mastermix_Layout.define_format(4, 6)
    Mastermix_Layout.set_available_wells()

    Maximum_Mastermix_Volume = 1000
    Min_Transfer_Volume = 5
    Extra_Reactions = 1
    Excluded_Reagents = []
    Excluded_Combinations = []
    Preferential_Reagents = []
    Seed = 1

    Mastermixes, Seed, Destination_Layouts, Mastermix_Layouts = bms.mastermixes_by_min_volume(
        Destination_Layouts = [Destination_Layout],
        Mastermix_Layout = Mastermix_Layout,
        Maximum_Mastermix_Volume = Maximum_Mastermix_Volume,
        Min_Transfer_Volume = Min_Transfer_Volume,
        Extra_Reactions=Extra_Reactions,
        Excluded_Reagents=Excluded_Reagents,
        Excluded_Combinations=Excluded_Combinations,
        Preferential_Reagents=Preferential_Reagents,
        Seed = Seed
    )

    assert Seed == 1
    assert Destination_Layouts[0] is Destination_Layout
    assert Mastermix_Layouts[0] is Mastermix_Layout

    assert len(Mastermix_Layouts[0].content) == 2
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Inducer") == ["A1"]
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Water") == ["A2"]
    assert Mastermix_Layouts[0].get_wells_containing_liquid("LB") == ["A1", "A2"]
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Cells 1") == []
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Cells 2") == []
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Inducer", "A1") == 7.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Water", "A2") == 7.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("LB", "A1") == 560.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("LB", "A2") == 560.0

    assert len(Mastermixes) == 2

    assert Mastermixes[0].reagents == ['Inducer_vol_1.0', 'LB_vol_80.0']
    assert Mastermixes[0].wells == {'0_A6', '0_A4', '0_A5', '0_A10', '0_A12', '0_A11'}

    assert Mastermixes[1].reagents == ['Water_vol_1.0', 'LB_vol_80.0']
    assert Mastermixes[1].wells == {'0_A1', '0_A7', '0_A8', '0_A3', '0_A2', '0_A9'}

def test_mastermixes_by_min_volume_preferential_cells():
    Destination_Layout = bms.Labware_Layout("Destination", "greiner655087_96_wellplate_340ul")
    Destination_Layout.define_format(8, 12)

    well_set_1 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A12")
    well_set_2 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A6")
    well_set_3 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A7:A12")
    well_set_4 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A3")
    well_set_5 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A4:A6")
    well_set_6 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A7:A9")
    well_set_7 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A10:A12")

    for well in well_set_1:
        Destination_Layout.add_content(well, "LB", 80)

    for well in well_set_2:
        Destination_Layout.add_content(well, "Cells 1", 19)

    for well in well_set_3:
        Destination_Layout.add_content(well, "Cells 2", 19)

    for well in well_set_4 + well_set_6:
        Destination_Layout.add_content(well, "Water", 1)

    for well in well_set_5 + well_set_7:
        Destination_Layout.add_content(well, "Inducer", 1)

    Mastermix_Layout = bms.Labware_Layout("Mastermix", "3dprinted_24_tuberack_1500ul")
    Mastermix_Layout.define_format(4, 6)
    Mastermix_Layout.set_available_wells()

    Maximum_Mastermix_Volume = 1000
    Min_Transfer_Volume = 5
    Extra_Reactions = 1
    Excluded_Reagents = []
    Excluded_Combinations = []
    Preferential_Reagents = ["Cells 1", "Cells 2"]
    Seed = 1

    Mastermixes, Seed, Destination_Layouts, Mastermix_Layouts = bms.mastermixes_by_min_volume(
        Destination_Layouts = [Destination_Layout],
        Mastermix_Layout = Mastermix_Layout,
        Maximum_Mastermix_Volume = Maximum_Mastermix_Volume,
        Min_Transfer_Volume = Min_Transfer_Volume,
        Extra_Reactions=Extra_Reactions,
        Excluded_Reagents=Excluded_Reagents,
        Excluded_Combinations=Excluded_Combinations,
        Preferential_Reagents=Preferential_Reagents,
        Seed = Seed
    )

    assert Seed == 1
    assert Destination_Layouts[0] is Destination_Layout
    assert Mastermix_Layouts[0] is Mastermix_Layout

    assert len(Mastermix_Layouts[0].content) == 4
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Cells 1") == ['A1', 'A3']
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Cells 2") == ['A2', 'A4']
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Inducer") == ['A1', 'A2']
    assert Mastermix_Layouts[0].get_wells_containing_liquid("Water") == ['A3', 'A4']
    assert Mastermix_Layouts[0].get_wells_containing_liquid("LB") == []
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Inducer", "A1") == 5.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Inducer", "A2") == 5.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Water", "A3") == 5.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Water", "A4") == 5.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Cells 1", "A1") == 95.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Cells 1", "A3") == 95.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Cells 2", "A2") == 95.0
    assert Mastermix_Layouts[0].get_volume_of_liquid_in_well("Cells 2", "A4") == 95.0

    assert len(Mastermixes) == 4

    assert Mastermixes[0].reagents == ['Inducer_vol_1.0', 'Cells 1_vol_19.0']
    assert Mastermixes[0].wells == {'0_A6', '0_A4', '0_A5'}

    assert Mastermixes[1].reagents == ['Inducer_vol_1.0', 'Cells 2_vol_19.0']
    assert Mastermixes[1].wells == {'0_A10', '0_A12', '0_A11'}

    assert Mastermixes[2].reagents == ['Water_vol_1.0', 'Cells 1_vol_19.0']
    assert Mastermixes[2].wells == {'0_A2', '0_A3', '0_A1'}

    assert Mastermixes[3].reagents == ['Water_vol_1.0', 'Cells 2_vol_19.0']
    assert Mastermixes[3].wells == {'0_A7', '0_A8', '0_A9'}

def test_mastermixes_by_min_volume_error():
    Destination_Layout = bms.Labware_Layout("Destination", "greiner655087_96_wellplate_340ul")
    Destination_Layout.define_format(8, 12)

    well_set_1 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A12")
    well_set_2 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A6")
    well_set_3 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A7:A12")
    well_set_4 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A1:A3")
    well_set_5 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A4:A6")
    well_set_6 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A7:A9")
    well_set_7 = bms.well_range(Labware_Format = Destination_Layout, Wells = "A10:A12")

    for well in well_set_1:
        Destination_Layout.add_content(well, "LB", 80)

    for well in well_set_2:
        Destination_Layout.add_content(well, "Cells 1", 19)

    for well in well_set_3:
        Destination_Layout.add_content(well, "Cells 2", 19)

    for well in well_set_4 + well_set_6:
        Destination_Layout.add_content(well, "Water", 1)

    for well in well_set_5 + well_set_7:
        Destination_Layout.add_content(well, "Inducer", 1)

    Mastermix_Layout = bms.Labware_Layout("Mastermix", "3dprinted_24_tuberack_1500ul")
    Mastermix_Layout.define_format(4, 6)
    Mastermix_Layout.set_available_wells()

    Maximum_Mastermix_Volume = 1000 # uL
    Min_Transfer_Volume = 5 # uL
    Extra_Reactions = 1
    Seed = None

    Excluded_Combinations = [
        ["LB", "Inducer"],
        ["Cells 1", "Inducer"],
        ["Cells 2", "Inducer"]
    ]

    with pytest.raises(bms.MastermixError) as excinfo:
        Mastermixes, Seed, Destination_Layouts, Mastermix_Layouts = bms.mastermixes_by_min_volume(
            Destination_Layouts = [Destination_Layout],
            Mastermix_Layout = Mastermix_Layout,
            Maximum_Mastermix_Volume = Maximum_Mastermix_Volume,
            Min_Transfer_Volume = Min_Transfer_Volume,
            Extra_Reactions=Extra_Reactions,
            Excluded_Combinations = Excluded_Combinations,
            Seed = Seed
        )

def test_create_labware():
    num_pcr_reactions = 234

    pcr_plate = bms.Labware_Layout(Name="PCR Plate", Type="96 Well Plate")

    pcr_plate.define_format(
        Rows=8,
        Columns=12,
    )

    # Basic use
    pcr_plate_layouts = bms.Create_Labware_Needed(
        Labware_Format=pcr_plate,
        N_Wells_Needed=num_pcr_reactions,
        N_Wells_Available="All",
    )
    assert len(pcr_plate_layouts) == 3

    # Without returning original layout
    pcr_plate_layouts = bms.Create_Labware_Needed(
        Labware_Format=pcr_plate,
        N_Wells_Needed=num_pcr_reactions,
        N_Wells_Available="All",
        Return_Original_Layout=False,
    )
    assert len(pcr_plate_layouts) == 2

    # Decrease number of PCR reactions
    pcr_plate_layouts = bms.Create_Labware_Needed(
        Labware_Format=pcr_plate,
        N_Wells_Needed=20,
        N_Wells_Available="All",
        Return_Original_Layout=True,
    )
    assert pcr_plate_layouts == [pcr_plate]

def test_import_labware():
    dna_stocks_filename = "Example DNA Stocks"
    # NOTE: This will fail if the path doesn't end in a / -- use Pathlib
    dna_stocks_path = "data/"
    dna_stocks_ext = ".xlsx"

    dna_stocks_layout = bms.Import_Labware_Layout(
        Filename=dna_stocks_filename,
        path=dna_stocks_path,
        ext=dna_stocks_ext,
    )

    dna_stocks_layout.print()

def test_labware_content_class():
    name = "Liquid1"
    volume = 10
    liquid_class = "AQ_BP"

    content1 = bms.Labware_Content(
        Name=name, Volume=volume, Liquid_Class=liquid_class
    )

    assert content1.get_info() == [name, volume, liquid_class]

    content2 = bms.Labware_Content(Name=name, Volume=volume)
    assert content2.get_info() == [name, volume, None]

def test_labware_layout_class():
    source_labware_name = "Source Plate"
    source_labware_type = "Greiner 96-well 2mL Masterblock (780270)"

    source_labware_layout = bms.Labware_Layout(
        source_labware_name, source_labware_type
    )
    source_labware_layout.define_format(Rows=8, Columns=12)
    assert source_labware_layout.get_format() == (8, 12)
    assert source_labware_layout.get_well_range() == list(
        f"{l}{n}" for l, n in product("ABCDEFGH", range(1, 13))
    )
    assert source_labware_layout.get_well_range(Direction="Vertical") == list(
        f"{l}{n}" for n, l in product(range(1, 13), "ABCDEFGH")
    )
    assert source_labware_layout.get_well_range(Well_Range="B3:D4") == (
        [f"B{n}" for n in range(3, 13)]
        + [f"C{n}" for n in range(1, 13)]
        + [f"D{n}" for n in range(1, 5)]
    )
    assert source_labware_layout.get_well_range(
        Well_Range="B3:D4", Box=True
    ) == (["B3", "B4", "C3", "C4", "D3", "D4"])

    assert source_labware_layout.get_well_range(
        Well_Range="A3:D4",
        Direction="Vertical",
        Box=True,
        Use_Outer_Wells=False,
    ) == ["B3", "C3", "D3", "B4", "C4", "D4"]

    source_labware_layout.set_available_wells(
        Well_Range="A3:D4",
        Direction="Vertical",
        Box=True,
        Use_Outer_Wells=False,
    )
    assert source_labware_layout.get_available_wells() == (
        ["B3", "C3", "D3", "B4", "C4", "D4"]
    )
    assert source_labware_layout.get_next_empty_well() == "B3"
    assert source_labware_layout.check_well("D4")
    assert source_labware_layout.check_well("A1")
    assert not source_labware_layout.check_well("J22")

def test_labware_layout_class_content():
    source_labware_name = "Source Plate"
    source_labware_type = "Greiner 96-well 2mL Masterblock (780270)"

    source_labware_layout = bms.Labware_Layout(
        source_labware_name, source_labware_type
    )
    source_labware_layout.define_format(Rows=8, Columns=12)

    source_labware_layout.set_available_wells()
    source_labware_layout.add_content(
        Well="A1", Reagent="DNA1", Volume=20, Liquid_Class=None
    )

    source_labware_layout.add_content(
        Well="B2:B6", Reagent="Water", Volume=30, Liquid_Class=None
    )

    source_labware_layout.add_content(
        Well=["A5", "C7", "D9"], Reagent="Buffer1", Volume=20, Liquid_Class=None
    )

    for reagent, volume in [
        (
            "Primer1",
            10,
        ),
        (
            "Primer2",
            15,
        ),
    ]:
        source_labware_layout.add_content(
            Well="C1", Reagent=reagent, Volume=volume
        )

    occupied_wells = [
        "A1",
        "A5",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "C1",
        "C7",
        "D9",
    ]
    assert occupied_wells == sorted(source_labware_layout.get_content().keys())
    assert occupied_wells == sorted(source_labware_layout.get_occupied_wells())
    assert len(source_labware_layout.get_content()["C1"]) == 2
    assert source_labware_layout.get_wells_containing_liquid("Buffer1") == [
        "A5",
        "C7",
        "D9",
    ]


# def test_serial_dilution_volumes():
#     final_volume = 100
#     dilution_factors = [1, 2, 4, 8, 16, 32]

#     sample_volumes, solution_volumes = bms.serial_dilution_volumes(
#         dilution_factors=dilution_factors, total_volume=final_volume
#     )

#     assert sample_volumes == [100.0, 50.0, 50.0, 50.0, 50.0, 50.0]
#     assert solution_volumes == [0.0, 50.0, 50.0, 50.0, 50.0, 50.0]

#     dilution_factors = [1, 2, 10, 50, 75, 100, 200]

#     sample_volumes, solution_volumes = bms.serial_dilution_volumes(
#         dilution_factors=dilution_factors, total_volume=final_volume
#     )
#     assert sample_volumes == [
#         100.0,
#         50.0,
#         20.0,
#         20.0,
#         66.66666666666666,
#         75.0,
#         50.0,
#     ]
#     assert solution_volumes == [
#         0.0,
#         50.0,
#         80.0,
#         80.0,
#         33.33333333333334,
#         25.0,
#         50.0,
#     ]


def test_assembly_class():
    assembly_name = "GFP Expression Unit"
    backbone = "pOdd1"
    parts = ["J23100", "B0034", "GFP", "B0015"]

    gfp_expression_assembly = bms.Assembly(
        Name=assembly_name, Backbone=backbone, Parts=parts
    )

    assert gfp_expression_assembly.name == assembly_name
    assert gfp_expression_assembly.backbone == backbone
    assert gfp_expression_assembly.parts == parts

class TestEchoProtoTemplateSuperclass:
    def test_simple_echoproto_template_superclass(self):
        class ColourMixing(ep.EchoProto_Template):
            def __init__(self):
                pass

        protocol = ColourMixing()

    def test_echoproto_template_superclass(self):
        class ColourMixing(ep.EchoProto_Template):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        colour_source_plates = [
            bms.Import_Labware_Layout(
                "Coloured_Solutions",
                path="data/",
            )
        ]
        mixuture_plate_layout = bms.Labware_Layout(
            "Mixture Plate", "384 OptiAmp Plate"
        )
        mixuture_plate_layout.define_format(16, 24)

        protocol = ColourMixing(
            Name="Walkthrough Example - Colour Mixing",
            Source_Plates=colour_source_plates,
            Destination_Plate_Layout=mixuture_plate_layout,
            Picklist_Save_Directory="./",
        )

        assert protocol.name == "Walkthrough Example - Colour Mixing"
        assert protocol.source_plate_layouts == colour_source_plates
        assert protocol.destination_plate_layouts == [mixuture_plate_layout]
        assert protocol.save_dir == "./"

class TestEchoProtocol:
    @pytest.fixture
    def protocol(self):
        protocol_title = "Example Protocol"
        protocol = ep.Protocol(Title=protocol_title)

        coloured_water_source_layout = bms.Labware_Layout(
            Name="DNA_Source_Plate", Type="384PP"
        )

        coloured_water_source_layout.add_content(
            Well="A1", Reagent="Red", Volume=40, Liquid_Class="AQ_BP"
        )

        coloured_water_source_layout.add_content(
            Well="A2", Reagent="Blue", Volume=40, Liquid_Class="AQ_BP"
        )

        protocol.add_source_plate(coloured_water_source_layout)

        destination_plate_layout = bms.Labware_Layout(
            Name="Destination Plate",
            Type="Optical Amp Plate",
        )
        destination_plate_layout.define_format(Rows=16, Columns=24)

        for well, reagent in [
            (
                "B2",
                "Yellow",
            ),
            (
                "B3",
                "Blue",
            ),
            (
                "B3",
                "Red",
            ),
            (
                "B4",
                "Yellow",
            ),
            (
                "B4",
                "Red",
            ),
        ]:
            destination_plate_layout.add_content(
                Well=well, Reagent=reagent, Volume=1
            )

        protocol.add_destination_plate(destination_plate_layout)
        return protocol

    def test_echo_protocol_class(self):
        protocol_title = "Example Protocol"
        protocol = ep.Protocol(Title=protocol_title)

        coloured_water_source_layout = bms.Labware_Layout(
            Name="DNA_Source_Plate", Type="384PP"
        )

        coloured_water_source_layout.add_content(
            Well="A1", Reagent="Red", Volume=40, Liquid_Class="AQ_BP"
        )

        coloured_water_source_layout.add_content(
            Well="A2", Reagent="Blue", Volume=40, Liquid_Class="AQ_BP"
        )

        assert sorted(ep.Source_Plate_Types.keys()) == [
            "384LDV",
            "384PP",
            "6RES",
        ]

        protocol.add_source_plate(coloured_water_source_layout)
        assert protocol.get_source_plates() == [coloured_water_source_layout]

        destination_plate_layout = bms.Labware_Layout(
            Name="Destination Plate",
            Type="Optical Amp Plate",
        )
        destination_plate_layout.define_format(Rows=16, Columns=24)

        for well, reagent in [
            (
                "B2",
                "Yellow",
            ),
            (
                "B3",
                "Blue",
            ),
            (
                "B3",
                "Red",
            ),
            (
                "B4",
                "Yellow",
            ),
            (
                "B4",
                "Red",
            ),
        ]:
            destination_plate_layout.add_content(
                Well=well, Reagent=reagent, Volume=1
            )

        protocol.add_destination_plate(destination_plate_layout)
        assert protocol.get_destination_plates() == [destination_plate_layout]

    def test_generate_actions_fails(self, protocol):
        with pytest.raises(bms.OutOFSourceMaterial) as excinfo:
            ep.Generate_Actions(protocol)

        assert (
            str(excinfo.value)
            == "Cannot find the following reagents in a source plate: {'Yellow'}"
        )

    def test_generate_actions_fails_ii(self, protocol):
        protocol_cp = deepcopy(protocol)
        protocol_cp.get_source_plates()[0].add_content(
            Well="A3", Reagent="Yellow", Volume=10, Liquid_Class="AQ_BP"
        )

        with pytest.raises(bms.OutOFSourceMaterial) as excinfo:
            ep.Generate_Actions(protocol_cp)

    def test_generate_actions_succeeds(self, protocol):
        protocol_cp = deepcopy(protocol)
        protocol_cp.get_source_plates()[0].add_content(
            Well="A3", Reagent="Yellow", Volume=10 + 7, Liquid_Class="AQ_BP"
        )
        ep.Generate_Actions(protocol_cp)
        assert protocol_cp.transfer_lists

    def test_write_picklist(self, protocol):
        protocol_cp = deepcopy(protocol)
        protocol_cp.get_source_plates()[0].add_content(
            Well="A3", Reagent="Yellow", Volume=10 + 7, Liquid_Class="AQ_BP"
        )
        ep.Generate_Actions(protocol_cp)

        dirname = tempfile.mkdtemp()
        expected_fname = f"{dirname}/Example Protocol-384PP-(DNA_Source_Plate).csv"
        if os.path.isfile(expected_fname):
            os.remove(expected_fname)

        ep.Write_Picklists(protocol_cp, Save_Location=dirname, Merge=False)

        assert os.path.isfile(expected_fname)
        os.remove(expected_fname)

class Test_EchoProto_Loop_Assembly:

    def test_unmerged(self):

        Protocol_Name = "Unmerged Example Loop Assembly"

        Metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = False

        Picklist_Save_Directory = tempfile.mkdtemp()

        Source_Plate_Directory = "data/"

        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        Assembly_Plate_Layout = bms.Labware_Layout("Assembly Plate", "384 OptiAmp Plate")
        Assembly_Plate_Layout.define_format(16,24)
        Assembly_Plate_Layout.set_available_wells()

        Final_Volume = 5 # uL
        Backbone_to_Part_Ratios = ["1:1", "1:3", "2:1"]
        Repeats = 1
        Enzyme = "BsaI" # For level 1 assemblies
        Buffer = "T4 Ligase Buffer"

        Promoters = [
            "J23100",
            "J23119",
            "J23101",
            "J23102",
            "J23103",
            "J23104",
            "J23105",
            "J23106",
            "J23107",
            "J23108",
            "J23109",
            "J23110",
            "J23111",
            "J23112",
            "J23113",
            "J23114",
            "J23115",
            "J23116",
            "J23117",
            "J23118"
        ]

        RBSs = [
            "B0034",
            "B0030",
            "B0031",
            "B0032"
        ]

        Assemblies = []


        for promoter in Promoters:
            for RBS in RBSs:
                Assemblies.append(
                    bms.Assembly(
                        Name = "{}-{}-GFP".format(promoter, RBS),
                        Backbone = "pOdd1",
                        Parts = [promoter, RBS, "GFP", "B0015"]
                    )
                )

        Loop_Protocol = Loop_Assembly.Template(
            Enzyme=Enzyme,
            Buffer=Buffer,
            Volume=Final_Volume,
            Assemblies=Assemblies,
            Backbone_to_Part=Backbone_to_Part_Ratios,
            Repeats=Repeats,
            Name=Protocol_Name,
            Source_Plates=Source_Plates,
            Destination_Plate_Layout=Assembly_Plate_Layout,
            Picklist_Save_Directory=Picklist_Save_Directory,
            Metadata=Metadata,
            Merge=Merge_Picklists
        )

        Loop_Protocol.run()

        # Check the picklist outputs
        picklist_filenames = [f for f in os.listdir(Loop_Protocol.save_dir) if Loop_Protocol.name in f]

        assert len(picklist_filenames) == 4

        # Check that all picklists exist
        validation_picklists = [
            "Unmerged Example Loop Assembly-384PP-(Example DNA Stocks).csv",
            "Unmerged Example Loop Assembly-384PP-(Example Plasmid Stocks).csv",
            "Unmerged Example Loop Assembly-6RES-(Water and Buffer Plate).csv",
            "Unmerged Example Loop Assembly-384LDV-(Reagents).csv",
        ]

        for picklist in validation_picklists:
            assert picklist in picklist_filenames

        for picklist in picklist_filenames:
            test_picklist = open(f"{Loop_Protocol.save_dir}/{picklist}", "r")
            validation_picklist = open(f"data/{picklist}", "r")

            assert len(test_picklist.read().split("\n")) == len(validation_picklist.read().split("\n"))

            test_picklist.close()
            validation_picklist.close()

    def test_merged(self):

        Protocol_Name = "Merged Example Loop Assembly"

        Metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = True

        Picklist_Save_Directory = tempfile.mkdtemp()

        Source_Plate_Directory = "data/"

        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        Assembly_Plate_Layout = bms.Labware_Layout("Assembly Plate", "384 OptiAmp Plate")
        Assembly_Plate_Layout.define_format(16,24)
        Assembly_Plate_Layout.set_available_wells()

        Final_Volume = 5 # uL
        Backbone_to_Part_Ratios = ["1:1", "1:3", "2:1"]
        Repeats = 1
        Enzyme = "BsaI" # For level 1 assemblies
        Buffer = "T4 Ligase Buffer"

        Promoters = [
            "J23100",
            "J23119",
            "J23101",
            "J23102",
            "J23103",
            "J23104",
            "J23105",
            "J23106",
            "J23107",
            "J23108",
            "J23109",
            "J23110",
            "J23111",
            "J23112",
            "J23113",
            "J23114",
            "J23115",
            "J23116",
            "J23117",
            "J23118"
        ]

        RBSs = [
            "B0034",
            "B0030",
            "B0031",
            "B0032"
        ]

        Assemblies = []


        for promoter in Promoters:
            for RBS in RBSs:
                Assemblies.append(
                    bms.Assembly(
                        Name = "{}-{}-GFP".format(promoter, RBS),
                        Backbone = "pOdd1",
                        Parts = [promoter, RBS, "GFP", "B0015"]
                    )
                )

        Loop_Protocol = Loop_Assembly.Template(
            Enzyme=Enzyme,
            Buffer=Buffer,
            Volume=Final_Volume,
            Assemblies=Assemblies,
            Backbone_to_Part=Backbone_to_Part_Ratios,
            Repeats=Repeats,
            Name=Protocol_Name,
            Source_Plates=Source_Plates,
            Destination_Plate_Layout=Assembly_Plate_Layout,
            Picklist_Save_Directory=Picklist_Save_Directory,
            Metadata=Metadata,
            Merge=Merge_Picklists
        )

        Loop_Protocol.run()

        # Check the picklist outputs
        picklist_filenames = [f for f in os.listdir(Loop_Protocol.save_dir) if Loop_Protocol.name in f]

        assert len(picklist_filenames) == 3

        # Check that all picklists exist
        validation_picklists = [
            "Merged Example Loop Assembly-384PP.csv",
            "Merged Example Loop Assembly-6RES-(Water and Buffer Plate).csv",
            "Merged Example Loop Assembly-384LDV-(Reagents).csv",
        ]

        for picklist in validation_picklists:
            assert picklist in picklist_filenames

        for picklist in picklist_filenames:
            test_picklist = open(f"{Loop_Protocol.save_dir}/{picklist}", "r")
            validation_picklist = open(f"data/{picklist}", "r")

            assert len(test_picklist.read().split("\n")) == len(validation_picklist.read().split("\n"))

            test_picklist.close()
            validation_picklist.close()

    def test_volume_overflow_fails(self):

        Protocol_Name = "Merged Example Loop Assembly"

        Metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = True

        Picklist_Save_Directory = tempfile.mkdtemp()

        Source_Plate_Directory = "data/"

        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        Assembly_Plate_Layout = bms.Labware_Layout("Assembly Plate", "384 OptiAmp Plate")
        Assembly_Plate_Layout.define_format(16,24)
        Assembly_Plate_Layout.set_available_wells()

        Final_Volume = 5 # uL
        Backbone_to_Part_Ratios = ["100:1"]
        Repeats = 1
        Enzyme = "BsaI" # For level 1 assemblies
        Buffer = "T4 Ligase Buffer"

        Promoters = [
            "J23100",
            "J23119",
            "J23101",
            "J23102",
            "J23103",
            "J23104",
            "J23105",
            "J23106",
            "J23107",
            "J23108",
            "J23109",
            "J23110",
            "J23111",
            "J23112",
            "J23113",
            "J23114",
            "J23115",
            "J23116",
            "J23117",
            "J23118"
        ]

        RBSs = [
            "B0034",
            "B0030",
            "B0031",
            "B0032"
        ]

        Assemblies = []


        for promoter in Promoters:
            for RBS in RBSs:
                Assemblies.append(
                    bms.Assembly(
                        Name = "{}-{}-GFP".format(promoter, RBS),
                        Backbone = "pOdd1",
                        Parts = [promoter, RBS, "GFP", "B0015"]
                    )
                )

        Loop_Protocol = Loop_Assembly.Template(
            Enzyme=Enzyme,
            Buffer=Buffer,
            Volume=Final_Volume,
            Assemblies=Assemblies,
            Backbone_to_Part=Backbone_to_Part_Ratios,
            Repeats=Repeats,
            Name=Protocol_Name,
            Source_Plates=Source_Plates,
            Destination_Plate_Layout=Assembly_Plate_Layout,
            Picklist_Save_Directory=Picklist_Save_Directory,
            Metadata=Metadata,
            Merge=Merge_Picklists
        )
        with pytest.raises(bms.NegativeVolumeError) as excinfo:
            Loop_Protocol.run()

class Test_EchoProto_PCR:
    def test_unmerged_no_mm(self):

        Protocol_Name = "Unmerged Example PCR No MM"

        metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = False # This merges source plates with the same TYPE into one picklist

        Picklist_Save_Directory = "data/"

        Source_Plate_Directory = "data/"
        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Primer Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        PCR_Plate_Layout = bms.Labware_Layout("PCR Plate", "384 OptiAmp Plate")
        PCR_Plate_Layout.define_format(16,24)
        PCR_Plate_Layout.set_available_wells()

        Polymerase = "Q5 Polymerase"
        Polymerase_Buffer = "Q5 Buffer"
        Buffer_Stock_Conc = 5 # x
        Master_Mix = False
        Master_Mix_Stock_Conc = None # x
        DNA_Amounts = [0.1, 0.5, 1] # uL

        Volume = 5
        Repeats = 1

        Reactions = [
            ("J23100", "VF2", "VR"),
            ("J23119", "VF2", "VR"),
            ("J23101", "VF2", "VR"),
            ("J23102", "VF2", "VR"),
            ("J23103", "VF2", "VR"),
            ("J23104", "VF2", "VR"),
            ("J23105", "VF2", "VR"),
            ("J23106", "VF2", "VR"),
            ("J23107", "VF2", "VR"),
            ("J23108", "VF2", "VR"),
            ("J23109", "VF2", "VR"),
            ("J23110", "VF2", "VR"),
            ("J23111", "VF2", "VR"),
            ("J23112", "VF2", "VR"),
            ("J23113", "VF2", "VR"),
            ("J23114", "VF2", "VR"),
            ("J23115", "VF2", "VR"),
            ("J23116", "VF2", "VR"),
            ("J23117", "VF2", "VR"),
            ("J23118", "VF2", "VR"),
            ("pOdd1", "VF2", "VR"),
        ]

        # This code block shouldn't need to be modified
        PCR_Protocol = PCR.Template(
            Name = Protocol_Name,
            Picklist_Save_Directory = Picklist_Save_Directory,
            Metadata = metadata,
            Volume= Volume,
            Reactions = Reactions,
            Polymerase = Polymerase,
            Polymerase_Buffer = Polymerase_Buffer,
            Polymerase_Buffer_Stock_Conc = Buffer_Stock_Conc,
            Master_Mix = Master_Mix,
            Master_Mix_Stock_Conc = Master_Mix_Stock_Conc,
            Repeats = Repeats,
            DNA_Amounts = DNA_Amounts,
            Source_Plates = Source_Plates,
            Destination_Plate_Layout = PCR_Plate_Layout,
            Merge = Merge_Picklists
        )
        PCR_Protocol.run()

        # Check the picklist outputs
        picklist_filenames = [f for f in os.listdir(PCR_Protocol.save_dir) if PCR_Protocol.name in f]

        assert len(picklist_filenames) == 5

        # Check that all picklists exist
        validation_picklists = [
            "Unmerged Example PCR No MM-384PP-(Example DNA Stocks).csv",
            "Unmerged Example PCR No MM-384PP-(Example Primer Stocks).csv",
            "Unmerged Example PCR No MM-384PP-(Example Plasmid Stocks).csv",
            "Unmerged Example PCR No MM-6RES-(Water and Buffer Plate).csv",
            "Unmerged Example PCR No MM-384LDV-(Reagents).csv",
        ]

        for picklist in validation_picklists:
            assert picklist in picklist_filenames

        for picklist in picklist_filenames:
            test_picklist = open(f"{PCR_Protocol.save_dir}/{picklist}", "r")
            validation_picklist = open(f"data/{picklist}", "r")

            assert len(test_picklist.read().split("\n")) == len(validation_picklist.read().split("\n"))

            test_picklist.close()
            validation_picklist.close()

    def test_merged_no_mm(self):

        Protocol_Name = "Merged Example PCR No MM"

        metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = True # This merges source plates with the same TYPE into one picklist

        Picklist_Save_Directory = "data/"

        Source_Plate_Directory = "data/"
        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Primer Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        PCR_Plate_Layout = bms.Labware_Layout("PCR Plate", "384 OptiAmp Plate")
        PCR_Plate_Layout.define_format(16,24)
        PCR_Plate_Layout.set_available_wells()

        Polymerase = "Q5 Polymerase"
        Polymerase_Buffer = "Q5 Buffer"
        Buffer_Stock_Conc = 5 # x
        Master_Mix = False
        Master_Mix_Stock_Conc = None # x
        DNA_Amounts = [0.1, 0.5, 1] # uL

        Volume = 5
        Repeats = 1

        Reactions = [
            ("J23100", "VF2", "VR"),
            ("J23119", "VF2", "VR"),
            ("J23101", "VF2", "VR"),
            ("J23102", "VF2", "VR"),
            ("J23103", "VF2", "VR"),
            ("J23104", "VF2", "VR"),
            ("J23105", "VF2", "VR"),
            ("J23106", "VF2", "VR"),
            ("J23107", "VF2", "VR"),
            ("J23108", "VF2", "VR"),
            ("J23109", "VF2", "VR"),
            ("J23110", "VF2", "VR"),
            ("J23111", "VF2", "VR"),
            ("J23112", "VF2", "VR"),
            ("J23113", "VF2", "VR"),
            ("J23114", "VF2", "VR"),
            ("J23115", "VF2", "VR"),
            ("J23116", "VF2", "VR"),
            ("J23117", "VF2", "VR"),
            ("J23118", "VF2", "VR"),
            ("pOdd1", "VF2", "VR"),
        ]

        # This code block shouldn't need to be modified
        PCR_Protocol = PCR.Template(
            Name = Protocol_Name,
            Picklist_Save_Directory = Picklist_Save_Directory,
            Metadata = metadata,
            Volume= Volume,
            Reactions = Reactions,
            Polymerase = Polymerase,
            Polymerase_Buffer = Polymerase_Buffer,
            Polymerase_Buffer_Stock_Conc = Buffer_Stock_Conc,
            Master_Mix = Master_Mix,
            Master_Mix_Stock_Conc = Master_Mix_Stock_Conc,
            Repeats = Repeats,
            DNA_Amounts = DNA_Amounts,
            Source_Plates = Source_Plates,
            Destination_Plate_Layout = PCR_Plate_Layout,
            Merge = Merge_Picklists
        )
        PCR_Protocol.run()

        # Check the picklist outputs
        picklist_filenames = [f for f in os.listdir(PCR_Protocol.save_dir) if PCR_Protocol.name in f]

        assert len(picklist_filenames) == 3

        # Check that all picklists exist
        validation_picklists = [
            "Merged Example PCR No MM-384PP.csv",
            "Merged Example PCR No MM-6RES-(Water and Buffer Plate).csv",
            "Merged Example PCR No MM-384LDV-(Reagents).csv",
        ]

        for picklist in validation_picklists:
            assert picklist in picklist_filenames

        for picklist in picklist_filenames:
            test_picklist = open(f"{PCR_Protocol.save_dir}/{picklist}", "r")
            validation_picklist = open(f"data/{picklist}", "r")

            assert len(test_picklist.read().split("\n")) == len(validation_picklist.read().split("\n"))

            test_picklist.close()
            validation_picklist.close()

    def test_unmerged_with_mm(self):

        Protocol_Name = "Unmerged Example PCR With MM"

        metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = False # This merges source plates with the same TYPE into one picklist

        Picklist_Save_Directory = "data/"

        Source_Plate_Directory = "data/"
        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Primer Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        PCR_Plate_Layout = bms.Labware_Layout("PCR Plate", "384 OptiAmp Plate")
        PCR_Plate_Layout.define_format(16,24)
        PCR_Plate_Layout.set_available_wells()

        Polymerase = "Q5 Polymerase"
        Polymerase_Buffer = "Q5 Buffer"
        Buffer_Stock_Conc = 5 # x
        Master_Mix = False
        Master_Mix_Stock_Conc = None # x
        DNA_Amounts = [0.1, 0.5, 1] # uL

        Volume = 5
        Repeats = 1

        Reactions = [
            ("J23100", "VF2", "VR"),
            ("J23119", "VF2", "VR"),
            ("J23101", "VF2", "VR"),
            ("J23102", "VF2", "VR"),
            ("J23103", "VF2", "VR"),
            ("J23104", "VF2", "VR"),
            ("J23105", "VF2", "VR"),
            ("J23106", "VF2", "VR"),
            ("J23107", "VF2", "VR"),
            ("J23108", "VF2", "VR"),
            ("J23109", "VF2", "VR"),
            ("J23110", "VF2", "VR"),
            ("J23111", "VF2", "VR"),
            ("J23112", "VF2", "VR"),
            ("J23113", "VF2", "VR"),
            ("J23114", "VF2", "VR"),
            ("J23115", "VF2", "VR"),
            ("J23116", "VF2", "VR"),
            ("J23117", "VF2", "VR"),
            ("J23118", "VF2", "VR"),
            ("pOdd1", "VF2", "VR"),
        ]

        # This code block shouldn't need to be modified
        PCR_Protocol = PCR.Template(
            Name = Protocol_Name,
            Picklist_Save_Directory = Picklist_Save_Directory,
            Metadata = metadata,
            Volume= Volume,
            Reactions = Reactions,
            Polymerase = Polymerase,
            Polymerase_Buffer = Polymerase_Buffer,
            Polymerase_Buffer_Stock_Conc = Buffer_Stock_Conc,
            Master_Mix = Master_Mix,
            Master_Mix_Stock_Conc = Master_Mix_Stock_Conc,
            Repeats = Repeats,
            DNA_Amounts = DNA_Amounts,
            Source_Plates = Source_Plates,
            Destination_Plate_Layout = PCR_Plate_Layout,
            Merge = Merge_Picklists
        )
        PCR_Protocol.run()

        # Check the picklist outputs
        picklist_filenames = [f for f in os.listdir(PCR_Protocol.save_dir) if PCR_Protocol.name in f]

        assert len(picklist_filenames) == 5

        # Check that all picklists exist
        validation_picklists = [
            "Unmerged Example PCR With MM-384PP-(Example DNA Stocks).csv",
            "Unmerged Example PCR With MM-384PP-(Example Primer Stocks).csv",
            "Unmerged Example PCR With MM-384PP-(Example Plasmid Stocks).csv",
            "Unmerged Example PCR With MM-6RES-(Water and Buffer Plate).csv",
            "Unmerged Example PCR With MM-384LDV-(Reagents).csv",
        ]

        for picklist in validation_picklists:
            assert picklist in picklist_filenames

        for picklist in picklist_filenames:
            test_picklist = open(f"{PCR_Protocol.save_dir}/{picklist}", "r")
            validation_picklist = open(f"data/{picklist}", "r")

            assert len(test_picklist.read().split("\n")) == len(validation_picklist.read().split("\n"))

            test_picklist.close()
            validation_picklist.close()

    def test_merged_with_mm(self):

        Protocol_Name = "Merged Example PCR With MM"

        metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = True # This merges source plates with the same TYPE into one picklist

        Picklist_Save_Directory = "data/"

        Source_Plate_Directory = "data/"
        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Primer Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        PCR_Plate_Layout = bms.Labware_Layout("PCR Plate", "384 OptiAmp Plate")
        PCR_Plate_Layout.define_format(16,24)
        PCR_Plate_Layout.set_available_wells()

        Polymerase = "Q5 Polymerase"
        Polymerase_Buffer = None
        Buffer_Stock_Conc = None # x
        Master_Mix = "Q5 Master Mix"
        Master_Mix_Stock_Conc = 2 # x
        DNA_Amounts = [0.1, 0.5, 1] # uL

        Volume = 5
        Repeats = 1

        Reactions = [
            ("J23100", "VF2", "VR"),
            ("J23119", "VF2", "VR"),
            ("J23101", "VF2", "VR"),
            ("J23102", "VF2", "VR"),
            ("J23103", "VF2", "VR"),
            ("J23104", "VF2", "VR"),
            ("J23105", "VF2", "VR"),
            ("J23106", "VF2", "VR"),
            ("J23107", "VF2", "VR"),
            ("J23108", "VF2", "VR"),
            ("J23109", "VF2", "VR"),
            ("J23110", "VF2", "VR"),
            ("J23111", "VF2", "VR"),
            ("J23112", "VF2", "VR"),
            ("J23113", "VF2", "VR"),
            ("J23114", "VF2", "VR"),
            ("J23115", "VF2", "VR"),
            ("J23116", "VF2", "VR"),
            ("J23117", "VF2", "VR"),
            ("J23118", "VF2", "VR"),
            ("pOdd1", "VF2", "VR"),
        ]

        # This code block shouldn't need to be modified
        PCR_Protocol = PCR.Template(
            Name = Protocol_Name,
            Picklist_Save_Directory = Picklist_Save_Directory,
            Metadata = metadata,
            Volume= Volume,
            Reactions = Reactions,
            Polymerase = Polymerase,
            Polymerase_Buffer = Polymerase_Buffer,
            Polymerase_Buffer_Stock_Conc = Buffer_Stock_Conc,
            Master_Mix = Master_Mix,
            Master_Mix_Stock_Conc = Master_Mix_Stock_Conc,
            Repeats = Repeats,
            DNA_Amounts = DNA_Amounts,
            Source_Plates = Source_Plates,
            Destination_Plate_Layout = PCR_Plate_Layout,
            Merge = Merge_Picklists
        )
        PCR_Protocol.run()

        # Check the picklist outputs
        picklist_filenames = [f for f in os.listdir(PCR_Protocol.save_dir) if PCR_Protocol.name in f]

        assert len(picklist_filenames) == 3

        # Check that all picklists exist
        validation_picklists = [
            "Merged Example PCR With MM-384PP.csv",
            "Merged Example PCR With MM-6RES-(Water and Buffer Plate).csv",
            "Merged Example PCR With MM-384LDV-(Reagents).csv",
        ]

        for picklist in validation_picklists:
            assert picklist in picklist_filenames

        for picklist in picklist_filenames:
            test_picklist = open(f"{PCR_Protocol.save_dir}/{picklist}", "r")
            validation_picklist = open(f"data/{picklist}", "r")

            assert len(test_picklist.read().split("\n")) == len(validation_picklist.read().split("\n"))

            test_picklist.close()
            validation_picklist.close()

    def test_volume_overflow_fails(self):
        Protocol_Name = "Unmerged Example PCR No MM"

        metadata = {
            "Author": "First Last",
            "Author Email": "author@email.com",
            "User": "Your Name",
            "User Email": "user@email.com",
            "Source": "BiomationScripter v0.2.0.dev",
            "Robot": "Echo525"
        }

        Merge_Picklists = False # This merges source plates with the same TYPE into one picklist

        Picklist_Save_Directory = "data/"

        Source_Plate_Directory = "data/"
        Source_Plates = [
            bms.Import_Labware_Layout("Example DNA Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Primer Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Example Plasmid Stocks", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Water and Buffer Plate", path = Source_Plate_Directory),
            bms.Import_Labware_Layout("Reagents", path = Source_Plate_Directory),
        ]

        PCR_Plate_Layout = bms.Labware_Layout("PCR Plate", "384 OptiAmp Plate")
        PCR_Plate_Layout.define_format(16,24)
        PCR_Plate_Layout.set_available_wells()

        Polymerase = "Q5 Polymerase"
        Polymerase_Buffer = "Q5 Buffer"
        Buffer_Stock_Conc = 5 # x
        Master_Mix = False
        Master_Mix_Stock_Conc = None # x
        DNA_Amounts = [5, 10, 15] # uL

        Volume = 5
        Repeats = 1

        Reactions = [
            ("J23100", "VF2", "VR"),
            ("J23119", "VF2", "VR"),
            ("J23101", "VF2", "VR"),
            ("J23102", "VF2", "VR"),
            ("J23103", "VF2", "VR"),
            ("J23104", "VF2", "VR"),
            ("J23105", "VF2", "VR"),
            ("J23106", "VF2", "VR"),
            ("J23107", "VF2", "VR"),
            ("J23108", "VF2", "VR"),
            ("J23109", "VF2", "VR"),
            ("J23110", "VF2", "VR"),
            ("J23111", "VF2", "VR"),
            ("J23112", "VF2", "VR"),
            ("J23113", "VF2", "VR"),
            ("J23114", "VF2", "VR"),
            ("J23115", "VF2", "VR"),
            ("J23116", "VF2", "VR"),
            ("J23117", "VF2", "VR"),
            ("J23118", "VF2", "VR"),
            ("pOdd1", "VF2", "VR"),
        ]

        # This code block shouldn't need to be modified
        PCR_Protocol = PCR.Template(
            Name = Protocol_Name,
            Picklist_Save_Directory = Picklist_Save_Directory,
            Metadata = metadata,
            Volume= Volume,
            Reactions = Reactions,
            Polymerase = Polymerase,
            Polymerase_Buffer = Polymerase_Buffer,
            Polymerase_Buffer_Stock_Conc = Buffer_Stock_Conc,
            Master_Mix = Master_Mix,
            Master_Mix_Stock_Conc = Master_Mix_Stock_Conc,
            Repeats = Repeats,
            DNA_Amounts = DNA_Amounts,
            Source_Plates = Source_Plates,
            Destination_Plate_Layout = PCR_Plate_Layout,
            Merge = Merge_Picklists
        )
        with pytest.raises(bms.NegativeVolumeError) as excinfo:
            PCR_Protocol.run()

class TestOTProto:
    def test_get_location(self):
        protocol = OT2.get_protocol_api("2.11")
        protocol.home()

        labware_type = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
        labware1 = otp.load_labware(
            parent=protocol, labware_api_name=labware_type
        )

        wells = ["A1", "B4", "D6"]
        assert len(otp.get_locations(Labware=labware1, Wells=wells)) == 3

        well_range = "A4:B5"
        assert len(otp.get_locations(Labware=labware1, Wells=well_range)) == 8

        assert (
            len(
                otp.get_locations(
                    Labware=labware1, Wells=well_range, Direction="Vertical"
                )
            )
            == 6
        )

        assert (
            len(
                otp.get_locations(
                    Labware=labware1,
                    Wells=well_range,
                    Direction="Vertical",
                    Box=True,
                )
            )
            == 4
        )

    def test_get_pipette_function(self):
        protocol = OT2.get_protocol_api("2.11")
        protocol.home()

        p20 = otp.get_pipette(Protocol=protocol, Pipette="p20")
        assert p20 is None

        protocol.load_instrument("p20_single_gen2", "left")
        p20 = otp.get_pipette(Protocol=protocol, Pipette="p20")
        assert p20

    def test_load_labware_function(self):
        protocol = OT2.get_protocol_api("2.11")
        protocol.home()

        custom_labware_dir = "custom_labware/"
        labware_type = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
        default_labware = otp.load_labware(
            parent=protocol, labware_api_name=labware_type
        )

        assert protocol.deck[1]
        assert protocol.deck[12]

        for pos in range(2, 12):
            assert protocol.deck[pos] is None

class TestOTProtoTemplateSuperclass:
    def test_simple_otproto_template_superclass(self):
        class ColourMixing(otp.OTProto_Template):
            def __init__(self):
                pass

        protocol = ColourMixing()

    def test_basic_otproto_template_superclass_methods(self):
        class ColourMixing(otp.OTProto_Template):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        metadata = {
            'protocolName': 'testing',
            'author': 'Bradley Brown',
            'author-email': 'b.bradley2@newcastle.ac.uk',
            'user': '',
            'user-email': '',
            'source': 'Uses BMS 0.2.0.dev',
            'apiLevel': '2.11',
            'robotName': 'RobOT2'
        }

        protocol = OT2.get_protocol_api(metadata["apiLevel"])
        protocol.home()

        Testing_Protocol = ColourMixing(
            Protocol = protocol,
            Name = metadata["protocolName"],
            Metadata = metadata,
            Starting_20uL_Tip = "A1",
            Starting_300uL_Tip = "B6",
            Starting_1000uL_Tip = "H2"
        )

        assert Testing_Protocol._protocol == protocol
        assert Testing_Protocol.name == metadata["protocolName"]
        assert Testing_Protocol.metadata == metadata

        assert Testing_Protocol.starting_tips["p20"] == "A1"
        assert Testing_Protocol.starting_tips["p300"] == "B6"
        assert Testing_Protocol.starting_tips["p1000"] == "H2"

        Testing_Protocol.custom_labware_directory("data/custom_labware/")

        assert Testing_Protocol.custom_labware_dir == "data/custom_labware/"

        assert Testing_Protocol.pipettes_loaded() is False

        with pytest.raises(bms.RobotConfigurationError) as excinfo:
            Testing_Protocol.pipette_config("p20_single_gen2", "asdfgh")

        assert Testing_Protocol._pipettes["right"] == "p300_single_gen2"
        assert Testing_Protocol._pipettes["left"] == "p20_single_gen2"

        Testing_Protocol.pipette_config("p20_single_gen2", "right")
        Testing_Protocol.pipette_config("p300_single_gen2", "left")

        assert Testing_Protocol._pipettes["left"] == "p300_single_gen2"
        assert Testing_Protocol._pipettes["right"] == "p20_single_gen2"

        Testing_Protocol.load_pipettes()

        assert Testing_Protocol.pipettes_loaded() is True

class Test_OTProto_Heat_Shock_Transformation:

    def test_with_temp_module(self):
        protocol = OT2.get_protocol_api('2.11')
        protocol.home()


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

        Custom_Labware_Dir = "data/custom_labware"

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

        DNA_Plate = bms.Labware_Layout("DNA Plate", "appliedbiosystemsmicroampoptical_384_wellplate_20ul")

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

        DNA_Tubes = bms.Labware_Layout("DNA Tubes", "3dprinted_24_tuberack_1500ul")

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

        # Starting Tips #

        Starting_20uL_Tip = "A8"
        Starting_300uL_Tip = "A1"

        Transformation = Heat_Shock_Transformation.Template(
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
            Starting_20uL_Tip = Starting_20uL_Tip,
            Starting_300uL_Tip = Starting_300uL_Tip,
        )
        Transformation.custom_labware_dir = Custom_Labware_Dir
        Transformation.run()

        assert len(protocol.commands()) == 754

    def test_with_cooled_cells(self):
        protocol = OT2.get_protocol_api('2.11')
        protocol.home()


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

        Custom_Labware_Dir = "data/custom_labware"

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

        DNA_Plate = bms.Labware_Layout("DNA Plate", "appliedbiosystemsmicroampoptical_384_wellplate_20ul")

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

        DNA_Tubes = bms.Labware_Layout("DNA Tubes", "3dprinted_24_tuberack_1500ul")

        DNA_Tubes.bulk_add_content(
            Wells = DNA_Tubes_Wells,
            Reagents = DNA_Tubes_Content,
            Volumes = 20
        )

        DNA_Source_Layouts = [DNA_Plate, DNA_Tubes]

        # Other labware and material info #

        Competent_Cells_Source_Type = "3dprinted_24_tuberack_1500ul"

        Comp_Cells_Modules = ["temperature module gen2"]

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

        # Starting Tips #

        Starting_20uL_Tip = "A8"
        Starting_300uL_Tip = "A1"

        Transformation = Heat_Shock_Transformation.Template(
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
            Cooled_Cells_Modules=Comp_Cells_Modules,
            Starting_20uL_Tip = Starting_20uL_Tip,
            Starting_300uL_Tip = Starting_300uL_Tip,
        )
        Transformation.custom_labware_dir = Custom_Labware_Dir
        Transformation.run()

        assert len(protocol.commands()) == 755

        assert protocol.commands().count("Setting Temperature Module temperature to 4.0 °C (rounded off to nearest integer)") == 3

        assert str(protocol.deck[1]) == "Temperature Module GEN2 on 1"
        assert str(protocol.deck[3]) == "Temperature Module GEN2 on 3"

    def test_with_thermocycler(self):

        protocol = OT2.get_protocol_api('2.11')
        protocol.home()


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

        Custom_Labware_Dir = "data/custom_labware"

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

        DNA_Plate = bms.Labware_Layout("DNA Plate", "appliedbiosystemsmicroampoptical_384_wellplate_20ul")

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

        DNA_Tubes = bms.Labware_Layout("DNA Tubes", "3dprinted_24_tuberack_1500ul")

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

        # Starting Tips #

        Starting_20uL_Tip = "A8"
        Starting_300uL_Tip = "A1"

        Transformation = Heat_Shock_Transformation.Template(
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
            Heat_Shock_Modules=["Thermocycler Module"],
            Starting_20uL_Tip = Starting_20uL_Tip,
            Starting_300uL_Tip = Starting_300uL_Tip,
        )
        Transformation.custom_labware_dir = Custom_Labware_Dir
        Transformation.run()

        assert len(protocol.commands()) == 756

        assert "Opening Thermocycler lid" in protocol.commands()

        assert "Setting Thermocycler well block temperature to 4.0 °C" in protocol.commands()

    def test_with_multiple_destinations(self):
        protocol = OT2.get_protocol_api('2.11')
        protocol.home()


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

        Custom_Labware_Dir = "data/custom_labware"

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

        DNA_Plate = bms.Labware_Layout("DNA Plate", "appliedbiosystemsmicroampoptical_384_wellplate_20ul")

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

        DNA_Tubes = bms.Labware_Layout("DNA Tubes", "3dprinted_24_tuberack_1500ul")

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

        Competent_Cells_Aliquot_Vol = 1000 # uL
        Media_Aliquot_Vol = 5000 # uL

        # Protocol Parameters #

        DNA_Per_Transformation = 3 # uL
        Competent_Cells_Volume = 20 # uL
        Final_Volume = 100 # uL
        Heat_Shock_Time = 30 # Seconds
        Heat_Shock_Temp = 42 # celcius
        Wait_Before_Shock = 300 # seconds
        Reps = 10

        # Starting Tips #

        Starting_20uL_Tip = "A8"
        Starting_300uL_Tip = "A1"

        Transformation = Heat_Shock_Transformation.Template(
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
            Heat_Shock_Modules=["temperature module gen2", "temperature module gen2"],
            Starting_20uL_Tip = Starting_20uL_Tip,
            Starting_300uL_Tip = Starting_300uL_Tip,
        )
        Transformation.custom_labware_dir = Custom_Labware_Dir
        Transformation.run()

        assert len(protocol.commands()) == 3800

        assert protocol.commands().count("Setting Temperature Module temperature to 4.0 °C (rounded off to nearest integer)") == 4
