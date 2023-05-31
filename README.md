# Dynamic-CT Scripts for Synchrotron Radiation
## Preamble
This repository is to organize the scripts used for performing dynamic CT data using synchrotron radiation (SR). Currently, they are organized for managing the data collected on January 8th, 2020 which were published in https://doi.org/10.1107/S1600577523000826. The scripts can be roughly grouped into three sectionsm pre-processing, reconstruction, and post-processing.

Sections of the script can be ‘commentted out’ with an if statement. For example, the variable ```run = 1``` is at the beginning of each python script. A section that has been ‘commentted out’ will come after ```if run == 0```. Similar usages are present in matlab scripts and imagej macros. 

## 1 - Pre Process
### 1.1 - Unwanted Files
The script ‘RemoveExcess.py’ will comb through all subdirectories and delete problematic files like ‘Thumbs.db’, ‘reco.params’, or ‘im_00001.tif.rec’.

### 1.2 - Creating Subfolders
‘MakeSubfolders.py’ is a way of organizing the large number of projections acquired for dynamic CT. This script needs to be placed in the raw data directory before the darks, flats, and tomo. It copies files from the original directory into a new directory, the raw data is left untouched.

![Make Subfolders](https://github.com/xfding57/XFDing-Dynamic-CT-Codes/blob/main/media/CreateSubfolders.jpg)

The inputs are the name of the raw data directory, the number of projections per CT, the starting projection (i.e., the first time point), the last projection (i.e., the last point), and step between stating and last (i.e., the temporal resolution).

## 2 - Reconstruction
### 2.1 - UFO
There are many packages available for CT reconstruciton. This secition uses EZ-UFO from the ufo-kit. The installation instruction can be found in https://github.com/sgasilov/ez_ufo. Because there are so many time points across different datasets, ‘RunUFO.py’ can be used for batch processing because once the parameters are known, the script can be run in a loop. ‘RunUFO.py’ needs to be placed in the same directory as the subdirectory created by in section 1.2.

The inputs are the name of the dataset, the size of the reconstructed volume, the rotation center, whether to reconstruct the whole volume, a single slice, or a thick slice, and the number of projections per CT.

### 2.2 - Tomopy
'RunTomopy.py' along with 'f_readstack.py' and 'f_paganin.py' are used to reconstruct using Tomopy. All three scripts should be kept in the same directory as the directories containing 'flats', 'darks', and 'tomo'. This is useful when the BMIT server is not avaiable. To use, create the following environment in anaconda:
```
conda create -n tomopy python=3.6.12
conda activate tomopy
conda install -c conda-forge tomopy=1.9.1
conda install -c conda-forge dxchange=0.1.5
conda install h5py=3.1.0
```
It should be fairly straightforward, for more information read [here](https://tomopy.readthedocs.io/en/latest/api.html). 

## 3 - Post Process
### 3.1 - Move Files out of ‘sli’
‘MoveFiles.py’ is a script that moves reconstructed images out of the ‘sli’ folder that automatically gets made. This is useful when reconstructed single slices in different locations e.g., the 300th slice. For dynamic CT data, each time point is in a different directory, the 300th slice at different time points are each in a different directory. Rather than moving them out individually, this script copies them into a central directory.

### 3.2 - Rotate and Reslice
‘Rotate.imj’ and ‘Reslice.imj’ perform singular tasks. ‘Rotate.imj’ rotates the images in a folder so that they are all the same orientation. ‘Reslice.imj’ saves the orthogonal views of a volume.

Both are ImageJ macros and in the input section, type in the directory that contains the images or the working directory. As they are now, they run as a loop and the input directories change for each run.

### 3.3 -	Polygon Tool for Segmentation
‘UpdatePolygonArray.imj’ is a macro that returns an array of x and y values for whatever polygon is drawn in ImageJ or Fiji. This is useful for keeping track of segmenting.

Open an image and use the polygon tool draw around the ROI. Run ‘UpdatePolygonArray.imj’ and the last line will be an array of x and y values that make of the currently drawn polygon.

![Calculate Area 1](https://github.com/xfding57/XFDing-Dynamic-CT-Codes/blob/main/media/PolygonArea1.PNG)

On a different position either in the stack or at a different time, update the polygon and run the macro again. The last output is a new array of x and y coordinates that correspond to the updated polygon.

![Calculate Area 2](https://github.com/xfding57/XFDing-Dynamic-CT-Codes/blob/main/media/PolygonArea2.PNG)

### 3.4 -	Calculate Stack ROI Area
‘CalcualteThresholdAreas.imj’ is a macro that calculates the thresholded area of each slice in a stack and then saves that information in a text file.
