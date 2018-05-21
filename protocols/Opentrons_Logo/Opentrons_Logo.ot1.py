"""
@author Opentrons
@date April 27th, 2018
@version 1.3
"""
from opentrons import containers, instruments
from otcustomizers import StringSelection


def run_custom_protocol(pipette_type: StringSelection(
    'p300-Single', 'p50-Single', 'p10-Single')='p300-Single',
    dye_labware_type: StringSelection(
        'trough-12row', 'tube-rack-2ml')='trough-12row'):
    if pipette_type == 'p300-Single':
        tiprack = containers.load('tiprack-200ul', 'A1')
        pipette = instruments.Pipette(
            axis='a',
            max_volume=300,
            tip_racks=[tiprack])
    elif pipette_type == 'p50-Single':
        tiprack = containers.load('tiprack-200ul', 'A1')
        pipette = instruments.Pipette(
            axis='a',
            max_volume=50,
            tip_racks=[tiprack])
    elif pipette_type == 'p10-Single':
        tiprack = containers.load('tiprack-10ul', 'A1')
        pipette = instruments.Pipette(
            axis='a',
            max_volume=10,
            tip_racks=[tiprack])

    if dye_labware_type == 'trough-12row':
        dye_container = containers.load('trough-12row', 'B2')
    else:
        dye_container = containers.load('tube-rack-2ml', 'B2')

    output = containers.load('96-flat', 'D1')
    # Well Location set-up
    dye1_wells = ['A5', 'A6', 'A8', 'A9', 'B4', 'B10', 'C3', 'C11', 'D3',
                  'D11', 'E3', 'E11', 'F3', 'F11', 'G4', 'G10',
                  'H5', 'H6', 'H7', 'H8', 'H9']

    dye2_wells = ['C7', 'D6', 'D7', 'D8', 'E5', 'E6', 'E7', 'E8',
                  'E9', 'F5', 'F6', 'F7', 'F8', 'F9', 'G6', 'G7', 'G8']

    dye2 = dye_container.wells('A1')
    dye1 = dye_container.wells('A2')

    pipette.distribute(
        50,
        dye1,
        output.wells(dye1_wells),
        new_tip='once')
    pipette.distribute(
        50,
        dye2,
        output.wells(dye2_wells),
        new_tip='once')
