% subs = {'06','07','12','13','14','16','17','20','21','22','23','26','27','28','29','30','31','33','34','35','36','37','39','40','41','42','43','44','45','46','47','48','49','50'};
% subs = {'01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31'};
subs = {'01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20'};
experiment = '1902';
numsubs= length(subs);
destination = ['..\analysis\data_new\',experiment,'\'];
summary_log = fopen('summary.txt','w');
eeglab

for isub = 1:numsubs
        processed_file = ['..\data\',experiment,'\',subs{isub},'\wst',experiment,'_',subs{isub},'_checked.set'];
        EEG = pop_loadset(processed_file);
        
        %Summary
        fprintf(summary_log, ['\nRunning ', EEG.setname, '\n\n']);
        trial_counts = rej_summary(EEG);
        for x = 1:4
            fprintf(summary_log,'Setsize %1.f:%1.f\n',x,trial_counts(x));
        end
        
        %if subject has fewer than 200 in any condition, reject
        if min(trial_counts) < 200
            continue
        end
        
        %Titles
        title = [experiment, '_', EEG.setname(end-1:end)];
        xdata_filename = [destination, title, '_xdata.mat'];
        ydata_filename = [destination, title, '_ydata.mat'];
        idx_filename = [destination, title, '_artifact_idx.mat'];
        behavior_filename = [destination, title, '_behavior.csv'];
        info_filename = [destination, title, '_info.mat'];
        
        % Remove unwanted channels and save xdata
        num_chans = EEG.nbchan;
        all_chans = strings(num_chans,1);
        for chan = 1:num_chans
            all_chans(chan,:) = EEG.chanlocs(chan).labels;
        end
        chan_idx = ismember(all_chans,{'L_GAZE_X','L_GAZE_Y','R_GAZE_X','R_GAZE_Y','StimTrak','HEOG','VEOG','TP9','GAZE_X','GAZE_Y','GAZE-X','GAZE-Y'});

        xdata = EEG.data(~chan_idx,:,:);
        save(xdata_filename, 'xdata');
        
        % Extract and save
        num_trials = size(xdata,3);
        ydata = zeros(num_trials,1);
        for x=1:num_trials
            sorted_labels = sort(EEG.epoch(x).eventbinlabel);
            char_labels = char(sorted_labels(end));
            ydata(x,:) = str2double(char_labels(6));
        end
        
        save(ydata_filename, 'ydata');
        
        % Gather info variables
        chan_labels = {EEG.chanlocs.labels}';
        chan_labels = char(chan_labels(~chan_idx));
        chan_x = [EEG.chanlocs.X];
        chan_y = [EEG.chanlocs.Y];
        chan_z = [EEG.chanlocs.Z];
        chan_x = chan_x(~chan_idx);
        chan_y = chan_y(~chan_idx);
        chan_z = chan_z(~chan_idx);
        sampling_rate = EEG.srate;
        times = EEG.times;
        
        unique_ID_file = ['..\data\',experiment,'\',subs{isub},'\wst',experiment,'_',subs{isub},'.txt'];
        fileID = fopen(unique_ID_file,'r');
        unique_id = fscanf(fileID,'%f');

        save(info_filename,'unique_id','chan_labels','chan_x','chan_y','chan_z','sampling_rate','times');
        
        %Saving artifact index for indexing behavior file
        num_rows = size(EEG.event,2);
        all_trials = zeros(num_rows,1);
        for x = 1:num_rows
            all_trials(:,x) = EEG.event(x).bepoch;
        end
        checked_trials = unique(all_trials);
        
        unchecked_file = ['..\data\',experiment,'\',subs{isub},'\wst',experiment,'_',subs{isub},'_processed.set'];
        EEG = pop_loadset(unchecked_file);
        unchecked_trials = (1:EEG.trials)';
        if unique_id == 124441 & experiment == '1901'
            unchecked_trials = (1:1680)';
        end
        artifact_idx = ismember(unchecked_trials,checked_trials);
        
        save(idx_filename,'artifact_idx')
        
        % Save copy of behavior csv
         behavior_file = ['..\data\',experiment,'\',subs{isub},'\wst',experiment,'_',subs{isub},'.csv'];
         copyfile(behavior_file,behavior_filename);
        
        clear labels num_trials templabel x y checked_trials 
end
"DATA EXTRACTION COMPLETE"