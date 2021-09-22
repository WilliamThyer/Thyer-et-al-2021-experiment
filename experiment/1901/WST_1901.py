from __future__ import division
from psychopy import visual, event, core, gui, parallel, monitors
from psychopy.visual import ShapeStim, TextStim, Circle, Rect
import numpy as np
import random, csv
import eyelinker
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
rad = 1.3
sync = 'sync ' #must have space at end of string!

#Color Setup
def color_convert(color):
    return [round(((n/127.5)-1), 2) for n in color]

color_array_idx = [0,1]
color_table =[[75,208,75],[255,155,55]] # Green, Orange
color_name_table = ['green','orange']

orient_array_idx = [0,1,2,3]
orient_table = [0,45,90,135]

rgb_table = []
for colorx in color_array_idx:
    rgb_table.append(color_convert(color_table[colorx]))

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
    'In this experiment you will be remembering orientations.\n\n'
    'In each block, the target color will switch.\n'
    'Each trial will start with a fixation cross. '
    'Do your best to keep your eyes on it at all times.\n'
    'Then, an array of colored circles with oriented bars will appear.\n'
    'Remember the orientations in target colored items and their locations as best you can.\n'
    'Ignore the non-target colored items. You will not be tested on these.\n'
    'After a short delay, another target item will reappear.\n'
    'If it has the SAME orientation as the item in its location before, press the "S" key.\n'
    'If it has a DIFFERENT orientation, press the "D" key.\n'
    'If you are not sure, just take your best guess.\n\n'
    'You will get breaks in between blocks.\n'
    "We'll start with some practice trials.\n\n"
    'Press the "S" key to start.'
)

#Misc Setup
data_lines_written = 0
experiment_info = {}
experiment_name = "wst_1901"
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
            'SampleOrients',
            'TestOrient',
            'StimColor']

###########
#FUNCTIONS#
###########

def get_experiment_info_dlg(additional_fields_dict=None):
    experiment_info = {
        'Subject Number': '0',
        'Age': '0',
        'Sex':'',
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
    question = {'Practice':'Y','Eyetracking':'Y','EEG':'Y'}

    cont = gui.DlgFromDict(
        question,title=experiment_name, fixed='Y/N',screen=1)
    
    if not cont.OK: 
        question['Practice'] = 'n'
        question['Eyetracking'] = 'n'
        question['EEG'] = 'n'

    return question

def setup_stim():
    #main window
    win = visual.Window(monitor = experiment_monitor, fullscr = True, units='deg')

    #fixation cross
    fix = TextStim(win, pos = [0,0], text='+', color=[-1, -1, -1], height = 1, units='deg')

    # stimulus
    circle = visual.Circle(win, lineColor=None, fillColor=[1,1,1], fillColorSpace='rgb',radius=rad,units='deg')
    orient_bar = visual.Rect(win, lineColor = None, fillColor = [0,0,0], fillColorSpace='rgb',width=.5,height=(rad*2)+.1,units = 'deg')

    white_track = visual.Circle(win, lineColor=None, fillColor = [1,1,1], fillColorSpace='rgb',radius=20, pos = [930,510],units='pix')

    return win, fix, circle, orient_bar, white_track 

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
            text = '', text_color = [-1,-1,-1], text_height = 36, win = None, circle = None, orient_bar = None,
            bg_color = [0,0,0], item_color = None, wait_for_input = True, input_keys = None):

    backgroundRect = visual.Rect(
        win, fillColor=bg_color, units='norm',
        width=20, height=20)

    textObject = visual.TextStim(
        win, text=text, color=text_color, units='pix',
        height=text_height, alignHoriz='center', alignVert='center',
        wrapWidth=round(.8*win.size[0]))
    
    backgroundRect.draw()
    textObject.draw()

    if circle:
        circle.fillColor = item_color
        circle.pos = [0,0]
        orient_bar.pos = [0,0]
        orient_bar.ori = 0
        circle.draw()
        orient_bar.draw()

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
    
    return num_stim, diff_trials

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
    return locs

def make_orient_trial(diff_trials, num_stim, itrial, block_stim_color,block_dist_color):
    #pick orients for stim, size = num of stim for this trial
    stim_orient_idx = np.random.choice(orient_array_idx, size = num_stim[itrial], replace = False)
    dist_orient_idx = np.random.choice(orient_array_idx, size = 5-num_stim[itrial], replace = False)

    #preallocating stim orient matrix
    stim_orient = np.zeros(num_stim[itrial]) 
    dist_orient = np.zeros(5-num_stim[itrial])

    #loop thru for num of stim and choose an orient for each stim
    for istim in range(num_stim[itrial]):
        stim_orient[istim] = orient_table[stim_orient_idx[istim]]

    for istim in range(5-num_stim[itrial]):
        dist_orient[istim] = orient_table[dist_orient_idx[istim]]

    #calls the make_locs function and returns num_stim number of x,y locations
    locs = make_locs(itrial)
    #arbitrarily always test on the first  loc
    test_loc = locs[0]

    #correct response keys and test color
    if diff_trials[itrial] == 0: #same trials
        cresp = same_key
        #make test orient match stim orient (test loc is always first loc which has first orient)
        test_orient = stim_orient[0]
    else: #different trials
        cresp = diff_key
        #any orient that isn't the first one
        other_orient = np.setdiff1d(orient_array_idx,stim_orient_idx[0])
        #choose randomly from temp which is anything that isn't a stim orient
        test_orient_idx = np.random.choice(other_orient,size=1)
        test_orient = orient_table[int(test_orient_idx)]

    trial = {
                'set_size': num_stim[itrial],
                'trial_type': diff_trials[itrial],
                'cresp': cresp,
                'locations': locs,
                'stim_orient': stim_orient,
                'stim_color': block_stim_color,
                'dist_orient': dist_orient,
                'dist_color': block_dist_color, 
                'test_orient': test_orient,
                'test_location': test_loc,
            }
    return trial

def display_orient_trial(trial, trial_idx,itrial, iblock, win, fix,orient_bar,circle,white_track,question,experiment_info,num_prac=None,tracker=None):
    #Recording Check
    if trial_idx == 1 or num_prac == 1:
        text_screen(text='Experimenter, are you recording?', input_keys='y',bg_color=[0,0,.3],win=win)
    #Subject initiates block
    if itrial == 0:
        stim_color_name = color_name_table[trial['stim_color']]
        text_screen(text='In this block, remember the {} items\n\n\n\n\n\n\nPress S to begin'.format(stim_color_name), input_keys = 's', 
                    win=win,circle=circle,orient_bar=orient_bar,item_color = rgb_table[trial['stim_color']])

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
            if trial['stim_color'] == 0:
                parallel.setData(1)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '1')
            else:
                parallel.setData(2)
                if question['Eyetracking'] == 'Y':
                    tracker.send_message(sync + '2')

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

    #END ITI

    #STIM PRESENTATION#
    fix.draw()

    #draw stim
    for istim in range(trial['set_size']):
        orient_bar.ori = trial['stim_orient'][istim]
        orient_bar.pos = trial['locations'][istim]
        circle.pos = trial['locations'][istim]
        circle.fillColor = rgb_table[trial['stim_color']]
        circle.draw()
        orient_bar.draw()

    #draw dist stim
    for istim in range(5-trial['set_size']):
        orient_bar.ori = trial['dist_orient'][istim]
        orient_bar.pos = trial['locations'][trial['set_size']+istim]
        circle.pos = trial['locations'][trial['set_size']+istim]
        circle.fillColor = rgb_table[trial['dist_color']]
        circle.draw()
        orient_bar.draw()
    
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
    fix.draw()
    orient_bar.ori = trial['test_orient']
    orient_bar.pos = trial['test_location']
    circle.pos = trial['test_location']
    circle.fillColor = rgb_table[trial['stim_color']]
    circle.draw()
    orient_bar.draw()
    
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
            'Age':experiment_info['Age'],
            'Sex':experiment_info['Sex'],
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
            'SampleOrients': trial['stim_orient'],
            'TestOrient': trial['test_orient'],
            'StimColor':trial['stim_color']
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
    
    if (int(experiment_info['Subject Number']) % 2) == 0: block_color_idx = np.tile([0,1],int(nblocks/2))
    else: block_color_idx = np.tile([1,0],int(nblocks/2))
    
    data_directory = os.getcwd()

    win, fix, circle, orient_bar, white_track = setup_stim()

    if question['Eyetracking'] == 'Y':
        tracker = eyelinker.EyeLinker(
                win, '1901_' + experiment_info['Subject Number'] + '.edf','LEFT')

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
            num_stim, diff_trials = make_block()
            prac_acc_num = 0
            prac_acc = 0
            num_prac = 0
            block_stim_color = random.choice(block_color_idx)
            block_dist_color = ~block_stim_color

            for itrial in range(12):
                num_prac += 1
                
                trial = make_orient_trial(diff_trials=diff_trials, num_stim=num_stim,itrial=itrial,block_stim_color=block_stim_color,block_dist_color=block_dist_color) #make trial info
                
                if question['Eyetracking'] == 'Y':
                    data = display_orient_trial(
                        trial=trial, trial_idx = trial_idx, itrial=itrial, iblock = 1, win=win, fix=fix,circle=circle,tracker=tracker,orient_bar=orient_bar,
                        white_track=white_track,question=question,experiment_info=experiment_info,num_prac=num_prac)
                else:
                    data = display_orient_trial(
                        trial=trial, trial_idx = trial_idx, itrial=itrial, iblock = 1, win=win, fix=fix, circle=circle, orient_bar=orient_bar,
                        white_track=white_track,question=question,experiment_info=experiment_info,num_prac=num_prac)
                prac_acc_num += data['ACC']
                prac_acc = prac_acc_num/num_prac
                print('Trial: {}, TrialType: {}, SetSize: {}, RESP: {}, CRESP: {}, ACC: {}'.format((itrial+1),data['TrialType'],data['SetSize'],data['RESP'],data['CRESP'],data['ACC']))
            
            prac_cont = text_screen(text = "Accuracy: {}%\n\nKeep going?".format(round(prac_acc,1)*100), input_keys=['n','y'],win=win)

    text_screen(text = "Practice complete!\n\nThe experiment will now begin.\nPress S to continue.", input_keys='s',win=win)

    #run trials for nblocks*ntrials
    for iblock in range(nblocks):
        num_stim, diff_trials = make_block()
        block_acc_num = 0
        block_acc = 0
        block_stim_color = block_color_idx[iblock]
        block_dist_color = ~block_stim_color

        if question['Eyetracking'] == 'Y':
            tracker.calibrate()
        
        for itrial in range(ntrials):
            trial_idx +=1

            ###EXPERIMENT###
            trial = make_orient_trial(diff_trials=diff_trials, num_stim=num_stim, itrial=itrial, block_stim_color=block_stim_color,block_dist_color=block_dist_color) #make trial info

            if question['Eyetracking'] == 'Y':
                data = display_orient_trial(
                        trial=trial,trial_idx=trial_idx, itrial=itrial,iblock=iblock,win=win,fix=fix,orient_bar=orient_bar,circle=circle,white_track=white_track,
                        question=question,experiment_info=experiment_info ,tracker=tracker)
            else:
                data = display_orient_trial(
                    trial=trial,trial_idx=trial_idx,itrial=itrial,iblock=iblock,win=win,fix=fix,orient_bar=orient_bar,circle=circle,white_track=white_track,
                    question=question,experiment_info=experiment_info) 

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
            text_screen(text= "The study is complete!\n\nPlease contact your experimenter.", input_keys= 's',win=win)
            if question['Eyetracking'] == 'Y':
                tracker.set_offline_mode()
                tracker.close_edf()
                tracker.transfer_edf()
                tracker.close_connection()
            win.close()

run_exp()