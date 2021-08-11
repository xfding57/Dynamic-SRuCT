import os
import numpy as np
from datetime import datetime
starttime = datetime.now() # get current time
present_dir = os.getcwd() # get present directory
run = 1

### This script relies on directing to the folder before flats, darks, and tomo
#============================ Inputs ===================================================================
# pre processing inputs
data_dir = [2] # which datasets to reconstruct
zsize = 802 # z size of reconstructed volume
rotationcent = 991.5 # rotation center

# script specific inputs
printrun = 0 # [printrun == 0] to run UFO or [printrun == 1] to print out the command if not sure
singleslicerun = 1 # [singleslicerun = 0] to reconstruct volume or [singleslicerun = 1] a single slice
multislicerun = 1 # [multislicerun = 0] to remain just a single slice or [multislicerun = 0] a thickness of slices
sli_thick = 1 # specify pixel thickness for slices to reconstruct starting from sli_num

# script specific defaults
sli_num = [1] # this is 1 by default, needs to be a list
specificslicerun = 0 # this is zero by default

#============================ This section does not matter if [run == 0] ===============================
if singleslicerun == 1: 
	specificslicerun = 1
	sli_num = [500] # specify which slice to reconstruct, needs to be a list
	all_sli_num = np.arange(-zsize/2,(zsize/2)+1,1)

for h in range(np.size(sli_num)):
	if specificslicerun == 1:
		### This part might need some tweaking because python counts from 0 and UFO starts from 1
		if multislicerun == 0:
			sli_a = all_sli_num[sli_num[h]-1]
			sli_b = all_sli_num[sli_num[h]]
		if multislicerun == 1:
			sli_a = all_sli_num[sli_num[h]-1]
			sli_b = all_sli_num[sli_num[h]-1+sli_thick]

#============================ Dataset specific information ============================================
	for i in range(np.size(data_dir)):
		# this is the name containing data, make sure it is correct
		current_data_dir = 'sc'+str(data_dir[i])+'_subs' # this is the name containing data, make sure it is correct
		print('>>> Reading directory: '+current_data_dir)

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

		# information on the current directory
		# get all subdirectories inside current_data_dir
		data_subdir = [f.path for f in os.scandir(os.path.join(present_dir,current_data_dir)) if f.is_dir()]
		# get names of all folder names inside current_data_dir
		data_subdir_names = os.listdir(os.path.join(present_dir,current_data_dir))
		# get the size of current_data_dir
		data_subdir_size = np.size(data_subdir)
		print('>>> Inside '+current_data_dir+' there are '+str(data_subdir_size)+' subdirectories:')
		print(data_subdir_names)

#============================ Subdataset specific information ==========================================
		for j in range(data_subdir_size):
			print('')
			print('>>> starting directory '+current_data_dir+' subdirectory '+str(j+1)+' out of '+str(data_subdir_size))
			# get flat, dark, and tomo directories
			dir_darks = os.path.join(data_subdir[j],'darks')
			dir_flats = os.path.join(data_subdir[j],'flats')
			dir_tomo = os.path.join(data_subdir[j],'tomo')
			print('>>> the darks directory is:')
			print(dir_darks)
			print('>>> the flats directory is:')
			print(dir_flats)
			print('>>> the tomo directory is:')
			print(dir_tomo)

			# get output directories for whole volume 
			if specificslicerun == 0:
				dir_output = os.path.join(present_dir,current_data_dir+'_rec',data_subdir_names[j],'sli')
			# get output directories for single slice 
			if specificslicerun == 1:
				dir_output = os.path.join(present_dir,current_data_dir+'_rec',data_subdir_names[j],'sli_'+str(sli_num[h]))
			print('>>> the output directory is:')
			print(dir_output)
			# get temp directory
			dir_temp = os.path.join(present_dir,'temp_ezufo') # make temp folder same as script, keep the name temp_ezufo, use the same when in ezufo
			print('>>> the temp directory is:')
			print(dir_temp)

#============================ print UFO command or run UFO =============================================
			# directories to draks, flats, tomo, and output
			UFO1 = "tofu reco --darks "+dir_darks+" --flats "+dir_flats+" --projections "+dir_tomo+" --output "+dir_output
			# centre of rotation, number of projections in CT, projections collected over 180 degrees, volume angle
			UFO2 = " --center-position-x "+str(rotationcent)+" --number "+str(num_CT)+" --overall-angle 180 --volume-angle-z 0.00000"
			# phase retrieval
			UFO3 = " --delta 1e-6 --energy 20.0 --propagation-distance 0.5 --pixel-size 5.5e-06 --regularization-rate 2.48"
			# specify region
			if specificslicerun == 0: # for whole volume
				UFO4 = " --region=-"+str(zsize/2)+","+str(zsize/2)+",1"
			if specificslicerun == 1: # for single slice
				UFO4 = " --region="+str(sli_a)+","+str(sli_b)+",1"
			# clip output to 8 bit image
			UFO5 = " --output-bitdepth 8 --output-minimum "+'" -8e-07"'+" --output-maximum "+'" 1e-06"'
			# other
			UFO5 = " --fix-nan-and-inf --absorptivity --disable-projection-crop --output-bytes-per-file 0 --slice-memory-coeff=0.5"

			if printrun == 0:
				os.system(UFO1+UFO2+UFO3+UFO4+UFO5+UFO6)
				print(datetime.now() - starttime) # show time elapsed at the end of each run of UFO
				print('')
			if printrun == 1:
				print("")
				print(UFO1+UFO2+UFO3+UFO4+UFO5+UFO6)
