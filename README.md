# Dynamic-SRuCT

Scripts for reconstructing and post-processing dynamic (time-resolved) synchrotron
micro-CT data, built around the [ufo-kit / tofu](https://github.com/ufo-kit) reconstruction
toolkit. Originally developed for the dataset described in
[Ding et al., *J. Synchrotron Rad.* (2023), DOI: 10.1107/S1600577523000826](https://doi.org/10.1107/S1600577523000826).

This is the second major version of the codebase — reconstruction is now driven by two
dedicated modes (fixed-interval "dynamic" scans and auto-detected "time-lapse" scans),
center-of-rotation finding is automated, and a PyQt5 GUI is available for building and
running commands without the command line.

## What's here

| Script | Purpose |
|---|---|
| `tofu_dynamic_ct.py` | Main reconstruction wrapper. Splits a raw projection stream into fixed-interval time points and reconstructs each with `tofu`/`ufo-launch` (flat-field correction, optional bright-spot removal, optional phase retrieval, optional ring removal, cropping/ROI, histogram clipping). |
| `tofu_timelapse_ct.py` | For scans where 180°-scan boundaries drift or aren't evenly spaced in time. Auto-detects each scan's start/stop by correlating projections, then calls `tofu_dynamic_ct.py` once per detected scan. |
| `find_center.py` | Finds the center of rotation by correlating the 0° and 180° projections (sub-pixel, via parabolic fit around the minimum). For standard single-page TIFF stacks. |
| `find_center_bigtiff.py` | Same as above, for data stored as BigTIFF / multi-page TIFF files. |
| `reslice.py` | Generates XY, XZ, and YZ resliced views across a folder of reconstructed time-point volumes, with resume support (skips already-processed time points) and optional 180° flip correction for time-lapse scans. |
| `ct_reconstruction_gui.py` | PyQt5 desktop app for building `tofu_dynamic_ct.py` / `tofu_timelapse_ct.py` / `reslice.py` commands interactively, plus a batch script editor for queuing and running multiple commands in sequence. |
| `utils.py` | Shared helper functions used across the above (subfolder splitting with/without binning, grey-value histogram bounds, ellipse mask generation, scan-boundary search, progress bar). |
| `imagej_save_polygon_array.txt` | ImageJ macro snippet for exporting polygon ROI coordinates (e.g. for tracking a region across slices/time points) to a flat array. |

## Requirements

Python dependencies:
```bash
pip install -r requirements.txt
```

You'll also need the [ufo-kit `tofu`/`ufo-launch` toolkit](https://github.com/ufo-kit) installed
and on your `PATH` — this does the actual CT reconstruction, flat-field correction, phase
retrieval, and ring removal, and is not a Python package.

## Workflow

1. **Reconstruct.**
   - If your scan has a fixed, known number of projections per 180° rotation and evenly spaced
     time points, use `tofu_dynamic_ct.py` directly.
   - If scan boundaries vary or need to be detected automatically, use `tofu_timelapse_ct.py`,
     which finds each scan's boundaries and calls `tofu_dynamic_ct.py` for you.
   - Either script can call `find_center.py` / `find_center_bigtiff.py` automatically with
     `-findCoR`, or you can run those separately first and pass `-CoR` explicitly.
2. **Reslice.** Run `reslice.py` on the output folder to generate XY/XZ/YZ views across all
   time points.
3. **GUI (optional).** Run `ct_reconstruction_gui.py` to build and launch any of the above
   commands through a form instead of the CLI, and to queue several runs as a batch script.

### Example: dynamic CT (fixed time points)

```bash
python tofu_dynamic_ct.py \
  -flatsdarks /data/raw/sample1 \
  -tomo /data/raw/sample1/tomo \
  -SAVE /data/rec/sample1 \
  -TEMP /data/tmp/sample1 \
  -number 1000 \
  -timeseries 0,7000,250 \
  -findCoR \
  -phaseparams 1,30,0.45,5,2000 \
  -ringremovalparams 1,3,1 \
  -brightspotparams 1,2000,5 \
  -cliphist 8,-0.0002,-0.0001 \
  -zroiparams 1,300,200,20 \
  -cropparams 1,1232,656,2000,2000
```

### Example: time-lapse CT (auto-detected scan boundaries)

```bash
python tofu_timelapse_ct.py \
  -flatsdarks /data/raw/sample1 \
  -tomo /data/raw/sample1/tomo \
  -SAVE /data/rec/sample1 \
  -TEMP /data/tmp/sample1 \
  -number 500 \
  -timelapsesearch 0,2500,8 \
  -findCoR \
  -phaseparams 1,20,0.5,5.5,200 \
  -cliphist 8,-0.0008,-0.0003 \
  -zroiparams 1,160,500,50 \
  -cropparams 1,500,500,1000,1000
```

### Example: reslicing

```bash
python reslice.py -PATH /data/rec/sample1 -XYsli 1,450 -XZsli 1,1200 -YZsli 0,1200 -mode 0
```

Run any script with `-h` for the full list of arguments and defaults.

## Notes

- `find_center.py`, `find_center_bigtiff.py`, `reslice.py`, and `ct_reconstruction_gui.py`
  invoke each other and `tofu_dynamic_ct.py` / `tofu_timelapse_ct.py` by filename via
  `os.system`/`subprocess`, so all scripts should stay in the same working directory (or on
  `PATH`) when running.
- Both bigtiff/multi-page TIFF stacks and folders of single-page TIFFs are supported for the
  raw projection input.
- This version does not include standalone raw-data housekeeping scripts (deleting scanner
  junk files, splitting raw projections into per-time-point subfolders ahead of time, moving
  reconstructed slices out of `tofu`'s output subfolders) — subfolder splitting is now handled
  internally by `tofu_dynamic_ct.py`. If you still need the old housekeeping scripts, they're
  available in the version history.

## Citation

If you use this code, please cite:

Ding, X. et al. (2023). *J. Synchrotron Rad.* DOI: [10.1107/S1600577523000826](https://doi.org/10.1107/S1600577523000826)
