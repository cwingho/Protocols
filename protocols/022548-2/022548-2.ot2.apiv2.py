from opentrons import protocol_api
from opentrons.protocol_api.labware import Well, Labware
from math import pi, ceil
from typing import Sequence, Tuple
import re


metadata = {
    'protocolName': '022548-2 - DNA extraction',
    'author': 'Eskil Andersen <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def parse_range_string(range_string: str) -> Tuple[int, int]:
    """ Parses a range or a single number from the input string.
    the format for a number is n-m, where n and m are any positive
    integers.
    :param range_string: range string to decode
    :return value: A tuple of the start and end index of the range
    """
    single_num_pattern = re.compile('[0-9]+')
    range_pattern = re.compile('[0-9]+-[0-9]+')
    # Case when there's only one index (e.g. the string decodes to a single
    # well
    if single_num_pattern.fullmatch(range_string) is not None:
        index = int(range_string)
        return index, index
    if range_pattern.fullmatch(range_string):
        # Return both substrings that match numbers (i.e. the start and
        # end indices
        start, end = range_string.split('-')
        return int(start), int(end)
    # If neither regular expression matched then we assume that the string
    # is incorrectly formatted
    raise Exception(("Invalid range string: it was \"{}\" but should be a "
                     "natural number or a range in the format of "
                     "n-m where n and m are natural numbers, "
                     "e.g: 1-4").format(range_string))


def is_15ml_tube(well: Well):
    name = str(well).lower()
    if "tube" not in name or "15" not in name:
        return False
    return True


def tube_15ml_cone_height(tube: Well):
    """
    :return value: Approximate height of the tube cone
    """

    if not is_15ml_tube(tube):
        msg = ("The input well parameter: {}, does not appear to "
               "be a 15 mL tube")
        msg.format(tube)
        raise Exception(msg)
    return 0.171 * tube.depth


def tube_liq_height(vol, tube: Well, is_min_cone_height: bool = True):
    """
    Calculates the height of the liquid level in a conical tube
    given its liquid volume.The function tries to account for the conical
    part of the tube
    :param vol: The volume in uL
    :param tuberack: The tuberack with the tubes
    :param is_min_cone_height: Always return the height of the cone at
    minimum
    :return value: The height of the liquid level measured from
    the bottom in mm
    """

    if not is_15ml_tube(tube):
        msg = ("The input well parameter: {}, does not appear to "
               "be a 15 mL tube")
        msg.format(tube)
        raise Exception(msg)

    r = tube.diameter/2
    # Fudge factor - height seems too low given a volume, so bump it up
    # a little bit by "decreasing" the radius
    r *= 0.94

    # Cone height approximation
    h_cone_max = tube_15ml_cone_height(tube)
    vol_cone_max = (h_cone_max*pi*r**2)/3

    if vol < vol_cone_max:
        h_cone = (3*vol)/(pi*r**2)
        # print("h_cone", h_cone)
        if is_min_cone_height:
            return h_cone_max
        return h_cone
    else:
        cylinder_partial_vol = vol - vol_cone_max
        # print('cylinder v', cylinder_partial_vol,
        # 'cone max vol', vol_cone_max)
        h_partial_tube = cylinder_partial_vol/(pi*r**2)
        # print('h cone max', h_cone_max, 'h partial tube', h_partial_tube)
        return h_cone_max + h_partial_tube


def get_values(*names):
    import json
    _all_values = json.loads("""{
                                  "n_sample_tuberacks":3,
                                  "n_samples_rack_1":32,
                                  "n_samples_rack_2":15,
                                  "n_samples_rack_3":0,
                                  "master_mix_range":"7-12",
                                  "mastermix_max_vol":9.54,
                                  "mastermix_tuberack_lname":false,
                                  "mastermix_mix_rate_multiplier":0.3,
                                  "mm_aspiration_flowrate_multiplier":0.1,
                                  "mm_dispense_flowrate_multiplier":0.1,
                                  "p300_mount":"left",
                                  "m300_mount":"right"
                                  }
                                  """)
    return [_all_values[n] for n in names]


def run(ctx: protocol_api.ProtocolContext):

    [n_sample_tuberacks,
     n_samples_rack_1,
     n_samples_rack_2,
     n_samples_rack_3,
     master_mix_range,
     mastermix_max_vol,
     mastermix_tuberack_lname,
     mastermix_mix_rate_multiplier,
     mm_aspiration_flowrate_multiplier,
     mm_dispense_flowrate_multiplier,
     p300_mount,
     m300_mount] = get_values(  # noqa: F821
     "n_sample_tuberacks",
     "n_samples_rack_1",
     "n_samples_rack_2",
     "n_samples_rack_3",
     "master_mix_range",
     "mastermix_max_vol",
     "mastermix_tuberack_lname",
     "mastermix_mix_rate_multiplier",
     "mm_aspiration_flowrate_multiplier",
     "mm_dispense_flowrate_multiplier",
     "p300_mount",
     "m300_mount")

    is_verbose_mode = True

    if n_sample_tuberacks > 3 or n_sample_tuberacks < 1:
        raise Exception(
            "The number of sample tube racks should be between 1 to 3 max")

    n_total_samples = 0
    for i, n in enumerate([n_samples_rack_1,
                           n_samples_rack_2,
                           n_samples_rack_3]):
        if n < 0 or n > 32:
            raise Exception(
                "Invalid number of samples (n={}) on tuberack #{}".format(
                    n, i+1)
                )
        n_total_samples += n

    # Check that there are enough mastermix wells

    # Todo: If tuberack: Error check that all tubes are 15 mL types

    # Define labware and slots
    sample_tuberack_loader = \
        ("nest_32_tuberack_8x15ml_8x15ml_8x15ml_8x15ml", ['2', '4', '7'])
    target_plate_loader = \
        ("thermofisherkingfisherdeepwell_96_wellplate_2000ul", '1')
    mastermix_source_lname = \
        ('nest_12_reservoir_15ml'
         if mastermix_tuberack_lname is False
         else mastermix_tuberack_lname)
    mastermix_labware_loader = (mastermix_source_lname, '10')
    sample_200ul_filtertiprack_loader = \
        ('opentrons_96_filtertiprack_200ul', '6')
    mastermix_300uL_tiprack_loader = ('opentrons_96_tiprack_300ul', '11')

    mm_well_vol_ul = mastermix_max_vol * 1_000
    # TODO: Remove dead volumes from the protocols - the dead-volume is
    # already defined by the 1.5 multiplier (1/3rd of the total vol)
    dead_vol = 1/3 * mm_well_vol_ul
    mm_pip = 'single' if mastermix_tuberack_lname is not False else 'multi'

    is_mm_pip_single = True if mm_pip == 'single' else False
    is_mm_source_tuberack = is_mm_pip_single

    mm_start_index, mm_end_index = parse_range_string(master_mix_range)
    n_mm_wells = mm_end_index - mm_start_index + 1
    mm_vol_per_sample = 275
    total_mm_vol = mm_vol_per_sample * n_total_samples * 1.5
    last_mm_well_vol = total_mm_vol % mm_well_vol_ul
    if is_mm_source_tuberack:
        last_dead_vol = min(last_mm_well_vol * 1/3, 100)
    else:
        last_dead_vol = min(last_mm_well_vol * 1/3, 1000)
    # update last_mm_well_vol because it should be twice as much as the dead
    # volume which might have changed because of these operations
    last_mm_well_vol = last_dead_vol * 2
    total_last_mm_vol = last_mm_well_vol + last_dead_vol

    # No more than 5 wells should be required for the mastermix
    # maximum number of samples: 31*3=93, mm volume per sample = 275
    # excess volume factor: 1.5
    # 93*275*1.5=38,362.5 uL, max volume per mm well is 9540 uL
    # n_wells = 38262.5/9540 = 4.02 wells
    n_required_mm_wells = ceil(total_mm_vol/(mm_well_vol_ul-dead_vol))
    if n_required_mm_wells > n_mm_wells:
        msg = ("This protocol run requires {} wells of mastermix, but "
               "there are only {} wells available, please ensure that there "
               "is enough mastermix")
        msg = msg.format(n_required_mm_wells, n_mm_wells)
        raise Exception(msg)

    # define all custom variables above here with descriptions:

    # load modules

    '''

    Add your modules here with:

    module_name = ctx.load_module('{module_loadname}', '{slot number}')

    Note: if you are loading a thermocycler, you do not need to specify
    a slot number - thermocyclers will always occupy slots 7, 8, 10, and 11.

    For all other modules, you can load them on slots 1, 3, 4, 6, 7, 9, 10.

    '''

    # load labware

    '''

    Add your labware here with:

    labware_name = ctx.load_labware('{loadname}', '{slot number}')

    If loading labware on a module, you can load with:

    labware_name = module_name.load_labware('{loadname}')
    where module_name is defined above.

    '''
    sample_rack_1 = ctx.load_labware(
        sample_tuberack_loader[0], sample_tuberack_loader[1][0])
    sample_rack_2 = ctx.load_labware(
        sample_tuberack_loader[0], sample_tuberack_loader[1][1])
    sample_rack_3 = ctx.load_labware(
        sample_tuberack_loader[0], sample_tuberack_loader[1][2])
    target_plate = ctx.load_labware(
        target_plate_loader[0], target_plate_loader[1])
    mm_source = ctx.load_labware(
        mastermix_labware_loader[0], mastermix_labware_loader[1])
    # load tipracks

    '''

    Add your tipracks here as a list:

    For a single tip rack:

    tiprack_name = [ctx.load_labware('{loadname}', '{slot number}')]

    For multiple tip racks of the same type:

    tiprack_name = [ctx.load_labware('{loadname}', 'slot')
                     for slot in ['1', '2', '3']]

    If two different tipracks are on the deck, use convention:
    tiprack[number of microliters]
    e.g. tiprack10, tiprack20, tiprack200, tiprack300, tiprack1000

    '''
    tiprack_200 = ctx.load_labware(sample_200ul_filtertiprack_loader[0],
                                   sample_200ul_filtertiprack_loader[1])
    tiprack_300 = ctx.load_labware(mastermix_300uL_tiprack_loader[0],
                                   mastermix_300uL_tiprack_loader[1])

    # load instrument

    '''
    Nomenclature for pipette:

    use 'p'  for single-channel, 'm' for multi-channel,
    followed by number of microliters.

    p20, p300, p1000 (single channel pipettes)
    m20, m300 (multi-channel pipettes)

    If loading pipette, load with:

    ctx.load_instrument(
                        '{pipette api load name}',
                        pipette_mount ("left", or "right"),
                        tip_racks=tiprack
                        )
    '''
    p300 = ctx.load_instrument(
                              'p300_single_gen2',
                              p300_mount,
                              tip_racks=[tiprack_200]
                              )
    m300 = ctx.load_instrument(
                              'p300_multi_gen2',
                              m300_mount,
                              tip_racks=[tiprack_300]
                              )

    # pipette functions   # INCLUDE ANY BINDING TO CLASS

    '''

    Define all pipette functions, and class extensions here.
    These may include but are not limited to:

    - Custom pickup functions
    - Custom drop tip functions
    - Custom Tip tracking functions
    - Custom Trash tracking functions
    - Slow tip withdrawal

    For any functions in your protocol, describe the function as well as
    describe the parameters which are to be passed in as a docstring below
    the function (see below).

    def pick_up(pipette):
        """`pick_up()` will pause the protocol when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the protocol will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the protocol (e.g. p300, m20).
        """
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    '''
    def pick_up(pipette):
        """`pick_up()` will pause the protocol when all tip boxes are out of
        tips, prompting the user to replace all tip racks. Once tipracks are
        reset, the protocol will start picking up tips from the first tip
        box as defined in the slot order when assigning the labware definition
        for that tip box. `pick_up()` will track tips for both pipettes if
        applicable.

        :param pipette: The pipette desired to pick up tip
        as definited earlier in the protocol (e.g. p300, m20).
        """
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    # helper functions
    '''
    Define any custom helper functions outside of the pipette scope here, using
    the convention seen above.

    e.g.

    def remove_supernatant(vol, index):
        """
        function description

        :param vol:

        :param index:
        """


    '''
    class VolTracker:
        def __init__(self, labware: Labware,
                     well_vol: float = 0,
                     start: int = 1,
                     end: int = 8,
                     mode: str = 'reagent',
                     pip_type: str = 'single',
                     msg: str = 'Refill labware volumes',
                     reagent_name: str = 'nameless reagent',
                     is_verbose: bool = True,
                     is_strict_mode: bool = False,
                     threshhold_advancement_vol: float = 1,
                     dead_volume: float = 0):
            """
            Voltracker tracks the volume(s) used in a piece of labware.
            It's conceptually important to understand that in reagent
            mode the volumes tracked are how much volume has been removed from
            the VolTracker, but waste and target is how much has been added
            to it, and how much was there/have been taken out to begin with.
            This will have implications for how the class is initialized.

            :param labware: The labware to track
            :param well_vol: The volume of the liquid in the wells, if using a
            multi-pipette with a well plate, treat the plate like a reservoir,
            i.e. start=1, end=1, well_vol = 8 * vol of each individual well.
            :param pip_type: The pipette type used: 'single' or 'multi',
            when the type is 'multi' volumes are multiplied by 8 to reflect
            the true volumes used by the pipette.
            :param mode: 'reagent', 'target' or 'waste'
            :param start: The starting well
            :param end: The ending well
            :param msg: Message to send to the user when all wells are empty
            (or full when in waste mode)
            :param reagent_name: Name of the reagent tracked by the object
            :param is_verbose: Whether to have VolTracker send ProtocolContext
            messages about its actions or not.
            :param is_strict_mode: If set to True VolTracker will pause
            execution when its tracked wells are depleted (or filled), ask the
            user to replace the labware and reset the volumes. If it's False
            VolTracker will raise an exception if trying to use more volume
            than the VolTracker is set up for. strict_mode also forces the
            user to check if there's enough volume in the active well and
            to manually advance to the next well by calling advance_well()
            :param threshhold_advancement_vol: If using strict mode VolTr.
            will throw an exception if the user advances the well while there
            is more than the threshhold_advancement_vol of volume left in
            the well.
            """
            # Boolean value: True if the well has been filled
            # or has been depleted
            self.labware_wells = {}
            for well in labware.wells()[start-1:end]:
                self.labware_wells[well] = [0, False]
            self.labware_wells_backup = self.labware_wells.copy()
            self.well_vol = well_vol
            self.pip_type = pip_type
            self.mode = mode
            self.start = start
            self.end = end
            self.msg = msg
            self.is_verbose = is_verbose
            # Total vol changed - how much volume has been withdrawn or added
            # to this Voltracker
            self.total_vol_changed = 0
            # If true, then labware should raise an exception when full
            # rather than reset
            self.is_strict_mode = is_strict_mode
            self.reagent_name = reagent_name
            self.dead_volume = dead_volume

            valid_modes = ['reagent', 'waste', 'target']

            # Parameter error checking
            if not (pip_type == 'single' or pip_type == 'multi'):
                raise Exception('Pipette type must be single or multi')

            if mode not in valid_modes:
                msg = "Invalid mode, valid modes are {}"
                msg = msg.format(valid_modes)
                raise Exception(msg)

            if mode != 'reagent' and dead_volume > 0:
                raise Exception(("Setting a dead/min volume only makes sense "
                                 "for reagents"))

        def __str__(self):
            msg = (self.reagent_name + " " + self.mode
                   + " volume change: " + str(self.total_vol_changed),
                   + " well vol: " + str(self.well_vol) + " dead vol: "
                   + str(self.dead_volume))
            msg += "\nChanges in each well:\n"
            for i, well_tracker in enumerate(self.labware_wells.values()):
                msg += "well {}: Volume change: {}\n".format(
                    i+1, well_tracker[0])
            return msg

        @staticmethod
        def flash_lights():
            """
            Flash the lights of the robot to grab the users attention
            """
            nonlocal ctx
            initial_light_state = ctx.rail_lights_on
            opposite_state = not initial_light_state
            for _ in range(5):
                ctx.set_rail_lights(opposite_state)
                ctx.delay(seconds=0.5)
                ctx.set_rail_lights(initial_light_state)
                ctx.delay(seconds=0.5)

        def get_wells(self) -> Sequence:
            return list(self.labware_wells.keys())

        def to_list(self):
            return list(self.labware_wells.items())

        def get_total_initial_vol(self):
            """
            Return the total initial volume of the
            tracker = n_wells * well_vol
            """
            return len(self.labware_wells) * self.well_vol

        def get_total_dead_volume(self):
            """
            Returns the total dead volume of the tracker
            """
            return len(self.labware_wells) * self.dead_volume

        def get_total_remaining_vol(self):
            """
            Returns the total volume remaining in the tracker
            including the dead volume
            """
            return (self.get_total_initial_vol()
                    - self.total_vol_changed)

        def get_active_well_vol_change(self):
            """
            Return the volume either used up (reagents) or added
            (target or trash) in the currently active well
            """
            well = self.get_active_well()
            return self.labware_wells[well][0]

        def get_active_well_remaining_vol(self):
            """
            Returns how much volume is remaing to be used (reagents) or the
            space left to fill the well (waste and targets)
            """
            vol_change = self.get_active_well_vol_change()
            return self.well_vol - vol_change - self.dead_volume

        def get_active_well(self):
            for key in self.labware_wells:
                # Return the first well that is not full
                if self.labware_wells[key][1] is False:
                    return key

        def advance_well(self):
            curr_well = self.get_active_well()
            # Mark the current well as 'used up'
            self.labware_wells[curr_well][1] = True
            pass

        def reset_labware(self):
            VolTracker.flash_lights()
            ctx.pause(self.msg)
            self.labware_wells = self.labware_wells_backup.copy()

        def get_active_well_vol(self):
            well = self.get_active_well()
            return self.labware_wells[well][0]

        def get_current_vol_by_key(self, well_key):
            return self.labware_wells[well_key][0]

        def track(self, vol: float) -> Well:
            """track() will track how much liquid
            was used up per well. If the volume of
            a given well is greater than self.well_vol
            it will remove it from the dictionary and iterate
            to the next well which will act as the active source well.
            :param vol: How much volume to track (per tip), i.e. if it's one
            tip track vol, but if it's multi-pipette, track 8 * vol.

            This implies that VolTracker will treat a column like a well,
            whether it's a plate or a reservoir.
            """
            well = self.get_active_well()
            # Treat plates like reservoirs and add 8 well volumes together
            # Total vol changed keeps track across labware resets, i.e.
            # when the user replaces filled/emptied wells
            vol = vol * 8 if self.pip_type == 'multi' else vol

            # Track the total change in volume of this volume tracker
            self.total_vol_changed += vol

            if (self.labware_wells[well][0] + vol
                    > self.well_vol - self.dead_volume):
                if self.is_strict_mode:
                    msg = ("Tracking a volume of {} uL would {} the "
                           "current well: {} on the {} {} tracker. "
                           "The max well volume is {}, and "
                           "the current vol is {}. The dead volume is {}")
                    mode_msg = ("over-deplete`" if self.mode == "reagent"
                                else "over-fill")
                    msg = msg.format(
                        vol, mode_msg, well, self.reagent_name, self.mode,
                        self.well_vol, self.get_active_well_vol(),
                        self.dead_volume)
                    raise Exception(msg)
                self.labware_wells[well][1] = True
                is_all_used = True

                # Check if wells are completely full (or depleted)
                for w in self.labware_wells:
                    if self.labware_wells[w][1] is False:
                        is_all_used = False

                if is_all_used is True:
                    if self.is_strict_mode is False:
                        self.reset_labware()
                    else:
                        e_msg = ("{}: {} {} wells would be {} by this action "
                                 "this VolTracker is in strict mode, check why"
                                 "manual reset was not performed")

                        fill_status = \
                            ("over-depleted" if self.mode == "reagent" else
                             "over-filled")
                        e_msg = e_msg.format(str(self),
                                             self.reagent,
                                             self.mode, fill_status)
                        raise Exception(e_msg)

                well = self.get_active_well()
                if self.is_verbose:
                    ctx.comment(
                        "\n{} {} tracker switching to well {}\n".format(
                            self.reagent_name, self.mode, well))
                self.labware_wells[well][0] += vol

            if self.is_verbose:
                if self.mode == 'waste':
                    ctx.comment('{}: {} ul of total waste'
                                .format(well,
                                        int(self.labware_wells[well][0])))
                elif self.mode == 'target':
                    ctx.comment('{}: {} ul of reagent added to target well'
                                .format(well,
                                        int(self.labware_wells[well][0])))
                else:
                    ctx.comment('{} uL of liquid used from {}'
                                .format(int(self.labware_wells[well][0]),
                                        well))
            return well

    # reagents

    '''
    Define where all reagents are on the deck using the labware defined above.

    e.g.

    water = reservoir12.wells()[-1]
    waste = reservoir.wells()[0]
    samples = plate.rows()[0][0]
    dnase = tuberack.wells_by_name()['A4']

    '''
    mm_tracker_first_wells = VolTracker(
        labware=mm_source,
        well_vol=mm_well_vol_ul,
        start=mm_start_index,
        end=mm_end_index-1,
        pip_type=mm_pip,
        reagent_name='Bead/binding buffer mastermix (full wells)',
        dead_volume=dead_vol,
        is_verbose=is_verbose_mode
        )

    mm_tracker_last_well = VolTracker(
        labware=mm_source,
        well_vol=total_last_mm_vol,
        start=mm_end_index,
        end=mm_end_index,
        pip_type=mm_pip,
        reagent_name='Bead/binding buffer mastermix (last well)',
        dead_volume=last_dead_vol,
        is_verbose=is_verbose_mode
        )

    # plate, tube rack maps

    '''
    Define any plate or tube maps here.

    e.g.

    plate_wells_by_row = [well for row in plate.rows() for well in row]

    '''

    total_samples = n_samples_rack_1 + n_samples_rack_2 + n_samples_rack_3
    sample_wells = []
    for num_s, rack in zip(
        [n_samples_rack_1, n_samples_rack_2, n_samples_rack_3],
            [sample_rack_1, sample_rack_2, sample_rack_3]):
        for well in rack.wells()[0:num_s]:
            sample_wells.append(well)

    dest_rows = target_plate.rows()

    i = 0
    dest_wells = []
    for row in dest_rows:
        for well in row:
            dest_wells.append(well)
            i += 1
            if i == total_samples:
                break

    # protocol

    '''

    Include header sections as follows for each "section" of your protocol.

    Section can be defined as a step in a bench protocol.

    e.g.

    ctx.comment('\n\nMOVING MASTERMIX TO SAMPLES IN COLUMNS 1-6\n')

    for .... in ...:
        ...
        ...

    ctx.comment('\n\nRUNNING THERMOCYCLER PROFILE\n')

    ...
    ...
    ...


    '''
    # Step 1 to 4 - Distribute samples from tubes to target plate
    """
    Step 1: Aspirate 200 uL of sample mixture from sample tube [Different
    Tips; 5 - 10 uL air gap if possible; Touch tip to side of tube]
    Step 2: Dispense sample into the one corresponding deep-well on 96
    deep-well plate in the order A1, A2... A12, B1, B2... B12, etc.
    [Different Tips; with blow out; Touch tip to side of deep-well]
    Step 3: Discard tip in waste
    Step 4: Repeat for all specified samples in rack for each specified rack
    """
    ctx.comment("\n\nDistributing samples from tubes to target plate wells\n")
    for s, d in zip(sample_wells, dest_wells):
        if not p300.has_tip:
            pick_up(p300)
        p300.aspirate(200, s)
        p300.touch_tip()
        p300.dispense(200, d)
        p300.blow_out()
        p300.touch_tip()
        p300.drop_tip()

    # Mastermix steps (5-11) are performed in protocol 1 - mastermix creation
    # Step 11 to 14 - Distribute binding buffer/bead mastermix
    # 13: Use 300 uL non-filtered tips to mix bead mastermix
    # Mix seven times
    # blowout after mix, touch tips (if tube source)

    # Check if we're using the tuberack or reservoir
    """
    Step 12: All used tips from the prior steps are discarded
    Step 13: The 8-channel pipettor acquires 8x300 uL non-filtered pipette
    tips and then slowly (make speed variable) pipette-mixes the bead master
    mixture 7 times in each well of the 12-well reservoir [same tips; blowout
    used after the last mix in each well; tip touch on side of each well in
    reservoir]
    Step 14: Discard Tips
    """
    pip = p300 if is_mm_pip_single else m300
    n_tips = 8 if is_mm_pip_single else 1

    if pip.has_tip:
        pip.drop_tip()

    pip.pick_up_tip(tiprack_300.wells()[0])

    def calculate_offset(pip, well_vol, is_tube):
        clearance = pip.well_bottom_clearance
        liq_height = (tube_liq_height(
            well_vol, mm_wells.get_active_well_vol)
            if is_tube else 0)
        offset = max(clearance, liq_height - 10)
        return offset

    ctx.comment("\n\nMixing the mastermix\n")
    mm_wells = mm_tracker_first_wells.get_wells()
    # TODO: Have to set a height offset for mixing tubes
    max_mix_vol = min(pip.max_volume*n_tips, mm_wells.well_vol)
    per_tip_mix_vol = max_mix_vol/n_tips
    offset = calculate_offset(pip, mm_wells.well_vol, is_mm_pip_single)
    for i, well in enumerate(mm_wells):
        pip.mix(7, per_tip_mix_vol, well.bottom(offset),
                mastermix_mix_rate_multiplier)
        pip.blow_out(well)
        pip.touch_tip()

    ctx.comment("\n\nMixing the last mastermix well\n")
    last_well_vol = mm_tracker_last_well.well_vol
    offset = calculate_offset(pip, last_well_vol, is_mm_pip_single)
    well = mm_tracker_last_well.get_active_well()
    max_mix_vol = min(pip.max_volume*n_tips, last_well_vol)
    per_tip_mix_vol = max_mix_vol/n_tips
    pip.mix(7, per_tip_mix_vol, well.bottom(offset),
            mastermix_mix_rate_multiplier)
    pip.blow_out(well)
    pip.touch_tip()

    pip.drop_tip()

    """
    Step 15: 8-channel pipette acquires [variable 1-8]x300uL non-filtered
    pipette tips and slowly aspirates 275 uL of master bead mixture from
    12-well reservoir [different tips; variable aspiration speed; tip touch
    on side of well]. For 4-8 samples in a column have the P300 remove
    8-n tips (0-4) and use the M300. For 1-3 samples transfer the mastermix
    with the P300. Make sure to adjust the pickup current for volume
    correction.
    Step 16: 8-Channel pippettor then dispenses 275 uL of master bead mix
    into the first column (column 1 starting with A1, B1, etc...) of the 96
    deep-well plate [different tips; variable dispensing speed; with blowout;
    tip touch on side of wells]
    Step 17: The tips are discarded [different tips]
    Step 18: Steps 15 - 17 are repeated for all designated wells on 96
    deep-well plate
    """

    ctx.comment("\n\nDistributing mastermix to samples on the target plate\n")
    # Calculate the number of sample wells in each column
    used_sample_wells_per_column = []
    n_wells_per_row = 12  # in a 96 well plate 8x12
    n_full_rows = total_samples // n_wells_per_row
    last_row_wells = total_samples % n_wells_per_row
    for i in range(n_wells_per_row):
        wells = n_full_rows + 1 if i < last_row_wells else n_full_rows
        used_sample_wells_per_column.append(wells)

    # Multi-channel pipette mastermix distribution
    if not is_mm_pip_single:
        if p300.has_tip:
            p300.drop_tip()

        # Check if there's enough tips to refill the first col with as many
        # tips as neccesary, otherwise ask user to replace tiprack
        do_refill_first_column = True
        if total_samples > 96-used_sample_wells_per_column[0]:
            ctx.pause(
                "\n\nPlease replace the 300 uL tiprack on deck slot 11\n")
            do_refill_first_column = False

        # Use the single channel pip to remove tips from the 300 uL
        # tiprack from rows not matching any sample wells
        # then when m300 is used to aspirate it doesn't waste mastermix
        # on unused sample wells

        ctx.comment("\n\nRemoving unused tips from tiprack 300\n")
        tiprack_300_columns = tiprack_300.columns()
        offset = 1 if do_refill_first_column else 0
        first_tiprack_col = tiprack_300_columns[0]
        n_tips_first_col_left = used_sample_wells_per_column[0]
        for n_used_wells, col in zip(
                used_sample_wells_per_column, tiprack_300_columns[offset:]):
            wells = col[n_used_wells:]
            for well in wells:
                p300.pick_up_tip(well)
                if do_refill_first_column and n_tips_first_col_left >= 0:
                    p300.drop_tip(first_tiprack_col[n_tips_first_col_left])
                    n_tips_first_col_left -= 1
                else:
                    p300.drop_tip()

        # Transfer mastermix to samples
        m300.reset_tipracks()
        ctx.comment("\n\nDistributing mastermix to samples on target plate\n")
        for well, n_used_wells in zip(
                target_plate.rows()[0], used_sample_wells_per_column):
            m300.pick_up_tip()
            m300.aspirate(
                mm_vol_per_sample, mm_tracker_first_wells.track(
                    mm_vol_per_sample),
                mm_aspiration_flowrate_multiplier)
            m300.air_gap(10)
            m300.dispense(
                mm_vol_per_sample+10, well, mm_dispense_flowrate_multiplier)
            m300.blow_out()
            m300.touch_tip()
            m300.drop_tip()

    else:
        # Distribute mastermix with single channel pipette from master mix
        # tube(s)
        ctx.comment("\n\nDistributing mastermix to samples on target plate\n")
        if p300.has_tip:
            p300.drop_tip()
        for well in dest_wells:
            mm_source_tube = mm_tracker_first_wells.track(0)
            tube_vol = \
                mm_tracker_first_wells.well_vol - \
                mm_tracker_first_wells.get_active_well_vol_change()
            liq_height = tube_liq_height(tube_vol, mm_source_tube)
            asp_loc = max(mm_source_tube.bottom(liq_height-10), 0.1)
            pick_up(p300)
            p300.aspirate(mm_vol_per_sample, asp_loc,
                          mm_aspiration_flowrate_multiplier)
            air_gap_vol = 10
            p300.air_gap(air_gap_vol)
            mm_tracker_first_wells.track(mm_vol_per_sample)
            p300.dispense(mm_vol_per_sample+air_gap_vol, well,
                          mm_dispense_flowrate_multiplier)
            p300.blow_out()
            p300.touch_tip()
            p300.drop_tip()

    ctx.comment("\n\n - Protocol finished! - \n")
