from __future__ import division
from psychopy import visual, event, core, gui, parallel, monitors
from psychopy.visual import ShapeStim, TextStim, Circle, Rect
import numpy as np
import random, csv
import eyelinker
import changedetection
import os

##################
#EXPERIMENT SETUP#
##################

#Things You May Want to Change
ntrials = 120 #must be a multiple of 4
nblocks = 14
nset = 4
max_per_quad = 2
min_distance = 4
dist_from_fix = 6
same_key = 's'
diff_key = 'd'
stim_size = 2
distractor_size = ((stim_size**2)/3.1415)**(1/2) 
sync = 'sync ' #must have space at end of string!

#Color Setup
def color_convert(color):
    return [round(((n/127.5)-1), 2) for n in color]

ncolors = 7
color_array_idx = [0,1,2,3,4,5,6]
color_table =[
    [255, 0, 0],
    [0, 255, 0],
    [0, 0, 255],
    [255, 255, 0],
    [255, 0, 255],
    [0, 255, 255],
    [255, 128, 0]
]

rgb_table = []
for colorx in color_array_idx:
    rgb_table.append(color_convert(color_table[colorx]))
grey = color_convert([166,166,166])

#Monitor Setup
monitor_name='Experiment Monitor' 
monitor_width=53
monitor_distance=70
monitor_px=[1920, 1080]

experiment_monitor = monitors.Monitor(
            monitor_name, width=monitor_width,
            distance=monitor_distance)
experiment_monitor.setSizePix(monitor_px)

#Instructions
instruct_text =(
    'In this experiment you will be remembering colored squares.\n\n'
    'Each trial will start with a fixation cross. '
    'Do your best to keep your eyes on it at all times.\n'
    'Then, an array of colored squares and grey circles will appear.\n'
    'Remember the colored squares and their locations as best you can.\n'
    'Ignore the grey circles. You will not be tested on these.\n'
    'After a short delay, a colored square will reappear.\n'
    'If it has the SAME color as the previous square in its location, press the "S" key.\n'
    'If it has a DIFFERENT color, press the "D" key.\n'
    'If you are not sure, just take your best guess.\n\n'
    'You will get breaks in between blocks.\n'
    "We'll start with some practice trials.\n\n"
    'Press the "S" key to start.'
)

#Misc Setup
data_lines_written = 0
experiment_info = {}
experiment_name = "WST_18_exp1"
data_keys = ['Subject',
            'Age',
            'Sex',
            'Block',
            'Trial',
            'Timestamp',
            'TrialType',
            'SetSize',
            'RT',
            'CRESP',
            'RESP',
            'ACC',
            'LocationTested',
            'Locations',
            'SampleColors',
            'TestColors']

###########
#FUNCTIONS#
###########

def get_experiment_info_dlg(additional_fields_dict=None):
    experiment_info = {
        'Subject Number': '0',
        'Age': '0',
        'Sex': '',
        'Experimenter Initials': 'WST',
        'Unique Subject Identifier': '000000'
        } 

    if additional_fields_dict is not None:
        experiment_info.update(additional_fields_dict)

    #Modifies experiment_info dict directly
    cont = gui.DlgFromDict(
        experiment_info, title=experiment_name,
        order=['Subject Number',
                'Age',
                'Sex',
                'Experimenter Initials',
                'Unique Subject Identifier'
                ],
        tip={'Unique Subject Identifier': 'From the cronus log'},
        screen = 1
    )

    if not cont.OK: exit()

    return experiment_info

def experiment_questions():
    question = {'Practice':'Y','Eyetracking':'Y','EEG':'Y','Stim Track':'Y'}

    cont = gui.DlgFromDict(
        question,title=experiment_name, fixed='Y/N',screen=1)
    
    if not cont.OK: 
        question['Practice'] = 'n'
        question['Eyetracking'] = 'n'
        question['EEG'] = 'n'
        question['Stim Track'] = 'n'

    return question

def setup_stim():
    #main window
    win = visual.Window(monitor = experiment_monitor, fullscr = True, units='deg')

    #fixation cross
    fix = TextStim(win, pos = [0,0], text='+', color=[-1, -1, -1], height = 32, units='pix')

    #stimulus
    square = visual.Rect(win, lineColor=None, fillColor=[0,0,0], fillColorSpace='rgb', width=stim_size, height=stim_size,units='deg')
    circle = visual.Circle(win, lineColor=None, fillColor=grey, fillColorSpace='rgb', radius=distractor_size,units='deg')
    white_track = visual.Circle(win, lineColor=None, fillColor = [1,1,1], fillColorSpace='rgb',radius=20, pos = [930,510],units='pix')
    black_track = visual.Circle(win, lineColor=None, fillColor = [-1,-1,-1], fillColorSpace='rgb',radius=20, pos = [930,510],units='pix')

    return win, fix, square, circle, white_track, black_track

def open_csv(experiment_info):
    #Create file name for csv
    file_name = experiment_name + '_' + experiment_info['Subject Number'] + '.csv'
    #write the headers for csv
    with open(file_name, 'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data_keys)
        writer.writeheader()
    return file_name

def write_to_csv(data, file_name):
    with open(file_name, 'ab') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = data_keys)
        writer.writerow(data)
    
#Text Screen
#Useful for instructions, break screens, end experiment
def text_screen(
            text = '', text_color = [-1,-1,-1], text_height = 36, win = None,
            bg_color = [0,0,0], wait_for_input = True, input_keys = None):

    backgroundRect = visual.Rect(
        win, fillColor=bg_color, units='norm',
        width=20, height=20)

    textObject = visual.TextStim(
        win, text=text, color=text_color, units='pix',
        height=text_height, alignHoriz='center', alignVert='center',
        wrapWidth=round(.8*win.size[0]))

    backgroundRect.draw()
    textObject.draw()
    win.flip()

    keys = None

    if wait_for_input:
        core.wait(0.2) #prevents accidental keypresses
        keys = event.waitKeys(keyList = input_keys)
        win.flip()

    return keys

#make the parameters for current block trials
def make_block():
    diff_trials = np.tile([0,1], ntrials//2) #0101... for ntrials
    diff_trials = np.random.permutation(diff_trials) #randomized 0s and 1s
    
    num_stim = np.tile([1,2,3,4], ntrials//4) #1,2,3,4,5 for n trials, assumes divisible by 5
    num_stim = np.random.permutation(num_stim) #randomize
    
    num_gstim = 5 - num_stim 

    return num_stim, diff_trials, num_gstim

def _which_quad(loc):
    if loc[0] < 0 and loc[1] < 0:
        return 0
    elif loc[0] >= 0 and loc[1] < 0:
        return 1
    elif loc[0] < 0 and loc[1] >= 0:
        return 2
    else:
        return 3

#check if locs are too close to eachother or the fixation
def _too_close(attempt, locs):
    if np.linalg.norm(np.array(attempt)) < min_distance:
            return True  # Too close to center

    for loc in locs:
        if np.linalg.norm(np.array(attempt) - np.array(loc)) < min_distance:
            return True  # Too close to another square

    return False

#generate locations for stimuli
def make_locs(itrial):
    quad_count = [0,0,0,0]
    locs = []
    counter = 0
    while len(locs) < 5:
        counter += 1
        if counter > 1000:
                raise ValueError('Timeout -- Cannot generate locations with given values.')
        
        attempt = [random.uniform(-dist_from_fix, dist_from_fix) for _ in range(2)]
        
        if _too_close(attempt, locs):
            continue

        if max_per_quad is not None:
            quad = _which_quad(attempt)
            if max(quad_count) > 0:
                if sum(quad_count) >= 4:
                    if quad_count[quad] < max_per_quad:
                        locs.append(attempt)
                        quad_count[quad] += 1
                else:
                    if quad_count[quad] < max_per_quad:
                        if quad_count[quad] < max(quad_count):
                            locs.append(attempt)
                            quad_count[quad] += 1
            else: 
                locs.append(attempt)
                quad_count[quad] += 1
        else:
            locs.append(attempt)
    print(locs)
    return locs

def make_trial(diff_trials, num_stim, num_gstim, itrial):
    #pick colors for stim, it is the size of the num of stim for this trial
    stim_color_idx = np.random.choice(color_array_idx, size = num_stim[itrial], replace = False)
    
    #preallocating stim color matrix
    stim_color = np.zeros(shape = [num_stim[itrial],3]) 

    #loop thru for num of stim and choose a color for each stim
    for istim in range(num_stim[itrial]):
        stim_color[istim] = rgb_table[stim_color_idx[istim]]

    #calls the make_locs function and returns num_stim number of x,y locations
    locs = make_locs(itrial)
    #arbitrarily always test on the first  loc
    test_loc = locs[0]

    #correct response keys and test color
    if diff_trials[itrial] == 0: #same trials
        cresp = same_key
        #make stim test color match stim color (test loc is always first loc which has first color)
        test_color = stim_color[0]
    else: #different trials
        cresp = diff_key
        #any color that isn't the first one
        other_color = np.setdiff1d(color_array_idx,stim_color_idx[1:])
        #choose randomly from temp which is anything that isn't a stim color
        test_color_idx = np.random.choice(other_color,size=1)
        test_color = rgb_table[int(test_color_idx)]

    trial = {
                'set_size': num_stim[itrial],
                'trial_type': diff_trials[itrial],
                'cresp': cresp,
                'locations': locs,
                'stim_colors': stim_color,
                'test_color': test_color,
                'test_location': test_loc,
            }
    return trial

def display_trial(trial, trial_idx,itrial, iblock, win, fix, square,circle,white_track,black_track,question,experiment_info,num_prac=None,tracker=None):
    #Recording Check
    if trial_idx == 1 or num_prac == 1:
        text_screen(text='Experimenter, are you recording?', input_keys='y',bg_color=[0,0,.3],win=win)
    
    #Subject initiates block
    if itrial == 0:
        text_screen(text='Press S to begin block', input_keys = 's', win=win)

    trial_code = 101 + itrial
    block_code = 231 + iblock       

    if question['Eyetracking'] == 'Y':
        if num_prac is None:
            tracker.send_message(str(trial_code)) #send eyetraker trial num
            tracker.send_message(str(block_code)) #send eyetracker block num
        else:
            tracker.send_message('Practice')
        status = 'Trial Type:%s, Block: %d, Trial: %d' % (trial['trial_type'], iblock+1, itrial+1)
        tracker.send_status(status)
        tracker.start_recording()    

    if question['EEG']=='Y':
        if num_prac is None:
            parallel.setData(1)
            if question['Eyetracking'] == 'Y':
                tracker.send_message(sync + '1')

    if question['Stim Track'] == 'Y':
        black_track.draw()    
    fix.draw()
    win.flip()

    #BEGIN ITI# also experimenter input for pause/calibrate/escape
    iti = (random.randrange(600,1000,20))/1000
    resp = []
    resp = event.waitKeys(maxWait=iti, keyList=['escape','o','b','m'])
    if resp == ['escape']:
        win.close()
        if tracker:
            tracker.stop_recording()
            tracker.set_offline_mode()
            tracker.close_edf()
            tracker.transfer_edf()
            tracker.close_connection()
        exit()
    if resp == ['o']:
        if tracker:
            tracker.calibrate()
        fix.draw()
        win.flip()
        core.wait(1.5)
    if resp == ['b']:
        TextStim(win=win,text='Blink',pos = [0,1], color = [1,-1,-1]).draw()
        fix.draw()
        win.flip()
        core.wait(1)
        fix.draw()
        win.flip()
        core.wait(1)
    if resp == ['m']:
        TextStim(win=win,text='Eye Movement',pos = [0,1], color = [1,-1,-1]).draw()
        fix.draw()
        win.flip()
        core.wait(1)
        fix.draw()
        win.flip()
        core.wait(1)
    if question['Stim Track'] == 'Y':
        black_track.draw()

    #END ITI

    #STIM PRESENTATION#
    fix.draw()

    #draw stim
    for istim in range(trial['set_size']):
        square.fillColor = trial['stim_colors'][istim]
        square.pos = trial['locations'][istim]
        square.draw()

    #draw grey stim
    for istim in range(5-trial['set_size']):
        circle.pos = trial['locations'][trial['set_size']+istim]
        circle.draw()
    
    if question['Stim Track'] == 'Y':
        white_track.draw()

    if question['Eyetracking'] == 'Y':
        tracker.send_message('ArrayOnset')

    if question['EEG']=='Y':
        if num_prac is None:
            if trial['set_size'] == 1:
                parallel.setData(11)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync+'11')
            if trial['set_size'] == 2:
                parallel.setData(12)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync+'12')
            if trial['set_size'] == 3:
                parallel.setData(13)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync+'13')
            if trial['set_size'] == 4:
                parallel.setData(14)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync+'14')

    #show stim
    win.flip()
    core.wait(.25) #amount of time for stim presentation
    #END STIM PRESENTATION#

    #BEGIN DELAY PERIOD#
    fix.draw()
    if question['Stim Track'] == 'Y':
        white_track.draw()
    if question['EEG']=='Y':
        if num_prac is None:
            parallel.setData(21)
            if question['Eyetracking'] == 'Y':
                tracker.send_message(sync + '21')
    win.flip()
    core.wait(1)

    #END DELAY PERIOD#

    #BEGIN PROBE#
    square.fillColor = trial['test_color']
    square.pos = trial['test_location']
    square.draw()
    fix.draw()
    
    if question['Stim Track'] == 'Y':
        black_track.draw()
    
    if question['EEG']=='Y':
        if num_prac is None:
            if trial['trial_type'] == 0:
                parallel.setData(31)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '31')
            else: 
                parallel.setData(32)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '32')

    win.flip()

    #get response
    rt_timer = core.MonotonicClock() #start timer

    resp = event.waitKeys(keyList=[same_key,diff_key], timeStamped=rt_timer)

    keyresp = resp[0][0] #log response 

    acc = 1 if keyresp == trial['cresp'] else 0 #record accuracy
    
    if question['EEG']=='Y':
        if num_prac is None:
            if acc == 1:
                parallel.setData(41)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '41')
            else:
                parallel.setData(42)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '42')

    rt = resp[0][1]*1000  # key and rt in milliseconds

    data = {
            'Subject': experiment_info['Subject Number'],
            'Age': experiment_info['Age'],
            'Sex': experiment_info['Sex'],
            'Block': iblock + 1,
            'Trial': itrial + 1,
            'Timestamp': core.getAbsTime(),
            'TrialType': trial['trial_type'],
            'SetSize': trial['set_size'],
            'RT': rt,
            'CRESP': trial['cresp'],
            'RESP': keyresp,
            'ACC': acc,
            'LocationTested': trial['test_location'],
            'Locations': trial['locations'],
            'SampleColors': trial['stim_colors'],
            'TestColors': trial['test_color'],
        }

    if question['Eyetracking'] == 'Y':
                tracker.stop_recording()
    return data

################
#Run Experiment#
################
def run_exp(): 
    #run experiment dialog boxes
    experiment_info = get_experiment_info_dlg()
    question = experiment_questions()
    
    data_directory = os.getcwd()

    change_detection_K = changedetection.Ktask(number_of_trials_per_block=1,
            number_of_blocks=2, experiment_name='KTask_'+experiment_name,
            data_fields=changedetection.data_fields, set_sizes=[6],
            monitor_distance=monitor_distance, data_directory=data_directory)

    #change_detection_K.run()

    win, fix, square, circle, white_track, black_track = setup_stim()

    if question['Eyetracking'] == 'Y':
        tracker = eyelinker.EyeLinker(
                win, 'CDET' + experiment_info['Subject Number'] + '.edf','LEFT')

    if question['Eyetracking'] == 'Y':
        #Eyetracking    
        tracker.initialize_graphics()
        tracker.open_edf()
        tracker.initialize_tracker()
        tracker.send_calibration_settings()

    #open csv to write data to
    file_name  = open_csv(experiment_info=experiment_info)

    #instructions
    text_screen(text = instruct_text, input_keys='s', win = win)

    #initialization
    prac_acc_num = 0
    prac_acc = 0
    num_prac = 0
    prac_cont = ['y']
    trial_idx = 0 #trial number tracker initialization
    total_block_acc = 0
    total_block_acc_num = 0

    if question['EEG']=='Y':
        print(parallel.setPortAddress(53328))

    #Practice Trials
    if question['Practice'] == 'Y':
        if question['Eyetracking'] == 'Y':
            tracker.calibrate()

        while prac_cont == ['y']:
            num_stim, diff_trials, num_gstim = make_block()
            prac_acc_num = 0
            prac_acc = 0
            num_prac = 0
            for itrial in range(12):
                num_prac += 1
                
                trial = make_trial(diff_trials=diff_trials, num_stim=num_stim,num_gstim=num_gstim,itrial=itrial) #make trial info
                
                if question['Eyetracking'] == 'Y':
                    data = display_trial(
                        trial=trial, trial_idx = trial_idx, itrial=itrial, iblock = 1, win=win, fix=fix,square=square,circle=circle,tracker=tracker,
                        white_track=white_track,black_track=black_track,question=question,experiment_info=experiment_info,num_prac=num_prac)
                else:
                    data = display_trial(
                        trial=trial, trial_idx = trial_idx, itrial=itrial, iblock = 1, win=win, fix=fix,square=square, circle=circle,
                        white_track=white_track,black_track=black_track,question=question,experiment_info=experiment_info,num_prac=num_prac)
                prac_acc_num += data['ACC']
                prac_acc = prac_acc_num/num_prac
                print('Trial: {}, TrialType: {}, SetSize: {}, RESP: {}, CRESP: {}, ACC: {}'.format((itrial+1),data['TrialType'],data['SetSize'],data['RESP'],data['CRESP'],data['ACC']))
            
            prac_cont = text_screen(text = "Accuracy: {}%\n\nKeep going?".format(round(prac_acc,1)*100), input_keys=['n','y'],win=win)

    text_screen(text = "Practice complete!\n\nThe experiment will now begin.\nPress S to continue.", input_keys='s',win=win)

    #run trials for nblocks*ntrials
    for iblock in range(nblocks):
        num_stim, diff_trials, num_gstim = make_block()
        block_acc_num = 0
        block_acc = 0

        if question['Eyetracking'] == 'Y':
            tracker.calibrate()
        
        for itrial in range(ntrials):
            trial_idx +=1

            ###EXPERIMENT###
            trial = make_trial(diff_trials=diff_trials, num_stim=num_stim, num_gstim=num_gstim,itrial=itrial) #make trial info

            if question['Eyetracking'] == 'Y':
                data = display_trial(
                        trial=trial,trial_idx=trial_idx, itrial=itrial,iblock=iblock,win=win,fix=fix,square=square,white_track=white_track,
                        black_track=black_track,question=question,experiment_info=experiment_info ,tracker=tracker, circle=circle)
            else:
                data = display_trial(
                    trial=trial,trial_idx=trial_idx,itrial=itrial,iblock=iblock,win=win,fix=fix,square=square,white_track=white_track,
                    black_track=black_track,question=question,experiment_info=experiment_info,circle=circle) 

            write_to_csv(data = data, file_name=file_name) #write individual trial info to csv

            print('Block: {}, Trial: {}, TrialType: {}, SetSize: {}, ACC: {}, CRESP: {}, RESP: {}'.format(data['Block'],data['Trial'],data['TrialType'],data['SetSize'],data['ACC'],data['CRESP'],data['RESP']))

            #vars for displaying current block acc
            block_acc_num += data['ACC']
            block_acc = block_acc_num/ntrials

        total_block_acc_num += block_acc
        total_block_acc = total_block_acc_num/(iblock+1)

        text_screen(
            text="You've completed block {}/{}\n\nBlock Accuracy: {}%\nTotal Accuracy: {}%\n\nPress S when you are ready to continue.".format(iblock+1,nblocks,int(block_acc*100),int(total_block_acc*100)),
            input_keys="s",bg_color=[0,0,.3],win=win)

        if iblock+1 == nblocks: #end experiment
            if question['EEG'] == 'Y':
                parallel.setData(4)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '4')
            if question['Eyetracking'] == 'Y':
                tracker.set_offline_mode()
                tracker.close_edf()
                tracker.transfer_edf()
                tracker.close_connection()
            text_screen(text= "The study is complete!\n\nPlease contact your experimenter.", input_keys= 'escape',win=win)
            win.close()

run_exp()