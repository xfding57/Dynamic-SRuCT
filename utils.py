import os, re, subprocess, tifffile, sys, argparse
import numpy as np
from shutil import copyfile
from datetime import datetime
from imageio import get_writer
from PIL import Image
run = 1
starttime = datetime.now()
present_dir = os.getcwd()

def root_path():
	return os.path.abspath(os.sep)

def progressbar2(it, prefix="", size=50, out=sys.stdout):
	count = len(it)
	def show(j):
		x = int(size*j/count)
		out.write("%s[%s%s] %i/%i\r" % (prefix, u"#"*x, "."*(size-x), j, count))
		out.flush()        
	show(0)
	for i, item in enumerate(it):
		yield item
		show(i+1)
	out.write("\n")
	out.flush()

def read_images(image_directory):
	# This function takes the directory containing darks, flats, and tomo folder 
	# then returns 3D arrays for darks, flats, and tomo
	# get names of all files inside directory
	directory_file_names = sorted([f for f in os.listdir(image_directory) if os.path.isfile(os.path.join(image_directory, f))])
	# get the number of images in folder
	directory_size = np.size(directory_file_names)
	# open the first image
	image_file = Image.open(os.path.join(image_directory, directory_file_names[0]))
	# change from image to array
	image_as_array = np.array(image_file)
	# get the shape of the array
	image_as_array_shape = np.shape(image_as_array)
	# preallocate space
	preallocate_matrix = np.zeros((directory_size, image_as_array_shape[0], image_as_array_shape[1]))
	# open all images and save as 3d array
	for i in range(directory_size):
		image_file = Image.open(os.path.join(image_directory, directory_file_names[i]))
		preallocate_matrix[i] = np.array(image_file)
	image_stack_array = preallocate_matrix

	return image_stack_array

def get_width_height(PATH):
	files = sorted([f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH,f))])
	im = Image.open(os.path.join(PATH,files[0]))
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

def make_sub_folder(tomoname,TEMP,number,timepoint,step):
	tomonames = sorted(os.listdir(tomoname))
	os.mkdir(os.path.join(TEMP,"tomosub"))
	for k in progressbar2(np.arange(0,number,step), ""):
		copyfile(os.path.join(tomoname,tomonames[int(k+timepoint)]), os.path.join(TEMP,"tomosub",tomonames[int(k+timepoint)]))

def make_sub_folder_binning(tomoname,flatsname,darksname,TEMP,number,timepoint,binvalue):
	tomonames = sorted(os.listdir(tomoname))
	flatsnames = sorted(os.listdir(flatsname))
	darksnames = sorted(os.listdir(darksname))
	width, height = get_width_height(tomoname)
	os.mkdir(os.path.join(TEMP,"tomosub"))
	for k in range(number):
		imsingle = np.array(tifffile.imread(os.path.join(tomoname,tomonames[k+timepoint])).astype(np.float32))
		imsingle = imsingle.reshape((int(height),binvalue,int(width),binvalue)).mean(axis=(1, 3))
		with get_writer(os.path.join(TEMP,"tomosub",str(k).zfill(5)+".tif")) as writer:
			writer.append_data(imsingle, {'compress': 9})
	os.mkdir(os.path.join(TEMP,"flatsub"))
	for k in range(len(flatsnames)):
		imsingle = np.array(tifffile.imread(os.path.join(flatsname,flatsnames[k])).astype(np.float32))
		imsingle = imsingle.reshape((int(height),binvalue,int(width),binvalue)).mean(axis=(1, 3))
		with get_writer(os.path.join(TEMP,"flatsub",str(k).zfill(5)+".tif")) as writer:
			writer.append_data(imsingle, {'compress': 9})
	os.mkdir(os.path.join(TEMP,"darksub"))
	for k in range(len(darksnames)):
		imsingle = np.array(tifffile.imread(os.path.join(darksname,darksnames[k])).astype(np.float32))
		imsingle = imsingle.reshape((int(height),binvalue,int(width),binvalue)).mean(axis=(1, 3))
		with get_writer(os.path.join(TEMP,"darksub",str(k).zfill(5)+".tif")) as writer:
			writer.append_data(imsingle, {'compress': 9})

def parselist(string):
	'''Converts a comma-separated string into a list of floats or integers.'''
	try:
		return [float(num) if '.' in num else int(num) for num in string.split(',')]
	except ValueError:
		raise argparse.ArgumentTypeError("Invalid format for --weights, expected format: 1,2,3")

def parselist_better(string):
    """Parse comma-separated numeric input into ints/floats. Returns None if invalid."""
    values = string.split(',')
    cleaned = []
    for v in values:
        v = v.strip()
        if not v:
            return None
        try:
            cleaned.append(float(v) if '.' in v else int(v))
        except ValueError:
            return None
    return cleaned

def get_grey_boundary(PATH,histperc,expansion):
	im = read_images(PATH)
	# Flatten the image stack to get the pixel intensity values across all images
	pixels = im.flatten()
	# lowest and highest values
	lowest = np.min(im)
	highest = np.max(im)

	# print(lowest)
	# print(highest)

	# Assuming pixels is your flattened array from the TIFF stack
	low = np.percentile(pixels, (1-histperc)*100)
	high = np.percentile(pixels, histperc*100)
	range_ = high - low
	# Calculate expansion of the range
	expansion = expansion * range_
	# Expand the low boundary downwards and the high boundary upwards by the expansion value
	lower = low - expansion
	higher = high + expansion

	print(lowest,lower,low,high,higher,highest)
	return lowest,lower,low,high,higher,highest

def set_grey_boundary(PATH,SAVE,histperc,expansion,mode):
	im = read_images(PATH)
	# Flatten the image stack to get the pixel intensity values across all images
	pixels = im.flatten()
	# lowest and highest values
	lowest = np.min(im)
	highest = np.max(im)

	# Assuming pixels is your flattened array from the TIFF stack
	low = np.percentile(pixels, (1-histperc)*100)
	high = np.percentile(pixels, histperc*100)
	range_ = high - low
	# Calculate expansion of the range
	expansion = expansion * range_
	# Expand the low boundary downwards and the high boundary upwards by the expansion value
	lower = low - expansion
	higher = high + expansion

	# scale im
	if mode == 1:
		im_partialhist = ((im-lowest)/(highest-lowest)*65535).astype(np.uint16)
	elif mode == 2:
		im_partialhist = ((im-lower)/(higher-lower)*65535).astype(np.uint16)
	elif mode == 3:
		im_partialhist = ((im-low)/(high-low)*65535).astype(np.uint16)
	# make output folder if it doesn't exist
	if not os.path.isdir(SAVE):
		os.mkdir(SAVE)
	# Iterate over each image in the scaled stack
	for i, im_single in enumerate(im_partialhist):
		filename = os.path.join(SAVE,"im_"+str(i).zfill(4)+".tif")
		tifffile.imwrite(filename, im_single)
		
def search_start_stop(tomoname,start,number,searchrange):
	PATH = tomoname
	files = sorted([f for f in os.listdir(PATH) if os.path.isfile(os.path.join(PATH,f))])

	startstop = np.array([[start,start+number]])
	if startstop[0][1] > len(files):
		print(">>> Last projection found "+str(len(files)))
		return len(files)

	print(">>> First projection found at "+str(start))
	im1 = Image.open(os.path.join(PATH,files[startstop[0][0]])).convert('F')
	vecount = 0
	difvec = []
	radiovec = []
	for i in np.arange(-searchrange/2,searchrange/2,1):
		im2 = Image.open(os.path.join(PATH,files[startstop[0][1]+int(i)])).convert('F')
		radiovec.append(startstop[0][1]+i)
		difvec.append(np.std(np.subtract(np.array(im1),np.array(im2))))
		vecount = vecount+1

	difvecdif = tuple(abs(np.diff(difvec)))
	lowest = difvecdif.index(max(difvecdif))+1
	print(">>> Last projection found "+str(radiovec[lowest]))

	return radiovec[lowest]

def search_start_stop_bigtiff(tomoname, start, number, searchrange, file_page_counts):
    total_frames = sum(c for _, c in file_page_counts)

    if start + number > total_frames:
        print(">>> Last projection found " + str(total_frames))
        return total_frames

    print(">>> First projection found at " + str(start))

    def get_frame(global_index):
        cursor = 0
        for fname, page_count in file_page_counts:
            if global_index < cursor + page_count:
                local_page = global_index - cursor
                with tifffile.TiffFile(os.path.join(tomoname, fname)) as tif:
                    return np.array(tif.pages[local_page].asarray(), dtype=np.float32)
            cursor += page_count
        raise IndexError(f"Global index {global_index} out of range")

    im1 = get_frame(start)
    difvec = []
    radiovec = []
    for i in np.arange(-searchrange/2, searchrange/2, 1):
        idx = start + number + int(i)
        im2 = get_frame(idx)
        radiovec.append(idx)
        difvec.append(np.std(np.subtract(im1, im2)))

    difvecdif = tuple(abs(np.diff(difvec)))
    lowest = difvecdif.index(max(difvecdif)) + 1
    print(">>> Last projection found " + str(radiovec[lowest]))
    return radiovec[lowest]

def get_integer_value():
	while True:
		userinput = input("Value: ")
		try:
			return int(userinput)
		except ValueError:
			pass

def get_clear_condition():
	clearcondition = input('Clear outside and inside [y/n]: ')
	if clearcondition == 'y':
		return True
	elif clearcondition == 'n':
		return False
	else:
		return get_clear_condition()

def create_ellipse_mask(shape, center_x, center_y, radius_x, radius_y):
	height, width = shape
	y, x = np.ogrid[:height, :width]
	distances = ((x-center_x)/radius_x)**2+((y-center_y)/radius_y)**2
	mask = distances<=1
	return mask
