metadata = {
    'protocolName': 'Phytip Protein A, ProPlus, ProPlus LX Columns:\
     Plate Prep',
    'author': 'Boren Lin',
    'source': '',
    'apiLevel': '2.11'
}


def run(ctx):
    [_num_samples, _vol_eql, _vol_wash1, _vol_wash2, _vol_eln, _p300mnt
     ] = get_values(  # noqa: F821
     '_num_samples', '_vol_eql', '_vol_wash1',
     '_vol_wash2', '_vol_eln', '_p300mnt')

    NUM_SAMPLES = _num_samples

    # liquid volume uL - Max. 200
    VOL_EQL = _vol_eql
    VOL_WASH1 = _vol_wash1
    VOL_WASH2 = _vol_wash2
    VOL_ELN = _vol_eln
    p300mnt = _p300mnt

    for vol in [VOL_EQL, VOL_WASH1, VOL_WASH2, VOL_ELN]:
        if vol > 200:
            raise Exception('Volume must be less than 200µL.')

    total_cols = int(NUM_SAMPLES//8)
    r1 = int(NUM_SAMPLES % 8)
    if r1 != 0:
        total_cols = total_cols + 1
    # load labware
    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '6')]
    m300 = ctx.load_instrument(
        'p300_multi_gen2', p300mnt, tip_racks=tiprack300)

    equilibration_plate = ctx.load_labware(
        'thermoscientific_96_wellplate_v_450', '9', 'equilibration plate')
    wash1_plate = ctx.load_labware(
        'thermoscientific_96_wellplate_v_450', '5', 'wash plate 1')
    wash2_plate = ctx.load_labware(
        'thermoscientific_96_wellplate_v_450', '7', 'wash plate 2')
    elution_plate = ctx.load_labware(
        'thermoscientific_96_wellplate_v_450', '11', 'elute plate')

    eql = equilibration_plate.rows()[0][:total_cols]
    wash1 = wash1_plate.rows()[0][:total_cols]
    wash2 = wash2_plate.rows()[0][:total_cols]
    eln = elution_plate.rows()[0][:total_cols]

    reagents = ctx.load_labware('nest_12_reservoir_15ml', '8', 'reagents')

    eql1_stock, eql2_stock, wash11_stock, wash12_stock, wash21_stock,\
        wash22_stock, eln1_stock, eln2_stock = [
            reagents.wells()[0],
            reagents.wells()[1],
            reagents.wells()[2],
            reagents.wells()[3],
            reagents.wells()[4],
            reagents.wells()[5],
            reagents.wells()[6],
            reagents.wells()[7]]

    # transfer reagent sequences
    def reagent_transfer(start1, start2, end, vol, cols):
        if vol > 100:
            vol1 = 100
            vol2 = vol - 100
            m300.mix(2, vol1, start1)
            for i in range(cols):
                m300.aspirate(vol1, start1)
                m300.dispense(vol1, end[i].top(z=-2), rate=0.5)
                m300.touch_tip()
            m300.mix(2, vol2, start2)
            for i in range(cols):
                m300.aspirate(vol2, start2)
                m300.dispense(vol2, end[i].top(z=-2), rate=0.5)
                m300.touch_tip()
        else:
            m300.mix(2, vol, start1)
            for i in range(cols):
                m300.aspirate(vol, start1)
                m300.dispense(vol, end[i].top(z=-2), rate=0.5)
                m300.touch_tip()

    # perform
    m300.pick_up_tip()
    reagent_transfer(eql1_stock, eql2_stock, eql, VOL_EQL, total_cols)
    reagent_transfer(wash11_stock, wash12_stock, wash1, VOL_WASH1, total_cols)
    reagent_transfer(wash21_stock, wash22_stock, wash2, VOL_WASH2, total_cols)
    reagent_transfer(eln1_stock, eln2_stock, eln, VOL_ELN, total_cols)
    m300.drop_tip()
