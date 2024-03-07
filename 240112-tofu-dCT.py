import os, re, subprocess, tifffile
import numpy as np
from shutil import copyfile
from datetime import datetime
from imageio import get_writer
from PIL import Image
import argparse
import util
run = 1
starttime = datetime.now()
present_dir = os.getcwd()

# Set up argparse to accept command line arguments
parser = argparse.ArgumentParser(description='Wrapper for dynamic CT reconstruction using ')
parser.add_argument('-PATH', type=str, default="", help='Path for the results')
parser.add_argument('-flatsname', type=str, default='flats', help='Name of flats folder')
parser.add_argument('-darksname', type=str, default='darks', help='Name of darks folder')
parser.add_argument('-tomoname', type=str, default='tomo', help='Name of tomo folder')
parser.add_argument('-SAVE', type=str, default="", help='Path for save reconstructed results')
parser.add_argument('-TEMP', type=str, default="", help='Path for temporary folders')
parser.add_argument('-number', type=int, default=500, help='Number of projections in one 180 scan')
parser.add_argument('-CoR', type=float, default=654.5, help='Center of Rotation')
parser.add_argument('-regionstart', type=int, default=300, help='Vertical position in projection for start of reconstruction')
parser.add_argument('-regionthickness', type=int, default=1, help='How many slices to reconstruct')
parser.add_argument('-timestart', type=int, default=15000, help='Temporal position in series for start of reconstruction')
parser.add_argument('-timestop', type=int, default=15000, help='Last temporal position')
parser.add_argument('-timestep', type=int, default=1, help='Time interval between reconstructions')
parser.add_argument('-phasemode', type=int, default=0, help='Use phase retreival (0 or 1)')
parser.add_argument('-energy', type=float, default=20, help='X-ray energy of monochromatic beam or peak energy of white beam')
parser.add_argument('-distance', type=float, default=0.3, help='Distance between sample and detector')
parser.add_argument('-pixelsize', type=float, default=5.5e-6, help='Effective pixel size')
parser.add_argument('-deltabeta', type=float, default=200, help='Delta over beta ratio')
parser.add_argument('-ringremovalmode', type=int, default=0, help='Use ring removal (0 or 1)')
parser.add_argument('-sigmah', type=int, default=10, help='Horizontal sigma')
parser.add_argument('-sigmav', type=int, default=1, help='Vertical sigma')
parser.add_argument('-cliphistmode', type=int, default=0, help='clip histogram (0 or 1)')
parser.add_argument('-histmin', type=float, default=0, help='min histogram value')
parser.add_argument('-histmax', type=float, default=0, help='max histogram value')
parser.add_argument('-binningmode', type=int, default=0, help='bin projections (0 or 1)')
parser.add_argument('-binvalue', type=int, default=2, help='how much to bin')
args = parser.parse_args()

################## INPUTS ##################

# relavant paths
PATH = args.PATH
flatsname = args.flatsname
darksname = args.darksname
tomoname = args.tomoname
SAVE = args.SAVE
TEMP = args.TEMP
# Remove temporary folder if it exists
if os.path.isdir(TEMP):
	os.system("rm -rf "+TEMP)

# projection values
number = args.number
width, height = util.get_width_height(os.path.join(PATH,tomoname))
CoR = args.CoR
region_start = args.regionstart
region_thick = args.regionthickness
if args.binningmode == 1: # binning considerations
	if (width % args.binvalue == 0) and (height % args.binvalue == 0):
		width = width/args.binvalue
		height = height/args.binvalue
		CoR = CoR/args.binvalue
		region_start = int(np.ceil(region_start/args.binvalue))
		region_thick = int(np.ceil(region_thick/args.binvalue))
	else:
		print("Binning not divisable")
		quit()
else:
	pass

# reconstruction region
if region_start+region_thick > height:
	print("Exceeds spatial region")
	quit()
region_all = np.arange(np.ceil(-height/2),np.ceil(height/2+1),1)
region_some = np.arange(np.ceil(-region_thick/2),np.ceil(region_thick/2+1),1)
if args.ringremovalmode == 0:
	regioncommand = "--region="+str(region_all[region_start])+","+str(region_all[region_start+region_thick])+",1"
elif args.ringremovalmode == 1:
	regioncommand = "--region="+str(region_some[0])+","+str(region_some[len(region_some)-1])+",1"

# dynmaic ct subgrouping
t_start = args.timestart
t_last = args.timestop
t_step = args.timestep

# phase retreival
energy = args.energy
distance = args.distance
pixelsize = args.pixelsize
deltabeta = args.deltabeta
regrate = 0.4339*np.log(deltabeta)+0.0034
if args.phasemode == 0:
  if args.ringremovalmode == 0:
    phasecommand = "--absorptivity"
  elif args.ringremovalmode == 1:
  	phasecommand = "--projection-filter none --absorptivity"
elif args.phasemode == 1:
  if args.ringremovalmode == 0:
    phasecommand = "--disable-projection-crop --delta 1e-6 --energy "+str(energy)+" --propagation-distance "+str(distance)+" --pixel-size "+str(pixelsize)+" --regularization-rate "+str(regrate)
  elif args.ringremovalmode == 1:
    phasecommand = "--projection-filter none --delta 1e-6 --energy "+str(energy)+" --propagation-distance "+str(distance)+" --pixel-size "+str(pixelsize)+" --regularization-rate "+str(regrate)

# ring removal sinogram padding
padwidth, padheight, padx, pady = util.calc_padding(width, number)
sigmah = args.sigmah
sigmav = args.sigmav

# histogramclipping
if args.cliphistmode == 1:
	bitratecommand = '--output-bitdepth 8 --output-minimum " '+str(args.histmin)+'" --output-maximum " '+str(args.histmax)+'"'
else:
	bitratecommand = ''

################## COMMANDS ##################

# STEP 1 - create directory variables and check darks flats and tomo
print("check raw data directory")
check1 = os.path.isdir(os.path.join(PATH,flatsname))
check2 = os.path.isdir(os.path.join(PATH,darksname))
check3 = os.path.isdir(os.path.join(PATH,tomoname))
if [check1,check2,check3] == [True,True,True]:
	pass
else:
	print("Incomplete Data")
	quit()

# STEP 2 - make subfolder
for j in range(t_start,t_last+t_step,t_step):
	if j < (len(os.listdir(os.path.join(PATH,tomoname)))-number+1):
		print('dataset '+str(j))
		# make temporary folder
		os.mkdir(TEMP)
		# if no binning
		if args.binningmode == 0:
			util.make_sub_folder(PATH,tomoname,TEMP,number,j)
			tomocommand = '--projections '+os.path.join(TEMP,"tomosub")+' --flats '+os.path.join(PATH,flatsname)+' --flat-scale 1.0 --darks '+os.path.join(PATH,darksname)+' --dark-scale 1.0'
		# apply binning if necessary
		else:
			util.make_sub_folder_binning(PATH,tomoname,flatsname,darksname,TEMP,flatsname,darksname,number,j,args.binvalue)
			tomocommand = "--projections "+os.path.join(TEMP,"tomosub")+" --flats "+os.path.join(TEMP,"flatsub")+" --flat-scale 1.0 --darks "+os.path.join(TEMP,"darksub")+" --dark-scale 1.0"

		# STEP 3 - Reconstruction
		# calculate rotation angle
		rotationangle = j*(180/number)
		if region_thick == 1:
			outputcommand = os.path.join(SAVE,str(j).zfill(5))
		else:
			outputcommand = os.path.join(SAVE,str(j).zfill(5),"sli")

		# reconstruct without ring removal
		if args.ringremovalmode == 0:
			os.system('tofu reco --overall-angle 180 '+tomocommand+' --output '+outputcommand+' --fix-nan-and-inf '+phasecommand+' --center-position-x '+str(CoR)+' --volume-angle-z '+str(rotationangle)+' --number '+str(number)+' '+regioncommand+' '+bitratecommand+'--output-bytes-per-file 0')
			os.system("rm -rf "+TEMP)

		# reconstruct with ring removal
		elif args.ringremovalmode == 1:
			os.system("tofu preprocess "+tomocommand+" --output "+TEMP+"/proj-step1/proj-%04i.tif --fix-nan-and-inf "+phasecommand+" --output-bytes-per-file 0")
			os.system("tofu sinos --projections "+TEMP+"/proj-step1 --output "+TEMP+"/sinos/sin-%04i.tif --number "+str(number)+" --y "+str(region_start)+" --height "+str(region_thick)+" --y-step 1 --output-bytes-per-file 0")
			os.system('ufo-launch read path='+TEMP+'/sinos ! pad x='+str(padx)+' width='+str(padwidth)+' y='+str(pady)+' height='+str(padheight)+' addressing-mode=mirrored_repeat ! fft dimensions=2 ! filter-stripes horizontal-sigma='+str(sigmah)+' vertical-sigma='+str(sigmav)+' ! ifft dimensions=2 crop-width='+str(padwidth)+' crop-height='+str(padheight)+' ! crop x='+str(padx)+' width='+str(width)+' y='+str(pady)+' height='+str(number)+' ! write filename="'+TEMP+'/sinos-filt/sin-%04i.tif" bytes-per-file=0 tiff-bigtiff=False')
			os.system("tofu sinos --projections "+TEMP+"/sinos-filt --output "+TEMP+"/proj-step2/proj-%04i.tif --number "+str(region_thick)+" --output-bytes-per-file 0")
			os.system('tofu reco --overall-angle 180  --projections '+TEMP+'/proj-step2 --output '+outputcommand+' --center-position-x '+str(CoR)+' --volume-angle-z '+str(rotationangle)+' --number '+str(number)+' '+regioncommand+' '+bitratecommand+'--output-bytes-per-file 0')
			os.system("rm -rf "+TEMP)

	else:
		print("Exceeds time limit")
		quit()

# record log
loglines = ["Relavant paths and names:" \
   ,"Raw data path = "+PATH \
   ,"Name of flats folder = "+flatsname \
   ,"Name of darks folder = "+darksname \
   ,"Name of tomo folder = "+tomoname \
   ,"Reconstruction path = "+SAVE \
   ,"Temporary folder path = "+TEMP \
   ,"" \
   ,"Projection values:" \
   ,"Number of projections = "+str(number) \
   ,"Projection height = "+str(height) \
   ,"Projection width = "+str(width) \
   ,"Center of rotation = "+str(CoR) \
   ,"" \
   ,"Reconstruction region:" \
   ,"First reconstructed slice = "+str(region_start) \
   ,"Total reconstructed slices = "+str(region_thick) \
   ,"First time point = "+str(t_start) \
   ,"Last time point = "+str(t_last) \
   ,"Time interval = "+str(t_step) \
   ,"" \
   ,"Phase retrieval:" \
   ,"Use phase retrieval ="+str(args.phasemode) \
   ,"X-ray energy = "+str(energy) \
   ,"Sample to detector distance = "+str(distance) \
   ,"Effective pixel size = "+str(pixelsize) \
   ,"delta/beta = "+str(deltabeta) \
   ,"" \
   ,"Ring removal:" \
   ,"Use ring removal ="+str(args.ringremovalmode) \
   ,"Horizontal sigma = "+str(sigmah) \
   ,"Vertical sigma = "+str(sigmav)]

# write log file
with open(os.path.join(SAVE,str(j).zfill(5)+".txt"), 'w') as f:
	f.write('\n'.join(loglines))

# print time elapsed
elapsedtime = str(datetime.now()-starttime)
print("Finisehd in "+elapsedtime)
starttime = datetime.now()




