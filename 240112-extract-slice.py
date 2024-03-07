import os, tifffile, time
import numpy as np
from datetime import datetime
from imageio import get_writer
import argparse
run = 1
starttime = datetime.now()
present_dir = os.getcwd()

# Set up argparse to accept command line arguments
parser = argparse.ArgumentParser(description='Extract slices from 3D reconstructions ')
parser.add_argument('-PATH', type=str, default="", help='Path to read from')
parser.add_argument('-SAVE', type=str, default="", help='Path to save to')
parser.add_argument('-timestart', type=int, default=15000, help='Temporal position in series for start of reconstruction')
parser.add_argument('-timestop', type=int, default=15000, help='Last temporal position')
parser.add_argument('-timestep', type=int, default=1, help='Time interval between reconstructions')
parser.add_argument('-waitforrec', type=int, default=1, help='Wait for reconstruction to finish')
parser.add_argument('-bitrate', type=int, default=32, help='Bitrate of reconstructed images')
parser.add_argument('-extractplane', type=str, default="xz", help='Which plane to extract xz or yz')
parser.add_argument('-regionstart', type=int, default=650, help='Position for start extract')
args = parser.parse_args()

t_start = args.timestart
t_last = args.timestop
t_step = args.timestep

for j in np.arange(t_start,t_last+t_step,t_step):
	PATH = os.path.join(args.PATH,str(j).zfill(5))
	SAVE = args.SAVE

	if args.waitforrec == 1:
		while os.path.isdir(os.path.join(os.path.split(PATH)[0],str(j+t_step).zfill(5))) == False:
			print("Wait for "+str(j).zfill(5)+" to finish")
			time.sleep(5)
		else:
			pass
		  
	# Read and store each image
	file_list = sorted([file for file in os.listdir(PATH) if file.endswith('.tif')])
	images = []
	print("Reading "+str(j).zfill(5))
	for file in file_list:
		file_path = os.path.join(PATH, file)
		if args.bitrate == 32:
			image = tifffile.imread(file_path).astype(np.float32) # reading as 32-bit float
		elif args.bitrate == 16:
			image = tifffile.imread(file_path).astype(np.uint16) # reading as 32-bit float
		elif args.bitrate == 8:
			image = tifffile.imread(file_path).astype(np.uint8) # reading as 32-bit float
		else:
			print("Unrecognized bitrate")
			quit()
		images.append(image)

	# Convert the list of images to a NumPy array
	images_array = np.array(images)

	# Save images
	if not os.path.isdir(SAVE):
		os.mkdir(SAVE)
	if args.extractplane == "xz":
		singleproj = images_array[:, args.regionstart, :]
		with get_writer(os.path.join(SAVE, str(j).zfill(5)+"-XZ.tif")) as writer:
			writer.append_data(singleproj, {'compress': 9})
	elif args.extractplane == "yz":
		singleproj = images_array[:, :, args.regionstart]
		with get_writer(os.path.join(SAVE, str(j).zfill(5)+"-YZ.tif")) as writer:
			writer.append_data(singleproj, {'compress': 9})
	else:
		print("Unrecognized plane")
		quit()



  
