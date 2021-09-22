from __future__ import print_function
from __future__ import division

import os
import sys
import time

import pylink as pl
from PsychoPyCustomDisplay import PsychoPyCustomDisplay

import psychopy.event
import psychopy.visual


class EyeLinker(object):
    def __init__(self, window, filename, eye):
        if len(filename) > 12:
            raise ValueError(
                'EDF filename must be at most 12 characters long including the extension.')

        if filename[-4:] != '.edf':
            raise ValueError(
                'Please include the .edf extension in the filename.')

        if eye not in ('LEFT', 'RIGHT', 'BOTH'):
            raise ValueError('eye must be set to LEFT, RIGHT, or BOTH.')

        self.window = window
        self.edf_filename = filename
        self.edf_open = False
        self.eye = eye
        self.resolution = tuple(window.size)
        self.tracker = pl.EyeLink()
        self.genv = PsychoPyCustomDisplay(self.window, self.tracker)

        if all(i >= 0.5 for i in self.window.color):
            self.text_color = (-1, -1, -1)
        else:
            self.text_color = (1, 1, 1)

    def initialize_graphics(self):
        self.set_offline_mode()
        pl.openGraphicsEx(self.genv)

    def initialize_tracker(self):
        if not self.edf_open:
            raise RuntimeError('EDF file must be open before tracker can be initialized.')

        pl.flushGetkeyQueue()
        self.set_offline_mode()

        self.send_command("screen_pixel_coords = 0 0 %d %d" % self.resolution)
        self.send_message("DISPLAY_COORDS 0 0 %d %d" % self.resolution)

        self.tracker.setFileEventFilter(
            "LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON")
        self.tracker.setFileSampleFilter(
            "LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS")
        self.tracker.setLinkEventFilter(
            "LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON")
        self.tracker.setLinkSampleFilter(
            "LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS")

    def send_calibration_settings(self, settings=None):
        defaults = {
            'automatic_calibration_pacing': 1000,
            'background_color': (0, 0, 0),
            'calibration_area_proportion': (0.5, 0.5),
            'calibration_type': 'HV9',
            'elcl_configuration': 'BTABLER',
            'enable_automatic_calibration': 'YES',
            'error_sound': '',
            'foreground_color': (255, 255, 255),
            'good_sound': '',
            'preamble_text': None,
            'pupil_size_diameter': 'NO',
            'saccade_acceleration_threshold': 9500,
            'saccade_motion_threshold': 0.15,
            'saccade_pursuit_fixup': 60,
            'saccade_velocity_threshold': 30,
            'sample_rate': 1000,
            'target_sound': '',
            'validation_area_proportion': (0.5, 0.5),
        }

        if settings is None:
            settings = {}

        settings.update(defaults)

        self.send_command('elcl_select_configuration = %s' % settings['elcl_configuration'])

        pl.setCalibrationColors(settings['foreground_color'], settings['background_color'])
        pl.setCalibrationSounds(
            settings['target_sound'], settings['good_sound'], settings['error_sound'])

        if self.eye in ('LEFT', 'RIGHT'):
            self.send_command('active_eye = %s' % self.eye)

        self.send_command(
            'automatic_calibration_pacing = %i' % settings['automatic_calibration_pacing'])

        if self.eye == 'BOTH':
            self.send_command('binocular_enabled = YES')
        else:
            self.send_command('binocular_enabled = NO')

        self.send_command(
            'calibration_area_proportion %f %f' % settings['calibration_area_proportion'])

        self.send_command('calibration_type = %s' % settings['calibration_type'])
        self.send_command(
            'enable_automatic_calibration = %s' % settings['enable_automatic_calibration'])
        if settings['preamble_text'] is not None:
            self.send_command('add_file_preamble_text %s' % '"' + settings['preamble_text'] + '"')
        self.send_command('pupil_size_diameter = %s' % settings['pupil_size_diameter'])
        self.send_command(
            'saccade_acceleration_threshold = %i' % settings['saccade_acceleration_threshold'])
        self.send_command('saccade_motion_threshold = %i' % settings['saccade_motion_threshold'])
        self.send_command('saccade_pursuit_fixup = %i' % settings['saccade_pursuit_fixup'])
        self.send_command(
            'saccade_velocity_threshold = %i' % settings['saccade_velocity_threshold'])
        self.send_command('sample_rate = %i' % settings['sample_rate'])
        self.send_command(
            'validation_area_proportion %f %f' % settings['validation_area_proportion'])

    def open_edf(self):
        self.tracker.openDataFile(self.edf_filename)
        self.edf_open = True

    def close_edf(self):
        self.tracker.closeDataFile()
        self.edf_open = False

    def transfer_edf(self, newFilename=None):
        if not newFilename:
            newFilename = self.edf_filename

        # Prevents timeouts due to excessive printing
        sys.stdout = open(os.devnull, "w")
        self.tracker.receiveDataFile(self.edf_filename, newFilename)
        sys.stdout = sys.__stdout__
        print(newFilename + ' has been transferred successfully.')

    def setup_tracker(self):
        self.window.flip()
        self.tracker.doTrackerSetup()

    def display_eyetracking_instructions(self):
        self.window.flip()

        psychopy.visual.Circle(
            self.window, units='pix', radius=18, lineColor='black', fillColor='white'
        ).draw()
        psychopy.visual.Circle(
            self.window, units='pix', radius=6, lineColor='black', fillColor='black'
        ).draw()

        psychopy.visual.TextStim(
            self.window, text='Sometimes a target that looks like this will appear.',
            color=self.text_color, units='norm', pos=(0, 0.22), height=0.05
        ).draw()

        psychopy.visual.TextStim(
            self.window, color=self.text_color, units='norm', pos=(0, -0.18), height=0.05,
            text='We use it to calibrate the eye tracker. Stare at it whenever you see it.'
        ).draw()

        psychopy.visual.TextStim(
            self.window, color=self.text_color, units='norm', pos=(0, -0.28), height=0.05,
            text='Press any key to continue.'
        ).draw()

        self.window.flip()
        psychopy.event.waitKeys()
        self.window.flip()

    def calibrate(self, text=None):
        self.window.flip()

        if text is None:
            text = (
                'Experimenter:\n'
                'If you would like to calibrate, press space.\n'
                'To skip calibration, press the escape key.'
            )

        psychopy.visual.TextStim(
            self.window, text=text, pos=(0, 0), height=0.05, units='norm', color=self.text_color
        ).draw()

        self.window.flip()

        keys = psychopy.event.waitKeys(keyList=['escape', 'space'])

        self.window.flip()

        if 'space' in keys:
            self.tracker.doTrackerSetup()

    def drift_correct(self, position=None, setup=1):
        if position is None:
            position = tuple([int(round(i/2)) for i in self.resolution])

        try:
            self.tracker.doDriftCorrect(position[0], position[1], 1, setup)
            self.tracker.applyDriftCorrect()
        except RuntimeError as e:
            print(e.message)

    def record(self, trial_func):
        def wrapped_func():
            self.start_recording()
            trial_func()
            self.stop_recording()
        return wrapped_func

    def start_recording(self):
        self.tracker.startRecording(1, 1, 1, 1)
        time.sleep(.1)  # required

    def stop_recording(self):
        time.sleep(.1)  # required
        self.tracker.stopRecording()

    @property
    def gaze_data(self):
        sample = self.tracker.getNewestSample()

        if self.eye == 'LEFT':
            return sample.getLeftEye().getGaze()
        elif self.eye == 'RIGHT':
            return sample.getRightEye().getGaze()
        else:
            return (sample.getLeftEye().getGaze(), sample.getRightEye().getGaze())

    @property
    def pupil_size(self):
        sample = self.tracker.getNewestSample()

        if self.eye == 'LEFT':
            return sample.getLeftEye().getPupilSize()
        elif self.eye == 'RIGHT':
            return sample.getRightEye().getPupilSize()
        else:
            return (sample.getLeftEye().getPupilSize(), sample.getRightEye().getPupilSize())

    def set_offline_mode(self):
        self.tracker.setOfflineMode()

    def send_command(self, cmd):
        self.tracker.sendCommand(cmd)

    def send_message(self, msg):
        self.tracker.sendMessage(msg)

    def send_status(self, status):
        if len(status) >= 80:
            print('Warning: Status should be less than 80 characters.')

        self.send_command("record_status_message '%s'" % status)

    def close_connection(self):
        self.tracker.close()
        pl.closeGraphics()
