# Thyer-et-al-2021-experiment
 
Contains experiment and preprocessing code for Thyer-et-al-2021.

# Experiments

## 1801

Experiment 1. Color change detection task.

## 1901

Experiment 2. Orientation change deteciton task.

## 1902

Experiment 3. Conjunction change detection task.

# Artifact rejection

## eegreject.m

Main script that handles alignment, epoching, other preprocessing, and artifact rejection.

## align_channels.m

Realign eyetracking, EOG, and stimtrak to make channels more visible during inspection of EEG for manual rejection.

## data_from_checked_eeg.m

Pull code from matlab and save it in .mat file for later analysis in Python.

## rej_summary.m

Summarize number of rejected trials and why during automatic rejection.

## summary.m

Save rejection info into rejection summaries.
