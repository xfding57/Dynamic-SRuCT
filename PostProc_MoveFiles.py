import os
import numpy as np
import shutil
from datetime import datetime
starttime = datetime.now() # get current time
present_dir = os.getcwd() # get present directory
run = 1

data_dir = [2] # which datasets to reconstruct

# indicate get directories
for i in range(np.size(data_dir)):
	# format of final containing reconstructed images
	dir_name = 'sc'+str(data_dir[i])+'_sli500' 
	os.mkdir(os.path.join(present_dir,dir_name)) # make directory

	# directory containing reconstructed images
	dir_first = os.path.join(present_dir,'sc'+str(data_dir[i])+'_subs_rec') # get the directory name correct
	dir_first_names = os.listdir(dir_first)

	for j in range(np.size(dir_first_names)):
		print('>>> Inside '+'sc'+str(data_dir[i])+'_rec, Folder '+dir_first_names[j])
		# subdirectory containing reconstructed images
		dir_second = os.path.join(dir_first,dir_first_names[j])
		dir_second_names = os.listdir(os.path.join(dir_second))
		print(dir_second_names)
		print('')
		shutil.copyfile(os.path.join(dir_second,dir_second_names[0]), os.path.join(present_dir,dir_name,'sc'+str(data_dir[i])+'_'+str(dir_first_names[j]).zfill(5)))+'.tif'

print(datetime.now() - starttime) # show time elapsed