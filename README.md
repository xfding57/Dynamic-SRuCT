# Dynamic-CT Scripts for Synchrotron Radiation
## Preamble
This repository is to organize the scripts used for performing dynamic CT data using synchrotron radiation (SR). Currently, they are organized for managing the data collected on January 8th, 2020 which were published in https://doi.org/10.1107/S1600577523000826. The scripts can be roughly grouped into three sectionsm pre-processing, reconstruction, and post-processing.

Sections of the script can be ‘commentted out’ with an if statement. For example, the variable ```run = 1``` is at the beginning of each python script. A section that has been ‘commentted out’ will come after ```if run == 0```. Similar usages are present in matlab scripts and imagej macros. 

## 1 - Pre Process
### 1.1 - Unwanted Files
The script '210811-RemoveExcess.py’ will comb through all subdirectories and delete problematic files like ‘Thumbs.db’, ‘reco.params’, or ‘im_00001.tif.rec’.

### 1.2 - Creating Subfolders
'210811-MakeSubfolders.py’ is a way of organizing the large number of projections acquired for dynamic CT. This script needs to be placed in the raw data directory before the darks, flats, and tomo. It copies files from the original directory into a new directory, the raw data is left untouched.

![Make Subfolders](https://github.com/xfding57/XFDing-Dynamic-CT-Codes/blob/main/media/CreateSubfolders.jpg)

The inputs are the name of the raw data directory, the number of projections per CT, the starting projection (i.e., the first time point), the last projection (i.e., the last point), and step between stating and last (i.e., the temporal resolution).

## 2 - Reconstruction
There are many packages available for CT reconstruciton. This secition uses EZ-UFO from the ufo-kit. The installation instruction can be found in https://github.com/sgasilov/ez_ufo. The script '240112-tofu-dCT.py' is a python wrapper for the tofu toolkit for CT reconstruction. Alternatively, CT reconstruction can be done by using the '210811-MakeSubfolders.py'

For '240112-tofu-dCT.py', call to the script
```
python run.py -PATH /path/to/raw/data/ -flatsname /name_of_flats_folder -darksname /name_of_darks_folder -tomoname /name_of_tomo_folder -SAVE /path/to/save/location/ -TEMP /path/to/temporary/folder -number number_of_projections_in_180_scan -CoR center_of_rotation -regionstart first_slice_for_reconstruction -regionthickness how_many_slices_to_reconstruct -timestart first_time_point -timestop last_time_point -timestep time_interval_between_reconstructions
```
There are three additional modes: phase retrieval, ring removal, clip histogram and binning. Phase retrieval uses TIE-Hom algorithm (https://doi.org/10.1046/j.1365-2818.2002.01010.x). To use, add the following to the call.
```
-phasemode 1 -energy x-ray_energy_in_keV -distance sample_to_detector_distance_in_meters -pixelsize effective_pixel_size_in_meters -deltabeta delta_over_beta_ratio_of_material
```
Ring removal algortihm uses fourier wavelet ring removal (https://doi.org/10.1364/OE.17.008567). To use, add the following to the call.
```
-ringremovalmode 1 -sigmah horizontal_sigma_value -sigmav vertical_sigma_value
```
Histogram clipping and binning are to make the reconstructed images easier for analysis. Histogram clipping  takes minimum and maximum range from the 32 bit reconstruction and outputs in 8 or 16 bits. To use, add the following to the call.
```
-cliphistmode 1 -histmin minimum_histogram_value -histmax maximum_histogram_value
```
Binning uses averaging to decrease size of reconstructed volume. To use, add the following to the call.
```
-binningmode 1 -binvalue how_many_pixels_to_average
```

## 3 - Post Process
### 3.1 - Move Files out of ‘sli’
‘210811-MoveFiles.py’ is a script that moves reconstructed images out of the ‘sli’ folder that automatically gets made. This is useful when reconstructed single slices in different locations e.g., the 300th slice. For dynamic CT data, each time point is in a different directory, the 300th slice at different time points are each in a different directory. Rather than moving them out individually, this script copies them into a central directory.

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
