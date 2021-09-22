%% Read Me

%% Setup
clearvars
eeglab

%% Options

%1801
subjectParentDir = '../data/1801/';
subjectDirectories =  {};  % optionally {} for recursive search
no_eyetracking = {'34','37'}; % list all subjects who have no ET data
do_eog_rejection = {'34','37'}; % no EOG rejection by default, add subs who you want to have rejection based on EOG
do_veog_rejection = {};

%1901
% subjectParentDir = '../data/1901/';
% subjectDirectories =  {};  
% no_eyetracking = {'01','26'}; 
% do_eog_rejection = {'01','10','14'};
% do_veog_rejection = {'26'};

%1902
% subjectParentDir = '../data/1902/';
% subjectDirectories =  {};  
% no_eyetracking = {}; 
% do_eog_rejection = {}; 
% do_veog_rejection = {};

lowboundFilterHz = 0.01;
highboundFilterHz = 30;

rerefType = 'mastoid'; % 'none', 'average', or 'mastoid' 
rerefExcludeChans = {'HEOG', 'VEOG', 'StimTrak'};
customEquationList = '';  % optional

EYEEEGKeyword = 'sync';
startEvent = 21;
endEvent = 21;
eyeRecorded = 'left';  % 'both', 'left', or 'right'

% binlistFile = 'manual_binlist.txt';  % if empty, will create one for you
binlistFile = '';
timelockCodes = [11,12,13,14];  % codes to timelock to
trialStart = -200;
trialEnd = 1250;
baselineStart = -200;
baselineEnd = 0;
rejectionStart = -200;
rejectionEnd = 1250;

eyeMoveThresh = 1;  %deg
distFromScreen = 738; %mm
monitorWidth = 532;  %mm
monitorHeight = 300;  %mm
screenResX = 1920;  %px
screenResY = 1080;  %px

eogThresh = 50; %microv

eegThresh = 85; %microv
eegNoiseThresh = 100; %microv %100 is a good threshold for subjects with high alpha

rejFlatline = true; %remove trials with any flatline data
%% Setup 

% Find all .vhdr files recursively if subjectDirectories is empty
if isempty(subjectDirectories)
    dirs = dir(subjectParentDir);
    for i=1:numel(dirs)
        d = dirs(i).name;
        if strcmp(d, '.') ||  strcmp(d, '..')
            continue
        end
        
        if ~isempty(dir(fullfile(subjectParentDir, d, '*.vhdr')))
            subjectDirectories{end+1} = d; %#ok<SAGROW>
        end
    end
end


log = fopen('log.txt', 'a+t');
fprintf(log, ['Run started: ', datestr(now), '\n\n']);
summary_log = fopen('summary.txt','w');

maximumGazeDist = calcdeg2pix(eyeMoveThresh, distFromScreen, monitorWidth, monitorHeight, screenResX, screenResY);
%% Main loop

for subdir=1:numel(subjectDirectories)
    subject_number = subjectDirectories{subdir};
    subdirPath = fullfile(subjectParentDir, subject_number);
    
    disp(['Running ', subdirPath])
    fprintf(log, ['Running ',subject_number, '\n\n']);
    
    vhdrDir = dir(fullfile(subdirPath, '*.vhdr'));
    
    if numel(vhdrDir) == 0
        warning(['Skipping ', subdirPath, '. No vhdr file found.'])
%         fprintf(log, ['Skipping ', subdirPath, '. No vhdr file found.\n\n']);
        continue
    elseif numel(vhdrDir) > 1
        warning(['Skipping ', subdirPath, '. More than one vhdr file found.'])
%         fprintf(log, ['Skipping ', subdirPath, '. More than one vhdr file found.\n\n']);
        continue
    end
    
    vhdrFilename = vhdrDir(1).name;
    
    ascDir = dir(fullfile(subdirPath, '*.asc'));
    
    if numel(ascDir) == 0
        warning(['Skipping ', subdirPath, '. No asc file found.'])
        fprintf(log, ['Skipping ', subdirPath, '. No vhdr file found.\n\n']);
        continue
    elseif numel(ascDir) > 1
        warning(['Skipping ', subdirPath, '. More than one asc file found.'])
        fprintf(log, ['Skipping ', subdirPath, '. More than one asc file found.\n\n']);
        continue
    end
    
    ascFullFilename = fullfile(subdirPath, ascDir(1).name);

    EEG = pop_loadbv(subdirPath, vhdrFilename);
    
    EEG.setname = vhdrFilename(1:end-5);
    
    if lowboundFilterHz ~= 0 && highboundFilterHz ~= 0
        fprintf(log, sprintf('Bandpass filtering with lowboundFilterHz = %f and highboundFilterHz=%f\n\n', lowboundFilterHz, highboundFilterHz));
        EEG = pop_basicfilter(EEG, 1:EEG.nbchan, 'Boundary', 'boundary', 'Cutoff', [lowboundFilterHz highboundFilterHz], 'Design', 'butter', 'Filter', 'bandpass', 'Order', 2);
    elseif highboundFilterHz ~= 0
        fprintf(log, sprintf('Lowpass filtering with highboundFilterHz=%f\n\n', highboundFilterHz));
        EEG = pop_basicfilter(EEG, 1:EEG.nbchan, 'Boundary', 'boundary', 'Cutoff', highboundFilterHz, 'Design', 'butter', 'Filter', 'lowpass', 'Order', 2);
    elseif lowboundFilterHz ~= 0
        fprintf(log, sprintf('Highpass filtering with lowboundFilterHz = %f\n\n', lowboundFilterHz));
        EEG = pop_basicfilter(EEG, 1:EEG.nbchan, 'Boundary', 'boundary', 'Cutoff', lowboundFilterHz, 'Design', 'butter', 'Filter', 'highpass', 'Order', 2);
    end
    
    if ~strcmp(rerefType, 'none')
        if ~strcmp(customEquationList, '')
            equationList = customEquationList;
        else
            equationList = get_chan_equations(EEG, rerefType, rerefExcludeChans);
        end
        
        fprintf(log, 'Rereferencing with following equation list:\n');
        fprintf(log, strjoin(equationList, '\n'));
        fprintf(log, '\n\n');
        
        EEG = pop_eegchanoperator(EEG, equationList);
    else
        fprintf(log, 'Skipping rereferencing because rerefType = "none"\n\n');
    end
    
    EYEEEGMatFilename = [ascFullFilename(1:end-4) '_eye.mat'];
    
    fprintf(log, sprintf('Parsing asc file: %s\n\n', ascFullFilename));
    parseeyelink(ascFullFilename, EYEEEGMatFilename, EYEEEGKeyword);

    diary 'log.txt'
    if strcmp(eyeRecorded, 'both')
        EEG = pop_importeyetracker(EEG, EYEEEGMatFilename, [startEvent endEvent], [2 3 5 6], {'L_GAZE_X' 'L_GAZE_Y' 'R_GAZE_X' 'R_GAZE_Y'}, 0, 1, 0, 0);
    else
        EEG = pop_importeyetracker(EEG, EYEEEGMatFilename, [startEvent endEvent], [2 3], {'GAZE_X' 'GAZE_Y'}, 0, 1, 0, 0);
    end
    diary off

    EEG = pop_creabasiceventlist(EEG, 'AlphanumericCleaning', 'on', 'BoundaryNumeric', {-99}, 'BoundaryString', {'boundary'}, 'Warning', 'off');
    
    if isempty(binlistFile)
        make_binlist(subdirPath, timelockCodes)
        binlistFile = fullfile(subdirPath, 'binlist.txt');
    end
    
    EEG = pop_binlister(EEG, 'BDF', binlistFile);
    EEG = pop_epochbin(EEG, [trialStart, trialEnd], sprintf('%d %d', baselineStart, baselineEnd));

    % Perform artifact rejection
    allChanNumbers = 1:EEG.nbchan;
    
    %EYETRACKING ARTIFACT REJECTION
    if ~any(strcmp(no_eyetracking,subject_number)) %if the subject has eyetracking
        m = 'doing eye tracking'
        eyetrackingIDX = allChanNumbers(ismember({EEG.chanlocs.labels}, {'L_GAZE_X','L_GAZE_Y','R_GAZE_X','R_GAZE_Y','GAZE-X','GAZE-Y'}));    
        %flags trials where absolute eyetracking value is greater than maximumGazeDist
        EEG = pop_artextval(EEG , 'Channel',  eyetrackingIDX, 'Flag',  1, 'Threshold', [-maximumGazeDist maximumGazeDist], 'Twindow', [rejectionStart rejectionEnd]);
    end   
   
    %EOG ARTIFACT REJECTION
    if any(strcmp(do_eog_rejection,subject_number)) %if you want to do EOG rejection
        eogIDX = allChanNumbers(ismember({EEG.chanlocs.labels}, {'HEOG','VEOG'}));    
        %flags trials where absolute EOG value is greather than eogThresh
        EEG = pop_artextval(EEG , 'Channel',  eogIDX, 'Flag',  2, 'Threshold', [-eogThresh eogThresh], 'Twindow', [rejectionStart rejectionEnd]);
    end
    
    %VEOG ARTIFACT REJECTION (one subject has only VEOG)
    if any(strcmp(do_veog_rejection,subject_number)) %if you want to do EOG rejection
        veogIDX = allChanNumbers(ismember({EEG.chanlocs.labels}, {'VEOG'}));    
        %flags trials where absolute EOG value is greather than eogThresh
        EEG = pop_artextval(EEG , 'Channel',  veogIDX, 'Flag',  2, 'Threshold', [-eogThresh eogThresh], 'Twindow', [rejectionStart rejectionEnd]);
    end
    
    %EEG ARTIFACT REJECTION
    eegIDX = allChanNumbers(~ismember({EEG.chanlocs.labels}, {'TP9', 'L_GAZE_X','L_GAZE_Y','R_GAZE_X','R_GAZE_Y','GAZE-X','GAZE-Y','HEOG','VEOG','StimTrak'}));
    %flags trials where absolute EEG value is greater than eegThresh
    EEG = pop_artextval(EEG , 'Channel',  eegIDX, 'Flag',  3, 'Threshold', [-eegThresh eegThresh], 'Twindow', [rejectionStart rejectionEnd]);
    %flags trials where EEG peak to peak activity within moving window is greater than eegNoiseThresh 
    EEG  = pop_artmwppth(EEG , 'Channel',  eegIDX, 'Flag',  4, 'Threshold', eegNoiseThresh, 'Twindow', [rejectionStart rejectionEnd], 'Windowsize', 200, 'Windowstep', 100); 
    %flags trials where line fit to EEG has a slope above a certain threshold. Good for linear trends.
    EEG = pop_rejtrend(EEG, 0, eegIDX, 725, 75, 0.3, 0, 0);
    
    %syncs rejection flags for ERPLAB and EEGLAB functions
    EEG = pop_syncroartifacts(EEG,'Direction' ,'bidirectional');
    
    %flags trials where any channel has flatlined completely (usually eyetracking)
    if rejFlatline
        if ~any(strcmp(no_eyetracking,subject_number)) %if sub has eyetracking, reject flatline eyetracking
            flatlineIDX = allChanNumbers(~ismember({EEG.chanlocs.labels}, {'StimTrak','HEOG','VEOG'}));
            EEG  = pop_artflatline(EEG , 'Channel', flatlineIDX, 'Duration',  200, 'Flag', 5, 'Threshold', [0 0], 'Twindow', [rejectionStart rejectionEnd]);
        end
        if any(strcmp(no_eyetracking,subject_number)) %if sub does not have eyetracking, don't reject flatline eyetracking
            flatlineIDX = allChanNumbers(~ismember({EEG.chanlocs.labels}, {'StimTrak','HEOG','VEOG','GAZE-X','GAZE-Y'}));
            EEG  = pop_artflatline(EEG , 'Channel', flatlineIDX, 'Duration',  200, 'Flag', 5, 'Threshold', [0 0], 'Twindow', [rejectionStart rejectionEnd]);
        end
    end 
    
    EEG = pop_saveset(EEG, 'filename', fullfile(subdirPath, [vhdrFilename(1:end-5) '_processed.set']));
    
    total = sum(EEG.reject.rejmanual);
    fprintf('Total Trials Rejected: %.0f\n', total);
    fprintf('Percent Trials Rejected: %.2f%%\n', round((total/EEG.trials)*100,1));
       
    summary(EEG,summary_log)
    
end

%% Clean up
eeglab redraw;


fclose(log);

%% Helper Functions

function equationList = get_chan_equations(EEG, rerefType, excludes)
    if ~any(strcmp({'mastoid', 'average'}, rerefType))
        error('rerefType must be "mastoid" or "average"')
    end

    baseEquation = 'ch%d = ch%d - (%s) Label %s';
    
    allLocs = {EEG.chanlocs.labels};
    
    includedChanLabels = allLocs;
    includedChanLabels(ismember(allLocs, excludes)) = [];
    [~, includedChanIndexes] = ismember(includedChanLabels, allLocs);
    
    equationList = {};
  
    if strcmp(rerefType, 'average')
        equationString = sprintf('avgchan(%s)', mat2colon(includedChanIndexes));
    else
        refIdx = find(strcmp({EEG.chanlocs.labels}, 'TP9'));
        equationString = sprintf('.5 * ch%d', refIdx);
    end
    
    for i=includedChanIndexes
        equationList{end + 1} = sprintf(baseEquation, i, i, equationString, allLocs{i}); %#ok<AGROW>
    end
    
end

function make_binlist(subdirPath, timelockCodes)
    % creates a simple binlist  (needed for epoching)

    binfid = fopen(fullfile(subdirPath, 'binlist.txt'), 'w');

    for i=1:numel(timelockCodes)
        fprintf(binfid, sprintf('bin %d\n', i));
        fprintf(binfid, sprintf('%d\n', timelockCodes(i)));
        fprintf(binfid, sprintf('.{%d}\n\n', timelockCodes(i)));
    end
end

function [xPix, yPix] = calcdeg2pix(eyeMoveThresh, distFromScreen, monitorWidth, monitorHeight, screenResX, screenResY)
    % takes a visual angle and returns the (rounded) horizontal and vertical number of
    % pixels from fixation that would be

    pixSize.X = monitorWidth/screenResX; %mm
    pixSize.Y = monitorHeight/screenResY; %mm

    mmfromfix = (2*distFromScreen) * tan(.5 * deg2rad(eyeMoveThresh));

    xPix = round(mmfromfix/pixSize.X);
    yPix = round(mmfromfix/pixSize.Y);
end