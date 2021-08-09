import os
import numpy as np
from datetime import datetime
starttime = datetime.now() # get current time
present_dir = os.getcwd() # get present directory
run = 1

data_dir = [2] # which datasets to reconstruct
zsize = 802 # z size of reconstructed volume

sli_num = 1
specificslicerun = 0

# reconstruct a whole volume [run == 0] or a single slice [run == 1]
if run == 1: 
	specificslicerun = 1
	sli_num = [500]
	all_sli_num = np.arange(-zsize/2,(zsize/2)+1,1)

for h in range(np.size(sli_num)):
	if specificslicerun == 1:
		if run == 1: # for a single slice
			sli_a = all_sli_num[sli_num[h]]
			sli_b = all_sli_num[sli_num[h]+1]
		if run == 0: # for multiple slices
			slicethickness = 100
			sli_a = all_sli_num[sli_num[h]]
			sli_b = all_sli_num[sli_num[h]+slicethickness]

	for i in range(np.size(data_dir)):
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
		print('>>> Inside '+current_data_dir+' there are '+str(data_subdir_size)+' subdirectories')

		for j in range(data_subdir_size):
			print('')
			print('>>> starting directory '+current_data_dir+' subdirectory '+str(j+1)+' out of '+str(data_subdir_size))

			# get input directories
			dir_darks = os.path.join(data_subdir[j],'darks')
			dir_flats = os.path.join(data_subdir[j],'flats')
			dir_tomo = os.path.join(data_subdir[j],'tomo')
			print('>>> the darks directory is '+dir_darks)
			print('>>> the flats directory is '+dir_flats)
			print('>>> the tomo directory is '+dir_tomo)

			# get output directories for whole volume 
			if specificslicerun == 0:
				dir_output = os.path.join(present_dir,current_data_dir+'_rec',data_subdir_names[j],'sli')
			# get output directories for single slice 
			if specificslicerun == 1:
				dir_output = os.path.join(present_dir,current_data_dir+'_rec',data_subdir_names[j],'sli_'+str(sli_num[h]))
			print('>>> the output directory is '+dir_output)

			if run == 1:
				# run command line for whole volume
				if specificslicerun == 0:
					os.system("tofu reco --darks "+dir_darks+" --flats "+dir_flats+" --projections "+dir_tomo+" --output "+dir_output+" --fix-nan-and-inf --overall-angle 180 --disable-projection-crop --delta 1e-6 --energy 20.0 --propagation-distance 0.5 --pixel-size 5.5e-06 --regularization-rate 2.48 --center-position-x 991.5 --number "+str(num_CT)+" --volume-angle-z 0.00000 --region=-401,401,1 --output-bitdepth 8 --output-minimum "+'" -8e-07"'+" --output-maximum "+'" 1e-06"'+" --output-bytes-per-file 0")
				# run command line for single slice
				if specificslicerun == 1:
					os.system("tofu reco --darks "+dir_darks+" --flats "+dir_flats+" --projections "+dir_tomo+" --output "+dir_output+" --fix-nan-and-inf --overall-angle 180 --disable-projection-crop --delta 1e-6 --energy 20.0 --propagation-distance 0.5 --pixel-size 5.5e-06 --regularization-rate 2.48 --center-position-x 991.5 --number "+str(num_CT)+" --volume-angle-z 0.00000 --region="+str(sli_a)+","+str(sli_b)+",1 --output-bitdepth 8 --output-minimum "+'" -8e-07"'+" --output-maximum "+'" 1e-06"'+" --output-bytes-per-file 0")
		
		print(datetime.now() - starttime) # show time elapsed
		print('')
