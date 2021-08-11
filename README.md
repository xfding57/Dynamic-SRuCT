# XFDing-Dynamic-CT-Codes

## Preamble
Hello everyone, I made this repository because it’s the proper way of managing codes/scripts/functions/programs and whatnot. Often there are many edits to scripts, and this is a good way of keeping track of those edits. The scripts that are included here were written simply to help me manage dynamic CT data and as they are now, are written specifically for managing the data collected on January 8th, 2020. The scripts can be roughly grouped into three sections.

Python scripts end in .py, MATLAB scripts end in .m ImageJ macros end in .txt or .ijm if written in Fiji. I like to name functions that are called to with a ‘f_’ in front of the name e.g. ‘f_function.py’. This is because I wouldn’t edit a called function whereas most of scripts I would edit ‘on the spot’.

I like to ‘comment out’ a section of my script with an if statement. For example, I will always have a variable ‘run = 1’ at the beginning of my script. A section that I ‘comment out’ will come after ‘if run == 0’.

## 1 - Pre Process
### 1.1 - Unwanted Files
The script ‘RemoveExcess.py’ will comb through all subdirectories and delete problematic files like ‘Thumbs.db’, ‘reco.params’, or ‘im_00001.tif.rec’.
### 1.2 - Creating Subfolders
‘MakeSubfolders.py’ is a way of organizing the large number of projections acquired for dynamic CT. This script needs to be placed in the raw data directory before the darks, flats, and tomo. It copies files from the original directory into a new directory, the raw data is left untouched.
!(XFDing-Dynamic-CT-Codes/media/CreateSubfolders.PNG)
The inputs are the name of the raw data directory, the number of projections per CT, the starting projection (i.e., the first time point), the last projection (i.e., the last point), and step between stating and last (i.e., the temporal resolution).

## 2 - Reconstruction
### 2.1 - UFO
### 2.2 - Tomopy

## 3 - Post Process
### 3.1 - Move Files out of ‘sli’
### 3.2 - Rotate and Reslice
### 3.3 -	Polygon Tool for Segmentation
### 3.4 -	Calculate Stack ROI Area
