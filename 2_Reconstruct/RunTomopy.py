import tomopy
import logging 
logging.basicConfig(level=logging.INFO)
import numpy as np
from PIL import Image
import os
from datetime import datetime
import f_readstack
import f_paganin
starttime = datetime.now() # get current time
present_dir = os.getcwd() # get present directory
run = 1

#============================ Inputs ===================================================================
# Save directory
save_dir = 'sli_'+str(datetime.now()).replace(" ","_").replace(":","-").replace(".","-")
previous_dir = os.path.normpath(present_dir+os.sep+os.pardir)
write_to_dir = os.path.join(previous_dir,save_dir)	
os.mkdir(write_to_dir)

# Read data	
if run == 1:
	print('> Loading darks')
	darks = f_readstack.read_images(os.path.join(present_dir,'darks'))
	print('> Loading flats')
	flats = f_readstack.read_images(os.path.join(present_dir,'flats'))
	print('> Loading tomo')
	tomo = f_readstack.read_images(os.path.join(present_dir,'tomo'))
	# Calculate angles
	tomo_dir_size = np.size(os.listdir(os.path.join(present_dir,'tomo')))
	theta = np.linspace(0, np.pi, num=tomo_dir_size)

# Preprocesses
if run == 1:
	print('> Normalize with flat and dark field corrections')
	tomo = tomopy.normalize(tomo, flats, darks)
	print('> Calculating $ -log(tomo) $ to linearize transmission tomography data')
	tomo = tomopy.minus_log(tomo)
if run == 1:
	print('> Performing phase retrieval')
	tomo = f_paganin.retrieve_phase(tomo, 
		pixel_size=0.00053,
		dist=50,
		energy=20,
		alpha=3e-5,
		pad=True)

# Specify which slices to reconstruct
if run == 1:
	# How many slices to reconstruct
	slice_thickness = 10
	# Where in tomographic projections to reconstruct
	slice_position = 350
	# Reshape loaded stacks
	darks = f_readstack.delete_position(darks, slice_thickness, slice_position)
	flats = f_readstack.delete_position(flats, slice_thickness, slice_position)
	tomo = f_readstack.delete_position(tomo, slice_thickness, slice_position)

# Center of rotation
if run == 1:
	if run == 1:
		# Define the rotation center
		rot_center = 999.25
	if run == 0:
		# Find rotation axis location by finding the offset between the
		# first projection and a mirrored projection 180 degrees apart
		# using phase correlation in Fourier space.
		dir_names = [f for f in os.listdir(os.path.join(present_dir,'tomo')) if os.path.isfile(os.path.join(os.path.join(present_dir,'tomo'),f))]
		dir_size = np.size(dir_names)
		tomo0 = np.array(Image.open(os.path.join(present_dir,'tomo',dir_names[0])))
		tomo180 = np.array(Image.open(os.path.join(present_dir,'tomo',dir_names[dir_size-1])))
		rot_center = tomopy.find_center_pc(tomo0, tomo180, tol=0.5, rotc_guess=999.5)
	print('> Center of rotation:',rot_center)

# Reconstruction, and filters
if run == 1:
	print('> Reconstructing')
	recon = tomopy.recon(tomo, theta,
		center=rot_center,
		sinogram_order=False,
		algorithm='gridrec')
	print('> Apply circulular mask to 3D array')
	recon = tomopy.circ_mask(recon, axis=0, ratio=0.95)

# Write to disk
if run == 1:
	print('> Saving reconstructed images')
	for i in range(np.size(recon[:,0,0])):
		counter = str(i)
		im = Image.fromarray(recon[i,:,:])
		im.save(os.path.join(write_to_dir,'sli_'+counter.zfill(4)+'.tif'))
