import BiomationScripter as _BMS
import BiomationScripter.OTProto as _OTProto
from opentrons import simulate as OT2
import math
import warnings
from typing import List, NewType, Tuple, Union
from collections import namedtuple


class Template(_OTProto.OTProto_Template):
    def __init__(self,
        DoE_File,
        Source_Materials,
        Destination_Content,
        Labware_APIs,
        Replicates_Per_Run = 1,
        Intermediates = {},
        Batch_Info = [None, None],
        **kwargs
    ):

        ########################################
        # User defined aspects of the protocol #
        ########################################
        self.doe_file = DoE_File
        self.batch_factor = Batch_Info[0]
        self.batch_value = Batch_Info[1]
        self.run_replicates = Replicates_Per_Run

        #############
        # Materials #
        #############
        self.source_materials = Source_Materials
        self.intermediates = Intermediates

        ###########################
        # Destination Information #
        ###########################
        self.destination_content = Destination_Content
        self.destination_layout = None

        ###########
        # Labware #
        ###########
        self.labware_apis = Labware_APIs
        self.labware_layouts = {}

        ##################################################
        # Protocol Metadata and Instrument Configuration #
        ##################################################
        super().__init__(**kwargs)

    def run(self):
        super().run()

        #################
        # Load DoE Data #
        #################
        if self.batch_factor and self.batch_value:
            DoE = _BMS.DoE_Experiment(self.metadata["protocolName"], self.doe_file).batch_by_factor_value(self.batch_factor, self.batch_value)
        else:
            DoE = _BMS.DoE_Experiment(self.metadata["protocolName"], self.doe_file)

        ###########################
        # Set up source materials #
        ###########################
        for source_material in self.source_materials:
        # If the source material has several variations based on factor values, deal with it
            if type(self.source_materials[source_material][0]) is list:
                factor_components = self.source_materials[source_material][0]
                materials_in_run_order = _BMS.DoE_Create_Source_Material(DoE, source_material, factor_components)
                unique_materials = set(materials_in_run_order)

                print("\nThe following combinations of {} are required:".format(source_material))
                for material in unique_materials:
                    print("{} * {}".format(material, materials_in_run_order.count(material)))



            # If source material is explicitly linked to a factor, deal with it differently to above (obvs)
            else:
                source_material_name = source_material
                source_material_factor = self.source_materials[source_material][0]


                _BMS.DoE_Create_Source_Material(DoE, source_material, source_material_factor)

                print("\n{} is required as a source material.".format(source_material_name))



        ########################
        # Set up intermediates #
        ########################

        for intermediate in self.intermediates:
            source_components = [component[0] for component in self.intermediates[intermediate]]
            source_components_amount_types = [component[1] for component in self.intermediates[intermediate]]
            source_components_amount_values = [component[2] for component in self.intermediates[intermediate]]


            intermediates_in_run_order = _BMS.DoE_Create_Intermediate(DoE, intermediate, source_components, source_components_amount_types, source_components_amount_values)
            unique_intermediates = set(intermediates_in_run_order)

            print("\nThe following combinations of {} are required:".format(intermediate))
            for unique_intermediate in unique_intermediates:
                print("{} * {}".format(unique_intermediate, intermediates_in_run_order.count(unique_intermediate)))

        #############################
        # Set up destination layout #
        #############################

        # Create destination labware layout and add content
        ## Content should be mastermix type and volume, and cell type and volume
        self.labware_layouts["Destination"] = _BMS.Labware_Layout("Destination Labware", self.labware_apis["Destination"])

        Destination_Layout = self.labware_layouts["Destination"]
        Destination_Labware_Format = _BMS.OTProto.get_labware_format(Destination_Layout.type, self.custom_labware_dir)
        Destination_Layout.define_format(Destination_Labware_Format[0], Destination_Labware_Format[1])
        Destination_Well_Range = Destination_Layout.get_well_range(Use_Outer_Wells=False)

        # Determine how many destination wells are required
        ## Calculation uses the number of runs, the number of controls per run, and the number of replicates required
        number_of_runs = len(DoE.runs)
        # len(Destination_Content.keys()) ensures that slots for controls are accounted for, as well as just the samples
        Destination_Slots_Required = (number_of_runs * len(self.destination_content.keys())) * self.run_replicates

        if not Destination_Slots_Required <= len(Destination_Well_Range):
            raise _BMS.LabwareError("Not enough wells in destination plate to set up this experiment ({} needed, {} available)".format(len(DoE.runs) * 6, len(Destination_Well_Range)))

        well_index = 0
        for run in DoE.runs:
            for sample_type in self.destination_content:
                for replicate in range(0, self.run_replicates):
                    content_to_add = []
                    destination_well = Destination_Well_Range[well_index]
                    for content_info in self.destination_content[sample_type]:
                        content = run.get_value_by_name(content_info[0])
                        content_volume = content_info[1]
                        Destination_Layout.add_content(destination_well, content, content_volume)
                    well_index += 1

        print("\n")
        Destination_Layout.print()
        self.destination_layout = Destination_Layout

        #################################
        # Set up intermediate layout(s) #
        #################################

        # Intermediate labware have two representations: intermediate as a destination and intermediate as a source
        ## The intermediate as destination lists the source materials required in each well
        ## The intermediate as a source lists the newly named intermediate materials

        for intermediate in self.intermediates:


            # Set up intermediate as source layout
            self.labware_layouts["{} as source".format(intermediate)] = _BMS.Labware_Layout("{} Labware".format(intermediate), self.labware_apis[intermediate])
            intermediate_as_source_layout = self.labware_layouts["{} as source".format(intermediate)]
            intermediate_as_source_labware_format = _BMS.OTProto.get_labware_format(intermediate_as_source_layout.type, self.custom_labware_dir)
            intermediate_as_source_layout.define_format(intermediate_as_source_labware_format[0], intermediate_as_source_labware_format[1])

            # Set up intermediate as destination layout
            self.labware_layouts["{} as destination".format(intermediate)] = _BMS.Labware_Layout("{} Labware".format(intermediate), self.labware_apis[intermediate])
            intermediate_as_destination_layout = self.labware_layouts["{} as destination".format(intermediate)]
            intermediate_as_destination_labware_format = _BMS.OTProto.get_labware_format(intermediate_as_destination_layout.type, self.custom_labware_dir)
            intermediate_as_destination_layout.define_format(intermediate_as_destination_labware_format[0], intermediate_as_destination_labware_format[1])

            # Get intermediate labware well range and capacity
            ## intermediate as source and intermediate as destination are the same thing,
            ## ...so these don't need to be got separately
            intermediate_well_range = intermediate_as_source_layout.get_well_range()
            intermediate_well_capacity = _BMS.OTProto.get_labware_well_capacity(intermediate_as_source_layout.type, self.custom_labware_dir)

            # Get the names of the intermediates; these will be added to the intermediate as source layout
            intermediates_in_run_order = DoE.get_all_values(intermediate)
            unique_intermediates = set(intermediates_in_run_order)

            # Add the intermediate names to the intermediate as source layout
            # Also add the intermediate components to the intermediate as destination layout
            well_index = 0

            # Get information about the components which make up the intermediates
            source_components_info = self.intermediates[intermediate]

            for unique_intermediate in unique_intermediates:
                # Get volume of intermediate required to fill the destination labware
                volume_required = 0

                intermediate_object = DoE.get_intermediate(unique_intermediate)

                for well in self.labware_layouts["Destination"].get_wells_containing_liquid(unique_intermediate):
                    volume_required += self.labware_layouts["Destination"].get_volume_of_liquid_in_well(unique_intermediate, well)

                # Add an additional 10% to account for pipetting errors, dead volume, etc.
                volume_required += volume_required*0.1

                slots_required = math.ceil(volume_required/intermediate_well_capacity)
                volume_per_slot = volume_required/slots_required

                for slot in range(0, slots_required):
                    intermediate_as_source_layout.add_content(intermediate_well_range[well_index], unique_intermediate, volume_per_slot)


                    # Calculate how much of each source material is required for this intermediate type
                    ## Create a variable to store the component which makes up the intermediate...
                    ## ... to a final volume, if applicable
                    make_up_to_final_volume = None

                    volume_in_slot = 0

                    for component_info in source_components_info:
                        # Convert each of the source component infos to a volume (in uL)
                        component_name, value_type, value_or_ref = component_info
                        component_volume = None

                        if value_type == "volume":
                            # Check if the value_or_ref is an int/float which specifies a constant volume
                            if type(value_or_ref) is int or type(value_or_ref) is float:
                                component_volume = value_or_ref
                            # Check if the value_or_ref specifies that this component should be used to...
                            # ... make up the intermediate to a final volume
                            elif value_or_ref == "make up to final volume":
                                component_volume = value_or_ref
                                make_up_to_final_volume = component_name
                                continue
                            # If neither of the above cases are true, assume that value_or_ref is a reference...
                            # ... to a DoE factor, which should be present in the intermediate name
                            else:
                                component_volume = float(unique_intermediate.split(value_or_ref)[1].split("(")[1].split(")")[0])

                        # Check if "concentration" is in value_type rather than is value_type == "concentration"...
                        # ... as concentration should be supplied "concentration-{}".format(stock concentration)
                        elif "concentration" in value_type:
                            # Get the stock concentration of the component
                            stock_concentration = float(value_type.split("-")[1])

                            # Check if the value_or_ref is an int/float which specifies a constant concentration
                            if type(value_or_ref) is int or type(value_or_ref) is float:
                                final_concentration = value_or_ref
                            # If not, assume that value_or_ref is a reference to a DoE factor, which should be...
                            # ... present in the intermediate name
                            else:

                                final_concentration = float(intermediate_object.components[component_name][2])


                            # Calculate what the concentration in the intermediate should be (as this will be diluted in the destination)
                            intermediate_dilution_in_destination = set()

                            # For each well in the destination which contains this intermediate
                            for well in self.labware_layouts["Destination"].get_wells_containing_liquid(unique_intermediate):
                                # Get the volume of the intermediate in the well
                                intermediate_volume_in_destination = self.labware_layouts["Destination"].get_volume_of_liquid_in_well(unique_intermediate, well)
                                # And the final volume of the destination well
                                final_destination_volume = 0
                                for component in self.labware_layouts["Destination"].get_liquids_in_well(well):
                                    final_destination_volume += self.labware_layouts["Destination"].get_volume_of_liquid_in_well(component, well)

                                # Calculate how much the intermediate is diluted in the destination well and add to the pre-prepared set
                                intermediate_dilution_in_destination.add(intermediate_volume_in_destination/final_destination_volume)

                            # Check that the dilution factor is the same across all wells for this unique intermediate
                            ## Raise an error if not because that would be difficult to handle
                            if not len(intermediate_dilution_in_destination) == 1:
                                raise _BMS.DoEError("Same amount of intermediate {} must be added to all destination wells as this is difficult to deal with at the moment.".format(unique_intermediate))

                            intermediate_dilution_in_destination = intermediate_dilution_in_destination.pop()
                            concentration_in_intermediate = final_concentration/intermediate_dilution_in_destination

                            # Calculate the volume which needs to be added to the intermediate from the stock solution
                            component_volume = round((concentration_in_intermediate*volume_per_slot)/stock_concentration, 1)

                            # Sanity check the volume being added
                            if component_volume <= 0:
                                raise _BMS.NegativeVolumeError("Volume of {} to be added to {} is too small".format(component_name, unique_intermediate))

                        else:
                            raise _BMS.DoEError("Value type for {} in {} must be either 'volume' or 'concentration-{stock_concentration}'".format(component_name, intermediate))

                        # Add the component and volume to the intermediate_as_destination layout



                        intermediate_as_destination_layout.add_content(intermediate_well_range[well_index], intermediate_object.components[component_name][0], component_volume)
                        volume_in_slot += component_volume


                    # If one of the components specified that it should be used to make up any remaining volume, deal with it now
                    if make_up_to_final_volume:
                        intermediate_as_destination_layout.add_content(intermediate_well_range[well_index], intermediate_object.components[make_up_to_final_volume][0], volume_per_slot - volume_in_slot)
                        volume_in_slot += volume_per_slot - volume_in_slot

                    # Sanity check:
                    if not volume_in_slot == volume_per_slot:
                        raise _BMS.DoEError("Calculation error for intermediate {} in well {}:\nVolume Added: {}\nVolume Expected: {}".format(unique_intermediate, intermediate_well_range[well_index], volume_in_slot, volume_per_slot))

                    well_index += 1



            print("\nAs Destination")
            intermediate_as_destination_layout.print()
            print("\nAs Source")
            intermediate_as_source_layout.print()

        ###########################
        # Set up source layout(s) #
        ###########################

        for source_material in self.source_materials:
            # Set up source material layout
            self.labware_layouts[source_material] = _BMS.Labware_Layout("{} Labware".format(source_material), self.labware_apis[source_material])
            source_material_layout = self.labware_layouts[source_material]
            source_material_labware_format = _BMS.OTProto.get_labware_format(source_material_layout.type, self.custom_labware_dir)
            source_material_layout.define_format(source_material_labware_format[0], source_material_labware_format[1])
            source_material_well_range = source_material_layout.get_well_range()

            well_index = 0

            unique_source_ids = set(DoE.get_all_values(source_material))

            for source_id in unique_source_ids:
                # iterate through all wells in intermediate as destination layout with current source_id...
                # ... to calculate the total volume required, then add 10% more to account for dead volumes etc.

                source_id_volume_required = 0

                # Check all "intermediate as destination" layouts for the source material id, and add the required volume to the total
                for intermediate in self.intermediates:
                    intermediate_layout = self.labware_layouts["{} as destination".format(intermediate)]
                    for well in intermediate_layout.get_wells_containing_liquid(source_id):
                        source_id_volume_required += intermediate_layout.get_volume_of_liquid_in_well(source_id, well)

                # Do the above with the destination layout
                destination_layout = self.labware_layouts["Destination"]
                for well in destination_layout.get_wells_containing_liquid(source_id):
                    source_id_volume_required += destination_layout.get_volume_of_liquid_in_well(source_id, well)

                source_id_volume_required += source_id_volume_required * 0.1 # Add 10% more required volume for pipetting accuracy


                aliquot_volume = self.source_materials[source_material][1]
                slots_required = math.ceil(source_id_volume_required/aliquot_volume)

                print("Requires {} uL of {} total - {} aliquots".format(source_id_volume_required, source_id, slots_required))

                for slot in range(0, slots_required):
                    source_material_layout.add_content(source_material_well_range[well_index], source_id, aliquot_volume)
                    well_index += 1

            print("\n")
            source_material_layout.print()

        ########################################
        # Convert layouts to opentrons labware #
        ########################################

        # Create protocol to generate intermediates from source layouts
        source_layouts = []
        destination_layouts = []

        for layout in self.labware_layouts:
            if layout in self.source_materials.keys():
                source_layouts.append(self.labware_layouts[layout])
            elif " as destination" in layout and layout.replace(" as destination", "") in self.intermediates.keys():
                destination_layouts.append(self.labware_layouts[layout])



        Intermediate_Prep_Protocol = _OTProto.Templates.Protocol_From_Layouts(
                                        Protocol = self._protocol,
                                        Name=self.metadata["protocolName"],
                                        Metadata=self.metadata,
                                        Source_Layouts = source_layouts,
                                        Destination_Layouts = destination_layouts
        )
        Intermediate_Prep_Protocol.custom_labware_dir = self.custom_labware_dir
        Intermediate_Prep_Protocol.run()

        self._protocol.pause("Re-load the deck as stated below, and then click continue")

        # Create protocol to generate destination plate
        source_layouts = []
        destination_layouts = []

        for layout in self.labware_layouts:
            if layout in self.source_materials.keys():
                source_layouts.append(self.labware_layouts[layout])
            elif " as source" in layout and layout.replace(" as source", "") in self.intermediates.keys():
                source_layouts.append(self.labware_layouts[layout])
            elif "Destination" in layout:
                destination_layouts.append(self.labware_layouts[layout])

        Destination_Prep_Protocol = _OTProto.Templates.Protocol_From_Layouts(
                                    Protocol = self._protocol,
                                    Name=self.metadata["protocolName"],
                                    Metadata=self.metadata,
                                    Source_Layouts = source_layouts,
                                    Destination_Layouts = destination_layouts
        )
        Destination_Prep_Protocol.custom_labware_dir = self.custom_labware_dir
        Destination_Prep_Protocol.run_as_module(self)
