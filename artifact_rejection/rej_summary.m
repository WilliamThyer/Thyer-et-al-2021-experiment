function [t] = rej_summary(EEG)
    
    ydata = zeros(EEG.trials,1);
    for x=1:EEG.trials
        sorted_labels = sort(EEG.epoch(x).eventbinlabel);
        char_labels = char(sorted_labels(end));
        ydata(x,:) = str2double(char_labels(6));
    end
    
    t = zeros(4,1);
    for x=1:4
        t(x) = sum(ydata==x);
    end
    