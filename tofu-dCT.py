import os, sys, argparse, utils, tifffile
import numpy as np
from imageio import get_writer
from datetime import datetime
run = 1
starttime = datetime.now()

# Set up argparse to accept command line arguments
parser = argparse.ArgumentParser(description='Wrapper for dynamic CT reconstruction using ')
parser.add_argument('-flatsdarks', type=str, default='', help='path to folder with flats and darks')
parser.add_argument('-tomo', type=str, default='', help='path to tomo')
parser.add_argument('-SAVE', type=str, default="", help='Path for save reconstructed results')
parser.add_argument('-TEMP', type=str, default="", help='Path for temporary folders')
parser.add_argument('-number', type=int, default=1000, help='Number of projections in one 180 scan')
parser.add_argument('-reduce', type=utils.parselist, default='1,250', help='reduce raw data projection number')
parser.add_argument('-timeseries', type=utils.parselist, default='0,7000,250', help='time start, time stop, time step')
parser.add_argument('-CoR', type=float, default=2221, help='Center of Rotation')
parser.add_argument('-findCoR', action="store_true", help='find CoR by correlating first and last')
parser.add_argument('-phaseparams', type=utils.parselist, default='1,30,0.45,5,2000', help='(0 or 1),energy[keV],distance[m],pixelsize[um],deltabeta')
parser.add_argument('-ringremovalparams', type=utils.parselist, default='1,3,1', help='(0 or 1),horizontal-sigma,vertical-sigma')
parser.add_argument('-brightspotparams', type=utils.parselist, default='1,2000,5', help='(0 or 1),thresholding,gaussian-sigma')
parser.add_argument('-cliphist', type=utils.parselist, default='8,-0.0002,-0.0001', help='output-bitdepth,output-minimum,output-maximum')
parser.add_argument('-zroiparams', type=utils.parselist, default='1,300,200,20', help='(0 or 1),start,height,step')
parser.add_argument('-cropparams', type=utils.parselist, default='1,1232, 656, 2000, 2000', help='(0 or 1),x,y,width,length')
parser.add_argument('-rotate', type=utils.parselist, default='0,0,0', help='angle in around z, x, y')
args = parser.parse_args()

################## INPUTS ##################

# relavant paths
flatsname = os.path.join(args.flatsdarks,'flats')
darksname = os.path.join(args.flatsdarks,'darks')
tomoname = args.tomo
TEMP = args.TEMP
SAVE = args.SAVE

# check raw data is complete
print(">>> Checking raw data directory")
check1 = os.path.isdir(flatsname)
check2 = os.path.isdir(darksname)
check3 = os.path.isdir(tomoname)
if [check1,check2,check3] == [True,True,True]:
	pass
else:
	print(">>> Incomplete Data")
	sys.exit() 

# check size of input tomo directory and one projection
# get size of input tomo directory and one projection
files = sorted([f for f in os.listdir(tomoname) if os.path.isfile(os.path.join(tomoname, f))])
with tifffile.TiffFile(os.path.join(tomoname, files[0])) as tif:
    is_bigtiff = tif.is_bigtiff
    pages_per_file = len(tif.pages)
    height, width = tif.pages[0].shape[0], tif.pages[0].shape[1]

is_multiview = (not is_bigtiff) and (pages_per_file > 1)

if is_bigtiff or is_multiview:
    file_page_counts = [(f, len(tifffile.TiffFile(os.path.join(tomoname, f)).pages)) for f in files]
else:
    file_page_counts = None

# center of rotation
number = args.number
CoR = args.CoR

# z region of interest
if args.zroiparams[0] == 1:
	region_start = args.zroiparams[1]
	region_thick = args.zroiparams[2]
	region_step = args.zroiparams[3]
	if region_start+region_thick > height:
		print(">>> Exceeds spatial region")
		sys.exit() 
else:
	region_start = 0
	region_thick = height
	region_step = 1
region_all = np.arange(np.ceil(-height/2),np.ceil(height/2+1),1)
region_some = np.arange(np.ceil(-region_thick/2),np.ceil(region_thick/2+1),1)
regioncommand = "--region="+str(region_all[region_start])+","+str(region_all[region_start+region_thick])+","+str(region_step)

# x and y region of interest
if args.cropparams[0] == 0:
	regioncommand = ''+regioncommand
elif args.cropparams[0] == 1:
	xstart = -np.floor(width/2)+args.cropparams[1]
	xstop = -np.floor(width/2)+args.cropparams[1]+args.cropparams[3]
	ystart = -np.floor(width/2)+args.cropparams[2]
	ystop = -np.floor(width/2)+args.cropparams[2]+args.cropparams[4]
	regioncommand = '--x-region='+str(xstart)+','+str(xstop)+',1 --y-region='+str(ystart)+','+str(ystop)+',1 '+regioncommand
else:
	print(">>> Non-boolean argument for cropping region of interest")
	sys.exit() 

# dynmaic ct subgrouping
t_start = args.timeseries[0]
t_last = args.timeseries[1]
t_step = args.timeseries[2]

# phase retreival
energy = args.phaseparams[1] # in kev
distance = args.phaseparams[2] # in m
pixelsize = args.phaseparams[3] # in microns
deltabeta = args.phaseparams[4]
regrate = 0.4339*np.log(deltabeta)+0.0034

# ring removal sinogram padding
sigmah = args.ringremovalparams[1]
sigmav = args.ringremovalparams[2]

# bright spot removal
spotthresh = args.brightspotparams[1]
gausssigma = args.brightspotparams[2]

# histogramclipping
if args.cliphist[0] == 8:
	bitratecommand = '--output-bitdepth 8 --output-minimum='+str(args.cliphist[1])+' --output-maximum='+str(args.cliphist[2])
elif args.cliphist[0] == 16:
	bitratecommand = '--output-bitdepth 16 --output-minimum='+str(args.cliphist[1])+' --output-maximum='+str(args.cliphist[2])
elif args.cliphist[0] == 32:
	bitratecommand = ''
else:
	print(">>> not available bit depth")
	sys.exit() 

# combine below so that in the try loop, it will delete an exsiting folder before making new folders also save the log to the rec
if run == 1:
	# Remove temporary folder if it exists
	if os.path.isdir(TEMP):
		print(">>> Deleting existing temporary folder")
		os.system("rm -r "+TEMP)
	else:
		pass

	# check write permission to temp and rec
	for labelname, pathdirectory in [("Save path", SAVE), ("Temp path", TEMP)]:
		try:
			os.makedirs(pathdirectory, exist_ok=True)
		except PermissionError:
			print(f"ERROR: No write permission to create {labelname} directory: {pathdirectory}")
			sys.exit(1)
		except Exception as e:
			print(f"ERROR: Could not create {labelname} directory: {pathdirectory}\n  {e}")
			sys.exit(1)

	# record log
	loglines = ["Relavant paths and names:" \
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
	   ,"Time resolved region:" \
	   ,"First time point = "+str(t_start) \
	   ,"Last time point = "+str(t_last) \
	   ,"Time interval = "+str(t_step) \
	   ,"" \
	   ,"Phase retrieval:" \
	   ,"Use phase retrieval ="+str(args.phaseparams[0]) \
	   ,"X-ray energy = "+str(energy) \
	   ,"Sample to detector distance = "+str(distance) \
	   ,"Effective pixel size = "+str(pixelsize) \
	   ,"delta/beta = "+str(deltabeta) \
	   ,"" \
	   ,"Ring removal:" \
	   ,"Use ring removal ="+str(args.ringremovalparams[0]) \
	   ,"Horizontal sigma = "+str(sigmah) \
	   ,"Vertical sigma = "+str(sigmav)
	   ,"" \
	   ,"Bright spot removal:" \
	   ,"Use ring removal ="+str(args.brightspotparams[0]) \
	   ,"Horizontal sigma = "+str(spotthresh) \
	   ,"Vertical sigma = "+str(gausssigma)
	   ,""\
	   ,"Histogram parameters = "+",".join(str(x) for x in args.cliphist)\
	   ,"Z ROI parameters = "+",".join(str(x) for x in args.zroiparams) \
	   ,"Crop ROI parameters = "+",".join(str(x) for x in args.cropparams) \
	   ,"Rotation paramters = "+",".join(str(x) for x in args.rotate)]

	# write log file
	with open(os.path.join(SAVE,"log.txt"), 'w') as f:
		f.write('\n'.join(loglines))


################## COMMANDS ##################

# STEP 2 - make subfolder
total_frames = sum(c for _, c in file_page_counts) if (is_bigtiff or is_multiview) else len(files)
for j in range(t_start, t_last+t_step, t_step):
	if j + number <= total_frames:
		print('>>> Copying dataset '+str(j)+' to temporary folder')

		# managing temp folder
		if j == t_start:
			# pass on first iteration because hard coded to make temp
			pass
		else:
			# make temporary folder since deleted at end of loop
			os.mkdir(TEMP)

		# separate out tomo subfolder 
		# for big tif or multiview
		if is_bigtiff or is_multiview:
		    reductionstep = int(np.round(number / args.reduce[1])) if args.reduce[0] == 1 else 1
		    local_indices = np.arange(j, j + number, reductionstep).astype(int)
		    os.makedirs(os.path.join(TEMP, 'tomosub'), exist_ok=True)
		    outpath = os.path.join(TEMP, 'tomosub', files[0])
		    with tifffile.TiffWriter(outpath, bigtiff=True) as tif_out:
		        for idx in utils.progressbar2(local_indices, ""):
		            # resolve global index idx across split files
		            cursor = 0
		            for fname, page_count in file_page_counts:
		                if idx < cursor + page_count:
		                    local_page = idx - cursor
		                    with tifffile.TiffFile(os.path.join(tomoname, fname)) as tif_in:
		                        tif_out.write(tif_in.pages[local_page].asarray())
		                    break
		                cursor += page_count
		    numbernew = len(local_indices)
		# for single tifs
		else:
		    if args.reduce[0] == 1:
		        reductionstep = np.round(number / args.reduce[1])
		    else:
		        reductionstep = 1
		    utils.make_sub_folder(tomoname, TEMP, number, j, reductionstep)
		    numbernew = len(sorted([f for f in os.listdir(os.path.join(TEMP, 'tomosub')) if os.path.isfile(os.path.join(TEMP, 'tomosub', f))]))

		# find rotation center
		if args.findCoR:
			if tif.is_bigtiff:
				os.system("python find-center-bigtif.py -flats "+flatsname+" -darks "+darksname+" -tomo "+os.path.join(TEMP,'tomosub')+" -SAVE "+SAVE+" -plot")
				with open(os.path.join(SAVE, "correlate-first-last", "rotation_axis.txt")) as f:
					CoR = float(f.read().strip())
			else:
				os.system("python find-center.py -flats "+flatsname+" -darks "+darksname+" -tomo "+os.path.join(TEMP,'tomosub')+" -SAVE "+SAVE+" -plot")
				with open(os.path.join(SAVE, "correlate-first-last", "rotation_axis.txt")) as f:
					CoR = float(f.read().strip())

		# STEP 3 - Reconstruction
		# calculate rotation angle
		rotationangle = j*(180/number)-55
		if region_thick == 1:
			outputcommand = os.path.join(SAVE,str(j).zfill(5))
		else:
			outputcommand = os.path.join(SAVE,str(j).zfill(5),"sli")

		# flat field correction
		print(">>> Flat field correction")
		os.system('tofu flatcorrect --fix-nan-and-inf --flats '+flatsname+' --darks '+darksname+' --reduction-mode median --projections '+TEMP+'/tomosub --output '+TEMP+'/ffc/ffc-%04i.tif --flat-scale 1.0')
		current_input = TEMP+"/ffc"

		# bright spot removal
		if args.brightspotparams[0] == 1:
			# find large bright spots
			print(">>> Make mask of flats")
			flats = utils.read_images(flatsname)
			flatsmedian = np.median(flats,axis=0).astype(np.uint16)
			with get_writer(os.path.join(TEMP,"flat-median.tif")) as writer:
				writer.append_data(flatsmedian, {'compress': 9})
			os.system('tofu find-large-spots --images '+TEMP+"/flat-median.tif"+' --output '+TEMP+'/mask.tif --output-bytes-per-file 0 --spot-threshold '+str(spotthresh)+' --gauss-sigma '+str(gausssigma))
			print(">>> Bright spot removal")
			os.system('ufo-launch [read path='+current_input+' height='+str(height)+' number='+str(numbernew)+', read path='+TEMP+'/mask.tif] ! horizontal-interpolate ! write filename="'+TEMP+'/bs/bs-%04i.tif"')
			os.system('rm -r '+current_input)
			current_input = TEMP+"/bs"

		# phase retrieval
		if args.phaseparams[0] == 1:
			print(">>> Phase retrieval")
			# projection padding
			padwidth, padheight, padx, pady = utils.calc_padding(width, height)
			os.system('ufo-launch read path='+current_input+' height='+str(height)+' number='+str(numbernew)+' ! pad x='+str(padx)+' width='+str(padwidth)+' y='+str(pady)+' height='+str(padheight)+' addressing-mode=clamp_to_edge ! fft dimensions=2 ! retrieve-phase energy='+str(energy)+' distance='+str(distance)+' pixel-size='+str(pixelsize)+'e-6 regularization-rate='+str(regrate)+' ! ifft dimensions=2 crop-width='+str(padwidth)+' crop-height='+str(padheight)+' ! crop x='+str(padx)+' width='+str(width)+' y='+str(pady)+' height='+str(height)+' ! opencl kernel='+"'absorptivity'"+' ! opencl kernel='+"'fix_nan_and_inf'"+' ! write filename="'+TEMP+'/phr/phr-%04i.tif"')
			os.system('rm -r '+current_input)
			current_input = TEMP+"/phr"

		# ring removal
		if args.ringremovalparams[0] == 1:
			print(">>> Ring removal")
			os.system('tofu sinos --projections '+current_input+' --output '+TEMP+'/sinos/sin-%04i.tif --number '+str(numbernew)+' --height '+str(height)+' --pass-size 21137')
			os.system('rm -r '+current_input)
			# sinogram padding
			padwidth, padheight, padx, pady = utils.calc_padding(width, numbernew)
			os.system('ufo-launch read path='+TEMP+'/sinos/ ! pad x='+str(padx)+' width='+str(padwidth)+' y='+str(pady)+' height='+str(padheight)+' addressing-mode=mirrored_repeat ! fft dimensions=2 ! filter-stripes horizontal-sigma='+str(sigmah)+' vertical-sigma='+str(sigmav)+' ! ifft dimensions=2 crop-width='+str(padwidth)+' crop-height='+str(padheight)+' ! crop x='+str(padx)+' width='+str(width)+' y='+str(pady)+' height='+str(numbernew)+' ! write filename="'+TEMP+'/sinos-filt/sin-%04i.tif"')
			os.system('rm -r '+TEMP+"/sinos")
			os.system('tofu sinos --projections '+TEMP+'/sinos-filt --output '+TEMP+'/rr/rr-%04i.tif --number '+str(height)+' --pass-size 21137')
			os.system('rm -r '+TEMP+"/sinos-filt")
			current_input = TEMP+"/rr"

		# reconstruct without ring removal
		absorptivitycommand = "" if args.phaseparams[0] == 1 else "--absorptivity"
		os.system('tofu reco --overall-angle 180 --projections '+current_input+' --output '+outputcommand+' --fix-nan-and-inf --center-position-x '+str(CoR)+' --volume-angle-y '+str(args.rotate[2])+' --volume-angle-x '+str(args.rotate[1])+' --volume-angle-z '+str(rotationangle+args.rotate[0])+' --number '+str(numbernew)+' '+regioncommand+' '+absorptivitycommand+' '+bitratecommand+' --output-bytes-per-file 0')

		print(">>> Cleaning up temporary folder")
		os.system("rm -r "+TEMP)

	else:
		print(">>> Exceeds time limit")
		sys.exit() 

# print time elapsed
elapsedtime = str(datetime.now()-starttime)
print(">>> Finisehd in "+elapsedtime)
starttime = datetime.now()




