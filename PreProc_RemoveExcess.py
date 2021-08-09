import os
from datetime import datetime
starttime = datetime.now() # get current time
present_dir = os.getcwd() # get present directory
run = 1

for directory, subdirlist, filelist in os.walk(present_dir):
	if run == 0:
		for f in filelist:
			if f == 'Thumbs.db':
				print(directory)
				print(f)
				print('')
				os.remove(os.path.join(directory,f))
			if f == 'reco.params':
				print(directory)
				print(f)
				print('')
				os.remove(os.path.join(directory,f))
			if f == 'im_00001.tif.rec':
				print(directory)
				print(f)
				print('')
				os.remove(os.path.join(directory,f))

print(datetime.now() - starttime) # show time elapsed