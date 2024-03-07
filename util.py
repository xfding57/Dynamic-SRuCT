import os, re, subprocess, tifffile
import numpy as np
from shutil import copyfile
from datetime import datetime
from imageio import get_writer
from PIL import Image
run = 1
starttime = datetime.now()
present_dir = os.getcwd()

def get_width_height(PATH):
	files = sorted([f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH,f))])
	im = Image.open(os.path.join(tomoname,files[0]))
	width, height = im.size
	return width, height

def calc_padding(width,height):
	padwidth = 2
	padheight = 2
	count = 1
	while padwidth <= width:
		padwidth = np.power(2,count)
		count = count+1
	count = 1
	while padheight <= height:
		padheight = np.power(2,count)
		count = count+1
	padx = (padwidth-width)/2
	pady = (padheight-height)/2

	return padwidth, padheight, padx, pady

def make_sub_folder(PATH,tomoname,TEMP,number,timepoint):
	tomonames = sorted(os.listdir(os.path.join(PATH,tomoname)))
	os.mkdir(os.path.join(TEMP,"tomosub"))
	for k in range(number):
		copyfile(os.path.join(PATH,tomoname,tomonames[k+timepoint]), os.path.join(TEMP,"tomosub",tomonames[k+timepoint]))

def make_sub_folder_binning(PATH,tomoname,flatsname,darksname,TEMP,number,timepoint,binvalue)
	tomonames = sorted(os.listdir(os.path.join(PATH,tomoname)))
	flatsnames = sorted(os.listdir(os.path.join(PATH,flatsname)))
	darksnames = sorted(os.listdir(os.path.join(PATH,darksname)))
	width, height = get_width_height(os.path.join(PATH,tomoname))
	os.mkdir(os.path.join(TEMP,"tomosub"))
	for k in range(number):
		imsingle = np.array(tifffile.imread(os.path.join(PATH,tomoname,tomonames[k+timepoint])).astype(np.float32))
		imsingle = imsingle.reshape((int(height),binvalue,int(width),binvalue)).mean(axis=(1, 3))
		with get_writer(os.path.join(TEMP,"tomosub",str(k).zfill(5)+".tif")) as writer:
			writer.append_data(imsingle, {'compress': 9})
	os.mkdir(os.path.join(TEMP,"flatsub"))
	for k in range(len(flatsnames)):
		imsingle = np.array(tifffile.imread(os.path.join(PATH,flatsname,flatsnames[k])).astype(np.float32))
		imsingle = imsingle.reshape((int(height),binvalue,int(width),binvalue)).mean(axis=(1, 3))
		with get_writer(os.path.join(TEMP,"flatsub",str(k).zfill(5)+".tif")) as writer:
			writer.append_data(imsingle, {'compress': 9})
	os.mkdir(os.path.join(TEMP,"darksub"))
	for k in range(len(darksnames)):
		imsingle = np.array(tifffile.imread(os.path.join(PATH,darksname,darksnames[k])).astype(np.float32))
		imsingle = imsingle.reshape((int(height),binvalue,int(width),binvalue)).mean(axis=(1, 3))
		with get_writer(os.path.join(TEMP,"darksub",str(k).zfill(5)+".tif")) as writer:
			writer.append_data(imsingle, {'compress': 9})




