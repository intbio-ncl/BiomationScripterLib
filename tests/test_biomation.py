import os
from itertools import product
from copy import deepcopy

import pytest
from opentrons import simulate as OT2

import BiomationScripter as bms
from BiomationScripter import EchoProto as ep
from BiomationScripter import OTProto as otp


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
    dna_stocks_path = "Resources/For Docs/Labware_Layout_Files/"
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


def test_serial_dilution_volumes():
    final_volume = 100
    dilution_factors = [1, 2, 4, 8, 16, 32]

    sample_volumes, solution_volumes = bms.serial_dilution_volumes(
        dilution_factors=dilution_factors, total_volume=final_volume
    )

    assert sample_volumes == [100.0, 50.0, 50.0, 50.0, 50.0, 50.0]
    assert solution_volumes == [0.0, 50.0, 50.0, 50.0, 50.0, 50.0]

    dilution_factors = [1, 2, 10, 50, 75, 100, 200]

    sample_volumes, solution_volumes = bms.serial_dilution_volumes(
        dilution_factors=dilution_factors, total_volume=final_volume
    )
    assert sample_volumes == [
        100.0,
        50.0,
        20.0,
        20.0,
        66.66666666666666,
        75.0,
        50.0,
    ]
    assert solution_volumes == [
        0.0,
        50.0,
        80.0,
        80.0,
        33.33333333333334,
        25.0,
        50.0,
    ]


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
                path="Resources/For Docs/Labware_Layout_Files/",
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
            Picklist_Save_Directory="./Resources/",
        )

        assert protocol.name == "Walkthrough Example - Colour Mixing"
        assert protocol.source_plate_layouts == colour_source_plates
        assert protocol.destination_plate_layouts == [mixuture_plate_layout]
        assert protocol.save_dir == "./Resources/"


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

        expected_fname = "/tmp/Example Protocol-384PP-(DNA_Source_Plate).csv"
        if os.path.isfile(expected_fname):
            os.remove(expected_fname)

        ep.Write_Picklists(protocol_cp, Save_Location="/tmp", Merge=False)

        assert os.path.isfile(expected_fname)
        os.remove(expected_fname)


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