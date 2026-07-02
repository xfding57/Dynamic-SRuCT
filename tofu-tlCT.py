import os, re, subprocess, tifffile, sys
import numpy as np
from shutil import copyfile
from datetime import datetime
from imageio import get_writer
from PIL import Image
import argparse
import utils
run = 1
starttime = datetime.now()
present_dir = os.getcwd()

# Set up argparse to accept command line arguments
parser = argparse.ArgumentParser(description='Wrapper for dynamic CT reconstruction using ')
parser.add_argument('-flatsdarks', type=str, default='flats', help='path to folder with flats and darks')
parser.add_argument('-tomo', type=str, default='tomo', help='path to folder with tomo')
parser.add_argument('-SAVE', type=str, default="", help='Path for save reconstructed results')
parser.add_argument('-TEMP', type=str, default="", help='Path for temporary folders')
parser.add_argument('-number', type=int, default=500, help='Number of projections in one 180 scan')
parser.add_argument('-reduce', type=utils.parselist, default='1,125', help='reduce raw data projection number')
parser.add_argument('-timelapsesearch', type=utils.parselist, default='0,2500,8', help='timelapse start, timelapse stop, timelapse search range')
parser.add_argument('-CoR', type=float, default=999.5, help='Center of Rotation')
parser.add_argument('-findCoR', action="store_true", help='find CoR by correlating first and last')
parser.add_argument('-phaseparams', type=utils.parselist, default='1,20,0.5,5.5,200', help='(0 or 1),energy[keV],distance[m],pixelsize[um],deltabeta')
parser.add_argument('-ringremovalparams', type=utils.parselist, default='1,3,1', help='(0 or 1),horizontal-sigma,vertical-sigma')
parser.add_argument('-brightspotparams', type=utils.parselist, default='1,2000,5', help='(0 or 1),thresholding,gaussian-sigma')
parser.add_argument('-cliphist', type=utils.parselist, default='8,-0.0008,-0.0003', help='output-bitdepth,output-minimum,output-maximum')
parser.add_argument('-zroiparams', type=utils.parselist, default='1,160,500,50', help='(0 or 1),start,height,step')
parser.add_argument('-cropparams', type=utils.parselist, default='1,500,500,1000,1000', help='(0 or 1),x,y,width,length')
args = parser.parse_args()

# detect big tifs or single tifs
files = sorted([f for f in os.listdir(args.tomo) if os.path.isfile(os.path.join(args.tomo, f))])
with tifffile.TiffFile(os.path.join(args.tomo, files[0])) as tif:
	is_bigtiff = tif.is_bigtiff
	if is_bigtiff:
		file_page_counts = [(f, len(tifffile.TiffFile(os.path.join(args.tomo, f)).pages)) for f in files]
	else:
		file_page_counts = None

timepoints = (args.timelapsesearch[1]-args.timelapsesearch[2])/args.number
start = args.timelapsesearch[0]

for i in range(int(np.floor(timepoints))):
	if is_bigtiff:
		stop = utils.search_start_stop_bigtiff(args.tomo, start, args.number, args.timelapsesearch[2], file_page_counts)
	else:
		stop = utils.search_start_stop(args.tomo, start, args.number, args.timelapsesearch[2])
	truenumber = int(stop-start)
	print(">>> Number of projections "+str(truenumber))

	if args.findCoR:
		CoRflag = "-findCoR"
	else:
		CoRflag = ""
	os.system("python tofu-dCT-260325.py -flatsdarks "+args.flatsdarks+" -tomo "+args.tomo+" -SAVE "+args.SAVE+" -TEMP "+args.TEMP+" -number "+str(truenumber)+" -reduce "+str(args.reduce[0])+","+str(args.reduce[1])+" -timeseries "+str(start)+","+str(start)+",1 -CoR "+str(args.CoR)+" "+CoRflag+" -phaseparams "+str(args.phaseparams[0])+","+str(args.phaseparams[1])+","+str(args.phaseparams[2])+","+str(args.phaseparams[3])+","+str(args.phaseparams[4])+" -ringremovalparams "+str(args.ringremovalparams[0])+","+str(args.ringremovalparams[1])+","+str(args.ringremovalparams[2])+" -brightspotparams "+str(args.brightspotparams[0])+","+str(args.brightspotparams[1])+","+str(args.brightspotparams[2])+" -cliphist "+str(args.cliphist[0])+","+str(args.cliphist[1])+","+str(args.cliphist[2])+" -zroiparams "+str(args.zroiparams[0])+","+str(args.zroiparams[1])+","+str(args.zroiparams[2])+","+str(args.zroiparams[3])+" -cropparams "+str(args.cropparams[0])+","+str(args.cropparams[1])+","+str(args.cropparams[2])+","+str(args.cropparams[3])+","+str(args.cropparams[4])+" -rotate 0,0,0")

	start = int(stop+1)

