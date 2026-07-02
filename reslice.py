import argparse
import numpy as np
from pathlib import Path
from skimage import io, transform
import tifffile
import utils

# Set up argparse to accept command line arguments
parser = argparse.ArgumentParser(description='Wrapper for dynamic time lapse CT reslicing')
parser.add_argument('-PATH', type=str, default='/beamlinedata/BMIT/projects/prj40G14532/rec/2026-1-27-BM/Xiaofan-test/Tablet-2/wet', help='path to reconstructions')
parser.add_argument('-XYsli', type=utils.parselist, default='1,450', help='XY slice position')
parser.add_argument('-XZsli', type=utils.parselist, default='1,1200', help='XZ slice position')
parser.add_argument('-YZsli', type=utils.parselist, default='0,1200', help='YZ slice position')
parser.add_argument('-mode', type=int, default=0, help='0 for dCT 1 for tlCT')
args = parser.parse_args()

# Get subdirectories
path = Path(args.PATH)
subdirs = sorted([d for d in path.iterdir() if d.is_dir()])

# Check existing outputs
xy_out = Path(str(args.PATH) + "-XY"+str(args.XYsli[1]))
xz_out = Path(str(args.PATH) + "-XZ"+str(args.XZsli[1]))
yz_out = Path(str(args.PATH) + "-YZ"+str(args.YZsli[1]))

XYdone = len(list(xy_out.glob("*.tif"))) if xy_out.exists() else 0
XZdone = len(list(xz_out.glob("*.tif"))) if xz_out.exists() else 0
YZdone = len(list(yz_out.glob("*.tif"))) if yz_out.exists() else 0

print(f">>> Already processed: XY={XYdone}, XZ={XZdone}, YZ={YZdone}")
print(f">>> Found {len(subdirs)} subdirectories to process")

for i, subdir in enumerate(subdirs):
    dirName = subdir.name
    
    # Get list of tif files
    tif_files = sorted(subdir.glob("*.tif")) + sorted(subdir.glob("*.tiff"))
    
    # Process XY slice
    if i >= XYdone and args.XYsli[0] == 1:
        xy_out.mkdir(exist_ok=True)
        output_path = xy_out / f"{dirName.zfill(5)}.tif"
        print(">>> Process XY slice "+output_path.name)
        # Load only the specific slice we need for XY
        img = io.imread(str(tif_files[args.XYsli[1]]))
        # Rotate 180 degrees if odd index
        if i % 2 == 1 and args.mode == 1:
            img = np.rot90(img, k=2)
        # Save the XY slice
        io.imsave(str(output_path), img, check_contrast=False)
    
    # Process XZ and YZ slices - need to load full stack
    if (i >= XZdone and args.XZsli[0] == 1) or (i >= YZdone and args.YZsli[0] == 1):
        # Load the entire stack
        print(f">>> Reading stack {dirName} to memory")
        stack = tifffile.imread(str(tif_files[0]))
        
        # If single image was loaded, load as collection
        if stack.ndim == 2:
            stack = np.array([io.imread(str(f)) for f in tif_files])
        
        # Rotate 180 degrees if odd index
        if i % 2 == 1 and args.mode == 1:
            stack = np.rot90(stack, k=2, axes=(1, 2))
        
        # Process XZ slice
        if i >= XZdone and args.XZsli[0] == 1:
            xz_out.mkdir(exist_ok=True)
            output_path = xz_out / f"{dirName.zfill(5)}.tif"
            print(">>> Process XZ reslicing "+output_path.name)
            xz_slice = stack[:, args.XZsli[1], :]
            io.imsave(str(output_path), xz_slice, check_contrast=False)
        
        # Process YZ slice
        if i >= YZdone and args.YZsli[0] == 1:
            yz_out.mkdir(exist_ok=True)
            output_path = yz_out / f"{dirName.zfill(5)}.tif"
            print(">>> Process YZ reslicing "+output_path.name)
            yz_slice = stack[:, :, args.YZsli[1]]
            io.imsave(str(output_path), yz_slice, check_contrast=False)
                
print(">>> Finished all tasks")