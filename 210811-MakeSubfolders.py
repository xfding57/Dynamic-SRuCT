import os
import numpy as np
from shutil import copyfile
from datetime import datetime
starttime = datetime.now() # get current time
present_dir = os.getcwd() # get present directory
run = 1

### This script relies on directing to the folder before flats, darks, and tomo
#============================ Inputs ===================================================================
data_dir = [2] # which datasets to reconstruct

for sets in range(np.size(data_dir)):
	# imaging parameters
	# determine number of projections for tomo
	if data_dir[i] == 4:
		num_CT = 750
	elif data_dir[i] == 5:
		num_CT = 1000
	elif data_dir[i] == 9:
		num_CT = 750
	elif data_dir[i] == 10:
		num_CT = 1000
	else:
		num_CT = 500
	first = 9000 # starting projection
	last = 10000 # ending projection 
	step = 100 # going up by steps of  

	# data directory format
	# format of folder containing original darks, flats, and tomo
	data_dir_name = 'sc'+str(data_dir[sets])

#=======================================================================================================
	darks_dir = 'darks' # name of darks folder
	flats_dir = 'flats' # name of flats folder
	tomo_dir = 'tomo' # name of tomo folder

	# get names of all files sli directory
	darks_names = [f for f in os.listdir(os.path.join(present_dir,data_dir_name, darks_dir)) if os.path.isfile(os.path.join(os.path.join(present_dir,data_dir_name, darks_dir, f)))]
	flats_names = [f for f in os.listdir(os.path.join(present_dir,data_dir_name, flats_dir)) if os.path.isfile(os.path.join(os.path.join(present_dir,data_dir_name, flats_dir, f)))]
	tomo_names = [f for f in os.listdir(os.path.join(present_dir,data_dir_name, tomo_dir)) if os.path.isfile(os.path.join(os.path.join(present_dir,data_dir_name, tomo_dir, f)))]

	# get the number of images in folder
	darks_count = np.size(darks_names)
	flats_count = np.size(flats_names)
	tomo_count = np.size(tomo_names)

	# Directory for reconstructed images
	data_subdir_name = data_dir_name+'_subs' # format of folder containing the separated datasets 
	os.mkdir(os.path.join(present_dir,data_subdir_name)) # this may cause problems if the subfolder is already made

	for i in range(first, last+step, step):
		limit = (tomo_count-num_CT)+1
		subfoldername = str(i+1).zfill(5) # format of folder containing reorganized darks, flats, and tomo
		if i < limit:
			if run == 1:
				print('> created directory ', subfoldername)
				os.mkdir(os.path.join(present_dir,data_subdir_name, subfoldername))
				os.mkdir(os.path.join(present_dir,data_subdir_name, subfoldername, darks_dir))
				os.mkdir(os.path.join(present_dir,data_subdir_name, subfoldername, flats_dir))
				os.mkdir(os.path.join(present_dir,data_subdir_name, subfoldername, tomo_dir))
				for j in range(darks_count):
					copyfile(os.path.join(present_dir,data_dir_name, darks_dir, darks_names[j]), os.path.join(present_dir,data_subdir_name, subfoldername, darks_dir, darks_names[j]))
				for j in range(flats_count):
					copyfile(os.path.join(present_dir,data_dir_name, flats_dir, flats_names[j]), os.path.join(present_dir,data_subdir_name, subfoldername, flats_dir, flats_names[j]))
				for j in range(num_CT):
					count = str(i+j+1).zfill(5)
					filename = 'im_'+count+'.tif'
					copyfile(os.path.join(present_dir,data_dir_name, tomo_dir, filename), os.path.join(present_dir,data_subdir_name, subfoldername, tomo_dir, filename))

print(datetime.now() - starttime) # show time elapsed


